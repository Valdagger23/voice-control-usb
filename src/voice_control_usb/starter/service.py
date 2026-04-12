"""Local starter skeleton for trusted USB launch."""

from __future__ import annotations

from pathlib import Path

from voice_control_usb.starter.config import StarterConfig


class TrustedUsbStarter:
    """Validate a trusted USB payload before launch."""

    def __init__(self, config: StarterConfig) -> None:
        self.config = config

    def is_trusted(self) -> bool:
        marker = Path(self.config.usb_root, self.config.trust_marker)
        return marker.exists()

    def launch_command(self) -> str:
        if not self.is_trusted():
            raise PermissionError("Trusted USB marker not found.")
        return self.config.assistant_entrypoint
