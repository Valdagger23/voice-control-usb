"""Tests for the friendly USB-root Voice Control executable."""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from packaging_helpers import (
    create_signing_material,
    write_active_pointer,
    write_identity,
    write_signed_release,
)
from voice_control_usb.portable.launcher import (
    PortableLaunchSpec,
    PortableLauncher,
    resolve_usb_root,
)
from voice_control_usb.runtime_support import AssistantInstanceGuard
from voice_control_usb.starter.manifest import ManifestVerificationError


class FakeLauncher:
    def __init__(self) -> None:
        self.specs: list[PortableLaunchSpec] = []

    def launch(self, spec: PortableLaunchSpec) -> object:
        self.specs.append(spec)
        return object()


class PortableLauncherTests(unittest.TestCase):
    def prepare_usb(self, parent: Path, release_id: str = "1.0.0") -> tuple[Path, Path, str]:
        private_key, public_key = create_signing_material(parent)
        usb_root = parent / "USB"
        usb_root.mkdir()
        write_identity(usb_root)
        write_active_pointer(usb_root, release_id)
        executable = write_signed_release(
            usb_root / "releases" / release_id,
            private_key,
            release_id=release_id,
        )
        return usb_root, executable, public_key

    def test_launches_visible_verified_release_from_current_usb_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            usb_root, executable, public_key = self.prepare_usb(Path(tmp_dir))
            process_launcher = FakeLauncher()

            result = PortableLauncher(public_key, process_launcher).launch(usb_root)

            self.assertTrue(result.launched)
            self.assertFalse(result.revealed_existing)
            self.assertEqual(result.release_id, "1.0.0")
            self.assertEqual(len(process_launcher.specs), 1)
            spec = process_launcher.specs[0]
            self.assertEqual(spec.usb_root, usb_root.resolve())
            self.assertEqual(spec.cwd, (usb_root / "releases" / "1.0.0").resolve())
            self.assertEqual(
                spec.command,
                (
                    str(executable.resolve()),
                    "--window",
                    "--usb-root",
                    str(usb_root.resolve()),
                    "--runtime-dir",
                    str((usb_root / "runtime").resolve()),
                ),
            )
            self.assertNotIn("--start-minimized", spec.command)

    def test_launcher_location_changes_with_usb_drive_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            parent = Path(tmp_dir)
            launcher_path = parent / "G" / "Voice Control.exe"

            self.assertEqual(
                resolve_usb_root(executable_path=launcher_path, frozen=True),
                launcher_path.parent.resolve(),
            )

    def test_tampered_release_is_rejected_before_process_launch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            usb_root, executable, public_key = self.prepare_usb(Path(tmp_dir))
            executable.write_text("tampered", encoding="utf-8")
            process_launcher = FakeLauncher()

            with self.assertRaisesRegex(ManifestVerificationError, "mismatch"):
                PortableLauncher(public_key, process_launcher).launch(usb_root)

            self.assertEqual(process_launcher.specs, [])

    def test_missing_active_pointer_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            usb_root, _executable, public_key = self.prepare_usb(Path(tmp_dir))
            (usb_root / "active-release.json").unlink()

            with self.assertRaisesRegex(ManifestVerificationError, "Active release pointer"):
                PortableLauncher(public_key, FakeLauncher()).launch(usb_root)

    def test_existing_instance_receives_show_window_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            usb_root, _executable, public_key = self.prepare_usb(Path(tmp_dir))
            runtime = usb_root / "runtime"
            runtime.mkdir()
            (runtime / "assistant.lock").write_text(
                json.dumps({"pid": os.getpid()}), encoding="utf-8"
            )
            process_launcher = FakeLauncher()

            with patch.object(AssistantInstanceGuard, "_pid_is_running", return_value=True):
                result = PortableLauncher(public_key, process_launcher).launch(usb_root)

            self.assertFalse(result.launched)
            self.assertTrue(result.revealed_existing)
            self.assertTrue((runtime / "show-window.request").is_file())
            self.assertEqual(process_launcher.specs, [])

    def test_invalid_runtime_lock_is_not_silently_removed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            usb_root, _executable, public_key = self.prepare_usb(Path(tmp_dir))
            runtime = usb_root / "runtime"
            runtime.mkdir()
            lock_path = runtime / "assistant.lock"
            lock_path.write_text("not-json", encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "invalid runtime lock"):
                PortableLauncher(public_key, FakeLauncher()).launch(usb_root)

            self.assertTrue(lock_path.is_file())


if __name__ == "__main__":
    unittest.main()
