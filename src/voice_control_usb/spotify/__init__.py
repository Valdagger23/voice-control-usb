"""Optional Spotify account authorization support."""

from voice_control_usb.spotify.credentials import (
    CredentialStore,
    InMemoryCredentialStore,
    WindowsCredentialStore,
)
from voice_control_usb.spotify.oauth import SpotifyOAuthClient, SpotifyOAuthConfig

__all__ = [
    "CredentialStore",
    "InMemoryCredentialStore",
    "SpotifyOAuthClient",
    "SpotifyOAuthConfig",
    "WindowsCredentialStore",
]
