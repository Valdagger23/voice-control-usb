"""Graphical entry point for the USB-root ``Voice Control.exe`` launcher."""

from __future__ import annotations

import argparse
import ctypes
from pathlib import Path
import sys

from voice_control_usb.portable.launcher import PortableLauncher, resolve_usb_root
from voice_control_usb.runtime_support import resolve_packaged_data_path
from voice_control_usb.starter.manifest import ManifestVerificationError


PUBLIC_KEY_RESOURCE = "release-public-key.txt"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Open Voice Control from its USB.")
    parser.add_argument("--usb-root", help="Override USB root for development verification.")
    parser.add_argument("--public-key", help="Override public-key file for development verification.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        usb_root = Path(args.usb_root).resolve() if args.usb_root else resolve_usb_root()
        public_key_path = (
            Path(args.public_key).resolve()
            if args.public_key
            else resolve_packaged_data_path("portable", PUBLIC_KEY_RESOURCE)
        )
        launcher = PortableLauncher(public_key_path.read_text(encoding="ascii"))
        result = launcher.launch(usb_root)
    except (FileNotFoundError, ManifestVerificationError, OSError, RuntimeError, ValueError) as error:
        _show_message("Voice Control could not open", str(error), error=True)
        return 2

    if result.revealed_existing:
        return 0
    return 0


def _show_message(title: str, message: str, *, error: bool) -> None:
    if sys.platform == "win32":
        icon = 0x10 if error else 0x40
        ctypes.windll.user32.MessageBoxW(None, message, title, icon)
        return
    print(f"{title}: {message}", file=sys.stderr if error else sys.stdout)


if __name__ == "__main__":
    raise SystemExit(main())
