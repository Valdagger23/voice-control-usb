"""Tests for speech transcriber selection and provider behavior."""

from __future__ import annotations

from types import SimpleNamespace
import unittest
from unittest.mock import patch

from voice_control_usb.audio.factory import create_speech_activator, create_speech_transcriber
from voice_control_usb.audio.activation import EnterToTalkSpeechActivator, ManualRecordSpeechActivator
from voice_control_usb.audio.transcriber import (
    ManualTextSpeechTranscriber,
    SpeechRecognitionTranscriber,
    TranscriptionResult,
    TranscriptionStatus,
)
from voice_control_usb.audio.windows_sapi import WindowsSapiSpeechTranscriber


class SpeechFactoryTests(unittest.TestCase):
    def test_stub_provider_is_default(self) -> None:
        transcriber = create_speech_transcriber()

        self.assertIsInstance(transcriber, ManualTextSpeechTranscriber)

    def test_speech_recognition_provider_selection_requires_dependency(self) -> None:
        with patch("importlib.util.find_spec", return_value=None):
            with self.assertRaisesRegex(ImportError, "SpeechRecognition is required"):
                create_speech_transcriber("speech_recognition")

    def test_speech_recognition_provider_can_be_selected(self) -> None:
        with patch("importlib.util.find_spec", return_value=SimpleNamespace()):
            transcriber = create_speech_transcriber("speech_recognition")

        self.assertIsInstance(transcriber, SpeechRecognitionTranscriber)

    def test_windows_sapi_provider_can_be_selected_on_windows(self) -> None:
        with patch("voice_control_usb.audio.factory.sys.platform", "win32"), patch(
            "importlib.util.find_spec",
            return_value=SimpleNamespace(),
        ):
            transcriber = create_speech_transcriber("windows_sapi")

        self.assertIsInstance(transcriber, WindowsSapiSpeechTranscriber)

    def test_windows_sapi_provider_is_platform_guarded(self) -> None:
        with patch("voice_control_usb.audio.factory.sys.platform", "linux"):
            with self.assertRaisesRegex(RuntimeError, "only available on Windows"):
                create_speech_transcriber("windows_sapi")

    def test_unknown_provider_fails_cleanly(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unknown speech provider selection"):
            create_speech_transcriber("mystery")

    def test_manual_speech_activation_is_default(self) -> None:
        activator = create_speech_activator()

        self.assertIsInstance(activator, ManualRecordSpeechActivator)

    def test_push_to_talk_activation_can_be_selected(self) -> None:
        activator = create_speech_activator("ptt")

        self.assertIsInstance(activator, EnterToTalkSpeechActivator)

    def test_unknown_activation_fails_cleanly(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unknown speech activation selection"):
            create_speech_activator("mystery")


class SpeechRecognitionTranscriberTests(unittest.TestCase):
    def test_transcriber_uses_recognition_backend_without_microphone(self) -> None:
        transcriber = SpeechRecognitionTranscriber()
        fake_sr = SimpleNamespace(Recognizer=lambda: object())

        with patch.object(transcriber, "_get_speech_recognition_module", return_value=fake_sr):
            with patch.object(transcriber, "_capture_audio", return_value="audio") as capture_audio:
                with patch.object(transcriber, "_recognize_audio", return_value="open excel") as recognize_audio:
                    result = transcriber.transcribe("record 7")

        self.assertEqual(result, "open excel")
        capture_audio.assert_called_once()
        recognize_audio.assert_called_once()

    def test_phrase_time_limit_defaults_for_plain_record(self) -> None:
        transcriber = SpeechRecognitionTranscriber(default_phrase_time_limit=4.0)

        self.assertEqual(transcriber._parse_phrase_time_limit("record"), 4.0)
        self.assertEqual(transcriber._parse_phrase_time_limit("record open excel"), 4.0)
        self.assertEqual(transcriber._parse_phrase_time_limit("record 7"), 7.0)

    def test_invalid_duration_fails_cleanly(self) -> None:
        transcriber = SpeechRecognitionTranscriber()

        with self.assertRaisesRegex(RuntimeError, "duration must be greater than zero"):
            transcriber._parse_phrase_time_limit("record 0")


class WindowsSapiSpeechTranscriberTests(unittest.TestCase):
    class FakeBackend:
        def __init__(self) -> None:
            self.calls: list[dict[str, object]] = []

        def available_input_devices(self) -> tuple[str, ...]:
            return ("Microphone A", "Microphone B")

        def recognize(self, **kwargs: object) -> TranscriptionResult:
            self.calls.append(dict(kwargs))
            return TranscriptionResult(
                status=TranscriptionStatus.RECOGNIZED,
                text="open excel",
                confidence=0.8,
            )

    def test_provider_returns_structured_offline_result(self) -> None:
        backend = self.FakeBackend()
        transcriber = WindowsSapiSpeechTranscriber(
            capture_timeout_seconds=6.0,
            backend=backend,  # type: ignore[arg-type]
        )
        transcriber.select_input_device("Microphone B")

        result = transcriber.transcribe_result("record 4")

        self.assertIs(result.status, TranscriptionStatus.RECOGNIZED)
        self.assertEqual(result.text, "open excel")
        self.assertEqual(
            backend.calls,
            [{"timeout_seconds": 4.0, "device_name": "Microphone B"}],
        )

    def test_provider_rejects_unknown_microphone(self) -> None:
        transcriber = WindowsSapiSpeechTranscriber(
            backend=self.FakeBackend(),  # type: ignore[arg-type]
        )

        with self.assertRaisesRegex(ValueError, "Microphone input not found"):
            transcriber.select_input_device("Missing microphone")

    def test_provider_rejects_nonpositive_capture_duration(self) -> None:
        transcriber = WindowsSapiSpeechTranscriber(
            backend=self.FakeBackend(),  # type: ignore[arg-type]
        )

        with self.assertRaisesRegex(RuntimeError, "duration must be greater than zero"):
            transcriber.transcribe_result("record 0")


if __name__ == "__main__":
    unittest.main()
