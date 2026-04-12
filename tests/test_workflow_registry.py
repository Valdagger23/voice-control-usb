"""Tests for deterministic workflow registry validation."""

from __future__ import annotations

import unittest

from voice_control_usb.core.workflows import WorkflowRegistry


class WorkflowRegistryTests(unittest.TestCase):
    def test_unknown_action_in_workflow_definition_is_rejected(self) -> None:
        registry = WorkflowRegistry.from_data(
            {
                "workflows": [
                    {
                        "name": "bad_workflow",
                        "description": "Invalid workflow",
                        "steps": [
                            {
                                "action": "arbitrary_shell",
                                "arguments": {},
                            }
                        ],
                    }
                ]
            }
        )

        with self.assertRaisesRegex(ValueError, "references unsupported action"):
            registry.validate({"open_excel", "go_to_cell"})

    def test_empty_workflow_is_rejected(self) -> None:
        registry = WorkflowRegistry.from_data(
            {
                "workflows": [
                    {
                        "name": "empty_workflow",
                        "description": "Invalid workflow",
                        "steps": [],
                    }
                ]
            }
        )

        with self.assertRaisesRegex(ValueError, "must contain at least one step"):
            registry.validate({"open_excel"})


if __name__ == "__main__":
    unittest.main()
