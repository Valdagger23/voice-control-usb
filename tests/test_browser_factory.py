"""Tests for visible browser adapter selection."""

from pathlib import Path
import unittest
from unittest.mock import patch

from voice_control_usb.browser.adapter import StubBrowserAdapter
from voice_control_usb.browser.factory import (
    create_browser_adapter,
    default_browser_profile_dir,
)
from voice_control_usb.browser.playwright_adapter import PlaywrightBrowserAdapter


class BrowserFactoryTests(unittest.TestCase):
    def test_stub_is_default(self) -> None:
        self.assertIsInstance(create_browser_adapter(), StubBrowserAdapter)

    def test_playwright_requires_windows_and_profile(self) -> None:
        with patch("voice_control_usb.browser.factory.sys.platform", "linux"):
            with self.assertRaisesRegex(RuntimeError, "only available on Windows"):
                create_browser_adapter("playwright", profile_dir=Path("profile"))
        with patch("voice_control_usb.browser.factory.sys.platform", "win32"):
            with self.assertRaisesRegex(ValueError, "profile directory"):
                create_browser_adapter("playwright")

    def test_playwright_adapter_is_lazy(self) -> None:
        with patch("voice_control_usb.browser.factory.sys.platform", "win32"):
            adapter = create_browser_adapter("playwright", profile_dir=Path("profile"))
        self.assertIsInstance(adapter, PlaywrightBrowserAdapter)
        self.assertIsNone(adapter._context)

    def test_default_profile_is_host_local_not_usb_runtime(self) -> None:
        with patch.dict(
            "voice_control_usb.browser.factory.os.environ",
            {"LOCALAPPDATA": "C:\\Users\\Example\\AppData\\Local"},
            clear=True,
        ):
            profile = default_browser_profile_dir()
        self.assertEqual(profile.name, "browser-profile")
        self.assertEqual(profile.parent.name, "VoiceControlUSB")
        self.assertNotIn("runtime", profile.parts)


if __name__ == "__main__":
    unittest.main()
