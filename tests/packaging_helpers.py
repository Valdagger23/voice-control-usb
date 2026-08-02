"""Test helpers for signed portable releases."""

from __future__ import annotations

from base64 import b64encode
import json
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from voice_control_usb.starter.manifest import (
    MANIFEST_NAME,
    SIGNATURE_NAME,
    build_manifest_payload,
    serialize_manifest,
    sign_manifest,
)


USB_ID = "12345678-1234-5678-1234-567812345678"


def create_signing_material(directory: Path) -> tuple[Path, str]:
    key = Ed25519PrivateKey.generate()
    private_path = directory / "signing-key.pem"
    private_path.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    public_key = b64encode(
        key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
    ).decode("ascii")
    return private_path, public_key


def write_identity(usb_root: Path, usb_id: str = USB_ID) -> None:
    (usb_root / "voice-control-usb.identity.json").write_text(
        json.dumps({"schema_version": 1, "usb_id": usb_id}) + "\n",
        encoding="utf-8",
    )


def write_active_pointer(usb_root: Path, release_id: str) -> None:
    (usb_root / "active-release.json").write_text(
        json.dumps({"schema_version": 1, "release_id": release_id}) + "\n",
        encoding="utf-8",
    )


def write_signed_release(
    release_dir: Path,
    private_key: Path,
    *,
    release_id: str,
    usb_id: str = USB_ID,
    content: str = "assistant binary",
) -> Path:
    executable = release_dir / "assistant" / "voice-control-usb-assistant.exe"
    executable.parent.mkdir(parents=True)
    executable.write_text(content, encoding="utf-8")
    payload = build_manifest_payload(
        release_dir,
        release_id=release_id,
        usb_id=usb_id,
        entrypoint="assistant/voice-control-usb-assistant.exe",
    )
    serialized = serialize_manifest(payload)
    (release_dir / MANIFEST_NAME).write_bytes(serialized)
    (release_dir / SIGNATURE_NAME).write_text(
        sign_manifest(serialized, private_key) + "\n",
        encoding="ascii",
    )
    return executable
