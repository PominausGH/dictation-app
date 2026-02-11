#!/usr/bin/env python3
"""Test RealtimeSTT with Alt+D toggle."""

from RealtimeSTT import AudioToTextRecorder
from pynput import keyboard
import threading

recording = False
recorder = None

def on_realtime(text):
    print(f"[LIVE] {text}", flush=True)

def on_start():
    print("[Recording started]", flush=True)

def on_stop():
    print("[Recording stopped]", flush=True)

def record_loop():
    global recording, recorder
    while recording:
        final = recorder.text()
        if final:
            print(f"\n>>> FINAL: {final}\n")

def toggle():
    global recording, recorder
    if recording:
        recording = False
        print("[STOPPED]")
    else:
        recording = True
        print("[STARTED] Speak now...")
        threading.Thread(target=record_loop, daemon=True).start()

# Track Cmd key
cmd_pressed = False

def on_press(key):
    global cmd_pressed
    if key == keyboard.Key.cmd or key == keyboard.Key.cmd_l or key == keyboard.Key.cmd_r:
        cmd_pressed = True
    elif hasattr(key, 'char') and key.char == 'd' and cmd_pressed:
        toggle()

def on_release(key):
    global cmd_pressed
    if key == keyboard.Key.cmd or key == keyboard.Key.cmd_l or key == keyboard.Key.cmd_r:
        cmd_pressed = False

print("Initializing recorder...")

recorder = AudioToTextRecorder(
    model="tiny",
    language="en",
    device="cpu",
    enable_realtime_transcription=True,
    realtime_model_type="tiny",
    realtime_processing_pause=0.05,
    on_realtime_transcription_update=on_realtime,
    on_recording_start=on_start,
    on_recording_stop=on_stop,
    silero_sensitivity=0.5,
    post_speech_silence_duration=0.3,
)

print("\nReady! Press Cmd+D to toggle recording.")
print("Press Ctrl+C to exit.\n")

with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    try:
        listener.join()
    except KeyboardInterrupt:
        print("\nExiting...")
        recorder.shutdown()
