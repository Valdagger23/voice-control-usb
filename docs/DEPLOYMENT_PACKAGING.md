# Deployment and Packaging

## Release model

Voice Control uses two Windows executables:

- a laptop-installed starter that detects and verifies the USB
- a signed, immutable assistant release stored on the USB

The private Ed25519 signing key stays with the release operator and must never be copied to the USB or a prepared laptop. Each laptop stores only the public key, expected USB UUID, and expected volume label.

## USB layout

```text
<USB_ROOT>\
  voice-control-usb.identity.json
  active-release.json
  releases\
    <RELEASE_ID>\
      manifest.json
      manifest.sig
      assistant\
        voice-control-usb-assistant.exe
  runtime\
```

The signed manifest binds the release ID and USB ID to the entry point and the SHA-256 hash and size of every release file. The active pointer selects one already-complete immutable release.

## First-time signing setup

Generate the signing key pair outside the repository and retain a secure backup of the private key:

```powershell
.\.venv\Scripts\python.exe scripts\release_tool.py generate-key `
  --private-key C:\secure\voice-control-signing-key.pem `
  --public-key C:\secure\voice-control-public-key.txt
```

Copy the base64 public-key value into each laptop's local `starter.json`. Do not copy the private key to the USB.

## Build a signed Windows release

Use one permanent UUID for the physical USB and a new release ID for each build:

```powershell
.\scripts\build_windows_binaries.ps1 `
  -Python .\.venv\Scripts\python.exe `
  -UsbId "<PERMANENT-USB-UUID>" `
  -ReleaseId "0.1.0" `
  -SigningPrivateKeyPath "C:\secure\voice-control-signing-key.pem"
```

The script installs the Windows and packaging dependencies, builds both executables, bundles the deterministic registries and native adapter dependencies, signs the assistant release, and produces:

```text
dist\windows\starter\voice-control-usb-starter.exe
dist\windows\usb\...
```

Copy the contents of `dist\windows\usb` to the USB root. Install the starter executable under `C:\Program Files\voice-control-usb` on each prepared laptop.

## Laptop configuration

Create `C:\ProgramData\voice-control-usb\starter.json` from `config\starter.example.json`, replacing the label, UUID, and public key with the real values. The USB ID and public key are host-pinned; changing a drive letter does not change trust.

Register the starter at logon:

```powershell
.\scripts\install_starter_task.ps1 `
  -StarterExe "C:\Program Files\voice-control-usb\voice-control-usb-starter.exe" `
  -ConfigPath "C:\ProgramData\voice-control-usb\starter.json"
```

The scheduled task ignores duplicate task starts, runs without a three-day execution limit, and restarts after transient failure.

## Verified updates

Prepare a new signed release directory with `release_tool.py create`. Then activate it through the local starter:

```powershell
voice-control-usb-starter.exe `
  --config C:\ProgramData\voice-control-usb\starter.json `
  --activate-update E:\staged\0.2.0
```

The starter verifies the source, copies it to a unique staging directory on the USB, verifies the copied files again, renames the complete directory into `releases`, and atomically replaces `active-release.json`. The old release remains untouched. If copying or verification is interrupted, the previous pointer remains usable.

Recover a missing or broken active pointer to the highest named fully verified installed release:

```powershell
voice-control-usb-starter.exe --config C:\ProgramData\voice-control-usb\starter.json --recover
```

## Safe removal

Before ejecting the USB, run:

```powershell
voice-control-usb-starter.exe `
  --config C:\ProgramData\voice-control-usb\starter.json `
  --prepare-removal
```

The assistant consumes the cooperative stop request, closes its visible window, releases its runtime lock, and reports when the USB is ready. If shutdown times out, do not remove the USB.

## Verification checklist

1. Run `python -m unittest discover -s tests -q`.
2. Verify the release with `release_tool.py verify` and the host public key.
3. Run the packaged starter with `--once` while the physical USB is connected.
4. Confirm the visible assistant window opens from the detected drive root.
5. Run a second `--once` and confirm it reports the existing instance.
6. Run `--prepare-removal` and confirm the window, process, `assistant.lock`, and `shutdown.request` are gone.
7. Change the USB drive letter and repeat; no configuration path should change.
