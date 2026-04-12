"""Registry loader for supported deterministic commands."""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib import resources
import json
from pathlib import Path
import re
from typing import Any


@dataclass(frozen=True, slots=True)
class CommandDefinition:
    """Compiled command definition loaded from the external registry."""

    name: str
    action: str
    description: str
    pattern: str
    regex: re.Pattern[str]
    fixed_arguments: dict[str, str] = field(default_factory=dict)
    argument_transforms: dict[str, str] = field(default_factory=dict)


class CommandRegistry:
    """Load deterministic commands from the packaged JSON registry."""

    def __init__(self, definitions: list[CommandDefinition]) -> None:
        self.definitions = definitions

    @classmethod
    def load_default(cls) -> "CommandRegistry":
        with resources.files("voice_control_usb.core").joinpath("command_registry.json").open(
            "r",
            encoding="utf-8",
        ) as handle:
            data = json.load(handle)
        return cls.from_data(data)

    @classmethod
    def from_path(cls, path: Path) -> "CommandRegistry":
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return cls.from_data(data)

    @classmethod
    def from_data(cls, data: dict[str, Any]) -> "CommandRegistry":
        commands = data.get("commands", [])
        definitions = [cls._parse_definition(item) for item in commands]
        return cls(definitions=definitions)

    @staticmethod
    def _parse_definition(item: dict[str, Any]) -> CommandDefinition:
        pattern = item["pattern"]
        return CommandDefinition(
            name=item["name"],
            action=item["action"],
            description=item["description"],
            pattern=pattern,
            regex=re.compile(pattern, re.IGNORECASE),
            fixed_arguments=dict(item.get("fixed_arguments", {})),
            argument_transforms=dict(item.get("argument_transforms", {})),
        )

    def names(self) -> list[str]:
        return [definition.name for definition in self.definitions]
