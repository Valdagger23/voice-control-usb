"""Tests for deterministic media contracts and adapters."""

from __future__ import annotations

import unittest

from voice_control_usb.core.models import Command
from voice_control_usb.desktop.adapter import StubDesktopAdapter
from voice_control_usb.desktop.registry import AppAliasRegistry
from voice_control_usb.excel.adapter import StubExcelAdapter
from voice_control_usb.executor.engine import ExecutionEngine
from voice_control_usb.media.adapter import StubMediaAdapter


class MediaCapabilityTests(unittest.TestCase):
    def make_engine(self, media: StubMediaAdapter) -> ExecutionEngine:
        return ExecutionEngine(
            excel=StubExcelAdapter(),
            desktop=StubDesktopAdapter(aliases=AppAliasRegistry.load_default()),
            media=media,
        )

    def test_playback_actions_route_through_media_capability(self) -> None:
        media = StubMediaAdapter()
        engine = self.make_engine(media)

        self.assertEqual(
            engine.execute(Command(name="play", action="play_media")),
            "Media playback started.",
        )
        self.assertEqual(media.playback_status, "playing")
        self.assertEqual(
            engine.execute(Command(name="pause", action="pause_media")),
            "Media playback paused.",
        )
        self.assertEqual(media.playback_status, "paused")

        engine.execute(Command(name="next", action="next_track"))
        self.assertEqual(media.title, "Next Test Track")
        engine.execute(Command(name="previous", action="previous_track"))
        self.assertEqual(media.title, "Previous Test Track")

    def test_explicit_mute_and_volume_actions_return_structured_state(self) -> None:
        media = StubMediaAdapter(volume_percent=33)
        engine = self.make_engine(media)

        mute = engine.execute_result(
            Command(
                name="mute",
                action="set_media_muted",
                arguments={"muted": True},
            )
        )
        volume = engine.execute_result(
            Command(
                name="set_volume",
                action="set_media_volume",
                arguments={"percent": 72},
            )
        )

        self.assertEqual(mute.message, "Speakers muted.")
        self.assertEqual(mute.details["muted"], True)
        self.assertEqual(volume.message, "Speaker volume set to 72 percent.")
        self.assertEqual(volume.details["percent"], 72)
        self.assertTrue(media.muted)

    def test_now_playing_returns_track_details_for_audit(self) -> None:
        media = StubMediaAdapter(
            title="Small Hours",
            artist="Example Artist",
            source_app="Spotify",
            playback_status="playing",
        )
        result = self.make_engine(media).execute_result(
            Command(name="now_playing", action="report_now_playing")
        )

        self.assertEqual(
            result.message,
            "Now playing: Small Hours by Example Artist in Spotify (playing).",
        )
        self.assertEqual(result.details["title"], "Small Hours")
        self.assertEqual(result.details["source_app"], "Spotify")

    def test_volume_validation_rejects_out_of_range_value(self) -> None:
        engine = self.make_engine(StubMediaAdapter())

        with self.assertRaisesRegex(ValueError, "between 0 and 100"):
            engine.execute(
                Command(
                    name="set_volume",
                    action="set_media_volume",
                    arguments={"percent": 101},
                )
            )


if __name__ == "__main__":
    unittest.main()
