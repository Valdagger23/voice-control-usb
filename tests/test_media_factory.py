"""Tests for media adapter selection."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from voice_control_usb.media.adapter import StubMediaAdapter
from voice_control_usb.media.factory import create_media_adapter
from voice_control_usb.media.windows_adapter import WindowsMediaAdapter


class MediaFactoryTests(unittest.TestCase):
    def test_stub_media_adapter_is_default(self) -> None:
        self.assertIsInstance(create_media_adapter(), StubMediaAdapter)

    def test_unknown_media_adapter_fails(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unknown media adapter"):
            create_media_adapter("unknown")

    def test_windows_media_adapter_is_platform_guarded(self) -> None:
        with patch("voice_control_usb.media.factory.sys.platform", "linux"):
            with self.assertRaisesRegex(RuntimeError, "only available on Windows"):
                create_media_adapter("windows")

    @unittest.skipUnless(__import__("sys").platform == "win32", "Windows-only adapter check")
    def test_windows_media_adapter_can_be_selected_when_dependencies_exist(self) -> None:
        self.assertIsInstance(create_media_adapter("windows"), WindowsMediaAdapter)


if __name__ == "__main__":
    unittest.main()
