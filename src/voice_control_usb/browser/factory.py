"""Browser adapter selection."""

from __future__ import annotations

from pathlib import Path
import os
import sys

from voice_control_usb.browser.adapter import BrowserAdapter, StubBrowserAdapter
from voice_control_usb.browser.playwright_adapter import PlaywrightBrowserAdapter


def default_browser_profile_dir() -> Path:
    """Keep browser identity on the prepared Windows host, never on the USB."""

    configured = os.environ.get("VOICE_CONTROL_USB_BROWSER_PROFILE")
    if configured:
        return Path(configured).expanduser().resolve()
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        raise RuntimeError("Windows LOCALAPPDATA is required for the browser profile.")
    return (Path(local_app_data) / "VoiceControlUSB" / "browser-profile").resolve()


def create_browser_adapter(
    selection: str = "stub",
    *,
    profile_dir: Path | None = None,
    channel: str = "chrome",
) -> BrowserAdapter:
    normalized = selection.strip().lower()
    if normalized == "stub":
        return StubBrowserAdapter()
    if normalized == "playwright":
        if sys.platform != "win32":
            raise RuntimeError("The visible browser adapter is only available on Windows.")
        if profile_dir is None:
            raise ValueError("Visible browser control requires an explicit profile directory.")
        return PlaywrightBrowserAdapter(profile_dir, channel=channel)
    raise ValueError("Unknown browser adapter selection. Expected stub or playwright.")
