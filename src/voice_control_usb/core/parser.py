"""Strict deterministic parser for the phase-1 command set."""

from __future__ import annotations

import re

from voice_control_usb.core.models import Command, ParseResult, UnsupportedProposal
from voice_control_usb.core.registry import CommandRegistry


class CommandParser:
    """Parse text by consulting the external deterministic command registry."""

    def __init__(self, registry: CommandRegistry | None = None) -> None:
        self.registry = registry or CommandRegistry.load_default()

    def parse(self, text: str) -> ParseResult:
        normalized = " ".join(text.strip().split())
        if not normalized:
            return ParseResult(
                proposal=UnsupportedProposal(
                    source_text=text,
                    reason="Empty input cannot be routed deterministically.",
                )
            )

        for definition in self.registry.definitions:
            match = definition.regex.fullmatch(normalized)
            if not match:
                continue

            arguments = {
                key: value
                for key, value in match.groupdict().items()
                if value is not None
            }
            arguments.update(definition.fixed_arguments)
            try:
                arguments = self._apply_transforms(arguments, definition.argument_transforms)
            except ValueError as error:
                return self._unsupported(normalized, str(error))

            return ParseResult(
                command=Command(
                    name=definition.name,
                    action=definition.action,
                    arguments=arguments,
                    source_text=normalized,
                )
            )

        return self._unsupported(
            normalized,
            "Command is not part of the approved deterministic command registry.",
        )

    def _apply_transforms(
        self,
        arguments: dict[str, str],
        transforms: dict[str, str],
    ) -> dict[str, object]:
        transformed: dict[str, object] = dict(arguments)
        for argument, transform in transforms.items():
            value = transformed.get(argument)
            if not isinstance(value, str):
                continue
            if transform == "lower":
                transformed[argument] = value.lower()
            elif transform == "strip":
                transformed[argument] = value.strip()
            elif transform == "upper":
                transformed[argument] = value.upper()
            elif transform == "excel_value":
                transformed[argument] = self._excel_value(value)
            elif transform == "excel_cell":
                transformed[argument] = self._excel_cell(value)
            elif transform == "excel_range":
                transformed[argument] = self._excel_range(value)
            elif transform == "excel_formula":
                transformed[argument] = self._excel_formula(value)
            elif transform == "percentage":
                transformed[argument] = self._percentage(value)
            elif transform == "positive_integer":
                transformed[argument] = self._positive_integer(value)
            else:
                raise ValueError(f"Unknown command argument transform: {transform}")
        return transformed

    @staticmethod
    def _excel_value(value: str) -> str | int | float:
        normalized = value.strip()
        if len(normalized) > 32_767:
            raise ValueError("Excel cell text may not exceed 32,767 characters.")
        if re.fullmatch(r"[+-]?\d+", normalized):
            return int(normalized)
        if re.fullmatch(r"[+-]?(?:\d+\.\d*|\.\d+)", normalized):
            return float(normalized)
        return normalized

    @staticmethod
    def _excel_cell(value: str) -> str:
        normalized = value.upper()
        match = re.fullmatch(r"([A-Z]{1,3})([1-9][0-9]{0,6})", normalized)
        if match is None:
            raise ValueError(f"Invalid Excel cell reference: {value}")
        letters, row_text = match.groups()
        column = 0
        for character in letters:
            column = column * 26 + ord(character) - ord("A") + 1
        if column > 16_384 or int(row_text) > 1_048_576:
            raise ValueError(f"Excel cell is outside worksheet bounds: {normalized}")
        return normalized

    @classmethod
    def _excel_range(cls, value: str) -> str:
        parts = value.upper().split(":")
        if len(parts) not in {1, 2}:
            raise ValueError(f"Invalid Excel range: {value}")
        normalized = [cls._excel_cell(part) for part in parts]
        return ":".join(normalized)

    @staticmethod
    def _excel_formula(value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Excel formula must not be empty.")
        if len(normalized) > 8_192:
            raise ValueError("Excel formula may not exceed 8,192 characters.")
        return normalized if normalized.startswith("=") else f"={normalized}"

    @staticmethod
    def _percentage(value: str) -> int:
        percent = int(value)
        if not 0 <= percent <= 100:
            raise ValueError("Percentage must be between 0 and 100.")
        return percent

    @staticmethod
    def _positive_integer(value: str) -> int:
        number = int(value)
        if number < 1:
            raise ValueError("Number must be at least 1.")
        return number

    def _unsupported(self, text: str, reason: str) -> ParseResult:
        return ParseResult(
            proposal=UnsupportedProposal(
                source_text=text,
                reason=reason,
            )
        )
