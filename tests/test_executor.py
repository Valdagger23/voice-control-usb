"""Smoke tests for the execution skeleton."""

import unittest

from voice_control_usb.core.models import Command
from voice_control_usb.excel.adapter import StubExcelAdapter
from voice_control_usb.executor.engine import ExecutionEngine


class ExecutionEngineTests(unittest.TestCase):
    def test_executor_routes_navigation_and_data_entry_workflow(self) -> None:
        engine = ExecutionEngine(excel=StubExcelAdapter())
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
        engine = ExecutionEngine(excel=excel)
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


if __name__ == "__main__":
    unittest.main()
