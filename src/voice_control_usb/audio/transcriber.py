"""Speech-to-text placeholder kept outside the deterministic core."""

from __future__ import annotations


class SpeechTranscriber:
    """Boundary for future speech-to-text providers."""

    def transcribe(self, audio_source: str) -> str:
        raise NotImplementedError("Speech-to-text integration is planned for a later phase.")
