"""Unit tests for gesture_manager.GestureStabilizer.

These are pure-logic tests: no webcam, no MediaPipe, no GUI. They can run
inside CI or on this Linux dev machine.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make ``src`` importable when the tests are executed directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.gesture_manager import GestureStabilizer, StabilityConfig  # noqa: E402


class FakeClock:
    def __init__(self, start: float = 0.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def _feed(stabilizer, gesture, times):
    hits = []
    for _ in range(times):
        result = stabilizer.update(gesture)
        if result is not None:
            hits.append(result)
    return hits


def test_requires_stability_before_confirmation():
    clock = FakeClock()
    stab = GestureStabilizer(StabilityConfig(stability_frames=5, cooldown_seconds=0.0,
                                             require_neutral_reset=False), clock=clock)
    # Only 4 frames -> not enough
    assert _feed(stab, "3_finger", 4) == []
    # 5th frame -> confirmed once
    assert stab.update("3_finger") == "3_finger"


def test_unstable_stream_does_not_confirm():
    clock = FakeClock()
    stab = GestureStabilizer(StabilityConfig(stability_frames=4, cooldown_seconds=0.0,
                                             require_neutral_reset=False), clock=clock)
    seq = ["1_finger", "2_finger", "1_finger", "3_finger", "2_finger"]
    for g in seq:
        assert stab.update(g) is None


def test_cooldown_blocks_second_launch():
    clock = FakeClock()
    stab = GestureStabilizer(StabilityConfig(stability_frames=3, cooldown_seconds=2.0,
                                             require_neutral_reset=False), clock=clock)
    # First confirmation
    for _ in range(3):
        result = stab.update("3_finger")
    assert result == "3_finger"

    # Immediately holding it -> cooldown blocks
    for _ in range(10):
        assert stab.update("3_finger") is None

    # After 2s -> allowed again on the very next update (stability window
    # is already full of "3_finger" from the previous frames).
    clock.advance(2.1)
    assert stab.update("3_finger") == "3_finger"


def test_neutral_reset_required_between_repeats():
    clock = FakeClock()
    stab = GestureStabilizer(StabilityConfig(stability_frames=3, cooldown_seconds=0.0,
                                             require_neutral_reset=True), clock=clock)
    # First "3"
    for _ in range(2):
        stab.update("3_finger")
    assert stab.update("3_finger") == "3_finger"

    # Without seeing neutral, another stable "3" should NOT re-fire.
    for _ in range(10):
        assert stab.update("3_finger") is None

    # After neutral gesture is seen, next stable "3" fires again.
    for _ in range(3):
        stab.update("0_finger")
    for _ in range(2):
        stab.update("3_finger")
    assert stab.update("3_finger") == "3_finger"


def test_switching_gesture_does_not_need_neutral_reset():
    clock = FakeClock()
    stab = GestureStabilizer(StabilityConfig(stability_frames=3, cooldown_seconds=0.0,
                                             require_neutral_reset=True), clock=clock)
    for _ in range(2):
        stab.update("2_finger")
    assert stab.update("2_finger") == "2_finger"

    # Different gesture: should fire without seeing neutral first.
    for _ in range(2):
        stab.update("4_finger")
    assert stab.update("4_finger") == "4_finger"


def test_neutral_gesture_itself_never_fires():
    clock = FakeClock()
    stab = GestureStabilizer(StabilityConfig(stability_frames=3, cooldown_seconds=0.0,
                                             require_neutral_reset=False), clock=clock)
    for _ in range(20):
        assert stab.update("0_finger") is None


def test_none_gesture_never_fires():
    clock = FakeClock()
    stab = GestureStabilizer(StabilityConfig(stability_frames=3, cooldown_seconds=0.0,
                                             require_neutral_reset=False), clock=clock)
    for _ in range(20):
        assert stab.update(None) is None
