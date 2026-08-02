"""Generate the multi-resolution Windows icon used by packaged executables."""

from __future__ import annotations

import argparse
from pathlib import Path

from voice_control_usb.assistant.tray import create_brand_icon


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    create_brand_icon(256).save(
        output,
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
