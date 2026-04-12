"""Deterministic safety policy for approved, confirmable, and blocked actions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from voice_control_usb.core.models import Command
from voice_control_usb.core.workflows import WorkflowRegistry


class SafetyClass(str, Enum):
    ALLOWED = "allowed"
    REQUIRES_CONFIRMATION = "requires_confirmation"
    BLOCKED = "blocked"
    CONFIRM = "confirm"
    CANCEL = "cancel"


@dataclass(frozen=True, slots=True)
class SafetyDecision:
    """Classification result for a parsed command."""

    safety_class: SafetyClass
    message: str = ""


class SafetyPolicy:
    """Classify parsed commands before execution."""

    def __init__(self, workflow_registry: WorkflowRegistry) -> None:
        self.workflow_registry = workflow_registry

    def classify(self, command: Command) -> SafetyDecision:
        return self._classify_action(command.action, command.arguments, command.source_text)

    def _classify_action(
        self,
        action: str,
        arguments: dict[str, str],
        source_text: str,
    ) -> SafetyDecision:
        if action == "confirm_pending":
            return SafetyDecision(SafetyClass.CONFIRM)
        if action == "cancel_pending":
            return SafetyDecision(SafetyClass.CANCEL)
        if action == "blocked_desktop_action":
            request = arguments.get("request", source_text)
            return SafetyDecision(
                SafetyClass.BLOCKED,
                f"Desktop action is blocked in MVP: {request}",
            )
        if action in {"shutdown", "restart"}:
            return SafetyDecision(
                SafetyClass.REQUIRES_CONFIRMATION,
                f"Confirmation required for risky action: {source_text}. Type confirm to proceed or cancel.",
            )
        if action == "run_workflow":
            workflow_name = arguments["workflow_name"]
            workflow = self.workflow_registry.get(workflow_name)
            if workflow is None:
                return SafetyDecision(
                    SafetyClass.BLOCKED,
                    f"Workflow is not approved in MVP: {workflow_name}",
                )

            highest = SafetyDecision(SafetyClass.ALLOWED)
            for step in workflow.steps:
                step_decision = self._classify_action(step.action, step.arguments, workflow.name)
                if step_decision.safety_class is SafetyClass.BLOCKED:
                    return SafetyDecision(
                        SafetyClass.BLOCKED,
                        f"Workflow '{workflow.name}' is blocked in MVP because it contains a blocked action.",
                    )
                if step_decision.safety_class is SafetyClass.REQUIRES_CONFIRMATION:
                    highest = SafetyDecision(
                        SafetyClass.REQUIRES_CONFIRMATION,
                        f"Confirmation required for workflow '{workflow.name}'. Type confirm to proceed or cancel.",
                    )
            return highest

        return SafetyDecision(SafetyClass.ALLOWED)
