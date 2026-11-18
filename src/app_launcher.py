"""Launch a Windows executable safely.

* Validates the path exists and is a file.
* Uses ``os.startfile`` on Windows so shell associations & shortcuts (.lnk)
  work correctly; falls back to ``subprocess.Popen`` on other platforms
  (useful during development on Linux/macOS).
* Never raises to the caller: always returns ``LaunchResult``.
"""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class LaunchResult:
    success: bool
    message: str
    path: Optional[str] = None


def launch(path: str) -> LaunchResult:
    if not path:
        return LaunchResult(False, "No application path configured.")
    p = Path(path).expanduser()
    if not p.exists():
        return LaunchResult(
            False,
            f"Application not found:\n{path}\n\nPlease update the path in Settings.",
            str(p),
        )
    if not p.is_file():
        return LaunchResult(False, f"Path is not a file:\n{path}", str(p))

    try:
        if sys.platform.startswith("win"):
            # os.startfile respects file associations and works for .exe/.lnk
            os.startfile(str(p))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(p)])
        else:
            # Linux: try to run it directly, or use xdg-open for non-exec.
            if os.access(str(p), os.X_OK):
                subprocess.Popen([str(p)])
            else:
                subprocess.Popen(["xdg-open", str(p)])
    except Exception as exc:  # pragma: no cover - platform specific
        return LaunchResult(False, f"Failed to launch application:\n{exc}", str(p))

    return LaunchResult(True, f"Launched {p.name}", str(p))


def quote_for_display(path: str) -> str:
    return shlex.quote(path)
