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

## Local verification
- `PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v`
- `PYTHONPATH=src .venv/bin/python -m voice_control_usb "open excel"`
