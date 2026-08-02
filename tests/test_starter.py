"""Tests for the trusted USB starter."""

from __future__ import annotations

import json
import os
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
from voice_control_usb.starter.service import LaunchSpec, TrustedUsbStarter, UsbVolume


class FakeProcess:
    def __init__(self, running: bool = True) -> None:
        self.running = running

    def poll(self) -> int | None:
        return None if self.running else 0


class FakeLauncher:
    def __init__(self) -> None:
        self.specs: list[LaunchSpec] = []
        self.process = FakeProcess()

    def launch(self, spec: LaunchSpec) -> FakeProcess:
        self.specs.append(spec)
        return self.process


class FakeVolumeProvider:
    def __init__(self, volumes: list[UsbVolume]) -> None:
        self.volumes = volumes

    def list_volumes(self) -> list[UsbVolume]:
        return list(self.volumes)


class StarterTests(unittest.TestCase):
    def make_config(self, public_key: str, **overrides: object) -> StarterConfig:
        payload: dict[str, object] = {
            "expected_volume_label": "VOICEBOT",
            "expected_usb_id": USB_ID,
            "manifest_public_key": public_key,
            "poll_interval_seconds": 1.0,
            "shutdown_timeout_seconds": 0.5,
        }
        payload.update(overrides)
        return StarterConfig.from_dict(payload)

    def prepare_usb(self, root: Path, private_key: Path, release_id: str = "1.0.0") -> Path:
        root.mkdir()
        write_identity(root)
        write_active_pointer(root, release_id)
        return write_signed_release(
            root / "releases" / release_id,
            private_key,
            release_id=release_id,
        )

    def test_loads_pinned_identity_and_public_key_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "starter.json"
            path.write_text(
                json.dumps(
                    {
                        "expected_volume_label": "VOICEBOT",
                        "expected_usb_id": USB_ID.upper(),
                        "manifest_public_key": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
                        "shutdown_timeout_seconds": 8,
                    }
                ),
                encoding="utf-8",
            )
            config = StarterConfig.load(path)
            self.assertEqual(config.expected_usb_id, USB_ID)
            self.assertEqual(
                config.manifest_public_key,
                "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
            )
            self.assertEqual(config.shutdown_timeout_seconds, 8)

    def test_config_requires_pinned_usb_id_and_public_key(self) -> None:
        with self.assertRaisesRegex(ValueError, "expected_usb_id is required"):
            StarterConfig.from_dict({"expected_volume_label": "VOICEBOT"})
        with self.assertRaisesRegex(ValueError, "manifest_public_key is required"):
            StarterConfig.from_dict(
                {"expected_volume_label": "VOICEBOT", "expected_usb_id": USB_ID}
            )

    def test_launch_verifies_release_and_uses_detected_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            parent = Path(tmp_dir)
            private_key, public_key = create_signing_material(parent)
            usb_root = parent / "F"
            executable = self.prepare_usb(usb_root, private_key)
            launcher = FakeLauncher()
            starter = TrustedUsbStarter(
                self.make_config(public_key),
                FakeVolumeProvider([UsbVolume(usb_root, "VOICEBOT")]),
                launcher,
            )

            result = starter.scan_and_launch()

            self.assertTrue(result.launched)
            spec = launcher.specs[0]
            self.assertEqual(spec.executable_path, executable.resolve())
            self.assertEqual(spec.cwd, (usb_root / "releases" / "1.0.0").resolve())
            self.assertEqual(spec.release_id, "1.0.0")
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

    def test_changed_drive_path_is_resolved_on_each_scan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            parent = Path(tmp_dir)
            private_key, public_key = create_signing_material(parent)
            old_root = parent / "E"
            self.prepare_usb(old_root, private_key)
            new_root = parent / "G"
            old_root.rename(new_root)
            launcher = FakeLauncher()
            starter = TrustedUsbStarter(
                self.make_config(public_key),
                FakeVolumeProvider([UsbVolume(new_root, "VOICEBOT")]),
                launcher,
            )

            result = starter.scan_and_launch()

            self.assertTrue(result.launched)
            self.assertEqual(launcher.specs[0].usb_root, new_root.resolve())
            self.assertNotIn(str(old_root), launcher.specs[0].command)

    def test_duplicate_is_blocked_and_finished_process_can_restart(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            parent = Path(tmp_dir)
            private_key, public_key = create_signing_material(parent)
            usb_root = parent / "usb"
            self.prepare_usb(usb_root, private_key)
            launcher = FakeLauncher()
            starter = TrustedUsbStarter(
                self.make_config(public_key),
                FakeVolumeProvider([UsbVolume(usb_root, "VOICEBOT")]),
                launcher,
            )
            self.assertTrue(starter.scan_and_launch().launched)
            self.assertIn("already running", starter.scan_and_launch().message)
            launcher.process.running = False
            self.assertTrue(starter.scan_and_launch().launched)
            self.assertEqual(len(launcher.specs), 2)

    def test_live_runtime_lock_blocks_fresh_starter_before_process_launch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            parent = Path(tmp_dir)
            private_key, public_key = create_signing_material(parent)
            usb_root = parent / "usb"
            self.prepare_usb(usb_root, private_key)
            runtime = usb_root / "runtime"
            runtime.mkdir()
            (runtime / "assistant.lock").write_text(
                json.dumps({"pid": os.getpid()}), encoding="utf-8"
            )
            launcher = FakeLauncher()
            starter = TrustedUsbStarter(
                self.make_config(public_key),
                FakeVolumeProvider([UsbVolume(usb_root, "VOICEBOT")]),
                launcher,
            )

            result = starter.scan_and_launch()

            self.assertFalse(result.launched)
            self.assertIn("already running", result.message)
            self.assertEqual(launcher.specs, [])

    def test_tampered_release_is_not_launched(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            parent = Path(tmp_dir)
            private_key, public_key = create_signing_material(parent)
            usb_root = parent / "usb"
            executable = self.prepare_usb(usb_root, private_key)
            executable.write_text("tampered", encoding="utf-8")
            launcher = FakeLauncher()
            starter = TrustedUsbStarter(
                self.make_config(public_key),
                FakeVolumeProvider([UsbVolume(usb_root, "VOICEBOT")]),
                launcher,
            )
            result = starter.scan_and_launch()
            self.assertFalse(result.launched)
            self.assertIn("mismatch", result.message)
            self.assertEqual(launcher.specs, [])

    def test_wrong_usb_identity_is_not_trusted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            parent = Path(tmp_dir)
            private_key, public_key = create_signing_material(parent)
            usb_root = parent / "usb"
            self.prepare_usb(usb_root, private_key)
            write_identity(usb_root, "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
            starter = TrustedUsbStarter(
                self.make_config(public_key),
                FakeVolumeProvider([UsbVolume(usb_root, "VOICEBOT")]),
                FakeLauncher(),
            )
            self.assertEqual(starter.scan_and_launch().message, "Trusted USB not detected.")

    def test_missing_active_pointer_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            parent = Path(tmp_dir)
            private_key, public_key = create_signing_material(parent)
            usb_root = parent / "usb"
            self.prepare_usb(usb_root, private_key)
            (usb_root / "active-release.json").unlink()
            starter = TrustedUsbStarter(
                self.make_config(public_key),
                FakeVolumeProvider([UsbVolume(usb_root, "VOICEBOT")]),
                FakeLauncher(),
            )
            result = starter.scan_and_launch()
            self.assertFalse(result.launched)
            self.assertIn("Active release pointer file is missing", result.message)

    def test_prepare_removal_waits_for_lock_to_clear(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            parent = Path(tmp_dir)
            private_key, public_key = create_signing_material(parent)
            usb_root = parent / "usb"
            self.prepare_usb(usb_root, private_key)
            runtime = usb_root / "runtime"
            runtime.mkdir()
            lock = runtime / "assistant.lock"
            lock.write_text('{"pid":123}', encoding="utf-8")

            def stop_assistant(_seconds: float) -> None:
                lock.unlink(missing_ok=True)

            starter = TrustedUsbStarter(
                self.make_config(public_key),
                FakeVolumeProvider([UsbVolume(usb_root, "VOICEBOT")]),
                FakeLauncher(),
                sleeper=stop_assistant,
            )
            result = starter.request_safe_shutdown()
            self.assertEqual(result.message, "Assistant stopped; USB is ready for removal.")
            self.assertFalse((runtime / "shutdown.request").exists())

    def test_prepare_removal_timeout_warns_user(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            parent = Path(tmp_dir)
            private_key, public_key = create_signing_material(parent)
            usb_root = parent / "usb"
            self.prepare_usb(usb_root, private_key)
            runtime = usb_root / "runtime"
            runtime.mkdir()
            (runtime / "assistant.lock").write_text('{"pid":123}', encoding="utf-8")
            clock_values = iter((0.0, 1.0))
            starter = TrustedUsbStarter(
                self.make_config(public_key),
                FakeVolumeProvider([UsbVolume(usb_root, "VOICEBOT")]),
                FakeLauncher(),
                sleeper=lambda _seconds: None,
                monotonic_clock=lambda: next(clock_values),
            )
            result = starter.request_safe_shutdown()
            self.assertEqual(result.message, "Assistant did not stop in time. Do not remove the USB yet.")


if __name__ == "__main__":
    unittest.main()
