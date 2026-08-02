"""Tests for CLI runtime modes."""

from __future__ import annotations

from io import StringIO
import unittest
from unittest.mock import patch

from voice_control_usb.assistant import cli
from voice_control_usb.runtime_support import DuplicateInstanceError


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

    def test_speech_session_mode_processes_manual_record_lines(self) -> None:
        input_stream = StringIO("record open excel\nquit\n")
        output_stream = StringIO()

        with patch("sys.stdin", input_stream), patch("sys.stdout", output_stream):
            exit_code = cli.main(
                ["--session", "--input-mode", "speech", "--speech-provider", "stub"]
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            output_stream.getvalue().splitlines(),
            [
                "Recognized: open excel",
                "Excel session ready (stub)",
                "Session ended.",
            ],
        )

    def test_cli_reports_duplicate_instance_guard_failure(self) -> None:
        output_stream = StringIO()
        with patch("sys.stdout", output_stream), patch(
            "voice_control_usb.assistant.cli.AssistantInstanceGuard.acquire",
            side_effect=DuplicateInstanceError(
                "Assistant already running for runtime directory: /tmp/runtime"
            ),
        ):
            exit_code = cli.main(["open", "excel"])

        self.assertEqual(exit_code, 3)
        self.assertIn("Assistant already running for runtime directory", output_stream.getvalue())

    def test_push_to_talk_session_mode_uses_enter_trigger(self) -> None:
        input_stream = StringIO("\nopen excel\nquit\n")
        output_stream = StringIO()

        with patch("sys.stdin", input_stream), patch("sys.stdout", output_stream):
            exit_code = cli.main(
                [
                    "--session",
                    "--input-mode",
                    "speech",
                    "--speech-activation",
                    "ptt",
                    "--speech-provider",
                    "stub",
                ]
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            output_stream.getvalue().splitlines(),
            [
                "Recognized: open excel",
                "Excel session ready (stub)",
                "Session ended.",
            ],
        )

    def test_window_mode_runs_visible_shell_with_shared_app(self) -> None:
        with patch("voice_control_usb.assistant.cli.run_windows_shell") as run_window:
            exit_code = cli.main(
                [
                    "--window",
                    "--excel-adapter",
                    "stub",
                    "--desktop-adapter",
                    "stub",
                    "--speech-provider",
                    "stub",
                ]
            )

        self.assertEqual(exit_code, 0)
        run_window.assert_called_once()
        self.assertEqual(
            run_window.call_args.args[0].executor.excel.__class__.__name__,
            "StubExcelAdapter",
        )
        self.assertEqual(
            run_window.call_args.args[1].__class__.__name__,
            "ManualTextSpeechTranscriber",
        )
        self.assertEqual(
            run_window.call_args.kwargs["global_controls_path"].name,
            "global-controls.json",
        )
        self.assertFalse(run_window.call_args.kwargs["start_minimized"])

    def test_window_mode_can_start_in_notification_area(self) -> None:
        with patch("voice_control_usb.assistant.cli.run_windows_shell") as run_window:
            exit_code = cli.main(
                [
                    "--window",
                    "--start-minimized",
                    "--excel-adapter",
                    "stub",
                    "--desktop-adapter",
                    "stub",
                    "--speech-provider",
                    "stub",
                ]
            )

        self.assertEqual(exit_code, 0)
        self.assertTrue(run_window.call_args.kwargs["start_minimized"])

    def test_window_mode_selects_native_desktop_adapter_on_windows(self) -> None:
        with patch("voice_control_usb.assistant.cli.sys.platform", "win32"), patch(
            "voice_control_usb.assistant.cli.create_desktop_adapter"
        ) as create_desktop, patch(
            "voice_control_usb.assistant.cli.run_windows_shell"
        ):
            exit_code = cli.main(
                [
                    "--window",
                    "--excel-adapter",
                    "stub",
                    "--media-adapter",
                    "stub",
                    "--browser-adapter",
                    "stub",
                    "--discord-adapter",
                    "stub",
                    "--speech-provider",
                    "stub",
                ]
            )

        self.assertEqual(exit_code, 0)
        create_desktop.assert_called_once_with("windows")


if __name__ == "__main__":
    unittest.main()
