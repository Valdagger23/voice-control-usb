"""CLI for the USB-hosted assistant."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

from voice_control_usb.assistant.app import AssistantApp
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
    parser.add_argument("command", nargs="+", help="Deterministic command text to run.")

    if not raw_args:
        print('Usage: python -m voice_control_usb [--excel-adapter stub|com] "open excel"')
        return 1

    namespace = parser.parse_args(raw_args)
    try:
        excel = create_excel_adapter(namespace.excel_adapter)
    except (ImportError, RuntimeError, ValueError) as error:
        print(str(error))
        return 2

    app = AssistantApp(
        proposal_path=Path("runtime/proposals/unsupported_commands.jsonl"),
        excel=excel,
    )
    print(app.handle_text(" ".join(namespace.command)))
    return 0
