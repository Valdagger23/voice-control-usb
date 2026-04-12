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

## Controlled activation model
The current speech slice uses explicit manual activation.
In speech session mode, each line should be one activation request:

- `record open workbook /tmp/context.xlsx`
- `record select sheet Sheet2`
- `record go to A123`
- `record type pass`

`record` without any speech payload produces `No speech recognized.`

This keeps speech input opt-in and deterministic while the real audio capture layer is still stubbed.

## Provider boundary
Speech providers plug in through `SpeechTranscriber`.

Current provider:
- `stub`
  Manual text provider for WSL and tests. It treats `record ...` input as recognized speech.

Future real providers should:
- implement `SpeechTranscriber.transcribe`
- be created through `create_speech_transcriber`
- preserve the same contract of returning recognized text into the existing assistant pipeline

## What is still stubbed
- microphone capture
- real speech recognition engine integration
- device selection
- push-to-talk hotkeys
- streaming partial transcripts

## Verification
WSL example:

```bash
printf 'record open workbook /tmp/context.xlsx\nrecord select sheet Sheet2\nrecord report current sheet\nrecord go to A123\nrecord type pass\nquit\n' | PYTHONPATH=src .venv/bin/python -m voice_control_usb --session --input-mode speech
```

Expected behavior:
- each `record ...` line is echoed as `Recognized: ...`
- the recognized text is executed through the same assistant session flow
- workbook and sheet context persist across recognized commands
