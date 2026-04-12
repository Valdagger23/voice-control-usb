"""Tests for long-running assistant session behavior."""

from __future__ import annotations

from io import StringIO
from pathlib import Path
import tempfile
import unittest

from voice_control_usb.assistant.app import AssistantApp
from voice_control_usb.assistant.session import run_session, run_speech_session
from voice_control_usb.audio.activation import EnterToTalkSpeechActivator, ManualRecordSpeechActivator
from voice_control_usb.audio.transcriber import ManualTextSpeechTranscriber
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

    def test_speech_session_routes_recognized_text_through_same_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            proposal_path = Path(tmp_dir) / "unsupported_commands.jsonl"
            app = AssistantApp(proposal_path=proposal_path, excel=StubExcelAdapter())
            input_stream = StringIO(
                "\n".join(
                    [
                        "record open workbook /tmp/context.xlsx",
                        "record select sheet Sheet2",
                        "record go to A123",
                        "record type pass",
                        "record report current sheet",
                        "quit",
                    ]
                )
                + "\n"
            )
            output_stream = StringIO()

            result = run_speech_session(
                app,
                ManualTextSpeechTranscriber(),
                ManualRecordSpeechActivator(),
                input_stream,
                output_stream,
            )

            self.assertEqual(result.processed_commands, 5)
            self.assertEqual(
                output_stream.getvalue().splitlines(),
                [
                    "Recognized: open workbook /tmp/context.xlsx",
                    "Opened workbook: context.xlsx",
                    "Recognized: select sheet Sheet2",
                    "Selected sheet: Sheet2",
                    "Recognized: go to A123",
                    "Moved to A123",
                    "Recognized: type pass",
                    "Typed 'pass' into A123",
                    "Recognized: report current sheet",
                    "Current sheet: Sheet2 (workbook: context.xlsx)",
                    "Session ended.",
                ],
            )

    def test_speech_session_handles_empty_and_invalid_activation_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            proposal_path = Path(tmp_dir) / "unsupported_commands.jsonl"
            app = AssistantApp(proposal_path=proposal_path, excel=StubExcelAdapter())
            input_stream = StringIO("record\nspeak open excel\nrecord open excel\nexit\n")
            output_stream = StringIO()

            result = run_speech_session(
                app,
                ManualTextSpeechTranscriber(),
                ManualRecordSpeechActivator(),
                input_stream,
                output_stream,
            )

            self.assertEqual(result.processed_commands, 1)
            self.assertEqual(
                output_stream.getvalue().splitlines(),
                [
                    "No speech recognized.",
                    "Speech mode expects 'record <utterance>' or 'quit'.",
                    "Recognized: open excel",
                    "Excel session ready (stub)",
                    "Session ended.",
                ],
            )

    def test_speech_session_handles_provider_runtime_failure_cleanly(self) -> None:
        class FailingTranscriber(ManualTextSpeechTranscriber):
            def transcribe(self, audio_source: str | None = None) -> str:
                raise RuntimeError("microphone backend missing")

        with tempfile.TemporaryDirectory() as tmp_dir:
            proposal_path = Path(tmp_dir) / "unsupported_commands.jsonl"
            app = AssistantApp(proposal_path=proposal_path, excel=StubExcelAdapter())
            input_stream = StringIO("record\nquit\n")
            output_stream = StringIO()

            result = run_speech_session(
                app,
                FailingTranscriber(),
                ManualRecordSpeechActivator(),
                input_stream,
                output_stream,
            )

            self.assertEqual(result.processed_commands, 0)
            self.assertEqual(
                output_stream.getvalue().splitlines(),
                [
                    "Speech input unavailable: microphone backend missing",
                    "Session ended.",
                ],
            )

    def test_push_to_talk_session_routes_stub_transcript_through_same_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            proposal_path = Path(tmp_dir) / "unsupported_commands.jsonl"
            app = AssistantApp(proposal_path=proposal_path, excel=StubExcelAdapter())
            input_stream = StringIO(
                "\n".join(
                    [
                        "",
                        "open workbook /tmp/context.xlsx",
                        "",
                        "select sheet Sheet2",
                        "",
                        "go to A123",
                        "",
                        "type pass",
                        "quit",
                    ]
                )
                + "\n"
            )
            output_stream = StringIO()

            result = run_speech_session(
                app,
                ManualTextSpeechTranscriber(),
                EnterToTalkSpeechActivator(),
                input_stream,
                output_stream,
            )

            self.assertEqual(result.processed_commands, 4)
            self.assertEqual(
                output_stream.getvalue().splitlines(),
                [
                    "Recognized: open workbook /tmp/context.xlsx",
                    "Opened workbook: context.xlsx",
                    "Recognized: select sheet Sheet2",
                    "Selected sheet: Sheet2",
                    "Recognized: go to A123",
                    "Moved to A123",
                    "Recognized: type pass",
                    "Typed 'pass' into A123",
                    "Session ended.",
                ],
            )


if __name__ == "__main__":
    unittest.main()
