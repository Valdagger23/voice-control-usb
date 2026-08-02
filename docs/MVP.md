# MVP

## Objective

Prove the complete VoiceControl interaction on native Windows with a deliberately small Excel capability. The architecture must allow later capability packs without implementing them in the first release.

## Primary user journey

1. The user launches VoiceControl on a prepared Windows laptop.
2. VoiceControl attaches to Excel or opens a requested workbook.
3. The user issues a typed command or holds push-to-talk and speaks.
4. VoiceControl shows the transcript, validates the command, and executes an approved Excel action.
5. Workbook, worksheet, cell, and row-entry context remain available for the session.
6. VoiceControl reports and audits the outcome.

## Included

### Assistant shell

- Small visible Windows interface or tray application.
- Ready, listening, processing, confirmation, and error states.
- Typed-command fallback.
- Push-to-talk activation; no always-listening wake word.
- Visible transcript and execution result.
- Help, status, pause, and exit controls.

### Deterministic runtime

- Typed command models and validated arguments.
- Session context separated from capability-specific state.
- Capability registry and explicit handler routing.
- Deterministic safety classification.
- Structured audit events and unsupported-command proposals.
- Stub adapters for automated tests and native adapters for Windows integration tests.

### Basic Excel capability

- Open or attach to Excel.
- Open a workbook by path or configured friendly name.
- Select and report the active workbook and worksheet.
- Go to and report the active cell.
- Enter validated text, numbers, `Pass`, `Fail`, or `N/A`.
- Move left, right, up, and down.
- Mark an approved value and move to the next anchored row.
- Save the active workbook.
- Record enough information to reverse the last assistant-made cell edit when possible.

## MVP safety behavior

- Unsupported or ambiguous input never executes.
- Excel uses COM/object-level automation.
- Every assistant-made mutation creates an audit event.
- Destructive actions require confirmation or remain blocked.
- No arbitrary shell commands, background autonomy, or self-modification.

## Explicitly deferred

- Spotify and general media control.
- Browser navigation and Google services.
- Discord navigation, messaging, microphone, and camera control.
- Wake-word activation.
- Broad natural-language planning.
- Arbitrary user-created executable workflows.

## Exit criteria

The MVP is complete when a user can perform a full Excel row-entry workflow using push-to-talk on native Windows, correct or reverse an assistant-made cell edit, save the workbook, and exit safely. Automated tests must cover parsing, policy, routing, state, and failure cases; native Windows verification must cover microphone input and real Excel COM behavior.
