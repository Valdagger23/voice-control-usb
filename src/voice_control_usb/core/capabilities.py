"""Capability-neutral action contracts and deterministic routing."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol

from voice_control_usb.core.models import Command


class SafetyClass(str, Enum):
    """Safety class declared by an action contract."""

    ALLOWED = "allowed"
    REQUIRES_CONFIRMATION = "requires_confirmation"
    BLOCKED = "blocked"
    CONFIRM = "confirm"
    CANCEL = "cancel"


@dataclass(frozen=True, slots=True)
class ActionSpec:
    """Stable metadata for one action exposed by a capability."""

    capability_id: str
    action_id: str
    description: str
    safety_class: SafetyClass = SafetyClass.ALLOWED
    reversible: bool = False
    argument_types: dict[str, type[object]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.capability_id.strip():
            raise ValueError("Capability ID must not be empty.")
        if not self.action_id.strip():
            raise ValueError("Action ID must not be empty.")


@dataclass(frozen=True, slots=True)
class ActionResult:
    """Structured result returned by the capability execution boundary."""

    capability_id: str
    action_id: str
    message: str
    succeeded: bool = True
    details: dict[str, object] = field(default_factory=dict)


ActionHandler = Callable[[Command], ActionResult | str]


@dataclass(frozen=True, slots=True)
class ActionBinding:
    """Connect one declared action contract to its implementation handler."""

    spec: ActionSpec
    handler: ActionHandler


class Capability(Protocol):
    """Module boundary implemented by every executable capability pack."""

    capability_id: str

    def bindings(self) -> list[ActionBinding]:
        """Return all executable actions exposed by this capability."""


class CapabilityRegistry:
    """Catalog approved action contracts and route them to bound handlers."""

    def __init__(self, specs: Iterable[ActionSpec] = ()) -> None:
        self._specs: dict[str, ActionSpec] = {}
        self._handlers: dict[str, ActionHandler] = {}
        for spec in specs:
            self.declare(spec)

    def declare(self, spec: ActionSpec) -> None:
        existing = self._specs.get(spec.action_id)
        if existing is not None and existing != spec:
            raise ValueError(f"Action is already declared: {spec.action_id}")
        self._specs[spec.action_id] = spec

    def register(self, spec: ActionSpec, handler: ActionHandler) -> None:
        self.declare(spec)
        if spec.action_id in self._handlers:
            raise ValueError(f"Action handler is already registered: {spec.action_id}")
        self._handlers[spec.action_id] = handler

    def register_bindings(self, bindings: Iterable[ActionBinding]) -> None:
        for binding in bindings:
            self.register(binding.spec, binding.handler)

    def spec_for(self, action_id: str) -> ActionSpec | None:
        return self._specs.get(action_id)

    def action_ids(self, *, executable_only: bool = False) -> set[str]:
        if executable_only:
            return set(self._handlers)
        return set(self._specs)

    def execute(self, command: Command) -> ActionResult:
        spec = self.validate_command(command)
        handler = self._handlers[command.action]

        result = handler(command)
        if isinstance(result, str):
            return ActionResult(
                capability_id=spec.capability_id,
                action_id=spec.action_id,
                message=result,
            )
        if result.capability_id != spec.capability_id or result.action_id != spec.action_id:
            raise ValueError(
                f"Action result identity does not match registered action: {command.action}"
            )
        return result

    def validate_command(
        self,
        command: Command,
        *,
        require_handler: bool = True,
    ) -> ActionSpec:
        """Validate action identity, executability, and typed arguments."""

        spec = self._specs.get(command.action)
        if spec is None:
            raise ValueError(f"Action is not declared by any capability: {command.action}")
        if require_handler and command.action not in self._handlers:
            raise ValueError(f"Action has no execution handler: {command.action}")

        self._validate_arguments(spec, command)
        return spec

    @staticmethod
    def _validate_arguments(spec: ActionSpec, command: Command) -> None:
        expected_names = set(spec.argument_types)
        supplied_names = set(command.arguments)
        missing = expected_names - supplied_names
        if missing:
            names = ", ".join(sorted(missing))
            raise ValueError(f"Action '{spec.action_id}' is missing arguments: {names}")
        unexpected = supplied_names - expected_names
        if unexpected:
            names = ", ".join(sorted(unexpected))
            raise ValueError(f"Action '{spec.action_id}' received unexpected arguments: {names}")
        for name, expected_type in spec.argument_types.items():
            value = command.arguments[name]
            if not isinstance(value, expected_type):
                raise ValueError(
                    f"Action '{spec.action_id}' argument '{name}' must be "
                    f"{expected_type.__name__}."
                )
