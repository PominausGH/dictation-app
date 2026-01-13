# Streaming Transcription Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace batch transcription with real-time streaming so words appear as you speak.

**Architecture:** RealtimeSTT handles audio capture and continuous Whisper transcription. A TextDiffer class tracks what's been typed and calculates corrections (backspaces + new text). Hotkey toggle (Ctrl+Shift+D) starts/stops the recorder.

**Tech Stack:** RealtimeSTT, pynput, ydotool, faster-whisper (used internally by RealtimeSTT)

---

## Task 1: Install RealtimeSTT and Update Dependencies

**Files:**
- Modify: `requirements.txt`

**Step 1: Install RealtimeSTT**

Run:
```bash
source venv/bin/activate && pip install RealtimeSTT
```

Expected: Successful installation with dependencies

**Step 2: Update requirements.txt**

Replace contents of `requirements.txt` with:

```
RealtimeSTT>=0.3.100
pynput>=1.7.6
```

Note: RealtimeSTT includes faster-whisper, numpy, sounddevice as dependencies.

**Step 3: Verify installation**

Run:
```bash
source venv/bin/activate && python -c "from RealtimeSTT import AudioToTextRecorder; print('OK')"
```

Expected: `OK`

**Step 4: Commit**

```bash
git init && git add requirements.txt && git commit -m "chore: add RealtimeSTT dependency"
```

---

## Task 2: Create TextDiffer Class with Tests

**Files:**
- Create: `text_differ.py`
- Create: `test_text_differ.py`

**Step 1: Write failing tests**

Create `test_text_differ.py`:

```python
"""Tests for TextDiffer class."""
import pytest
from text_differ import TextDiffer


class TestTextDiffer:
    def test_initial_state_empty(self):
        differ = TextDiffer()
        assert differ.last_typed == ""

    def test_first_text_no_backspaces(self):
        differ = TextDiffer()
        backspaces, new_text = differ.calculate_diff("Hello")
        assert backspaces == 0
        assert new_text == "Hello"

    def test_append_only(self):
        differ = TextDiffer()
        differ.update("Hello")
        backspaces, new_text = differ.calculate_diff("Hello world")
        assert backspaces == 0
        assert new_text == " world"

    def test_correction_needed(self):
        differ = TextDiffer()
        differ.update("I want to go")
        backspaces, new_text = differ.calculate_diff("I wanted to go")
        # Common prefix is "I want", need to delete " to go" (6 chars)
        # Then type "ed to go"
        assert backspaces == 6
        assert new_text == "ed to go"

    def test_complete_replacement(self):
        differ = TextDiffer()
        differ.update("Hello")
        backspaces, new_text = differ.calculate_diff("Goodbye")
        assert backspaces == 5
        assert new_text == "Goodbye"

    def test_reset_clears_state(self):
        differ = TextDiffer()
        differ.update("Some text")
        differ.reset()
        assert differ.last_typed == ""

    def test_skip_large_correction(self):
        differ = TextDiffer(max_backspaces=20)
        differ.update("A" * 30)
        backspaces, new_text = differ.calculate_diff("B" * 30)
        # Should skip - return None to signal skip
        assert backspaces is None
        assert new_text is None

    def test_update_tracks_typed_text(self):
        differ = TextDiffer()
        differ.update("Hello")
        assert differ.last_typed == "Hello"
        differ.update("Hello world")
        assert differ.last_typed == "Hello world"
```

**Step 2: Run tests to verify they fail**

Run:
```bash
source venv/bin/activate && pytest test_text_differ.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'text_differ'"

**Step 3: Write TextDiffer implementation**

Create `text_differ.py`:

```python
"""TextDiffer: Calculate diff between transcription updates for real-time typing."""


class TextDiffer:
    """Tracks typed text and calculates corrections needed for new transcriptions."""

    def __init__(self, max_backspaces: int = 20):
        """Initialize differ.

        Args:
            max_backspaces: Maximum backspaces before skipping correction.
        """
        self.last_typed = ""
        self.max_backspaces = max_backspaces

    def calculate_diff(self, new_text: str) -> tuple[int | None, str | None]:
        """Calculate backspaces and new text needed.

        Args:
            new_text: The new transcription text.

        Returns:
            Tuple of (backspaces_needed, text_to_type).
            Returns (None, None) if correction would exceed max_backspaces.
        """
        # Find common prefix length
        common_len = 0
        for i in range(min(len(self.last_typed), len(new_text))):
            if self.last_typed[i] == new_text[i]:
                common_len += 1
            else:
                break

        backspaces = len(self.last_typed) - common_len
        new_chars = new_text[common_len:]

        # Skip if too many backspaces needed
        if backspaces > self.max_backspaces:
            return None, None

        return backspaces, new_chars

    def update(self, text: str) -> None:
        """Update the tracked typed text.

        Args:
            text: The text that has been typed.
        """
        self.last_typed = text

    def reset(self) -> None:
        """Reset to initial state."""
        self.last_typed = ""
