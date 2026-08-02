"""Media action boundary and deterministic development stub."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MediaSnapshot:
    """Visible state reported by the current Windows media session."""

    title: str
    artist: str = ""
    source_app: str = ""
    playback_status: str = "unknown"


@dataclass(frozen=True, slots=True)
class VolumeSnapshot:
    """State of the default Windows playback endpoint."""

    percent: int
    muted: bool
    device_name: str = ""


class MediaAdapter:
    """Boundary for deterministic playback and speaker actions."""

    def play(self) -> None:
        raise NotImplementedError

    def pause(self) -> None:
        raise NotImplementedError

    def next_track(self) -> None:
        raise NotImplementedError

    def previous_track(self) -> None:
        raise NotImplementedError

    def set_muted(self, muted: bool) -> VolumeSnapshot:
        raise NotImplementedError

    def set_volume(self, percent: int) -> VolumeSnapshot:
        raise NotImplementedError

    def get_volume(self) -> VolumeSnapshot:
        raise NotImplementedError

    def now_playing(self) -> MediaSnapshot:
        raise NotImplementedError


@dataclass
class StubMediaAdapter(MediaAdapter):
    """Safe in-memory media adapter used by tests and non-Windows hosts."""

    title: str = "Test Track"
    artist: str = "Test Artist"
    source_app: str = "stub-player"
    playback_status: str = "paused"
    volume_percent: int = 50
    muted: bool = False

    def play(self) -> None:
        self.playback_status = "playing"

    def pause(self) -> None:
        self.playback_status = "paused"

    def next_track(self) -> None:
        self.title = "Next Test Track"

    def previous_track(self) -> None:
        self.title = "Previous Test Track"

    def set_muted(self, muted: bool) -> VolumeSnapshot:
        self.muted = muted
        return self.get_volume()

    def set_volume(self, percent: int) -> VolumeSnapshot:
        self._validate_percent(percent)
        self.volume_percent = percent
        return self.get_volume()

    def get_volume(self) -> VolumeSnapshot:
        return VolumeSnapshot(
            percent=self.volume_percent,
            muted=self.muted,
            device_name="stub-speakers",
        )

    def now_playing(self) -> MediaSnapshot:
        return MediaSnapshot(
            title=self.title,
            artist=self.artist,
            source_app=self.source_app,
            playback_status=self.playback_status,
        )

    @staticmethod
    def _validate_percent(percent: int) -> None:
        if not 0 <= percent <= 100:
            raise ValueError("Volume must be between 0 and 100 percent.")
