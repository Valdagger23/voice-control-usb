"""Deterministic command executor."""

from __future__ import annotations

from voice_control_usb.core.models import Command, CommandName
from voice_control_usb.excel.adapter import ExcelAdapter


class ExecutionEngine:
    """Route parsed commands to approved execution handlers."""

    def __init__(self, excel: ExcelAdapter) -> None:
        self.excel = excel

    def execute(self, command: Command) -> str:
        if command.name is CommandName.OPEN_EXCEL:
            return self.excel.open_excel()
        if command.name is CommandName.READ_CELL:
            return self.excel.read_cell(command.arguments["cell"])
        if command.name is CommandName.WRITE_CELL:
            return self.excel.write_cell(
                command.arguments["cell"],
                command.arguments["value"],
            )

        raise ValueError(f"Unsupported command routed to executor: {command.name}")
