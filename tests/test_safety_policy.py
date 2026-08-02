"""Tests for deterministic safety classification."""

from __future__ import annotations

import unittest

from voice_control_usb.core.capabilities import ActionSpec, CapabilityRegistry, SafetyClass
from voice_control_usb.core.models import Command
from voice_control_usb.core.safety import SafetyPolicy
from voice_control_usb.core.workflows import WorkflowRegistry


class SafetyPolicyTests(unittest.TestCase):
    def test_running_assistant_policy_uses_declared_capability_safety(self) -> None:
        catalog = CapabilityRegistry(
            [
                ActionSpec(
                    capability_id="privacy",
                    action_id="enable_camera",
                    description="Enable the camera.",
                    safety_class=SafetyClass.REQUIRES_CONFIRMATION,
                )
            ]
        )
        policy = SafetyPolicy(WorkflowRegistry.from_data({}), catalog)

        decision = policy.classify(
            Command(
                name="enable_camera",
                action="enable_camera",
                source_text="turn camera on",
            )
        )

        self.assertIs(decision.safety_class, SafetyClass.REQUIRES_CONFIRMATION)

    def test_unknown_catalog_action_is_blocked(self) -> None:
        policy = SafetyPolicy(WorkflowRegistry.from_data({}), CapabilityRegistry())

        decision = policy.classify(Command(name="unknown", action="unknown"))

        self.assertIs(decision.safety_class, SafetyClass.BLOCKED)
        self.assertEqual(decision.message, "Action is not approved: unknown")

    def test_safe_action_is_allowed(self) -> None:
        policy = SafetyPolicy(WorkflowRegistry.load_default())

        decision = policy.classify(
            Command(name="open_excel", action="open_excel", source_text="open excel")
        )

        self.assertIs(decision.safety_class, SafetyClass.ALLOWED)

    def test_risky_action_requires_confirmation(self) -> None:
        policy = SafetyPolicy(WorkflowRegistry.load_default())

        decision = policy.classify(
            Command(name="shutdown", action="shutdown", source_text="shutdown")
        )

        self.assertIs(decision.safety_class, SafetyClass.REQUIRES_CONFIRMATION)

    def test_blocked_action_stays_blocked(self) -> None:
        policy = SafetyPolicy(WorkflowRegistry.load_default())

        decision = policy.classify(
            Command(
                name="reject_run_command",
                action="blocked_desktop_action",
                arguments={"request": "dir"},
                source_text="run command dir",
            )
        )

        self.assertIs(decision.safety_class, SafetyClass.BLOCKED)

    def test_workflow_with_confirmation_required_step_requires_confirmation(self) -> None:
        registry = WorkflowRegistry.from_data(
            {
                "workflows": [
                    {
                        "name": "risky_workflow",
                        "description": "Contains restart",
                        "steps": [
                            {"action": "restart", "arguments": {}},
                        ],
                    }
                ]
            }
        )
        policy = SafetyPolicy(registry)

        decision = policy.classify(
            Command(
                name="workflow_risky",
                action="run_workflow",
                arguments={"workflow_name": "risky_workflow"},
                source_text="risky workflow",
            )
        )

        self.assertIs(decision.safety_class, SafetyClass.REQUIRES_CONFIRMATION)

    def test_workflow_with_blocked_step_is_blocked(self) -> None:
        registry = WorkflowRegistry.from_data(
            {
                "workflows": [
                    {
                        "name": "blocked_workflow",
                        "description": "Contains blocked action",
                        "steps": [
                            {"action": "blocked_desktop_action", "arguments": {"request": "dir"}},
                        ],
                    }
                ]
            }
        )
        policy = SafetyPolicy(registry)

        decision = policy.classify(
            Command(
                name="workflow_blocked",
                action="run_workflow",
                arguments={"workflow_name": "blocked_workflow"},
                source_text="blocked workflow",
            )
        )

        self.assertIs(decision.safety_class, SafetyClass.BLOCKED)
