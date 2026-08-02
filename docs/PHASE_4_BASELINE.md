# Phase 4 Baseline

## Outcome

Phase 4 delivers the first non-Excel capability through the same deterministic parser, safety policy, capability registry, structured results, audit history, typed input, and push-to-talk path.

## Delivered behavior

- Native Windows current-session play, pause, next, previous, and now-playing operations.
- Native default speaker mute, unmute, set-volume, and volume-reporting operations.
- Explicit media action contracts and a deterministic in-memory stub.
- Clear failure when no compatible Windows media session is active.
- Structured track, source-app, playback, volume, mute, and device details in action results and audit events.
- Optional Spotify Authorization Code with PKCE connection flow.
- Playback-only Spotify scopes and refresh-token rotation support.
- Windows Credential Manager persistence for the refresh token; access tokens remain in memory.
- Legacy Windows console output protection for media titles containing Unicode characters.

## Safety and privacy boundary

- No media-key simulation or arbitrary input injection.
- No Spotify client secret is used by the desktop app.
- No account token is written to repository files, USB runtime files, logs, or console output.
- Spotify authorization is user-initiated and separate from ordinary local playback control.
- Mute and volume commands set explicit desired state.
- Unsupported phrases still enter the reviewed proposal flow.

## Verification completed

- Automated suite: 148 completed after the Phase 4 additions; 146 passed and 2 expected native-adapter guard checks skipped.
- The native adapter identified the default NVIDIA playback endpoint and preserved its existing volume and mute state.
- Windows reported the active Chrome media session and its current track metadata.
- Native pause and play succeeded, and the verification restored the original playback state.
- A temporary generic credential completed a Windows Credential Manager round-trip and was removed.
- One-shot `now playing`, `report volume`, and Spotify account status commands were exercised on Windows.

## Run Phase 4

```powershell
cd D:\VoiceControl
.\.venv\Scripts\python.exe -m pip install -e ".[windows]"
.\.venv\Scripts\python.exe -m voice_control_usb --window
```

Useful first phrases:

```text
now playing
pause music
play music
next track
set volume to 40 percent
mute speakers
unmute speakers
```
