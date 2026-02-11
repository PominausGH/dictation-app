#!/usr/bin/env python3
"""Test RealtimeSTT with different initialization."""

from RealtimeSTT import AudioToTextRecorder
import time

def on_realtime(text):
    print(f"[LIVE] {text}", flush=True)

def on_stabilized(text):
    print(f"[STABLE] {text}", flush=True)

def on_start():
    print("[Recording started]", flush=True)

def on_stop():
    print("[Recording stopped]", flush=True)

print("Initializing... (this may take a moment)")

recorder = AudioToTextRecorder(
    model="tiny",
    language="en",
    device="cpu",
    compute_type="int8",
    # Realtime settings
    enable_realtime_transcription=True,
    realtime_model_type="tiny",
    realtime_processing_pause=0.05,  # Faster updates
    use_main_model_for_realtime=True,  # Use same model
    # Callbacks
    on_realtime_transcription_update=on_realtime,
    on_realtime_transcription_stabilized=on_stabilized,
    on_recording_start=on_start,
    on_recording_stop=on_stop,
    # VAD settings - more sensitive
    silero_sensitivity=0.5,
    webrtc_sensitivity=3,
    post_speech_silence_duration=0.3,
    min_length_of_recording=0.3,
)

print("\nReady! Speak now...")
print("(Press Ctrl+C to stop)\n")

try:
    while True:
        final = recorder.text()
        if final:
            print(f"\n>>> FINAL: {final}\n")
except KeyboardInterrupt:
    print("\nStopping...")
    recorder.shutdown()
