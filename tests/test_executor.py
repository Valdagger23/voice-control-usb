"""Smoke tests for the execution skeleton."""

import unittest

from voice_control_usb.core.models import Command
from voice_control_usb.desktop.adapter import StubDesktopAdapter
from voice_control_usb.desktop.registry import AppAliasRegistry
from voice_control_usb.excel.adapter import StubExcelAdapter
from voice_control_usb.executor.engine import ExecutionEngine


class ExecutionEngineTests(unittest.TestCase):
    def make_engine(self) -> ExecutionEngine:
        return ExecutionEngine(
            excel=StubExcelAdapter(),
            desktop=StubDesktopAdapter(aliases=AppAliasRegistry.load_default()),
        )

    def test_executor_routes_workbook_and_sheet_context_commands(self) -> None:
        excel = StubExcelAdapter()
        engine = ExecutionEngine(
            excel=excel,
            desktop=StubDesktopAdapter(aliases=AppAliasRegistry.load_default()),
        )

        outputs = [
            engine.execute(
                Command(
                    name="open_workbook",
                    action="open_workbook",
                    arguments={"path": "/tmp/audit.xlsx"},
                    source_text="open workbook /tmp/audit.xlsx",
                )
            ),
            engine.execute(
                Command(
                    name="select_sheet",
                    action="select_sheet",
                    arguments={"sheet_name": "Sheet2"},
                    source_text="select sheet Sheet2",
                )
            ),
            engine.execute(
                Command(
                    name="report_current_sheet",
                    action="report_current_sheet",
                    arguments={},
                    source_text="report current sheet",
                )
            ),
            engine.execute(
                Command(
                    name="save_workbook",
                    action="save_workbook",
                    arguments={},
                    source_text="save workbook",
                )
            ),
        ]

        self.assertEqual(outputs[0], "Opened workbook: audit.xlsx")
        self.assertEqual(outputs[1], "Selected sheet: Sheet2")
        self.assertEqual(outputs[2], "Current sheet: Sheet2 (workbook: audit.xlsx)")
        self.assertEqual(outputs[3], "Saved workbook: audit.xlsx")
        self.assertEqual(excel.current_context().sheet_name, "Sheet2")
        self.assertEqual(excel.current_context().workbook_name, "audit.xlsx")

    def test_executor_routes_navigation_and_data_entry_workflow(self) -> None:
        engine = self.make_engine()
        commands = [
            Command(
                name="open_excel",
                action="open_excel",
                arguments={},
                source_text="open excel",
            ),
            Command(
                name="go_to_cell",
                action="go_to_cell",
                arguments={"cell": "A123"},
                source_text="go to A123",
            ),
            Command(
                name="type_pass",
                action="type_text",
                arguments={"value": "pass"},
                source_text="type pass",
            ),
            Command(
                name="go_right",
                action="go_right",
                arguments={},
                source_text="go right",
            ),
            Command(
                name="type_fail",
                action="type_text",
                arguments={"value": "fail"},
                source_text="type fail",
            ),
            Command(
                name="next_row_from_start",
                action="next_row_from_start",
                arguments={},
                source_text="next row from start",
            ),
        ]

        outputs = [engine.execute(command) for command in commands]

        self.assertEqual(outputs[0], "Excel session ready (stub)")
        self.assertEqual(outputs[1], "Moved to A123")
        self.assertEqual(outputs[2], "Typed 'pass' into A123")
        self.assertEqual(outputs[3], "Moved right to B123")
        self.assertEqual(outputs[4], "Typed 'fail' into B123")
        self.assertEqual(outputs[5], "Moved to next row start at A124")
        self.assertEqual(engine.excel.cells["A123"], "pass")
        self.assertEqual(engine.excel.cells["B123"], "fail")

    def test_executor_routes_go_down(self) -> None:
        excel = StubExcelAdapter()
        engine = ExecutionEngine(
            excel=excel,
            desktop=StubDesktopAdapter(aliases=AppAliasRegistry.load_default()),
        )
        engine.execute(
            Command(
                name="go_to_cell",
                action="go_to_cell",
                arguments={"cell": "C7"},
                source_text="go to C7",
            )
        )

        result = engine.execute(
            Command(
                name="go_down",
                action="go_down",
                arguments={},
                source_text="go down",
            )
        )

        self.assertEqual(result, "Moved down to C8")

    def test_sheet_selection_preserves_per_sheet_navigation_context(self) -> None:
        excel = StubExcelAdapter()
        engine = ExecutionEngine(
            excel=excel,
            desktop=StubDesktopAdapter(aliases=AppAliasRegistry.load_default()),
        )

        engine.execute(
            Command(
                name="open_workbook",
                action="open_workbook",
                arguments={"path": "/tmp/context.xlsx"},
                source_text="open workbook /tmp/context.xlsx",
            )
        )
        engine.execute(
            Command(
                name="go_to_cell",
                action="go_to_cell",
                arguments={"cell": "B2"},
                source_text="go to B2",
            )
        )
        engine.execute(
            Command(
                name="select_sheet",
                action="select_sheet",
                arguments={"sheet_name": "Sheet2"},
                source_text="select sheet Sheet2",
            )
        )
        engine.execute(
            Command(
                name="go_to_cell",
                action="go_to_cell",
                arguments={"cell": "D5"},
                source_text="go to D5",
            )
        )
        engine.execute(
            Command(
                name="select_sheet",
                action="select_sheet",
                arguments={"sheet_name": "Sheet1"},
                source_text="select sheet Sheet1",
            )
        )

        result = engine.execute(
            Command(
                name="next_row_from_start",
                action="next_row_from_start",
                arguments={},
                source_text="next row from start",
            )
        )

        self.assertEqual(result, "Moved to next row start at B3")

    def test_executor_routes_desktop_actions_through_stub_adapter(self) -> None:
        engine = self.make_engine()

        outputs = [
            engine.execute(
                Command(
                    name="open_app",
                    action="open_app",
                    arguments={"app_alias": "notepad"},
                    source_text="open app notepad",
                )
            ),
            engine.execute(
                Command(
                    name="open_url",
                    action="open_url",
                    arguments={"url": "https://example.com"},
                    source_text="open url https://example.com",
                )
            ),
            engine.execute(
                Command(
                    name="open_folder",
                    action="open_folder",
                    arguments={"path": "/tmp"},
                    source_text="open folder /tmp",
                )
            ),
        ]

        self.assertEqual(outputs[0], "Opened app alias: notepad (stub)")
        self.assertEqual(outputs[1], "Opened URL: https://example.com (stub)")
        self.assertEqual(outputs[2], "Opened folder: /tmp (stub)")

    def test_executor_rejects_risky_desktop_actions_explicitly(self) -> None:
        engine = self.make_engine()

        result = engine.execute(
            Command(
                name="reject_shutdown",
                action="reject_desktop_action",
                arguments={"request": "shutdown"},
                source_text="shutdown",
            )
        )

        self.assertEqual(result, "Desktop action is not approved in MVP: shutdown")


if __name__ == "__main__":
    unittest.main()
