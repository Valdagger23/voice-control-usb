"""Operator tooling for signed, immutable USB releases."""

from __future__ import annotations

import argparse
from base64 import b64encode
import json
from pathlib import Path
import sys
from uuid import UUID

from voice_control_usb.starter.manifest import (
    MANIFEST_NAME,
    SIGNATURE_NAME,
    ReleaseManifest,
    build_manifest_payload,
    serialize_manifest,
    sign_manifest,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build and verify Voice Control USB releases.")
    commands = parser.add_subparsers(dest="action", required=True)

    keys = commands.add_parser("generate-key", help="Generate an offline Ed25519 signing key pair.")
    keys.add_argument("--private-key", required=True)
    keys.add_argument("--public-key", required=True)

    export_key = commands.add_parser(
        "export-public-key",
        help="Derive a base64 public verification key from an Ed25519 private key.",
    )
    export_key.add_argument("--private-key", required=True)
    export_key.add_argument("--public-key", required=True)

    provision = commands.add_parser("provision-usb", help="Write USB identity and initial active pointer.")
    provision.add_argument("--usb-root", required=True)
    provision.add_argument("--usb-id", required=True)
    provision.add_argument("--release-id", required=True)

    create = commands.add_parser("create", help="Create and sign a release manifest.")
    create.add_argument("--release-dir", required=True)
    create.add_argument("--usb-id", required=True)
    create.add_argument("--release-id", required=True)
    create.add_argument("--entrypoint", required=True)
    create.add_argument("--private-key", required=True)

    verify = commands.add_parser("verify", help="Verify a complete signed release.")
    verify.add_argument("--release-dir", required=True)
    verify.add_argument("--usb-id", required=True)
    verify.add_argument("--release-id", required=True)
    verify.add_argument("--public-key", required=True, help="File containing the base64 public key.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.action == "generate-key":
            public_key = generate_key_pair(Path(args.private_key), Path(args.public_key))
            print(f"Generated Ed25519 key pair. Host public key: {public_key}")
        elif args.action == "export-public-key":
            public_key = export_public_key(Path(args.private_key), Path(args.public_key))
            print(f"Exported Ed25519 public key: {public_key}")
        elif args.action == "provision-usb":
            provision_usb(Path(args.usb_root), args.usb_id, args.release_id)
            print(f"Provisioned USB identity {UUID(args.usb_id)} for release {args.release_id}.")
        elif args.action == "create":
            create_release_manifest(
                Path(args.release_dir),
                usb_id=args.usb_id,
                release_id=args.release_id,
                entrypoint=args.entrypoint,
                private_key_path=Path(args.private_key),
            )
            print(f"Created signed release manifest: {args.release_id}")
        else:
            verify_release(
                Path(args.release_dir),
                usb_id=args.usb_id,
                release_id=args.release_id,
                public_key_path=Path(args.public_key),
            )
            print(f"Verified signed release: {args.release_id}")
    except (FileExistsError, FileNotFoundError, RuntimeError, ValueError) as error:
        print(f"Release operation failed: {error}", file=sys.stderr)
        return 2
    return 0


def generate_key_pair(private_path: Path, public_path: Path) -> str:
    if private_path.exists() or public_path.exists():
        raise FileExistsError("Refusing to overwrite an existing signing key file.")
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    except ImportError as error:
        raise RuntimeError("Key generation requires the packaging dependencies.") from error
    key = Ed25519PrivateKey.generate()
    private_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.parent.mkdir(parents=True, exist_ok=True)
    private_path.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    public_value = b64encode(
        key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
    ).decode("ascii")
    public_path.write_text(public_value + "\n", encoding="ascii")
    return public_value


def export_public_key(private_path: Path, public_path: Path) -> str:
    """Write the raw base64 public key derived from an existing private key."""

    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    except ImportError as error:
        raise RuntimeError("Public-key export requires the packaging dependencies.") from error
    key = serialization.load_pem_private_key(private_path.read_bytes(), password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise ValueError("Signing key must be an Ed25519 private key.")
    public_value = b64encode(
        key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
    ).decode("ascii")
    public_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.write_text(public_value + "\n", encoding="ascii")
    return public_value


def provision_usb(usb_root: Path, usb_id: str, release_id: str) -> None:
    root = usb_root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    identity = {"schema_version": 1, "usb_id": str(UUID(usb_id))}
    active = {"schema_version": 1, "release_id": release_id}
    _write_json(root / "voice-control-usb.identity.json", identity)
    _write_json(root / "active-release.json", active)


def create_release_manifest(
    release_dir: Path,
    *,
    usb_id: str,
    release_id: str,
    entrypoint: str,
    private_key_path: Path,
) -> None:
    payload = build_manifest_payload(
        release_dir,
        usb_id=usb_id,
        release_id=release_id,
        entrypoint=entrypoint,
    )
    serialized = serialize_manifest(payload)
    signature = sign_manifest(serialized, private_key_path)
    (release_dir / MANIFEST_NAME).write_bytes(serialized)
    (release_dir / SIGNATURE_NAME).write_text(signature + "\n", encoding="ascii")


def verify_release(
    release_dir: Path,
    *,
    usb_id: str,
    release_id: str,
    public_key_path: Path,
) -> None:
    manifest = ReleaseManifest.load(release_dir / MANIFEST_NAME)
    manifest.verify(
        release_dir,
        release_dir / SIGNATURE_NAME,
        public_key=public_key_path.read_text(encoding="ascii").strip(),
        expected_usb_id=str(UUID(usb_id)),
        expected_release_id=release_id,
    )


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
