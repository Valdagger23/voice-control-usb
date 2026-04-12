"""Windows COM-backed Excel adapter."""

from __future__ import annotations

from dataclasses import dataclass
import sys
from typing import Any

from voice_control_usb.excel.adapter import ExcelAdapter


@dataclass
class ComExcelAdapter(ExcelAdapter):
    """Drive Excel through object-level COM automation on Windows."""

    visible: bool = True
    start_column: int | None = None
    _excel: Any | None = None

    def open_excel(self) -> str:
        excel = self._get_excel()
        excel.Visible = self.visible
        self._ensure_workbook()
        return "Excel session ready (COM)"

    def go_to_cell(self, cell: str) -> str:
        worksheet = self._active_sheet()
        target = worksheet.Range(cell.upper())
        target.Select()
        self.start_column = int(target.Column)
        return f"Moved to {self.current_cell}"

    def type_text(self, value: str) -> str:
        active_cell = self._active_cell()
        active_cell.Value = value
        return f"Typed '{value}' into {self.current_cell}"

    def go_right(self) -> str:
        target = self._active_cell().Offset(0, 1)
        target.Select()
        return f"Moved right to {self.current_cell}"

    def go_down(self) -> str:
        target = self._active_cell().Offset(1, 0)
        target.Select()
        return f"Moved down to {self.current_cell}"

    def next_row_from_start(self) -> str:
        if self.start_column is None:
            raise ValueError("No starting column is set. Use 'go to <CELL>' first.")

        active_cell = self._active_cell()
        target = self._active_sheet().Cells(int(active_cell.Row) + 1, self.start_column)
        target.Select()
        return f"Moved to next row start at {self.current_cell}"

    @property
    def current_cell(self) -> str:
        active_cell = self._active_cell()
        return f"{self._column_letters(int(active_cell.Column))}{int(active_cell.Row)}"

    def _get_excel(self) -> Any:
        if sys.platform != "win32":
            raise RuntimeError("The COM Excel adapter is only available on Windows.")

        if self._excel is None:
            try:
                import win32com.client  # type: ignore[import-not-found]
            except ImportError as error:
                raise ImportError(
                    "pywin32 is required for the COM Excel adapter. Install it with "
                    "'pip install pywin32' or 'pip install .[windows]' on Windows."
                ) from error

            self._excel = win32com.client.Dispatch("Excel.Application")
        return self._excel

    def _ensure_workbook(self) -> Any:
        excel = self._get_excel()
        if int(excel.Workbooks.Count) == 0:
            workbook = excel.Workbooks.Add()
            workbook.Worksheets(1).Activate()
            workbook.ActiveSheet.Cells(1, 1).Select()
            return workbook

        active_workbook = excel.ActiveWorkbook
        if active_workbook is not None:
            return active_workbook
        return excel.Workbooks(1)

    def _active_sheet(self) -> Any:
        workbook = self._ensure_workbook()
        return workbook.ActiveSheet

    def _active_cell(self) -> Any:
        excel = self._get_excel()
        self._ensure_workbook()
        active_cell = excel.ActiveCell
        if active_cell is None:
            fallback = self._active_sheet().Cells(1, 1)
            fallback.Select()
            return fallback
        return active_cell

    def _column_letters(self, number: int) -> str:
        result: list[str] = []
        current = number
        while current > 0:
            current, remainder = divmod(current - 1, 26)
            result.append(chr(ord("A") + remainder))
        return "".join(reversed(result))
