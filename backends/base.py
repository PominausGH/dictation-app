"""Platform backend interface — hotkey listening, typing, notifications."""

import abc
from typing import Callable, Optional


class Backend(abc.ABC):
    @abc.abstractmethod
    def check_ready(self) -> tuple[bool, Optional[str]]:
        """Preflight gate, called once from VoxttyApp.run(). Never raises."""

    @abc.abstractmethod
    def type_text(self, text: str) -> None:
        """Type literal text into the focused window. Never raises — logs and swallows."""

    @abc.abstractmethod
    def notify(self, summary: str, body: str = "") -> None:
        """Best-effort desktop notification. Never raises — logs and swallows."""

    @abc.abstractmethod
    def run_hotkey_listener(
        self, on_toggle: Callable[[], None], should_stop: Callable[[], bool]
    ) -> None:
        """Blocking loop run on its own daemon thread.

        Calls on_toggle() when Alt+D fires. Returns once should_stop() is true
        (polled, not pushed).
        """

    def attach_tray(self, icon) -> None:
        """Optional hook, called once after the tray icon exists, before tray.run().

        Default no-op. Backends that notify through the tray icon (e.g. Windows)
        override this to stash the icon for later use in notify().
        """
