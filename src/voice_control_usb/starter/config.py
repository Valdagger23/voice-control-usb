"""Trusted USB starter configuration."""

from __future__ import annotations

from dataclasses import dataclass
from base64 import b64decode
from binascii import Error as Base64Error
import json
from pathlib import Path
from uuid import UUID


@dataclass(frozen=True, slots=True)
class StarterConfig:
    """Settings for validating and launching the USB assistant."""

    expected_volume_label: str
    expected_usb_id: str
    manifest_public_key: str
    identity_file: str = "voice-control-usb.identity.json"
    active_release_file: str = "active-release.json"
    releases_dir: str = "releases"
    poll_interval_seconds: float = 2.0
    shutdown_timeout_seconds: float = 15.0
    log_path: Path | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "StarterConfig":
        """Build a config object from JSON-like data."""

        expected_volume_label = str(payload.get("expected_volume_label", "")).strip()
        if not expected_volume_label:
            raise ValueError("expected_volume_label is required.")

        expected_usb_id = str(payload.get("expected_usb_id", "")).strip()
        if not expected_usb_id:
            raise ValueError("expected_usb_id is required.")
        try:
            expected_usb_id = str(UUID(expected_usb_id))
        except (Base64Error, ValueError) as error:
            raise ValueError("expected_usb_id must be a valid UUID.") from error
        manifest_public_key = str(payload.get("manifest_public_key", "")).strip()
        if not manifest_public_key:
            raise ValueError("manifest_public_key is required.")
        try:
            public_key_bytes = b64decode(manifest_public_key, validate=True)
        except ValueError as error:
            raise ValueError("manifest_public_key must be valid base64.") from error
        if len(public_key_bytes) != 32:
            raise ValueError("manifest_public_key must contain a 32-byte Ed25519 public key.")

        identity_file = _required_text(payload, "identity_file", "voice-control-usb.identity.json")
        active_release_file = _required_text(payload, "active_release_file", "active-release.json")
        releases_dir = _required_text(payload, "releases_dir", "releases")

        poll_interval_seconds = float(payload.get("poll_interval_seconds", 2.0))
        if poll_interval_seconds <= 0:
            raise ValueError("poll_interval_seconds must be greater than zero.")
        shutdown_timeout_seconds = float(payload.get("shutdown_timeout_seconds", 15.0))
        if shutdown_timeout_seconds <= 0:
            raise ValueError("shutdown_timeout_seconds must be greater than zero.")

        raw_log_path = payload.get("log_path")
        log_path = Path(str(raw_log_path)) if raw_log_path else None

        return cls(
            expected_volume_label=expected_volume_label,
            expected_usb_id=expected_usb_id,
            manifest_public_key=manifest_public_key,
            identity_file=identity_file,
            active_release_file=active_release_file,
            releases_dir=releases_dir,
            poll_interval_seconds=poll_interval_seconds,
            shutdown_timeout_seconds=shutdown_timeout_seconds,
            log_path=log_path,
        )

    @classmethod
    def load(cls, path: Path) -> "StarterConfig":
        """Load starter configuration from a JSON file."""

        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Starter config root must be a JSON object.")
        return cls.from_dict(payload)


def _required_text(payload: dict[str, object], key: str, default: str) -> str:
    value = str(payload.get(key, default)).strip()
    if not value:
        raise ValueError(f"{key} must not be empty.")
    return value
