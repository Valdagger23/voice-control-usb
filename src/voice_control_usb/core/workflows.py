"""Registry loader and validator for deterministic workflows."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any

from voice_control_usb.runtime_support import resolve_packaged_data_path


@dataclass(frozen=True, slots=True)
class WorkflowStep:
    """Single deterministic action inside a workflow."""

    action: str
    arguments: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class WorkflowDefinition:
    """Approved workflow definition."""

    name: str
    description: str
    steps: list[WorkflowStep]


class WorkflowRegistry:
    """Load and validate approved deterministic workflows."""

    def __init__(self, workflows: dict[str, WorkflowDefinition]) -> None:
        self.workflows = workflows

    @classmethod
    def load_default(cls) -> "WorkflowRegistry":
        return cls.from_path(resolve_packaged_data_path("core", "workflow_registry.json"))

    @classmethod
    def from_path(cls, path: Path) -> "WorkflowRegistry":
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return cls.from_data(data)

    @classmethod
    def from_data(cls, data: dict[str, Any]) -> "WorkflowRegistry":
        workflows: dict[str, WorkflowDefinition] = {}
        for item in data.get("workflows", []):
            name = item["name"]
            steps = [
                WorkflowStep(
                    action=step["action"],
                    arguments=dict(step.get("arguments", {})),
                )
                for step in item.get("steps", [])
            ]
            workflows[name] = WorkflowDefinition(
                name=name,
                description=item["description"],
                steps=steps,
            )
        return cls(workflows=workflows)

    def get(self, name: str) -> WorkflowDefinition | None:
        return self.workflows.get(name)

    def validate(self, allowed_actions: set[str]) -> None:
        for workflow in self.workflows.values():
            if not workflow.steps:
                raise ValueError(f"Workflow '{workflow.name}' must contain at least one step.")
            for step in workflow.steps:
                if step.action == "run_workflow":
                    raise ValueError(
                        f"Workflow '{workflow.name}' may not reference nested workflows."
                    )
                if step.action not in allowed_actions:
                    raise ValueError(
                        f"Workflow '{workflow.name}' references unsupported action '{step.action}'."
                    )
                if not isinstance(step.arguments, dict):
                    raise ValueError(
                        f"Workflow '{workflow.name}' step arguments must be a string map."
                    )
