"""Small Spotify Web API adapter using the existing PKCE credential flow."""

from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from voice_control_usb.spotify.adapter import SpotifyAdapter
from voice_control_usb.spotify.oauth import SpotifyOAuthClient


SPOTIFY_API_ROOT = "https://api.spotify.com/v1"


class SpotifyWebApiAdapter(SpotifyAdapter):
    def __init__(self, oauth: SpotifyOAuthClient) -> None:
        self.oauth = oauth

    def play_item(self, item_type: str, query: str) -> str:
        if item_type not in {"track", "artist", "album", "playlist"}:
            raise ValueError("Spotify item type must be track, artist, album, or playlist.")
        payload = self._request(
            "GET",
            "/search",
            query={"q": query, "type": item_type, "limit": "1"},
        )
        container = payload.get(f"{item_type}s")
        items = container.get("items", []) if isinstance(container, dict) else []
        if not isinstance(items, list) or not items or not isinstance(items[0], dict):
            raise ValueError(f"No Spotify {item_type} found for: {query}")
        item = items[0]
        uri, name = item.get("uri"), item.get("name")
        if not isinstance(uri, str) or not isinstance(name, str):
            raise RuntimeError("Spotify search returned an incomplete item.")
        body = {"uris": [uri]} if item_type == "track" else {"context_uri": uri}
        self._request("PUT", "/me/player/play", body=body)
        return f"Playing Spotify {item_type}: {name}"

    def set_shuffle(self, enabled: bool) -> str:
        self._request("PUT", "/me/player/shuffle", query={"state": str(enabled).lower()})
        return f"Spotify shuffle {'on' if enabled else 'off'}"

    def set_repeat(self, mode: str) -> str:
        if mode not in {"track", "context", "off"}:
            raise ValueError("Spotify repeat mode must be track, context, or off.")
        self._request("PUT", "/me/player/repeat", query={"state": mode})
        return f"Spotify repeat set to {mode}"

    def seek(self, direction: str, seconds: int) -> str:
        if direction not in {"forward", "backward"} or seconds < 1:
            raise ValueError("Spotify seek requires a direction and positive seconds.")
        state = self._request("GET", "/me/player")
        progress = state.get("progress_ms", 0)
        item = state.get("item", {})
        duration = item.get("duration_ms", 0) if isinstance(item, dict) else 0
        if not isinstance(progress, int) or not isinstance(duration, int):
            raise RuntimeError("Spotify did not report a seekable playback position.")
        delta = seconds * 1000 * (1 if direction == "forward" else -1)
        target = max(0, min(duration, progress + delta))
        self._request("PUT", "/me/player/seek", query={"position_ms": str(target)})
        return f"Spotify moved {direction} {seconds} second(s)"

    def restart_song(self) -> str:
        self._request("PUT", "/me/player/seek", query={"position_ms": "0"})
        return "Spotify song restarted"

    def like_song(self) -> str:
        uri, name = self._current_track()
        self._request("PUT", "/me/library", query={"uris": uri})
        return f"Saved Spotify song: {name}"

    def add_to_playlist(self, playlist: str) -> str:
        uri, name = self._current_track()
        payload = self._request("GET", "/me/playlists", query={"limit": "50"})
        items = payload.get("items", [])
        matches = [
            item
            for item in items
            if isinstance(item, dict)
            and isinstance(item.get("name"), str)
            and playlist.casefold() in item["name"].casefold()
        ] if isinstance(items, list) else []
        if not matches:
            raise ValueError(f"Spotify playlist not found: {playlist}")
        if len(matches) > 1:
            exact = [item for item in matches if item["name"].casefold() == playlist.casefold()]
            if len(exact) != 1:
                raise ValueError(f"Multiple Spotify playlists match: {playlist}")
            matches = exact
        playlist_id = matches[0].get("id")
        playlist_name = matches[0].get("name")
        if not isinstance(playlist_id, str) or not isinstance(playlist_name, str):
            raise RuntimeError("Spotify returned an incomplete playlist.")
        self._request("POST", f"/playlists/{quote(playlist_id)}/items", body={"uris": [uri]})
        return f"Added {name} to Spotify playlist: {playlist_name}"

    def _current_track(self) -> tuple[str, str]:
        payload = self._request("GET", "/me/player/currently-playing")
        item = payload.get("item")
        if not isinstance(item, dict):
            raise RuntimeError("Spotify is not currently playing a track.")
        uri, name = item.get("uri"), item.get("name")
        if not isinstance(uri, str) or not uri.startswith("spotify:track:") or not isinstance(name, str):
            raise RuntimeError("The current Spotify item is not a savable track.")
        return uri, name

    def _request(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, str] | None = None,
        body: dict[str, object] | None = None,
    ) -> dict[str, object]:
        token = self.oauth.refresh_access_token().access_token
        url = f"{SPOTIFY_API_ROOT}{path}"
        if query:
            url += "?" + urlencode(query)
        data = None if body is None else json.dumps(body).encode("utf-8")
        request = Request(
            url,
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=20) as response:
                raw = response.read()
        except HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Spotify request failed with HTTP {error.code}: {detail}") from error
        except URLError as error:
            raise RuntimeError(f"Spotify network request failed: {error.reason}") from error
        if not raw:
            return {}
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict):
            raise RuntimeError("Spotify returned an invalid response.")
        return payload
