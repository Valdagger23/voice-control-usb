# Phase 3 Baseline

## Outcome

Phase 3 places controlled offline speech in front of the proven typed Excel pipeline. The visible Windows assistant can now complete the basic Excel vertical slice through one push-activated utterance at a time while retaining typed input.

## Delivered behavior

- Offline `windows_sapi` provider using the installed Microsoft English recognizer through pywin32.
- Windows `auto` provider selection chooses SAPI; non-Windows development remains on the manual stub.
- Microphone enumeration, system-default selection, exact named-device selection, and clear missing-device failures.
- Non-blocking push-to-talk button in the visible Windows shell.
- Structured recognized, silence, and ambiguous transcription outcomes.
- Silence and ambiguous speech never reach command parsing or execution.
- Raw transcript and changed deterministic interpretation are both visible.
- Narrow normalization for common Excel cell and `enter` command recognition forms.
- Unsupported recognized phrases still use the existing reviewed proposal flow.
- Input rejection and provider failure outcomes are written to structured audit history.
- Existing terminal manual and Enter-to-record activation modes remain available.

## Safety and privacy boundary

- No wake word or always-listening process.
- No capture occurs until the user presses the button or terminal trigger.
- One capture ends on recognition or an eight-second timeout.
- The assistant does not persist captured microphone audio.
- Ambiguous and silent captures execute nothing.
- Speech normalization is narrow, visible, deterministic, and audited.
- All interpreted commands still pass through the existing parser and safety policy.

## Verification completed

- Automated suite: 130 completed; 128 passed and 2 expected platform guard checks skipped on Windows.
- Native SAPI verification detected three microphone inputs.
- The system-default microphone completed a one-second capture probe without saving audio.
- Offline synthesized speech successfully routed `open excel`, `go to A1`, `enter 42`, `report current cell`, and `save workbook` through the assistant pipeline and an isolated real Excel workbook.
- Temporary WAV and runtime files were removed after verification.

## Run Phase 3

```powershell
cd D:\VoiceControl
.\.venv\Scripts\python.exe -m pip install -e ".[windows]"
.\.venv\Scripts\python.exe -m voice_control_usb --window
```

Choose a microphone, press `Push to talk`, and speak one command. Useful first phrases:

```text
open excel
go to A one
enter forty two
report current cell
go right
type pass
undo last change
save workbook
```

Repeat the safe native verification with:

```powershell
.\.venv\Scripts\python.exe scripts\verify_windows_speech.py
```
