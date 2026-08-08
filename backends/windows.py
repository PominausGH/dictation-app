"""Windows backend — pynput for the Alt+D hotkey and typing, pystray for notifications."""

import logging
import threading
from typing import Callable, Optional

from pynput import keyboard

from .base import Backend

log = logging.getLogger("voxtty.windows")


class WindowsBackend(Backend):
    def __init__(self) -> None:
        self._controller = keyboard.Controller()
        self._icon = None

    # ── Readiness ────────────────────────────────────────────────────────────

    def check_ready(self) -> tuple[bool, Optional[str]]:
        return True, None

    # ── Tray / notifications ─────────────────────────────────────────────────

    def attach_tray(self, icon) -> None:
        self._icon = icon

    def notify(self, summary: str, body: str = "") -> None:
        if self._icon is None:
            return
        try:
            self._icon.notify(body, summary)
        except Exception:
            pass

    # ── Typing ───────────────────────────────────────────────────────────────

    def type_text(self, text: str) -> None:
        if not text:
            return
        try:
            self._controller.type(text)
        except Exception as e:
            log.error(f"pynput type failed: {e}")

    # ── Keyboard ─────────────────────────────────────────────────────────────

    def run_hotkey_listener(
        self, on_toggle: Callable[[], None], should_stop: Callable[[], bool]
    ) -> None:
        alt_pressed = False

        def on_press(key) -> None:
            nonlocal alt_pressed
            if key in (keyboard.Key.alt_l, keyboard.Key.alt_r):
                alt_pressed = True
            elif alt_pressed and getattr(key, "char", None) and key.char.lower() == "d":
                threading.Thread(target=on_toggle, daemon=True).start()

        def on_release(key) -> None:
            nonlocal alt_pressed
            if key in (keyboard.Key.alt_l, keyboard.Key.alt_r):
                alt_pressed = False

        listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        listener.start()
        try:
            while not should_stop() and listener.is_alive():
                listener.join(timeout=0.5)
        finally:
            listener.stop()
