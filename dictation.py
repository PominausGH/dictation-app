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
