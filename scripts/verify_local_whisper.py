"""Verify the local Whisper engine with synthesized speech and no user recording."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

from voice_control_usb.assistant.app import AssistantApp
from voice_control_usb.assistant.speech_flow import dispatch_transcription
from voice_control_usb.audio.local_whisper import FasterWhisperBackend
from voice_control_usb.audio.speech_profile import LOCAL_WHISPER, SpeechProfile
from voice_control_usb.audio.transcriber import TranscriptionStatus


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="base.en")
    parser.add_argument(
        "--model-root",
        type=Path,
        default=Path("work/local-whisper-models"),
    )
    return parser.parse_args()


def main() -> int:
    if sys.platform != "win32":
        print("SKIP: local Whisper verification requires Windows SAPI synthesis.")
        return 0

    args = parse_args()
    try:
        import pythoncom  # type: ignore[import-not-found]
        import win32com.client  # type: ignore[import-not-found]
        from faster_whisper.audio import decode_audio
    except ImportError as error:
        raise RuntimeError(
            "Install the Windows and accuracy extras before running this check."
        ) from error

    with TemporaryDirectory(prefix="voice-control-whisper-") as folder:
        wave_path = Path(folder) / "open-excel.wav"
        pythoncom.CoInitialize()
        try:
            stream = win32com.client.Dispatch("SAPI.SpFileStream")
            stream.Open(str(wave_path), 3, False)
            voice = win32com.client.Dispatch("SAPI.SpVoice")
            voice.AudioOutputStream = stream
            voice.Speak("open excel", 0)
            stream.Close()
        finally:
            pythoncom.CoUninitialize()

        audio = decode_audio(str(wave_path), sampling_rate=16_000)
        result = FasterWhisperBackend().recognize(
            audio,
            model_name=args.model,
            model_root=args.model_root.resolve(),
            language="en",
            prompt="Voice Control command. Common term: Excel.",
        )
        if result.status is not TranscriptionStatus.RECOGNIZED:
            raise AssertionError(f"Expected recognized speech; received {result.status.value}.")
        dispatch = dispatch_transcription(
            AssistantApp(proposal_path=Path(folder) / "proposals.jsonl"),
            result,
            speech_profile=SpeechProfile(
                provider=LOCAL_WHISPER,
                model=args.model,
                confidence_threshold=0.0,
            ),
        )
        if dispatch.message != "Excel session ready (stub)":
            raise AssertionError(
                f"Heard {result.text!r}; interpreted {dispatch.interpreted_text!r}; "
                f"received {dispatch.message!r}."
            )
        print(
            f"Speech route: {result.text!r} -> {dispatch.interpreted_text!r} "
            f"-> {dispatch.message!r}"
        )

    print("PASS: local Whisper speech provider verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
