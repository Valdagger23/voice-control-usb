"""Assistant orchestration for the deterministic MVP."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import monotonic
from typing import Callable

from voice_control_usb.core.models import Command
from voice_control_usb.core.parser import CommandParser
from voice_control_usb.core.proposals import ProposalStore
from voice_control_usb.core.safety import SafetyClass, SafetyPolicy
from voice_control_usb.core.workflows import WorkflowRegistry
from voice_control_usb.desktop.adapter import DesktopAdapter, StubDesktopAdapter
from voice_control_usb.desktop.registry import AppAliasRegistry
from voice_control_usb.excel.adapter import ExcelAdapter, StubExcelAdapter
from voice_control_usb.executor.engine import ExecutionEngine


@dataclass(frozen=True, slots=True)
class PendingAction:
    """Risky action waiting for confirmation."""

    command: Command
    description: str
    created_at: float
    expires_at: float | None = None


class AssistantApp:
    """Glue parser, executor, and proposal logging together."""

    CONFIRMATION_ALERT_PREFIX = "[CONFIRMATION REQUIRED]"

    def __init__(
        self,
        proposal_path: Path,
        excel: ExcelAdapter | None = None,
        desktop: DesktopAdapter | None = None,
        workflow_registry: WorkflowRegistry | None = None,
        pending_action_timeout_seconds: float | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self.workflow_registry = workflow_registry or WorkflowRegistry.load_default()
        self.parser = CommandParser()
        self.executor = ExecutionEngine(
            excel=excel or StubExcelAdapter(),
            desktop=desktop or StubDesktopAdapter(aliases=AppAliasRegistry.load_default()),
            workflow_registry=self.workflow_registry,
        )
        self.safety = SafetyPolicy(self.workflow_registry)
        self.proposals = ProposalStore(proposal_path)
        self.pending_action_timeout_seconds = pending_action_timeout_seconds
        self.clock = clock or monotonic
        self.pending_action: PendingAction | None = None

    def handle_text(self, text: str) -> str:
        expired_action = self._expire_pending_action_if_needed()
        parsed = self.parser.parse(text)
        if parsed.command:
            if parsed.command.action == "report_status":
                return self._status_message(expired_action)

            decision = self.safety.classify(parsed.command)
            if decision.safety_class is SafetyClass.CONFIRM:
                if self.pending_action is None:
                    return self._append_expired_notice(
                        "No pending action to confirm.",
                        expired_action,
                    )
                result = self.executor.execute(self.pending_action.command)
                self.pending_action = None
                return f"Confirmed. {result}"
            if decision.safety_class is SafetyClass.CANCEL:
                if self.pending_action is None:
                    return self._append_expired_notice(
                        "No pending action to cancel.",
                        expired_action,
                    )
                canceled = self.pending_action.description
                self.pending_action = None
                return f"Canceled pending action: {canceled}"
            if decision.safety_class is SafetyClass.BLOCKED:
                return decision.message
            if decision.safety_class is SafetyClass.REQUIRES_CONFIRMATION:
                if self.pending_action is not None:
                    return (
                        f"Pending confirmation already required for: {self.pending_action.description}. "
                        "Type confirm or cancel first."
                    )
                self.pending_action = self._build_pending_action(parsed.command)
                return self._format_confirmation_required_message(decision.message)

            return self.executor.execute(parsed.command)

        assert parsed.proposal is not None
        self.proposals.record(parsed.proposal)
        return f"Unsupported command logged for review: {parsed.proposal.reason}"

    def _build_pending_action(self, command: Command) -> PendingAction:
        created_at = self.clock()
        expires_at = None
        if self.pending_action_timeout_seconds is not None:
            expires_at = created_at + self.pending_action_timeout_seconds
        return PendingAction(
            command=command,
            description=command.source_text,
            created_at=created_at,
            expires_at=expires_at,
        )

    def _expire_pending_action_if_needed(self) -> PendingAction | None:
        pending = self.pending_action
        if pending is None or pending.expires_at is None:
            return None
        if self.clock() < pending.expires_at:
            return None
        self.pending_action = None
        return pending

    def _status_message(self, expired_action: PendingAction | None) -> str:
        pending = self.pending_action
        if pending is None:
            return self._append_expired_notice(
                "No pending confirmation action.",
                expired_action,
            )

        message = (
            f"Pending confirmation: {pending.description}. "
            "Type confirm to proceed or cancel."
        )
        if self.pending_action_timeout_seconds is not None:
            message += f" Timeout: {self._format_timeout(self.pending_action_timeout_seconds)}."
        return message

    def _format_confirmation_required_message(self, message: str) -> str:
        return f"{self.CONFIRMATION_ALERT_PREFIX} {message}"

    def _append_expired_notice(
        self,
        message: str,
        expired_action: PendingAction | None,
    ) -> str:
        if expired_action is None:
            return message
        return (
            f"{message} "
            f"The previous pending action expired: {expired_action.description}."
        )

    @staticmethod
    def _format_timeout(timeout_seconds: float) -> str:
        timeout_value = float(timeout_seconds)
        if timeout_value.is_integer():
            return f"{int(timeout_value)}s"
        return f"{timeout_value:g}s"
