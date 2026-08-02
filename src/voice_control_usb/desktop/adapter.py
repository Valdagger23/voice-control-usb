"""Desktop action boundary and WSL-safe stub implementation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from voice_control_usb.desktop.registry import AppAliasRegistry


class DesktopAdapter:
    """Boundary for deterministic desktop actions."""

    def open_app(self, alias: str) -> str:
        raise NotImplementedError

    def open_url(self, url: str) -> str:
        raise NotImplementedError

    def open_folder(self, path: str) -> str:
        raise NotImplementedError

    def shutdown(self) -> str:
        raise NotImplementedError

    def restart(self) -> str:
        raise NotImplementedError

    def switch_app(self, alias: str) -> str: raise NotImplementedError
    def close_current_window(self) -> str: raise NotImplementedError
    def set_window_state(self, state: str) -> str: raise NotImplementedError
    def snap_window(self, side: str) -> str: raise NotImplementedError
    def show_desktop(self) -> str: raise NotImplementedError
    def send_shortcut(self, shortcut: str) -> str: raise NotImplementedError
    def take_screenshot(self) -> str: raise NotImplementedError
    def lock_computer(self) -> str: raise NotImplementedError
    def open_settings(self, area: str) -> str: raise NotImplementedError
    def read_clipboard(self) -> str: raise NotImplementedError
    def clear_clipboard(self) -> str: raise NotImplementedError


@dataclass
class StubDesktopAdapter(DesktopAdapter):
    """Safe stub that validates desktop actions without launching them."""

    aliases: AppAliasRegistry
    active_app: str = "assistant"
    window_state: str = "normal"
    clipboard_text: str = ""

    def open_app(self, alias: str) -> str:
        app = self.aliases.resolve(alias)
        if app is None:
            return f"Desktop app alias is not approved in MVP: {alias}"
        return f"Opened app alias: {app.alias} (stub)"

    def open_url(self, url: str) -> str:
        if not self._is_allowed_url(url):
            return f"Desktop URL is not approved in MVP: {url}"
        return f"Opened URL: {url} (stub)"

    def open_folder(self, path: str) -> str:
        folder = Path(path).expanduser()
        if not folder.exists() or not folder.is_dir():
            return f"Desktop folder is not available: {folder}"
        return f"Opened folder: {folder} (stub)"

    def shutdown(self) -> str:
        return "Shutdown requested (stub)"

    def restart(self) -> str:
        return "Restart requested (stub)"

    def switch_app(self, alias: str) -> str:
        app = self.aliases.resolve(alias)
        if app is None:
            return f"Desktop app alias is not approved in MVP: {alias}"
        self.active_app = app.alias
        return f"Switched to app alias: {app.alias} (stub)"

    def close_current_window(self) -> str:
        return f"Closed current window: {self.active_app} (stub)"

    def set_window_state(self, state: str) -> str:
        if state not in {"minimized", "maximized", "restored"}:
            raise ValueError("Window state must be minimized, maximized, or restored.")
        self.window_state = state
        return f"Current window {state} (stub)"

    def snap_window(self, side: str) -> str:
        if side not in {"left", "right"}:
            raise ValueError("Window snap side must be left or right.")
        self.window_state = f"snapped-{side}"
        return f"Current window snapped {side} (stub)"

    def show_desktop(self) -> str:
        self.window_state = "desktop"
        return "Desktop shown (stub)"

    def send_shortcut(self, shortcut: str) -> str:
        if shortcut not in {"copy", "paste", "select_all"}:
            raise ValueError("Desktop shortcut is not approved.")
        return f"Sent desktop shortcut: {shortcut.replace('_', ' ')} (stub)"

    def take_screenshot(self) -> str:
        return "Screenshot captured: screenshots/stub-screen.png (stub)"

    def lock_computer(self) -> str:
        return "Computer locked (stub)"

    def open_settings(self, area: str) -> str:
        approved = {"display", "sound", "bluetooth", "network", "apps", "privacy", "windows update"}
        if area not in approved:
            return f"Windows Settings area is not approved: {area}"
        return f"Opened Windows Settings: {area} (stub)"

    def read_clipboard(self) -> str:
        return f"Clipboard text: {self.clipboard_text or '<empty>'}"

    def clear_clipboard(self) -> str:
        self.clipboard_text = ""
        return "Clipboard cleared (stub)"

    def _is_allowed_url(self, url: str) -> bool:
        parsed = urlparse(url)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
