"""Spotify playback boundary and deterministic test implementation."""

from __future__ import annotations

from dataclasses import dataclass, field


class SpotifyAdapter:
    def play_item(self, item_type: str, query: str) -> str: raise NotImplementedError
    def set_shuffle(self, enabled: bool) -> str: raise NotImplementedError
    def set_repeat(self, mode: str) -> str: raise NotImplementedError
    def seek(self, direction: str, seconds: int) -> str: raise NotImplementedError
    def restart_song(self) -> str: raise NotImplementedError
    def like_song(self) -> str: raise NotImplementedError
    def add_to_playlist(self, playlist: str) -> str: raise NotImplementedError


@dataclass
class StubSpotifyAdapter(SpotifyAdapter):
    """Stateful Spotify stand-in used by deterministic tests."""

    current_item: str = "Test Song"
    current_uri: str = "spotify:track:test"
    shuffle_enabled: bool = False
    repeat_mode: str = "off"
    position_seconds: int = 0
    liked: bool = False
    playlists: dict[str, list[str]] = field(default_factory=lambda: {"Favorites": []})

    def play_item(self, item_type: str, query: str) -> str:
        if item_type not in {"track", "artist", "album", "playlist"}:
            raise ValueError("Spotify item type must be track, artist, album, or playlist.")
        self.current_item = query
        self.current_uri = f"spotify:{item_type}:{query.casefold().replace(' ', '-')}"
        self.position_seconds = 0
        return f"Playing Spotify {item_type}: {query}"

    def set_shuffle(self, enabled: bool) -> str:
        self.shuffle_enabled = enabled
        return f"Spotify shuffle {'on' if enabled else 'off'}"

    def set_repeat(self, mode: str) -> str:
        if mode not in {"track", "context", "off"}:
            raise ValueError("Spotify repeat mode must be track, context, or off.")
        self.repeat_mode = mode
        return f"Spotify repeat set to {mode}"

    def seek(self, direction: str, seconds: int) -> str:
        if direction not in {"forward", "backward"} or seconds < 1:
            raise ValueError("Spotify seek requires a direction and positive seconds.")
        delta = seconds if direction == "forward" else -seconds
        self.position_seconds = max(0, self.position_seconds + delta)
        return f"Spotify moved {direction} {seconds} second(s)"

    def restart_song(self) -> str:
        self.position_seconds = 0
        return "Spotify song restarted"

    def like_song(self) -> str:
        self.liked = True
        return f"Saved Spotify song: {self.current_item}"

    def add_to_playlist(self, playlist: str) -> str:
        target = next((name for name in self.playlists if name.casefold() == playlist.casefold()), None)
        if target is None:
            raise ValueError(f"Spotify playlist not found: {playlist}")
        self.playlists[target].append(self.current_uri)
        return f"Added {self.current_item} to Spotify playlist: {target}"


class UnavailableSpotifyAdapter(SpotifyAdapter):
    def _unavailable(self):
        raise RuntimeError(
            "Spotify voice search is not connected. Configure the Spotify client ID, "
            "then run the Spotify connection setup first."
        )

    def play_item(self, item_type: str, query: str) -> str: return self._unavailable()
    def set_shuffle(self, enabled: bool) -> str: return self._unavailable()
    def set_repeat(self, mode: str) -> str: return self._unavailable()
    def seek(self, direction: str, seconds: int) -> str: return self._unavailable()
    def restart_song(self) -> str: return self._unavailable()
    def like_song(self) -> str: return self._unavailable()
    def add_to_playlist(self, playlist: str) -> str: return self._unavailable()
