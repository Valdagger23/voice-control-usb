"""Credential-store boundary for Spotify refresh tokens."""

from __future__ import annotations


SPOTIFY_REFRESH_TOKEN_TARGET = "voice-control-usb/spotify-refresh-token"


class CredentialStore:
    """Minimal secret store used by the Spotify authorization boundary."""

    def get_refresh_token(self) -> str | None:
        raise NotImplementedError

    def set_refresh_token(self, refresh_token: str) -> None:
        raise NotImplementedError

    def delete_refresh_token(self) -> bool:
        raise NotImplementedError


class InMemoryCredentialStore(CredentialStore):
    """Non-persistent credential store used only by automated tests."""

    def __init__(self, refresh_token: str | None = None) -> None:
        self.refresh_token = refresh_token

    def get_refresh_token(self) -> str | None:
        return self.refresh_token

    def set_refresh_token(self, refresh_token: str) -> None:
        self.refresh_token = _validate_refresh_token(refresh_token)

    def delete_refresh_token(self) -> bool:
        existed = self.refresh_token is not None
        self.refresh_token = None
        return existed


class WindowsCredentialStore(CredentialStore):
    """Store the Spotify refresh token in Windows Credential Manager."""

    def __init__(self, target_name: str = SPOTIFY_REFRESH_TOKEN_TARGET) -> None:
        if not target_name.strip():
            raise ValueError("Credential target name must not be empty.")
        self.target_name = target_name

    def get_refresh_token(self) -> str | None:
        win32cred = self._win32cred()
        credential_error = self._credential_error()
        try:
            credential = win32cred.CredRead(
                self.target_name,
                win32cred.CRED_TYPE_GENERIC,
                0,
            )
        except credential_error as error:
            if error.winerror == 1168:
                return None
            raise RuntimeError(f"Could not read the Windows credential: {error}") from error
        blob = credential.get("CredentialBlob", b"")
        if isinstance(blob, bytes):
            return blob.decode("utf-16-le")
        return str(blob)

    def set_refresh_token(self, refresh_token: str) -> None:
        token = _validate_refresh_token(refresh_token)
        win32cred = self._win32cred()
        credential_error = self._credential_error()
        try:
            win32cred.CredWrite(
                {
                    "Type": win32cred.CRED_TYPE_GENERIC,
                    "TargetName": self.target_name,
                    "CredentialBlob": token,
                    "Persist": win32cred.CRED_PERSIST_LOCAL_MACHINE,
                    "UserName": "Spotify OAuth refresh token",
                    "Comment": "Managed by Voice Control USB",
                },
                0,
            )
        except credential_error as error:
            raise RuntimeError(f"Could not save the Windows credential: {error}") from error

    def delete_refresh_token(self) -> bool:
        win32cred = self._win32cred()
        credential_error = self._credential_error()
        try:
            win32cred.CredDelete(
                self.target_name,
                win32cred.CRED_TYPE_GENERIC,
                0,
            )
        except credential_error as error:
            if error.winerror == 1168:
                return False
            raise RuntimeError(f"Could not delete the Windows credential: {error}") from error
        return True

    @staticmethod
    def _win32cred():
        try:
            import win32cred
        except ImportError as error:
            raise ImportError(
                "Windows Credential Manager support requires pywin32. Install the "
                "project with 'pip install .[windows]'."
            ) from error
        return win32cred

    @staticmethod
    def _credential_error():
        try:
            import pywintypes
        except ImportError as error:
            raise ImportError(
                "Windows Credential Manager support requires pywin32. Install the "
                "project with 'pip install .[windows]'."
            ) from error
        return pywintypes.error


def _validate_refresh_token(refresh_token: str) -> str:
    token = refresh_token.strip()
    if not token:
        raise ValueError("Spotify refresh token must not be empty.")
    return token
