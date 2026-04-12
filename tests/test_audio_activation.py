"""Tests for speech activation controllers."""

from __future__ import annotations

from io import StringIO
import unittest

from voice_control_usb.audio.activation import (
    EnterToTalkSpeechActivator,
    ManualRecordSpeechActivator,
)
from voice_control_usb.audio.transcriber import ManualTextSpeechTranscriber, SpeechRecognitionTranscriber


class SpeechActivationTests(unittest.TestCase):
    def test_manual_activator_returns_record_payload(self) -> None:
        activator = ManualRecordSpeechActivator()
        activation = activator.next_activation(
            ManualTextSpeechTranscriber(),
            StringIO("record open excel\n"),
            StringIO(),
            interactive=False,
        )

        assert activation is not None
        self.assertEqual(activation.payload, "record open excel")
        self.assertFalse(activation.should_exit)

    def test_push_to_talk_activator_uses_second_line_for_stub_transcript(self) -> None:
        activator = EnterToTalkSpeechActivator()
        activation = activator.next_activation(
            ManualTextSpeechTranscriber(),
            StringIO("\nopen excel\n"),
            StringIO(),
            interactive=False,
        )

        assert activation is not None
        self.assertEqual(activation.payload, "open excel")

    def test_push_to_talk_activator_uses_record_payload_for_real_provider(self) -> None:
        activator = EnterToTalkSpeechActivator()
        activation = activator.next_activation(
            SpeechRecognitionTranscriber(),
            StringIO("\n"),
            StringIO(),
            interactive=False,
        )

        assert activation is not None
        self.assertEqual(activation.payload, "record")

    def test_push_to_talk_activator_rejects_typed_lines(self) -> None:
        activator = EnterToTalkSpeechActivator()
        output = StringIO()
        activation = activator.next_activation(
            ManualTextSpeechTranscriber(),
            StringIO("record open excel\nquit\n"),
            output,
            interactive=False,
        )

        assert activation is not None
        self.assertTrue(activation.should_exit)
        self.assertEqual(
            output.getvalue().splitlines(),
            ["Push-to-talk mode expects Enter to record or 'quit'."],
        )


if __name__ == "__main__":
    unittest.main()
