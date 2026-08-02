"""Discord adapter selection."""

from __future__ import annotations

import sys

from voice_control_usb.discord.adapter import DiscordAdapter, StubDiscordAdapter
from voice_control_usb.discord.registry import DiscordTargetRegistry
from voice_control_usb.discord.windows_adapter import WindowsDiscordAdapter


def create_discord_adapter(selection: str = "stub") -> DiscordAdapter:
    registry = DiscordTargetRegistry.load_configured()
    normalized = selection.strip().lower()
    if normalized == "stub": return StubDiscordAdapter(registry)
    if normalized == "windows":
        if sys.platform != "win32": raise RuntimeError("The Windows Discord adapter is only available on Windows.")
        return WindowsDiscordAdapter(registry)
    raise ValueError("Unknown Discord adapter selection. Expected stub or windows.")
