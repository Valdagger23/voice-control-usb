"""Native Windows media-session and default speaker adapter."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable
from typing import TypeVar

from voice_control_usb.media.adapter import MediaAdapter, MediaSnapshot, VolumeSnapshot


T = TypeVar("T")


class WindowsMediaAdapter(MediaAdapter):
    """Control the current GSMTC session and default Windows playback endpoint."""

    def play(self) -> None:
        self._run_session_operation("start playback", "try_play_async")

    def pause(self) -> None:
        self._run_session_operation("pause playback", "try_pause_async")

    def next_track(self) -> None:
        self._run_session_operation("skip to the next track", "try_skip_next_async")

    def previous_track(self) -> None:
        self._run_session_operation(
            "return to the previous track",
            "try_skip_previous_async",
        )

    def set_muted(self, muted: bool) -> VolumeSnapshot:
        endpoint = self._speaker_endpoint()
        endpoint.EndpointVolume.SetMute(muted, None)
        return self._volume_snapshot(endpoint)

    def set_volume(self, percent: int) -> VolumeSnapshot:
        if not 0 <= percent <= 100:
            raise ValueError("Volume must be between 0 and 100 percent.")
        endpoint = self._speaker_endpoint()
        endpoint.EndpointVolume.SetMasterVolumeLevelScalar(percent / 100, None)
        return self._volume_snapshot(endpoint)

    def get_volume(self) -> VolumeSnapshot:
        return self._volume_snapshot(self._speaker_endpoint())

    def now_playing(self) -> MediaSnapshot:
        return self._run(self._read_now_playing())

    def _run_session_operation(self, description: str, method_name: str) -> None:
        succeeded = self._run(self._try_session_operation(method_name))
        if not succeeded:
            raise RuntimeError(f"The current media app could not {description}.")

    async def _try_session_operation(self, method_name: str) -> bool:
        session = await self._current_session()
        operation = getattr(session, method_name)
        return bool(await operation())

    async def _read_now_playing(self) -> MediaSnapshot:
        session = await self._current_session()
        properties = await session.try_get_media_properties_async()
        if properties is None:
            raise RuntimeError("The current media session did not provide track details.")
        status = session.get_playback_info().playback_status.name.casefold()
        return MediaSnapshot(
            title=properties.title.strip() or "Unknown title",
            artist=properties.artist.strip(),
            source_app=session.source_app_user_model_id.strip(),
            playback_status=status,
        )

    @staticmethod
    async def _current_session():
        try:
            from winrt.windows.media.control import (
                GlobalSystemMediaTransportControlsSessionManager,
            )
        except ImportError as error:
            raise ImportError(
                "Windows media support is not installed. Install the project with "
                "the Windows extras: 'pip install .[windows]'."
            ) from error

        manager = await GlobalSystemMediaTransportControlsSessionManager.request_async()
        session = manager.get_current_session()
        if session is None:
            raise RuntimeError(
                "No controllable Windows media session is active. Start Spotify or "
                "play media in a supported browser first."
            )
        return session

    @staticmethod
    def _speaker_endpoint():
        try:
            from pycaw.pycaw import AudioUtilities
        except ImportError as error:
            raise ImportError(
                "Windows speaker control is not installed. Install the project with "
                "the Windows extras: 'pip install .[windows]'."
            ) from error

        endpoint = AudioUtilities.GetSpeakers()
        if endpoint is None:
            raise RuntimeError("Windows did not report a default playback device.")
        return endpoint

    @staticmethod
    def _volume_snapshot(endpoint) -> VolumeSnapshot:
        volume = endpoint.EndpointVolume
        return VolumeSnapshot(
            percent=round(float(volume.GetMasterVolumeLevelScalar()) * 100),
            muted=bool(volume.GetMute()),
            device_name=str(endpoint.FriendlyName),
        )

    @staticmethod
    def _run(awaitable: Awaitable[T]) -> T:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(awaitable)
        close = getattr(awaitable, "close", None)
        if callable(close):
            close()
        raise RuntimeError(
            "Windows media actions cannot run inside an existing asynchronous event loop."
        )
