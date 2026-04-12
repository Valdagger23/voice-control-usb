"""Shared command and proposal models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class CommandName(str, Enum):
    """Known deterministic commands for the phase-1 MVP."""

    OPEN_EXCEL = "open_excel"
    READ_CELL = "read_cell"
    WRITE_CELL = "write_cell"


@dataclass(frozen=True, slots=True)
class Command:
    """Normalized command produced by the strict parser."""

    name: CommandName
    arguments: dict[str, str] = field(default_factory=dict)
    source_text: str = ""


@dataclass(frozen=True, slots=True)
class UnsupportedProposal:
    """Reviewable proposal generated for unsupported input."""

    source_text: str
    reason: str


@dataclass(frozen=True, slots=True)
class ParseResult:
    """Parse output that keeps unknown commands out of the executor."""

    command: Command | None = None
    proposal: UnsupportedProposal | None = None

    @property
    def is_supported(self) -> bool:
        return self.command is not None
