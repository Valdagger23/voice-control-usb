"""Desktop action abstractions."""

from voice_control_usb.desktop.adapter import DesktopAdapter, StubDesktopAdapter
from voice_control_usb.desktop.factory import create_desktop_adapter
from voice_control_usb.desktop.registry import AppAliasRegistry
from voice_control_usb.desktop.windows_adapter import WindowsDesktopAdapter

__all__ = [
    "AppAliasRegistry",
    "DesktopAdapter",
    "StubDesktopAdapter",
    "WindowsDesktopAdapter",
    "create_desktop_adapter",
]
