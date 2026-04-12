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


@dataclass
class StubDesktopAdapter(DesktopAdapter):
    """Safe stub that validates desktop actions without launching them."""

    aliases: AppAliasRegistry

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

    def _is_allowed_url(self, url: str) -> bool:
        parsed = urlparse(url)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
