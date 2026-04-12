"""Speech-to-text provider boundary for controlled runtime input."""

from __future__ import annotations


class SpeechTranscriber:
    """Boundary for pluggable speech-to-text providers."""

    def transcribe(self, audio_source: str | None = None) -> str:
        raise NotImplementedError


class ManualTextSpeechTranscriber(SpeechTranscriber):
    """Stub provider that treats manual `record ...` input as recognized speech."""

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
