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

## Local verification
- `PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v`
- `PYTHONPATH=src .venv/bin/python -m voice_control_usb "open excel"`
- `PYTHONPATH=src .venv/bin/python -m voice_control_usb "go to A123"`

## Windows COM verification
- `python -m pip install pywin32`
- `set PYTHONPATH=src`
- `python -m voice_control_usb --excel-adapter com "open excel"`
- `python -m voice_control_usb --excel-adapter com "go to A123"`
