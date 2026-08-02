"""Application-neutral state retained for one assistant session."""

from __future__ import annotations

from dataclasses import dataclass, field

from voice_control_usb.core.models import Command


@dataclass(frozen=True, slots=True)
class PendingAction:
    """Approved command waiting for explicit user confirmation."""

    command: Command
    description: str
    created_at: float
    expires_at: float | None = None


@dataclass(slots=True)
class SessionContext:
    """Core session state plus isolated state owned by capabilities."""

    pending_action: PendingAction | None = None
    capability_state: dict[str, object] = field(default_factory=dict)

    def get_capability_state(self, capability_id: str) -> object | None:
        return self.capability_state.get(capability_id)

    def set_capability_state(self, capability_id: str, state: object) -> None:
        if not capability_id.strip():
            raise ValueError("Capability ID must not be empty.")
        self.capability_state[capability_id] = state

    def clear_capability_state(self, capability_id: str) -> None:
        self.capability_state.pop(capability_id, None)
