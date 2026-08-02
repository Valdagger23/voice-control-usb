"""Editable, locally persisted user routines made from supported command phrases."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re

from voice_control_usb.core.models import Command
from voice_control_usb.core.parser import CommandParser


_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _-]{0,39}$")
_DISALLOWED_ACTIONS = {
    "blocked_desktop_action",
    "discord_blocked_action",
    "confirm_pending",
    "cancel_pending",
    "report_status",
    "repeat_response",
    "repeat_last_command",
    "undo_last_action",
    "report_last_input",
    "correct_last_input",
    "show_commands",
    "stop_listening",
    "create_user_routine",
    "run_user_routine",
    "list_user_routines",
    "edit_user_routine",
    "delete_user_routine",
}


@dataclass(frozen=True, slots=True)
class UserRoutine:
    name: str
    commands: tuple[str, ...] = ()


class UserRoutineStore:
    """Manage validated routines with optional JSON persistence."""

    def __init__(
        self,
        path: Path | None = None,
        parser: CommandParser | None = None,
    ) -> None:
        self.path = path
        self.parser = parser or CommandParser()
        self._routines: dict[str, UserRoutine] = {}
        self._load()

    def list(self) -> tuple[UserRoutine, ...]:
        return tuple(sorted(self._routines.values(), key=lambda item: item.name.casefold()))

    def get(self, name: str) -> UserRoutine | None:
        return self._routines.get(name.strip().casefold())

    def create(self, name: str) -> UserRoutine:
        normalized = self._validate_name(name)
        key = normalized.casefold()
        if key in self._routines:
            raise ValueError(f"Routine already exists: {normalized}")
        routine = UserRoutine(normalized)
        self._routines[key] = routine
        self._save()
        return routine

    def set_commands(self, name: str, commands: list[str] | tuple[str, ...]) -> UserRoutine:
        routine = self._required(name)
        normalized = tuple(self._validate_command(command) for command in commands)
        updated = UserRoutine(routine.name, normalized)
        self._routines[routine.name.casefold()] = updated
        self._save()
        return updated

    def add_command(self, name: str, command: str, index: int | None = None) -> UserRoutine:
        routine = self._required(name)
        commands = list(routine.commands)
        insertion = len(commands) if index is None else max(0, min(index, len(commands)))
        commands.insert(insertion, self._validate_command(command))
        return self.set_commands(routine.name, commands)

    def update_command(self, name: str, index: int, command: str) -> UserRoutine:
        routine = self._required(name)
        commands = list(routine.commands)
        self._required_index(commands, index)
        commands[index] = self._validate_command(command)
        return self.set_commands(routine.name, commands)

    def remove_command(self, name: str, index: int) -> UserRoutine:
        routine = self._required(name)
        commands = list(routine.commands)
        self._required_index(commands, index)
        del commands[index]
        return self.set_commands(routine.name, commands)

    def move_command(self, name: str, old_index: int, new_index: int) -> UserRoutine:
        routine = self._required(name)
        commands = list(routine.commands)
        self._required_index(commands, old_index)
        item = commands.pop(old_index)
        commands.insert(max(0, min(new_index, len(commands))), item)
        return self.set_commands(routine.name, commands)

    def rename(self, old_name: str, new_name: str) -> UserRoutine:
        routine = self._required(old_name)
        normalized = self._validate_name(new_name)
        new_key = normalized.casefold()
        if new_key != routine.name.casefold() and new_key in self._routines:
            raise ValueError(f"Routine already exists: {normalized}")
        del self._routines[routine.name.casefold()]
        updated = UserRoutine(normalized, routine.commands)
        self._routines[new_key] = updated
        self._save()
        return updated

    def delete(self, name: str) -> UserRoutine:
        routine = self._required(name)
        del self._routines[routine.name.casefold()]
        self._save()
        return routine

    def parsed_commands(self, name: str) -> tuple[Command, ...]:
        routine = self._required(name)
        parsed_commands: list[Command] = []
        for phrase in routine.commands:
            result = self.parser.parse(phrase)
            if result.command is None:
                raise ValueError(f"Routine contains an unsupported command: {phrase}")
            parsed_commands.append(result.command)
        return tuple(parsed_commands)

    def _validate_command(self, command: str) -> str:
        normalized = " ".join(command.strip().split())
        result = self.parser.parse(normalized)
        if result.command is None:
            raise ValueError(f"Routine command is not supported: {normalized}")
        if result.command.action in _DISALLOWED_ACTIONS:
            raise ValueError(f"Command cannot be placed in a routine: {normalized}")
        return normalized

    @staticmethod
    def _validate_name(name: str) -> str:
        normalized = " ".join(name.strip().split())
        if not _NAME_PATTERN.fullmatch(normalized):
            raise ValueError(
                "Routine names must be 1-40 characters using letters, numbers, spaces, '-' or '_'."
            )
        return normalized

    def _required(self, name: str) -> UserRoutine:
        routine = self.get(name)
        if routine is None:
            raise ValueError(f"Routine not found: {name}")
        return routine

    @staticmethod
    def _required_index(commands: list[str], index: int) -> None:
        if not 0 <= index < len(commands):
            raise IndexError("Routine step is no longer available.")

    def _load(self) -> None:
        if self.path is None or not self.path.is_file():
            return
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeError(f"Could not load saved routines: {error}") from error
        if not isinstance(payload, dict) or not isinstance(payload.get("routines", []), list):
            raise RuntimeError("Saved routine data has an invalid format.")
        for item in payload.get("routines", []):
            if not isinstance(item, dict):
                raise RuntimeError("Saved routine data contains an invalid entry.")
            name = self._validate_name(str(item.get("name", "")))
            raw_commands = item.get("commands", [])
            if not isinstance(raw_commands, list):
                raise RuntimeError(f"Saved routine commands are invalid: {name}")
            commands = tuple(self._validate_command(str(command)) for command in raw_commands)
            self._routines[name.casefold()] = UserRoutine(name, commands)

    def _save(self) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 1,
            "routines": [
                {"name": routine.name, "commands": list(routine.commands)}
                for routine in self.list()
            ],
        }
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        temporary.replace(self.path)
