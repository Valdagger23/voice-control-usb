"""Assistant orchestration for the deterministic MVP."""

from __future__ import annotations

from pathlib import Path
from time import monotonic
from typing import Callable

from voice_control_usb.core.audit import (
    AuditEvent,
    AuditOutcome,
    AuditStore,
    JsonlAuditStore,
)
from voice_control_usb.core.models import Command
from voice_control_usb.core.parser import CommandParser
from voice_control_usb.core.proposals import ProposalStore
from voice_control_usb.core.safety import SafetyClass, SafetyPolicy
from voice_control_usb.core.session_context import PendingAction, SessionContext
from voice_control_usb.core.workflows import WorkflowRegistry
from voice_control_usb.desktop.adapter import DesktopAdapter, StubDesktopAdapter
from voice_control_usb.desktop.registry import AppAliasRegistry
from voice_control_usb.excel.adapter import ExcelAdapter, StubExcelAdapter
from voice_control_usb.executor.engine import ExecutionEngine

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
        audit_store: AuditStore | None = None,
        session_context: SessionContext | None = None,
    ) -> None:
        self.workflow_registry = workflow_registry or WorkflowRegistry.load_default()
        self.parser = CommandParser()
        self.executor = ExecutionEngine(
            excel=excel or StubExcelAdapter(),
            desktop=desktop or StubDesktopAdapter(aliases=AppAliasRegistry.load_default()),
            workflow_registry=self.workflow_registry,
        )
        self.safety = SafetyPolicy(self.workflow_registry, self.executor.registry)
        self.proposals = ProposalStore(proposal_path)
        self.audit = audit_store or JsonlAuditStore(proposal_path.with_name("audit.jsonl"))
        self.pending_action_timeout_seconds = pending_action_timeout_seconds
        self.clock = clock or monotonic
        self.context = session_context or SessionContext()

    @property
    def pending_action(self) -> PendingAction | None:
        """Compatibility view over application-neutral session context."""

        return self.context.pending_action

    @pending_action.setter
    def pending_action(self, value: PendingAction | None) -> None:
        self.context.pending_action = value

    def handle_text(self, text: str) -> str:
        expired_action = self._expire_pending_action_if_needed()
        parsed = self.parser.parse(text)
        if parsed.command:
            command = parsed.command
            decision = self.safety.classify(command)
            if command.action == "report_status":
                message = self._status_message(expired_action)
                return self._record_response(
                    command,
                    decision.safety_class,
                    AuditOutcome.STATUS,
                    message,
                )

            if decision.safety_class is SafetyClass.CONFIRM:
                if self.pending_action is None:
                    message = self._append_expired_notice(
                        "No pending action to confirm.",
                        expired_action,
                    )
                    return self._record_response(
                        command,
                        decision.safety_class,
                        AuditOutcome.STATUS,
                        message,
                    )
                pending = self.pending_action
                try:
                    result = self.executor.execute_result(pending.command)
                except Exception as error:
                    self._record_response(
                        command,
                        decision.safety_class,
                        AuditOutcome.FAILED,
                        str(error),
                        details={"confirmed_action": pending.command.action},
                    )
                    raise
                self.pending_action = None
                return self._record_response(
                    command,
                    decision.safety_class,
                    AuditOutcome.SUCCEEDED,
                    f"Confirmed. {result.message}",
                    details={
                        "confirmed_action": pending.command.action,
                        "confirmed_capability": result.capability_id,
                    },
                )
            if decision.safety_class is SafetyClass.CANCEL:
                if self.pending_action is None:
                    message = self._append_expired_notice(
                        "No pending action to cancel.",
                        expired_action,
                    )
                    return self._record_response(
                        command,
                        decision.safety_class,
                        AuditOutcome.STATUS,
                        message,
                    )
                canceled = self.pending_action.description
                self.pending_action = None
                return self._record_response(
                    command,
                    decision.safety_class,
                    AuditOutcome.CANCELED,
                    f"Canceled pending action: {canceled}",
                    details={"canceled_action": canceled},
                )
            if decision.safety_class is SafetyClass.BLOCKED:
                return self._record_response(
                    command,
                    decision.safety_class,
                    AuditOutcome.BLOCKED,
                    decision.message,
                )
            if decision.safety_class is SafetyClass.REQUIRES_CONFIRMATION:
                if self.pending_action is not None:
                    message = (
                        f"Pending confirmation already required for: {self.pending_action.description}. "
                        "Type confirm or cancel first."
                    )
                    return self._record_response(
                        command,
                        decision.safety_class,
                        AuditOutcome.BLOCKED,
                        message,
                    )
                self.pending_action = self._build_pending_action(command)
                message = self._format_confirmation_required_message(decision.message)
                return self._record_response(
                    command,
                    decision.safety_class,
                    AuditOutcome.CONFIRMATION_REQUIRED,
                    message,
                )

            try:
                result = self.executor.execute_result(command)
            except Exception as error:
                self._record_response(
                    command,
                    decision.safety_class,
                    AuditOutcome.FAILED,
                    str(error),
                )
                raise
            return self._record_response(
                command,
                decision.safety_class,
                AuditOutcome.SUCCEEDED,
                result.message,
                details=result.details,
            )

        assert parsed.proposal is not None
        self.proposals.record(parsed.proposal)
        message = f"Unsupported command logged for review: {parsed.proposal.reason}"
        self.audit.record(
            AuditEvent.create(
                source_text=parsed.proposal.source_text,
                outcome=AuditOutcome.UNSUPPORTED,
                message=message,
            )
        )
        return message

    def _record_response(
        self,
        command: Command,
        safety_class: SafetyClass,
        outcome: AuditOutcome,
        message: str,
        *,
        details: dict[str, object] | None = None,
    ) -> str:
        spec = self.executor.registry.spec_for(command.action)
        self.audit.record(
            AuditEvent.create(
                source_text=command.source_text,
                command_name=command.name,
                capability_id=None if spec is None else spec.capability_id,
                action_id=command.action,
                safety_class=safety_class.value,
                outcome=outcome,
                message=message,
                details=details,
            )
        )
        return message

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
