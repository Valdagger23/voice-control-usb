"""Allowlist registry for deterministic desktop app aliases."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from voice_control_usb.runtime_support import resolve_packaged_data_path


@dataclass(frozen=True, slots=True)
class AppAlias:
    """Allowlisted app launch target."""

    alias: str
    description: str
    windows_command: list[str]


class AppAliasRegistry:
    """Load app aliases from packaged JSON configuration."""

    def __init__(self, aliases: dict[str, AppAlias]) -> None:
        self.aliases = aliases

    @classmethod
    def load_default(cls) -> "AppAliasRegistry":
        return cls.from_path(resolve_packaged_data_path("desktop", "app_aliases.json"))

    @classmethod
    def from_path(cls, path: Path) -> "AppAliasRegistry":
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return cls.from_data(data)

    @classmethod
    def from_data(cls, data: dict[str, Any]) -> "AppAliasRegistry":
        aliases: dict[str, AppAlias] = {}
        for alias, payload in data.get("apps", {}).items():
            aliases[alias] = AppAlias(
                alias=alias,
                description=payload["description"],
                windows_command=list(payload["windows_command"]),
            )
        return cls(aliases=aliases)

    def resolve(self, alias: str) -> AppAlias | None:
        return self.aliases.get(alias.casefold())
