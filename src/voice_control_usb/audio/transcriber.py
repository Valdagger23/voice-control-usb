"""Speech-to-text provider boundary for controlled runtime input."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class SpeechTranscriber:
    """Boundary for pluggable speech-to-text providers."""

    def transcribe(self, audio_source: str | None = None) -> str:
        raise NotImplementedError

    def requires_manual_transcript(self) -> bool:
        return False


class ManualTextSpeechTranscriber(SpeechTranscriber):
    """Stub provider that treats manual `record ...` input as recognized speech."""

    def requires_manual_transcript(self) -> bool:
        return True

    def transcribe(self, audio_source: str | None = None) -> str:
        normalized = "" if audio_source is None else audio_source.strip()
        if not normalized:
            return ""

        lowered = normalized.casefold()
        if lowered == "record":
            return ""
        if lowered.startswith("record "):
            return normalized[7:].strip()
        return normalized


@dataclass
class SpeechRecognitionTranscriber(SpeechTranscriber):
    """Controlled microphone capture using the SpeechRecognition package."""

    language: str = "en-US"
    listen_timeout: float = 5.0
    default_phrase_time_limit: float = 5.0
    ambient_noise_duration: float = 0.3

    def transcribe(self, audio_source: str | None = None) -> str:
        phrase_time_limit = self._parse_phrase_time_limit(audio_source)
        sr = self._get_speech_recognition_module()
        recognizer = sr.Recognizer()
        audio = self._capture_audio(sr, recognizer, phrase_time_limit)
        return self._recognize_audio(sr, recognizer, audio)

    def _parse_phrase_time_limit(self, audio_source: str | None) -> float:
        normalized = "" if audio_source is None else audio_source.strip()
        if not normalized or normalized.casefold() == "record":
            return self.default_phrase_time_limit

        if normalized.casefold().startswith("record "):
            candidate = normalized[7:].strip()
            try:
                seconds = float(candidate)
            except ValueError:
                return self.default_phrase_time_limit
            if seconds <= 0:
                raise RuntimeError("Speech recording duration must be greater than zero.")
            return seconds

        return self.default_phrase_time_limit

    def _get_speech_recognition_module(self) -> Any:
        try:
            import speech_recognition as sr  # type: ignore[import-not-found]
        except ImportError as error:
            raise ImportError(
                "SpeechRecognition is required for the speech_recognition provider. "
                "Install it with 'pip install SpeechRecognition' or 'pip install .[speech]'."
            ) from error
        return sr

    def _capture_audio(self, sr: Any, recognizer: Any, phrase_time_limit: float) -> Any:
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(
                    source,
                    duration=self.ambient_noise_duration,
                )
                return recognizer.listen(
                    source,
                    timeout=self.listen_timeout,
                    phrase_time_limit=phrase_time_limit,
                )
        except Exception as error:  # pragma: no cover - exact backend errors vary by platform
            raise RuntimeError(
                "Microphone capture is unavailable for the speech_recognition provider. "
                "Ensure a supported microphone backend such as PyAudio is installed."
            ) from error

    def _recognize_audio(self, sr: Any, recognizer: Any, audio: Any) -> str:
        try:
            recognized = recognizer.recognize_google(audio, language=self.language)
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as error:
            raise RuntimeError(
                "The speech_recognition provider could not reach the recognition service."
            ) from error
        return recognized.strip()
