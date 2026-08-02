# VoiceControl

VoiceControl is a Windows-first, USB-portable voice assistant. The long-term product supports modular Windows capabilities; the first production capability is deliberately limited to reliable Microsoft Excel control.

## Project status

The planned Phase 0-7 roadmap is complete. Voice Control now combines the native Excel, speech, media, browser, and deliberate Discord slices with a verified USB deployment and recovery path.

- The existing deterministic prototype is preserved as the implementation baseline.
- Basic Excel control now works through typed input or controlled offline speech in the visible Windows shell.
- Discord launch, allowlisted navigation, visible drafts, and inspected device state now use Windows accessibility without user tokens or self-bot APIs.
- Existing user-visible command behavior is preserved behind capability-neutral contracts.
- Signed immutable releases, host-pinned USB identity, duplicate protection, safe removal, staged updates, and recovery are implemented and verified on the physical D: removable drive.

Planning documents:

- [Product vision](docs/PRODUCT_VISION.md)
- [MVP scope](docs/MVP.md)
- [Target architecture](docs/ARCHITECTURE.md)
- [Implementation plan](docs/IMPLEMENTATION_PLAN.md)
- [Safety model](docs/SAFETY.md)
- [Phase 0 baseline](docs/PHASE_0_BASELINE.md)
- [Phase 1 baseline](docs/PHASE_1_BASELINE.md)
- [Phase 2 baseline](docs/PHASE_2_BASELINE.md)
- [Phase 3 baseline](docs/PHASE_3_BASELINE.md)
- [Phase 4 baseline](docs/PHASE_4_BASELINE.md)
- [Phase 5 baseline](docs/PHASE_5_BASELINE.md)
- [Phase 6 baseline](docs/PHASE_6_BASELINE.md)
- [Phase 7 baseline](docs/PHASE_7_BASELINE.md)

## Existing prototype

The repository currently provides a tested deterministic foundation:
- trusted local starter skeleton
- USB-hosted assistant shell
- strict parser
- executor
- Excel adapter boundary
- unsupported-command proposal logging
- tests

Phase 1 additionally provides:

- typed capability action contracts and argument validation
- capability-owned Excel and desktop action declarations
- structured execution results
- capability-driven safety metadata
- application-neutral session context
- structured JSONL audit events at `runtime/audit/events.jsonl`

Phase 2 additionally provides:

- a visible Windows command window with transcript and execution status
- native Excel workbook, sheet, cell, entry, navigation, save, and reporting operations
- text, integer, decimal, `pass`, `fail`, and `N/A` cell entry
- four-way cell navigation and worksheet-boundary checks
- one-level undo for the most recent assistant-made cell edit
- clear missing-workbook, protected-sheet, invalid-cell, and lost-session failures

Phase 3 additionally provides:

- offline Windows SAPI recognition through the installed pywin32 dependency
- a non-blocking `Push to talk` button and microphone selector
- raw transcript, visible normalized interpretation, and execution status
- deterministic silence, ambiguity, unsupported-phrase, and provider-failure handling
- audit events for speech input that is rejected before command parsing
- typed input retained alongside speech for testing and accessibility

Phase 4 additionally provides:

- native play, pause, previous, next, and now-playing control through the current Windows media session
- explicit speaker mute, unmute, volume setting, and volume reporting through the default Windows playback endpoint
- deterministic media commands available through typed input and the existing push-to-talk path
- optional Spotify Authorization Code with PKCE setup using only playback scopes
- Spotify refresh-token storage in Windows Credential Manager; no token is written to the repository or USB runtime

Phase 5 additionally provides:

- a visible assistant-controlled Chrome or Edge session with its own persistent profile
- direct URL navigation, Google search, tabs, history, refresh, scrolling, and page identity reporting
- safe visible-link listing and numbered navigation without clicking page buttons or controls
- download links excluded and no form submission, purchase, or outgoing-message actions

Phase 6 additionally provides:

- visible Discord launch and allowlisted server/channel or DM navigation
- visible single-message drafting, editing, cancellation, and confirmed preparation
- physical Enter remains required to send; Voice Control never submits a normal user's message
- inspected Discord microphone and deafen state with privacy-reducing actions immediate and enabling actions confirmed
- camera actions only when Discord exposes reliable state in the current call view
- personal-token, self-bot, bulk-message, and background-message automation blocked

Phase 7 additionally provides:

