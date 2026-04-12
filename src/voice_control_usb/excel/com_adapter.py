"""Windows COM-backed Excel adapter."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import sys
from typing import Any

from voice_control_usb.excel.adapter import ExcelAdapter, ExcelContext


@dataclass
class ComExcelAdapter(ExcelAdapter):
    """Drive Excel through object-level COM automation on Windows."""

    visible: bool = True
    _excel: Any | None = None
    _start_columns: dict[tuple[str, str], int] = field(default_factory=dict)

    def open_excel(self) -> str:
        excel = self._get_excel()
        excel.Visible = self.visible
        self._ensure_workbook()
        return "Excel session ready (COM)"

    def open_workbook(self, path: str) -> str:
        excel = self._get_excel()
        excel.Visible = self.visible
        normalized_path = str(Path(path))
        workbook = self._find_open_workbook(normalized_path)
        if workbook is None:
            workbook = excel.Workbooks.Open(normalized_path)
        workbook.Activate()
        workbook.ActiveSheet.Activate()
        return f"Opened workbook: {workbook.Name}"

    def select_sheet(self, name: str) -> str:
        workbook = self._active_workbook()
        worksheet = workbook.Worksheets(name)
        worksheet.Activate()
        return f"Selected sheet: {worksheet.Name}"

    def save_workbook(self) -> str:
        workbook = self._active_workbook()
        if not self._workbook_has_save_path(workbook):
            raise ValueError("Active workbook has no path. Use 'open workbook <PATH>' first.")
        workbook.Save()
        return f"Saved workbook: {workbook.Name}"

    def report_current_sheet(self) -> str:
        context = self.current_context()
        if context.sheet_name is None or context.workbook_name is None:
            raise ValueError("No active worksheet is available.")
        return f"Current sheet: {context.sheet_name} (workbook: {context.workbook_name})"

    def current_context(self) -> ExcelContext:
        workbook = self._active_workbook()
        sheet = workbook.ActiveSheet
        workbook_path = getattr(workbook, "FullName", None)
        if workbook_path == workbook.Name:
            workbook_path = None
        return ExcelContext(
            workbook_name=str(workbook.Name),
            workbook_path=str(workbook_path) if workbook_path else None,
            sheet_name=str(sheet.Name),
        )

    def go_to_cell(self, cell: str) -> str:
        worksheet = self._active_sheet()
        target = worksheet.Range(cell.upper())
        target.Select()
        self._set_start_column(int(target.Column))
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
        active_cell = self._active_cell()
        start_column = self._get_start_column()
        if start_column is None:
            raise ValueError("No starting column is set. Use 'go to <CELL>' first.")

        target = self._active_sheet().Cells(int(active_cell.Row) + 1, start_column)
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

    def _active_workbook(self) -> Any:
        workbook = self._ensure_workbook()
        workbook.Activate()
        return workbook

    def _active_sheet(self) -> Any:
        return self._active_workbook().ActiveSheet

    def _active_cell(self) -> Any:
        excel = self._get_excel()
        workbook = self._active_workbook()
        active_cell = excel.ActiveCell
        if active_cell is None:
            fallback = workbook.ActiveSheet.Cells(1, 1)
            fallback.Select()
            return fallback
        return active_cell

    def _find_open_workbook(self, path: str) -> Any | None:
        excel = self._get_excel()
        target = str(Path(path)).lower()
        for index in range(1, int(excel.Workbooks.Count) + 1):
            workbook = excel.Workbooks(index)
            workbook_path = getattr(workbook, "FullName", "")
            if str(workbook_path).lower() == target:
                return workbook
        return None

    def _workbook_has_save_path(self, workbook: Any) -> bool:
        full_name = getattr(workbook, "FullName", "")
        path = getattr(workbook, "Path", "")
        return bool(path and full_name)

    def _set_start_column(self, column: int) -> None:
        self._start_columns[self._context_key()] = column

    def _get_start_column(self) -> int | None:
        return self._start_columns.get(self._context_key())

    def _context_key(self) -> tuple[str, str]:
        context = self.current_context()
        return (
            context.workbook_path or context.workbook_name or "",
            context.sheet_name or "",
        )

    def _column_letters(self, number: int) -> str:
        result: list[str] = []
        current = number
        while current > 0:
            current, remainder = divmod(current - 1, 26)
            result.append(chr(ord("A") + remainder))
        return "".join(reversed(result))
