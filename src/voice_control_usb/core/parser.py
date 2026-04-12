"""Strict deterministic parser for the phase-1 command set."""

from __future__ import annotations

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
            arguments = self._apply_transforms(arguments, definition.argument_transforms)

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
    ) -> dict[str, str]:
        transformed = dict(arguments)
        for argument, transform in transforms.items():
            value = transformed.get(argument)
            if value is None:
                continue
            if transform == "strip":
                transformed[argument] = value.strip()
            if transform == "upper":
                transformed[argument] = value.upper()
        return transformed

    def _unsupported(self, text: str, reason: str) -> ParseResult:
        return ParseResult(
            proposal=UnsupportedProposal(
                source_text=text,
                reason=reason,
            )
        )
