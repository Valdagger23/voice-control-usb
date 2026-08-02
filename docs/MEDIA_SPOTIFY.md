# Media and Spotify

## Native media behavior

The Windows media adapter controls whichever media session Windows currently considers active. This works with Spotify and supported browser players without requiring a Spotify account connection.

Supported commands:

```text
play music
pause music
next track
previous track
mute speakers
unmute speakers
set volume to 40 percent
report volume
now playing
```

Playback and now-playing use Windows Global System Media Transport Controls. Volume and mute use the default Windows playback endpoint. If no compatible player is active, the assistant reports that no controllable media session exists and executes nothing.

The deterministic stub remains the default for tests and one-shot development commands. Select native media explicitly with:

```powershell
.\.venv\Scripts\python.exe -m voice_control_usb --media-adapter windows "now playing"
```

The visible Windows assistant selects the native adapter automatically.

## Optional Spotify account connection

Ordinary control of the local Spotify app does not need OAuth. Account authorization is reserved for later Spotify Connect features that need the Web API.

To prepare it:

1. Create a Spotify developer app.
2. Add the exact redirect URI `http://127.0.0.1:8765/callback` to that app.
3. Put the non-secret client ID in `VOICE_CONTROL_USB_SPOTIFY_CLIENT_ID`.
4. Run `--spotify-connect` and approve the playback scopes in the browser.

```powershell
$env:VOICE_CONTROL_USB_SPOTIFY_CLIENT_ID = "your-client-id"
.\.venv\Scripts\python.exe -m voice_control_usb --spotify-connect
.\.venv\Scripts\python.exe -m voice_control_usb --spotify-status
```

The desktop flow uses Authorization Code with PKCE, so it does not use or store a Spotify client secret. It requests only `user-read-playback-state` and `user-modify-playback-state`. The access token remains in memory; the refresh token is stored under the current Windows user in Credential Manager.

Remove that credential with:

```powershell
.\.venv\Scripts\python.exe -m voice_control_usb --spotify-disconnect
```

Spotify developer-mode and Web API playback availability can depend on the account and current Spotify platform rules. Native Windows playback remains the default path.

## Native verification

Start playback in Spotify or a supported browser, then run:

```powershell
.\.venv\Scripts\python.exe scripts\verify_windows_media.py --exercise-play-pause
```

The verification reads the current session, sets speaker controls to their existing values, briefly exercises play/pause, restores the original state, writes a temporary test credential, and removes it.
