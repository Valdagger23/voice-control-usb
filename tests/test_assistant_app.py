"""End-to-end assistant tests for supported and unsupported text commands."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from voice_control_usb.assistant.app import AssistantApp
from voice_control_usb.excel.adapter import StubExcelAdapter


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

    def test_app_uses_injected_excel_adapter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            proposal_path = Path(tmp_dir) / "unsupported_commands.jsonl"
            excel = StubExcelAdapter()
            app = AssistantApp(proposal_path=proposal_path, excel=excel)

            app.handle_text("go to C7")
            result = app.handle_text("type pass")

            self.assertEqual(result, "Typed 'pass' into C7")
            self.assertEqual(excel.cells["C7"], "pass")

    def test_app_handles_workbook_context_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            proposal_path = Path(tmp_dir) / "unsupported_commands.jsonl"
            excel = StubExcelAdapter()
            app = AssistantApp(proposal_path=proposal_path, excel=excel)

            open_result = app.handle_text("open workbook /tmp/context.xlsx")
            select_result = app.handle_text("select sheet Sheet2")
            report_result = app.handle_text("report current sheet")
            save_result = app.handle_text("save workbook")

            self.assertEqual(open_result, "Opened workbook: context.xlsx")
            self.assertEqual(select_result, "Selected sheet: Sheet2")
            self.assertEqual(report_result, "Current sheet: Sheet2 (workbook: context.xlsx)")
            self.assertEqual(save_result, "Saved workbook: context.xlsx")

    def test_app_handles_desktop_commands_without_changing_proposal_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            proposal_path = Path(tmp_dir) / "unsupported_commands.jsonl"
            app = AssistantApp(proposal_path=proposal_path)

            safe_result = app.handle_text("open app notepad")
            risky_result = app.handle_text("shutdown")

            self.assertEqual(safe_result, "Opened app alias: notepad (stub)")
            self.assertEqual(risky_result, "Desktop action is not approved in MVP: shutdown")
            self.assertFalse(proposal_path.exists())


if __name__ == "__main__":
    unittest.main()
