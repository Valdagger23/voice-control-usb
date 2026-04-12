"""Speech transcriber selection."""

from __future__ import annotations

import importlib.util

from voice_control_usb.audio.transcriber import (
    ManualTextSpeechTranscriber,
    SpeechRecognitionTranscriber,
    SpeechTranscriber,
)


def create_speech_transcriber(selection: str = "stub") -> SpeechTranscriber:
    """Create the configured speech transcriber."""

    normalized = selection.strip().lower()
    if normalized == "stub":
        return ManualTextSpeechTranscriber()
    if normalized == "speech_recognition":
        if importlib.util.find_spec("speech_recognition") is None:
            raise ImportError(
                "SpeechRecognition is required for the speech_recognition provider. "
                "Install it with 'pip install SpeechRecognition' or 'pip install .[speech]'."
            )
        return SpeechRecognitionTranscriber()
    raise ValueError(
        "Unknown speech provider selection. Expected one of: 'stub', 'speech_recognition'."
    )
