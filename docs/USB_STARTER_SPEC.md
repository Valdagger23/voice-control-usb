# USB Starter Spec

## Purpose
The local starter is the laptop-resident deployment component.
It is separate from the USB-hosted assistant and has one narrow job:

- detect removable drives
- validate the trusted USB identity
- launch the assistant from the USB
- avoid duplicate launches
- log what happened

It does not rely on USB autorun.

## Prepared laptop setup
Each prepared Windows laptop needs a local starter config JSON file.
Minimum required fields:

- `expected_volume_label`
- `trust_marker`

Recommended fields:

- `assistant_python`
- `assistant_module`
- `assistant_pythonpath`
- `assistant_workdir`
- `poll_interval_seconds`
- `log_path`

Example:

```json
{
  "expected_volume_label": "VOICEBOT",
  "trust_marker": "voice-control-usb.trusted",
  "assistant_python": "python",
  "assistant_module": "voice_control_usb",
  "assistant_pythonpath": "src",
  "assistant_workdir": ".",
  "poll_interval_seconds": 2.0,
  "log_path": "C:\\ProgramData\\voice-control-usb\\starter.log"
}
```

## Trusted USB identity
The USB is trusted only when both checks pass:

1. the removable volume label exactly matches the configured `expected_volume_label`
2. the configured marker file exists in the USB root

Example trusted layout:

```text
E:\
  voice-control-usb.trusted
  src\
  docs\
  ...
```

If either the label or marker check fails, the starter does not launch anything.

## Launch behavior
When one trusted USB is detected, the starter builds a direct module launch:

- command: `<assistant_python> -m <assistant_module>`
- working directory: `<usb_root>/<assistant_workdir>`
- `PYTHONPATH`: prepended with `<usb_root>/<assistant_pythonpath>`

The launch path uses `subprocess.Popen(..., shell=False)` only.
No arbitrary shell command execution is used.

## Duplicate-launch prevention
The starter tracks the launched assistant process in memory.

- if the assistant is still running, the starter does not launch another copy
- if the tracked process has exited, the starter allows a fresh launch
- if more than one trusted USB is visible at once, launch is skipped to avoid ambiguity

## Watcher behavior
The starter can run:

- one scan cycle with `--once`
- a polling loop using `poll_interval_seconds`

The watcher remains intentionally small.
It does not attempt broader device management, desktop control, or assistant orchestration.

## Windows verification
The removable-drive watcher is Windows-only.
Verify on a prepared Windows laptop with a configured USB:

```powershell
$env:PYTHONPATH = "src"
python -m voice_control_usb.starter.cli --config C:\ProgramData\voice-control-usb\starter.json --once
```

Expected outcomes:

- trusted USB present: `Launched assistant from trusted USB: <drive>`
- trusted USB already running: `Assistant already running from <drive>.`
- no trusted USB: `Trusted USB not detected.`
- ambiguous trusted USBs: `Multiple trusted USB volumes detected. Launch skipped.`

## WSL development status
WSL tests cover:

- JSON config parsing
- USB label and marker validation
- duplicate-launch prevention
- relaunch after process exit

WSL does not verify live removable-drive discovery on Windows.
That part still requires native Windows testing.
