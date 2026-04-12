"""CLI entrypoint for the trusted local USB starter."""

from __future__ import annotations

import argparse
from pathlib import Path

from voice_control_usb.starter.config import StarterConfig
from voice_control_usb.starter.service import TrustedUsbStarter
from voice_control_usb.starter.windows import WindowsUsbVolumeProvider


def build_parser() -> argparse.ArgumentParser:
    """Create the local starter CLI parser."""

    parser = argparse.ArgumentParser(description="Trusted local USB starter")
    parser.add_argument("--config", required=True, help="Path to the starter JSON config.")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run one detection cycle instead of polling continuously.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the Windows-only starter CLI."""

    args = build_parser().parse_args(argv)
    config = StarterConfig.load(Path(args.config))
    starter = TrustedUsbStarter(
        config=config,
        volume_provider=WindowsUsbVolumeProvider(),
    )

    if args.once:
        result = starter.scan_and_launch()
        print(result.message)
        return 0

    starter.run_watch_loop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
