"""Action contracts declared by the Excel capability."""

from __future__ import annotations

from voice_control_usb.core.capabilities import ActionBinding, ActionSpec
from voice_control_usb.core.models import Command
from voice_control_usb.excel.adapter import ExcelAdapter, ExcelValue


def excel_action_specs() -> list[ActionSpec]:
    return [
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
