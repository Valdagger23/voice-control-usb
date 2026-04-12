"""Speech-to-text integration boundary."""

from voice_control_usb.audio.activation import (
    EnterToTalkSpeechActivator,
    ManualRecordSpeechActivator,
    SpeechActivator,
)
from voice_control_usb.audio.factory import create_speech_activator, create_speech_transcriber
from voice_control_usb.audio.transcriber import (
    ManualTextSpeechTranscriber,
    SpeechRecognitionTranscriber,
    SpeechTranscriber,
)

__all__ = [
    "EnterToTalkSpeechActivator",
    "ManualRecordSpeechActivator",
    "SpeechActivator",
    "ManualTextSpeechTranscriber",
    "SpeechRecognitionTranscriber",
    "SpeechTranscriber",
    "create_speech_activator",
    "create_speech_transcriber",
]
