"""Deterministic command executor."""

from __future__ import annotations

from collections.abc import Callable

from voice_control_usb.core.models import Command
from voice_control_usb.excel.adapter import ExcelAdapter


class ExecutionEngine:
    """Route parsed commands to approved execution handlers."""

    def __init__(self, excel: ExcelAdapter) -> None:
        self.excel = excel
        self.handlers: dict[str, Callable[[Command], str]] = {
            "open_excel": self._handle_open_excel,
            "open_workbook": self._handle_open_workbook,
            "select_sheet": self._handle_select_sheet,
            "save_workbook": self._handle_save_workbook,
            "report_current_sheet": self._handle_report_current_sheet,
            "go_to_cell": self._handle_go_to_cell,
            "type_text": self._handle_type_text,
            "go_right": self._handle_go_right,
            "go_down": self._handle_go_down,
            "next_row_from_start": self._handle_next_row_from_start,
        }

    def execute(self, command: Command) -> str:
        try:
            handler = self.handlers[command.action]
        except KeyError as error:
            raise ValueError(f"Unsupported command routed to executor: {command.action}") from error
        return handler(command)

    def _handle_open_excel(self, command: Command) -> str:
        return self.excel.open_excel()

    def _handle_open_workbook(self, command: Command) -> str:
        return self.excel.open_workbook(command.arguments["path"])

    def _handle_select_sheet(self, command: Command) -> str:
        return self.excel.select_sheet(command.arguments["sheet_name"])

    def _handle_save_workbook(self, command: Command) -> str:
        return self.excel.save_workbook()

    def _handle_report_current_sheet(self, command: Command) -> str:
        return self.excel.report_current_sheet()

    def _handle_go_to_cell(self, command: Command) -> str:
        return self.excel.go_to_cell(command.arguments["cell"])

    def _handle_type_text(self, command: Command) -> str:
        return self.excel.type_text(command.arguments["value"])

    def _handle_go_right(self, command: Command) -> str:
        return self.excel.go_right()

    def _handle_go_down(self, command: Command) -> str:
        return self.excel.go_down()

    def _handle_next_row_from_start(self, command: Command) -> str:
        return self.excel.next_row_from_start()
