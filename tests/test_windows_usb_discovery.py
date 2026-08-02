"""Regression tests for native Windows removable-drive enumeration."""

from __future__ import annotations

import unittest

from voice_control_usb.starter.windows import _split_logical_drive_strings


class WindowsUsbDiscoveryTests(unittest.TestCase):
    def test_multi_string_keeps_drives_after_system_drive(self) -> None:
        self.assertEqual(
            _split_logical_drive_strings("C:\\\x00D:\\\x00E:\\\x00\x00"),
            ["C:\\", "D:\\", "E:\\"],
        )


if __name__ == "__main__":
    unittest.main()
