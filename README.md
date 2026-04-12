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

## Desktop adapter selection
- Default: stub adapter for WSL/dev and tests
- Windows desktop adapter: `--desktop-adapter windows`
- Env override: `VOICE_CONTROL_USB_DESKTOP_ADAPTER=stub|windows`
- Details: [docs/DESKTOP_ACTIONS.md](docs/DESKTOP_ACTIONS.md)

## Runtime modes
- One-shot mode: runs one command and exits
- Session mode: `--session` keeps one assistant process alive and preserves Excel context across commands
- Speech session mode: `--session --input-mode speech` accepts controlled `record ...` activations and routes recognized text into the same assistant pipeline
- Push-to-talk speech mode: `--session --input-mode speech --speech-activation ptt` uses Enter as the recording trigger in terminal sessions

## Workflows
- Approved multi-step macros are registry-driven
- Workflow phrases expand into existing deterministic actions only
- Details: [docs/WORKFLOWS.md](docs/WORKFLOWS.md)

## Local verification
- `PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v`
- `PYTHONPATH=src .venv/bin/python -m voice_control_usb "open excel"`
- `PYTHONPATH=src .venv/bin/python -m voice_control_usb "open excel and go to A1"`
- `printf 'go to A5\nmark fail and next row\nquit\n' | PYTHONPATH=src .venv/bin/python -m voice_control_usb --session`
- `PYTHONPATH=src .venv/bin/python -m voice_control_usb "go to A123"`
- `PYTHONPATH=src .venv/bin/python -m voice_control_usb "open app notepad"`
- `PYTHONPATH=src .venv/bin/python -m voice_control_usb "open url https://example.com"`
- `PYTHONPATH=src .venv/bin/python -m voice_control_usb "open folder /tmp"`
- `PYTHONPATH=src .venv/bin/python -m voice_control_usb "shutdown"`
- `printf 'open workbook /tmp/context.xlsx\nselect sheet Sheet2\ngo to A123\ntype pass\nreport current sheet\nquit\n' | PYTHONPATH=src .venv/bin/python -m voice_control_usb --session`
- `printf 'record open workbook /tmp/context.xlsx\nrecord select sheet Sheet2\nrecord go to A123\nrecord type pass\nquit\n' | PYTHONPATH=src .venv/bin/python -m voice_control_usb --session --input-mode speech`
- `printf '\nopen workbook /tmp/context.xlsx\n\nselect sheet Sheet2\n\nreport current sheet\nquit\n' | PYTHONPATH=src .venv/bin/python -m voice_control_usb --session --input-mode speech --speech-activation ptt`

## Windows COM verification
- `python -m pip install pywin32`
- `set PYTHONPATH=src`
- `python -m voice_control_usb --excel-adapter com "open excel"`
- `python -m voice_control_usb --excel-adapter com "go to A123"`
- `python -m voice_control_usb --desktop-adapter windows "open app notepad"`
- `python -m voice_control_usb --desktop-adapter windows "open url https://example.com"`
- Session mode is available with `python -m voice_control_usb --excel-adapter com --session`
- Speech session mode is available with `python -m voice_control_usb --excel-adapter com --session --input-mode speech`

## Speech input
- Controlled activation only for now: manual `record ...` lines in speech session mode
- Default speech provider: stub/manual for WSL and tests
- First real provider: `speech_recognition`
- Speech activation modes: `manual` and `ptt`
- Future providers plug in through `SpeechTranscriber` and `create_speech_transcriber`
- Future triggers plug in through `SpeechActivator` and `create_speech_activator`
- Details: [docs/SPEECH_INPUT.md](docs/SPEECH_INPUT.md)
