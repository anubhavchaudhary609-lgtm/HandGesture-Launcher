"""Dialog to add or edit a gesture -> application mapping."""

from __future__ import annotations

from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Callable, Optional

import customtkinter as ctk


FINGER_CHOICES = [
    ("☝  1 Finger", 1),
    ("✌  2 Fingers", 2),
    ("🤟 3 Fingers", 3),
    ("🖖 4 Fingers", 4),
    ("🖐 5 Fingers", 5),
]


class ApplicationDialog(ctk.CTkToplevel):
    """Modal dialog for creating/editing a mapping."""

    def __init__(
        self,
        master,
        on_save: Callable[[int, str, str], None],
        finger_count: Optional[int] = None,
        app_name: str = "",
        app_path: str = "",
        title: str = "Add Application",
        allow_change_gesture: bool = True,
    ) -> None:
        super().__init__(master)
        self.title(title)
        self.geometry("520x330")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self._on_save = on_save

        # Gesture picker
        ctk.CTkLabel(self, text="Gesture", anchor="w", font=ctk.CTkFont(size=13, weight="bold")).pack(
            fill="x", padx=20, pady=(20, 4)
        )
        self._finger_var = ctk.StringVar(
            value=self._label_for(finger_count) if finger_count else FINGER_CHOICES[0][0]
        )
        self._finger_menu = ctk.CTkOptionMenu(
            self,
            variable=self._finger_var,
            values=[lbl for lbl, _ in FINGER_CHOICES],
            state="normal" if allow_change_gesture else "disabled",
        )
        self._finger_menu.pack(fill="x", padx=20)

        # Application name
        ctk.CTkLabel(self, text="Application name", anchor="w", font=ctk.CTkFont(size=13, weight="bold")).pack(
            fill="x", padx=20, pady=(16, 4)
        )
        self._name_entry = ctk.CTkEntry(self, placeholder_text="e.g. Spotify")
        self._name_entry.insert(0, app_name)
        self._name_entry.pack(fill="x", padx=20)

        # Executable path
        ctk.CTkLabel(self, text="Executable path", anchor="w", font=ctk.CTkFont(size=13, weight="bold")).pack(
            fill="x", padx=20, pady=(16, 4)
        )
        path_row = ctk.CTkFrame(self, fg_color="transparent")
        path_row.pack(fill="x", padx=20)
        self._path_entry = ctk.CTkEntry(path_row, placeholder_text=r"C:\Path\to\App.exe")
        self._path_entry.insert(0, app_path)
        self._path_entry.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(path_row, text="Browse…", width=90, command=self._browse).pack(side="left", padx=(8, 0))

        # Buttons
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(24, 20))
        ctk.CTkButton(btn_row, text="Cancel", fg_color="gray30", hover_color="gray20", command=self.destroy).pack(
            side="right", padx=(8, 0)
        )
        ctk.CTkButton(btn_row, text="Save", command=self._save).pack(side="right")

    # ------------------------------------------------------------------
    @staticmethod
    def _label_for(count: int) -> str:
        for lbl, n in FINGER_CHOICES:
            if n == count:
                return lbl
        return FINGER_CHOICES[0][0]

    def _finger_from_label(self, label: str) -> int:
        for lbl, n in FINGER_CHOICES:
            if lbl == label:
                return n
        return 1

    # ------------------------------------------------------------------
    def _browse(self) -> None:
        filetypes = [("Executables", "*.exe *.lnk *.bat *.cmd"), ("All files", "*.*")]
        path = filedialog.askopenfilename(parent=self, title="Select application", filetypes=filetypes)
        if path:
            self._path_entry.delete(0, "end")
            self._path_entry.insert(0, path)
            if not self._name_entry.get().strip():
                self._name_entry.insert(0, Path(path).stem)

    def _save(self) -> None:
        finger = self._finger_from_label(self._finger_var.get())
        name = self._name_entry.get().strip()
        path = self._path_entry.get().strip()
        if not name:
            messagebox.showerror("Missing name", "Please enter an application name.", parent=self)
            return
        if not path:
            messagebox.showerror("Missing path", "Please choose an executable file.", parent=self)
            return
        if not Path(path).expanduser().exists():
            if not messagebox.askyesno(
                "File not found",
                f"The path\n{path}\ndoes not exist on this system.\n\nSave anyway?",
                parent=self,
            ):
                return
        self._on_save(finger, name, path)
        self.destroy()
