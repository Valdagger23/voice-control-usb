"""Tests for speech decisions before command execution."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from voice_control_usb.assistant.app import AssistantApp
from voice_control_usb.assistant.speech_flow import (
    dispatch_transcription,
    normalize_spoken_command,
    record_speech_failure,
)
from voice_control_usb.audio.transcriber import (
    TranscriptionResult,
    TranscriptionStatus,
)
from voice_control_usb.core.audit import AuditOutcome, InMemoryAuditStore
from voice_control_usb.excel.adapter import StubExcelAdapter


class SpeechFlowTests(unittest.TestCase):
    def make_app(self) -> tuple[AssistantApp, StubExcelAdapter, InMemoryAuditStore, TemporaryDirectory[str]]:
        temporary = TemporaryDirectory()
        excel = StubExcelAdapter()
        audit = InMemoryAuditStore()
        app = AssistantApp(
            proposal_path=Path(temporary.name) / "proposals.jsonl",
            excel=excel,
            audit_store=audit,
        )
        return app, excel, audit, temporary

    def test_recognized_transcript_executes_through_normal_pipeline(self) -> None:
        app, excel, audit, temporary = self.make_app()
        self.addCleanup(temporary.cleanup)

        result = dispatch_transcription(
            app,
            TranscriptionResult(
                status=TranscriptionStatus.RECOGNIZED,
                text="open excel",
            ),
        )

        self.assertTrue(result.executed)
        self.assertTrue(excel.opened)
        self.assertIs(audit.events[0].outcome, AuditOutcome.SUCCEEDED)

    def test_silence_and_ambiguous_speech_never_execute(self) -> None:
        for transcription in (
            TranscriptionResult(status=TranscriptionStatus.SILENCE),
            TranscriptionResult(status=TranscriptionStatus.RECOGNIZED, text="  "),
            TranscriptionResult(
                status=TranscriptionStatus.AMBIGUOUS,
                text="open excel",
                confidence=-0.5,
            ),
        ):
            with self.subTest(status=transcription.status):
                app, excel, audit, temporary = self.make_app()
                self.addCleanup(temporary.cleanup)

                result = dispatch_transcription(app, transcription)

                self.assertFalse(result.executed)
                self.assertFalse(excel.opened)
                self.assertIs(audit.events[0].outcome, AuditOutcome.INPUT_REJECTED)
                expected_status = (
                    TranscriptionStatus.SILENCE.value
                    if transcription.status is TranscriptionStatus.RECOGNIZED
                    else transcription.status.value
                )
                self.assertEqual(
                    audit.events[0].details["transcription_status"],
                    expected_status,
                )

    def test_recognized_unsupported_phrase_uses_proposal_flow(self) -> None:
        app, excel, audit, temporary = self.make_app()
        self.addCleanup(temporary.cleanup)

        result = dispatch_transcription(
            app,
            TranscriptionResult(
                status=TranscriptionStatus.RECOGNIZED,
                text="send every spreadsheet",
            ),
        )

        self.assertTrue(result.executed)
        self.assertFalse(excel.opened)
        self.assertIn("Unsupported command logged", result.message)
        self.assertIs(audit.events[0].outcome, AuditOutcome.UNSUPPORTED)

    def test_provider_failure_is_audited_without_execution(self) -> None:
        app, excel, audit, temporary = self.make_app()
        self.addCleanup(temporary.cleanup)

        message = record_speech_failure(app, RuntimeError("microphone unavailable"))

        self.assertEqual(message, "Speech input unavailable: microphone unavailable")
        self.assertFalse(excel.opened)
        self.assertIs(audit.events[0].outcome, AuditOutcome.INPUT_FAILED)

    def test_spoken_cell_and_enter_forms_are_normalized_transparently(self) -> None:
        cases = (
            ("Go to a one", "go to A1"),
            ("go to bravo ten", "go to B10"),
            ("And you're 42", "enter 42"),
            ("and your inspection complete", "enter inspection complete"),
            ("Save a workbook", "save workbook"),
            ("report current cell", "report current cell"),
        )

        for transcript, expected in cases:
            with self.subTest(transcript=transcript):
                self.assertEqual(normalize_spoken_command(transcript), expected)

    def test_changed_speech_interpretation_is_visible_and_audited(self) -> None:
        app, excel, audit, temporary = self.make_app()
        self.addCleanup(temporary.cleanup)

        result = dispatch_transcription(
            app,
            TranscriptionResult(
                status=TranscriptionStatus.RECOGNIZED,
                text="Go to a one",
            ),
        )

        self.assertEqual(result.transcript, "Go to a one")
        self.assertEqual(result.interpreted_text, "go to A1")
        self.assertEqual(result.message, "Moved to A1")
        self.assertIs(audit.events[0].outcome, AuditOutcome.STATUS)
        self.assertEqual(audit.events[0].details["interpreted_text"], "go to A1")
