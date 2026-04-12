"""Long-running assistant session helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TextIO

from voice_control_usb.assistant.app import AssistantApp
from voice_control_usb.audio.activation import SpeechActivator
from voice_control_usb.audio.transcriber import SpeechTranscriber

SESSION_EXIT_COMMANDS = {"exit", "quit"}


@dataclass(frozen=True, slots=True)
class SessionResult:
    """Summary of a session run."""

    processed_commands: int


def run_session(
    app: AssistantApp,
    input_stream: TextIO,
    output_stream: TextIO,
    *,
    prompt: str = "voice-control-usb> ",
) -> SessionResult:
    """Process commands line by line while preserving adapter state."""

    processed = 0
    interactive = _is_interactive(input_stream, output_stream)

    while True:
        if interactive:
            output_stream.write(prompt)
            output_stream.flush()

        raw_line = input_stream.readline()
        if raw_line == "":
            if interactive:
                output_stream.write("\n")
            break

        command = raw_line.strip()
        if not command:
            continue
        if _should_exit_session(command, output_stream):
            break

        processed += _handle_command(app, command, output_stream)

    return SessionResult(processed_commands=processed)


def run_speech_session(
    app: AssistantApp,
    transcriber: SpeechTranscriber,
    activator: SpeechActivator,
    input_stream: TextIO,
    output_stream: TextIO,
) -> SessionResult:
    """Process controlled speech input through the same assistant pipeline."""

    processed = 0
    interactive = _is_interactive(input_stream, output_stream)

    while True:
        if interactive:
            output_stream.write(activator.prompt)
            output_stream.flush()

        activation = activator.next_activation(
            transcriber,
            input_stream,
            output_stream,
            interactive=interactive,
        )
        if activation is None:
            break
        if activation.should_exit:
            output_stream.write("Session ended.\n")
            output_stream.flush()
            break

        try:
            recognized = transcriber.transcribe(activation.payload)
        except (ImportError, RuntimeError) as error:
            output_stream.write(f"Speech input unavailable: {error}\n")
            output_stream.flush()
            continue
        if not recognized:
            output_stream.write("No speech recognized.\n")
            output_stream.flush()
            continue

        output_stream.write(f"Recognized: {recognized}\n")
        output_stream.flush()
        processed += _handle_command(app, recognized, output_stream)

    return SessionResult(processed_commands=processed)


def _handle_command(app: AssistantApp, command: str, output_stream: TextIO) -> int:
    output_stream.write(f"{app.handle_text(command)}\n")
    output_stream.flush()
    return 1


def _should_exit_session(command: str, output_stream: TextIO) -> bool:
    if command.casefold() in SESSION_EXIT_COMMANDS:
        output_stream.write("Session ended.\n")
        output_stream.flush()
        return True
    return False


def _is_interactive(input_stream: TextIO, output_stream: TextIO) -> bool:
    input_isatty = getattr(input_stream, "isatty", lambda: False)
    output_isatty = getattr(output_stream, "isatty", lambda: False)
    return bool(input_isatty() and output_isatty())
