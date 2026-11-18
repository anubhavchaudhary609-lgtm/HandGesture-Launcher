"""Launch and gracefully close tracked application windows on Windows."""

from __future__ import annotations

import ctypes
import shlex
import subprocess
import sys
import threading
import time

from ctypes import wintypes
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class LaunchResult:
    success: bool
    message: str
    path: Optional[str] = None


_last_hwnd: Optional[int] = None
_last_application: Optional[str] = None
_last_process = None

_lock = threading.Lock()

WM_CLOSE = 0x0010
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


def _resolve_shortcut(path: Path):
    escaped_path = str(path).replace("'", "''")

    script = (
        "$s = (New-Object -ComObject WScript.Shell)"
        f".CreateShortcut('{escaped_path}'); "
        "[Console]::WriteLine($s.TargetPath); "
        "[Console]::WriteLine($s.Arguments); "
        "[Console]::WriteLine($s.WorkingDirectory)"
    )

    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        capture_output=True,
        text=True,
        timeout=10,
        check=True,
    )

    lines = result.stdout.splitlines()

    if not lines or not lines[0].strip():
        raise ValueError("Could not resolve shortcut target.")

    return (
        lines[0].strip(),
        lines[1].strip() if len(lines) > 1 else "",
        lines[2].strip() if len(lines) > 2 else "",
    )


def _get_window_list(expected_exe: str) -> set[int]:
    """Return visible windows belonging to the expected executable."""

    if not sys.platform.startswith("win"):
        return set()

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    user32.EnumWindows.restype = wintypes.BOOL

    user32.GetWindowThreadProcessId.argtypes = [
        wintypes.HWND,
        ctypes.POINTER(wintypes.DWORD),
    ]

    user32.GetWindowThreadProcessId.restype = wintypes.DWORD

    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.IsWindowVisible.restype = wintypes.BOOL

    kernel32.OpenProcess.argtypes = [
        wintypes.DWORD,
        wintypes.BOOL,
        wintypes.DWORD,
    ]
    kernel32.OpenProcess.restype = wintypes.HANDLE

    kernel32.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.LPWSTR,
        ctypes.POINTER(wintypes.DWORD),
    ]
    kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL

    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL

    windows = set()

    EnumProc = ctypes.WINFUNCTYPE(
        wintypes.BOOL,
        wintypes.HWND,
        wintypes.LPARAM,
    )

    def callback(hwnd, _):

        if not user32.IsWindowVisible(hwnd):
            return True

        pid = wintypes.DWORD()

        user32.GetWindowThreadProcessId(
            hwnd,
            ctypes.byref(pid),
        )

        if not pid.value:
            return True

        handle = kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION,
            False,
            pid.value,
        )

        if not handle:
            return True

        try:
            buffer = ctypes.create_unicode_buffer(1024)
            size = wintypes.DWORD(len(buffer))

            if kernel32.QueryFullProcessImageNameW(
                handle,
                0,
                buffer,
                ctypes.byref(size),
            ):
                process_name = Path(buffer.value).name.lower()

                if process_name == expected_exe.lower():
                    windows.add(int(hwnd))

        finally:
            kernel32.CloseHandle(handle)

        return True

    callback_ref = EnumProc(callback)

    user32.EnumWindows(callback_ref, 0)

    return windows


def _wait_for_new_window(
    expected_exe: str,
    previous_windows: set[int],
    timeout: float = 12,
) -> Optional[int]:
    """Wait for a new visible window created by the launched application."""

    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:

        current_windows = _get_window_list(expected_exe)

        new_windows = current_windows - previous_windows

        if new_windows:
            return next(iter(new_windows))

        time.sleep(0.25)

    return None


