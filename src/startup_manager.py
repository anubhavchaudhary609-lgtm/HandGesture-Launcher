"""Register the application to start with Windows.

Uses the HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run registry
key which does not require administrator rights and is the standard place
for per-user autostart entries.

All functions become no-ops on non-Windows platforms so the app can still
be developed & tested on Linux/macOS.
"""

from __future__ import annotations

import sys
from pathlib import Path

APP_NAME = "HandGestureLauncher"
_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _is_windows() -> bool:
    return sys.platform.startswith("win")


def is_supported() -> bool:
    return _is_windows()


def is_enabled() -> bool:
    if not _is_windows():
        return False
    try:
        import winreg  # type: ignore
    except ImportError:
        return False
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY) as key:
            winreg.QueryValueEx(key, APP_NAME)
        return True
    except FileNotFoundError:
        return False
    except OSError:
        return False


def enable(target_path: str | None = None) -> bool:
    """Register the executable/script to run at Windows logon."""
    if not _is_windows():
        return False
    try:
        import winreg  # type: ignore
    except ImportError:
        return False

    if not target_path:
        # Prefer the frozen exe (when packaged with PyInstaller), otherwise
        # fall back to `pythonw <script>` for a windowed launch.
        if getattr(sys, "frozen", False):
            target_path = sys.executable
        else:
            pyw = Path(sys.executable).with_name("pythonw.exe")
            interp = str(pyw if pyw.exists() else sys.executable)
            script = Path(sys.argv[0]).resolve()
            target_path = f'"{interp}" "{script}"'

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, target_path)
        return True
    except OSError:
        return False


def disable() -> bool:
    if not _is_windows():
        return False
    try:
        import winreg  # type: ignore
    except ImportError:
        return False
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.DeleteValue(key, APP_NAME)
        return True
    except FileNotFoundError:
        return True
    except OSError:
        return False
