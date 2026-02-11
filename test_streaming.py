#!/usr/bin/env python3
"""Minimal test to verify RealtimeSTT streaming callbacks work."""

from RealtimeSTT import AudioToTextRecorder
import time

def on_realtime(text):
    print(f"[REALTIME] {text}")

def on_final(text):
    print(f"[FINAL] {text}")

print("Starting recorder...")
print("Speak for 5 seconds, watch for [REALTIME] messages...")
print()

recorder = AudioToTextRecorder(
    model="tiny",
    language="en",
    device="cpu",
    enable_realtime_transcription=True,
    realtime_model_type="tiny",
    realtime_processing_pause=0.1,
    on_realtime_transcription_update=on_realtime,
)

print("Recorder ready. Listening...")

# Get one utterance
final = recorder.text()
print(f"\nFinal result: {final}")

recorder.shutdown()
print("Done.")
