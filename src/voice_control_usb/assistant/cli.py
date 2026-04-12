"""CLI for the USB-hosted assistant."""

from __future__ import annotations

from pathlib import Path
import sys

from voice_control_usb.assistant.app import AssistantApp


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print("Usage: python -m voice_control_usb \"open excel\"")
        return 1

    app = AssistantApp(proposal_path=Path("runtime/proposals/unsupported_commands.jsonl"))
    print(app.handle_text(" ".join(args)))
    return 0
