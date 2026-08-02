"""Spotify OAuth 2.0 Authorization Code with PKCE boundary."""

from __future__ import annotations

import base64
from collections.abc import Callable, Mapping
from dataclasses import dataclass
import hashlib
import json
import os
import secrets
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from voice_control_usb.spotify.credentials import CredentialStore


SPOTIFY_AUTHORIZE_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
DEFAULT_SPOTIFY_REDIRECT_URI = "http://127.0.0.1:8765/callback"
DEFAULT_SPOTIFY_SCOPES = (
    "user-read-playback-state",
    "user-modify-playback-state",
)

TokenPost = Callable[[str, Mapping[str, str]], Mapping[str, object]]


@dataclass(frozen=True, slots=True)
class SpotifyOAuthConfig:
    """Non-secret Spotify desktop-app OAuth configuration."""

    client_id: str
    redirect_uri: str = DEFAULT_SPOTIFY_REDIRECT_URI
    scopes: tuple[str, ...] = DEFAULT_SPOTIFY_SCOPES

    def __post_init__(self) -> None:
        if not self.client_id.strip():
            raise ValueError("Spotify client ID must not be empty.")
        parsed = urlparse(self.redirect_uri)
        if parsed.scheme != "http" or parsed.hostname != "127.0.0.1":
            raise ValueError(
                "Spotify redirect URI must use an explicit 127.0.0.1 loopback address."
            )
        if parsed.port is None or not parsed.path.startswith("/"):
            raise ValueError("Spotify redirect URI must include a port and callback path.")
        if not self.scopes:
            raise ValueError("At least one Spotify OAuth scope is required.")

    @classmethod
    def from_environment(cls) -> "SpotifyOAuthConfig":
        client_id = os.environ.get("VOICE_CONTROL_USB_SPOTIFY_CLIENT_ID", "").strip()
        if not client_id:
            raise RuntimeError(
                "Spotify is not configured. Set VOICE_CONTROL_USB_SPOTIFY_CLIENT_ID "
                "to the client ID from your Spotify developer app."
            )
        return cls(
            client_id=client_id,
            redirect_uri=os.environ.get(
                "VOICE_CONTROL_USB_SPOTIFY_REDIRECT_URI",
                DEFAULT_SPOTIFY_REDIRECT_URI,
            ).strip(),
        )


@dataclass(frozen=True, slots=True)
class SpotifyAuthorizationRequest:
    """Short-lived PKCE values kept only for one browser authorization."""

    url: str
    state: str
    code_verifier: str


@dataclass(frozen=True, slots=True)
class SpotifyTokenSet:
    """Validated token response returned by Spotify."""

    access_token: str
    refresh_token: str
    expires_in: int
    scope: str


class SpotifyOAuthClient:
    """Build PKCE requests, exchange codes, and persist only refresh tokens."""

    def __init__(
        self,
        config: SpotifyOAuthConfig,
        credential_store: CredentialStore,
        token_post: TokenPost | None = None,
    ) -> None:
        self.config = config
        self.credential_store = credential_store
        self.token_post = token_post or _post_token_form

    @property
    def is_connected(self) -> bool:
        return self.credential_store.get_refresh_token() is not None

    def create_authorization_request(self) -> SpotifyAuthorizationRequest:
        verifier = secrets.token_urlsafe(64)
        challenge = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode("ascii")).digest()
        ).rstrip(b"=").decode("ascii")
        state = secrets.token_urlsafe(32)
        query = urlencode(
            {
                "client_id": self.config.client_id,
                "response_type": "code",
                "redirect_uri": self.config.redirect_uri,
                "scope": " ".join(self.config.scopes),
                "code_challenge_method": "S256",
                "code_challenge": challenge,
                "state": state,
            }
        )
        return SpotifyAuthorizationRequest(
            url=f"{SPOTIFY_AUTHORIZE_URL}?{query}",
            state=state,
            code_verifier=verifier,
        )

    def exchange_code(self, code: str, code_verifier: str) -> SpotifyTokenSet:
        if not code.strip() or not code_verifier.strip():
            raise ValueError("Spotify authorization code and PKCE verifier are required.")
        payload = self.token_post(
            SPOTIFY_TOKEN_URL,
            {
                "client_id": self.config.client_id,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.config.redirect_uri,
                "code_verifier": code_verifier,
            },
        )
        tokens = self._parse_token_set(payload, require_refresh_token=True)
        self.credential_store.set_refresh_token(tokens.refresh_token)
        return tokens

    def refresh_access_token(self) -> SpotifyTokenSet:
        refresh_token = self.credential_store.get_refresh_token()
        if refresh_token is None:
            raise RuntimeError("Spotify is not connected.")
        payload = self.token_post(
            SPOTIFY_TOKEN_URL,
            {
                "client_id": self.config.client_id,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
        )
        tokens = self._parse_token_set(
            payload,
            fallback_refresh_token=refresh_token,
        )
        if tokens.refresh_token != refresh_token:
            self.credential_store.set_refresh_token(tokens.refresh_token)
        return tokens

    @staticmethod
    def _parse_token_set(
        payload: Mapping[str, object],
        *,
        require_refresh_token: bool = False,
        fallback_refresh_token: str = "",
    ) -> SpotifyTokenSet:
        access_token = payload.get("access_token")
        refresh_token = payload.get("refresh_token", fallback_refresh_token)
        expires_in = payload.get("expires_in")
        scope = payload.get("scope", "")
        if not isinstance(access_token, str) or not access_token:
            raise RuntimeError("Spotify token response did not include an access token.")
        if require_refresh_token and (not isinstance(refresh_token, str) or not refresh_token):
            raise RuntimeError("Spotify token response did not include a refresh token.")
        if not isinstance(refresh_token, str) or not refresh_token:
            raise RuntimeError("No Spotify refresh token is available.")
        if not isinstance(expires_in, int) or isinstance(expires_in, bool):
            raise RuntimeError("Spotify token response did not include a valid expiry.")
        if not isinstance(scope, str):
            raise RuntimeError("Spotify token response included an invalid scope value.")
        return SpotifyTokenSet(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            scope=scope,
        )


def _post_token_form(url: str, form: Mapping[str, str]) -> Mapping[str, object]:
    request = Request(
        url,
        data=urlencode(form).encode("ascii"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Spotify authorization failed with HTTP {error.code}: {body}") from error
    except URLError as error:
        raise RuntimeError(f"Spotify authorization network request failed: {error.reason}") from error
    if not isinstance(payload, dict):
        raise RuntimeError("Spotify token endpoint returned an invalid response.")
    return payload
