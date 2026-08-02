"""Structured audit events for assistant decisions and outcomes."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path


class AuditOutcome(str, Enum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"
    CONFIRMATION_REQUIRED = "confirmation_required"
    CANCELED = "canceled"
    UNSUPPORTED = "unsupported"
    STATUS = "status"


@dataclass(frozen=True, slots=True)
class AuditEvent:
    """One user-visible assistant decision or execution outcome."""

    timestamp: str
    source_text: str
    outcome: AuditOutcome
    message: str
    command_name: str | None = None
    capability_id: str | None = None
    action_id: str | None = None
    safety_class: str | None = None
    details: dict[str, object] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        source_text: str,
        outcome: AuditOutcome,
        message: str,
        command_name: str | None = None,
        capability_id: str | None = None,
        action_id: str | None = None,
        safety_class: str | None = None,
        details: dict[str, object] | None = None,
    ) -> "AuditEvent":
        return cls(
            timestamp=datetime.now(timezone.utc).isoformat(),
            source_text=source_text,
            outcome=outcome,
            message=message,
            command_name=command_name,
            capability_id=capability_id,
            action_id=action_id,
            safety_class=safety_class,
            details={} if details is None else dict(details),
        )


class AuditStore:
    """Persistence boundary for structured audit events."""

    def record(self, event: AuditEvent) -> None:
        raise NotImplementedError


class JsonlAuditStore(AuditStore):
    """Append audit events to a portable JSONL log."""

    def __init__(self, output_path: Path) -> None:
        self.output_path = output_path

    def record(self, event: AuditEvent) -> None:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with self.output_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(event), ensure_ascii=False) + "\n")


class InMemoryAuditStore(AuditStore):
    """Test store that keeps events in execution order."""

    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def record(self, event: AuditEvent) -> None:
        self.events.append(event)
