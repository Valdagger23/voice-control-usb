"""Trusted USB starter configuration."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path


@dataclass(frozen=True, slots=True)
class StarterConfig:
    """Settings for validating and launching the USB assistant."""

    expected_volume_label: str
    trust_marker: str = "voice-control-usb.trusted"
    assistant_python: str = "python"
    assistant_module: str = "voice_control_usb"
    assistant_pythonpath: str = "src"
    assistant_workdir: str = "."
    poll_interval_seconds: float = 2.0
    log_path: Path | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "StarterConfig":
        """Build a config object from JSON-like data."""

        expected_volume_label = str(payload.get("expected_volume_label", "")).strip()
        if not expected_volume_label:
            raise ValueError("expected_volume_label is required.")

        trust_marker = str(payload.get("trust_marker", "voice-control-usb.trusted")).strip()
        if not trust_marker:
            raise ValueError("trust_marker must not be empty.")

        assistant_python = str(payload.get("assistant_python", "python")).strip()
        if not assistant_python:
            raise ValueError("assistant_python must not be empty.")

        assistant_module = str(payload.get("assistant_module", "voice_control_usb")).strip()
        if not assistant_module:
            raise ValueError("assistant_module must not be empty.")

        assistant_pythonpath = str(payload.get("assistant_pythonpath", "src")).strip()
        if not assistant_pythonpath:
            raise ValueError("assistant_pythonpath must not be empty.")

        assistant_workdir = str(payload.get("assistant_workdir", ".")).strip()
        if not assistant_workdir:
            raise ValueError("assistant_workdir must not be empty.")

        poll_interval_seconds = float(payload.get("poll_interval_seconds", 2.0))
        if poll_interval_seconds <= 0:
            raise ValueError("poll_interval_seconds must be greater than zero.")

        raw_log_path = payload.get("log_path")
        log_path = Path(str(raw_log_path)) if raw_log_path else None

        return cls(
            expected_volume_label=expected_volume_label,
            trust_marker=trust_marker,
            assistant_python=assistant_python,
            assistant_module=assistant_module,
            assistant_pythonpath=assistant_pythonpath,
            assistant_workdir=assistant_workdir,
            poll_interval_seconds=poll_interval_seconds,
            log_path=log_path,
        )

    @classmethod
    def load(cls, path: Path) -> "StarterConfig":
        """Load starter configuration from a JSON file."""

        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Starter config root must be a JSON object.")
        return cls.from_dict(payload)
