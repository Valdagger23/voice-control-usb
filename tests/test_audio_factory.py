"""Tests for speech transcriber selection."""

from __future__ import annotations

import unittest

from voice_control_usb.audio.factory import create_speech_transcriber
from voice_control_usb.audio.transcriber import ManualTextSpeechTranscriber


class SpeechFactoryTests(unittest.TestCase):
    def test_stub_provider_is_default(self) -> None:
        transcriber = create_speech_transcriber()

        self.assertIsInstance(transcriber, ManualTextSpeechTranscriber)

    def test_unknown_provider_fails_cleanly(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unknown speech provider selection"):
            create_speech_transcriber("mystery")


if __name__ == "__main__":
    unittest.main()
