"""Tests for long-running assistant session behavior."""

from __future__ import annotations

from io import StringIO
from pathlib import Path
import tempfile
import unittest

from voice_control_usb.assistant.app import AssistantApp
from voice_control_usb.assistant.session import run_session
from voice_control_usb.excel.adapter import StubExcelAdapter


class AssistantSessionTests(unittest.TestCase):
    def test_session_preserves_excel_context_across_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            proposal_path = Path(tmp_dir) / "unsupported_commands.jsonl"
            app = AssistantApp(proposal_path=proposal_path, excel=StubExcelAdapter())
            input_stream = StringIO(
                "\n".join(
                    [
                        "open workbook /tmp/context.xlsx",
                        "select sheet Sheet2",
                        "go to A123",
                        "type pass",
                        "go right",
                        "type fail",
                        "report current sheet",
                        "next row from start",
                        "quit",
                    ]
                )
                + "\n"
            )
            output_stream = StringIO()

            result = run_session(app, input_stream, output_stream)

            self.assertEqual(result.processed_commands, 8)
            self.assertEqual(
                output_stream.getvalue().splitlines(),
                [
                    "Opened workbook: context.xlsx",
                    "Selected sheet: Sheet2",
                    "Moved to A123",
                    "Typed 'pass' into A123",
                    "Moved right to B123",
                    "Typed 'fail' into B123",
                    "Current sheet: Sheet2 (workbook: context.xlsx)",
                    "Moved to next row start at A124",
                    "Session ended.",
                ],
            )

    def test_session_logs_unsupported_commands_without_stopping(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            proposal_path = Path(tmp_dir) / "unsupported_commands.jsonl"
            app = AssistantApp(proposal_path=proposal_path, excel=StubExcelAdapter())
            input_stream = StringIO("send email\nopen excel\nexit\n")
            output_stream = StringIO()

            result = run_session(app, input_stream, output_stream)

            self.assertEqual(result.processed_commands, 2)
            self.assertIn("Unsupported command logged for review", output_stream.getvalue())
            self.assertTrue(proposal_path.exists())


if __name__ == "__main__":
    unittest.main()
