"""Configuration manager for HandGesture Launcher.

Persists user configuration to a JSON file so that gesture mappings and
runtime settings survive application restarts. Configuration lives under
%APPDATA%/HandGestureLauncher on Windows or ~/.handgesture_launcher on
other platforms so the same code can be exercised on any OS while
developing.
"""

from __future__ import annotations

import json
import os
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Optional


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

# Sensible example mappings. Paths are OS-specific placeholders that will
# almost certainly not exist on the user's machine, which is intentional:
# the UI shows them as "unavailable" and prompts the user to update them.
DEFAULT_MAPPINGS: Dict[str, Optional[Dict[str, str]]] = {
    "0": None,  # 0 fingers is reserved as the neutral / reset gesture.
    "1": {"name": "Google Chrome",
          "path": r"C:\Program Files\Google\Chrome\Application\chrome.exe"},
    "2": {"name": "Visual Studio Code",
          "path": r"C:\Users\Public\AppData\Local\Programs\Microsoft VS Code\Code.exe"},
    "3": {"name": "Spotify",
          "path": r"C:\Users\Public\AppData\Roaming\Spotify\Spotify.exe"},
    "4": {"name": "WhatsApp",
          "path": r"C:\Users\Public\AppData\Local\WhatsApp\WhatsApp.exe"},
    "5": {"name": "Calculator",
          "path": r"C:\Windows\System32\calc.exe"},
}

DEFAULT_SETTINGS: Dict[str, Any] = {
    "camera_index": 0,
    "camera_width": 640,
    "camera_height": 480,
    "detection_confidence": 0.7,
    "tracking_confidence": 0.5,
    "stability_frames": 12,       # ~0.4s at 30fps
    "cooldown_seconds": 3.0,
    "require_neutral_reset": True,
    "start_with_windows": False,
    "show_landmarks": True,
    "mirror_preview": True,
}


def _default_config_dir() -> Path:
    """Return per-user config directory, creating it if needed."""
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or str(Path.home())
        return Path(base) / "HandGestureLauncher"
    return Path.home() / ".handgesture_launcher"


class ConfigManager:
    """Load/save JSON configuration with safe defaults and validation."""

    def __init__(self, config_path: Optional[Path] = None) -> None:
        self.config_path: Path = config_path or (_default_config_dir() / "config.json")
        self._data: Dict[str, Any] = {
            "mappings": deepcopy(DEFAULT_MAPPINGS),
            "settings": deepcopy(DEFAULT_SETTINGS),
        }
        self.load()

    # -- persistence --------------------------------------------------------

    def load(self) -> None:
        if not self.config_path.exists():
            self.save()  # create defaults on first run
            return
        try:
            with self.config_path.open("r", encoding="utf-8") as fh:
                loaded = json.load(fh)
        except (OSError, json.JSONDecodeError):
            # Corrupt or unreadable config -> fall back to defaults
            self.save()
            return

        # Merge: keep unknown keys out, fill in missing defaults
        mappings = loaded.get("mappings") or {}
        settings = loaded.get("settings") or {}
        merged_mappings = deepcopy(DEFAULT_MAPPINGS)
        for key in ("0", "1", "2", "3", "4", "5"):
            if key in mappings:
                merged_mappings[key] = mappings[key]
        merged_settings = deepcopy(DEFAULT_SETTINGS)
        merged_settings.update({k: v for k, v in settings.items() if k in DEFAULT_SETTINGS})

        self._data = {"mappings": merged_mappings, "settings": merged_settings}

    def save(self) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.config_path.with_suffix(".json.tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            json.dump(self._data, fh, indent=2, ensure_ascii=False)
        tmp.replace(self.config_path)

    # -- mappings ----------------------------------------------------------

    def get_mapping(self, finger_count: int) -> Optional[Dict[str, str]]:
        return self._data["mappings"].get(str(finger_count))

    def set_mapping(self, finger_count: int, name: str, path: str) -> None:
        self._data["mappings"][str(finger_count)] = {"name": name, "path": path}
        self.save()

    def remove_mapping(self, finger_count: int) -> None:
        self._data["mappings"][str(finger_count)] = None
        self.save()

    def all_mappings(self) -> Dict[str, Optional[Dict[str, str]]]:
        return deepcopy(self._data["mappings"])

    def reset_mappings(self) -> None:
        self._data["mappings"] = deepcopy(DEFAULT_MAPPINGS)
        self.save()

    # -- settings ----------------------------------------------------------

    def get_setting(self, key: str) -> Any:
        return self._data["settings"].get(key, DEFAULT_SETTINGS.get(key))

    def set_setting(self, key: str, value: Any) -> None:
        if key not in DEFAULT_SETTINGS:
            raise KeyError(f"Unknown setting: {key}")
        self._data["settings"][key] = value
        self.save()

    def all_settings(self) -> Dict[str, Any]:
        return deepcopy(self._data["settings"])