def launch(path: str) -> LaunchResult:
    """Launch an application and track its actual window."""

    global _last_hwnd, _last_application, _last_process

    if not path:
        return LaunchResult(False, "No application path configured.")

    p = Path(path).expanduser()

    if not p.exists():
        return LaunchResult(
            False,
            f"Application not found:\n{path}",
            str(p),
        )

    if not p.is_file():
        return LaunchResult(
            False,
            f"Path is not a file:\n{path}",
            str(p),
        )

    try:

        if not sys.platform.startswith("win"):
            return LaunchResult(
                False,
                "Window tracking currently supports Windows only.",
            )

        if p.suffix.lower() == ".lnk":
            target, arguments, working_dir = _resolve_shortcut(p)

            command = [
                target,
                *shlex.split(arguments, posix=False),
            ]

            cwd = working_dir or None

        else:
            target = str(p)
            command = [target]
            cwd = str(p.parent)

        executable_name = Path(target).name.lower()
        # Chrome Apps launch through chrome_proxy.exe,
# but their actual windows belong to chrome.exe.
# Chrome Apps launch through chrome_proxy.exe,
# but their actual windows belong to chrome.exe.
        window_executable_name = executable_name

        if executable_name == "chrome_proxy.exe":
            window_executable_name = "chrome.exe"

        # Force Chrome and Edge shortcuts to open a separate window.
        browsers = {
            "chrome.exe",
            "msedge.exe",
            "firefox.exe",
        }

        if executable_name in browsers:

            if not any(
                arg.lower() in ("--new-window", "-new-window")
                for arg in command
            ):
                command.insert(1, "--new-window")

        # Record existing windows before launching.
        previous_windows = _get_window_list(window_executable_name)

        process = subprocess.Popen(
            command,
            cwd=cwd,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )

        # Find the actual new application window.
        hwnd = _wait_for_new_window(
            window_executable_name,
            previous_windows,
        )

        if hwnd is None:
            return LaunchResult(
                False,
                "Application started, but its new window could not be "
                "identified. No window was recorded for closing.",
                str(p),
            )

        with _lock:
            _last_hwnd = hwnd
            _last_application = p.name
            _last_process = process

        return LaunchResult(
            True,
            f"Launched and tracked {p.name}.",
            str(p),
        )

    except Exception as exc:
        return LaunchResult(
            False,
            f"Failed to launch application:\n{exc}",
            str(p),
        )


def minimize_last() -> LaunchResult:
    """Minimise the last application window launched by HandGesture Launcher."""

    global _last_hwnd

    if not sys.platform.startswith("win"):
        return LaunchResult(False, "Windows only.")

    with _lock:
        hwnd = _last_hwnd
        name = _last_application

    if hwnd is None:
        return LaunchResult(
            False,
            "No tracked application window found."
        )

    user32 = ctypes.WinDLL("user32", use_last_error=True)

    user32.IsWindow.argtypes = [wintypes.HWND]
    user32.IsWindow.restype = wintypes.BOOL

    user32.ShowWindow.argtypes = [
        wintypes.HWND,
        ctypes.c_int,
    ]
    user32.ShowWindow.restype = wintypes.BOOL

    user32.IsIconic.argtypes = [wintypes.HWND]
    user32.IsIconic.restype = wintypes.BOOL

    if not user32.IsWindow(hwnd):
        return LaunchResult(
            False,
            "Application window no longer exists."
        )

    SW_MINIMIZE = 6

    user32.ShowWindow(hwnd, SW_MINIMIZE)

    if user32.IsIconic(hwnd):
        return LaunchResult(
            True,
            f"{name} minimised successfully."
        )

    return LaunchResult(
        False,
        f"Could not minimise {name}."
    )
def restore_last() -> LaunchResult:
    """Restore the last minimised application window."""

    global _last_hwnd

    if not sys.platform.startswith("win"):
        return LaunchResult(False, "Windows only.")

    with _lock:
        hwnd = _last_hwnd
        name = _last_application

    if hwnd is None:
        return LaunchResult(False, "No tracked application window.")

    user32 = ctypes.WinDLL("user32", use_last_error=True)

    user32.IsWindow.argtypes = [wintypes.HWND]
    user32.IsWindow.restype = wintypes.BOOL

    user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.ShowWindow.restype = wintypes.BOOL

    if not user32.IsWindow(hwnd):
        return LaunchResult(False, "Application window no longer exists.")

    SW_RESTORE = 9
    user32.ShowWindow(hwnd, SW_RESTORE)

    return LaunchResult(
        True,
        f"{name} restored successfully."
    )    
def quote_for_display(path: str) -> str:
    return shlex.quote(path)