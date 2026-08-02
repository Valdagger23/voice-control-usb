"""CLI for the USB-hosted assistant."""

from __future__ import annotations

import argparse
from contextlib import suppress
import os
import sys

from voice_control_usb.assistant.app import AssistantApp
from voice_control_usb.assistant.session import run_session, run_speech_session
from voice_control_usb.assistant.windows_shell import run_windows_shell
from voice_control_usb.audio.factory import create_speech_activator, create_speech_transcriber
from voice_control_usb.core.audit import JsonlAuditStore
from voice_control_usb.desktop.factory import create_desktop_adapter
from voice_control_usb.excel.factory import create_excel_adapter
from voice_control_usb.runtime_support import (
    AssistantInstanceGuard,
    AssistantRuntimePaths,
    DuplicateInstanceError,
)


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
        "--window",
        action="store_true",
        help="Open the visible Windows assistant window with typed input.",
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
        "--speech-activation",
        default=os.environ.get("VOICE_CONTROL_USB_SPEECH_ACTIVATION", "manual"),
        choices=("manual", "ptt"),
        help="Choose the controlled speech activation model.",
    )
    parser.add_argument(
        "--usb-root",
        default=os.environ.get("VOICE_CONTROL_USB_USB_ROOT"),
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--runtime-dir",
        default=os.environ.get("VOICE_CONTROL_USB_RUNTIME_DIR"),
        help=argparse.SUPPRESS,
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
    if namespace.session and namespace.window:
        parser.error("choose either --session or --window")
    if not namespace.session and not namespace.window and not namespace.command:
        parser.error("one-shot mode requires a command, or use --session or --window")
    if namespace.window and namespace.command:
        parser.error("window mode does not accept a one-shot command")
    if namespace.input_mode == "speech" and not namespace.session:
        parser.error("speech input mode requires --session")

    excel_selection = namespace.excel_adapter
    if (
        namespace.window
        and not any(
            argument == "--excel-adapter" or argument.startswith("--excel-adapter=")
            for argument in raw_args
        )
        and "VOICE_CONTROL_USB_EXCEL_ADAPTER" not in os.environ
        and sys.platform == "win32"
    ):
        excel_selection = "com"

    try:
        runtime_paths = AssistantRuntimePaths.from_cli(
            usb_root=namespace.usb_root,
            runtime_dir=namespace.runtime_dir,
        )
    except RuntimeError as error:
        print(f"Assistant startup failed: {error}")
        return 2

    instance_guard = AssistantInstanceGuard(runtime_paths.lock_path)
    try:
        instance_guard.acquire()
    except DuplicateInstanceError as error:
        print(str(error))
        return 3

    try:
        excel = create_excel_adapter(excel_selection)
        desktop = create_desktop_adapter(namespace.desktop_adapter)
    except (ImportError, RuntimeError, ValueError, FileNotFoundError) as error:
        instance_guard.release()
        print(f"Assistant startup failed: {error}")
        return 2

    try:
        app = AssistantApp(
            proposal_path=runtime_paths.proposal_path,
            excel=excel,
            desktop=desktop,
            audit_store=JsonlAuditStore(runtime_paths.audit_path),
        )
        if namespace.window:
            run_windows_shell(app)
            return 0
        if namespace.session:
            if namespace.input_mode == "speech":
                try:
                    transcriber = create_speech_transcriber(namespace.speech_provider)
                    activator = create_speech_activator(namespace.speech_activation)
                except ValueError as error:
                    print(str(error))
                    return 2
                run_speech_session(app, transcriber, activator, sys.stdin, sys.stdout)
                return 0

            run_session(app, sys.stdin, sys.stdout)
            return 0

        print(app.handle_text(" ".join(namespace.command)))
        return 0
    except (FileNotFoundError, RuntimeError, ValueError) as error:
        print(f"Assistant startup failed: {error}")
        return 2
    finally:
        with suppress(Exception):
            instance_guard.release()
