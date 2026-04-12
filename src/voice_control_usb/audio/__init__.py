"""Speech-to-text integration boundary."""

from voice_control_usb.audio.factory import create_speech_transcriber
from voice_control_usb.audio.transcriber import (
    ManualTextSpeechTranscriber,
    SpeechRecognitionTranscriber,
    SpeechTranscriber,
)

__all__ = [
    "ManualTextSpeechTranscriber",
    "SpeechRecognitionTranscriber",
    "SpeechTranscriber",
    "create_speech_transcriber",
]
