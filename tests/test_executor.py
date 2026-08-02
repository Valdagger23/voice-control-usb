"""Smoke tests for the execution skeleton."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from voice_control_usb.core.models import Command
from voice_control_usb.core.workflows import WorkflowRegistry
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

    def test_executor_supports_four_way_navigation_with_sheet_boundaries(self) -> None:
        excel = StubExcelAdapter()
        engine = ExecutionEngine(
            excel=excel,
            desktop=StubDesktopAdapter(aliases=AppAliasRegistry.load_default()),
        )
        engine.execute(
            Command("go_to_cell", "go_to_cell", {"cell": "B2"}, "go to B2")
        )

        self.assertEqual(
            engine.execute(Command("go_left", "go_left", {}, "go left")),
            "Moved left to A2",
        )
        self.assertEqual(
            engine.execute(Command("go_up", "go_up", {}, "go up")),
            "Moved up to A1",
        )
        with self.assertRaisesRegex(ValueError, "column A"):
            engine.execute(Command("go_left", "go_left", {}, "go left"))
        with self.assertRaisesRegex(ValueError, "row 1"):
            engine.execute(Command("go_up", "go_up", {}, "go up"))

        engine.execute(
            Command("go_to_cell", "go_to_cell", {"cell": "XFD1"}, "go to XFD1")
        )
        with self.assertRaisesRegex(ValueError, "column XFD"):
            engine.execute(Command("go_right", "go_right", {}, "go right"))

        engine.execute(
            Command(
                "go_to_cell",
                "go_to_cell",
                {"cell": "A1048576"},
                "go to A1048576",
            )
        )
        with self.assertRaisesRegex(ValueError, "row 1048576"):
            engine.execute(Command("go_down", "go_down", {}, "go down"))

    def test_executor_enters_reports_and_undoes_typed_and_numeric_values(self) -> None:
        excel = StubExcelAdapter()
        engine = ExecutionEngine(
            excel=excel,
            desktop=StubDesktopAdapter(aliases=AppAliasRegistry.load_default()),
        )
        engine.execute(Command("go_to_cell", "go_to_cell", {"cell": "C4"}, "go to C4"))
        first = engine.execute(
            Command("enter_value", "type_text", {"value": 42}, "enter 42")
        )
        report = engine.execute(
            Command("report_current_cell", "report_current_cell", {}, "report current cell")
        )
        engine.execute(
            Command("enter_value", "type_text", {"value": "N/A"}, "enter N/A")
        )
        undone = engine.execute(
            Command(
                "undo_last_excel_change",
                "undo_last_excel_change",
                {},
                "undo last change",
            )
        )

        self.assertEqual(first, "Typed 42 into C4")
        self.assertEqual(report, "Current cell: C4 (value: 42)")
        self.assertEqual(undone, "Undid last Excel change in Sheet1!C4.")
        self.assertEqual(excel.cells["C4"], 42)
        self.assertEqual(
            engine.execute(
                Command(
                    "undo_last_excel_change",
                    "undo_last_excel_change",
                    {},
                    "undo last change",
                )
            ),
            "No assistant-made Excel change to undo.",
        )

    def test_undo_restores_an_empty_cell_after_moving_to_another_sheet(self) -> None:
        excel = StubExcelAdapter()
        engine = ExecutionEngine(
            excel=excel,
            desktop=StubDesktopAdapter(aliases=AppAliasRegistry.load_default()),
        )
        engine.execute(Command("go_to_cell", "go_to_cell", {"cell": "A1"}, "go to A1"))
        engine.execute(Command("enter_value", "type_text", {"value": "check"}, "enter check"))
        engine.execute(
            Command(
                "select_sheet",
                "select_sheet",
                {"sheet_name": "Sheet2"},
                "select sheet Sheet2",
            )
        )

        result = engine.execute(
            Command(
                "undo_last_excel_change",
                "undo_last_excel_change",
                {},
                "undo last change",
            )
        )

        self.assertEqual(result, "Undid last Excel change in Sheet1!A1.")
        engine.execute(
            Command(
                "select_sheet",
                "select_sheet",
                {"sheet_name": "Sheet1"},
                "select sheet Sheet1",
            )
        )
        self.assertNotIn("A1", excel.cells)

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

        with TemporaryDirectory() as folder_path:
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
                        arguments={"path": folder_path},
                        source_text=f"open folder {folder_path}",
                    )
                ),
            ]

        self.assertEqual(outputs[0], "Opened app alias: notepad (stub)")
        self.assertEqual(outputs[1], "Opened URL: https://example.com (stub)")
        self.assertEqual(outputs[2], f"Opened folder: {Path(folder_path)} (stub)")

    def test_executor_routes_confirm_required_desktop_actions_after_approval(self) -> None:
        engine = self.make_engine()

        shutdown_result = engine.execute(
            Command(
                name="shutdown",
                action="shutdown",
                arguments={},
                source_text="shutdown",
            )
        )
        restart_result = engine.execute(
            Command(
                name="restart",
                action="restart",
                arguments={},
                source_text="restart",
            )
        )

        self.assertEqual(shutdown_result, "Shutdown requested (stub)")
        self.assertEqual(restart_result, "Restart requested (stub)")

    def test_executor_keeps_blocked_desktop_actions_blocked(self) -> None:
        engine = self.make_engine()

        result = engine.execute(
            Command(
                name="blocked_run_command",
                action="blocked_desktop_action",
                arguments={"request": "dir"},
                source_text="run command dir",
            )
        )

        self.assertEqual(result, "Desktop action is blocked in MVP: dir")

    def test_executor_runs_workflow_in_order_against_excel_context(self) -> None:
        excel = StubExcelAdapter()
        engine = ExecutionEngine(
            excel=excel,
            desktop=StubDesktopAdapter(aliases=AppAliasRegistry.load_default()),
        )
        engine.execute(
            Command(
                name="go_to_cell",
                action="go_to_cell",
                arguments={"cell": "A10"},
                source_text="go to A10",
            )
        )

        result = engine.execute(
            Command(
                name="workflow_mark_pass_and_next_row",
                action="run_workflow",
                arguments={"workflow_name": "mark_pass_and_next_row"},
                source_text="mark pass and next row",
            )
        )

        self.assertEqual(
            result,
            "Workflow 'mark_pass_and_next_row' completed. Final result: Moved to next row start at A11",
        )
        self.assertEqual(excel.cells["A10"], "pass")
        self.assertEqual(excel.current_cell, "A11")

    def test_executor_runs_open_excel_and_go_to_a1_workflow(self) -> None:
        engine = self.make_engine()

        result = engine.execute(
            Command(
                name="workflow_open_excel_and_go_to_a1",
                action="run_workflow",
                arguments={"workflow_name": "open_excel_and_go_to_a1"},
                source_text="open excel and go to a1",
            )
        )

        self.assertEqual(
            result,
            "Workflow 'open_excel_and_go_to_a1' completed. Final result: Moved to A1",
        )

    def test_invalid_workflow_definition_is_rejected(self) -> None:
        registry = WorkflowRegistry.from_data(
            {
                "workflows": [
                    {
                        "name": "bad_workflow",
                        "description": "Invalid workflow",
                        "steps": [
                            {
                                "action": "run_workflow",
                                "arguments": {"workflow_name": "nested"},
                            }
                        ],
                    }
                ]
            }
        )

        with self.assertRaisesRegex(ValueError, "may not reference nested workflows"):
            ExecutionEngine(
                excel=StubExcelAdapter(),
                desktop=StubDesktopAdapter(aliases=AppAliasRegistry.load_default()),
                workflow_registry=registry,
            )


if __name__ == "__main__":
    unittest.main()
