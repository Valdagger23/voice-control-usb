"""CLI for the USB-hosted assistant."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

from voice_control_usb.assistant.app import AssistantApp
from voice_control_usb.assistant.session import run_session, run_speech_session
from voice_control_usb.audio.factory import create_speech_transcriber
from voice_control_usb.desktop.factory import create_desktop_adapter
from voice_control_usb.excel.factory import create_excel_adapter


def main(argv: list[str] | None = None) -> int:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(
        prog="python -m voice_control_usb",
        description="Run a deterministic voice-control-usb command.",
    )
    parser.add_argument(
        "--excel-adapter",
        default=os.environ.get("VOICE_CONTROL_USB_EXCEL_ADAPTER", "stub"),
        choices=("stub", "com"),
        help="Select the Excel adapter implementation.",
    )
    parser.add_argument(
        "--desktop-adapter",
        default=os.environ.get("VOICE_CONTROL_USB_DESKTOP_ADAPTER", "stub"),
        choices=("stub", "windows"),
        help="Select the desktop adapter implementation.",
    )
    parser.add_argument(
        "--session",
        action="store_true",
        help="Run a long-lived session and read one command per line from stdin.",
    )
    parser.add_argument(
        "--input-mode",
        default=os.environ.get("VOICE_CONTROL_USB_INPUT_MODE", "typed"),
        choices=("typed", "speech"),
        help="Choose typed or speech input for session mode.",
    )
    parser.add_argument(
        "--speech-provider",
        default=os.environ.get("VOICE_CONTROL_USB_SPEECH_PROVIDER", "stub"),
        help="Select the speech transcriber provider for speech session mode.",
    )
    parser.add_argument(
        "command",
        nargs="*",
        help="Deterministic command text to run in one-shot mode.",
    )

    if not raw_args:
        print(
            'Usage: python -m voice_control_usb [--excel-adapter stub|com] [--session] "open excel"'
        )
        return 1

    namespace = parser.parse_args(raw_args)
    if not namespace.session and not namespace.command:
        parser.error("one-shot mode requires a command, or use --session")
    if namespace.input_mode == "speech" and not namespace.session:
        parser.error("speech input mode requires --session")

    try:
        excel = create_excel_adapter(namespace.excel_adapter)
        desktop = create_desktop_adapter(namespace.desktop_adapter)
    except (ImportError, RuntimeError, ValueError) as error:
        print(str(error))
        return 2

    app = AssistantApp(
        proposal_path=Path("runtime/proposals/unsupported_commands.jsonl"),
        excel=excel,
        desktop=desktop,
    )
    if namespace.session:
        if namespace.input_mode == "speech":
            try:
                transcriber = create_speech_transcriber(namespace.speech_provider)
            except ValueError as error:
                print(str(error))
                return 2
            run_speech_session(app, transcriber, sys.stdin, sys.stdout)
            return 0

        run_session(app, sys.stdin, sys.stdout)
        return 0

    print(app.handle_text(" ".join(namespace.command)))
    return 0
