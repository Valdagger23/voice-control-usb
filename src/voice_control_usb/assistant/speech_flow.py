"""Shared speech-result routing for terminal and window surfaces."""

from __future__ import annotations

from dataclasses import dataclass
import re

from voice_control_usb.assistant.app import AssistantApp
from voice_control_usb.audio.transcriber import (
    TranscriptionResult,
    TranscriptionStatus,
    non_executed_transcription_message,
)
from voice_control_usb.core.audit import AuditOutcome


@dataclass(frozen=True, slots=True)
class SpeechDispatchResult:
    """Visible result of deciding whether a transcript may execute."""

    message: str
    transcript: str = ""
    interpreted_text: str = ""
    executed: bool = False


def dispatch_transcription(
    app: AssistantApp,
    transcription: TranscriptionResult,
) -> SpeechDispatchResult:
    """Execute recognized text or audit a rejected input-stage result."""

    if (
        transcription.status is TranscriptionStatus.RECOGNIZED
        and not transcription.text.strip()
    ):
        transcription = TranscriptionResult(status=TranscriptionStatus.SILENCE)

    if transcription.status is not TranscriptionStatus.RECOGNIZED:
        message = non_executed_transcription_message(transcription)
        app.record_input_outcome(
            source_text=transcription.text,
            outcome=AuditOutcome.INPUT_REJECTED,
            message=message,
            details={
                "input_type": "speech",
                "transcription_status": transcription.status.value,
                "confidence": transcription.confidence,
                "alternatives": list(transcription.alternatives),
            },
        )
        return SpeechDispatchResult(message=message, transcript=transcription.text)

    interpreted_text = normalize_spoken_command(transcription.text)
    if interpreted_text != transcription.text:
        app.record_input_outcome(
            source_text=transcription.text,
            outcome=AuditOutcome.STATUS,
            message=f"Interpreted speech as: {interpreted_text}",
            details={
                "input_type": "speech",
                "transcription_status": transcription.status.value,
                "interpreted_text": interpreted_text,
            },
        )
    return SpeechDispatchResult(
        message=app.handle_text(interpreted_text),
        transcript=transcription.text,
        interpreted_text=interpreted_text,
        executed=True,
    )


def record_speech_failure(app: AssistantApp, error: Exception) -> str:
    """Audit and format a provider failure that produced no transcript."""

    message = f"Speech input unavailable: {error}"
    app.record_input_outcome(
        source_text="",
        outcome=AuditOutcome.INPUT_FAILED,
        message=message,
        details={"input_type": "speech", "error_type": type(error).__name__},
    )
    return message


def normalize_spoken_command(transcript: str) -> str:
    """Normalize a small, explicit set of common command recognizer forms."""

    normalized = " ".join(transcript.strip().split())
    fixed_aliases = {
        "save a workbook": "save workbook",
    }
    fixed_alias = fixed_aliases.get(normalized.casefold())
    if fixed_alias is not None:
        return fixed_alias

    enter_match = re.fullmatch(
        r"(?:and you(?:'|’)re|and your) (?P<value>.+)",
        normalized,
        flags=re.IGNORECASE,
    )
    if enter_match:
        return f"enter {enter_match.group('value')}"

    cell_match = re.fullmatch(
        r"go to (?P<column>[a-z]|alpha|bravo|charlie|delta|echo) "
        r"(?P<row>one|two|three|four|five|six|seven|eight|nine|ten|[0-9]+)",
        normalized,
        flags=re.IGNORECASE,
    )
    if cell_match:
        column_words = {
            "alpha": "A",
            "bravo": "B",
            "charlie": "C",
            "delta": "D",
            "echo": "E",
        }
        row_words = {
            "one": "1",
            "two": "2",
            "three": "3",
            "four": "4",
            "five": "5",
            "six": "6",
            "seven": "7",
            "eight": "8",
            "nine": "9",
            "ten": "10",
        }
        column = cell_match.group("column").casefold()
        row = cell_match.group("row").casefold()
        return f"go to {column_words.get(column, column.upper())}{row_words.get(row, row)}"

    return normalized
