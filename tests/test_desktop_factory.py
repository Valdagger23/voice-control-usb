"""Tests for desktop adapter selection and stub behavior."""

from __future__ import annotations

import sys
import tempfile
import unittest

from voice_control_usb.desktop.adapter import StubDesktopAdapter
from voice_control_usb.desktop.factory import create_desktop_adapter


class DesktopFactoryTests(unittest.TestCase):
    def test_stub_desktop_adapter_is_default(self) -> None:
        adapter = create_desktop_adapter()

        self.assertIsInstance(adapter, StubDesktopAdapter)

    def test_windows_desktop_adapter_is_platform_guarded(self) -> None:
        if sys.platform == "win32":
            self.skipTest("Windows desktop adapter is documented for manual verification.")

        with self.assertRaisesRegex(RuntimeError, "only available on Windows"):
            create_desktop_adapter("windows")

    def test_unknown_desktop_adapter_fails(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unknown desktop adapter selection"):
            create_desktop_adapter("mystery")

    def test_stub_adapter_uses_allowlist_and_safety_guards(self) -> None:
        adapter = create_desktop_adapter("stub")

        with tempfile.TemporaryDirectory() as tmp_dir:
            self.assertEqual(adapter.open_app("notepad"), "Opened app alias: notepad (stub)")
            self.assertEqual(
                adapter.open_app("powershell"),
                "Desktop app alias is not approved in MVP: powershell",
            )
            self.assertEqual(
                adapter.open_url("ftp://example.com"),
                "Desktop URL is not approved in MVP: ftp://example.com",
            )
            self.assertEqual(
                adapter.open_folder(tmp_dir),
                f"Opened folder: {tmp_dir} (stub)",
            )


if __name__ == "__main__":
    unittest.main()
