"""Settings tab: camera, sensitivity, mappings, startup."""

from __future__ import annotations

from tkinter import messagebox
from typing import Callable, Optional

import customtkinter as ctk

from src import startup_manager
from src.camera import CameraManager
from src.config_manager import ConfigManager
from src.gui.application_dialog import ApplicationDialog


GESTURE_LABELS = {
    1: "☝  1 Finger",
    2: "✌  2 Fingers",
    3: "🤟 3 Fingers",
    4: "🖖 4 Fingers",
    5: "🖐 5 Fingers",
}


class SettingsFrame(ctk.CTkFrame):
    def __init__(self, master, config: ConfigManager, on_settings_changed: Callable[[], None]) -> None:
        super().__init__(master, fg_color="transparent")
        self.config_mgr = config
        self._on_changed = on_settings_changed
        self._mapping_rows: dict[int, dict] = {}

        # Scrollable container
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        self._build_camera_section(scroll)
        self._build_sensitivity_section(scroll)
        self._build_mappings_section(scroll)
        self._build_startup_section(scroll)

    # ------------------------------------------------------------------
    def _section_header(self, parent, text: str) -> None:
        ctk.CTkLabel(
            parent, text=text, anchor="w",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(fill="x", padx=4, pady=(18, 8))

    # -- Camera --------------------------------------------------------
    def _build_camera_section(self, parent) -> None:
        self._section_header(parent, "Camera")
        card = ctk.CTkFrame(parent)
        card.pack(fill="x", padx=4, pady=(0, 4))

        ctk.CTkLabel(card, text="Camera device", anchor="w").pack(fill="x", padx=16, pady=(14, 4))
        cams = CameraManager.list_cameras(max_probe=5)
        values = [f"{c.index}: {c.label}" for c in cams] or ["0: Camera 0"]
        current = self.config_mgr.get_setting("camera_index")
        current_value = next((v for v in values if v.startswith(f"{current}:")), values[0])
        self._camera_var = ctk.StringVar(value=current_value)
        ctk.CTkOptionMenu(card, variable=self._camera_var, values=values,
                          command=lambda _: self._apply_camera()).pack(fill="x", padx=16, pady=(0, 14))

    def _apply_camera(self) -> None:
        try:
            idx = int(self._camera_var.get().split(":", 1)[0])
        except ValueError:
            return
        self.config_mgr.set_setting("camera_index", idx)
        self._on_changed()

    # -- Sensitivity --------------------------------------------------
    def _build_sensitivity_section(self, parent) -> None:
        self._section_header(parent, "Gesture sensitivity")
        card = ctk.CTkFrame(parent)
        card.pack(fill="x", padx=4, pady=(0, 4))

        # Stability frames
        s = self.config_mgr.all_settings()
        self._stability_var = ctk.IntVar(value=int(s["stability_frames"]))
        self._cooldown_var = ctk.DoubleVar(value=float(s["cooldown_seconds"]))
        self._confidence_var = ctk.DoubleVar(value=float(s["detection_confidence"]))
        self._neutral_var = ctk.BooleanVar(value=bool(s["require_neutral_reset"]))
        self._mirror_var = ctk.BooleanVar(value=bool(s["mirror_preview"]))
        self._landmarks_var = ctk.BooleanVar(value=bool(s["show_landmarks"]))

        self._add_slider(card, "Stability (frames)", self._stability_var, 3, 40, 1,
                         lambda v: self.config_mgr.set_setting("stability_frames", int(float(v))) or self._on_changed())
        self._add_slider(card, "Cooldown (seconds)", self._cooldown_var, 0.5, 10.0, 0.1,
                         lambda v: self.config_mgr.set_setting("cooldown_seconds", round(float(v), 1)) or self._on_changed(),
                         fmt="{:.1f}")
        self._add_slider(card, "Detection confidence", self._confidence_var, 0.3, 0.95, 0.05,
                         lambda v: self.config_mgr.set_setting("detection_confidence", round(float(v), 2)) or self._on_changed(),
                         fmt="{:.2f}")

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(4, 14))
        ctk.CTkCheckBox(row, text="Require neutral gesture (0 fingers) between repeats",
                        variable=self._neutral_var,
                        command=lambda: self.config_mgr.set_setting("require_neutral_reset", self._neutral_var.get()) or self._on_changed()
                        ).pack(anchor="w", pady=2)
        ctk.CTkCheckBox(row, text="Mirror webcam preview", variable=self._mirror_var,
                        command=lambda: self.config_mgr.set_setting("mirror_preview", self._mirror_var.get()) or self._on_changed()
                        ).pack(anchor="w", pady=2)
        ctk.CTkCheckBox(row, text="Draw hand landmarks on preview", variable=self._landmarks_var,
                        command=lambda: self.config_mgr.set_setting("show_landmarks", self._landmarks_var.get()) or self._on_changed()
                        ).pack(anchor="w", pady=2)

    def _add_slider(self, parent, label, var, from_, to, step, on_change, fmt="{}"):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(10, 2))
        ctk.CTkLabel(row, text=label, anchor="w").pack(side="left")
        value_lbl = ctk.CTkLabel(row, text=fmt.format(var.get()), width=60, anchor="e")
        value_lbl.pack(side="right")

        def _cmd(v):
            value_lbl.configure(text=fmt.format(float(v)))
            on_change(v)

        slider = ctk.CTkSlider(parent, from_=from_, to=to,
                               number_of_steps=int(max(1, (to - from_) / step)),
                               command=_cmd)
        slider.set(var.get())
        slider.pack(fill="x", padx=16, pady=(0, 6))

    # -- Mappings -----------------------------------------------------
    def _build_mappings_section(self, parent) -> None:
        self._section_header(parent, "Gesture mappings")
        card = ctk.CTkFrame(parent)
        card.pack(fill="x", padx=4, pady=(0, 4))
        self._mappings_card = card

        header_row = ctk.CTkFrame(card, fg_color="transparent")
        header_row.pack(fill="x", padx=16, pady=(14, 6))
        ctk.CTkButton(header_row, text="+ Add / Edit", width=120,
                      command=self._open_add_dialog).pack(side="left")
        ctk.CTkButton(header_row, text="Reset to defaults", width=140, fg_color="gray30",
                      hover_color="gray20", command=self._reset_mappings).pack(side="left", padx=8)

        self._rows_frame = ctk.CTkFrame(card, fg_color="transparent")
        self._rows_frame.pack(fill="x", padx=16, pady=(0, 14))
        self.refresh_mappings()

    def refresh_mappings(self) -> None:
        for w in self._rows_frame.winfo_children():
            w.destroy()
        self._mapping_rows.clear()
        mappings = self.config_mgr.all_mappings()
        for finger in (1, 2, 3, 4, 5):
            row = ctk.CTkFrame(self._rows_frame)
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(row, text=GESTURE_LABELS[finger], width=110, anchor="w",
                         font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=(12, 6), pady=8)
            m = mappings.get(str(finger))
            text = f"{m['name']}   —   {m['path']}" if m else "— not assigned —"
            lbl = ctk.CTkLabel(row, text=text, anchor="w")
            lbl.pack(side="left", fill="x", expand=True, padx=6)
            ctk.CTkButton(row, text="Edit", width=60,
                          command=lambda f=finger: self._open_edit_dialog(f)).pack(side="left", padx=4)
            ctk.CTkButton(row, text="Remove", width=70, fg_color="#8B2E2E", hover_color="#6E2323",
                          command=lambda f=finger: self._remove_mapping(f)).pack(side="left", padx=(4, 12))
            self._mapping_rows[finger] = {"row": row, "label": lbl}

    def _open_add_dialog(self) -> None:
        ApplicationDialog(self, on_save=self._save_mapping, title="Add / Edit Application")

    def _open_edit_dialog(self, finger: int) -> None:
        m = self.config_mgr.get_mapping(finger) or {}
        ApplicationDialog(self, on_save=self._save_mapping,
                          finger_count=finger, app_name=m.get("name", ""),
                          app_path=m.get("path", ""), title=f"Edit {GESTURE_LABELS[finger]}",
                          allow_change_gesture=True)

    def _save_mapping(self, finger: int, name: str, path: str) -> None:
        self.config_mgr.set_mapping(finger, name, path)
        self.refresh_mappings()
        self._on_changed()

    def _remove_mapping(self, finger: int) -> None:
        if messagebox.askyesno("Remove mapping",
                               f"Remove the application assigned to {GESTURE_LABELS[finger]}?",
                               parent=self):
            self.config_mgr.remove_mapping(finger)
            self.refresh_mappings()
            self._on_changed()

    def _reset_mappings(self) -> None:
        if messagebox.askyesno("Reset mappings", "Reset all gesture mappings to defaults?", parent=self):
            self.config_mgr.reset_mappings()
            self.refresh_mappings()
            self._on_changed()

    # -- Startup ------------------------------------------------------
    def _build_startup_section(self, parent) -> None:
        self._section_header(parent, "Startup")
        card = ctk.CTkFrame(parent)
        card.pack(fill="x", padx=4, pady=(0, 12))

        self._startup_var = ctk.BooleanVar(value=self.config_mgr.get_setting("start_with_windows"))
        cb = ctk.CTkCheckBox(
            card,
            text="Start HandGesture Launcher with Windows",
            variable=self._startup_var,
            command=self._toggle_startup,
        )
        cb.pack(anchor="w", padx=16, pady=14)
        if not startup_manager.is_supported():
            cb.configure(state="disabled")
            ctk.CTkLabel(
                card,
                text="(Available only on Windows — this feature will activate when running on Windows.)",
                text_color="gray70",
            ).pack(anchor="w", padx=16, pady=(0, 12))

    def _toggle_startup(self) -> None:
        enabled = self._startup_var.get()
        ok = startup_manager.enable() if enabled else startup_manager.disable()
        if not ok and startup_manager.is_supported():
            messagebox.showerror("Startup", "Could not update Windows startup entry.", parent=self)
            self._startup_var.set(not enabled)
            return
        self.config_mgr.set_setting("start_with_windows", enabled)
