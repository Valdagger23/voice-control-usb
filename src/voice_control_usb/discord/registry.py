"""Allowlisted Discord navigation targets."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re

from voice_control_usb.runtime_support import resolve_packaged_data_path


@dataclass(frozen=True, slots=True)
class DiscordTarget:
    alias: str
    guild_id: str
    channel_id: str
    label: str

    @property
    def uri(self) -> str:
        return f"discord://-/channels/{self.guild_id}/{self.channel_id}"


class DiscordTargetRegistry:
    def __init__(self, targets: dict[str, DiscordTarget]) -> None:
        self.targets = targets

    @classmethod
    def load_default(cls) -> "DiscordTargetRegistry":
        return cls.from_path(resolve_packaged_data_path("discord", "discord_targets.json"))

    @classmethod
    def load_configured(cls) -> "DiscordTargetRegistry":
        configured = os.environ.get("VOICE_CONTROL_USB_DISCORD_TARGETS")
        return cls.from_path(Path(configured).expanduser().resolve()) if configured else cls.load_default()

    @classmethod
    def from_path(cls, path: Path) -> "DiscordTargetRegistry":
        data = json.loads(path.read_text(encoding="utf-8"))
        targets = {}
        for item in data.get("targets", []):
            alias = str(item["alias"]).strip().casefold()
            guild = str(item["guild_id"]).strip()
            channel = str(item["channel_id"]).strip()
            if not re.fullmatch(r"[a-z0-9_-]+", alias):
                raise ValueError(f"Invalid Discord target alias: {alias}")
            if guild != "@me" and not guild.isdigit():
                raise ValueError(f"Invalid Discord guild ID for alias: {alias}")
            if not channel.isdigit():
                raise ValueError(f"Invalid Discord channel ID for alias: {alias}")
            targets[alias] = DiscordTarget(alias, guild, channel, str(item.get("label", alias)))
        return cls(targets)

    def resolve(self, alias: str) -> DiscordTarget | None:
        return self.targets.get(alias.casefold())
