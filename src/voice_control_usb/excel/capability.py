"""Action contracts declared by the Excel capability."""

from __future__ import annotations

from voice_control_usb.core.capabilities import ActionBinding, ActionSpec
from voice_control_usb.core.models import Command
from voice_control_usb.excel.adapter import ExcelAdapter


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
            action_id="go_to_cell",
            description="Move to a cell.",
            argument_types={"cell": str},
        ),
        ActionSpec(
            capability_id="excel",
            action_id="type_text",
            description="Enter text in the active cell.",
            reversible=True,
            argument_types={"value": str},
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
            "go_to_cell": self._go_to_cell,
            "type_text": self._type_text,
            "go_right": self._go_right,
            "go_down": self._go_down,
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

    def _go_to_cell(self, command: Command) -> str:
        return self.adapter.go_to_cell(self._string_argument(command, "cell"))

    def _type_text(self, command: Command) -> str:
        return self.adapter.type_text(self._string_argument(command, "value"))

    def _go_right(self, command: Command) -> str:
        return self.adapter.go_right()

    def _go_down(self, command: Command) -> str:
        return self.adapter.go_down()

    def _next_row_from_start(self, command: Command) -> str:
        return self.adapter.next_row_from_start()

    @staticmethod
    def _string_argument(command: Command, name: str) -> str:
        value = command.arguments.get(name)
        if not isinstance(value, str):
            raise ValueError(f"Action '{command.action}' argument '{name}' must be str.")
        return value
