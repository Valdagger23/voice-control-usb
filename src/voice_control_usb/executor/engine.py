"""Deterministic command executor."""

from __future__ import annotations

from collections.abc import Callable

from voice_control_usb.core.models import Command
from voice_control_usb.core.workflows import WorkflowRegistry
from voice_control_usb.desktop.adapter import DesktopAdapter
from voice_control_usb.excel.adapter import ExcelAdapter


class ExecutionEngine:
    """Route parsed commands to approved execution handlers."""

    def __init__(
        self,
        excel: ExcelAdapter,
        desktop: DesktopAdapter,
        workflow_registry: WorkflowRegistry | None = None,
    ) -> None:
        self.excel = excel
        self.desktop = desktop
        self.handlers: dict[str, Callable[[Command], str]] = {
            "run_workflow": self._handle_run_workflow,
            "open_excel": self._handle_open_excel,
            "open_app": self._handle_open_app,
            "open_url": self._handle_open_url,
            "open_folder": self._handle_open_folder,
            "shutdown": self._handle_shutdown,
            "restart": self._handle_restart,
            "blocked_desktop_action": self._handle_blocked_desktop_action,
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
        self.workflow_registry = workflow_registry or WorkflowRegistry.load_default()
        self.workflow_registry.validate(self._workflow_allowed_actions())

    def execute(self, command: Command) -> str:
        try:
            handler = self.handlers[command.action]
        except KeyError as error:
            raise ValueError(f"Unsupported command routed to executor: {command.action}") from error
        return handler(command)

    def _handle_open_excel(self, command: Command) -> str:
        return self.excel.open_excel()

    def _handle_run_workflow(self, command: Command) -> str:
        workflow_name = command.arguments["workflow_name"]
        workflow = self.workflow_registry.get(workflow_name)
        if workflow is None:
            raise ValueError(f"Unknown workflow requested: {workflow_name}")

        last_result = ""
        for index, step in enumerate(workflow.steps, start=1):
            step_command = Command(
                name=f"{workflow.name}_step_{index}",
                action=step.action,
                arguments=step.arguments,
                source_text=command.source_text,
            )
            last_result = self.handlers[step.action](step_command)

        return f"Workflow '{workflow.name}' completed. Final result: {last_result}"

    def _handle_open_app(self, command: Command) -> str:
        return self.desktop.open_app(command.arguments["app_alias"])

    def _handle_open_url(self, command: Command) -> str:
        return self.desktop.open_url(command.arguments["url"])

    def _handle_open_folder(self, command: Command) -> str:
        return self.desktop.open_folder(command.arguments["path"])

    def _handle_shutdown(self, command: Command) -> str:
        return self.desktop.shutdown()

    def _handle_restart(self, command: Command) -> str:
        return self.desktop.restart()

    def _handle_blocked_desktop_action(self, command: Command) -> str:
        request = command.arguments["request"]
        return f"Desktop action is blocked in MVP: {request}"

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

    def _workflow_allowed_actions(self) -> set[str]:
        return {action for action in self.handlers if action != "run_workflow"}
