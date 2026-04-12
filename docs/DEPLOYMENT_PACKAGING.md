# Deployment Packaging

## Goal
Prepare two separate Windows binaries:

- a USB-hosted assistant executable
- a laptop-installed starter executable

The starter remains local to each prepared laptop.
The assistant remains portable on the trusted USB.

## Expected packaged layout

### USB layout
The trusted USB should contain the packaged assistant at:

```text
<USB_ROOT>\
  voice-control-usb.trusted
  dist\
    voice-control-usb-assistant\
      voice-control-usb-assistant.exe
```

This path matches the default starter config field:

- `assistant_relative_executable = "dist/voice-control-usb-assistant/voice-control-usb-assistant.exe"`

### Prepared laptop layout
Recommended local starter install layout:

```text
C:\Program Files\voice-control-usb\
  voice-control-usb-starter.exe

C:\ProgramData\voice-control-usb\
  starter.json
  starter.log
```

## Building the Windows binaries
Use the packaging script from a native Windows environment:

```powershell
Set-Location C:\path\to\voice-control-usb
.\scripts\build_windows_binaries.ps1
```

The script:

- installs `pyinstaller`
- builds `voice-control-usb-assistant.exe`
- builds `voice-control-usb-starter.exe`
- copies the outputs into:
  - `dist\windows\assistant\voice-control-usb-assistant.exe`
  - `dist\windows\starter\voice-control-usb-starter.exe`

## Deploying the packaged assistant to USB
Copy the assistant binary to the trusted USB so the final path is:

```text
<USB_ROOT>\dist\voice-control-usb-assistant\voice-control-usb-assistant.exe
```

Also place the trust marker file in the USB root:

```text
<USB_ROOT>\voice-control-usb.trusted
```

Set the USB volume label to the configured expected label, for example `VOICEBOT`.

## Installing the starter on a prepared laptop
1. Copy `dist\windows\starter\voice-control-usb-starter.exe` to:
   `C:\Program Files\voice-control-usb\voice-control-usb-starter.exe`
2. Create `C:\ProgramData\voice-control-usb\starter.json`
3. Optionally create `C:\ProgramData\voice-control-usb\starter.log`
4. Register the starter at logon through Task Scheduler

Example starter config:

```json
{
  "expected_volume_label": "VOICEBOT",
  "trust_marker": "voice-control-usb.trusted",
  "assistant_relative_executable": "dist/voice-control-usb-assistant/voice-control-usb-assistant.exe",
  "assistant_workdir": ".",
  "poll_interval_seconds": 2.0,
  "log_path": "C:\\ProgramData\\voice-control-usb\\starter.log"
}
```

## Task Scheduler startup
You can register the starter manually in Task Scheduler or use:

```powershell
.\scripts\install_starter_task.ps1 `
  -StarterExe "C:\Program Files\voice-control-usb\voice-control-usb-starter.exe" `
  -ConfigPath "C:\ProgramData\voice-control-usb\starter.json"
```

This creates a logon task that runs the starter for the current machine.

## How the starter finds the assistant
On each scan:

1. enumerate removable drives
2. find drives whose volume label matches `expected_volume_label`
3. require the marker file in the USB root
4. resolve `<USB_ROOT>/<assistant_relative_executable>`
5. launch that executable with `shell=False`

If the packaged assistant file is missing, launch is skipped and the reason is logged.

## Native Windows verification still required
WSL tests cover launch-spec generation and packaged-path resolution.
Native Windows verification is still required for:

- real PyInstaller output
- real removable-drive discovery
- real Task Scheduler startup
- real packaged assistant launch from USB