```

**Step 4: Run tests to verify they pass**

Run:
```bash
source venv/bin/activate && pytest test_text_differ.py -v
```

Expected: All 8 tests PASS

**Step 5: Commit**

```bash
git add text_differ.py test_text_differ.py && git commit -m "feat: add TextDiffer class for real-time corrections"
```

---

## Task 3: Refactor DictationApp to Use RealtimeSTT

**Files:**
- Modify: `dictation.py`

**Step 1: Backup current implementation**

Run:
```bash
cp dictation.py dictation_backup.py
```

**Step 2: Rewrite dictation.py**

Replace entire contents of `dictation.py` with:

```python
#!/usr/bin/env python3
"""
Dictation App for Ubuntu Linux
Press Ctrl+Shift+D to toggle dictation on/off.
Speaks into microphone, transcribes with streaming Whisper, types into focused app.
"""

import subprocess
import threading
import sys
from pynput import keyboard
from RealtimeSTT import AudioToTextRecorder
from text_differ import TextDiffer


class DictationApp:
    def __init__(self):
        self.recorder = None
        self.recording = False
        self.differ = TextDiffer(max_backspaces=20)
        self.lock = threading.Lock()
        self.word_count = 0

        # Hotkey state
        self.ctrl_pressed = False
        self.shift_pressed = False

    def type_text(self, text: str) -> bool:
        """Type text into focused application using ydotool.

        Returns True on success, False on failure.
        """
        if not text:
            return True
        try:
            subprocess.run(
                ["ydotool", "type", "--", text],
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed to type: {e}")
            return False
        except FileNotFoundError:
            print("[ERROR] ydotool not found. Run setup.sh first.")
            return False

    def type_backspaces(self, count: int) -> bool:
        """Type backspace keys using ydotool.

        Returns True on success, False on failure.
        """
        if count <= 0:
            return True
        try:
            # ydotool key command: 14 is backspace keycode
            # Format: 14:1 = press, 14:0 = release
            for _ in range(count):
                subprocess.run(
                    ["ydotool", "key", "14:1", "14:0"],
                    check=True,
                    capture_output=True
                )
            return True
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed to backspace: {e}")
            return False
        except FileNotFoundError:
            print("[ERROR] ydotool not found. Run setup.sh first.")
            return False

    def on_realtime_update(self, text: str):
        """Called when RealtimeSTT has a transcription update."""
        text = text.strip()
        if not text:
            return

        backspaces, new_text = self.differ.calculate_diff(text)

        if backspaces is None:
            print("[WARN] Skipped large correction")
            return

        # Apply correction
        if backspaces > 0:
            if not self.type_backspaces(backspaces):
                return

        if new_text:
            if self.type_text(new_text):
                self.differ.update(text)
                self.word_count = len(text.split())

    def on_recording_start(self):
        """Called when recording starts."""
        print("\n[DICTATING] Speak now... (Ctrl+Shift+D to stop)")

    def on_recording_stop(self):
        """Called when recording stops."""
        pass  # Handled in stop_recording

    def start_recording(self):
        """Start streaming dictation."""
        with self.lock:
            if self.recording:
                return
            self.recording = True
            self.differ.reset()
            self.word_count = 0

        # Initialize recorder with streaming enabled
        self.recorder = AudioToTextRecorder(
            model="tiny",
            language="en",
            device="cpu",
            enable_realtime_transcription=True,
            realtime_model_type="tiny",
            realtime_processing_pause=0.1,
            on_realtime_transcription_update=self.on_realtime_update,
            on_recording_start=self.on_recording_start,
            on_recording_stop=self.on_recording_stop,
            silero_sensitivity=0.4,
            post_speech_silence_duration=0.4,
        )

        # Start recording in background thread
        self.record_thread = threading.Thread(target=self._record_loop)
        self.record_thread.start()

    def _record_loop(self):
        """Recording loop that runs in background thread."""
        try:
            while self.recording:
                # text() blocks until speech detected and silence follows
                # But we mainly use realtime callbacks for typing
                final_text = self.recorder.text()
                if final_text and self.recording:
                    # Final text - ensure it's fully typed
                    final_text = final_text.strip()
                    if final_text:
                        backspaces, new_text = self.differ.calculate_diff(final_text)
                        if backspaces is not None:
                            self.type_backspaces(backspaces)
                            if new_text:
                                self.type_text(new_text)
                            self.differ.update(final_text)
        except Exception as e:
            print(f"[ERROR] Recording error: {e}")
        finally:
            if self.recorder:
                self.recorder.shutdown()

    def stop_recording(self):
        """Stop streaming dictation."""
        with self.lock:
            if not self.recording:
                return
            self.recording = False

        print(f"[DONE] Typed {self.word_count} words")

        # Recorder will be shut down in _record_loop

    def toggle_recording(self):
        """Toggle recording on/off."""
        if self.recording:
            self.stop_recording()
        else:
            self.start_recording()

    def on_press(self, key):
        """Handle key press events."""
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            self.ctrl_pressed = True
        elif key == keyboard.Key.shift_l or key == keyboard.Key.shift_r:
            self.shift_pressed = True
        elif hasattr(key, 'char') and key.char == 'd':
            if self.ctrl_pressed and self.shift_pressed:
                threading.Thread(target=self.toggle_recording).start()

    def on_release(self, key):
        """Handle key release events."""
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            self.ctrl_pressed = False
        elif key == keyboard.Key.shift_l or key == keyboard.Key.shift_r:
            self.shift_pressed = False

    def check_ydotool(self) -> bool:
        """Check if ydotool is available and working."""
        try:
            subprocess.run(
                ["ydotool", "--help"],
                check=True,
                capture_output=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def run(self):
        """Run the dictation app."""
        print("=" * 50)
        print("       DICTATION APP FOR UBUNTU")
        print("         (Streaming Mode)")
        print("=" * 50)
        print()

        # Check ydotool
        if not self.check_ydotool():
            print("[ERROR] ydotool not available.")
            print("Make sure ydotoold is running and you're in the 'input' group.")
            print("Run: sudo ydotoold &")
            sys.exit(1)

        print("Ready! Press Ctrl+Shift+D to toggle dictation.")
        print("Press Ctrl+C to exit.")
        print()

        # Start keyboard listener
        with keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        ) as listener:
            try:
                listener.join()
            except KeyboardInterrupt:
                print("\nExiting...")
                self.recording = False
                if self.recorder:
                    self.recorder.shutdown()


def main():
    app = DictationApp()
    app.run()


if __name__ == "__main__":
    main()
```

**Step 3: Verify syntax**

Run:
```bash
source venv/bin/activate && python -m py_compile dictation.py && echo "Syntax OK"
```

Expected: `Syntax OK`

**Step 4: Commit**

```bash
git add dictation.py && git commit -m "feat: replace batch transcription with RealtimeSTT streaming"
```

---

## Task 4: Manual Testing

**Step 1: Test short phrase**

Run:
```bash
source venv/bin/activate && python dictation.py
```

1. Open a text editor
2. Press Ctrl+Shift+D
3. Say "Hello world"
4. Press Ctrl+Shift+D to stop
5. Verify: Words appeared as you spoke, not after stopping

Expected: Text appears within ~0.5-1s of speaking

**Step 2: Test correction behavior**

1. Press Ctrl+Shift+D
2. Say "I want to go" then continue "home"
3. Observe if any corrections happen (backspaces)
4. Press Ctrl+Shift+D to stop

Expected: Corrections are minimal and not chaotic

**Step 3: Test long dictation**

1. Press Ctrl+Shift+D
2. Speak continuously for 30+ seconds
3. Press Ctrl+Shift+D to stop

Expected: App remains responsive, text continues appearing

**Step 4: Test rapid toggle**

1. Press Ctrl+Shift+D to start
2. Immediately press Ctrl+Shift+D to stop
3. Repeat 3 times

Expected: No crashes or hangs

---

## Task 5: Cleanup and Final Commit

**Step 1: Remove backup file**

Run:
```bash
rm -f dictation_backup.py
```

**Step 2: Final commit**

```bash
git add -A && git commit -m "feat: complete streaming transcription implementation"
```

---

## Troubleshooting

**If RealtimeSTT fails to import:**
```bash
pip install --upgrade RealtimeSTT
```

**If audio doesn't work:**
- Check microphone: `arecord -l`
- Try different input device index in AudioToTextRecorder

**If typing doesn't work:**
- Verify ydotoold is running: `pgrep ydotoold`
- Start it: `sudo ydotoold &`
- Check group membership: `groups | grep input`

**If transcription is slow:**
- The first transcription downloads/loads the model
- Subsequent transcriptions should be faster
- Try `realtime_processing_pause=0.05` for faster updates (more CPU)
