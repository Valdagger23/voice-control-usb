"""Signed release manifests for trusted USB payloads."""

from __future__ import annotations

from base64 import b64decode, b64encode
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any
from uuid import UUID


MANIFEST_NAME = "manifest.json"
SIGNATURE_NAME = "manifest.sig"
_RELEASE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


class ManifestVerificationError(RuntimeError):
    """Raised when portable release identity or contents cannot be trusted."""


@dataclass(frozen=True, slots=True)
class UsbIdentity:
    usb_id: str

    @classmethod
    def load(cls, path: Path) -> "UsbIdentity":
        payload = _load_object(path, "USB identity")
        _require_schema(payload, "USB identity")
        return cls(usb_id=_canonical_usb_id(payload.get("usb_id")))


@dataclass(frozen=True, slots=True)
class ActiveRelease:
    release_id: str

    @classmethod
    def load(cls, path: Path) -> "ActiveRelease":
        payload = _load_object(path, "active release pointer")
        _require_schema(payload, "active release pointer")
        return cls(release_id=validate_release_id(payload.get("release_id")))


@dataclass(frozen=True, slots=True)
class ManifestFile:
    sha256: str
    size: int


@dataclass(frozen=True, slots=True)
class ReleaseManifest:
    release_id: str
    usb_id: str
    entrypoint: str
    files: dict[str, ManifestFile]
    serialized: bytes

    @classmethod
    def load(cls, path: Path) -> "ReleaseManifest":
        try:
            serialized = path.read_bytes()
        except OSError as error:
            raise ManifestVerificationError(f"Release manifest could not be read: {path}") from error
        try:
            payload = json.loads(serialized)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ManifestVerificationError(f"Release manifest is not valid JSON: {path}") from error
        if not isinstance(payload, dict):
            raise ManifestVerificationError("Release manifest root must be a JSON object.")
        _require_schema(payload, "release manifest")

        release_id = validate_release_id(payload.get("release_id"))
        usb_id = _canonical_usb_id(payload.get("usb_id"))
        entrypoint = validate_relative_path(payload.get("entrypoint"), "entrypoint")
        raw_files = payload.get("files")
        if not isinstance(raw_files, dict) or not raw_files:
            raise ManifestVerificationError("Release manifest files must be a non-empty object.")

        files: dict[str, ManifestFile] = {}
        for raw_path, raw_metadata in raw_files.items():
            relative_path = validate_relative_path(raw_path, "file path")
            if not isinstance(raw_metadata, dict):
                raise ManifestVerificationError(f"Manifest metadata is invalid for: {relative_path}")
            digest = str(raw_metadata.get("sha256", "")).casefold()
            if not re.fullmatch(r"[0-9a-f]{64}", digest):
                raise ManifestVerificationError(f"Manifest SHA-256 is invalid for: {relative_path}")
            size = raw_metadata.get("size")
            if not isinstance(size, int) or isinstance(size, bool) or size < 0:
                raise ManifestVerificationError(f"Manifest size is invalid for: {relative_path}")
            files[relative_path] = ManifestFile(sha256=digest, size=size)

        if entrypoint not in files:
            raise ManifestVerificationError("Release entrypoint is not listed in manifest files.")
        return cls(
            release_id=release_id,
            usb_id=usb_id,
            entrypoint=entrypoint,
            files=files,
            serialized=serialized,
        )

    def verify(
        self,
        release_dir: Path,
        signature_path: Path,
        *,
        public_key: str,
        expected_usb_id: str,
        expected_release_id: str,
    ) -> Path:
        if self.usb_id != _canonical_usb_id(expected_usb_id):
            raise ManifestVerificationError("Release manifest USB identity does not match this host.")
        if self.release_id != validate_release_id(expected_release_id):
            raise ManifestVerificationError("Release manifest does not match the active release pointer.")
        _verify_signature(self.serialized, signature_path, public_key)

        resolved_release = release_dir.resolve()
        actual_files = {
            path.relative_to(resolved_release).as_posix()
            for path in resolved_release.rglob("*")
            if path.is_file()
            and path.relative_to(resolved_release).as_posix()
            not in {MANIFEST_NAME, SIGNATURE_NAME}
        }
        declared_files = set(self.files)
        unexpected = sorted(actual_files - declared_files)
        if unexpected:
            raise ManifestVerificationError(f"Release contains undeclared file: {unexpected[0]}")
        for relative_path, metadata in self.files.items():
            target = _resolve_within(resolved_release, relative_path)
            if not target.is_file():
                raise ManifestVerificationError(f"Manifest file is missing: {relative_path}")
            stat = target.stat()
            if stat.st_size != metadata.size:
                raise ManifestVerificationError(f"Manifest file size mismatch: {relative_path}")
            if _sha256(target) != metadata.sha256:
                raise ManifestVerificationError(f"Manifest file hash mismatch: {relative_path}")
        return _resolve_within(resolved_release, self.entrypoint)


