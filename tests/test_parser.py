"""Tests for the registry-driven deterministic parser."""

import unittest

from voice_control_usb.core.parser import CommandParser


class CommandParserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = CommandParser()

    def test_parse_open_excel(self) -> None:
        result = self.parser.parse("open excel")

        self.assertTrue(result.is_supported)
        self.assertIsNotNone(result.command)
        assert result.command is not None
        self.assertEqual(result.command.name, "open_excel")
        self.assertEqual(result.command.action, "open_excel")

    def test_parse_go_to_cell_normalizes_reference(self) -> None:
        result = self.parser.parse("go to a123")

        self.assertIsNotNone(result.command)
        assert result.command is not None
        self.assertEqual(result.command.name, "go_to_cell")
        self.assertEqual(result.command.action, "go_to_cell")
        self.assertEqual(result.command.arguments["cell"], "A123")

    def test_parse_type_pass_from_registry(self) -> None:
        result = self.parser.parse("type pass")

        self.assertIsNotNone(result.command)
        assert result.command is not None
        self.assertEqual(result.command.name, "type_pass")
        self.assertEqual(result.command.action, "type_text")
        self.assertEqual(result.command.arguments, {"value": "pass"})

    def test_parse_type_fail_from_registry(self) -> None:
        result = self.parser.parse("type fail")

        self.assertIsNotNone(result.command)
        assert result.command is not None
        self.assertEqual(result.command.name, "type_fail")
        self.assertEqual(result.command.action, "type_text")
        self.assertEqual(result.command.arguments, {"value": "fail"})

    def test_parse_navigation_commands_from_registry(self) -> None:
        for raw_text, expected_name in (
            ("go right", "go_right"),
            ("go down", "go_down"),
            ("next row from start", "next_row_from_start"),
        ):
            with self.subTest(raw_text=raw_text):
                result = self.parser.parse(raw_text)

                self.assertIsNotNone(result.command)
                assert result.command is not None
                self.assertEqual(result.command.name, expected_name)
                self.assertEqual(result.command.action, expected_name)

    def test_parse_unknown_command_becomes_proposal(self) -> None:
        result = self.parser.parse("email the spreadsheet to finance")

        self.assertIsNone(result.command)
        self.assertIsNotNone(result.proposal)
        assert result.proposal is not None
        self.assertIn("deterministic command registry", result.proposal.reason)

    def test_parse_invalid_cell_becomes_proposal(self) -> None:
        result = self.parser.parse("go to 12B")

        self.assertIsNone(result.command)
        self.assertIsNotNone(result.proposal)
        assert result.proposal is not None
        self.assertIn("deterministic command registry", result.proposal.reason)


if __name__ == "__main__":
    unittest.main()
