"""Action contracts declared by the media capability."""

from __future__ import annotations

from voice_control_usb.core.capabilities import (
    ActionBinding,
    ActionResult,
    ActionSpec,
)
from voice_control_usb.core.models import Command
from voice_control_usb.media.adapter import MediaAdapter, MediaSnapshot, VolumeSnapshot


def media_action_specs() -> list[ActionSpec]:
    return [
        ActionSpec(
            capability_id="media",
            action_id="play_media",
            description="Start or resume the current Windows media session.",
            reversible=True,
        ),
        ActionSpec(
            capability_id="media",
            action_id="pause_media",
            description="Pause the current Windows media session.",
            reversible=True,
        ),
        ActionSpec(
            capability_id="media",
            action_id="next_track",
            description="Skip to the next item in the current media session.",
        ),
        ActionSpec(
            capability_id="media",
            action_id="previous_track",
            description="Return to the previous item in the current media session.",
        ),
        ActionSpec(
            capability_id="media",
            action_id="set_media_muted",
            description="Set the default Windows playback endpoint mute state.",
            reversible=True,
            argument_types={"muted": bool},
        ),
        ActionSpec(
            capability_id="media",
            action_id="set_media_volume",
            description="Set default Windows playback volume from 0 to 100 percent.",
            argument_types={"percent": int},
        ),
        ActionSpec(
            capability_id="media",
            action_id="report_media_volume",
            description="Report default Windows playback volume and mute state.",
        ),
        ActionSpec(
            capability_id="media",
            action_id="report_now_playing",
            description="Report the current Windows media session and playback state.",
        ),
        ActionSpec(
            capability_id="media",
            action_id="adjust_media_volume",
            description="Adjust speaker volume by a relative amount.",
            reversible=True,
            argument_types={"delta": int},
        ),
    ]


class MediaCapability:
    """Expose Windows media-session and speaker operations as action bindings."""

    capability_id = "media"

    def __init__(self, adapter: MediaAdapter) -> None:
        self.adapter = adapter

    def bindings(self) -> list[ActionBinding]:
        handlers = {
            "play_media": self._play,
            "pause_media": self._pause,
            "next_track": self._next_track,
            "previous_track": self._previous_track,
            "set_media_muted": self._set_muted,
            "set_media_volume": self._set_volume,
            "report_media_volume": self._report_volume,
            "report_now_playing": self._report_now_playing,
            "adjust_media_volume": self._adjust_volume,
        }
        return [ActionBinding(spec, handlers[spec.action_id]) for spec in media_action_specs()]

    def _play(self, command: Command) -> ActionResult:
        self.adapter.play()
        return self._result(command, "Media playback started.")

    def _pause(self, command: Command) -> ActionResult:
        self.adapter.pause()
        return self._result(command, "Media playback paused.")

    def _next_track(self, command: Command) -> ActionResult:
        self.adapter.next_track()
        return self._result(command, "Skipped to the next track.")

    def _previous_track(self, command: Command) -> ActionResult:
        self.adapter.previous_track()
        return self._result(command, "Returned to the previous track.")

    def _set_muted(self, command: Command) -> ActionResult:
        muted = command.arguments.get("muted")
        if not isinstance(muted, bool):
            raise ValueError("Media mute state must be true or false.")
        snapshot = self.adapter.set_muted(muted)
        state = "muted" if snapshot.muted else "unmuted"
        return self._volume_result(command, snapshot, f"Speakers {state}.")

    def _set_volume(self, command: Command) -> ActionResult:
        percent = command.arguments.get("percent")
        if not isinstance(percent, int) or isinstance(percent, bool):
            raise ValueError("Media volume must be a whole number.")
        if not 0 <= percent <= 100:
            raise ValueError("Volume must be between 0 and 100 percent.")
        snapshot = self.adapter.set_volume(percent)
        return self._volume_result(
            command,
            snapshot,
            f"Speaker volume set to {snapshot.percent} percent.",
        )

    def _report_volume(self, command: Command) -> ActionResult:
        snapshot = self.adapter.get_volume()
        mute_text = "muted" if snapshot.muted else "not muted"
        return self._volume_result(
            command,
            snapshot,
            f"Speaker volume is {snapshot.percent} percent and {mute_text}.",
        )

    def _report_now_playing(self, command: Command) -> ActionResult:
        snapshot = self.adapter.now_playing()
        artist_text = f" by {snapshot.artist}" if snapshot.artist else ""
        source_text = f" in {snapshot.source_app}" if snapshot.source_app else ""
        message = (
            f"Now playing: {snapshot.title}{artist_text}{source_text} "
            f"({snapshot.playback_status})."
        )
        return self._result(
            command,
            message,
            details={
                "title": snapshot.title,
                "artist": snapshot.artist,
                "source_app": snapshot.source_app,
                "playback_status": snapshot.playback_status,
            },
        )

    def _adjust_volume(self, command: Command) -> ActionResult:
        delta = command.arguments.get("delta")
        if not isinstance(delta, int) or isinstance(delta, bool):
            raise ValueError("Media volume adjustment must be a whole number.")
        current = self.adapter.get_volume()
        target = max(0, min(100, current.percent + delta))
        snapshot = self.adapter.set_volume(target)
        direction = "raised" if delta > 0 else "lowered"
        return self._volume_result(
            command,
            snapshot,
            f"Speaker volume {direction} to {snapshot.percent} percent.",
        )

    @staticmethod
    def _result(
        command: Command,
        message: str,
        *,
        details: dict[str, object] | None = None,
    ) -> ActionResult:
        return ActionResult(
            capability_id="media",
            action_id=command.action,
            message=message,
            details={} if details is None else details,
        )

    @classmethod
    def _volume_result(
        cls,
        command: Command,
        snapshot: VolumeSnapshot,
        message: str,
    ) -> ActionResult:
        return cls._result(
            command,
            message,
            details={
                "percent": snapshot.percent,
                "muted": snapshot.muted,
                "device_name": snapshot.device_name,
            },
        )
