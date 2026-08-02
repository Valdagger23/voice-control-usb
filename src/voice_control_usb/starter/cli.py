"""CLI entrypoint for the trusted local USB starter."""

from __future__ import annotations

import argparse
from pathlib import Path

from voice_control_usb.starter.config import StarterConfig
from voice_control_usb.starter.service import TrustedUsbStarter
from voice_control_usb.starter.updates import UsbUpdateManager
from voice_control_usb.starter.windows import WindowsUsbVolumeProvider


def build_parser() -> argparse.ArgumentParser:
    """Create the local starter CLI parser."""

    parser = argparse.ArgumentParser(description="Trusted local USB starter")
    parser.add_argument("--config", required=True, help="Path to the starter JSON config.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--once",
        action="store_true",
        help="Run one detection cycle instead of polling continuously.",
    )
    mode.add_argument(
        "--prepare-removal",
        action="store_true",
        help="Ask the assistant to stop and wait until the USB can be safely removed.",
    )
    mode.add_argument(
        "--activate-update",
        metavar="RELEASE_DIR",
        help="Verify, install, and atomically activate a staged release directory.",
    )
    mode.add_argument(
        "--recover",
        action="store_true",
        help="Recover the active pointer to the highest fully verified installed release.",
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

    if args.activate_update or args.recover:
        volumes = starter.find_trusted_volumes()
        if len(volumes) != 1:
            message = (
                "Trusted USB not detected."
                if not volumes
                else "Multiple trusted USB volumes detected. Operation skipped."
            )
            print(message)
            return 2
        manager = UsbUpdateManager(config)
        try:
            if args.activate_update:
                release_id = manager.activate(volumes[0].mount_path, Path(args.activate_update))
                print(f"Verified and activated release: {release_id}")
            else:
                release_id = manager.recover(volumes[0].mount_path)
                print(f"Recovered active release: {release_id}")
        except (FileNotFoundError, RuntimeError, ValueError) as error:
            print(f"USB operation failed: {error}")
            return 2
        return 0

    if args.prepare_removal:
        result = starter.request_safe_shutdown()
        print(result.message)
        return 0 if "ready for removal" in result.message else 2
    if args.once:
        result = starter.scan_and_launch()
        print(result.message)
        return 0

    starter.run_watch_loop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
