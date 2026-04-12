"""Excel automation abstractions."""

from voice_control_usb.excel.adapter import ExcelAdapter, StubExcelAdapter
from voice_control_usb.excel.com_adapter import ComExcelAdapter
from voice_control_usb.excel.factory import create_excel_adapter

__all__ = [
    "ComExcelAdapter",
    "ExcelAdapter",
    "StubExcelAdapter",
    "create_excel_adapter",
]
