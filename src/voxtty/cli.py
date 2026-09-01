"""Command-line entry point.

Deliberately imports nothing heavy at module level. `--version` and the
service commands must work even when the audio/ML stack is missing or
broken — that is exactly when someone needs to run them.
"""

import argparse

from . import __version__


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="voxtty",
        description="Private, local-first voice dictation. Press Alt+D, speak, and "
                    "your words are typed into the focused app.",
    )
    parser.add_argument("--version", action="version", version=f"voxtty {__version__}")
    parser.add_argument(
        "--install-service", action="store_true",
        help="register Voxtty to start automatically at login, and start it now",
    )
    parser.add_argument(
        "--uninstall-service", action="store_true",
        help="stop Voxtty and remove the autostart registration",
    )
    args = parser.parse_args()

    if args.install_service or args.uninstall_service:
        # Only the backend is needed here, not the transcription stack.
        from .backends import get_backend

        backend = get_backend()
        ok, msg = (
            backend.install_service() if args.install_service else backend.uninstall_service()
        )
        print(msg)
        raise SystemExit(0 if ok else 1)

    try:
        from .app import main as run_app
    except ImportError as e:
        raise SystemExit(
            f"Voxtty could not start: {e}\n"
            "A dependency is missing or failed to build. On Debian/Ubuntu:\n"
            "  sudo apt install gcc python3-dev portaudio19-dev ydotool\n"
            "then reinstall Voxtty."
        )
    run_app()
