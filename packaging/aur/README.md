# AUR packaging (build-tested, not yet published)

This directory is a `voxtty-git` PKGBUILD. It has been built and smoke-tested end-to-end in a clean Arch Linux container (`makepkg -s`, plus importing every runtime dependency with a virtual X server so `pystray`'s tray-icon backend actually loads) — but it has never been run on real Arch hardware, and it is not yet published to the AUR.

## Confirmed by testing

- `depends` (`python-gobject`, `gtk3`, `libnotify`, `libayatana-appindicator`) are all correct and sufficient — `pystray` loads its `_appindicator` backend cleanly with these installed. `libayatana-appindicator` is an official `extra` package, not AUR-only.
- `openwakeword`'s Linux dependency `tflite-runtime` publishes no wheels for Python 3.13+, so a plain `pip install -r requirements.txt` fails outright on Arch (which always ships current Python). Fix: install `openwakeword` with `--no-deps` and supply its other real dependencies by hand — openwakeword itself falls back to `onnxruntime` at import time when `tflite_runtime` is missing, and `openwakeword.utils.download_models()` fetches both `.tflite` and `.onnx` copies of every model, so the fallback is fully functional, not degraded.
- `webrtcvad` imports `pkg_resources`, which `setuptools` stopped bundling somewhere between 80.10.2 and 83.0.0. Fix: pin `setuptools<81` in the build venv.
- `pkgver()`'s `git rev-list --count` / `git rev-parse --short` scheme works correctly against the real repo.
- `voxtty.py` compiles and every import in `requirements.txt` resolves under the packaged venv.
- The `ExecStart` path in `voxtty.service` (`/opt/voxtty/venv/bin/python /opt/voxtty/voxtty.py`) matches `package()`'s actual install layout.
- `.SRCINFO` has been generated and committed.

## Still unverified

- Never run on real Arch hardware — only in a headless Arch Linux Docker container (built with `pacman -S base-devel` + the package's own `depends`/`makedepends`, non-root build user, `Xvfb` for the display-dependent import check). Hotkey capture (`ydotool`/`evdev`), microphone capture (`pyaudio`/`portaudio`), and the actual tray icon rendering were never exercised against real hardware/session.
- The venv-in-package approach (pip-installing `faster-whisper`/`openwakeword`/etc. from PyPI rather than declaring Arch `depends`) works, but the resulting package is large (~170 MB compressed) and slow to build — that tradeoff hasn't been validated against AUR community norms/reviewer expectations.
- `makepkg`'s packaging step reproducibly hits `bsdtar: opt/voxtty/venv/bin/𝜋thon: Can't translate pathname ... to UTF-8` — this is a genuine CPython 3.14 feature (`venv/__init__.py` adds a `𝜋thon` symlink alongside `python` on UTF-8 filesystems for this Python version specifically), not a bug in this PKGBUILD. `bsdtar` just skips that one file; harmless, since nothing depends on it.

## Publishing without real Arch hardware

No Arch hardware or VM is available to run the hotkey/microphone/tray-icon smoke test in a real session before the first publish, so this is going out with only the container-verified build/import guarantees above — real hotkey capture, mic capture, and tray rendering are unconfirmed. This is normal practice for a new AUR `-git` package: publish, then let the AUR comment thread be the feedback loop for anything that only shows up on real hardware. Keep an eye on comments after the first few installs.

## To actually publish this

1. Create an AUR account at https://aur.archlinux.org and add an SSH key — this has to be done by a human, not from here.
2. `git clone ssh://aur@aur.archlinux.org/voxtty-git.git`, copy `PKGBUILD`, `voxtty.service`, `voxtty.install`, `.SRCINFO` into it, commit, push.
