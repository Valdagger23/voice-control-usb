"""Contract tests for the native Windows media adapter using fake endpoints."""

from __future__ import annotations

import unittest

from voice_control_usb.media.windows_adapter import WindowsMediaAdapter


class _Status:
    name = "PLAYING"


class _PlaybackInfo:
    playback_status = _Status()


class _Properties:
    title = "Native Test Track"
    artist = "Native Test Artist"


class _Session:
    source_app_user_model_id = "Test.Player"

    def __init__(self, operation_succeeded: bool = True) -> None:
        self.operation_succeeded = operation_succeeded
        self.calls: list[str] = []

    async def try_play_async(self) -> bool:
        self.calls.append("play")
        return self.operation_succeeded

    async def try_pause_async(self) -> bool:
        self.calls.append("pause")
        return self.operation_succeeded

    async def try_skip_next_async(self) -> bool:
        self.calls.append("next")
        return self.operation_succeeded

    async def try_skip_previous_async(self) -> bool:
        self.calls.append("previous")
        return self.operation_succeeded

    async def try_get_media_properties_async(self) -> _Properties:
        return _Properties()

    def get_playback_info(self) -> _PlaybackInfo:
        return _PlaybackInfo()


class _EndpointVolume:
    def __init__(self) -> None:
        self.scalar = 0.59
        self.muted = False

    def SetMute(self, muted: bool, event_context) -> None:
        self.muted = muted

    def SetMasterVolumeLevelScalar(self, scalar: float, event_context) -> None:
        self.scalar = scalar

    def GetMasterVolumeLevelScalar(self) -> float:
        return self.scalar

    def GetMute(self) -> bool:
        return self.muted


class _Endpoint:
    FriendlyName = "Test Speakers"

    def __init__(self) -> None:
        self.EndpointVolume = _EndpointVolume()


class _TestableWindowsMediaAdapter(WindowsMediaAdapter):
    def __init__(self, session: _Session, endpoint: _Endpoint | None = None) -> None:
        self.session = session
        self.endpoint = endpoint or _Endpoint()

    async def _current_session(self) -> _Session:
        return self.session

    def _speaker_endpoint(self) -> _Endpoint:
        return self.endpoint


class WindowsMediaAdapterTests(unittest.TestCase):
    def test_session_operations_call_explicit_native_methods(self) -> None:
        session = _Session()
        adapter = _TestableWindowsMediaAdapter(session)

        adapter.play()
        adapter.pause()
        adapter.next_track()
        adapter.previous_track()

        self.assertEqual(session.calls, ["play", "pause", "next", "previous"])

    def test_failed_native_operation_is_visible(self) -> None:
        adapter = _TestableWindowsMediaAdapter(_Session(operation_succeeded=False))

        with self.assertRaisesRegex(RuntimeError, "could not start playback"):
            adapter.play()

    def test_now_playing_and_volume_are_normalized(self) -> None:
        adapter = _TestableWindowsMediaAdapter(_Session())

        media = adapter.now_playing()
        volume = adapter.get_volume()

        self.assertEqual(media.title, "Native Test Track")
        self.assertEqual(media.playback_status, "playing")
        self.assertEqual(volume.percent, 59)
        self.assertEqual(volume.device_name, "Test Speakers")

        self.assertTrue(adapter.set_muted(True).muted)
        self.assertEqual(adapter.set_volume(25).percent, 25)


if __name__ == "__main__":
    unittest.main()
