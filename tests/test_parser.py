"""Tests for the deterministic parser skeleton."""

import unittest

from voice_control_usb.core.models import CommandName
from voice_control_usb.core.parser import CommandParser


class CommandParserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = CommandParser()

    def test_parse_open_excel(self) -> None:
        result = self.parser.parse("open excel")

        self.assertTrue(result.is_supported)
        self.assertIsNotNone(result.command)
        assert result.command is not None
        self.assertIs(result.command.name, CommandName.OPEN_EXCEL)

    def test_parse_read_cell_normalizes_reference(self) -> None:
        result = self.parser.parse("read cell b12")

        self.assertIsNotNone(result.command)
        assert result.command is not None
        self.assertIs(result.command.name, CommandName.READ_CELL)
        self.assertEqual(result.command.arguments["cell"], "B12")

    def test_parse_write_cell_extracts_value(self) -> None:
        result = self.parser.parse("write cell c3 value quarterly total")

        self.assertIsNotNone(result.command)
        assert result.command is not None
        self.assertIs(result.command.name, CommandName.WRITE_CELL)
        self.assertEqual(
            result.command.arguments,
            {"cell": "C3", "value": "quarterly total"},
        )

    def test_parse_unknown_command_becomes_proposal(self) -> None:
        result = self.parser.parse("email the spreadsheet to finance")

        self.assertIsNone(result.command)
        self.assertIsNotNone(result.proposal)
        assert result.proposal is not None
        self.assertIn("deterministic MVP command set", result.proposal.reason)

    def test_parse_invalid_cell_becomes_proposal(self) -> None:
        result = self.parser.parse("read cell 12B")

        self.assertIsNone(result.command)
        self.assertIsNotNone(result.proposal)
        assert result.proposal is not None
        self.assertIn("Cell reference", result.proposal.reason)


if __name__ == "__main__":
    unittest.main()
