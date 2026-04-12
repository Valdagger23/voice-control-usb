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
Allowed immediately:
- `open app <ALIAS>`
- `open url <URL>`
- `open folder <PATH>`

Requires confirmation:
- `shutdown`
- `restart`

Blocked in MVP:
- `kill process <NAME>`
- `run command <TEXT>`

One-shot behavior:
- `shutdown` and `restart` return a `[CONFIRMATION REQUIRED]` response and do not execute.
- `status` reports that no pending confirmation action exists in one-shot mode.

Session behavior:
- `shutdown` and `restart` create a pending action.
- `status` reports the currently queued risky action.
- `confirm` executes the pending action.
- `cancel` drops the pending action.
- Optional pending-action timeout support exists in the assistant flow, but it is disabled by default.

Blocked examples:
- `Desktop action is blocked in MVP: dir`

Actions outside the approved grammar still flow into unsupported-command proposal logging.

## Verification
WSL:

```bash
PYTHONPATH=src .venv/bin/python -m voice_control_usb "open app notepad"
PYTHONPATH=src .venv/bin/python -m voice_control_usb "open url https://example.com"
PYTHONPATH=src .venv/bin/python -m voice_control_usb "open folder /tmp"
PYTHONPATH=src .venv/bin/python -m voice_control_usb "shutdown"
PYTHONPATH=src .venv/bin/python -m voice_control_usb "status"
printf 'shutdown\nconfirm\nquit\n' | PYTHONPATH=src .venv/bin/python -m voice_control_usb --session
printf 'shutdown\nstatus\nquit\n' | PYTHONPATH=src .venv/bin/python -m voice_control_usb --session
```

Windows:

```powershell
$env:PYTHONPATH = "src"
python -m voice_control_usb --desktop-adapter windows "open app notepad"
python -m voice_control_usb --desktop-adapter windows "open url https://example.com"
python -m voice_control_usb --desktop-adapter windows "open folder C:\Users"
python -m voice_control_usb --desktop-adapter windows "shutdown"
@"
shutdown
confirm
quit
"@ | python -m voice_control_usb --desktop-adapter windows --session
```
