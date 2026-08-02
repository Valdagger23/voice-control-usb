"""Windows desktop adapter implementation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import os
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlparse

from voice_control_usb.desktop.adapter import DesktopAdapter
from voice_control_usb.desktop.registry import AppAliasRegistry


@dataclass
class WindowsDesktopAdapter(DesktopAdapter):
    """Launch allowlisted desktop actions on Windows."""

    aliases: AppAliasRegistry
    screenshot_dir: Path = field(
        default_factory=lambda: Path.home() / "Pictures" / "Voice Control"
    )

    def open_app(self, alias: str) -> str:
        app = self.aliases.resolve(alias)
        if app is None:
            return f"Desktop app alias is not approved in MVP: {alias}"
        self._ensure_windows()
        subprocess.Popen(app.windows_command, shell=False)
        return f"Opened app alias: {app.alias}"

    def open_url(self, url: str) -> str:
        if not self._is_allowed_url(url):
            return f"Desktop URL is not approved in MVP: {url}"
        self._ensure_windows()
        os.startfile(url)  # type: ignore[attr-defined]
        return f"Opened URL: {url}"

    def open_folder(self, path: str) -> str:
        folder = Path(path).expanduser()
        if not folder.exists() or not folder.is_dir():
            return f"Desktop folder is not available: {folder}"
        self._ensure_windows()
        os.startfile(str(folder))  # type: ignore[attr-defined]
        return f"Opened folder: {folder}"

    def shutdown(self) -> str:
        self._ensure_windows()
        subprocess.run(["shutdown", "/s", "/t", "0"], shell=False, check=False)
        return "Shutdown requested"

    def restart(self) -> str:
        self._ensure_windows()
        subprocess.run(["shutdown", "/r", "/t", "0"], shell=False, check=False)
        return "Restart requested"

    def switch_app(self, alias: str) -> str:
        app = self.aliases.resolve(alias)
        if app is None:
            return f"Desktop app alias is not approved in MVP: {alias}"
        self._ensure_windows()
        win32gui, _win32con, win32process = self._window_modules()
        expected = Path(app.windows_command[0]).stem.casefold()
        matches: list[int] = []

        def collect(handle: int, _extra: object) -> None:
            if not win32gui.IsWindowVisible(handle):
                return
            title = win32gui.GetWindowText(handle).casefold()
            if alias.casefold() in title or app.description.casefold() in title:
                matches.append(handle)
                return
            try:
                _thread, process_id = win32process.GetWindowThreadProcessId(handle)
                process_handle = self._open_process(process_id)
                try:
                    executable = self._process_image_name(process_handle)
                finally:
                    process_handle.Close()
                if Path(executable).stem.casefold() == expected:
                    matches.append(handle)
            except OSError:
                return

        win32gui.EnumWindows(collect, None)
        if not matches:
            raise RuntimeError(f"No visible window is open for app alias: {alias}")
        handle = matches[0]
        win32gui.ShowWindow(handle, 9)
        win32gui.SetForegroundWindow(handle)
        return f"Switched to app alias: {app.alias}"

    def close_current_window(self) -> str:
        win32gui, win32con, _win32process = self._window_modules()
        handle = self._foreground_window(win32gui)
        title = win32gui.GetWindowText(handle) or "current window"
        win32gui.PostMessage(handle, win32con.WM_CLOSE, 0, 0)
        return f"Close requested for: {title}"

    def set_window_state(self, state: str) -> str:
        states = {"minimized": 6, "maximized": 3, "restored": 9}
        if state not in states:
            raise ValueError("Window state must be minimized, maximized, or restored.")
        win32gui, _win32con, _win32process = self._window_modules()
        win32gui.ShowWindow(self._foreground_window(win32gui), states[state])
        return f"Current window {state}"

    def snap_window(self, side: str) -> str:
        if side not in {"left", "right"}:
            raise ValueError("Window snap side must be left or right.")
        win32gui, win32con, _win32process = self._window_modules()
        try:
            import win32api
        except ImportError as error:
            raise ImportError("Window snapping requires pywin32.") from error
        handle = self._foreground_window(win32gui)
        monitor = win32api.MonitorFromWindow(handle, win32con.MONITOR_DEFAULTTONEAREST)
        left, top, right, bottom = win32api.GetMonitorInfo(monitor)["Work"]
        midpoint = left + ((right - left) // 2)
        x = left if side == "left" else midpoint
        win32gui.SetWindowPos(
            handle,
            win32con.HWND_TOP,
            x,
            top,
            midpoint - left,
            bottom - top,
            win32con.SWP_SHOWWINDOW,
        )
        return f"Current window snapped {side}"

    def show_desktop(self) -> str:
        self._ensure_windows()
        try:
            import win32com.client
        except ImportError as error:
            raise ImportError("Showing the desktop requires pywin32.") from error
        win32com.client.Dispatch("Shell.Application").ToggleDesktop()
        return "Desktop shown"

    def send_shortcut(self, shortcut: str) -> str:
        keys = {"copy": "C", "paste": "V", "select_all": "A"}
        if shortcut not in keys:
            raise ValueError("Desktop shortcut is not approved.")
        try:
            import win32api
            import win32con
        except ImportError as error:
            raise ImportError("Desktop shortcuts require pywin32.") from error
        key = ord(keys[shortcut])
        win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
        win32api.keybd_event(key, 0, 0, 0)
        win32api.keybd_event(key, 0, win32con.KEYEVENTF_KEYUP, 0)
        win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
        return f"Sent desktop shortcut: {shortcut.replace('_', ' ')}"

    def take_screenshot(self) -> str:
        self._ensure_windows()
        try:
            from PIL import ImageGrab
        except ImportError as error:
            raise ImportError("Screenshot capture requires Pillow.") from error
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        path = self.screenshot_dir / f"voice-control-{timestamp}.png"
        ImageGrab.grab(all_screens=True).save(path)
        return f"Screenshot captured: {path}"

    def lock_computer(self) -> str:
        self._ensure_windows()
        import ctypes

        if not ctypes.windll.user32.LockWorkStation():
            raise RuntimeError("Windows could not lock the current session.")
        return "Computer locked"

    def open_settings(self, area: str) -> str:
        settings = {
            "display": "ms-settings:display",
            "sound": "ms-settings:sound",
            "bluetooth": "ms-settings:bluetooth",
            "network": "ms-settings:network-status",
            "apps": "ms-settings:appsfeatures",
            "privacy": "ms-settings:privacy",
            "windows update": "ms-settings:windowsupdate",
        }
        uri = settings.get(area)
        if uri is None:
            return f"Windows Settings area is not approved: {area}"
        self._ensure_windows()
        os.startfile(uri)  # type: ignore[attr-defined]
        return f"Opened Windows Settings: {area}"

    def read_clipboard(self) -> str:
        try:
            import win32clipboard
        except ImportError as error:
            raise ImportError("Clipboard control requires pywin32.") from error
        win32clipboard.OpenClipboard()
        try:
            if not win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
                return "Clipboard text: <empty or non-text content>"
            value = str(win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT))
        finally:
            win32clipboard.CloseClipboard()
        return f"Clipboard text: {value or '<empty>'}"

    def clear_clipboard(self) -> str:
        try:
            import win32clipboard
        except ImportError as error:
            raise ImportError("Clipboard control requires pywin32.") from error
        win32clipboard.OpenClipboard()
        try:
            win32clipboard.EmptyClipboard()
        finally:
            win32clipboard.CloseClipboard()
        return "Clipboard cleared"

    def _ensure_windows(self) -> None:
        if sys.platform != "win32":
            raise RuntimeError("The Windows desktop adapter is only available on Windows.")
        if not hasattr(os, "startfile"):
            raise RuntimeError("Windows desktop launching is unavailable in this environment.")

    def _is_allowed_url(self, url: str) -> bool:
        parsed = urlparse(url)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

    @staticmethod
    def _window_modules():
        try:
            import win32con
            import win32gui
            import win32process
        except ImportError as error:
            raise ImportError("Window control requires pywin32.") from error
        return win32gui, win32con, win32process

    @staticmethod
    def _foreground_window(win32gui) -> int:
        handle = int(win32gui.GetForegroundWindow())
        if not handle:
            raise RuntimeError("Windows did not report a foreground window.")
        return handle

    @staticmethod
    def _open_process(process_id: int):
        try:
            import win32api
            import win32con
        except ImportError as error:
            raise ImportError("Application switching requires pywin32.") from error
        return win32api.OpenProcess(win32con.PROCESS_QUERY_LIMITED_INFORMATION, False, process_id)

    @staticmethod
    def _process_image_name(process_handle) -> str:
        try:
            import win32process
        except ImportError as error:
            raise ImportError("Application switching requires pywin32.") from error
        return str(win32process.GetModuleFileNameEx(process_handle, 0))
