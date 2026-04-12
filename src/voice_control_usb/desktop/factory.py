"""Desktop adapter selection."""

from __future__ import annotations

import sys

from voice_control_usb.desktop.adapter import DesktopAdapter, StubDesktopAdapter
from voice_control_usb.desktop.registry import AppAliasRegistry
from voice_control_usb.desktop.windows_adapter import WindowsDesktopAdapter


def create_desktop_adapter(selection: str = "stub") -> DesktopAdapter:
    """Create the configured desktop adapter."""

    aliases = AppAliasRegistry.load_default()
    normalized = selection.strip().lower()
    if normalized == "stub":
        return StubDesktopAdapter(aliases=aliases)
    if normalized == "windows":
        if sys.platform != "win32":
            raise RuntimeError("The Windows desktop adapter is only available on Windows.")
        return WindowsDesktopAdapter(aliases=aliases)
    raise ValueError(
        "Unknown desktop adapter selection. Expected one of: 'stub', 'windows'."
    )
