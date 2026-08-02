"""Action contracts declared by the Excel capability."""

from __future__ import annotations

from voice_control_usb.core.capabilities import ActionBinding, ActionSpec, SafetyClass
from voice_control_usb.core.models import Command
from voice_control_usb.excel.adapter import ExcelAdapter, ExcelValue


def excel_action_specs() -> list[ActionSpec]:
    specs = [
        ActionSpec(
            capability_id="excel",
            action_id="open_excel",
            description="Open or attach to Excel.",
        ),
        ActionSpec(
            capability_id="excel",
            action_id="open_workbook",
            description="Open a workbook from a path.",
            argument_types={"path": str},
        ),
        ActionSpec(
            capability_id="excel",
            action_id="select_sheet",
            description="Select a worksheet.",
            argument_types={"sheet_name": str},
        ),
        ActionSpec(
            capability_id="excel",
            action_id="save_workbook",
            description="Save the active workbook.",
        ),
        ActionSpec(
            capability_id="excel",
            action_id="report_current_sheet",
            description="Report the active worksheet.",
        ),
        ActionSpec(
            capability_id="excel",
            action_id="report_current_cell",
            description="Report the active cell and its value.",
        ),
        ActionSpec(
            capability_id="excel",
            action_id="go_to_cell",
            description="Move to a cell.",
            argument_types={"cell": str},
        ),
        ActionSpec(
            capability_id="excel",
            action_id="type_text",
            description="Enter text or a number in the active cell.",
            reversible=True,
            argument_types={"value": (str, int, float)},
        ),
        ActionSpec(
            capability_id="excel",
            action_id="undo_last_excel_change",
            description="Restore the value before the last assistant-made cell edit.",
            reversible=True,
        ),
        ActionSpec(
            capability_id="excel",
            action_id="go_left",
            description="Move one cell left.",
        ),
        ActionSpec(
            capability_id="excel",
            action_id="go_right",
            description="Move one cell right.",
        ),
        ActionSpec(
            capability_id="excel",
            action_id="go_down",
            description="Move one cell down.",
        ),
        ActionSpec(
            capability_id="excel",
            action_id="go_up",
            description="Move one cell up.",
        ),
        ActionSpec(
            capability_id="excel",
            action_id="next_row_from_start",
            description="Move to the next row's anchored start column.",
        ),
    ]
    specs.extend(
        [
            ActionSpec("excel", "create_workbook", "Create a new workbook."),
            ActionSpec("excel", "create_sheet", "Create a worksheet.", argument_types={"sheet_name": str}),
            ActionSpec("excel", "rename_sheet", "Rename the active worksheet.", reversible=True, argument_types={"sheet_name": str}),
            ActionSpec("excel", "delete_sheet", "Delete the active worksheet.", safety_class=SafetyClass.REQUIRES_CONFIRMATION),
            ActionSpec("excel", "select_range", "Select a cell range.", argument_types={"range": str}),
            ActionSpec("excel", "read_range", "Read a cell range.", argument_types={"range": str}),
            ActionSpec("excel", "clear_cell", "Clear the active cell.", reversible=True),
            ActionSpec("excel", "clear_range", "Clear a cell range.", reversible=True, argument_types={"range": str}),
            ActionSpec("excel", "copy_cell", "Copy the active cell."),
            ActionSpec("excel", "copy_range", "Copy a cell range.", argument_types={"range": str}),
            ActionSpec("excel", "paste_cells", "Paste copied cells.", reversible=True),
            ActionSpec("excel", "fill_down", "Fill the selection down.", reversible=True),
            ActionSpec("excel", "find_excel_value", "Find a worksheet value.", argument_types={"query": str}),
            ActionSpec("excel", "replace_excel_value", "Replace worksheet values.", safety_class=SafetyClass.REQUIRES_CONFIRMATION, reversible=True, argument_types={"old": str, "new": str}),
            ActionSpec("excel", "enter_formula", "Enter a formula.", reversible=True, argument_types={"formula": str}),
            ActionSpec("excel", "format_currency", "Format the selection as currency.", reversible=True),
            ActionSpec("excel", "format_bold", "Make the selection bold.", reversible=True),
            ActionSpec("excel", "sort_by_column", "Sort by a worksheet column.", safety_class=SafetyClass.REQUIRES_CONFIRMATION, reversible=True, argument_types={"column": str}),
            ActionSpec("excel", "filter_column", "Filter a worksheet column.", reversible=True, argument_types={"column": str, "value": (str, int, float)}),
            ActionSpec("excel", "insert_row", "Insert a worksheet row.", reversible=True, argument_types={"position": str}),
            ActionSpec("excel", "close_workbook", "Close the active workbook without saving.", safety_class=SafetyClass.REQUIRES_CONFIRMATION),
        ]
    )
    return specs


