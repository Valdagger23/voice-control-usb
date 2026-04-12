"""Strict deterministic parser for the phase-1 command set."""

from __future__ import annotations

import re

from voice_control_usb.core.models import Command, CommandName, ParseResult, UnsupportedProposal

CELL_RE = re.compile(r"^[A-Z]{1,3}[1-9][0-9]{0,6}$")


class CommandParser:
    """Parse a narrow command language into structured commands."""

    def parse(self, text: str) -> ParseResult:
        normalized = " ".join(text.strip().split())
        if not normalized:
            return ParseResult(
                proposal=UnsupportedProposal(
                    source_text=text,
                    reason="Empty input cannot be routed deterministically.",
                )
            )

        lowered = normalized.casefold()
        if lowered == "open excel":
            return ParseResult(
                command=Command(
                    name=CommandName.OPEN_EXCEL,
                    source_text=normalized,
                )
            )

        if lowered.startswith("read cell "):
            cell = normalized[len("read cell ") :].strip().upper()
            if self._is_cell_reference(cell):
                return ParseResult(
                    command=Command(
                        name=CommandName.READ_CELL,
                        arguments={"cell": cell},
                        source_text=normalized,
                    )
                )
            return self._unsupported(normalized, "Cell reference must look like A1 or AA10.")

        if lowered.startswith("write cell "):
            remainder = normalized[len("write cell ") :].strip()
            cell, separator, value = remainder.partition(" value ")
            if not separator:
                return self._unsupported(
                    normalized,
                    "Write command must use 'write cell <CELL> value <TEXT>'.",
                )

            cell = cell.strip().upper()
            if not self._is_cell_reference(cell):
                return self._unsupported(normalized, "Cell reference must look like A1 or AA10.")
            if not value:
                return self._unsupported(normalized, "Write command requires a non-empty value.")

            return ParseResult(
                command=Command(
                    name=CommandName.WRITE_CELL,
                    arguments={"cell": cell, "value": value},
                    source_text=normalized,
                )
            )

        return self._unsupported(
            normalized,
            "Command is not part of the approved deterministic MVP command set.",
        )

    def _is_cell_reference(self, value: str) -> bool:
        return bool(CELL_RE.fullmatch(value))

    def _unsupported(self, text: str, reason: str) -> ParseResult:
        return ParseResult(
            proposal=UnsupportedProposal(
                source_text=text,
                reason=reason,
            )
        )
