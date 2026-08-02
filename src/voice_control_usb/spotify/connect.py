"""User-initiated local callback flow for optional Spotify connection."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, HTTPServer
import time
from urllib.parse import parse_qs, urlparse
import webbrowser

from voice_control_usb.spotify.oauth import SpotifyOAuthClient


def connect_spotify_account(client: SpotifyOAuthClient, timeout_seconds: float = 180) -> str:
    """Open Spotify authorization and receive one local loopback callback."""

    authorization = client.create_authorization_request()
    redirect = urlparse(client.config.redirect_uri)
    expected_path = redirect.path
    callback: dict[str, str] = {}

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
            requested = urlparse(self.path)
            if requested.path != expected_path:
                self.send_error(404)
                return
            values = parse_qs(requested.query)
            callback["code"] = values.get("code", [""])[0]
            callback["state"] = values.get("state", [""])[0]
            callback["error"] = values.get("error", [""])[0]
            body = (
                b"Spotify connection received. You can close this browser tab and "
                b"return to Voice Control USB."
            )
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            return

    try:
        server = HTTPServer(
            (redirect.hostname or "127.0.0.1", redirect.port or 8765),
            CallbackHandler,
        )
    except OSError as error:
        raise RuntimeError(
            f"Could not start the local Spotify callback on {client.config.redirect_uri}: {error}"
        ) from error
    server.timeout = 0.5
    try:
        if not webbrowser.open(authorization.url, new=1, autoraise=True):
            raise RuntimeError(
                "Could not open the Spotify sign-in page in the default browser."
            )
        deadline = time.monotonic() + timeout_seconds
        while not callback and time.monotonic() < deadline:
            server.handle_request()
    finally:
        server.server_close()

    if not callback:
        raise RuntimeError("Spotify connection timed out before authorization completed.")
    if callback.get("error"):
        raise RuntimeError(f"Spotify authorization was not completed: {callback['error']}")
    if callback.get("state") != authorization.state:
        raise RuntimeError("Spotify authorization returned an invalid state value.")
    code = callback.get("code", "")
    if not code:
        raise RuntimeError("Spotify authorization did not return a code.")
    client.exchange_code(code, authorization.code_verifier)
    return "Spotify account connected. Refresh token saved in Windows Credential Manager."
