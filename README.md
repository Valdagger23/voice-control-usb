# voice-control-usb

Windows-first, USB-portable voice automation system with deterministic Excel control, modular command parsing, and a safe path for AI-assisted command expansion later.

## Phase 1 goal
Build the deterministic core:
- trusted local starter skeleton
- USB-hosted assistant shell
- strict parser
- executor
- Excel adapter boundary
- unsupported-command proposal logging
- tests

## Development environment
- WSL
- Python virtual environment
- VS Code
- Codex

## Excel adapter selection
- Default: stub adapter for WSL/dev and tests
- Windows COM adapter: `--excel-adapter com`
- Env override: `VOICE_CONTROL_USB_EXCEL_ADAPTER=stub|com`
- Details: [docs/EXCEL_ADAPTERS.md](docs/EXCEL_ADAPTERS.md)

## Runtime modes
- One-shot mode: runs one command and exits
- Session mode: `--session` keeps one assistant process alive and preserves Excel context across commands
- Speech session mode: `--session --input-mode speech` accepts controlled `record ...` activations and routes recognized text into the same assistant pipeline

## Local verification
- `PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v`
- `PYTHONPATH=src .venv/bin/python -m voice_control_usb "open excel"`
- `PYTHONPATH=src .venv/bin/python -m voice_control_usb "go to A123"`
- `printf 'open workbook /tmp/context.xlsx\nselect sheet Sheet2\ngo to A123\ntype pass\nreport current sheet\nquit\n' | PYTHONPATH=src .venv/bin/python -m voice_control_usb --session`
- `printf 'record open workbook /tmp/context.xlsx\nrecord select sheet Sheet2\nrecord go to A123\nrecord type pass\nquit\n' | PYTHONPATH=src .venv/bin/python -m voice_control_usb --session --input-mode speech`

## Windows COM verification
- `python -m pip install pywin32`
- `set PYTHONPATH=src`
- `python -m voice_control_usb --excel-adapter com "open excel"`
- `python -m voice_control_usb --excel-adapter com "go to A123"`
- Session mode is available with `python -m voice_control_usb --excel-adapter com --session`
- Speech session mode is available with `python -m voice_control_usb --excel-adapter com --session --input-mode speech`

## Speech input
- Controlled activation only for now: manual `record ...` lines in speech session mode
- Default speech provider: stub/manual for WSL and tests
- First real provider: `speech_recognition`
- Future providers plug in through `SpeechTranscriber` and `create_speech_transcriber`
- Details: [docs/SPEECH_INPUT.md](docs/SPEECH_INPUT.md)
