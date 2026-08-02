"""Tests for local high-accuracy transcription without loading a real model."""

from __future__ import annotations

from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from voice_control_usb.audio.local_whisper import (
    FasterWhisperBackend,
    LocalWhisperSpeechTranscriber,
    SoundDeviceRecorder,
)
from voice_control_usb.audio.transcriber import TranscriptionResult, TranscriptionStatus


class _FakeRecorder:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def available_input_devices(self) -> tuple[str, ...]:
        return ("USB Mic",)

    def record(self, **kwargs: object) -> object:
        self.calls.append(dict(kwargs))
        return SimpleNamespace(size=10)


class _FakeBackend:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def recognize(self, audio: object, **kwargs: object) -> TranscriptionResult:
        self.calls.append({"audio": audio, **kwargs})
        return TranscriptionResult(
            TranscriptionStatus.RECOGNIZED,
            "open excel",
            confidence=0.91,
        )


class LocalWhisperTests(unittest.TestCase):
    def test_transcriber_records_selected_microphone_and_passes_command_prompt(self) -> None:
        recorder = _FakeRecorder()
        backend = _FakeBackend()
        transcriber = LocalWhisperSpeechTranscriber(
            model_root=Path("models"),
            recorder=recorder,  # type: ignore[arg-type]
            backend=backend,  # type: ignore[arg-type]
        )
        transcriber.select_input_device("USB Mic")

        result = transcriber.transcribe_result("record 4")

        self.assertEqual(result.text, "open excel")
        self.assertEqual(recorder.calls[0]["timeout_seconds"], 4.0)
        self.assertEqual(recorder.calls[0]["device_name"], "USB Mic")
        self.assertIn("Excel", str(backend.calls[0]["prompt"]))

    def test_faster_whisper_backend_combines_segments_and_normalizes_confidence(self) -> None:
        class FakeModel:
            def transcribe(self, _audio: object, **_kwargs: object):
                return iter(
                    (
                        SimpleNamespace(text=" open", avg_logprob=-0.1),
                        SimpleNamespace(text=" excel ", avg_logprob=-0.3),
                    )
                ), object()

        backend = FasterWhisperBackend()
        backend._load_model = lambda _name, _root: FakeModel()  # type: ignore[method-assign]

        result = backend.recognize(
            SimpleNamespace(size=20),
            model_name="small.en",
            model_root=Path("models"),
            language="en",
            prompt="commands",
        )

        self.assertEqual(result.text, "open excel")
        self.assertAlmostEqual(result.confidence or 0.0, 0.8187, places=3)

    def test_device_resolution_requires_exact_input_device(self) -> None:
        fake_sounddevice = SimpleNamespace(
            query_devices=lambda: (
                {"name": "Speakers", "max_input_channels": 0},
                {"name": "USB Mic", "max_input_channels": 1},
            )
        )

        self.assertEqual(SoundDeviceRecorder._resolve_device(fake_sounddevice, "USB Mic"), 1)
        with self.assertRaisesRegex(ValueError, "Microphone input not found"):
            SoundDeviceRecorder._resolve_device(fake_sounddevice, "Missing")

    def test_model_download_materializes_portable_directory_instead_of_link_cache(self) -> None:
        downloads: list[tuple[str, str]] = []
        loaded_paths: list[str] = []

        def fake_download(model_name: str, *, output_dir: str) -> None:
            downloads.append((model_name, output_dir))
            Path(output_dir, "config.json").write_text("{}", encoding="utf-8")
            Path(output_dir, "model.bin").write_bytes(b"model")

        def fake_model(model_path: str, **_kwargs: object) -> object:
            loaded_paths.append(model_path)
            return object()

        fake_package = SimpleNamespace(WhisperModel=fake_model)
        fake_utils = SimpleNamespace(download_model=fake_download)
        with TemporaryDirectory() as folder, patch.dict(
            sys.modules,
            {
                "faster_whisper": fake_package,
                "faster_whisper.utils": fake_utils,
            },
        ):
            backend = FasterWhisperBackend()
            first = backend._load_model("base.en", Path(folder))
            second = backend._load_model("base.en", Path(folder))

        self.assertIs(first, second)
        self.assertEqual(len(downloads), 1)
        self.assertEqual(Path(downloads[0][1]).name, "base.en")
        self.assertEqual(Path(loaded_paths[0]).name, "base.en")


if __name__ == "__main__":
    unittest.main()
