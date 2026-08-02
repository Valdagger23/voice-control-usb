"""Tests for persistent speech tuning, provider switching, and safe phrase recovery."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from voice_control_usb.audio.profiled import ProfiledSpeechTranscriber
from voice_control_usb.audio.speech_profile import (
    LOCAL_WHISPER,
    SpeechProfile,
    SpeechProfileStore,
    apply_personal_correction,
    match_safe_static_command,
)
from voice_control_usb.audio.transcriber import (
    SpeechTranscriber,
    TranscriptionResult,
    TranscriptionStatus,
)


class SpeechProfileTests(unittest.TestCase):
    def test_profile_round_trips_portable_settings_and_normalized_corrections(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "speech-profile.json"
            store = SpeechProfileStore(path)
            profile = SpeechProfile.from_dict(
                {
                    "provider": LOCAL_WHISPER,
                    "microphone": "  USB   Microphone ",
                    "locale": "en-IE",
                    "model": "small.en",
                    "confidence_threshold": 0.58,
                    "command_matching": True,
                    "corrections": {"Open   exhale": "open excel"},
                }
            )

            store.save(profile)
            loaded = store.load()

            self.assertEqual(loaded, profile)
            self.assertEqual(loaded.microphone, "USB Microphone")
            self.assertEqual(loaded.corrections, {"open exhale": "open excel"})

    def test_profile_rejects_invalid_threshold_provider_and_empty_correction(self) -> None:
        for payload, message in (
            ({"provider": "cloud"}, "Unsupported speech provider"),
            ({"confidence_threshold": 2}, "between 0 and 1"),
            ({"corrections": {"": "open excel"}}, "cannot contain empty"),
        ):
            with self.subTest(payload=payload):
                with self.assertRaisesRegex(ValueError, message):
                    SpeechProfile.from_dict(payload)

    def test_personal_correction_checks_primary_and_alternative_transcripts(self) -> None:
        profile = SpeechProfile(corrections={"open exhale": "open excel"})

        primary = apply_personal_correction("open exhale", profile)
        alternative = apply_personal_correction(
            "open eggshell",
            profile,
            alternatives=("open exhale",),
        )

        self.assertEqual(primary.text, "open excel")
        self.assertEqual(primary.source, "personal")
        self.assertEqual(alternative.text, "open excel")

    def test_static_command_matching_requires_clear_same_first_word_winner(self) -> None:
        candidates = ("open excel", "open discord", "pause music")

        recovered = match_safe_static_command("open exel", candidates)
        unchanged = match_safe_static_command("start exel", candidates)

        self.assertEqual(recovered.text, "open excel")
        self.assertEqual(recovered.source, "command_match")
        self.assertEqual(unchanged.text, "start exel")
        self.assertEqual(unchanged.source, "unchanged")


class _FakeProvider(SpeechTranscriber):
    def __init__(self, name: str) -> None:
        self.name = name
        self.selected: str | None = None
        self.stopped = False

    def available_input_devices(self) -> tuple[str, ...]:
        return (f"{self.name} microphone",)

    def select_input_device(self, name: str | None) -> None:
        self.selected = name

    def transcribe_result(self, audio_source: str | None = None) -> TranscriptionResult:
        return TranscriptionResult(TranscriptionStatus.RECOGNIZED, f"{self.name} result")

    def stop_capture(self) -> None:
        self.stopped = True


class ProfiledSpeechTranscriberTests(unittest.TestCase):
    def test_switches_provider_persists_settings_and_learns_correction(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            providers: list[_FakeProvider] = []

            def factory(profile: SpeechProfile) -> SpeechTranscriber:
                provider = _FakeProvider(profile.provider)
                providers.append(provider)
                return provider

            store = SpeechProfileStore(root / "speech-profile.json")
            controller = ProfiledSpeechTranscriber(
                store,
                root / "models",
                provider_factory=factory,
            )
            updated = SpeechProfile(
                provider=LOCAL_WHISPER,
                microphone="local_whisper microphone",
                confidence_threshold=0.6,
            )

            controller.configure(updated)
            controller.remember_correction("open exhale", "open excel")
            controller.select_input_device("preferred microphone")

            self.assertTrue(providers[0].stopped)
            self.assertEqual(providers[1].selected, "preferred microphone")
            self.assertEqual(controller.transcribe_result().text, "local_whisper result")
            persisted = store.load()
            self.assertEqual(persisted.provider, LOCAL_WHISPER)
            self.assertEqual(persisted.microphone, "preferred microphone")
            self.assertEqual(persisted.corrections["open exhale"], "open excel")

    def test_explicit_provider_override_wins_without_rewriting_saved_profile(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            store = SpeechProfileStore(root / "speech-profile.json")
            store.save(SpeechProfile(provider="windows_sapi"))

            controller = ProfiledSpeechTranscriber(
                store,
                root / "models",
                provider_override=LOCAL_WHISPER,
                provider_factory=lambda profile: _FakeProvider(profile.provider),
            )

            self.assertEqual(controller.provider_name, LOCAL_WHISPER)
            self.assertEqual(store.load().provider, "windows_sapi")


if __name__ == "__main__":
    unittest.main()
