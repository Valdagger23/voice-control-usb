"""Offline Windows SAPI speech recognition for controlled capture."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import sys
from time import monotonic, sleep
from typing import Any

from voice_control_usb.audio.transcriber import (
    SpeechTranscriber,
    TranscriptionResult,
    TranscriptionStatus,
)

SAPI_INACTIVE = 0
SAPI_ACTIVE = 1


class _RecognitionEvents:
    """Collect one terminal recognition event from a SAPI context."""

    result: TranscriptionResult | None
    error: Exception | None

    def __init__(self) -> None:
        self.result = None
        self.error = None

    def OnRecognition(
        self,
        stream_number: int,
        stream_position: object,
        recognition_type: int,
        result: Any,
    ) -> None:
        try:
            self.result = _result_from_sapi(result, TranscriptionStatus.RECOGNIZED)
        except Exception as error:
            self.error = error

    def OnFalseRecognition(
        self,
        stream_number: int,
        stream_position: object,
        result: Any,
    ) -> None:
        try:
            self.result = _result_from_sapi(result, TranscriptionStatus.AMBIGUOUS)
        except Exception as error:
            self.error = error


@dataclass
class WindowsSapiBackend:
    """Own one in-process SAPI capture cycle."""

    poll_interval_seconds: float = 0.05

    def available_input_devices(self) -> tuple[str, ...]:
        pythoncom, win32com = self._load_com()
        pythoncom.CoInitialize()
        try:
            recognizer = win32com.client.Dispatch("SAPI.SpInprocRecognizer")
            tokens = recognizer.GetAudioInputs()
            return tuple(
                str(tokens.Item(index).GetDescription())
                for index in range(int(tokens.Count))
            )
        except Exception as error:
            raise RuntimeError(f"Windows could not enumerate microphone inputs: {error}") from error
        finally:
            pythoncom.CoUninitialize()

    def recognize(
        self,
        *,
        timeout_seconds: float,
        device_name: str | None = None,
        audio_file: Path | None = None,
    ) -> TranscriptionResult:
        if sys.platform != "win32":
            raise RuntimeError("Windows SAPI speech recognition is only available on Windows.")
        if timeout_seconds <= 0:
            raise ValueError("Speech capture timeout must be greater than zero.")

        pythoncom, win32com = self._load_com()
        pythoncom.CoInitialize()
        recognizer = None
        grammar = None
        audio_stream = None
        try:
            recognizer = win32com.client.gencache.EnsureDispatch(
                "SAPI.SpInprocRecognizer"
            )
            if audio_file is not None:
                audio_stream = win32com.client.Dispatch("SAPI.SpFileStream")
                audio_stream.Open(str(audio_file), 0, False)
                recognizer.AudioInputStream = audio_stream
            elif device_name:
                recognizer.AudioInput = self._select_input(recognizer, device_name)

            context = recognizer.CreateRecoContext()
            events = win32com.client.WithEvents(context, _RecognitionEvents)
            grammar = context.CreateGrammar(1)
            grammar.DictationLoad()
            grammar.DictationSetState(SAPI_ACTIVE)
            recognizer.State = SAPI_ACTIVE

            deadline = monotonic() + timeout_seconds
            while (
                events.result is None
                and events.error is None
                and monotonic() < deadline
            ):
                pythoncom.PumpWaitingMessages()
                sleep(self.poll_interval_seconds)
            if events.error is not None:
                raise RuntimeError(
                    f"Windows could not read the speech recognition result: {events.error}"
                ) from events.error
            return events.result or TranscriptionResult(
                status=TranscriptionStatus.SILENCE
            )
        except (RuntimeError, ValueError):
            raise
        except Exception as error:
            raise RuntimeError(f"Windows speech capture failed: {error}") from error
        finally:
            if grammar is not None:
                try:
                    grammar.DictationSetState(SAPI_INACTIVE)
                except Exception:
                    pass
            if recognizer is not None:
                try:
                    recognizer.State = SAPI_INACTIVE
                except Exception:
                    pass
            if audio_stream is not None:
                try:
                    audio_stream.Close()
                except Exception:
                    pass
            pythoncom.CoUninitialize()

    def _select_input(self, recognizer: Any, requested_name: str) -> Any:
        tokens = recognizer.GetAudioInputs()
        matches = [
            tokens.Item(index)
            for index in range(int(tokens.Count))
            if str(tokens.Item(index).GetDescription()).casefold()
            == requested_name.casefold()
        ]
        if not matches:
            raise ValueError(f"Microphone input not found: {requested_name}")
        return matches[0]

    @staticmethod
    def _load_com() -> tuple[Any, Any]:
        if sys.platform != "win32":
            raise RuntimeError("Windows SAPI speech recognition is only available on Windows.")
        try:
            import pythoncom  # type: ignore[import-not-found]
            import win32com  # type: ignore[import-not-found]
            import win32com.client  # type: ignore[import-not-found]
        except ImportError as error:
            raise ImportError(
                "pywin32 is required for Windows SAPI speech recognition. "
                "Install the project with 'pip install -e .[windows]'."
            ) from error
        return pythoncom, win32com


@dataclass
class WindowsSapiSpeechTranscriber(SpeechTranscriber):
    """Offline, push-activated Windows speech provider."""

    capture_timeout_seconds: float = 8.0
    device_name: str | None = None
    backend: WindowsSapiBackend = field(default_factory=WindowsSapiBackend)

    def transcribe(self, audio_source: str | None = None) -> str:
        result = self.transcribe_result(audio_source)
        if result.status is not TranscriptionStatus.RECOGNIZED:
            return ""
        return result.text

    def transcribe_result(self, audio_source: str | None = None) -> TranscriptionResult:
        return self.backend.recognize(
            timeout_seconds=self._parse_capture_timeout(audio_source),
            device_name=self.device_name,
        )

    def available_input_devices(self) -> tuple[str, ...]:
        return self.backend.available_input_devices()

    def select_input_device(self, name: str | None) -> None:
        normalized = None if name is None else name.strip()
        if normalized and normalized not in self.available_input_devices():
            raise ValueError(f"Microphone input not found: {normalized}")
        self.device_name = normalized or None

    def _parse_capture_timeout(self, audio_source: str | None) -> float:
        normalized = "" if audio_source is None else audio_source.strip()
        if not normalized or normalized.casefold() == "record":
            return self.capture_timeout_seconds
        if normalized.casefold().startswith("record "):
            try:
                timeout = float(normalized[7:].strip())
            except ValueError:
                return self.capture_timeout_seconds
            if timeout <= 0:
                raise RuntimeError("Speech recording duration must be greater than zero.")
            return timeout
        return self.capture_timeout_seconds


def _result_from_sapi(result: Any, status: TranscriptionStatus) -> TranscriptionResult:
    import win32com.client  # type: ignore[import-not-found]

    result = win32com.client.Dispatch(result)
    phrase_info = result.PhraseInfo
    text = str(phrase_info.GetText()).strip()
    confidence_values = [
        float(phrase_info.Elements.Item(index).EngineConfidence)
        for index in range(int(phrase_info.Elements.Count))
    ]
    confidence = (
        sum(confidence_values) / len(confidence_values)
        if confidence_values
        else None
    )
    if not text:
        return TranscriptionResult(status=TranscriptionStatus.SILENCE)
    return TranscriptionResult(
        status=status,
        text=text,
        confidence=confidence,
    )
