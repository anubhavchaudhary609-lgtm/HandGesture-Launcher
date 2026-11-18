"""Stability confirmation and cooldown logic.

Kept intentionally UI- and MediaPipe-agnostic so the whole file can be
unit-tested without a webcam.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from typing import Callable, Deque, Optional


@dataclass
class StabilityConfig:
    stability_frames: int = 12
    cooldown_seconds: float = 3.0
    require_neutral_reset: bool = True
    neutral_gesture: str = "0_finger"


class GestureStabilizer:
    """Confirms a gesture only once it has been stable for N consecutive
    updates AND the cooldown has elapsed AND (optionally) the user has
    returned to a neutral gesture since the last confirmation."""

    def __init__(self, config: StabilityConfig, clock: Callable[[], float] = time.monotonic) -> None:
        self.config = config
        self._clock = clock
        self._history: Deque[Optional[str]] = deque(maxlen=max(1, config.stability_frames))
        self._last_confirmed: Optional[str] = None
        self._last_confirmed_at: float = -1e9
        self._neutral_seen_since_last: bool = True  # allow first launch

    # ------------------------------------------------------------------
    def update_config(self, config: StabilityConfig) -> None:
        self.config = config
        self._history = deque(self._history, maxlen=max(1, config.stability_frames))

    # ------------------------------------------------------------------
    def update(self, gesture: Optional[str]) -> Optional[str]:
        """Feed the latest gesture. Return the confirmed gesture (only on
        the frame it becomes confirmed), otherwise None."""
        self._history.append(gesture)

        # Track neutral reset
        if gesture == self.config.neutral_gesture:
            self._neutral_seen_since_last = True

        # Need a full window of identical, non-None readings
        if len(self._history) < self.config.stability_frames:
            return None
        first = self._history[0]
        if first is None:
            return None
        if any(g != first for g in self._history):
            return None

        # Never treat the neutral gesture itself as a launch trigger
        if first == self.config.neutral_gesture:
            return None

        # Cooldown gate
        now = self._clock()
        if now - self._last_confirmed_at < self.config.cooldown_seconds:
            return None

        # Optional: require the user to return to the neutral gesture
        # between two identical confirmations.
        if self.config.require_neutral_reset and first == self._last_confirmed:
            if not self._neutral_seen_since_last:
                return None

        self._last_confirmed = first
        self._last_confirmed_at = now
        self._neutral_seen_since_last = False
        return first

    # ------------------------------------------------------------------
    def cooldown_remaining(self) -> float:
        remaining = self.config.cooldown_seconds - (self._clock() - self._last_confirmed_at)
        return max(0.0, remaining)

    def reset(self) -> None:
        self._history.clear()
        self._last_confirmed = None
        self._last_confirmed_at = -1e9
        self._neutral_seen_since_last = True