- signed Ed25519 release manifests with complete file hashes and sizes
- a host-pinned USB UUID and public verification key
- immutable releases selected through an atomic active pointer
- portable launch from the currently detected drive root, never a fixed letter
- duplicate-instance protection using native Windows PID inspection
- cooperative assistant shutdown before USB removal
- staged double-verification, atomic activation, and verified-release recovery

## Development environment
- Active repository: `D:\VoiceControl`
- Windows Python 3.12 or newer in a project-local `.venv`
- WSL remains supported for deterministic stub-based tests when the USB is mounted there
- VS Code
- Codex

Windows setup:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[windows]"
```

## Trusted USB starter
- Local starter config is JSON-based and separate from the USB-hosted assistant
- Trust requires the expected removable-volume label, host-pinned USB UUID, signed manifest, and matching hash and size for every release file
- The starter launches a packaged assistant executable from the trusted USB with `shell=False`
- The starter passes `--window`, `--usb-root`, and `--runtime-dir` explicitly to the packaged assistant
- Duplicate launches are prevented by watcher tracking, pre-launch lock inspection, and the assistant's atomic runtime lock
- `--prepare-removal` cooperatively closes the assistant and waits for lock cleanup
- `--activate-update` verifies before and after staging, then atomically switches the active release; `--recover` repairs the pointer from verified releases
- Details: [docs/USB_STARTER_SPEC.md](docs/USB_STARTER_SPEC.md)
- Packaging details: [docs/DEPLOYMENT_PACKAGING.md](docs/DEPLOYMENT_PACKAGING.md)

## Excel adapter selection
- Default: stub adapter for WSL/dev and tests
- Windows COM adapter: `--excel-adapter com`
- Env override: `VOICE_CONTROL_USB_EXCEL_ADAPTER=stub|com`
- Details: [docs/EXCEL_ADAPTERS.md](docs/EXCEL_ADAPTERS.md)

## Desktop adapter selection
- Default: stub adapter for WSL/dev and tests
- Windows desktop adapter: `--desktop-adapter windows`
- Env override: `VOICE_CONTROL_USB_DESKTOP_ADAPTER=stub|windows`
- Details: [docs/DESKTOP_ACTIONS.md](docs/DESKTOP_ACTIONS.md)

## Media adapter selection

- Default: stub adapter for cross-platform development and tests
- Native Windows adapter: `--media-adapter windows`
- Visible Windows mode selects the native media adapter by default
- Environment override: `VOICE_CONTROL_USB_MEDIA_ADAPTER=stub|windows`
- Details and commands: [docs/MEDIA_SPOTIFY.md](docs/MEDIA_SPOTIFY.md)

## Runtime modes
- Visible Windows mode: `--window` opens typed and push-to-talk input, selecting native Excel COM and offline Windows speech by default
- One-shot mode: runs one command and exits
- Session mode: `--session` keeps one assistant process alive and preserves Excel context across commands
- Speech session mode: `--session --input-mode speech` accepts controlled `record ...` activations and routes recognized text into the same assistant pipeline
- Push-to-talk speech mode: `--session --input-mode speech --speech-activation ptt` uses Enter as the recording trigger in terminal sessions
- Safety flow: safe commands run immediately, risky commands raise a clear `[CONFIRMATION REQUIRED]` alert, `status` reports pending confirmation state, and blocked MVP actions still do not execute

## Browser adapter selection

- Default: deterministic stub for tests and cross-platform development
- Native visible adapter: `--browser-adapter playwright`
- Browser choice: `--browser-channel chrome|msedge`
- Visible Windows mode selects Playwright with Chrome by default
- Browser profile: `%LOCALAPPDATA%\VoiceControlUSB\browser-profile`, local to the prepared Windows host and separate from the USB and everyday browser profile
- Details: [docs/BROWSER_GOOGLE.md](docs/BROWSER_GOOGLE.md)

## Workflows
- Approved multi-step macros are registry-driven
- Workflow phrases expand into existing deterministic actions only
- Details: [docs/WORKFLOWS.md](docs/WORKFLOWS.md)

## Local verification

Windows baseline:

- `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`
- `.\.venv\Scripts\python.exe scripts\verify_excel_com.py`
- `.\.venv\Scripts\python.exe scripts\verify_windows_speech.py`
- `.\.venv\Scripts\python.exe scripts\verify_windows_media.py --exercise-play-pause`
- `.\.venv\Scripts\python.exe scripts\verify_windows_browser.py`
- `.\.venv\Scripts\python.exe -m voice_control_usb --window`
- `.\.venv\Scripts\python.exe -m voice_control_usb "open excel"`
- `.\.venv\Scripts\python.exe -m voice_control_usb "open excel and go to A1"`
- `.\.venv\Scripts\python.exe -m voice_control_usb --media-adapter windows "now playing"`
- `.\.venv\Scripts\python.exe -m voice_control_usb --media-adapter windows "report volume"`

WSL baseline, when the USB filesystem is mounted:

- `PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v`
- `PYTHONPATH=src .venv/bin/python -m voice_control_usb "open excel"`
- `PYTHONPATH=src .venv/bin/python -m voice_control_usb "open excel and go to A1"`
- `printf 'go to A5\nmark fail and next row\nquit\n' | PYTHONPATH=src .venv/bin/python -m voice_control_usb --session`
- `PYTHONPATH=src .venv/bin/python -m voice_control_usb "go to A123"`
- `PYTHONPATH=src .venv/bin/python -m voice_control_usb "open app notepad"`
- `PYTHONPATH=src .venv/bin/python -m voice_control_usb "open url https://example.com"`
- `PYTHONPATH=src .venv/bin/python -m voice_control_usb "open folder /tmp"`
- `PYTHONPATH=src .venv/bin/python -m voice_control_usb "shutdown"`
- `PYTHONPATH=src .venv/bin/python -m voice_control_usb "status"`
- `printf 'shutdown\nconfirm\nquit\n' | PYTHONPATH=src .venv/bin/python -m voice_control_usb --session`
- `printf 'shutdown\nstatus\nquit\n' | PYTHONPATH=src .venv/bin/python -m voice_control_usb --session`
- `printf 'restart\ncancel\nquit\n' | PYTHONPATH=src .venv/bin/python -m voice_control_usb --session`
- `printf 'open workbook /tmp/context.xlsx\nselect sheet Sheet2\ngo to A123\ntype pass\nreport current sheet\nquit\n' | PYTHONPATH=src .venv/bin/python -m voice_control_usb --session`
- `printf 'record open workbook /tmp/context.xlsx\nrecord select sheet Sheet2\nrecord go to A123\nrecord type pass\nquit\n' | PYTHONPATH=src .venv/bin/python -m voice_control_usb --session --input-mode speech`
- `printf '\nopen workbook /tmp/context.xlsx\n\nselect sheet Sheet2\n\nreport current sheet\nquit\n' | PYTHONPATH=src .venv/bin/python -m voice_control_usb --session --input-mode speech --speech-activation ptt`

## Windows COM verification
- `python -m pip install -e ".[windows]"`
- `set PYTHONPATH=src`
- `python scripts\verify_excel_com.py`
- `python -m voice_control_usb --window`
- `python -m voice_control_usb --excel-adapter com "open excel"`
- `python -m voice_control_usb --excel-adapter com "go to A123"`
- `python -m voice_control_usb --desktop-adapter windows "open app notepad"`
- `python -m voice_control_usb --desktop-adapter windows "open url https://example.com"`
- `.\scripts\build_windows_binaries.ps1 -UsbId "<UUID>" -ReleaseId "0.1.0" -SigningPrivateKeyPath "C:\secure\voice-control-signing-key.pem"`
- `.\scripts\install_starter_task.ps1 -StarterExe "C:\Program Files\voice-control-usb\voice-control-usb-starter.exe" -ConfigPath "C:\ProgramData\voice-control-usb\starter.json"`
- `C:\Program Files\voice-control-usb\voice-control-usb-starter.exe --config C:\ProgramData\voice-control-usb\starter.json --once`
- `C:\Program Files\voice-control-usb\voice-control-usb-starter.exe --config C:\ProgramData\voice-control-usb\starter.json --prepare-removal`
- Session mode is available with `python -m voice_control_usb --excel-adapter com --session`
- Speech session mode is available with `python -m voice_control_usb --excel-adapter com --session --input-mode speech`

## Speech input
- Controlled activation only for now: manual `record ...` lines in speech session mode
- Default speech provider: stub/manual for WSL and tests
- First real provider: `speech_recognition`
- Speech activation modes: `manual` and `ptt`
- Future providers plug in through `SpeechTranscriber` and `create_speech_transcriber`
- Future triggers plug in through `SpeechActivator` and `create_speech_activator`
- Details: [docs/SPEECH_INPUT.md](docs/SPEECH_INPUT.md)
