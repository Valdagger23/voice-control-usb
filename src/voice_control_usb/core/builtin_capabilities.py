"""Action contracts owned by the assistant and workflow runtime."""

from __future__ import annotations

from voice_control_usb.core.capabilities import (
    ActionBinding,
    ActionSpec,
    CapabilityRegistry,
    SafetyClass,
)
from voice_control_usb.core.models import Command
from voice_control_usb.core.workflows import WorkflowRegistry


def assistant_action_specs() -> list[ActionSpec]:
    return [
        ActionSpec(
            capability_id="assistant",
            action_id="confirm_pending",
            description="Confirm the current pending action.",
            safety_class=SafetyClass.CONFIRM,
        ),
        ActionSpec(
            capability_id="assistant",
            action_id="cancel_pending",
            description="Cancel the current pending action.",
            safety_class=SafetyClass.CANCEL,
        ),
        ActionSpec(
            capability_id="assistant",
            action_id="report_status",
            description="Report the assistant confirmation state.",
        ),
    ]


def workflow_action_specs() -> list[ActionSpec]:
    return [
        ActionSpec(
            capability_id="workflow",
            action_id="run_workflow",
            description="Run an approved deterministic workflow.",
            argument_types={"workflow_name": str},
        )
    ]


class WorkflowCapability:
    """Expand approved workflows through the same capability registry."""

    capability_id = "workflow"

    def __init__(
        self,
        workflows: WorkflowRegistry,
        action_registry: CapabilityRegistry,
    ) -> None:
        self.workflows = workflows
        self.action_registry = action_registry

    def bindings(self) -> list[ActionBinding]:
        spec = workflow_action_specs()[0]
        return [ActionBinding(spec, self._run_workflow)]

    def _run_workflow(self, command: Command) -> str:
        workflow_name = command.arguments.get("workflow_name")
        if not isinstance(workflow_name, str):
            raise ValueError("Workflow name must be a string.")
        workflow = self.workflows.get(workflow_name)
        if workflow is None:
            raise ValueError(f"Unknown workflow requested: {workflow_name}")

        last_result = ""
        for index, step in enumerate(workflow.steps, start=1):
            step_command = Command(
                name=f"{workflow.name}_step_{index}",
                action=step.action,
                arguments=step.arguments,
                source_text=command.source_text,
            )
            last_result = self.action_registry.execute(step_command).message

        return f"Workflow '{workflow.name}' completed. Final result: {last_result}"
