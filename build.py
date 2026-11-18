"""PyInstaller build script for HandGesture Launcher.

Run on a Windows machine after installing requirements:

    python build.py

Produces ``dist/HandGestureLauncher.exe`` (one-file, windowed).
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
BUILD = ROOT / "build_tmp"


def main() -> int:
    if shutil.which("pyinstaller") is None:
        print("PyInstaller is not installed. Run: pip install pyinstaller")
        return 2

    # MediaPipe ships large model/data files that must be bundled.
    try:
        import mediapipe
        mp_dir = Path(mediapipe.__file__).parent
    except ImportError:
        print("mediapipe is not installed. Run: pip install -r requirements.txt")
        return 2

    add_data_sep = ";" if sys.platform.startswith("win") else ":"
    add_data = f"{mp_dir}{add_data_sep}mediapipe"

    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name", "HandGestureLauncher",
        "--collect-all", "mediapipe",
        "--collect-all", "customtkinter",
        "--collect-submodules", "cv2",
        "--add-data", add_data,
        "--distpath", str(DIST),
        "--workpath", str(BUILD),
        str(ROOT / "main.py"),
    ]

    icon = ROOT / "assets" / "icon.ico"
    if icon.exists():
        cmd += ["--icon", str(icon)]

    print("Running:", " ".join(cmd))
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
