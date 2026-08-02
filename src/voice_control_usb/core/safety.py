"""Deterministic safety policy for approved, confirmable, and blocked actions."""

from __future__ import annotations

from dataclasses import dataclass

from voice_control_usb.core.capabilities import CapabilityRegistry, SafetyClass
from voice_control_usb.core.models import Command
from voice_control_usb.core.workflows import WorkflowRegistry


@dataclass(frozen=True, slots=True)
class SafetyDecision:
    """Classification result for a parsed command."""

    safety_class: SafetyClass
    message: str = ""


class SafetyPolicy:
    """Classify parsed commands before execution."""

    def __init__(
        self,
        workflow_registry: WorkflowRegistry,
        action_catalog: CapabilityRegistry | None = None,
    ) -> None:
        self.workflow_registry = workflow_registry
        self.action_catalog = action_catalog

    def classify(self, command: Command) -> SafetyDecision:
        return self._classify_action(command.action, command.arguments, command.source_text)

    def _classify_action(
        self,
        action: str,
        arguments: dict[str, object],
        source_text: str,
    ) -> SafetyDecision:
        safety_class = self._declared_safety_class(action)
        if safety_class is SafetyClass.CONFIRM:
            return SafetyDecision(safety_class)
        if safety_class is SafetyClass.CANCEL:
            return SafetyDecision(safety_class)
        if safety_class is SafetyClass.BLOCKED:
            if action != "blocked_desktop_action":
                return SafetyDecision(
                    safety_class,
                    f"Action is not approved: {action}",
                )
            request = arguments.get("request", source_text)
            return SafetyDecision(
                safety_class,
                f"Desktop action is blocked in MVP: {request}",
            )
        if safety_class is SafetyClass.REQUIRES_CONFIRMATION:
            return SafetyDecision(
                safety_class,
                f"Confirmation required for risky action: {source_text}. Type confirm to proceed or cancel.",
            )
        if action == "run_workflow":
            workflow_name = arguments.get("workflow_name")
            if not isinstance(workflow_name, str):
                return SafetyDecision(
                    SafetyClass.BLOCKED,
                    "Workflow name must be a string.",
                )
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

        return SafetyDecision(safety_class)

    def _declared_safety_class(self, action: str) -> SafetyClass:
        if self.action_catalog is not None:
            spec = self.action_catalog.spec_for(action)
            if spec is None:
                return SafetyClass.BLOCKED
            return spec.safety_class

        # Transitional compatibility for direct SafetyPolicy users. The running
        # assistant always supplies the capability catalog as the source of truth.
        if action == "confirm_pending":
            return SafetyClass.CONFIRM
        if action == "cancel_pending":
            return SafetyClass.CANCEL
        if action == "blocked_desktop_action":
            return SafetyClass.BLOCKED
        if action in {"shutdown", "restart"}:
            return SafetyClass.REQUIRES_CONFIRMATION
        return SafetyClass.ALLOWED
