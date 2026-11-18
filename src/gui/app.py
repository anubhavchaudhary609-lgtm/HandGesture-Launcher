"""Main HandGestureLauncher window.

Runs webcam capture + MediaPipe processing on a background thread.
All UI updates are marshalled back to the main thread via after().
"""

from __future__ import annotations

import threading
import time
import traceback
from queue import Empty, Queue
from tkinter import messagebox
from typing import Optional

import customtkinter as ctk
from PIL import Image

from src import app_launcher
from src.camera import CameraManager
from src.config_manager import ConfigManager
from src.gesture_detector import (
    HandGestureDetector,
    GestureEngine,
    gesture_to_finger_count,
)
from src.gesture_manager import GestureStabilizer, StabilityConfig
from src.gui.dashboard import DashboardFrame
from src.gui.settings import SettingsFrame


try:
    import cv2
    _CV2 = True
except Exception:
    cv2 = None
    _CV2 = False


class HandGestureApp(ctk.CTk):

    def __init__(self) -> None:
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("HandGesture Launcher")
        self.geometry("1080x680")
        self.minsize(960, 620)

        self.config_mgr = ConfigManager()

        # Worker thread state
        self._worker: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._ui_queue: Queue = Queue()
        self._settings_dirty = threading.Event()

        self._build_ui()
        self._poll_ui_queue()

    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------

    def _build_ui(self) -> None:

        header = ctk.CTkFrame(self, height=64, corner_radius=0)
        header.pack(fill="x")

        ctk.CTkLabel(
            header,
            text="✋  HANDGESTURE LAUNCHER",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(side="left", padx=20, pady=14)

        self._start_btn = ctk.CTkButton(
            header,
            text="Start detection",
            width=140,
            command=self.start_detection,
        )
        self._start_btn.pack(side="right", padx=(6, 20), pady=14)

        self._stop_btn = ctk.CTkButton(
            header,
            text="Stop detection",
            width=140,
            fg_color="#8B2E2E",
            hover_color="#6E2323",
            command=self.stop_detection,
            state="disabled",
        )
        self._stop_btn.pack(side="right", padx=6, pady=14)

        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.tabs.add("Dashboard")
        self.tabs.add("Settings")

        self.dashboard = DashboardFrame(self.tabs.tab("Dashboard"))
        self.dashboard.pack(fill="both", expand=True)

        self.settings = SettingsFrame(
            self.tabs.tab("Settings"),
            self.config_mgr,
            on_settings_changed=self._settings_changed,
        )
        self.settings.pack(fill="both", expand=True)

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _settings_changed(self) -> None:
        self._settings_dirty.set()

    # ---------------------------------------------------------
    # Detection controls
    # ---------------------------------------------------------

    def start_detection(self) -> None:

        if self._worker and self._worker.is_alive():
            return

        if not _CV2:
            messagebox.showerror(
                "Missing dependency",
                "OpenCV (cv2) is not available. Please install requirements.txt.",
            )
            return

        self._stop_event.clear()

        self._worker = threading.Thread(
            target=self._detection_loop,
            daemon=True,
        )
        self._worker.start()

        self._start_btn.configure(state="disabled")
        self._stop_btn.configure(state="normal")

    def stop_detection(self) -> None:

        self._stop_event.set()

        if self._worker:
            self._worker.join(timeout=2.5)

        self._worker = None

        self._start_btn.configure(state="normal")
        self._stop_btn.configure(state="disabled")

        self.dashboard.set_video_image(None)
        self.dashboard.set_camera_status(False, "Idle")
        self.dashboard.set_status("Stopped", "Detection paused.")

    # ---------------------------------------------------------
    # Main detection loop
    # ---------------------------------------------------------

    def _detection_loop(self) -> None:

        settings = self.config_mgr.all_settings()

        camera = CameraManager(
            width=settings["camera_width"],
            height=settings["camera_height"],
        )

        if not camera.open(settings["camera_index"]):
            self._push_status(
                "Camera error",
                "Could not open the webcam. Check that a camera is connected "
                "and not in use by another program.",
                camera_active=False,
                color="#E06C75",
            )
            return

        try:
            detector = HandGestureDetector(
                detection_confidence=float(settings["detection_confidence"]),
                tracking_confidence=float(settings["tracking_confidence"]),
                max_num_hands=2,
            )

        except Exception as exc:

            self._push_status(
                "Detector error",
                f"MediaPipe failed to initialise:\n{exc}",
                camera_active=False,
                color="#E06C75",
            )

            camera.close()
            return

        engine = GestureEngine()

        stabilizer = GestureStabilizer(
            StabilityConfig(
                stability_frames=int(settings["stability_frames"]),
                cooldown_seconds=float(settings["cooldown_seconds"]),
                require_neutral_reset=bool(settings["require_neutral_reset"]),
            )
        )

        # Fist gesture state
        fist_frames = 0
        fist_triggered = False
        v_sign_triggered = False

        self._push(camera_active=True, camera_message="")

        last_frame_time = time.monotonic()

        try:

            while not self._stop_event.is_set():

                # Live settings updates
                if self._settings_dirty.is_set():

                    self._settings_dirty.clear()
                    s = self.config_mgr.all_settings()

                    stabilizer.update_config(
                        StabilityConfig(
                            stability_frames=int(s["stability_frames"]),
                            cooldown_seconds=float(s["cooldown_seconds"]),
                            require_neutral_reset=bool(s["require_neutral_reset"]),
                        )
                    )

                    if s["camera_index"] != settings["camera_index"]:

                        camera.close()

                        if not camera.open(s["camera_index"]):

                            self._push_status(
                                "Camera error",
                                "Could not switch camera.",
                                camera_active=False,
                                color="#E06C75",
                            )
                            break

                    settings = s

                # Read camera frame
                ok, frame = camera.read()

                if not ok or frame is None:

                    self._push_status(
                        "Camera disconnected",
                        "The webcam stopped returning frames.",
                        camera_active=False,
                        color="#E06C75",
                    )

                    time.sleep(0.5)
                    continue

                if settings.get("mirror_preview", True):
                    frame = cv2.flip(frame, 1)

                # MediaPipe processing
                try:
                    result = detector.process(frame)

                except Exception:
                    traceback.print_exc()
                    result = None

                fingers: Optional[int] = None
                gesture: Optional[str] = None

                if result is not None:

                    if result.multiple_hands:
                        self._push(
                            status_title="Multiple hands",
                            status_detail="Please show only one hand.",
                            status_color="#E5C07B",
                        )

                    gesture = engine.classify(result.hand)
                    fingers = gesture_to_finger_count(gesture)
                    if gesture == "rock_sign" and not v_sign_triggered:
                        v_sign_triggered = True

                        threading.Thread(
                            target=self._restore_last_and_report,
                            daemon=True,
                        ).start()

                    elif gesture != "v_sign":
                        v_sign_triggered = False
                # -------------------------------------------------
                # FIST GESTURE
                # -------------------------------------------------

                if gesture == "0_finger":
                    fist_frames += 1

                    if fist_frames == 1:
                        print("DEBUG: FIST DETECTED")

                else:
                    fist_frames = 0
                    fist_triggered = False

                fist_threshold = max(
                    3,
                    int(settings["stability_frames"]),
                )

                if (
                    fist_frames >= fist_threshold
                    and not fist_triggered
                ):
                    fist_triggered = True

                    print("DEBUG: FIST TRIGGERED")
                    print("DEBUG: Calling close_last()")

                    threading.Thread(
                        target=self._close_last_and_report,
                        daemon=True,
                    ).start()

                # Normal gesture stabilisation
                confirmed = stabilizer.update(gesture)

                # Draw landmarks
                if settings.get("show_landmarks", True) and result is not None:
                    frame = detector.draw(frame, result)

                # Convert image
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                pil_img = Image.fromarray(rgb)
                pil_img.thumbnail((640, 480))

                # Dashboard payload
                payload = {
                    "image": pil_img,
                    "fingers": fingers,
                    "status_title": self._status_for(fingers, stabilizer),
                    "assigned": self._assigned_for(fingers),
                }

                # Normal application launching
                if confirmed is not None:

                    fc = gesture_to_finger_count(confirmed)

                    if fc is not None:

                        mapping = self.config_mgr.get_mapping(fc)

                        if not mapping:

                            payload["status_title"] = "No application assigned"
                            payload["status_detail"] = (
                                f"Assign one to {fc} finger(s) in Settings."
                            )
                            payload["status_color"] = "#E5C07B"

                        else:

                            payload["status_title"] = (
                                f"Launching {mapping['name']}…"
                            )
                            payload["status_detail"] = mapping["path"]
                            payload["status_color"] = "#3ECF8E"

                            threading.Thread(
                                target=self._launch_and_report,
                                args=(
                                    mapping["name"],
                                    mapping["path"],
                                ),
                                daemon=True,
                            ).start()

                self._ui_queue.put(payload)

                # Limit approximately 30 FPS
                elapsed = time.monotonic() - last_frame_time
                delay = max(0.0, (1 / 30.0) - elapsed)

                if delay:
                    time.sleep(delay)

                last_frame_time = time.monotonic()

        finally:

            detector.close()
            camera.close()

            self._push(
                camera_active=False,
                camera_message="Idle",
            )

    # ---------------------------------------------------------
    # Application launching
    # ---------------------------------------------------------

    def _launch_and_report(self, name: str, path: str) -> None:

        result = app_launcher.launch(path)

        if result.success:

            self._ui_queue.put({
                "status_title": f"✓ {name} launched",
                "status_detail": path,
                "status_color": "#3ECF8E",
            })

        else:

            self._ui_queue.put({
                "status_title": "Launch failed",
                "status_detail": result.message,
                "status_color": "#E06C75",
            })

    # ---------------------------------------------------------
    # Application closing using fist
    # ---------------------------------------------------------

    def _close_last_and_report(self) -> None:

        print("DEBUG: close_last() function started")

        result = app_launcher.minimize_last()

        print("DEBUG: Minimise result:", result.success)
        print("DEBUG: Message:", result.message)

        self._ui_queue.put({
            "status_title": (
                "✓ Application minimised"
                if result.success
                else "Minimise unsuccessful"
            ),
            "status_detail": result.message,
            "status_color": (
                "#3ECF8E"
                if result.success
                else "#E06C75"
            ),
        })
    def _restore_last_and_report(self) -> None:

        
        result = app_launcher.restore_last()


       
        self._ui_queue.put({
            "status_title": (
                "✓ Application restored"
                if result.success
                else "Restore unsuccessful"
            ),
            "status_detail": result.message,
            "status_color": (
                "#3ECF8E"
                if result.success
                else "#E06C75"
            ),
        })
            # ---------------------------------------------------------
    # Dashboard helpers
    # ---------------------------------------------------------

    def _status_for(
        self,
        fingers: Optional[int],
        stabilizer: GestureStabilizer,
    ) -> str:

        if fingers is None:
            return "Waiting for gesture"

        remaining = stabilizer.cooldown_remaining()

        if remaining > 0:
            return f"Cooldown ({remaining:.1f}s)"

        return "Gesture detected"

    def _assigned_for(self, fingers: Optional[int]):

        if fingers is None or fingers < 1:
            return {"name": "—", "path": ""}

        mapping = self.config_mgr.get_mapping(fingers)

        if not mapping:
            return {"name": "Not assigned", "path": ""}

        return mapping
    # ---------------------------------------------------------
    # UI queue
    # ---------------------------------------------------------

    def _push(self, **kwargs) -> None:
        self._ui_queue.put(kwargs)

    def _push_status(
        self,
        title: str,
        detail: str = "",
        camera_active: bool = True,
        color: str = "",
    ) -> None:

        self._ui_queue.put({
            "status_title": title,
            "status_detail": detail,
            "status_color": color,
            "camera_active": camera_active,
            "camera_message": "" if camera_active else title,
        })

    def _poll_ui_queue(self) -> None:

        try:

            while True:

                payload = self._ui_queue.get_nowait()
                self._apply_payload(payload)

        except Empty:
            pass

        self.after(30, self._poll_ui_queue)

    def _apply_payload(self, payload: dict) -> None:

        if "image" in payload and payload["image"] is not None:

            pil = payload["image"]

            image = ctk.CTkImage(
                light_image=pil,
                dark_image=pil,
                size=pil.size,
            )

            self.dashboard.set_video_image(image)

        if "camera_active" in payload:

            self.dashboard.set_camera_status(
                bool(payload["camera_active"]),
                payload.get("camera_message", ""),
            )

        if "fingers" in payload:
            self.dashboard.set_gesture(payload["fingers"])

        if "assigned" in payload and payload["assigned"] is not None:

            assigned = payload["assigned"]

            self.dashboard.set_assigned_app(
                assigned.get("name", "—"),
                assigned.get("path", ""),
            )

        if "status_title" in payload:

            self.dashboard.set_status(
                payload["status_title"],
                payload.get("status_detail", ""),
                payload.get("status_color", ""),
            )

    # ---------------------------------------------------------
    # Application shutdown
    # ---------------------------------------------------------

    def _on_close(self) -> None:

        self._stop_event.set()

        if self._worker:
            self._worker.join(timeout=2.0)

        self.destroy()


def run() -> None:

    app = HandGestureApp()
    app.mainloop()