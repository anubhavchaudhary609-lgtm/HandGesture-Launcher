"""Tests for app_launcher — verifies error handling paths without
actually launching apps."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.app_launcher import launch  # noqa: E402


def test_launch_empty_path():
    result = launch("")
    assert result.success is False
    assert "No application path" in result.message


def test_launch_missing_path(tmp_path):
    missing = tmp_path / "does_not_exist.exe"
    result = launch(str(missing))
    assert result.success is False
    assert "not found" in result.message.lower()


def test_launch_directory_is_not_a_file(tmp_path):
    result = launch(str(tmp_path))
    assert result.success is False
    assert "not a file" in result.message.lower()
