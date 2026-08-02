"""Verified, interruption-safe activation for immutable USB releases."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
from uuid import uuid4

from voice_control_usb.starter.config import StarterConfig
from voice_control_usb.starter.manifest import (
    MANIFEST_NAME,
    SIGNATURE_NAME,
    ManifestVerificationError,
    ReleaseManifest,
    UsbIdentity,
)


class UsbUpdateManager:
    """Stage complete releases and atomically switch the active pointer."""

    def __init__(self, config: StarterConfig) -> None:
        self.config = config

    def activate(self, usb_root: Path, source_release_dir: Path) -> str:
        root = usb_root.resolve()
        identity = self._verify_identity(root)
        source = source_release_dir.resolve()
        manifest = ReleaseManifest.load(source / MANIFEST_NAME)
        manifest.verify(
            source,
            source / SIGNATURE_NAME,
            public_key=self.config.manifest_public_key,
            expected_usb_id=identity.usb_id,
            expected_release_id=manifest.release_id,
        )

        releases_root = self._resolve(root, self.config.releases_dir)
        releases_root.mkdir(parents=True, exist_ok=True)
        target = self._resolve(releases_root, manifest.release_id)
        if target.exists():
            raise FileExistsError(f"Release is already installed: {manifest.release_id}")
        staging = releases_root / f".staging-{manifest.release_id}-{uuid4().hex}"
        try:
            shutil.copytree(source, staging)
            staged_manifest = ReleaseManifest.load(staging / MANIFEST_NAME)
            staged_manifest.verify(
                staging,
                staging / SIGNATURE_NAME,
                public_key=self.config.manifest_public_key,
                expected_usb_id=identity.usb_id,
                expected_release_id=manifest.release_id,
            )
            os.replace(staging, target)
            self._write_active_pointer(root, manifest.release_id)
        finally:
            if staging.exists():
                shutil.rmtree(staging)
        return manifest.release_id

    def recover(self, usb_root: Path) -> str:
        """Select the highest named fully verified installed release."""

        root = usb_root.resolve()
        identity = self._verify_identity(root)
        releases_root = self._resolve(root, self.config.releases_dir)
        if not releases_root.is_dir():
            raise ManifestVerificationError("No installed releases are available for recovery.")
        candidates = sorted(
            (
                path
                for path in releases_root.iterdir()
                if path.is_dir() and not path.name.startswith(".staging-")
            ),
            key=lambda path: path.name,
            reverse=True,
        )
        for candidate in candidates:
            try:
                manifest = ReleaseManifest.load(candidate / MANIFEST_NAME)
                manifest.verify(
                    candidate,
                    candidate / SIGNATURE_NAME,
                    public_key=self.config.manifest_public_key,
                    expected_usb_id=identity.usb_id,
                    expected_release_id=candidate.name,
                )
            except (FileNotFoundError, ManifestVerificationError, RuntimeError, ValueError):
                continue
            self._write_active_pointer(root, manifest.release_id)
            self.cleanup_interrupted_staging(root)
            return manifest.release_id
        raise ManifestVerificationError("No fully verified installed release is available for recovery.")

    def cleanup_interrupted_staging(self, usb_root: Path) -> int:
        releases_root = self._resolve(usb_root.resolve(), self.config.releases_dir)
        if not releases_root.is_dir():
            return 0
        removed = 0
        for path in releases_root.glob(".staging-*"):
            if path.is_dir():
                shutil.rmtree(path)
                removed += 1
        return removed

    def _verify_identity(self, root: Path) -> UsbIdentity:
        identity = UsbIdentity.load(self._resolve(root, self.config.identity_file))
        if identity.usb_id != self.config.expected_usb_id:
            raise ManifestVerificationError("USB identity does not match this prepared host.")
        return identity

    def _write_active_pointer(self, root: Path, release_id: str) -> None:
        pointer = self._resolve(root, self.config.active_release_file)
        pointer.parent.mkdir(parents=True, exist_ok=True)
        temporary = pointer.with_name(f".{pointer.name}.{uuid4().hex}.tmp")
        payload = {"schema_version": 1, "release_id": release_id}
        try:
            with temporary.open("w", encoding="utf-8", newline="\n") as handle:
                json.dump(payload, handle, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, pointer)
        finally:
            temporary.unlink(missing_ok=True)

    @staticmethod
    def _resolve(root: Path, relative_path: str) -> Path:
        normalized = relative_path.replace("\\", "/")
        if Path(normalized).is_absolute():
            raise ValueError(f"USB layout path must be relative: {relative_path}")
        candidate = (root / normalized).resolve()
        try:
            candidate.relative_to(root)
        except ValueError as error:
            raise ValueError(f"USB layout path escapes its root: {relative_path}") from error
        return candidate
