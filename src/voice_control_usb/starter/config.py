"""Trusted USB starter configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class StarterConfig:
    """Settings for validating and launching the USB assistant."""

    usb_root: Path
    trust_marker: str = "voice-control-usb.trusted"
    assistant_entrypoint: str = "python -m voice_control_usb"
