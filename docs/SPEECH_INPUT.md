# Speech Input

## Phase 3 outcome

Speech input is a controlled boundary in front of the same deterministic command pipeline used by typed input. On native Windows, the assistant provides a microphone selector, an on-screen `Push to talk` button, and one user-assigned global keyboard key or mouse button. There is no wake word or unattended activation.

## Default Windows provider

The default native provider is `windows_sapi`. It uses the installed Microsoft Speech API recognizer through pywin32:

- recognition runs locally through the installed Windows speech engine
- the system-default microphone is used unless the user chooses another listed input
- capture ends after a recognition event or the eight-second safety timeout
- captured audio is not saved by the assistant
- the provider returns a structured `recognized`, `silence`, or `ambiguous` result

Microsoft documents that SAPI recognition contexts deliver successful and false-recognition events separately, and that audio inputs can be enumerated through the recognizer. The implementation uses those event types as the deterministic execute/reject boundary:

- [SAPI recognition event](https://learn.microsoft.com/en-us/previous-versions/windows/desktop/ms722027%28v%3Dvs.85%29)
- [SAPI false-recognition event](https://learn.microsoft.com/en-us/previous-versions/windows/desktop/ms722020%28v%3Dvs.85%29)
- [SAPI audio input enumeration](https://learn.microsoft.com/en-us/previous-versions/windows/desktop/ms722065%28v%3Dvs.85%29)

## Visible Windows workflow

Run from `D:\VoiceControl`:

```powershell
.\.venv\Scripts\python.exe -m voice_control_usb --window
```

Then:

1. Select `System default` or one of the listed microphones.
2. Press `Push to talk`.
3. Speak one supported command.
4. Wait for the transcript, optional interpretation, and assistant response.

## Global keyboard and mouse activation

Select `CONTROL` beside the microphone picker, then:

1. Select `CAPTURE KEY / MOUSE`.
2. Press the keyboard key or mouse button you want to assign.
3. Choose `PUSH TO TALK` or `TOGGLE LISTENING`.
4. Enable global control and save.

`PUSH TO TALK` starts capture on press and requests an early stop on release. `TOGGLE LISTENING` starts an explicit loop of bounded capture cycles; press the same input again, select `STOP LISTENING`, or say `stop listening` to end it. The global listener observes the selected input but does not block it from the foreground application.

The setting is stored alongside the USB runtime in `global-controls.json`, so it follows the prepared Voice Control USB. The notification-area menu also shows the assigned input and current listening state.

The UI remains responsive during capture. The button and typed command field are temporarily disabled so two commands cannot race each other. Typed input remains available after every capture.

## Speech decision flow

Only a `recognized` result is allowed to reach the parser.

- `silence`: displays `No speech recognized.` and executes nothing.
- `ambiguous`: displays the best match for review and executes nothing.
- provider or microphone failure: displays a clear error and executes nothing.
- recognized but unsupported phrase: uses the normal unsupported-command proposal flow.
- recognized supported phrase: uses the normal parser, safety policy, capability registry, executor, and audit flow.

Silence, ambiguity, and provider failures are also written to the audit store even though they never become commands.

## Visible speech normalization

SAPI dictation may return common spoken forms such as `Go to a one` for cell `A1`, or the homophone `And you're 42` for `enter 42`. Phase 3 applies only a small explicit normalization table for these command forms.

When normalization changes the text, the window shows both:

- `Voice`: the raw recognized transcript
- `Interpretation`: the deterministic command passed to the parser

The change is also audited. Unknown phrases are not broadly rewritten or guessed.

Currently normalized forms include:

- cell columns A-E, including Alpha, Bravo, Charlie, Delta, and Echo
- cell rows one through ten or a numeric row token
- `and you're <VALUE>` / `and your <VALUE>` to `enter <VALUE>`
- `save a workbook` to `save workbook`

## Terminal push-to-talk

The terminal session keeps the existing Enter-to-record activation:

```powershell
.\.venv\Scripts\python.exe -m voice_control_usb --session --input-mode speech --speech-activation ptt
```

On Windows, `auto` chooses `windows_sapi`. Press Enter to start one capture cycle and type `quit` to leave the session.

Select a microphone explicitly with its exact displayed name:

```powershell
.\.venv\Scripts\python.exe -m voice_control_usb --session --input-mode speech --speech-activation ptt --microphone "Headset Microphone (Razer Audio Controller - Chat)"
```

The equivalent environment setting is `VOICE_CONTROL_USB_MICROPHONE`.

## Other providers

- `stub`: manual text provider used by deterministic tests and non-Windows development.
- `windows_sapi`: native offline Windows provider and Windows `auto` default.
- `speech_recognition`: optional legacy provider using the SpeechRecognition package and its Google recognition path.

Explicit provider examples:

```powershell
.\.venv\Scripts\python.exe -m voice_control_usb --window --speech-provider windows_sapi
.\.venv\Scripts\python.exe -m voice_control_usb --window --speech-provider stub
.\.venv\Scripts\python.exe -m voice_control_usb --session --input-mode speech --speech-provider speech_recognition
```

There is still no wake word, unattended startup of listening, streaming transcript, or AI command guessing. Toggle listening is always started and stopped explicitly by the configured user input.

## Verification

Automated suite:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Native offline verification:

```powershell
.\.venv\Scripts\python.exe scripts\verify_windows_speech.py
```

The native check:

- enumerates SAPI microphone inputs
- opens the default microphone for a one-second capture probe without saving audio
- synthesizes temporary local WAV phrases through Windows SAPI
- recognizes those phrases through the offline provider
- routes them through speech normalization, the normal assistant pipeline, and an isolated real Excel workbook
- verifies `open excel`, `go to A1`, `enter 42`, `report current cell`, and `save workbook`
- removes the temporary audio and runtime files afterward
