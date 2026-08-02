"""Tests for optional Spotify PKCE and credential-store boundaries."""

from __future__ import annotations

import unittest
from urllib.parse import parse_qs, urlparse

from voice_control_usb.spotify.credentials import InMemoryCredentialStore
from voice_control_usb.spotify.oauth import SpotifyOAuthClient, SpotifyOAuthConfig


class SpotifyOAuthTests(unittest.TestCase):
    def test_authorization_request_uses_pkce_state_and_least_playback_scopes(self) -> None:
        client = SpotifyOAuthClient(
            SpotifyOAuthConfig(client_id="client-123"),
            InMemoryCredentialStore(),
        )

        request = client.create_authorization_request()
        query = parse_qs(urlparse(request.url).query)

        self.assertEqual(query["client_id"], ["client-123"])
        self.assertEqual(query["response_type"], ["code"])
        self.assertEqual(query["code_challenge_method"], ["S256"])
        self.assertEqual(query["state"], [request.state])
        self.assertNotEqual(query["code_challenge"], [request.code_verifier])
        self.assertEqual(
            set(query["scope"][0].split()),
            {"user-read-playback-state", "user-modify-playback-state"},
        )

    def test_code_exchange_persists_only_refresh_token_through_store(self) -> None:
        posted: list[tuple[str, dict[str, str]]] = []

        def token_post(url: str, form) -> dict[str, object]:
            posted.append((url, dict(form)))
            return {
                "access_token": "short-lived-access",
                "refresh_token": "long-lived-refresh",
                "expires_in": 3600,
                "scope": "user-read-playback-state user-modify-playback-state",
            }

        store = InMemoryCredentialStore()
        client = SpotifyOAuthClient(
            SpotifyOAuthConfig(client_id="client-123"),
            store,
            token_post=token_post,
        )

        tokens = client.exchange_code("authorization-code", "pkce-verifier")

        self.assertEqual(tokens.access_token, "short-lived-access")
        self.assertEqual(store.get_refresh_token(), "long-lived-refresh")
        self.assertEqual(posted[0][1]["grant_type"], "authorization_code")
        self.assertNotIn("client_secret", posted[0][1])

    def test_refresh_reuses_existing_token_when_spotify_does_not_rotate_it(self) -> None:
        store = InMemoryCredentialStore("existing-refresh")

        def token_post(url: str, form) -> dict[str, object]:
            self.assertEqual(form["refresh_token"], "existing-refresh")
            return {
                "access_token": "new-access",
                "expires_in": 3600,
                "scope": "user-read-playback-state",
            }

        client = SpotifyOAuthClient(
            SpotifyOAuthConfig(client_id="client-123"),
            store,
            token_post=token_post,
        )

        tokens = client.refresh_access_token()

        self.assertEqual(tokens.refresh_token, "existing-refresh")
        self.assertEqual(store.get_refresh_token(), "existing-refresh")

    def test_config_rejects_non_loopback_redirect(self) -> None:
        with self.assertRaisesRegex(ValueError, "loopback"):
            SpotifyOAuthConfig(
                client_id="client-123",
                redirect_uri="https://example.com/callback",
            )


if __name__ == "__main__":
    unittest.main()
