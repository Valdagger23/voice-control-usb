# Architecture

## Product boundary

VoiceControl is a capability-based Windows assistant. Excel is the first production capability; media/Spotify, browser/Google, and Discord are later capability packs using the same command, policy, context, and audit pipeline.

## Deployable components

1. **Local Windows starter** — discovers and verifies the trusted USB payload, prevents duplicate launches, and starts the assistant without performing automation.
2. **USB-hosted assistant** — owns the user interface, input, command processing, safety policy, capability routing, session state, and audit history.

The system does not use USB autorun. Account credentials remain in the prepared Windows user's credential store rather than portable plaintext files.

## Target layers

1. **Assistant shell** — tray/window UI, lifecycle, visible state, and typed fallback.
2. **Input adapters** — push-to-talk activation and pluggable speech transcription.
3. **Interpretation** — normalize input into a typed command or a reviewable unsupported proposal.
4. **Policy** — classify the command as allowed, confirmation-required, or blocked.
5. **Context** — maintain application-neutral session state plus isolated capability state.
6. **Capability registry** — resolve an approved action to exactly one capability handler.
7. **Capability adapters** — Excel COM first; later media, browser, Google, and Discord adapters.
8. **Workflow engine** — execute validated sequences of approved actions without arbitrary code hooks.
9. **Audit and recovery** — record commands, decisions, results, errors, and reversible mutations.

## Runtime flow

1. The user activates typed or push-to-talk input.
2. Speech is transcribed into text.
3. Interpretation produces a typed command with validated arguments.
4. Policy evaluates the action and current state.
5. Confirmation is requested when required.
6. The capability registry routes the command to an approved adapter.
7. The adapter returns a structured result and optional reversible-change record.
8. The shell reports the outcome and persists an audit event.

## Capability contract

Every capability declares:

- stable capability and action identifiers
- typed argument and result schemas
- safety class for each action
- required configuration and credentials
- state it owns and exposes
- whether the action is reversible
- stub and native adapter behavior

The core must not import capability-specific implementation details.

## Capability roadmap

### Excel

Uses COM/object-level control. Keyboard and mouse automation are not the default Excel strategy.

### Media and Spotify

Uses the Windows Global System Media Transport Controls current-session API for player-neutral playback and now-playing state. Default speaker volume and mute state use the Windows Core Audio endpoint boundary. Optional account-specific Spotify access uses Authorization Code with PKCE, two playback-only scopes, short-lived access tokens in memory, and a refresh token in Windows Credential Manager.

### Browser and Google

Uses Playwright with an assistant-owned persistent Chrome or Edge profile. The adapter reports pages, tabs, and safe visible anchors through object-level browser APIs. Numbered links are reopened as verified HTTP(S) navigation rather than DOM clicks. Form controls, downloads, purchases, and outgoing messages are outside this capability. Private Google services remain a separate future OAuth boundary.

### Discord

Uses the installed Discord client in forced renderer-accessibility mode and Windows UI Automation. Navigation is limited to configured `discord://` target aliases. Draft text uses the accessible composer value pattern, and confirmed preparation only focuses the unchanged draft; the user physically sends it. Microphone, deafen, and camera actions run only from readable button state. Personal account tokens, self-bots, simulated sending, background sending, and bulk messaging are prohibited.

## Development model

- Windows is the production and native-integration target.
- WSL or cross-platform Python may run deterministic unit tests against stubs.
- Windows-sensitive code remains behind narrow interfaces.
- Each phase must preserve the existing test baseline while adding contract and integration coverage.

## Phase 1 implementation map

- `core.capabilities` defines action specifications, bindings, typed argument validation, structured results, and the central registry.
- `excel.capability` and `desktop.capability` own their action contracts and adapter bindings.
- `media.capability` owns player and speaker action contracts; `media.windows_adapter` keeps WinRT and Core Audio details outside the core.
- `core.builtin_capabilities` owns assistant controls and deterministic workflow expansion.
- `executor.engine` composes capabilities and preserves the existing string-returning compatibility boundary.
- `core.session_context` stores pending confirmation and namespaced future capability state without importing Excel.
- `core.audit` defines structured events plus JSONL and in-memory stores.
- `core.safety` reads safety classes from the running capability catalog; its legacy fallback remains only for direct compatibility callers.
- Workflow steps are validated against action existence and argument types during startup.
