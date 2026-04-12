"""Long-running assistant session helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TextIO

from voice_control_usb.assistant.app import AssistantApp

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
        if command.casefold() in SESSION_EXIT_COMMANDS:
            output_stream.write("Session ended.\n")
            output_stream.flush()
            break

        output_stream.write(f"{app.handle_text(command)}\n")
        output_stream.flush()
        processed += 1

    return SessionResult(processed_commands=processed)


def _is_interactive(input_stream: TextIO, output_stream: TextIO) -> bool:
    input_isatty = getattr(input_stream, "isatty", lambda: False)
    output_isatty = getattr(output_stream, "isatty", lambda: False)
    return bool(input_isatty() and output_isatty())
