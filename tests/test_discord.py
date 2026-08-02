"""Tests for deliberate Discord contracts and safety."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from voice_control_usb.assistant.app import AssistantApp
from voice_control_usb.discord.adapter import StubDiscordAdapter
from voice_control_usb.discord.registry import DiscordTarget, DiscordTargetRegistry


class DiscordCapabilityTests(unittest.TestCase):
    def make_app(self, directory: str) -> tuple[AssistantApp, StubDiscordAdapter]:
        registry = DiscordTargetRegistry(
            {"team": DiscordTarget("team", "123", "456", "Team chat")}
        )
        adapter = StubDiscordAdapter(registry)
        return AssistantApp(Path(directory) / "proposals.jsonl", discord=adapter), adapter

    def test_navigation_and_visible_draft_never_send_automatically(self) -> None:
        with TemporaryDirectory() as directory:
            app, adapter = self.make_app(directory)
            self.assertIn("Team chat", app.handle_text("go to discord team"))
            self.assertIn("draft present", app.handle_text("draft discord message hello"))
            pending = app.handle_text("send discord draft")

            self.assertIn("CONFIRMATION REQUIRED", pending)
            self.assertEqual(adapter.snapshot.draft, "hello")
            prepared = app.handle_text("confirm")
            self.assertIn("press Enter yourself to send", prepared)
            self.assertEqual(adapter.snapshot.draft, "hello")

    def test_privacy_reducing_actions_run_and_enabling_actions_require_confirmation(self) -> None:
        with TemporaryDirectory() as directory:
            app, adapter = self.make_app(directory)
            self.assertIn("muted", app.handle_text("mute microphone"))
            self.assertTrue(adapter.snapshot.microphone_muted)
            self.assertIn("CONFIRMATION REQUIRED", app.handle_text("unmute microphone"))
            self.assertTrue(adapter.snapshot.microphone_muted)
            app.handle_text("cancel")
            self.assertIn("disabled", app.handle_text("disable camera"))
            self.assertIn("CONFIRMATION REQUIRED", app.handle_text("enable camera"))

    def test_user_token_and_bulk_messaging_are_blocked(self) -> None:
        with TemporaryDirectory() as directory:
            app, _ = self.make_app(directory)
            self.assertIn("not approved", app.handle_text("configure discord user token secret"))
            self.assertIn("not approved", app.handle_text("send discord messages everyone"))


if __name__ == "__main__":
    unittest.main()
