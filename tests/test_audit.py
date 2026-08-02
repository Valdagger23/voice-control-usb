"""Tests for structured assistant audit events."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from voice_control_usb.assistant.app import AssistantApp
from voice_control_usb.core.audit import (
    AuditEvent,
    AuditOutcome,
    InMemoryAuditStore,
    JsonlAuditStore,
)


class AuditTests(unittest.TestCase):
    def test_supported_action_records_capability_and_policy_outcome(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            audit = InMemoryAuditStore()
            app = AssistantApp(
                proposal_path=Path(tmp_dir) / "proposals.jsonl",
                audit_store=audit,
            )

            result = app.handle_text("open excel")

            self.assertEqual(result, "Excel session ready (stub)")
            self.assertEqual(len(audit.events), 1)
            event = audit.events[0]
            self.assertEqual(event.capability_id, "excel")
            self.assertEqual(event.action_id, "open_excel")
            self.assertEqual(event.safety_class, "allowed")
            self.assertIs(event.outcome, AuditOutcome.SUCCEEDED)

    def test_confirmation_and_confirmed_execution_are_audited(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            audit = InMemoryAuditStore()
            app = AssistantApp(
                proposal_path=Path(tmp_dir) / "proposals.jsonl",
                audit_store=audit,
            )

            app.handle_text("restart")
            app.handle_text("confirm")

            self.assertEqual(
                [event.outcome for event in audit.events],
                [AuditOutcome.CONFIRMATION_REQUIRED, AuditOutcome.SUCCEEDED],
            )
            self.assertEqual(audit.events[0].capability_id, "desktop")
            self.assertEqual(audit.events[1].capability_id, "assistant")
            self.assertEqual(audit.events[1].details["confirmed_action"], "restart")

    def test_unsupported_input_is_audited_without_an_action_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            audit = InMemoryAuditStore()
            app = AssistantApp(
                proposal_path=Path(tmp_dir) / "proposals.jsonl",
                audit_store=audit,
            )

            app.handle_text("do something unknown")

            self.assertIs(audit.events[0].outcome, AuditOutcome.UNSUPPORTED)
            self.assertIsNone(audit.events[0].action_id)
            self.assertIsNone(audit.events[0].capability_id)

    def test_jsonl_store_serializes_structured_event(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "audit.jsonl"
            store = JsonlAuditStore(path)
            store.record(
                AuditEvent.create(
                    source_text="open excel",
                    command_name="open_excel",
                    capability_id="excel",
                    action_id="open_excel",
                    safety_class="allowed",
                    outcome=AuditOutcome.SUCCEEDED,
                    message="Excel session ready (stub)",
                )
            )

            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["outcome"], "succeeded")
            self.assertEqual(payload["capability_id"], "excel")
            self.assertTrue(payload["timestamp"].endswith("+00:00"))


if __name__ == "__main__":
    unittest.main()
