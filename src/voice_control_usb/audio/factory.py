"""Speech transcriber selection."""

from __future__ import annotations

import importlib.util
import sys

from voice_control_usb.audio.activation import (
    EnterToTalkSpeechActivator,
    ManualRecordSpeechActivator,
    SpeechActivator,
)
from voice_control_usb.audio.transcriber import (
    ManualTextSpeechTranscriber,
    SpeechRecognitionTranscriber,
    SpeechTranscriber,
)
from voice_control_usb.audio.windows_sapi import WindowsSapiSpeechTranscriber


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
    if normalized == "windows_sapi":
        if sys.platform != "win32":
            raise RuntimeError("The windows_sapi speech provider is only available on Windows.")
        if importlib.util.find_spec("win32com") is None:
            raise ImportError(
                "pywin32 is required for the windows_sapi speech provider. "
                "Install the project with 'pip install -e .[windows]'."
            )
        return WindowsSapiSpeechTranscriber()
    raise ValueError(
        "Unknown speech provider selection. Expected one of: "
        "'stub', 'windows_sapi', 'speech_recognition'."
    )


def create_speech_activator(selection: str = "manual") -> SpeechActivator:
    """Create the configured speech activation controller."""

    normalized = selection.strip().lower()
    if normalized == "manual":
        return ManualRecordSpeechActivator()
    if normalized == "ptt":
        return EnterToTalkSpeechActivator()
    raise ValueError(
        "Unknown speech activation selection. Expected one of: 'manual', 'ptt'."
    )
