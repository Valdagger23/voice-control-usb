"""Create the Spotify capability adapter for the current host."""

from __future__ import annotations

import sys

from voice_control_usb.spotify.adapter import SpotifyAdapter, UnavailableSpotifyAdapter
from voice_control_usb.spotify.credentials import WindowsCredentialStore
from voice_control_usb.spotify.oauth import SpotifyOAuthClient, SpotifyOAuthConfig
from voice_control_usb.spotify.web_api import SpotifyWebApiAdapter


def create_spotify_adapter() -> SpotifyAdapter:
    if sys.platform != "win32":
        return UnavailableSpotifyAdapter()
    try:
        config = SpotifyOAuthConfig.from_environment()
        store = WindowsCredentialStore()
        if store.get_refresh_token() is None:
            return UnavailableSpotifyAdapter()
        return SpotifyWebApiAdapter(SpotifyOAuthClient(config, store))
    except (ImportError, RuntimeError, ValueError):
        return UnavailableSpotifyAdapter()
