"""Thin wrapper around cv2.VideoCapture with camera discovery."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

try:
    import cv2
    _CV2 = True
except Exception:  # pragma: no cover
    cv2 = None
    _CV2 = False


@dataclass
class CameraInfo:
    index: int
    label: str


class CameraManager:
    def __init__(self, width: int = 640, height: int = 480) -> None:
        self.width = width
        self.height = height
        self._cap = None
        self._index: Optional[int] = None

    # ------------------------------------------------------------------
    @staticmethod
    def list_cameras(max_probe: int = 5) -> List[CameraInfo]:
        """Probe the first few indices and return which ones open."""
        cams: List[CameraInfo] = []
        if not _CV2:
            return cams
        for idx in range(max_probe):
            cap = cv2.VideoCapture(idx)
            ok = cap.isOpened()
            cap.release()
            if ok:
                cams.append(CameraInfo(idx, f"Camera {idx}"))
        if not cams:
            cams.append(CameraInfo(0, "Camera 0"))
        return cams

    # ------------------------------------------------------------------
    def open(self, index: int) -> bool:
        if not _CV2:
            return False
        self.close()
        cap = cv2.VideoCapture(index)
        if not cap.isOpened():
            return False
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self._cap = cap
        self._index = index
        return True

    def is_open(self) -> bool:
        return self._cap is not None and self._cap.isOpened()

    def read(self):
        """Return (ok, frame_bgr) or (False, None) if unavailable."""
        if not self.is_open():
            return False, None
        return self._cap.read()

    def close(self) -> None:
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                pass
        self._cap = None
        self._index = None
