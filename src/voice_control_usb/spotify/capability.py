"""Declared Spotify voice actions."""

from __future__ import annotations

from voice_control_usb.core.capabilities import ActionBinding, ActionSpec, SafetyClass
from voice_control_usb.core.models import Command
from voice_control_usb.spotify.adapter import SpotifyAdapter


def spotify_action_specs() -> list[ActionSpec]:
    return [
        ActionSpec("spotify", "spotify_play_item", "Play a named Spotify item.", argument_types={"item_type": str, "query": str}),
        ActionSpec("spotify", "spotify_set_shuffle", "Set Spotify shuffle.", reversible=True, argument_types={"enabled": bool}),
        ActionSpec("spotify", "spotify_set_repeat", "Set Spotify repeat.", reversible=True, argument_types={"mode": str}),
        ActionSpec("spotify", "spotify_seek", "Seek Spotify playback.", reversible=True, argument_types={"direction": str, "seconds": int}),
        ActionSpec("spotify", "spotify_restart_song", "Restart the current Spotify item.", reversible=True),
        ActionSpec("spotify", "spotify_like_song", "Save the current Spotify song.", safety_class=SafetyClass.REQUIRES_CONFIRMATION),
        ActionSpec("spotify", "spotify_add_to_playlist", "Add the current song to a playlist.", safety_class=SafetyClass.REQUIRES_CONFIRMATION, argument_types={"playlist": str}),
    ]


class SpotifyCapability:
    capability_id = "spotify"

    def __init__(self, adapter: SpotifyAdapter) -> None:
        self.adapter = adapter

    def bindings(self) -> list[ActionBinding]:
        handlers = {
            "spotify_play_item": lambda c: self.adapter.play_item(self._text(c, "item_type"), self._text(c, "query")),
            "spotify_set_shuffle": lambda c: self.adapter.set_shuffle(self._bool(c, "enabled")),
            "spotify_set_repeat": lambda c: self.adapter.set_repeat(self._text(c, "mode")),
            "spotify_seek": lambda c: self.adapter.seek(self._text(c, "direction"), self._int(c, "seconds")),
            "spotify_restart_song": lambda c: self.adapter.restart_song(),
            "spotify_like_song": lambda c: self.adapter.like_song(),
            "spotify_add_to_playlist": lambda c: self.adapter.add_to_playlist(self._text(c, "playlist")),
        }
        return [ActionBinding(spec, handlers[spec.action_id]) for spec in spotify_action_specs()]

    @staticmethod
    def _text(command: Command, name: str) -> str:
        value = command.arguments.get(name)
        if not isinstance(value, str):
            raise ValueError(f"Spotify argument '{name}' must be text.")
        return value

    @staticmethod
    def _bool(command: Command, name: str) -> bool:
        value = command.arguments.get(name)
        if not isinstance(value, bool):
            raise ValueError(f"Spotify argument '{name}' must be true or false.")
        return value

    @staticmethod
    def _int(command: Command, name: str) -> int:
        value = command.arguments.get(name)
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError(f"Spotify argument '{name}' must be a whole number.")
        return value
