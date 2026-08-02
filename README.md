# VoiceControl

VoiceControl is a Windows-first, USB-portable voice assistant. The long-term product supports modular Windows capabilities; the first production capability is deliberately limited to reliable Microsoft Excel control.

## Project status

Phase 3 controlled push-to-talk speech is complete on top of the native Excel vertical slice.

- The existing deterministic prototype is preserved as the implementation baseline.
- Basic Excel control now works through typed input or controlled offline speech in the visible Windows shell.
- Media/Spotify, browser/Google, and Discord capabilities follow after Excel is proven on Windows.
- Existing user-visible command behavior is preserved behind capability-neutral contracts.
- The next implementation phase is Windows media and Spotify control.

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
- Trust requires both the expected USB volume label and a marker file in the USB root
- The starter launches a packaged assistant executable from the trusted USB with `shell=False`
- The starter passes `--usb-root` and `--runtime-dir` explicitly to the packaged assistant
- Duplicate launches are prevented both by the starter’s child-process tracking and the assistant’s runtime lock file
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

## Runtime modes
- Visible Windows mode: `--window` opens typed and push-to-talk input, selecting native Excel COM and offline Windows speech by default
- One-shot mode: runs one command and exits
- Session mode: `--session` keeps one assistant process alive and preserves Excel context across commands
- Speech session mode: `--session --input-mode speech` accepts controlled `record ...` activations and routes recognized text into the same assistant pipeline
- Push-to-talk speech mode: `--session --input-mode speech --speech-activation ptt` uses Enter as the recording trigger in terminal sessions
- Safety flow: safe commands run immediately, risky commands raise a clear `[CONFIRMATION REQUIRED]` alert, `status` reports pending confirmation state, and blocked MVP actions still do not execute

## Workflows
- Approved multi-step macros are registry-driven
- Workflow phrases expand into existing deterministic actions only
- Details: [docs/WORKFLOWS.md](docs/WORKFLOWS.md)

## Local verification

Windows baseline:

- `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`
- `.\.venv\Scripts\python.exe scripts\verify_excel_com.py`
- `.\.venv\Scripts\python.exe scripts\verify_windows_speech.py`
- `.\.venv\Scripts\python.exe -m voice_control_usb --window`
- `.\.venv\Scripts\python.exe -m voice_control_usb "open excel"`
- `.\.venv\Scripts\python.exe -m voice_control_usb "open excel and go to A1"`

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
- `.\scripts\build_windows_binaries.ps1`
- `.\scripts\install_starter_task.ps1 -StarterExe "C:\Program Files\voice-control-usb\voice-control-usb-starter.exe" -ConfigPath "C:\ProgramData\voice-control-usb\starter.json"`
- `C:\Program Files\voice-control-usb\voice-control-usb-starter.exe --config C:\ProgramData\voice-control-usb\starter.json --once`
- `E:\dist\voice-control-usb-assistant\voice-control-usb-assistant.exe --usb-root E:\ --runtime-dir E:\runtime`
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
