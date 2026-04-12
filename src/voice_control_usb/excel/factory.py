"""Adapter selection for development and Windows runtime."""

from __future__ import annotations

import importlib.util
import sys

from voice_control_usb.excel.adapter import ExcelAdapter, StubExcelAdapter
from voice_control_usb.excel.com_adapter import ComExcelAdapter


def create_excel_adapter(selection: str = "stub") -> ExcelAdapter:
    """Create the configured Excel adapter implementation."""

    normalized = selection.strip().lower()
    if normalized == "stub":
        return StubExcelAdapter()
    if normalized == "com":
        if sys.platform != "win32":
            raise RuntimeError("The COM Excel adapter is only available on Windows.")
        if importlib.util.find_spec("win32com") is None:
            raise ImportError(
                "pywin32 is required for the COM Excel adapter. Install it with "
                "'pip install pywin32' or 'pip install .[windows]' on Windows."
            )
        return ComExcelAdapter()
    raise ValueError(
        "Unknown Excel adapter selection. Expected one of: 'stub', 'com'."
    )
