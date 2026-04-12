# Desktop Actions

## Overview
Desktop actions are routed through a dedicated `DesktopAdapter` boundary.
The deterministic runtime currently supports only a narrow, approved set of actions:

- `open app <ALIAS>`
- `open url <URL>`
- `open folder <PATH>`

These commands use the same command registry, parser, executor, session, and speech pipeline as the Excel commands.

## App alias allowlist
Applications are launched only through the packaged allowlist in:

- `src/voice_control_usb/desktop/app_aliases.json`

Current aliases:
- `notepad`
- `calculator`
- `explorer`

The runtime does not accept arbitrary desktop executables or shell commands.

## Runtime behavior

### Stub desktop adapter
Default for WSL and tests.
It validates actions and returns deterministic responses without launching anything.

### Windows desktop adapter
Windows-only implementation.
It launches allowlisted apps with `subprocess.Popen(..., shell=False)` and opens URLs or folders with `os.startfile`.

## Safety boundaries
Explicitly not supported in MVP:
- shutdown
- restart
- kill process
- arbitrary command execution

These risky actions are parsed into explicit deterministic rejections such as:
- `Desktop action is not approved in MVP: shutdown`

Actions outside the approved grammar still flow into unsupported-command proposal logging.

## Verification
WSL:

```bash
PYTHONPATH=src .venv/bin/python -m voice_control_usb "open app notepad"
PYTHONPATH=src .venv/bin/python -m voice_control_usb "open url https://example.com"
PYTHONPATH=src .venv/bin/python -m voice_control_usb "open folder /tmp"
PYTHONPATH=src .venv/bin/python -m voice_control_usb "shutdown"
```

Windows:

```powershell
$env:PYTHONPATH = "src"
python -m voice_control_usb --desktop-adapter windows "open app notepad"
python -m voice_control_usb --desktop-adapter windows "open url https://example.com"
python -m voice_control_usb --desktop-adapter windows "open folder C:\Users"
python -m voice_control_usb --desktop-adapter windows "shutdown"
```
