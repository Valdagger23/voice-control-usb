"""Tests for signed manifests and interruption-safe USB updates."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from packaging_helpers import (
    USB_ID,
    create_signing_material,
    write_active_pointer,
    write_identity,
    write_signed_release,
)
from voice_control_usb.starter.config import StarterConfig
from voice_control_usb.starter.manifest import (
    MANIFEST_NAME,
    SIGNATURE_NAME,
    ManifestVerificationError,
    ReleaseManifest,
)
from voice_control_usb.starter.updates import UsbUpdateManager


class PackagingHardeningTests(unittest.TestCase):
    def make_config(self, public_key: str) -> StarterConfig:
        return StarterConfig.from_dict(
            {
                "expected_volume_label": "VOICEBOT",
                "expected_usb_id": USB_ID,
                "manifest_public_key": public_key,
            }
        )

    def test_signed_manifest_verifies_every_declared_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            private_key, public_key = create_signing_material(root)
            release = root / "release"
            executable = write_signed_release(release, private_key, release_id="1.0.0")
            manifest = ReleaseManifest.load(release / MANIFEST_NAME)

            resolved = manifest.verify(
                release,
                release / SIGNATURE_NAME,
                public_key=public_key,
                expected_usb_id=USB_ID,
                expected_release_id="1.0.0",
            )
            self.assertEqual(resolved, executable.resolve())

    def test_modified_manifest_and_modified_binary_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            private_key, public_key = create_signing_material(root)
            release = root / "release"
            executable = write_signed_release(release, private_key, release_id="1.0.0")
            executable.write_text("changed", encoding="utf-8")
            manifest = ReleaseManifest.load(release / MANIFEST_NAME)
            with self.assertRaisesRegex(ManifestVerificationError, "mismatch"):
                manifest.verify(
                    release,
                    release / SIGNATURE_NAME,
                    public_key=public_key,
                    expected_usb_id=USB_ID,
                    expected_release_id="1.0.0",
                )

            executable.write_text("assistant binary", encoding="utf-8")
            payload = json.loads((release / MANIFEST_NAME).read_text(encoding="utf-8"))
            payload["release_id"] = "2.0.0"
            (release / MANIFEST_NAME).write_text(json.dumps(payload), encoding="utf-8")
            manifest = ReleaseManifest.load(release / MANIFEST_NAME)
            with self.assertRaisesRegex(ManifestVerificationError, "signature"):
                manifest.verify(
                    release,
                    release / SIGNATURE_NAME,
                    public_key=public_key,
                    expected_usb_id=USB_ID,
                    expected_release_id="2.0.0",
                )

    def test_undeclared_release_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            private_key, public_key = create_signing_material(root)
            release = root / "release"
            write_signed_release(release, private_key, release_id="1.0.0")
            (release / "extra.dll").write_text("not declared", encoding="utf-8")
            manifest = ReleaseManifest.load(release / MANIFEST_NAME)

            with self.assertRaisesRegex(ManifestVerificationError, "undeclared file"):
                manifest.verify(
                    release,
                    release / SIGNATURE_NAME,
                    public_key=public_key,
                    expected_usb_id=USB_ID,
                    expected_release_id="1.0.0",
                )

    def test_verified_update_switches_pointer_and_preserves_old_release(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            private_key, public_key = create_signing_material(root)
            usb = root / "usb"
            usb.mkdir()
            write_identity(usb)
            old_release = usb / "releases" / "1.0.0"
            write_signed_release(old_release, private_key, release_id="1.0.0")
            write_active_pointer(usb, "1.0.0")
            source = root / "downloaded-2.0.0"
            write_signed_release(source, private_key, release_id="2.0.0", content="new")

            activated = UsbUpdateManager(self.make_config(public_key)).activate(usb, source)

            self.assertEqual(activated, "2.0.0")
            active = json.loads((usb / "active-release.json").read_text(encoding="utf-8"))
            self.assertEqual(active["release_id"], "2.0.0")
            self.assertTrue(old_release.is_dir())
            self.assertTrue((usb / "releases" / "2.0.0" / MANIFEST_NAME).is_file())

    def test_failed_update_leaves_working_pointer_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            private_key, public_key = create_signing_material(root)
            usb = root / "usb"
            usb.mkdir()
            write_identity(usb)
            write_active_pointer(usb, "1.0.0")
            write_signed_release(
                usb / "releases" / "1.0.0", private_key, release_id="1.0.0"
            )
            source = root / "downloaded-2.0.0"
            executable = write_signed_release(source, private_key, release_id="2.0.0")
            executable.write_text("corrupt", encoding="utf-8")

            with self.assertRaises(ManifestVerificationError):
                UsbUpdateManager(self.make_config(public_key)).activate(usb, source)

            active = json.loads((usb / "active-release.json").read_text(encoding="utf-8"))
            self.assertEqual(active["release_id"], "1.0.0")
            self.assertFalse((usb / "releases" / "2.0.0").exists())

    def test_recovery_ignores_corrupt_and_interrupted_releases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            private_key, public_key = create_signing_material(root)
            usb = root / "usb"
            usb.mkdir()
            write_identity(usb)
            write_active_pointer(usb, "missing")
            write_signed_release(
                usb / "releases" / "1.0.0", private_key, release_id="1.0.0"
            )
            corrupt = usb / "releases" / "9.0.0"
            executable = write_signed_release(corrupt, private_key, release_id="9.0.0")
            executable.write_text("corrupt", encoding="utf-8")
            interrupted = usb / "releases" / ".staging-2.0.0-deadbeef"
            interrupted.mkdir(parents=True)
            (interrupted / "partial").write_text("partial", encoding="utf-8")

            recovered = UsbUpdateManager(self.make_config(public_key)).recover(usb)

            self.assertEqual(recovered, "1.0.0")
            active = json.loads((usb / "active-release.json").read_text(encoding="utf-8"))
            self.assertEqual(active["release_id"], "1.0.0")
            self.assertFalse(interrupted.exists())


if __name__ == "__main__":
    unittest.main()
