"""Focused failure tests for the native Excel COM boundary."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from voice_control_usb.excel.com_adapter import ComExcelAdapter


class _DisconnectedExcel:
    @property
    def Workbooks(self) -> object:
        raise OSError("COM server disconnected")


class ComExcelAdapterFailureTests(unittest.TestCase):
    def test_lost_excel_session_has_a_clear_recovery_message(self) -> None:
        adapter = ComExcelAdapter(_excel=_DisconnectedExcel())

        with patch("voice_control_usb.excel.com_adapter.sys.platform", "win32"):
            with self.assertRaisesRegex(
                RuntimeError,
                "Excel session is no longer available",
            ):
                adapter.report_current_cell()

        self.assertIsNone(adapter._excel)


if __name__ == "__main__":
    unittest.main()
