"""Shared speech-result routing for terminal and window surfaces."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Callable

from voice_control_usb.assistant.app import AssistantApp
from voice_control_usb.assistant.command_legend import COMMAND_SECTIONS
from voice_control_usb.audio.speech_profile import (
    PhraseInterpretation,
    SpeechProfile,
    apply_personal_correction,
    match_safe_static_command,
)
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


_SAFE_STATIC_COMMANDS = tuple(
    command.example
    for section in COMMAND_SECTIONS
    for command in section.commands
    if not command.badge and "<" not in command.phrase
)


def dispatch_transcription(
    app: AssistantApp,
    transcription: TranscriptionResult,
    *,
    speech_profile: SpeechProfile | None = None,
    correction_recorder: Callable[[str, str], None] | None = None,
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

    if (
        speech_profile is not None
        and transcription.confidence is not None
        and transcription.confidence < speech_profile.confidence_threshold
    ):
        confidence_percent = round(max(0.0, min(1.0, transcription.confidence)) * 100)
        message = (
            f"Speech confidence was only {confidence_percent}%. Nothing was executed; "
            "please try again or lower the threshold in Speech Accuracy."
        )
        app.record_input_outcome(
            source_text=transcription.text,
            outcome=AuditOutcome.INPUT_REJECTED,
            message=message,
            details={
                "input_type": "speech",
                "transcription_status": "low_confidence",
                "confidence": transcription.confidence,
                "confidence_threshold": speech_profile.confidence_threshold,
                "alternatives": list(transcription.alternatives),
            },
        )
        return SpeechDispatchResult(message=message, transcript=transcription.text)

    interpretation_source = "normalization"
    correction = (
        apply_personal_correction(
            transcription.text,
            speech_profile,
            alternatives=transcription.alternatives,
        )
        if speech_profile is not None
        else None
    )
    source_text = correction.text if correction is not None else transcription.text
    if correction is not None and correction.source == "personal":
        interpretation_source = correction.source
    interpreted_text = normalize_spoken_command(source_text)
    if app.parser.parse(interpreted_text).command is None:
        punctuation_recovery = recover_terminal_command_punctuation(
            interpreted_text,
            lambda candidate: app.parser.parse(candidate).command is not None,
        )
        if punctuation_recovery.source == "terminal_punctuation":
            interpreted_text = punctuation_recovery.text
            interpretation_source = punctuation_recovery.source
    if (
        speech_profile is not None
        and speech_profile.command_matching
        and app.parser.parse(interpreted_text).command is None
    ):
        command_match = match_safe_static_command(interpreted_text, _SAFE_STATIC_COMMANDS)
        if command_match.source == "command_match":
            interpreted_text = command_match.text
            interpretation_source = command_match.source
    if interpreted_text != transcription.text:
        app.record_input_outcome(
            source_text=transcription.text,
            outcome=AuditOutcome.STATUS,
            message=f"Interpreted speech as: {interpreted_text}",
            details={
                "input_type": "speech",
                "transcription_status": transcription.status.value,
                "interpreted_text": interpreted_text,
                "interpretation_source": interpretation_source,
            },
        )
    previous_input = app.last_input_text
    parsed = app.parser.parse(interpreted_text).command
    if (
        parsed is not None
        and parsed.action == "correct_last_input"
        and correction_recorder is not None
        and previous_input
    ):
        intended = parsed.arguments.get("correction")
        if isinstance(intended, str) and app.parser.parse(intended).command is not None:
            correction_recorder(previous_input, intended)
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


def recover_terminal_command_punctuation(
    transcript: str,
    is_supported: Callable[[str], bool],
) -> PhraseInterpretation:
    """Remove recognizer sentence punctuation only when that reveals a command."""

    if is_supported(transcript):
        return PhraseInterpretation(transcript)
    without_terminal_punctuation = re.sub(r"[.!?,;:…]+$", "", transcript).rstrip()
    if (
        without_terminal_punctuation != transcript
        and is_supported(without_terminal_punctuation)
    ):
        return PhraseInterpretation(
            without_terminal_punctuation,
            "terminal_punctuation",
            1.0,
        )
    return PhraseInterpretation(transcript)
