"""Private local microphone transcription using faster-whisper."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import exp
from pathlib import Path
from threading import Event, Lock
from time import monotonic, sleep
from typing import Any, Callable

from voice_control_usb.audio.transcriber import (
    SpeechTranscriber,
    TranscriptionResult,
    TranscriptionStatus,
)


@dataclass
class SoundDeviceRecorder:
    sample_rate: int = 16_000
    voice_threshold: float = 0.012
    trailing_silence_seconds: float = 0.85
    poll_interval_seconds: float = 0.05

    def available_input_devices(self) -> tuple[str, ...]:
        sounddevice, _numpy = self._dependencies()
        devices = sounddevice.query_devices()
        names = {
            str(device["name"])
            for device in devices
            if int(device.get("max_input_channels", 0)) > 0
        }
        return tuple(sorted(names, key=str.casefold))

    def record(
        self,
        *,
        timeout_seconds: float,
        device_name: str | None,
        stop_requested: Callable[[], bool],
    ) -> Any:
        if timeout_seconds <= 0:
            raise ValueError("Speech capture timeout must be greater than zero.")
        sounddevice, numpy = self._dependencies()
        device = self._resolve_device(sounddevice, device_name)
        frames: list[Any] = []
        voice_started = [False]
        last_voice_at = [0.0]

        def callback(indata: Any, _frame_count: int, _time_info: object, status: object) -> None:
            if status:
                # PortAudio status flags are informational; captured audio remains usable.
                pass
            sample = indata[:, 0].copy()
            frames.append(sample)
            rms = float(numpy.sqrt(numpy.mean(numpy.square(sample))))
            if rms >= self.voice_threshold:
                voice_started[0] = True
                last_voice_at[0] = monotonic()

        deadline = monotonic() + timeout_seconds
        try:
            with sounddevice.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype="float32",
                device=device,
                callback=callback,
            ):
                while monotonic() < deadline and not stop_requested():
                    if (
                        voice_started[0]
                        and monotonic() - last_voice_at[0] >= self.trailing_silence_seconds
                    ):
                        break
                    sleep(self.poll_interval_seconds)
        except Exception as error:
            raise RuntimeError(f"Local microphone capture failed: {error}") from error
        if not frames or not voice_started[0]:
            return numpy.asarray([], dtype="float32")
        return numpy.concatenate(frames).astype("float32", copy=False)

    @staticmethod
    def _resolve_device(sounddevice: Any, device_name: str | None) -> int | None:
        if not device_name:
            return None
        matches = [
            index
            for index, device in enumerate(sounddevice.query_devices())
            if int(device.get("max_input_channels", 0)) > 0
            and str(device["name"]).casefold() == device_name.casefold()
        ]
        if not matches:
            raise ValueError(f"Microphone input not found: {device_name}")
        return matches[0]

    @staticmethod
    def _dependencies() -> tuple[Any, Any]:
        try:
            import numpy
            import sounddevice
        except ImportError as error:
            raise ImportError(
                "Local accurate speech requires the packaged accuracy components."
            ) from error
        return sounddevice, numpy


@dataclass
class FasterWhisperBackend:
    """Lazy CPU model wrapper; loading may download the model on first use."""

    _models: dict[tuple[str, str], object] = field(default_factory=dict, init=False)

    def recognize(
        self,
        audio: Any,
        *,
        model_name: str,
        model_root: Path,
        language: str,
        prompt: str,
    ) -> TranscriptionResult:
        if int(getattr(audio, "size", 0)) == 0:
            return TranscriptionResult(status=TranscriptionStatus.SILENCE)
        model = self._load_model(model_name, model_root)
        try:
            segments, _info = model.transcribe(  # type: ignore[attr-defined]
                audio,
                language=language,
                beam_size=5,
                best_of=5,
                temperature=0.0,
                vad_filter=True,
                condition_on_previous_text=False,
                initial_prompt=prompt,
            )
            materialized = list(segments)
        except Exception as error:
            raise RuntimeError(f"Local accurate transcription failed: {error}") from error
        text = " ".join(str(segment.text).strip() for segment in materialized).strip()
        if not text:
            return TranscriptionResult(status=TranscriptionStatus.SILENCE)
        log_probabilities = [
            float(segment.avg_logprob)
            for segment in materialized
            if getattr(segment, "avg_logprob", None) is not None
        ]
        confidence = None
        if log_probabilities:
            confidence = max(0.0, min(1.0, exp(sum(log_probabilities) / len(log_probabilities))))
        return TranscriptionResult(
            status=TranscriptionStatus.RECOGNIZED,
            text=text,
            confidence=confidence,
        )

    def _load_model(self, model_name: str, model_root: Path) -> object:
        key = (model_name, str(model_root.resolve()))
        if key in self._models:
            return self._models[key]
        try:
            from faster_whisper import WhisperModel
            from faster_whisper.utils import download_model
        except ImportError as error:
            raise ImportError(
                "Local accurate speech requires faster-whisper. Rebuild with accuracy support."
            ) from error
        model_path = model_root / model_name
        model_path.mkdir(parents=True, exist_ok=True)
        try:
            # A Hugging Face cache uses filesystem links that are unavailable on many
            # removable-drive formats. output_dir materializes a portable model tree.
            if not (model_path / "config.json").is_file() or not (
                model_path / "model.bin"
            ).is_file():
                download_model(model_name, output_dir=str(model_path))
            model = WhisperModel(
                str(model_path),
                device="cpu",
                compute_type="int8",
            )
        except Exception as error:
            raise RuntimeError(
                "The local speech model could not be loaded. The first use requires an "
                f"internet connection to download {model_name}: {error}"
            ) from error
        self._models[key] = model
        return model


@dataclass
class LocalWhisperSpeechTranscriber(SpeechTranscriber):
    model_root: Path
    model_name: str = "small.en"
    locale: str = "en-IE"
    capture_timeout_seconds: float = 8.0
    device_name: str | None = None
    recorder: SoundDeviceRecorder = field(default_factory=SoundDeviceRecorder)
    backend: FasterWhisperBackend = field(default_factory=FasterWhisperBackend)
    _stop_requested: Event = field(default_factory=Event, init=False, repr=False)
    _capture_lock: Lock = field(default_factory=Lock, init=False, repr=False)
    _prepared: bool = field(default=False, init=False, repr=False)

    def transcribe_result(self, audio_source: str | None = None) -> TranscriptionResult:
        with self._capture_lock:
            if self._prepared:
                self._prepared = False
            else:
                self._stop_requested.clear()
        audio = self.recorder.record(
            timeout_seconds=self._parse_capture_timeout(audio_source),
            device_name=self.device_name,
            stop_requested=self._stop_requested.is_set,
        )
        return self.backend.recognize(
            audio,
            model_name=self.model_name,
            model_root=self.model_root,
            language="en",
            prompt=self._command_prompt(),
        )

    def transcribe(self, audio_source: str | None = None) -> str:
        result = self.transcribe_result(audio_source)
        return result.text if result.status is TranscriptionStatus.RECOGNIZED else ""

    def available_input_devices(self) -> tuple[str, ...]:
        return self.recorder.available_input_devices()

    def select_input_device(self, name: str | None) -> None:
        normalized = None if name is None else name.strip()
        if normalized and normalized not in self.available_input_devices():
            raise ValueError(f"Microphone input not found: {normalized}")
        self.device_name = normalized or None

    def prepare_capture(self) -> None:
        with self._capture_lock:
            self._stop_requested.clear()
            self._prepared = True

    def stop_capture(self) -> None:
        self._stop_requested.set()

    def _parse_capture_timeout(self, audio_source: str | None) -> float:
        normalized = "" if audio_source is None else audio_source.strip()
        if normalized.casefold().startswith("record "):
            try:
                timeout = float(normalized[7:].strip())
            except ValueError:
                return self.capture_timeout_seconds
            if timeout <= 0:
                raise RuntimeError("Speech recording duration must be greater than zero.")
            return timeout
        return self.capture_timeout_seconds

    def _command_prompt(self) -> str:
        return (
            f"Voice Control commands spoken in {self.locale} English. "
            "Common terms: Excel, workbook, Spotify, Discord, microphone, camera, "
            "browser, Google, routine, volume, mute, unmute, deafen, worksheet."
        )
