"""Excel adapter interface and MVP stub implementation."""

from __future__ import annotations

from dataclasses import dataclass, field


class ExcelAdapter:
    """Object-level Excel operations only."""

    def open_excel(self) -> str:
        raise NotImplementedError

    def read_cell(self, cell: str) -> str:
        raise NotImplementedError

    def write_cell(self, cell: str, value: str) -> str:
        raise NotImplementedError


@dataclass
class StubExcelAdapter(ExcelAdapter):
    """Safe test stub until Windows COM integration is added."""

    cells: dict[str, str] = field(default_factory=dict)
    opened: bool = False

    def open_excel(self) -> str:
        self.opened = True
        return "Excel session ready (stub)"

    def read_cell(self, cell: str) -> str:
        return self.cells.get(cell, "")

    def write_cell(self, cell: str, value: str) -> str:
        self.cells[cell] = value
        return f"Wrote '{value}' to {cell}"
