"""Windows desktop adapter implementation."""

from __future__ import annotations

from dataclasses import dataclass
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

    def _ensure_windows(self) -> None:
        if sys.platform != "win32":
            raise RuntimeError("The Windows desktop adapter is only available on Windows.")
        if not hasattr(os, "startfile"):
            raise RuntimeError("Windows desktop launching is unavailable in this environment.")

    def _is_allowed_url(self, url: str) -> bool:
        parsed = urlparse(url)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
