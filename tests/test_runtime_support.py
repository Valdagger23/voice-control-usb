"""Tests for packaged runtime path helpers and duplicate-instance guarding."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from voice_control_usb.runtime_support import (
    AssistantInstanceGuard,
    AssistantRuntimePaths,
    DuplicateInstanceError,
    package_root,
    resolve_packaged_data_path,
)


class RuntimeSupportTests(unittest.TestCase):
    def test_assistant_runtime_paths_resolve_usb_runtime_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            usb_root = Path(tmp_dir) / "usb"
            usb_root.mkdir()

            runtime_paths = AssistantRuntimePaths.from_cli(usb_root=str(usb_root))

            self.assertEqual(runtime_paths.usb_root, usb_root.resolve())
            self.assertEqual(runtime_paths.runtime_dir, (usb_root / "runtime").resolve())
            self.assertEqual(
                runtime_paths.proposal_path,
                (usb_root / "runtime" / "proposals" / "unsupported_commands.jsonl").resolve(),
            )

    def test_assistant_runtime_paths_reject_missing_usb_root(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "Configured USB root does not exist"):
            AssistantRuntimePaths.from_cli(usb_root="/does/not/exist")

    def test_resolve_packaged_data_path_uses_source_tree_by_default(self) -> None:
        path = resolve_packaged_data_path("core", "command_registry.json")

        self.assertTrue(path.is_file())
        self.assertEqual(path.name, "command_registry.json")

    def test_resolve_packaged_data_path_uses_packaged_base_when_provided(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            packaged_base = Path(tmp_dir)
            package_dir = packaged_base / "voice_control_usb" / "core"
            package_dir.mkdir(parents=True)
            resource_path = package_dir / "command_registry.json"
            resource_path.write_text('{"commands": []}', encoding="utf-8")

            resolved = resolve_packaged_data_path(
                "core",
                "command_registry.json",
                packaged_base=packaged_base,
            )

            self.assertEqual(resolved, resource_path)

    def test_resolve_packaged_data_path_reports_missing_resource(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            with self.assertRaisesRegex(FileNotFoundError, "Required runtime data file not found"):
                resolve_packaged_data_path(
                    "core",
                    "missing.json",
                    packaged_base=Path(tmp_dir),
                )

    def test_package_root_uses_packaged_base(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            resolved = package_root(packaged_base=Path(tmp_dir))

            self.assertEqual(resolved, Path(tmp_dir).resolve() / "voice_control_usb")

    def test_instance_guard_blocks_duplicate_live_instance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            lock_path = Path(tmp_dir) / "assistant.lock"
            first = AssistantInstanceGuard(lock_path, pid_provider=lambda: 1234)
            second = AssistantInstanceGuard(lock_path, pid_provider=lambda: 5678)

            try:
                first.acquire()
                with patch.object(AssistantInstanceGuard, "_pid_is_running", return_value=True):
                    with self.assertRaisesRegex(DuplicateInstanceError, "Assistant already running"):
                        second.acquire()
            finally:
                first.release()

    def test_instance_guard_recovers_stale_lock(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            lock_path = Path(tmp_dir) / "assistant.lock"
            lock_path.write_text('{"pid": 999999}', encoding="utf-8")
            guard = AssistantInstanceGuard(lock_path, pid_provider=lambda: 1234)

            with patch.object(AssistantInstanceGuard, "_pid_is_running", return_value=False):
                guard.acquire()
            self.assertTrue(lock_path.exists())
            guard.release()
            self.assertFalse(lock_path.exists())


if __name__ == "__main__":
    unittest.main()
