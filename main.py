"""HandGesture Launcher — entry point."""

from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path


def _ensure_project_on_path() -> None:
    """Make ``src`` importable when the script is run directly or as an exe."""
    here = Path(__file__).resolve().parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))


def main() -> int:
    _ensure_project_on_path()
    try:
        from src.gui.app import run
        run()
        return 0
    except Exception:
        traceback.print_exc()
        # Best-effort fatal error popup so a packaged .exe doesn't just close.
        try:
            from tkinter import messagebox, Tk
            root = Tk()
            root.withdraw()
            messagebox.showerror(
                "HandGesture Launcher",
                "The application crashed.\n\n"
                + traceback.format_exc(limit=3),
            )
            root.destroy()
        except Exception:
            pass
        return 1


if __name__ == "__main__":
    sys.exit(main())
