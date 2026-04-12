"""Excel adapter interface and MVP stub implementation."""

from __future__ import annotations

from dataclasses import dataclass, field


class ExcelAdapter:
    """Object-level Excel operations only."""

    def open_excel(self) -> str:
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

    cells: dict[str, str] = field(default_factory=dict)
    opened: bool = False
    current_row: int = 1
    current_column: int = 1
    start_column: int | None = None

    def open_excel(self) -> str:
        self.opened = True
        return "Excel session ready (stub)"

    def go_to_cell(self, cell: str) -> str:
        row, column = self._parse_cell_reference(cell)
        self.current_row = row
        self.current_column = column
        self.start_column = column
        return f"Moved to {self.current_cell}"

    def type_text(self, value: str) -> str:
        self.cells[self.current_cell] = value
        return f"Typed '{value}' into {self.current_cell}"

    def go_right(self) -> str:
        self.current_column += 1
        return f"Moved right to {self.current_cell}"

    def go_down(self) -> str:
        self.current_row += 1
        return f"Moved down to {self.current_cell}"

    def next_row_from_start(self) -> str:
        if self.start_column is None:
            raise ValueError("No starting column is set. Use 'go to <CELL>' first.")
        self.current_row += 1
        self.current_column = self.start_column
        return f"Moved to next row start at {self.current_cell}"

    @property
    def current_cell(self) -> str:
        return f"{self._column_letters(self.current_column)}{self.current_row}"

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
