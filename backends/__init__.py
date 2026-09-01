"""Platform backend factory — picks the right Backend implementation for sys.platform."""

import sys

from .base import Backend


def get_backend(cfg: dict | None = None) -> Backend:
    cfg = cfg or {}
    if sys.platform.startswith("linux"):
        from .linux import LinuxBackend
        return LinuxBackend(key_delay_ms=cfg.get("type_key_delay_ms", 0))
    if sys.platform == "win32":
        from .windows import WindowsBackend
        return WindowsBackend()
    raise RuntimeError(f"Unsupported platform: {sys.platform}")