class ExcelCapability:
    """Expose object-level Excel adapter operations as capability bindings."""

    capability_id = "excel"

    def __init__(self, adapter: ExcelAdapter) -> None:
        self.adapter = adapter

    def bindings(self) -> list[ActionBinding]:
        handlers = {
            "open_excel": self._open_excel,
            "open_workbook": self._open_workbook,
            "select_sheet": self._select_sheet,
            "save_workbook": self._save_workbook,
            "report_current_sheet": self._report_current_sheet,
            "report_current_cell": self._report_current_cell,
            "go_to_cell": self._go_to_cell,
            "type_text": self._type_text,
            "undo_last_excel_change": self._undo_last_excel_change,
            "go_left": self._go_left,
            "go_right": self._go_right,
            "go_down": self._go_down,
            "go_up": self._go_up,
            "next_row_from_start": self._next_row_from_start,
            "create_workbook": lambda c: self.adapter.create_workbook(),
            "create_sheet": lambda c: self.adapter.create_sheet(self._string_argument(c, "sheet_name")),
            "rename_sheet": lambda c: self.adapter.rename_sheet(self._string_argument(c, "sheet_name")),
            "delete_sheet": lambda c: self.adapter.delete_sheet(),
            "select_range": lambda c: self.adapter.select_range(self._string_argument(c, "range")),
            "read_range": lambda c: self.adapter.read_range(self._string_argument(c, "range")),
            "clear_cell": lambda c: self.adapter.clear_cell(),
            "clear_range": lambda c: self.adapter.clear_range(self._string_argument(c, "range")),
            "copy_cell": lambda c: self.adapter.copy_cell(),
            "copy_range": lambda c: self.adapter.copy_range(self._string_argument(c, "range")),
            "paste_cells": lambda c: self.adapter.paste_cells(),
            "fill_down": lambda c: self.adapter.fill_down(),
            "find_excel_value": lambda c: self.adapter.find_value(self._string_argument(c, "query")),
            "replace_excel_value": lambda c: self.adapter.replace_value(self._string_argument(c, "old"), self._string_argument(c, "new")),
            "enter_formula": lambda c: self.adapter.enter_formula(self._string_argument(c, "formula")),
            "format_currency": lambda c: self.adapter.format_currency(),
            "format_bold": lambda c: self.adapter.format_bold(),
            "sort_by_column": lambda c: self.adapter.sort_by_column(self._string_argument(c, "column")),
            "filter_column": lambda c: self.adapter.filter_column(self._string_argument(c, "column"), self._excel_value_argument(c, "value")),
            "insert_row": lambda c: self.adapter.insert_row(self._string_argument(c, "position")),
            "close_workbook": lambda c: self.adapter.close_workbook(),
        }
        return [ActionBinding(spec, handlers[spec.action_id]) for spec in excel_action_specs()]

    def _open_excel(self, command: Command) -> str:
        return self.adapter.open_excel()

    def _open_workbook(self, command: Command) -> str:
        return self.adapter.open_workbook(self._string_argument(command, "path"))

    def _select_sheet(self, command: Command) -> str:
        return self.adapter.select_sheet(self._string_argument(command, "sheet_name"))

    def _save_workbook(self, command: Command) -> str:
        return self.adapter.save_workbook()

    def _report_current_sheet(self, command: Command) -> str:
        return self.adapter.report_current_sheet()

    def _report_current_cell(self, command: Command) -> str:
        return self.adapter.report_current_cell()

    def _go_to_cell(self, command: Command) -> str:
        return self.adapter.go_to_cell(self._string_argument(command, "cell"))

    def _type_text(self, command: Command) -> str:
        return self.adapter.type_text(self._excel_value_argument(command, "value"))

    def _undo_last_excel_change(self, command: Command) -> str:
        return self.adapter.undo_last_change()

    def _go_left(self, command: Command) -> str:
        return self.adapter.go_left()

    def _go_right(self, command: Command) -> str:
        return self.adapter.go_right()

    def _go_down(self, command: Command) -> str:
        return self.adapter.go_down()

    def _go_up(self, command: Command) -> str:
        return self.adapter.go_up()

    def _next_row_from_start(self, command: Command) -> str:
        return self.adapter.next_row_from_start()

    @staticmethod
    def _string_argument(command: Command, name: str) -> str:
        value = command.arguments.get(name)
        if not isinstance(value, str):
            raise ValueError(f"Action '{command.action}' argument '{name}' must be str.")
        return value

    @staticmethod
    def _excel_value_argument(command: Command, name: str) -> ExcelValue:
        value = command.arguments.get(name)
        if isinstance(value, bool) or not isinstance(value, (str, int, float)):
            raise ValueError(
                f"Action '{command.action}' argument '{name}' must be str, int, or float."
            )
        return value
