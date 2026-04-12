"""Smoke tests for the execution skeleton."""

import unittest

from voice_control_usb.core.models import Command, CommandName
from voice_control_usb.excel.adapter import StubExcelAdapter
from voice_control_usb.executor.engine import ExecutionEngine


class ExecutionEngineTests(unittest.TestCase):
    def test_executor_routes_write_then_read(self) -> None:
        engine = ExecutionEngine(excel=StubExcelAdapter())
        write = Command(
            name=CommandName.WRITE_CELL,
            arguments={"cell": "A1", "value": "hello"},
            source_text="write cell A1 value hello",
        )
        read = Command(
            name=CommandName.READ_CELL,
            arguments={"cell": "A1"},
            source_text="read cell A1",
        )

        self.assertIn("Wrote", engine.execute(write))
        self.assertEqual(engine.execute(read), "hello")


if __name__ == "__main__":
    unittest.main()
