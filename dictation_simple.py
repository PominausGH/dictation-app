#!/usr/bin/env python3
"""
Simple Dictation - Press Enter to toggle recording.
Transcribes every 1.5 seconds while speaking.
"""

import subprocess
import threading
import time
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from text_differ import TextDiffer

SAMPLE_RATE = 16000
CHUNK_DURATION = 2.0  # Shorter chunks to avoid losing end


class SimpleDictation:
    def __init__(self):
        self.recording = False
        self.audio_buffer = []
        self.differ = TextDiffer(max_backspaces=20)
        self.model = None
        self.stream = None

    def load_model(self):
        print("Loading Whisper model (medium)...")
        self.model = WhisperModel("medium", device="cpu", compute_type="int8")
        print("Model loaded!")

    def type_text(self, text: str):
        if not text:
            return
        try:
            subprocess.run(["ydotool", "type", "--", text], check=True, capture_output=True)
        except Exception as e:
            print(f"[ERROR] {e}")

    def type_backspaces(self, count: int):
        if count <= 0:
            return
        try:
            for _ in range(count):
                subprocess.run(["ydotool", "key", "14:1", "14:0"], check=True, capture_output=True)
        except Exception as e:
            print(f"[ERROR] {e}")

    def audio_callback(self, indata, frames, time_info, status):
        if self.recording:
            self.audio_buffer.append(indata.copy())

    def transcribe_buffer(self):
        if not self.audio_buffer:
            return

        audio = np.concatenate(self.audio_buffer, axis=0).flatten()

        if np.abs(audio).max() < 0.01:
            print("[quiet]")
            return

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

        backspaces, new_text = self.differ.calculate_diff(text)

        if backspaces is None:
            print("[WARN] Large correction skipped")
            return

        if backspaces > 0:
            self.type_backspaces(backspaces)

        if new_text:
            self.type_text(new_text)
            self.differ.update(text)

        print(f"[{len(self.audio_buffer)} chunks] {text}")

    def transcription_loop(self):
        while self.recording:
            time.sleep(CHUNK_DURATION)
            if self.recording and self.audio_buffer:
                self.transcribe_buffer()

    def start_recording(self):
        self.recording = True
        self.audio_buffer = []
        self.differ.reset()

        print("\n>>> RECORDING - speak now! Press Enter to stop.\n")

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
        self.recording = False

        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        # Final transcription
        if self.audio_buffer:
            print("\n[Final transcription...]")
            self.transcribe_buffer()

        print("\n>>> STOPPED\n")

    def run(self):
        print("=" * 50)
        print("    SIMPLE DICTATION (Enter to toggle)")
        print("=" * 50)
        print()

        self.load_model()

        print("\nPress Enter to start/stop recording.")
        print("Press Ctrl+C to exit.\n")

        try:
            while True:
                input(">> Press Enter to START recording: ")
                self.start_recording()
                input()  # Wait for Enter to stop
                self.stop_recording()
        except KeyboardInterrupt:
            print("\nExiting...")
            self.recording = False


if __name__ == "__main__":
    app = SimpleDictation()
    app.run()
