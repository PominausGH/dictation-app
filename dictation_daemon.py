#!/usr/bin/env python3
"""
Dictation Daemon - Runs in background, toggles via signal or file.
"""

import subprocess
import threading
import time
import os
import sys
import signal
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from text_differ import TextDiffer

SAMPLE_RATE = 16000
CHUNK_DURATION = 1.0  # Shorter chunks for faster response
STATE_FILE = "/tmp/dictation_state"
PID_FILE = "/tmp/dictation.pid"


class DictationDaemon:
    def __init__(self):
        self.recording = False
        self.running = True
        self.audio_buffer = []
        self.differ = TextDiffer(max_backspaces=20)
        self.model = None
        self.stream = None

    def load_model(self):
        # "tiny" - fastest, transcribes in ~2 seconds
        self.model = WhisperModel("tiny", device="cpu", compute_type="int8")

    def notify(self, message):
        """Show desktop notification."""
        try:
            subprocess.run(["notify-send", "-t", "1000", "Dictation", message],
                         capture_output=True, timeout=1)
        except:
            pass

    def type_text(self, text: str):
        if not text:
            return
        try:
            subprocess.run(["ydotool", "type", "--", text], check=True, capture_output=True)
        except:
            pass

    def type_backspaces(self, count: int):
        if count <= 0:
            return
        try:
            for _ in range(count):
                subprocess.run(["ydotool", "key", "14:1", "14:0"], check=True, capture_output=True)
        except:
            pass

    def audio_callback(self, indata, frames, time_info, status):
        if self.recording:
            self.audio_buffer.append(indata.copy())

    def transcribe_buffer(self):
        if not self.audio_buffer:
            return

        audio = np.concatenate(self.audio_buffer, axis=0).flatten()

        if np.abs(audio).max() < 0.01:
            return

        segments, _ = self.model.transcribe(
            audio, beam_size=1, language="en",
            without_timestamps=True, vad_filter=False,
        )
        text = " ".join([s.text for s in segments]).strip()

        if not text:
            return

        backspaces, new_text = self.differ.calculate_diff(text)
        if backspaces is None:
            return

        if backspaces > 0:
            self.type_backspaces(backspaces)

        if new_text:
            self.type_text(new_text)
            self.differ.update(text)

    def transcription_loop(self):
        while self.recording:
            time.sleep(CHUNK_DURATION)
            if self.recording and self.audio_buffer:
                self.transcribe_buffer()

    def start_recording(self):
        if self.recording:
            return

        self.recording = True
        self.audio_buffer = []
        self.differ.reset()

        self.stream = sd.InputStream(
            samplerate=SAMPLE_RATE, channels=1,
            dtype=np.float32, callback=self.audio_callback,
            device=6  # Logitech BRIO webcam mic
        )
        self.stream.start()

        threading.Thread(target=self.transcription_loop, daemon=True).start()
        self.notify("🎤 Recording...")

    def stop_recording(self):
        if not self.recording:
            return

        # Brief delay to capture trailing audio while still recording
        time.sleep(0.3)

        self.recording = False

        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        # Final transcription of all remaining audio
        if self.audio_buffer:
            self.transcribe_buffer()

        self.notify("⏹️ Stopped")

    def toggle(self):
        if self.recording:
            self.stop_recording()
        else:
            self.start_recording()

    def handle_signal(self, signum, frame):
        if signum == signal.SIGUSR1:
            self.toggle()
        elif signum in (signal.SIGTERM, signal.SIGINT):
            self.stop_recording()
            self.running = False

    def check_toggle_file(self):
        """Check if toggle was requested via file."""
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)
            return True
        return False

    def run(self):
        # Write PID file
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))

        # Set up signal handlers
        signal.signal(signal.SIGUSR1, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)
        signal.signal(signal.SIGINT, self.handle_signal)

        self.load_model()
        self.notify("Dictation ready")

        # Main loop - check for toggle requests
        while self.running:
            if self.check_toggle_file():
                self.toggle()
            time.sleep(0.1)

        # Cleanup
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)


if __name__ == "__main__":
    daemon = DictationDaemon()
    daemon.run()
