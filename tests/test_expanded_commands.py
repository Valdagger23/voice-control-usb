"""Coverage for the expanded command catalogue and capability adapters."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from voice_control_usb.assistant.app import AssistantApp
from voice_control_usb.assistant.command_legend import COMMAND_SECTIONS
from voice_control_usb.browser.adapter import StubBrowserAdapter
from voice_control_usb.core.parser import CommandParser
from voice_control_usb.desktop.adapter import StubDesktopAdapter
from voice_control_usb.desktop.registry import AppAliasRegistry
from voice_control_usb.discord.adapter import StubDiscordAdapter
from voice_control_usb.discord.registry import DiscordTarget, DiscordTargetRegistry
from voice_control_usb.excel.adapter import StubExcelAdapter
from voice_control_usb.spotify.adapter import StubSpotifyAdapter


class ExpandedCommandParserTests(unittest.TestCase):
    def test_every_listed_command_example_reaches_its_registry_definition(self) -> None:
        parser = CommandParser()

        for section in COMMAND_SECTIONS:
            for item in section.commands:
                with self.subTest(command=item.registry_name, example=item.example):
                    result = parser.parse(item.example)
                    self.assertIsNotNone(result.command)
                    self.assertEqual(result.command.name, item.registry_name)

    def test_excel_ranges_formulas_and_percentages_are_normalized(self) -> None:
        parser = CommandParser()

        selected = parser.parse("select range a1:c10").command
        formula = parser.parse("enter formula SUM(A1:A10)").command
        discord_volume = parser.parse("set discord output volume to 65").command

        self.assertEqual(selected.arguments, {"range": "A1:C10"})
        self.assertEqual(formula.arguments, {"formula": "=SUM(A1:A10)"})
        self.assertEqual(discord_volume.arguments, {"percent": 65})


class ExpandedAdapterTests(unittest.TestCase):
    def test_excel_range_clipboard_format_and_sheet_commands(self) -> None:
        excel = StubExcelAdapter()
        excel.create_workbook()
        excel.go_to_cell("A1")
        excel.type_text("pass")
        excel.select_range("A1:A3")
        excel.fill_down()
        excel.copy_range("A1:A3")
        excel.go_to_cell("B1")
        excel.paste_cells()
        excel.select_range("B1:B3")
        excel.format_bold()
        excel.format_currency()
        pasted = [excel.cells[f"B{row}"] for row in range(1, 4)]
        created = excel.create_sheet("Results")
        renamed = excel.rename_sheet("Summary")

        self.assertEqual(pasted, ["pass"] * 3)
        self.assertEqual(excel._active_sheet().formats, {})
        self.assertEqual(created, "Created sheet: Results")
        self.assertEqual(renamed, "Renamed sheet Results to Summary")

    def test_excel_find_replace_filter_rows_and_formula_commands(self) -> None:
        excel = StubExcelAdapter()
        excel.open_excel()
        excel.go_to_cell("A1")
        excel.type_text("pending")
        self.assertIn("A1", excel.find_value("pend"))
        self.assertIn("Replaced 1", excel.replace_value("pending", "complete"))
        excel.enter_formula("=1+1")
        excel.filter_column("A", "complete")
        inserted = excel.insert_row("above")
        read = excel.read_range("A1:A2")

        self.assertEqual(inserted, "Inserted row 1")
        self.assertIn("A2==1+1", read)
        self.assertEqual(excel._active_sheet().filters["A"], "complete")

    def test_desktop_window_shortcut_settings_and_clipboard_commands(self) -> None:
        desktop = StubDesktopAdapter(AppAliasRegistry.load_default())
        desktop.clipboard_text = "hello"

        self.assertIn("notepad", desktop.switch_app("notepad"))
        self.assertIn("maximized", desktop.set_window_state("maximized"))
        self.assertIn("left", desktop.snap_window("left"))
        self.assertIn("select all", desktop.send_shortcut("select_all"))
        self.assertIn("sound", desktop.open_settings("sound"))
        self.assertEqual(desktop.read_clipboard(), "Clipboard text: hello")
        self.assertEqual(desktop.clear_clipboard(), "Clipboard cleared (stub)")
        self.assertIn("Screenshot captured", desktop.take_screenshot())

    def test_browser_tab_read_zoom_and_navigation_commands(self) -> None:
        browser = StubBrowserAdapter()
        browser.open_url("https://example.com")
        browser.new_tab()
        browser.open_url("https://docs.example.org")

        self.assertEqual(browser.switch_tab_title("docs.example.org").tab_index, 2)
        self.assertEqual(browser.zoom("in")[1], 110)
        self.assertEqual(browser.zoom("reset")[1], 100)
        self.assertTrue(browser.read_headings())
        self.assertEqual(browser.read_selection(), "Example selected text")
        self.assertEqual(browser.copy_page_url(), "https://docs.example.org")
        browser.close_tab_index(2)
        self.assertEqual(browser.reopen_closed_tab().url, "https://docs.example.org")

    def test_spotify_search_playback_and_library_commands(self) -> None:
        spotify = StubSpotifyAdapter(playlists={"Favorites": []})

        self.assertIn("Discovery", spotify.play_item("album", "Discovery"))
        spotify.set_shuffle(True)
        spotify.set_repeat("context")
        spotify.seek("forward", 30)
        spotify.seek("backward", 10)
        spotify.restart_song()
        spotify.like_song()
        added = spotify.add_to_playlist("favorites")

        self.assertTrue(spotify.shuffle_enabled)
        self.assertEqual(spotify.repeat_mode, "context")
        self.assertEqual(spotify.position_seconds, 0)
        self.assertTrue(spotify.liked)
        self.assertIn("Favorites", added)

    def test_discord_call_read_and_volume_commands(self) -> None:
        registry = DiscordTargetRegistry(
            {
                "general": DiscordTarget(
                    "general", "123", "456", "General voice"
                )
            }
        )
        discord = StubDiscordAdapter(registry)
        joined = discord.join_channel("general")
        discord.set_input_volume(75)
        discord.set_output_volume(60)

        self.assertTrue(joined.in_call)
        self.assertEqual(discord.read_channel(), "General voice")
        self.assertEqual(discord.report().input_volume, 75)
        self.assertEqual(discord.report().output_volume, 60)
        self.assertFalse(discord.leave_call().in_call)


class ConversationalControlTests(unittest.TestCase):
    def test_repeat_report_correction_and_undo_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            excel = StubExcelAdapter()
            app = AssistantApp(
                proposal_path=Path(tmp_dir) / "unsupported.jsonl",
                excel=excel,
            )
            app.handle_text("go to A1")
            app.handle_text("enter 42")

            self.assertIn("Last input: enter 42", app.handle_text("what did you hear"))
            self.assertIn("Current cell", app.handle_text("no, I said report current cell"))
            app.handle_text("enter 99")
            self.assertIn("Undid last Excel change", app.handle_text("undo that"))
            self.assertIn("Undid last Excel change", app.handle_text("repeat that"))

    def test_show_commands_and_stop_listening_are_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            app = AssistantApp(proposal_path=Path(tmp_dir) / "unsupported.jsonl")

            commands = app.handle_text("show browser commands")
            stopped = app.handle_text("stop listening")

            self.assertIn("open link <NUMBER>", commands)
            self.assertIn("Listening stopped", stopped)


if __name__ == "__main__":
    unittest.main()
