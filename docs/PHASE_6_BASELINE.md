# Phase 6 Baseline

## Outcome

Phase 6 adds deliberate Discord navigation, drafting, and state-aware privacy controls without user-account APIs or automated message submission.

## Delivered behavior

- Visible Discord launch with renderer accessibility enabled.
- Allowlisted server/channel and DM navigation through configured aliases.
- One visible draft with edit and cancel support.
- Confirmed send preparation verifies the draft is unchanged and focuses it; physical Enter is still required.
- Readable microphone and deafen state plus state-setting actions.
- Camera state and actions only when controls are exposed in the current call view.
- Immediate mute, deafen, and camera-disable actions.
- Confirmed unmute, undeafen, and camera-enable actions.
- Explicitly blocked user-token and bulk-message command forms.

## Verification completed

- Automated suite: 162 completed; 160 passed and 2 expected native-adapter guard checks skipped.
- Native Discord accessibility reported microphone unmuted and deafen off.
- Camera state correctly reported unknown outside a call.
- Reapplying current microphone and deafen state changed nothing.
- No message was drafted or sent during native verification.

## Run Phase 6

```powershell
.\.venv\Scripts\python.exe -m voice_control_usb --window
.\.venv\Scripts\python.exe scripts\verify_windows_discord.py
```
