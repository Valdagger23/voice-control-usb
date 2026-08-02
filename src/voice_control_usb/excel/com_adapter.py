"""Windows COM-backed Excel adapter."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import sys
from typing import Any

from voice_control_usb.excel.adapter import (
    MAX_EXCEL_COLUMNS,
    MAX_EXCEL_ROWS,
    ExcelAdapter,
    ExcelContext,
    ExcelValue,
)


class ExcelSessionDisconnectedError(RuntimeError):
    """Raised when the bound Excel COM process is no longer reachable."""


@dataclass(frozen=True, slots=True)
class ComCellEdit:
    """The last assistant-made COM cell edit."""

    workbook_key: str
    sheet_name: str
    cell: str
    previous_value: object


@dataclass
class ComExcelAdapter(ExcelAdapter):
    """Drive Excel through object-level COM automation on Windows."""

    visible: bool = True
    _excel: Any | None = None
    _start_columns: dict[tuple[str, str], int] = field(default_factory=dict)
    _last_edit: ComCellEdit | None = None

    def open_excel(self) -> str:
        try:
            excel = self._get_excel()
        except ExcelSessionDisconnectedError:
            excel = self._get_excel()
        excel.Visible = self.visible
        self._ensure_workbook()
        return "Excel session ready (COM)"

    def open_workbook(self, path: str) -> str:
        excel = self._get_excel()
        excel.Visible = self.visible
        normalized_path = str(Path(path))
        if not Path(normalized_path).is_file():
            raise FileNotFoundError(f"Workbook not found: {normalized_path}")
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

    def report_current_cell(self) -> str:
        active_cell = self._active_cell()
        value = self._read_cell_value(active_cell)
        return f"Current cell: {self.current_cell} (value: {self._display_value(value)})"

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

    def type_text(self, value: ExcelValue) -> str:
        active_cell = self._active_cell()
        worksheet = self._active_sheet()
        if bool(getattr(worksheet, "ProtectContents", False)):
            raise ValueError(f"Worksheet is protected: {worksheet.Name}")
        cell = self.current_cell
        context = self.current_context()
        self._last_edit = ComCellEdit(
            workbook_key=context.workbook_path or context.workbook_name or "",
            sheet_name=context.sheet_name or "",
            cell=cell,
            previous_value=self._read_cell_content(active_cell),
        )
        try:
            active_cell.Value = value
        except Exception as error:
            self._last_edit = None
            raise RuntimeError(f"Excel could not write to {cell}: {error}") from error
        return f"Typed {self._quoted_value(value)} into {cell}"

    def undo_last_change(self) -> str:
        edit = self._last_edit
        if edit is None:
            return "No assistant-made Excel change to undo."
        workbook = self._find_workbook_by_key(edit.workbook_key)
        if workbook is None:
            raise ValueError("The workbook for the last Excel change is no longer open.")
        try:
            worksheet = workbook.Worksheets(edit.sheet_name)
            if bool(getattr(worksheet, "ProtectContents", False)):
                raise ValueError(f"Worksheet is protected: {worksheet.Name}")
            worksheet.Range(edit.cell).Formula = edit.previous_value
        except ValueError:
            raise
        except Exception as error:
            raise RuntimeError(
                f"Excel could not undo the change in {edit.sheet_name}!{edit.cell}: {error}"
            ) from error
        self._last_edit = None
        return f"Undid last Excel change in {edit.sheet_name}!{edit.cell}."

    def go_left(self) -> str:
        active_cell = self._active_cell()
        if int(active_cell.Column) <= 1:
            raise ValueError("Cannot move left from column A.")
        self._active_sheet().Cells(
            int(active_cell.Row),
            int(active_cell.Column) - 1,
        ).Select()
        return f"Moved left to {self.current_cell}"

    def go_right(self) -> str:
        active_cell = self._active_cell()
        if int(active_cell.Column) >= MAX_EXCEL_COLUMNS:
            raise ValueError("Cannot move right from column XFD.")
        self._active_sheet().Cells(
            int(active_cell.Row),
            int(active_cell.Column) + 1,
        ).Select()
        return f"Moved right to {self.current_cell}"

    def go_down(self) -> str:
        active_cell = self._active_cell()
        if int(active_cell.Row) >= MAX_EXCEL_ROWS:
            raise ValueError("Cannot move down from row 1048576.")
        self._active_sheet().Cells(
            int(active_cell.Row) + 1,
            int(active_cell.Column),
        ).Select()
        return f"Moved down to {self.current_cell}"

    def go_up(self) -> str:
        active_cell = self._active_cell()
        if int(active_cell.Row) <= 1:
            raise ValueError("Cannot move up from row 1.")
        self._active_sheet().Cells(
            int(active_cell.Row) - 1,
            int(active_cell.Column),
        ).Select()
        return f"Moved up to {self.current_cell}"

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

        if self._excel is not None:
            try:
                _ = self._excel.Workbooks.Count
            except Exception as error:
                self._excel = None
                raise ExcelSessionDisconnectedError(
                    "Excel session is no longer available. Run 'open excel' to reconnect."
                ) from error

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

    def _find_workbook_by_key(self, key: str) -> Any | None:
        excel = self._get_excel()
        normalized_key = key.lower()
        for index in range(1, int(excel.Workbooks.Count) + 1):
            workbook = excel.Workbooks(index)
            workbook_path = str(getattr(workbook, "FullName", ""))
            workbook_name = str(getattr(workbook, "Name", ""))
            if normalized_key in (workbook_path.lower(), workbook_name.lower()):
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

    @staticmethod
    def _display_value(value: object) -> str:
        if value is None or value == "":
            return "<empty>"
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value)

    @staticmethod
    def _quoted_value(value: ExcelValue) -> str:
        if isinstance(value, str):
            return f"'{value}'"
        return str(value)

    @staticmethod
    def _read_cell_value(cell: Any) -> object:
        try:
            return cell.Value2
        except AttributeError:
            return cell.Value

    @staticmethod
    def _read_cell_content(cell: Any) -> object:
        try:
            return cell.Formula
        except AttributeError:
            return ComExcelAdapter._read_cell_value(cell)
