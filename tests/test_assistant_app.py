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
            self.assertEqual(
                risky_result,
                "[CONFIRMATION REQUIRED] Confirmation required for risky action: shutdown. Type confirm to proceed or cancel.",
            )
            self.assertFalse(proposal_path.exists())

    def test_app_handles_workflow_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            proposal_path = Path(tmp_dir) / "unsupported_commands.jsonl"
            excel = StubExcelAdapter()
            app = AssistantApp(proposal_path=proposal_path, excel=excel)

            app.handle_text("go to A5")
            result = app.handle_text("mark fail and next row")

            self.assertEqual(
                result,
                "Workflow 'mark_fail_and_next_row' completed. Final result: Moved to next row start at A6",
            )
            self.assertEqual(excel.cells["A5"], "fail")

    def test_app_confirms_and_cancels_pending_risky_actions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            proposal_path = Path(tmp_dir) / "unsupported_commands.jsonl"
            app = AssistantApp(proposal_path=proposal_path)

            pending = app.handle_text("shutdown")
            canceled = app.handle_text("cancel")
            no_pending = app.handle_text("confirm")

            self.assertEqual(
                pending,
                "[CONFIRMATION REQUIRED] Confirmation required for risky action: shutdown. Type confirm to proceed or cancel.",
            )
            self.assertEqual(canceled, "Canceled pending action: shutdown")
            self.assertEqual(no_pending, "No pending action to confirm.")

    def test_status_reports_pending_confirmation_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            proposal_path = Path(tmp_dir) / "unsupported_commands.jsonl"
            app = AssistantApp(proposal_path=proposal_path)

            no_pending = app.handle_text("status")
            app.handle_text("shutdown")
            pending = app.handle_text("status")

            self.assertEqual(no_pending, "No pending confirmation action.")
            self.assertEqual(
                pending,
                "Pending confirmation: shutdown. Type confirm to proceed or cancel.",
            )

    def test_app_confirms_risky_action_before_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            proposal_path = Path(tmp_dir) / "unsupported_commands.jsonl"
            app = AssistantApp(proposal_path=proposal_path)

            app.handle_text("restart")
            confirmed = app.handle_text("confirm")

            self.assertEqual(confirmed, "Confirmed. Restart requested (stub)")

    def test_no_pending_confirm_and_cancel_are_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            proposal_path = Path(tmp_dir) / "unsupported_commands.jsonl"
            app = AssistantApp(proposal_path=proposal_path)

            self.assertEqual(app.handle_text("confirm"), "No pending action to confirm.")
            self.assertEqual(app.handle_text("cancel"), "No pending action to cancel.")

    def test_pending_action_replacement_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            proposal_path = Path(tmp_dir) / "unsupported_commands.jsonl"
            app = AssistantApp(proposal_path=proposal_path)

            app.handle_text("shutdown")
            replacement = app.handle_text("restart")
            status = app.handle_text("status")

            self.assertEqual(
                replacement,
                "Pending confirmation already required for: shutdown. Type confirm or cancel first.",
            )
            self.assertEqual(
                status,
                "Pending confirmation: shutdown. Type confirm to proceed or cancel.",
            )

    def test_pending_action_can_expire_when_timeout_is_configured(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            proposal_path = Path(tmp_dir) / "unsupported_commands.jsonl"
            current_time = [10.0]
            app = AssistantApp(
                proposal_path=proposal_path,
                pending_action_timeout_seconds=5.0,
                clock=lambda: current_time[0],
            )

            queued = app.handle_text("shutdown")
            current_time[0] = 16.0
            status = app.handle_text("status")
            confirm = app.handle_text("confirm")

            self.assertEqual(
                queued,
                "[CONFIRMATION REQUIRED] Confirmation required for risky action: shutdown. Type confirm to proceed or cancel.",
            )
            self.assertEqual(
                status,
                "No pending confirmation action. The previous pending action expired: shutdown.",
            )
            self.assertEqual(confirm, "No pending action to confirm.")

    def test_blocked_actions_remain_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            proposal_path = Path(tmp_dir) / "unsupported_commands.jsonl"
            app = AssistantApp(proposal_path=proposal_path)

            blocked = app.handle_text("run command dir")

            self.assertEqual(blocked, "Desktop action is blocked in MVP: dir")


if __name__ == "__main__":
    unittest.main()
