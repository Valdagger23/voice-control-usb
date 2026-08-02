"""Tests for application-neutral session state."""

from __future__ import annotations

import unittest

from voice_control_usb.core.models import Command
from voice_control_usb.core.session_context import PendingAction, SessionContext


class SessionContextTests(unittest.TestCase):
    def test_capability_state_is_namespaced_and_clearable(self) -> None:
        context = SessionContext()
        excel_state = {"workbook": "audit.xlsx"}
        media_state = {"device": "speakers"}

        context.set_capability_state("excel", excel_state)
        context.set_capability_state("media", media_state)
        context.clear_capability_state("excel")

        self.assertIsNone(context.get_capability_state("excel"))
        self.assertIs(context.get_capability_state("media"), media_state)

    def test_pending_confirmation_is_core_state_not_capability_state(self) -> None:
        pending = PendingAction(
            command=Command(name="restart", action="restart", source_text="restart"),
            description="restart",
            created_at=10.0,
        )
        context = SessionContext(pending_action=pending)

        self.assertIs(context.pending_action, pending)
        self.assertEqual(context.capability_state, {})

    def test_empty_capability_id_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            SessionContext().set_capability_state("", object())


if __name__ == "__main__":
    unittest.main()
