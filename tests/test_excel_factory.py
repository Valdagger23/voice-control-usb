"""Tests for Excel adapter selection."""

from __future__ import annotations

import sys
import unittest

from voice_control_usb.excel.adapter import StubExcelAdapter
from voice_control_usb.excel.factory import create_excel_adapter


class ExcelFactoryTests(unittest.TestCase):
    def test_stub_adapter_is_default(self) -> None:
        adapter = create_excel_adapter()

        self.assertIsInstance(adapter, StubExcelAdapter)

    def test_stub_adapter_can_be_selected_explicitly(self) -> None:
        adapter = create_excel_adapter("stub")

        self.assertIsInstance(adapter, StubExcelAdapter)

    def test_unknown_adapter_selection_fails(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unknown Excel adapter selection"):
            create_excel_adapter("mystery")

    def test_com_adapter_selection_is_platform_guarded(self) -> None:
        if sys.platform == "win32":
            self.skipTest("Windows COM selection is documented for manual verification.")

        with self.assertRaisesRegex(RuntimeError, "only available on Windows"):
            create_excel_adapter("com")


if __name__ == "__main__":
    unittest.main()