def build_manifest_payload(
    release_dir: Path,
    *,
    release_id: str,
    usb_id: str,
    entrypoint: str,
) -> dict[str, Any]:
    """Create a deterministic manifest payload for a prepared release directory."""

    release_id = validate_release_id(release_id)
    usb_id = _canonical_usb_id(usb_id)
    entrypoint = validate_relative_path(entrypoint, "entrypoint")
    files: dict[str, dict[str, object]] = {}
    for path in sorted(release_dir.rglob("*")):
        if not path.is_file():
            continue
        relative_path = path.relative_to(release_dir).as_posix()
        if relative_path in {MANIFEST_NAME, SIGNATURE_NAME}:
            continue
        validate_relative_path(relative_path, "file path")
        files[relative_path] = {"sha256": _sha256(path), "size": path.stat().st_size}
    if entrypoint not in files:
        raise ManifestVerificationError(f"Release entrypoint does not exist: {entrypoint}")
    return {
        "schema_version": 1,
        "release_id": release_id,
        "usb_id": usb_id,
        "entrypoint": entrypoint,
        "files": files,
    }


def serialize_manifest(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True).encode("utf-8") + b"\n"


def sign_manifest(serialized: bytes, private_key_path: Path) -> str:
    """Return a base64 Ed25519 signature using an operator-held PEM key."""

    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    except ImportError as error:
        raise RuntimeError("Manifest signing requires the packaging dependencies.") from error
    key = serialization.load_pem_private_key(private_key_path.read_bytes(), password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise ValueError("Signing key must be an Ed25519 private key.")
    return b64encode(key.sign(serialized)).decode("ascii")


def validate_release_id(value: object) -> str:
    release_id = str(value or "").strip()
    if not _RELEASE_ID.fullmatch(release_id):
        raise ManifestVerificationError("Release ID contains unsupported characters.")
    return release_id


def validate_relative_path(value: object, label: str) -> str:
    path_text = str(value or "").strip()
    path = PurePosixPath(path_text)
    if (
        not path_text
        or "\\" in path_text
        or path.is_absolute()
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise ManifestVerificationError(f"Release {label} is not a safe relative path: {path_text}")
    return path.as_posix()


def _verify_signature(serialized: bytes, signature_path: Path, public_key: str) -> None:
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    except ImportError as error:
        raise RuntimeError("Manifest verification requires the packaging dependencies.") from error
    try:
        key_bytes = b64decode(public_key, validate=True)
        signature = b64decode(signature_path.read_text(encoding="ascii").strip(), validate=True)
        key = Ed25519PublicKey.from_public_bytes(key_bytes)
        key.verify(signature, serialized)
    except FileNotFoundError as error:
        raise ManifestVerificationError(f"Release signature is missing: {signature_path}") from error
    except (ValueError, InvalidSignature) as error:
        raise ManifestVerificationError("Release manifest signature is invalid.") from error


def _load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ManifestVerificationError(f"{label.capitalize()} file is missing: {path}") from error
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ManifestVerificationError(f"{label.capitalize()} file is invalid: {path}") from error
    if not isinstance(payload, dict):
        raise ManifestVerificationError(f"{label.capitalize()} root must be a JSON object.")
    return payload


def _require_schema(payload: dict[str, Any], label: str) -> None:
    if payload.get("schema_version") != 1:
        raise ManifestVerificationError(f"Unsupported {label} schema version.")


def _canonical_usb_id(value: object) -> str:
    try:
        return str(UUID(str(value or "")))
    except ValueError as error:
        raise ManifestVerificationError("USB identity must be a valid UUID.") from error


def _resolve_within(root: Path, relative_path: str) -> Path:
    candidate = root.joinpath(*PurePosixPath(relative_path).parts).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as error:
        raise ManifestVerificationError(f"Release path escapes its release directory: {relative_path}") from error
    return candidate


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
