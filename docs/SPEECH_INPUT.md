# Speech Input

## Overview
Speech input is a controlled runtime boundary that feeds recognized text into the same assistant command pipeline used by typed sessions.

Current design goals:
- deterministic command handling stays unchanged
- no wake word
- no always-listening background mode
- no LLM interpretation layer
- explicit user activation before each speech transcription

## Runtime modes

### One-shot mode
Runs one typed command and exits.

Example:
- `PYTHONPATH=src .venv/bin/python -m voice_control_usb "open excel"`

### Typed session mode
Keeps one assistant process alive and accepts one typed command per line.
Workbook, worksheet, cell, and anchor state persist across lines in that session.

Example:
- `PYTHONPATH=src .venv/bin/python -m voice_control_usb --session`

### Speech session mode
Keeps one assistant process alive and accepts one manual speech activation per line.
Each activation is transcribed first, then the recognized text is passed into `AssistantApp.handle_text`.

Example:
- `PYTHONPATH=src .venv/bin/python -m voice_control_usb --session --input-mode speech`

### Push-to-talk speech mode
Keeps one assistant process alive and uses a controlled trigger before each transcription.
The first terminal trigger is `Enter` in `--speech-activation ptt` mode.

Example:
- `PYTHONPATH=src .venv/bin/python -m voice_control_usb --session --input-mode speech --speech-activation ptt`

## Controlled activation model
The current speech slice uses explicit manual activation.
In speech session mode, each line should be one activation request:

- `record open workbook /tmp/context.xlsx`
- `record select sheet Sheet2`
- `record go to A123`
- `record type pass`

`record` without any speech payload produces `No speech recognized.`

This keeps speech input opt-in and deterministic while the real audio capture layer is still stubbed.

Push-to-talk mode keeps activation explicit too:
- press `Enter` to start one recording cycle
- recognition stops automatically when the provider reaches silence or phrase limits
- the recognized text is dispatched through the normal assistant command path

With the stub provider in WSL/tests:
- pressing `Enter` starts a simulated recording cycle
- the next line is treated as the recognized transcript

## Provider boundary
Speech providers plug in through `SpeechTranscriber`.

Current provider:
- `stub`
  Manual text provider for WSL and tests. It treats `record ...` input as recognized speech.
- `speech_recognition`
  First real provider. It uses the Python `SpeechRecognition` package with explicit microphone capture and `recognize_google`.

Future real providers should:
- implement `SpeechTranscriber.transcribe`
- be created through `create_speech_transcriber`
- preserve the same contract of returning recognized text into the existing assistant pipeline

Speech activation controls plug in through `SpeechActivator`.

Current activators:
- `manual`
  Existing `record ...` line-based activation.
- `ptt`
  Push-to-talk activation for terminal sessions. Today it uses `Enter` as the trigger.

Future Windows hotkey-based triggers should plug in through `SpeechActivator` without changing the parser or executor.

## Real provider mode
Select the first real provider explicitly:

- `PYTHONPATH=src python -m voice_control_usb --session --input-mode speech --speech-provider speech_recognition`
- `PYTHONPATH=src python -m voice_control_usb --session --input-mode speech --speech-provider speech_recognition --speech-activation ptt`

Activation remains controlled:
- `record`
- `record 7`

`record` captures one utterance using the default phrase time limit.
`record 7` captures one utterance with a `7` second phrase time limit.

## Dependencies and setup
Install the first real provider with:

- `pip install SpeechRecognition`

Or:

- `pip install .[speech]`

Microphone capture may also require a supported backend such as `PyAudio`, depending on the operating system and audio stack.

If dependencies or microphone support are unavailable:
- provider selection fails cleanly when `SpeechRecognition` is missing
- runtime capture failures are reported in-session without crashing the assistant

## Limitations of the first real provider
- requires explicit `record` activation each time
- push-to-talk currently stops by phrase timeout or silence rather than a second keypress
- uses a network-backed recognizer path through `recognize_google`
- depends on local microphone/backend support
- does not provide streaming transcripts
- does not provide wake word or continuous listening

## What is still stubbed
- microphone capture
- device selection
- push-to-talk hotkeys
- streaming partial transcripts

With the `speech_recognition` provider selected, only the microphone capture and recognition call are real. The activation model and the rest of the command pipeline remain deterministic and unchanged.

## Verification
WSL example:

```bash
printf 'record open workbook /tmp/context.xlsx\nrecord select sheet Sheet2\nrecord report current sheet\nrecord go to A123\nrecord type pass\nquit\n' | PYTHONPATH=src .venv/bin/python -m voice_control_usb --session --input-mode speech
printf '\nopen workbook /tmp/context.xlsx\n\nselect sheet Sheet2\n\nreport current sheet\nquit\n' | PYTHONPATH=src .venv/bin/python -m voice_control_usb --session --input-mode speech --speech-activation ptt
```

Expected behavior:
- each `record ...` line is echoed as `Recognized: ...`
- the recognized text is executed through the same assistant session flow
- workbook and sheet context persist across recognized commands
- push-to-talk mode does the same, but uses Enter as the activation trigger and the next line as simulated speech for the stub provider

Real provider example on a machine with microphone support:

```bash
PYTHONPATH=src python -m voice_control_usb --session --input-mode speech --speech-provider speech_recognition
PYTHONPATH=src python -m voice_control_usb --session --input-mode speech --speech-provider speech_recognition --speech-activation ptt
```

Then enter:
- `record`
- `record 7`
- `quit`

For push-to-talk mode, press `Enter` to start each recording cycle and `quit` to leave the session.
