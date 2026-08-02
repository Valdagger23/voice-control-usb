"""Regression tests for the command deck shown in the Windows shell."""

from __future__ import annotations

import unittest

from voice_control_usb.assistant.command_legend import (
    COMMAND_SECTIONS,
    filter_command_sections,
    registry_names_in_legend,
)
from voice_control_usb.core.registry import CommandRegistry


class CommandLegendTests(unittest.TestCase):
    def test_legend_covers_every_registered_voice_command(self) -> None:
        registry_names = set(CommandRegistry.load_default().names())

        self.assertEqual(registry_names_in_legend(), registry_names)

    def test_catalogue_registry_names_are_unique(self) -> None:
        names = [
            command.registry_name
            for section in COMMAND_SECTIONS
            for command in section.commands
        ]

        self.assertEqual(len(names), len(set(names)))

    def test_category_filter_returns_only_selected_section(self) -> None:
        sections = filter_command_sections(category="Media")

        self.assertEqual([section.short_name for section in sections], ["Media"])
        self.assertTrue(all(section.commands for section in sections))

    def test_query_filter_matches_phrases_and_descriptions(self) -> None:
        volume = filter_command_sections(query="volume")
        playback = filter_command_sections(query="playback")

        self.assertEqual(
            {command.registry_name for section in volume for command in section.commands},
            {
                "set_media_volume",
                "report_media_volume",
                "increase_media_volume",
                "decrease_media_volume",
                "discord_input_volume",
                "discord_output_volume",
            },
        )
        self.assertTrue(
            {"play_media", "pause_media", "mute_media"}.issubset(
                {
                    command.registry_name
                    for section in playback
                    for command in section.commands
                }
            )
        )

    def test_query_filter_is_case_insensitive_and_can_be_empty(self) -> None:
        discord = filter_command_sections(query="CAMERA")
        missing = filter_command_sections(query="not-a-real-command")

        self.assertEqual(
            {command.registry_name for section in discord for command in section.commands},
            {"discord_disable_camera", "discord_enable_camera"},
        )
        self.assertEqual(missing, ())


if __name__ == "__main__":
    unittest.main()
