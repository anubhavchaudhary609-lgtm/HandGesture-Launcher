"""Tests for finger counting from synthetic landmarks."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.gesture_detector import HandLandmarks, count_fingers, gesture_to_finger_count  # noqa: E402


def _make_hand(fingers_up: set[int], handedness: str = "Right") -> HandLandmarks:
    """Build 21 synthetic landmark points for a right hand.

    Layout in image coordinates (origin top-left, y grows downward):
      - WRIST is at the bottom (y=0.9)
      - Fingers extend upward when raised (tip.y small) and curl when down.
      - Thumb tip.x < IP.x when extended for a right hand (image space).

    ``fingers_up`` is a subset of {0..4} where 0=thumb, 1=index, 2=middle,
    3=ring, 4=pinky.
    """
    pts = [(0.5, 0.9, 0.0)] * 21

    def set_point(i, x, y):
        pts[i] = (x, y, 0.0)

    # Thumb chain: MCP(2), IP(3), TIP(4)
    if 0 in fingers_up:
        set_point(2, 0.55, 0.75)
        set_point(3, 0.50, 0.70)  # IP
        set_point(4, 0.40, 0.68)  # TIP -- tip.x < IP.x (right hand extended)
    else:
        set_point(2, 0.55, 0.75)
        set_point(3, 0.58, 0.72)
        set_point(4, 0.60, 0.74)  # tip.x > IP.x (curled)

    # Index, middle, ring, pinky (tip, pip) -- extended => tip.y < pip.y
    finger_chains = {
        1: (8, 6, 0.60),   # index
        2: (12, 10, 0.55), # middle
        3: (16, 14, 0.50), # ring
        4: (20, 18, 0.45), # pinky
    }
    for f, (tip_idx, pip_idx, x) in finger_chains.items():
        if f in fingers_up:
            set_point(pip_idx, x, 0.55)
            set_point(tip_idx, x, 0.30)  # tip clearly above pip
        else:
            set_point(pip_idx, x, 0.55)
            set_point(tip_idx, x, 0.70)  # tip below pip (curled)

    return HandLandmarks(points=pts, handedness=handedness)


def test_count_fingers_zero():
    assert count_fingers(_make_hand(set())) == 0


def test_count_fingers_one_index():
    assert count_fingers(_make_hand({1})) == 1


def test_count_fingers_two_peace_sign():
    assert count_fingers(_make_hand({1, 2})) == 2


def test_count_fingers_three():
    assert count_fingers(_make_hand({1, 2, 3})) == 3


def test_count_fingers_four_no_thumb():
    assert count_fingers(_make_hand({1, 2, 3, 4})) == 4


def test_count_fingers_five_open_palm():
    assert count_fingers(_make_hand({0, 1, 2, 3, 4})) == 5


def test_count_fingers_thumb_left_hand():
    # Left hand: thumb extended has tip.x > IP.x. Build manually.
    hand = _make_hand({0}, handedness="Left")
    pts = list(hand.points)
    # Override thumb to have tip.x > IP.x
    pts[3] = (0.50, 0.70, 0.0)
    pts[4] = (0.60, 0.68, 0.0)
    hand.points = pts
    assert count_fingers(hand) == 1


def test_gesture_to_finger_count():
    assert gesture_to_finger_count("3_finger") == 3
    assert gesture_to_finger_count("0_finger") == 0
    assert gesture_to_finger_count(None) is None
    assert gesture_to_finger_count("thumbs_up") is None
