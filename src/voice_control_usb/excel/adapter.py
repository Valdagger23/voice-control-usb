"""Excel adapter interface and WSL-safe stub implementation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path, PureWindowsPath


@dataclass(frozen=True, slots=True)
class ExcelContext:
    """Workbook and worksheet context exposed by the adapter boundary."""

    workbook_name: str | None
    workbook_path: str | None
    sheet_name: str | None


@dataclass
class SheetState:
    """Per-sheet deterministic state for the stub adapter."""

    cells: dict[str, str] = field(default_factory=dict)
    current_row: int = 1
    current_column: int = 1
    start_column: int | None = None


@dataclass
class WorkbookState:
    """Per-workbook deterministic state for the stub adapter."""

    name: str
    path: str | None = None
    sheets: dict[str, SheetState] = field(default_factory=dict)
    active_sheet_name: str = "Sheet1"
    saved: bool = False


class ExcelAdapter:
    """Object-level Excel operations only."""

    def open_excel(self) -> str:
        raise NotImplementedError

    def open_workbook(self, path: str) -> str:
        raise NotImplementedError

    def select_sheet(self, name: str) -> str:
        raise NotImplementedError

    def save_workbook(self) -> str:
        raise NotImplementedError

    def report_current_sheet(self) -> str:
        raise NotImplementedError

    def current_context(self) -> ExcelContext:
        raise NotImplementedError

    def go_to_cell(self, cell: str) -> str:
        raise NotImplementedError

    def type_text(self, value: str) -> str:
        raise NotImplementedError

    def go_right(self) -> str:
        raise NotImplementedError

    def go_down(self) -> str:
        raise NotImplementedError

    def next_row_from_start(self) -> str:
        raise NotImplementedError


@dataclass
class StubExcelAdapter(ExcelAdapter):
    """Safe test stub until Windows COM integration is added."""

    opened: bool = False
    workbooks: dict[str, WorkbookState] = field(default_factory=dict)
    active_workbook_key: str | None = None
    _untitled_counter: int = 1

    def open_excel(self) -> str:
        self.opened = True
        self._ensure_workbook()
        return "Excel session ready (stub)"

    def open_workbook(self, path: str) -> str:
        normalized_path = str(Path(path))
        workbook_name = self._path_name(path)
        workbook = self.workbooks.get(normalized_path)
        if workbook is None:
            workbook = WorkbookState(
                name=workbook_name,
                path=normalized_path,
                sheets=self._default_sheets(),
                active_sheet_name="Sheet1",
                saved=True,
            )
            self.workbooks[normalized_path] = workbook

        self.opened = True
        self.active_workbook_key = normalized_path
        return f"Opened workbook: {workbook.name}"

    def select_sheet(self, name: str) -> str:
        workbook = self._active_workbook()
        if name not in workbook.sheets:
            raise ValueError(f"Worksheet not found: {name}")
        workbook.active_sheet_name = name
        return f"Selected sheet: {name}"

    def save_workbook(self) -> str:
        workbook = self._active_workbook()
        if workbook.path is None:
            raise ValueError("Active workbook has no path. Use 'open workbook <PATH>' first.")
        workbook.saved = True
        return f"Saved workbook: {workbook.name}"

    def report_current_sheet(self) -> str:
        context = self.current_context()
        if context.sheet_name is None or context.workbook_name is None:
            raise ValueError("No active worksheet is available.")
        return f"Current sheet: {context.sheet_name} (workbook: {context.workbook_name})"

    def current_context(self) -> ExcelContext:
        workbook = self._active_workbook()
        return ExcelContext(
            workbook_name=workbook.name,
            workbook_path=workbook.path,
            sheet_name=workbook.active_sheet_name,
        )

    def go_to_cell(self, cell: str) -> str:
        row, column = self._parse_cell_reference(cell)
        sheet = self._active_sheet()
        sheet.current_row = row
        sheet.current_column = column
        sheet.start_column = column
        return f"Moved to {self.current_cell}"

    def type_text(self, value: str) -> str:
        sheet = self._active_sheet()
        sheet.cells[self.current_cell] = value
        return f"Typed '{value}' into {self.current_cell}"

    def go_right(self) -> str:
        sheet = self._active_sheet()
        sheet.current_column += 1
        return f"Moved right to {self.current_cell}"

    def go_down(self) -> str:
        sheet = self._active_sheet()
        sheet.current_row += 1
        return f"Moved down to {self.current_cell}"

    def next_row_from_start(self) -> str:
        sheet = self._active_sheet()
        if sheet.start_column is None:
            raise ValueError("No starting column is set. Use 'go to <CELL>' first.")
        sheet.current_row += 1
        sheet.current_column = sheet.start_column
        return f"Moved to next row start at {self.current_cell}"

    @property
    def current_cell(self) -> str:
        sheet = self._active_sheet()
        return f"{self._column_letters(sheet.current_column)}{sheet.current_row}"

    @property
    def cells(self) -> dict[str, str]:
        """Compatibility view used by tests for the active sheet cells."""

        return self._active_sheet().cells

    def _ensure_workbook(self) -> WorkbookState:
        if self.active_workbook_key is None:
            workbook_name = f"Book{self._untitled_counter}"
            self._untitled_counter += 1
            key = f"__untitled__:{workbook_name}"
            self.workbooks[key] = WorkbookState(
                name=workbook_name,
                path=None,
                sheets=self._default_sheets(),
                active_sheet_name="Sheet1",
                saved=False,
            )
            self.active_workbook_key = key
        return self.workbooks[self.active_workbook_key]

    def _active_workbook(self) -> WorkbookState:
        return self._ensure_workbook()

    def _active_sheet(self) -> SheetState:
        workbook = self._active_workbook()
        return workbook.sheets[workbook.active_sheet_name]

    def _default_sheets(self) -> dict[str, SheetState]:
        return {
            "Sheet1": SheetState(),
            "Sheet2": SheetState(),
            "Sheet3": SheetState(),
        }

    def _path_name(self, path: str) -> str:
        windows_name = PureWindowsPath(path).name
        posix_name = Path(path).name
        return windows_name or posix_name or path

    def _parse_cell_reference(self, cell: str) -> tuple[int, int]:
        letters = "".join(character for character in cell if character.isalpha()).upper()
        digits = "".join(character for character in cell if character.isdigit())
        if not letters or not digits:
            raise ValueError(f"Invalid cell reference: {cell}")
        return int(digits), self._column_number(letters)

    def _column_number(self, letters: str) -> int:
        total = 0
        for character in letters:
            total = (total * 26) + (ord(character) - ord("A") + 1)
        return total

    def _column_letters(self, number: int) -> str:
        result: list[str] = []
        current = number
        while current > 0:
            current, remainder = divmod(current - 1, 26)
            result.append(chr(ord("A") + remainder))
        return "".join(reversed(result))
