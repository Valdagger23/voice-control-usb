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
from voice_control_usb.browser.factory import (
    create_browser_adapter,
    default_browser_profile_dir,
)
from voice_control_usb.core.audit import JsonlAuditStore
from voice_control_usb.desktop.factory import create_desktop_adapter
from voice_control_usb.excel.factory import create_excel_adapter
from voice_control_usb.media.factory import create_media_adapter
from voice_control_usb.runtime_support import (
    AssistantInstanceGuard,
    AssistantRuntimePaths,
    DuplicateInstanceError,
)
from voice_control_usb.spotify.connect import connect_spotify_account
from voice_control_usb.spotify.credentials import WindowsCredentialStore
from voice_control_usb.spotify.oauth import SpotifyOAuthClient, SpotifyOAuthConfig


def main(argv: list[str] | None = None) -> int:
    _configure_console_output()
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
        "--media-adapter",
        default=os.environ.get("VOICE_CONTROL_USB_MEDIA_ADAPTER", "stub"),
        choices=("stub", "windows"),
        help="Select the media adapter implementation.",
    )
    parser.add_argument(
        "--browser-adapter",
        default=os.environ.get("VOICE_CONTROL_USB_BROWSER_ADAPTER", "stub"),
        choices=("stub", "playwright"),
        help="Select the visible browser adapter implementation.",
    )
    parser.add_argument(
        "--browser-channel",
        default=os.environ.get("VOICE_CONTROL_USB_BROWSER_CHANNEL", "chrome"),
        choices=("chrome", "msedge"),
        help="Choose Chrome or Edge for the assistant-controlled browser.",
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
        default=os.environ.get("VOICE_CONTROL_USB_SPEECH_PROVIDER", "auto"),
        help="Select the speech transcriber provider for speech session mode.",
    )
    parser.add_argument(
        "--microphone",
        default=os.environ.get("VOICE_CONTROL_USB_MICROPHONE"),
        help="Select a microphone by its exact Windows device name.",
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
    spotify_group = parser.add_mutually_exclusive_group()
    spotify_group.add_argument(
        "--spotify-connect",
        action="store_true",
        help="Connect an optional Spotify account using a browser sign-in.",
    )
    spotify_group.add_argument(
        "--spotify-status",
        action="store_true",
        help="Report whether optional Spotify account access is configured.",
    )
    spotify_group.add_argument(
        "--spotify-disconnect",
        action="store_true",
        help="Remove the Spotify refresh token from Windows Credential Manager.",
    )
    parser.add_argument(
        "command",
        nargs="*",
        help="Deterministic command text to run in one-shot mode.",
    )

    if not raw_args:
        print(
            "Usage: python -m voice_control_usb --window, --session, or <command>"
        )
        return 1

    namespace = parser.parse_args(raw_args)
    if namespace.session and namespace.window:
        parser.error("choose either --session or --window")
    spotify_mode = any(
        (
            namespace.spotify_connect,
            namespace.spotify_status,
            namespace.spotify_disconnect,
        )
    )
    if not namespace.session and not namespace.window and not namespace.command and not spotify_mode:
        parser.error("one-shot mode requires a command, or use --session or --window")
    if namespace.window and namespace.command:
        parser.error("window mode does not accept a one-shot command")
    if namespace.input_mode == "speech" and not namespace.session:
        parser.error("speech input mode requires --session")
    if spotify_mode and (namespace.session or namespace.window or namespace.command):
        parser.error("Spotify account setup must run as a separate command")

    if spotify_mode:
        try:
            return _handle_spotify_mode(namespace)
        except (ImportError, RuntimeError, ValueError) as error:
            print(f"Spotify setup failed: {error}")
            return 2

    excel_selection = namespace.excel_adapter
    media_selection = namespace.media_adapter
    browser_selection = namespace.browser_adapter
    speech_selection = namespace.speech_provider
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
    if (
        namespace.window
        and not any(
            argument == "--media-adapter" or argument.startswith("--media-adapter=")
            for argument in raw_args
        )
        and "VOICE_CONTROL_USB_MEDIA_ADAPTER" not in os.environ
        and sys.platform == "win32"
    ):
        media_selection = "windows"
    if (
        namespace.window
        and not any(
            argument == "--browser-adapter" or argument.startswith("--browser-adapter=")
            for argument in raw_args
        )
        and "VOICE_CONTROL_USB_BROWSER_ADAPTER" not in os.environ
        and sys.platform == "win32"
    ):
        browser_selection = "playwright"
    if speech_selection == "auto":
        speech_selection = "windows_sapi" if sys.platform == "win32" else "stub"

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

    browser = None
    try:
        excel = create_excel_adapter(excel_selection)
        desktop = create_desktop_adapter(namespace.desktop_adapter)
        media = create_media_adapter(media_selection)
        browser = create_browser_adapter(
            browser_selection,
            profile_dir=(
                default_browser_profile_dir()
                if browser_selection == "playwright"
                else None
            ),
            channel=namespace.browser_channel,
        )
    except (ImportError, RuntimeError, ValueError, FileNotFoundError) as error:
        instance_guard.release()
        print(f"Assistant startup failed: {error}")
        return 2

    try:
        app = AssistantApp(
            proposal_path=runtime_paths.proposal_path,
            excel=excel,
            desktop=desktop,
            media=media,
            browser=browser,
            audit_store=JsonlAuditStore(runtime_paths.audit_path),
        )
        if namespace.window:
            try:
                transcriber = create_speech_transcriber(speech_selection)
                transcriber.select_input_device(namespace.microphone)
            except (ImportError, RuntimeError, ValueError) as error:
                print(f"Assistant startup failed: {error}")
                return 2
            run_windows_shell(app, transcriber)
            return 0
        if namespace.session:
            if namespace.input_mode == "speech":
                try:
                    transcriber = create_speech_transcriber(speech_selection)
                    transcriber.select_input_device(namespace.microphone)
                    activator = create_speech_activator(namespace.speech_activation)
                except (ImportError, RuntimeError, ValueError) as error:
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
        if browser is not None:
            with suppress(Exception):
                browser.close()
        with suppress(Exception):
            instance_guard.release()


def _handle_spotify_mode(namespace: argparse.Namespace) -> int:
    if sys.platform != "win32":
        raise RuntimeError("Spotify credential storage is only available on Windows.")
    store = WindowsCredentialStore()
    if namespace.spotify_status:
        configured = bool(os.environ.get("VOICE_CONTROL_USB_SPOTIFY_CLIENT_ID", "").strip())
        connected = store.get_refresh_token() is not None
        print(
            "Spotify account access: "
            f"{'configured' if configured else 'client ID not configured'}, "
            f"{'connected' if connected else 'not connected'}."
        )
        return 0
    if namespace.spotify_disconnect:
        removed = store.delete_refresh_token()
        print(
            "Spotify account disconnected; Windows credential removed."
            if removed
            else "Spotify account was not connected."
        )
        return 0

    config = SpotifyOAuthConfig.from_environment()
    client = SpotifyOAuthClient(config, store)
    print(connect_spotify_account(client))
    return 0


def _configure_console_output() -> None:
    """Keep valid media metadata from failing on legacy Windows code pages."""

    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(errors="backslashreplace")
