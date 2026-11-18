"""Dashboard: webcam preview + detected gesture panel."""

from __future__ import annotations

from typing import Optional

import customtkinter as ctk


GESTURE_ICONS = {
    0: "✊", 1: "☝", 2: "✌", 3: "🤟", 4: "🖖", 5: "🖐",
}
GESTURE_NAMES = {
    0: "Fist / Neutral",
    1: "One Finger",
    2: "Two Fingers",
    3: "Three Fingers",
    4: "Four Fingers",
    5: "Five Fingers",
}


class DashboardFrame(ctk.CTkFrame):
    """Left: video preview. Right: detected gesture info card."""

    def __init__(self, master) -> None:
        super().__init__(master, fg_color="transparent")

        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        # -- Left: video preview --------------------------------------
        preview = ctk.CTkFrame(self)
        preview.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=8)
        preview.grid_rowconfigure(1, weight=1)
        preview.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(preview, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 6))
        ctk.CTkLabel(header, text="WEBCAM PREVIEW",
                     font=ctk.CTkFont(size=12, weight="bold"), text_color="gray70").pack(side="left")
        self.camera_status = ctk.CTkLabel(header, text="●  Idle", text_color="gray60",
                                          font=ctk.CTkFont(size=12, weight="bold"))
        self.camera_status.pack(side="right")

        self.video_label = ctk.CTkLabel(preview, text="Camera off\nPress “Start detection”",
                                        text_color="gray60", anchor="center",
                                        font=ctk.CTkFont(size=14))
        self.video_label.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))

        # -- Right: detected gesture ---------------------------------
        panel = ctk.CTkFrame(self)
        panel.grid(row=0, column=1, sticky="nsew", padx=(4, 8), pady=8)
        ctk.CTkLabel(panel, text="DETECTED GESTURE",
                     font=ctk.CTkFont(size=12, weight="bold"), text_color="gray70").pack(anchor="w", padx=18, pady=(14, 6))

        self.icon_label = ctk.CTkLabel(panel, text="—", font=ctk.CTkFont(size=64))
        self.icon_label.pack(pady=(4, 0))
        self.fingers_label = ctk.CTkLabel(panel, text="0 fingers",
                                          font=ctk.CTkFont(size=20, weight="bold"))
        self.fingers_label.pack(pady=(4, 0))
        self.gesture_name_label = ctk.CTkLabel(panel, text="Waiting for hand…",
                                               text_color="gray70")
        self.gesture_name_label.pack(pady=(2, 14))

        ctk.CTkFrame(panel, height=1, fg_color="gray30").pack(fill="x", padx=18)

        ctk.CTkLabel(panel, text="ASSIGNED APPLICATION",
                     font=ctk.CTkFont(size=12, weight="bold"), text_color="gray70").pack(anchor="w", padx=18, pady=(14, 4))
        self.app_name_label = ctk.CTkLabel(panel, text="—",
                                           font=ctk.CTkFont(size=16, weight="bold"))
        self.app_name_label.pack(anchor="w", padx=18)
        self.app_path_label = ctk.CTkLabel(panel, text="", text_color="gray60",
                                           wraplength=280, justify="left")
        self.app_path_label.pack(anchor="w", padx=18, pady=(2, 14))

        ctk.CTkFrame(panel, height=1, fg_color="gray30").pack(fill="x", padx=18)

        ctk.CTkLabel(panel, text="STATUS",
                     font=ctk.CTkFont(size=12, weight="bold"), text_color="gray70").pack(anchor="w", padx=18, pady=(14, 4))
        self.status_label = ctk.CTkLabel(panel, text="Ready", font=ctk.CTkFont(size=14, weight="bold"))
        self.status_label.pack(anchor="w", padx=18)
        self.status_detail = ctk.CTkLabel(panel, text="", text_color="gray60", wraplength=280, justify="left")
        self.status_detail.pack(anchor="w", padx=18, pady=(2, 14))

    # ------------------------------------------------------------------
    # Public updates -- all called from the main thread via app.after()
    # ------------------------------------------------------------------
    def set_video_image(self, image: Optional[ctk.CTkImage]) -> None:
        if image is None:
            self.video_label.configure(image="", text="Camera off\nPress “Start detection”")
        else:
            self.video_label.configure(image=image, text="")

    def set_camera_status(self, active: bool, message: str = "") -> None:
        if active:
            self.camera_status.configure(text=f"●  Active {message}", text_color="#3ECF8E")
        else:
            self.camera_status.configure(text=f"●  {message or 'Idle'}", text_color="gray60")

    def set_gesture(self, fingers: Optional[int]) -> None:
        if fingers is None:
            self.icon_label.configure(text="—")
            self.fingers_label.configure(text="No hand")
            self.gesture_name_label.configure(text="Waiting for hand…")
            return
        self.icon_label.configure(text=GESTURE_ICONS.get(fingers, "—"))
        self.fingers_label.configure(text=f"{fingers} finger" + ("s" if fingers != 1 else ""))
        self.gesture_name_label.configure(text=GESTURE_NAMES.get(fingers, ""))

    def set_assigned_app(self, name: str, path: str) -> None:
        self.app_name_label.configure(text=name or "—")
        self.app_path_label.configure(text=path or "")

    def set_status(self, title: str, detail: str = "", color: str = "") -> None:
        self.status_label.configure(text=title, text_color=color or ("white"))
        self.status_detail.configure(text=detail)
