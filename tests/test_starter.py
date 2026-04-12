"""Tests for the trusted USB starter."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

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
        self.process = FakeProcess(running=True)

    def launch(self, spec: LaunchSpec) -> FakeProcess:
        self.specs.append(spec)
        return self.process


class FakeVolumeProvider:
    def __init__(self, volumes: list[UsbVolume]) -> None:
        self.volumes = volumes

    def list_volumes(self) -> list[UsbVolume]:
        return list(self.volumes)


class StarterConfigTests(unittest.TestCase):
    def test_loads_json_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "starter.json"
            config_path.write_text(
                json.dumps(
                    {
                        "expected_volume_label": "VOICEBOT",
                        "trust_marker": "trusted.marker",
                        "assistant_relative_executable": "assistant\\voice-control-usb-assistant.exe",
                        "assistant_workdir": ".",
                        "poll_interval_seconds": 3.5,
                        "log_path": str(Path(tmp_dir) / "starter.log"),
                    }
                ),
                encoding="utf-8",
            )

            config = StarterConfig.load(config_path)

            self.assertEqual(config.expected_volume_label, "VOICEBOT")
            self.assertEqual(config.trust_marker, "trusted.marker")
            self.assertEqual(
                config.assistant_relative_executable,
                "assistant\\voice-control-usb-assistant.exe",
            )
            self.assertEqual(config.poll_interval_seconds, 3.5)
            self.assertEqual(config.log_path, Path(tmp_dir) / "starter.log")

    def test_requires_expected_volume_label(self) -> None:
        with self.assertRaisesRegex(ValueError, "expected_volume_label is required"):
            StarterConfig.from_dict({})


class TrustedUsbStarterTests(unittest.TestCase):
    def make_config(self, **overrides: object) -> StarterConfig:
        payload: dict[str, object] = {
            "expected_volume_label": "VOICEBOT",
            "trust_marker": "voice-control-usb.trusted",
            "assistant_relative_executable": "dist/voice-control-usb-assistant/voice-control-usb-assistant.exe",
            "assistant_workdir": ".",
            "poll_interval_seconds": 1.0,
        }
        payload.update(overrides)
        return StarterConfig.from_dict(payload)

    def test_validates_volume_label_and_marker_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            trusted_root = Path(tmp_dir) / "trusted"
            trusted_root.mkdir()
            (trusted_root / "voice-control-usb.trusted").write_text("ok", encoding="utf-8")
            untrusted_root = Path(tmp_dir) / "untrusted"
            untrusted_root.mkdir()

            starter = TrustedUsbStarter(
                config=self.make_config(),
                volume_provider=FakeVolumeProvider([]),
            )

            self.assertTrue(
                starter.is_trusted_volume(
                    UsbVolume(mount_path=trusted_root, volume_label="VOICEBOT")
                )
            )
            self.assertFalse(
                starter.is_trusted_volume(
                    UsbVolume(mount_path=trusted_root, volume_label="OTHER")
                )
            )
            self.assertFalse(
                starter.is_trusted_volume(
                    UsbVolume(mount_path=untrusted_root, volume_label="VOICEBOT")
                )
            )

    def test_scan_launches_trusted_usb_once_and_prevents_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            usb_root = Path(tmp_dir) / "usb"
            usb_root.mkdir()
            (usb_root / "voice-control-usb.trusted").write_text("ok", encoding="utf-8")
            packaged_dir = usb_root / "dist" / "voice-control-usb-assistant"
            packaged_dir.mkdir(parents=True)
            packaged_exe = packaged_dir / "voice-control-usb-assistant.exe"
            packaged_exe.write_text("stub", encoding="utf-8")
            launcher = FakeLauncher()
            starter = TrustedUsbStarter(
                config=self.make_config(),
                volume_provider=FakeVolumeProvider(
                    [UsbVolume(mount_path=usb_root, volume_label="VOICEBOT")]
                ),
                launcher=launcher,
            )

            first = starter.scan_and_launch()
            second = starter.scan_and_launch()

            self.assertTrue(first.launched)
            self.assertFalse(second.launched)
            self.assertEqual(len(launcher.specs), 1)
            self.assertIn("Assistant already running", second.message)
            self.assertEqual(launcher.specs[0].command, (str(packaged_exe.resolve()),))
            self.assertEqual(launcher.specs[0].executable_path, packaged_exe.resolve())
            self.assertEqual(launcher.specs[0].usb_root, usb_root.resolve())
            self.assertEqual(launcher.specs[0].cwd, usb_root.resolve())
            self.assertEqual(launcher.specs[0].env_overrides, {})

    def test_finished_process_can_be_relaunched(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            usb_root = Path(tmp_dir) / "usb"
            usb_root.mkdir()
            (usb_root / "voice-control-usb.trusted").write_text("ok", encoding="utf-8")
            packaged_dir = usb_root / "dist" / "voice-control-usb-assistant"
            packaged_dir.mkdir(parents=True)
            (packaged_dir / "voice-control-usb-assistant.exe").write_text("stub", encoding="utf-8")
            launcher = FakeLauncher()
            starter = TrustedUsbStarter(
                config=self.make_config(),
                volume_provider=FakeVolumeProvider(
                    [UsbVolume(mount_path=usb_root, volume_label="VOICEBOT")]
                ),
                launcher=launcher,
            )

            starter.scan_and_launch()
            launcher.process.running = False
            second = starter.scan_and_launch()

            self.assertTrue(second.launched)
            self.assertEqual(len(launcher.specs), 2)

    def test_multiple_trusted_volumes_skip_launch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            first_root = Path(tmp_dir) / "usb-a"
            second_root = Path(tmp_dir) / "usb-b"
            first_root.mkdir()
            second_root.mkdir()
            (first_root / "voice-control-usb.trusted").write_text("ok", encoding="utf-8")
            (second_root / "voice-control-usb.trusted").write_text("ok", encoding="utf-8")
            for root in (first_root, second_root):
                packaged_dir = root / "dist" / "voice-control-usb-assistant"
                packaged_dir.mkdir(parents=True)
                (packaged_dir / "voice-control-usb-assistant.exe").write_text("stub", encoding="utf-8")
            launcher = FakeLauncher()
            starter = TrustedUsbStarter(
                config=self.make_config(),
                volume_provider=FakeVolumeProvider(
                    [
                        UsbVolume(mount_path=first_root, volume_label="VOICEBOT"),
                        UsbVolume(mount_path=second_root, volume_label="VOICEBOT"),
                    ]
                ),
                launcher=launcher,
            )

            result = starter.scan_and_launch()

            self.assertFalse(result.launched)
            self.assertEqual(result.message, "Multiple trusted USB volumes detected. Launch skipped.")
            self.assertEqual(launcher.specs, [])

    def test_missing_packaged_assistant_skips_launch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            usb_root = Path(tmp_dir) / "usb"
            usb_root.mkdir()
            (usb_root / "voice-control-usb.trusted").write_text("ok", encoding="utf-8")
            launcher = FakeLauncher()
            starter = TrustedUsbStarter(
                config=self.make_config(),
                volume_provider=FakeVolumeProvider(
                    [UsbVolume(mount_path=usb_root, volume_label="VOICEBOT")]
                ),
                launcher=launcher,
            )

            result = starter.scan_and_launch()

            self.assertFalse(result.launched)
            self.assertIn("Packaged assistant executable not found on trusted USB", result.message)
            self.assertEqual(launcher.specs, [])


if __name__ == "__main__":
    unittest.main()
