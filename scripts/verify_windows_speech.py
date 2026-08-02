"""Verify the native offline SAPI recognizer without recording user audio."""

from __future__ import annotations

from pathlib import Path
import sys
from tempfile import TemporaryDirectory

from voice_control_usb.assistant.app import AssistantApp
from voice_control_usb.assistant.speech_flow import dispatch_transcription
from voice_control_usb.audio.transcriber import TranscriptionStatus
from voice_control_usb.audio.windows_sapi import (
    WindowsSapiBackend,
    WindowsSapiSpeechTranscriber,
)
from voice_control_usb.excel.com_adapter import ComExcelAdapter


def main() -> int:
    if sys.platform != "win32":
        print("SKIP: native Windows speech verification requires Windows.")
        return 0

    import pythoncom  # type: ignore[import-not-found]
    import win32com.client  # type: ignore[import-not-found]

    backend = WindowsSapiBackend()
    devices = backend.available_input_devices()
    if not devices:
        raise RuntimeError("No Windows speech microphone inputs were found.")
    print(f"Detected {len(devices)} microphone input(s).")

    microphone_probe = WindowsSapiSpeechTranscriber(
        capture_timeout_seconds=1.0,
        backend=backend,
    ).transcribe_result("record 1")
    print(f"Microphone capture probe completed: {microphone_probe.status.value}")

    with TemporaryDirectory(prefix="voice-control-speech-") as folder:
        workbook_path = Path(folder) / "speech-verification.xlsx"
        excel_application = win32com.client.DispatchEx("Excel.Application")
        excel_application.Visible = False
        excel_application.DisplayAlerts = False
        workbook = excel_application.Workbooks.Add()
        try:
            workbook.SaveAs(str(workbook_path))
            app = AssistantApp(
                proposal_path=Path(folder) / "proposals.jsonl",
                excel=ComExcelAdapter(visible=False, _excel=excel_application),
            )
            phrases = (
                ("open excel", "Excel session ready (COM)"),
                ("go to A one", "Moved to A1"),
                ("enter forty two", "Typed 42 into A1"),
                ("report current cell", "Current cell: A1 (value: 42)"),
                ("save workbook", "Saved workbook: speech-verification.xlsx"),
            )
            for index, (phrase, expected_response) in enumerate(phrases):
                wave_path = Path(folder) / f"phrase-{index}.wav"
                pythoncom.CoInitialize()
                try:
                    stream = win32com.client.Dispatch("SAPI.SpFileStream")
                    stream.Open(str(wave_path), 3, False)
                    voice = win32com.client.Dispatch("SAPI.SpVoice")
                    voice.AudioOutputStream = stream
                    voice.Speak(phrase, 0)
                    stream.Close()
                finally:
                    pythoncom.CoUninitialize()

                result = backend.recognize(
                    timeout_seconds=10.0,
                    audio_file=wave_path,
                )
                if result.status is not TranscriptionStatus.RECOGNIZED:
                    raise AssertionError(
                        f"Expected recognized speech; received {result.status.value}."
                    )
                dispatch = dispatch_transcription(app, result)
                if dispatch.message != expected_response:
                    raise AssertionError(
                        f"Heard {result.text!r}. Expected {expected_response!r}; "
                        f"received {dispatch.message!r}."
                    )
                print(
                    f"Speech route: {result.text!r} -> "
                    f"{dispatch.interpreted_text!r} -> {dispatch.message!r}"
                )
            assert workbook.Worksheets("Sheet1").Range("A1").Value2 == 42
        finally:
            workbook.Close(SaveChanges=False)
            excel_application.Quit()

    print("PASS: native offline Windows speech provider verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
