"""Tests for ConfigManager JSON persistence."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config_manager import ConfigManager, DEFAULT_MAPPINGS, DEFAULT_SETTINGS  # noqa: E402


def test_first_run_creates_defaults(tmp_path):
    cfg_path = tmp_path / "config.json"
    cm = ConfigManager(config_path=cfg_path)
    assert cfg_path.exists()
    data = json.loads(cfg_path.read_text())
    assert set(data["mappings"].keys()) == set(DEFAULT_MAPPINGS.keys())
    assert set(data["settings"].keys()) == set(DEFAULT_SETTINGS.keys())
    assert cm.get_setting("stability_frames") == DEFAULT_SETTINGS["stability_frames"]


def test_set_and_remove_mapping(tmp_path):
    cfg_path = tmp_path / "config.json"
    cm = ConfigManager(config_path=cfg_path)
    cm.set_mapping(3, "Spotify", "/tmp/spotify")
    assert cm.get_mapping(3) == {"name": "Spotify", "path": "/tmp/spotify"}

    # Reload from disk
    cm2 = ConfigManager(config_path=cfg_path)
    assert cm2.get_mapping(3) == {"name": "Spotify", "path": "/tmp/spotify"}

    cm2.remove_mapping(3)
    assert cm2.get_mapping(3) is None
    cm3 = ConfigManager(config_path=cfg_path)
    assert cm3.get_mapping(3) is None


def test_reset_mappings(tmp_path):
    cfg_path = tmp_path / "config.json"
    cm = ConfigManager(config_path=cfg_path)
    cm.set_mapping(1, "X", "/tmp/x")
    cm.reset_mappings()
    assert cm.get_mapping(1) == DEFAULT_MAPPINGS["1"]


def test_unknown_setting_rejected(tmp_path):
    cm = ConfigManager(config_path=tmp_path / "config.json")
    try:
        cm.set_setting("nope", 42)
    except KeyError:
        return
    raise AssertionError("Expected KeyError for unknown setting")


def test_corrupt_file_falls_back_to_defaults(tmp_path):
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text("{ this is : not json")
    cm = ConfigManager(config_path=cfg_path)
    assert cm.get_setting("cooldown_seconds") == DEFAULT_SETTINGS["cooldown_seconds"]
