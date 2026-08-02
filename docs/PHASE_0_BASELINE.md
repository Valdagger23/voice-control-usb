# Phase 0 Baseline

Recorded: 2026-08-02

## Repository

- Active location: `D:\VoiceControl`
- Branch: `main`
- Baseline commit: `3f1977c14587d9fd464d40c8a4eea1b4be74e413`
- Remote: `git@github.com:Valdagger23/voice-control-usb.git`
- Git history was preserved from the clean WSL source repository.

## Development environment

- Windows Python: 3.14.5
- Project environment: `D:\VoiceControl\.venv`
- Package installed in editable mode from the USB repository.
- `.gitattributes` now records cross-platform line-ending expectations.

## Verification

Command:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Result:

- 95 tests completed successfully: 93 passed and 2 were skipped.
- The skipped tests mark live Windows desktop and Excel COM selection for manual verification.
- A test that assumed the POSIX-only `/tmp` directory was changed to use a platform-neutral temporary directory. Runtime behavior was not changed.

## Phase 0 documentation

- Product vision updated for a broad Windows assistant with Excel first.
- MVP narrowed to the initial Excel vertical slice.
- Target capability-based architecture documented.
- Media/Spotify, browser/Google, and Discord phases recorded.
- Messaging, microphone, camera, credential, and self-bot safety rules recorded.

## Outstanding native checks

These are intentionally deferred to their implementation phases:

- live Excel COM behavior against Microsoft Excel
- live microphone capture and push-to-talk
- Windows media-session and Spotify behavior
- browser navigation integration
- Discord state inspection and visible confirmed messaging
- packaged starter behavior with the physical USB under changing drive letters

## Next phase

Phase 1 generalizes the deterministic runtime into a capability-neutral contract while preserving existing visible behavior and the full baseline suite.
