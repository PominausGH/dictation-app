#!/usr/bin/env python3
"""
Dictation App with Chunked Streaming
Transcribes every 1.5 seconds while speaking, not waiting for silence.
"""

import subprocess
import threading
import sys
import time
import numpy as np
import sounddevice as sd
from pynput import keyboard
from faster_whisper import WhisperModel
from text_differ import TextDiffer

SAMPLE_RATE = 16000
CHUNK_DURATION = 1.5  # Transcribe every 1.5 seconds


class ChunkedDictation:
    def __init__(self):
        self.recording = False
        self.audio_buffer = []
        self.differ = TextDiffer(max_backspaces=20)
        self.lock = threading.Lock()
        self.model = None
        self.stream = None

        # Hotkey state
        self.cmd_pressed = False

    def load_model(self):
        print("Loading Whisper model...")
        self.model = WhisperModel("tiny", device="cpu", compute_type="int8")
        print("Model loaded!")

    def type_text(self, text: str) -> bool:
        if not text:
            return True
        try:
            subprocess.run(["ydotool", "type", "--", text], check=True, capture_output=True)
            return True
        except Exception as e:
            print(f"[ERROR] {e}")
            return False

    def type_backspaces(self, count: int) -> bool:
        if count <= 0:
            return True
        try:
            for _ in range(count):
                subprocess.run(["ydotool", "key", "14:1", "14:0"], check=True, capture_output=True)
            return True
        except Exception as e:
            print(f"[ERROR] {e}")
            return False

    def audio_callback(self, indata, frames, time_info, status):
        if self.recording:
            self.audio_buffer.append(indata.copy())

    def transcribe_buffer(self):
        """Transcribe accumulated audio and type the result."""
        if not self.audio_buffer:
            return

        # Combine all audio chunks
        audio = np.concatenate(self.audio_buffer, axis=0).flatten()

        # Check if audio is too quiet
        if np.abs(audio).max() < 0.01:
            return

        # Transcribe
        segments, _ = self.model.transcribe(
            audio,
            beam_size=1,
            language="en",
            without_timestamps=True,
            vad_filter=False,
        )
        text = " ".join([s.text for s in segments]).strip()

        if not text:
            return

        # Calculate diff and type
        backspaces, new_text = self.differ.calculate_diff(text)

        if backspaces is None:
            print("[WARN] Large correction skipped")
            return

        if backspaces > 0:
            self.type_backspaces(backspaces)

        if new_text:
            self.type_text(new_text)
            self.differ.update(text)
            print(f"[LIVE] {text}")

    def transcription_loop(self):
        """Periodically transcribe the audio buffer."""
        print("[DEBUG] Transcription loop started")
        while self.recording:
            time.sleep(CHUNK_DURATION)
            print(f"[DEBUG] Buffer has {len(self.audio_buffer)} chunks")
            if self.recording and self.audio_buffer:
                self.transcribe_buffer()
        print("[DEBUG] Transcription loop ended")

    def start_recording(self):
        with self.lock:
            if self.recording:
                return
            self.recording = True
            self.audio_buffer = []
            self.differ.reset()

        print("\n[RECORDING] Speak now... (Cmd+D to stop)")

        # Start audio stream
        self.stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype=np.float32,
            callback=self.audio_callback
        )
        self.stream.start()

        # Start transcription thread
        self.transcribe_thread = threading.Thread(target=self.transcription_loop, daemon=True)
        self.transcribe_thread.start()

    def stop_recording(self):
        with self.lock:
            if not self.recording:
                return
            self.recording = False

        # Stop audio
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        # Final transcription
        if self.audio_buffer:
            self.transcribe_buffer()

        print("[STOPPED]")

    def toggle(self):
        print("[DEBUG] Toggle called")
        if self.recording:
            self.stop_recording()
        else:
            self.start_recording()

    def on_press(self, key):
        print(f"[KEY] {key}")  # DEBUG - show every keypress
        if key == keyboard.Key.cmd or key == keyboard.Key.cmd_l or key == keyboard.Key.cmd_r:
            self.cmd_pressed = True
            print("[DEBUG] Cmd pressed")
        elif hasattr(key, 'char') and key.char == 'd':
            print(f"[DEBUG] 'd' pressed, cmd_pressed={self.cmd_pressed}")
            if self.cmd_pressed:
                threading.Thread(target=self.toggle).start()

    def on_release(self, key):
        if key == keyboard.Key.cmd or key == keyboard.Key.cmd_l or key == keyboard.Key.cmd_r:
            self.cmd_pressed = False

    def run(self):
        print("=" * 50)
        print("    CHUNKED DICTATION (updates every 1.5s)")
        print("=" * 50)
        print()

        self.load_model()

        print("\nReady! Press Cmd+D to toggle.")
        print("Press Ctrl+C to exit.\n")

        with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as listener:
            try:
                listener.join()
            except KeyboardInterrupt:
                print("\nExiting...")
                self.recording = False


if __name__ == "__main__":
    print("Starting...")
    try:
        app = ChunkedDictation()
        print("App created, running...")
        app.run()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
