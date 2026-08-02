# Phase 7 Baseline

## Delivered

- Native PyInstaller builds for the assistant and local starter.
- Immutable USB release directories selected by an atomic active pointer.
- Host-pinned USB UUID and Ed25519 release public key.
- Signed release ID, USB ID, entry point, file sizes, and SHA-256 hashes.
- Direct visible-window launch resolved entirely from the detected USB root.
- Windows-native live-PID duplicate protection across both assistant and restarted starter processes.
- Cooperative shutdown and lock cleanup before USB removal.
- Double verification before update activation and explicit verified-release recovery.
- Regression handling for missing files, altered files, invalid signatures, changed drive paths, partial staging, broken pointers, stale locks, and shutdown timeout.

## Automated verification

```text
Ran 174 tests
OK (skipped=2)
```

The two skips are expected non-Windows compatibility checks. The suite includes signed-manifest tamper detection, atomic update behavior, recovery, portable path resolution, drive multi-string parsing, duplicate locks, and safe-removal behavior.

## Native Windows verification

- Built both real Windows executables with Python 3.14 and PyInstaller 6.21.
- Generated an ephemeral Ed25519 test key and verified the signed release.
- Confirmed Windows exposes `D:` as the healthy removable `VOICE-BOT` volume.
- Found and fixed the native multi-string drive-enumeration bug that initially hid drives after `C:`.
- Launched the signed packaged assistant through the packaged starter from the real `D:` USB root.
- Visually verified the packaged `Voice Control Assistant` window and native adapter subtitle.
- Verified packaged Windows media and Discord status calls.
- Found and fixed the Windows PID-probe bug that initially allowed a duplicate packaged instance.
- Re-ran the packaged duplicate test: the second process exited with code 3, the first exited normally, and the lock was removed.
- Ran packaged safe removal: the assistant window and both PyInstaller processes closed, with no lock or shutdown request remaining.
- Removed the temporary identity, active pointer, release, and runtime payload from the USB root after verification.

The test signing key and build outputs were temporary, ignored artifacts and are not part of the repository.
