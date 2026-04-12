"""Tests for CLI runtime modes."""

from __future__ import annotations

from io import StringIO
import unittest
from unittest.mock import patch

from voice_control_usb.assistant import cli


class CliTests(unittest.TestCase):
    def test_one_shot_mode_runs_single_command(self) -> None:
        output_stream = StringIO()
        with patch("sys.stdout", output_stream):
            exit_code = cli.main(["open", "excel"])

        self.assertEqual(exit_code, 0)
        self.assertIn("Excel session ready (stub)", output_stream.getvalue())

    def test_session_mode_processes_multiple_commands(self) -> None:
        input_stream = StringIO("open workbook /tmp/context.xlsx\nreport current sheet\nquit\n")
        output_stream = StringIO()

        with patch("sys.stdin", input_stream), patch("sys.stdout", output_stream):
            exit_code = cli.main(["--session"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            output_stream.getvalue().splitlines(),
            [
                "Opened workbook: context.xlsx",
                "Current sheet: Sheet1 (workbook: context.xlsx)",
                "Session ended.",
            ],
        )


if __name__ == "__main__":
    unittest.main()
