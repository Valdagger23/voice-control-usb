"""End-to-end assistant tests for supported and unsupported text commands."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from voice_control_usb.assistant.app import AssistantApp


class AssistantAppTests(unittest.TestCase):
    def test_unsupported_command_is_logged_as_proposal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            proposal_path = Path(tmp_dir) / "unsupported_commands.jsonl"
            app = AssistantApp(proposal_path=proposal_path)

            result = app.handle_text("send this workbook by email")

            self.assertIn("Unsupported command logged for review", result)
            contents = proposal_path.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(contents), 1)
            payload = json.loads(contents[0])
            self.assertEqual(payload["source_text"], "send this workbook by email")

    def test_supported_command_runs_without_writing_proposal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            proposal_path = Path(tmp_dir) / "unsupported_commands.jsonl"
            app = AssistantApp(proposal_path=proposal_path)

            result = app.handle_text("open excel")

            self.assertEqual(result, "Excel session ready (stub)")
            self.assertFalse(proposal_path.exists())


if __name__ == "__main__":
    unittest.main()
