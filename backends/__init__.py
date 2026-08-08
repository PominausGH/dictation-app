"""Platform backend factory — picks the right Backend implementation for sys.platform."""

import sys

from .base import Backend


def get_backend() -> Backend:
    if sys.platform.startswith("linux"):
        from .linux import LinuxBackend
        return LinuxBackend()
    if sys.platform == "win32":
        from .windows import WindowsBackend
        return WindowsBackend()
    raise RuntimeError(f"Unsupported platform: {sys.platform}")
