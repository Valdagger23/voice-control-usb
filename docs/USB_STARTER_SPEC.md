# Trusted USB Starter Specification

## Responsibility

The laptop-resident starter has a narrow role: enumerate removable drives, validate a host-pinned USB identity, verify a signed application release, prevent duplicate launch, start the visible assistant without a shell, coordinate safe shutdown, and activate only fully verified updates. It performs no assistant automation and does not use USB autorun.

## Trust checks

A payload can launch only when all checks pass:

1. Windows reports the drive as removable.
2. The volume label matches `expected_volume_label` case-insensitively.
3. `voice-control-usb.identity.json` contains the host-pinned UUID.
4. `active-release.json` contains a safe release ID.
5. The selected immutable release exists below `releases`.
6. Its Ed25519 signature verifies against the host-local public key.
7. Its manifest USB ID and release ID match the selected USB and directory.
8. Every declared file has the signed size and SHA-256 hash.
9. The signed entry point exists and remains inside its release directory.

Any missing, malformed, escaped, altered, ambiguous, or unverifiable path fails closed.

## Launch behavior

The starter resolves every path from the drive root returned by the current Windows scan. The launch is direct and uses `shell=False`:

```text
<SIGNED_ENTRYPOINT> --window --usb-root <USB_ROOT> --runtime-dir <USB_ROOT>\runtime
```

No fixed drive letter is stored. Runtime and environment paths are explicit.

## Duplicate protection and recovery

- A running watcher tracks its child process.
- A fresh watcher inspects the USB runtime lock before spawning.
- The assistant creates the lock atomically and records its PID.
- Windows PID liveness uses `OpenProcess`, not Unix signal-zero behavior.
- Stale locks with a valid dead PID are removed; malformed locks block launch until an operator confirms no assistant process is running and removes the lock.
- A process releases only a lock that still records its own PID.

## Safe shutdown

`--prepare-removal` verifies the host-pinned USB identity, writes `runtime\shutdown.request`, and waits for `assistant.lock` to disappear. It remains available even if the active release pointer is damaged. The visible shell polls for the request, closes, and releases the lock. A timeout warns the user not to remove the drive.

## Update behavior

`--activate-update <RELEASE_DIR>` verifies the source, copies it to a unique staging directory under the USB's releases directory, re-verifies the copy, renames it into its immutable final directory, then atomically replaces the active pointer. Old releases are retained. `--recover` ignores partial and corrupt directories, selects the highest named verified installed release, repairs the active pointer, and removes interrupted staging directories.

## Local configuration

Required fields:

- `expected_volume_label`
- `expected_usb_id`
- `manifest_public_key`

Optional fields:

- `identity_file`
- `active_release_file`
- `releases_dir`
- `poll_interval_seconds`
- `shutdown_timeout_seconds`
- `log_path`

The private release-signing key is never a starter configuration field.
