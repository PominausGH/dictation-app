#!/usr/bin/env python3
"""Detect what keys are being pressed."""

from pynput import keyboard

print("Press keys to see their names. Press Ctrl+C to exit.\n")

def on_press(key):
    print(f"Pressed: {key}")

def on_release(key):
    print(f"Released: {key}")

with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()
