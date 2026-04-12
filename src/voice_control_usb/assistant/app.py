"""Assistant orchestration for the deterministic MVP."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

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

    command: object
    description: str


class AssistantApp:
    """Glue parser, executor, and proposal logging together."""

    def __init__(
        self,
        proposal_path: Path,
        excel: ExcelAdapter | None = None,
        desktop: DesktopAdapter | None = None,
        workflow_registry: WorkflowRegistry | None = None,
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
        self.pending_action: PendingAction | None = None

    def handle_text(self, text: str) -> str:
        parsed = self.parser.parse(text)
        if parsed.command:
            decision = self.safety.classify(parsed.command)
            if decision.safety_class is SafetyClass.CONFIRM:
                if self.pending_action is None:
                    return "No pending action to confirm."
                result = self.executor.execute(self.pending_action.command)
                self.pending_action = None
                return f"Confirmed. {result}"
            if decision.safety_class is SafetyClass.CANCEL:
                if self.pending_action is None:
                    return "No pending action to cancel."
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
                self.pending_action = PendingAction(
                    command=parsed.command,
                    description=parsed.command.source_text,
                )
                return decision.message

            return self.executor.execute(parsed.command)

        assert parsed.proposal is not None
        self.proposals.record(parsed.proposal)
        return f"Unsupported command logged for review: {parsed.proposal.reason}"
