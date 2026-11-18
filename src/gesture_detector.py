"""Hand detection + finger counting using MediaPipe.

The engine is deliberately split into two layers:

* ``HandGestureDetector`` runs MediaPipe on a frame and returns a
  ``DetectionResult`` with landmark data.
* ``GestureEngine`` interprets landmarks into a named gesture. The default
  implementation only recognises finger counts (0-5) but the design is
  extensible: register more ``GestureRule`` objects (fist, thumbs up, OK,
  pinch, ...) without touching the rest of the app.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

import numpy as np

try:
    import cv2  # noqa: F401
    import mediapipe as mp
    _MP_AVAILABLE = True
except Exception:  # pragma: no cover - only fails when deps missing
    mp = None
    _MP_AVAILABLE = False


# MediaPipe landmark indices for reference
WRIST = 0
THUMB_TIP, THUMB_IP, THUMB_MCP = 4, 3, 2
INDEX_TIP, INDEX_PIP = 8, 6
MIDDLE_TIP, MIDDLE_PIP = 12, 10
RING_TIP, RING_PIP = 16, 14
PINKY_TIP, PINKY_PIP = 20, 18

FINGER_TIP_PIP = [
    (INDEX_TIP, INDEX_PIP),
    (MIDDLE_TIP, MIDDLE_PIP),
    (RING_TIP, RING_PIP),
    (PINKY_TIP, PINKY_PIP),
]


@dataclass
class HandLandmarks:
    """Normalised landmark coordinates for a single hand."""
    points: List[tuple]                # list of (x, y, z), each 0..1
    handedness: str = "Right"          # "Left" or "Right" from MediaPipe

    def __getitem__(self, idx: int) -> tuple:
        return self.points[idx]


@dataclass
class DetectionResult:
    hand: Optional[HandLandmarks]
    multiple_hands: bool = False
    raw_result: object = None          # raw MediaPipe result (for drawing)


# ---------------------------------------------------------------------------
# Finger counting (pure function, easy to unit-test)
# ---------------------------------------------------------------------------

def count_fingers(hand: HandLandmarks) -> int:
    """Return the number of extended fingers (0..5).

    Uses the classic tip-vs-PIP rule for the four fingers and a
    handedness-aware x-check for the thumb.
    """
    if hand is None or len(hand.points) < 21:
        return 0

    pts = hand.points
    fingers = 0

    # Thumb: compare tip.x to IP.x, direction depends on which hand.
    # MediaPipe reports handedness from the *user's* point of view but the
    # image is often mirrored -> we compare tip to mcp along x.
    thumb_tip_x = pts[THUMB_TIP][0]
    thumb_ip_x = pts[THUMB_IP][0]
    if hand.handedness == "Right":
        if thumb_tip_x < thumb_ip_x:
            fingers += 1
    else:
        if thumb_tip_x > thumb_ip_x:
            fingers += 1

    # For the other four fingers a finger is "up" when the tip is above
    # (smaller y in image coordinates) its PIP joint.
    for tip_idx, pip_idx in FINGER_TIP_PIP:
        if pts[tip_idx][1] < pts[pip_idx][1]:
            fingers += 1

    return max(0, min(5, fingers))


# ---------------------------------------------------------------------------
# Extensible gesture engine
# ---------------------------------------------------------------------------

GestureRuleFn = Callable[[HandLandmarks], Optional[str]]


@dataclass
class GestureEngine:
    """Applies an ordered list of gesture rules and returns the first hit.

    The default rule set only maps finger counts (0..5) to canonical names
    like ``"1_finger"``. Additional rules (fist, thumbs_up, OK, pinch, ...)
    can be registered in the future without changing the rest of the app.
    """

    rules: List[GestureRuleFn] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.rules:
            self.rules = [finger_count_rule]

    def classify(self, hand: Optional[HandLandmarks]) -> Optional[str]:
        if hand is None:
            return None
        for rule in self.rules:
            result = rule(hand)
            if result:
                return result
        return None


def finger_count_rule(hand: HandLandmarks) -> Optional[str]:
    n = count_fingers(hand)
    return f"{n}_finger" if n >= 0 else None


def gesture_to_finger_count(gesture: Optional[str]) -> Optional[int]:
    """Reverse map ``'3_finger'`` -> ``3``. Returns None for other gestures."""
    if not gesture or not gesture.endswith("_finger"):
        return None
    try:
        return int(gesture.split("_", 1)[0])
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# MediaPipe wrapper
# ---------------------------------------------------------------------------

class HandGestureDetector:
    """Wraps MediaPipe Hands and returns a ``DetectionResult`` per frame."""

    def __init__(
        self,
        detection_confidence: float = 0.7,
        tracking_confidence: float = 0.5,
        max_num_hands: int = 2,
    ) -> None:
        if not _MP_AVAILABLE:
            raise RuntimeError(
                "mediapipe is not installed. Please install requirements first.")
        self._mp_hands = mp.solutions.hands
        self._hands = self._mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_num_hands,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence,
        )
        self._mp_draw = mp.solutions.drawing_utils
        self._mp_styles = mp.solutions.drawing_styles

    # ------------------------------------------------------------------
    def process(self, frame_bgr: np.ndarray) -> DetectionResult:
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        result = self._hands.process(rgb)

        hand: Optional[HandLandmarks] = None
        multiple = False
        if result.multi_hand_landmarks:
            multiple = len(result.multi_hand_landmarks) > 1
            # Pick the most prominent hand: largest bounding box area.
            best_idx = 0
            best_area = -1.0
            for i, lms in enumerate(result.multi_hand_landmarks):
                xs = [lm.x for lm in lms.landmark]
                ys = [lm.y for lm in lms.landmark]
                area = (max(xs) - min(xs)) * (max(ys) - min(ys))
                if area > best_area:
                    best_area = area
                    best_idx = i
            lms = result.multi_hand_landmarks[best_idx]
            handedness_label = "Right"
            if result.multi_handedness and len(result.multi_handedness) > best_idx:
                handedness_label = result.multi_handedness[best_idx].classification[0].label
            hand = HandLandmarks(
                points=[(lm.x, lm.y, lm.z) for lm in lms.landmark],
                handedness=handedness_label,
            )
        return DetectionResult(hand=hand, multiple_hands=multiple, raw_result=result)

    # ------------------------------------------------------------------
    def draw(self, frame_bgr: np.ndarray, result: DetectionResult) -> np.ndarray:
        if result.raw_result and result.raw_result.multi_hand_landmarks:
            for lms in result.raw_result.multi_hand_landmarks:
                self._mp_draw.draw_landmarks(
                    frame_bgr,
                    lms,
                    self._mp_hands.HAND_CONNECTIONS,
                    self._mp_styles.get_default_hand_landmarks_style(),
                    self._mp_styles.get_default_hand_connections_style(),
                )
        return frame_bgr

    def close(self) -> None:
        try:
            self._hands.close()
        except Exception:
            pass
