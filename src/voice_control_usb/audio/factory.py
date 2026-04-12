"""Speech transcriber selection."""

from __future__ import annotations

from voice_control_usb.audio.transcriber import ManualTextSpeechTranscriber, SpeechTranscriber


def create_speech_transcriber(selection: str = "stub") -> SpeechTranscriber:
    """Create the configured speech transcriber."""

    normalized = selection.strip().lower()
    if normalized == "stub":
        return ManualTextSpeechTranscriber()
    raise ValueError(
        "Unknown speech provider selection. Expected one of: 'stub'."
    )
