# Implementation Plan

## Planning rule

Each phase must deliver a usable vertical slice, preserve earlier behavior unless a migration is documented, and finish with code, automated tests, relevant documentation, and explicit native-Windows verification steps.

## Phase 0 — Rebaseline and relocate

Goal: establish the USB repository and approved product contract without changing runtime behavior.

- Place the Git repository at `D:\VoiceControl` and preserve its history and GitHub remote.
- Record the product vision, target architecture, MVP boundary, safety rules, and phased roadmap.
- Establish a clean project-local development environment on the USB copy.
- Run the existing automated suite from the USB copy.
- Record any native-Windows checks that remain outstanding.

Exit: the USB repository is the active clean baseline, documentation agrees on the new direction, and all existing automated tests pass.

## Phase 1 — Generalize the deterministic core

Goal: make the core capability-neutral without changing visible prototype behavior.

Status: complete on the `agent/phase-1-capability-core` branch.

- Introduce capability and action identifiers, typed arguments, structured results, and audit events.
- Separate application-neutral session context from Excel state.
- Add a capability registry and declared action safety metadata.
- Adapt existing Excel and desktop handlers through the new contract.
- Preserve command parsing and proposal behavior during migration.
- Add contract tests for capabilities, policies, results, and failures.

Exit: existing commands pass through the new capability contract and the full baseline remains green.

## Phase 2 — Basic Excel vertical slice

Goal: deliver the first real user workflow on native Windows.

- Add the minimal Windows shell with typed input and visible state.
- Complete Excel COM support for workbook, sheet, cell, entry, navigation, and save operations.
- Add current-cell reporting and a reversible record for assistant-made cell edits.
- Add the basic approved row-entry workflows.
- Validate failures such as missing workbooks, protected sheets, invalid values, and lost Excel sessions.
- Verify against real Excel on Windows.

Exit: a user completes and saves a row-entry workflow through the visible assistant with deterministic results and audit history.

## Phase 3 — Push-to-talk speech

Goal: place controlled speech in front of the same typed-command pipeline.

- Implement microphone selection and push-to-talk activation.
- Integrate the chosen local/offline transcription provider by default.
- Show transcript, interpretation, execution state, and errors.
- Reject silence, ambiguous recognition, and unsupported phrases safely.
- Keep typed input available for testing and accessibility.

Exit: the Excel vertical slice can be completed using push-to-talk on native Windows.

## Phase 4 — Media and Spotify

Goal: add the first non-Excel capability without weakening the core boundaries.

- Add Windows media-session play, pause, previous, next, mute, volume, and now-playing actions.
- Add optional Spotify OAuth for account-specific playback features.
- Keep credentials in the Windows credential store.
- Add capability-specific tests and native playback verification.

## Phase 5 — Browser and Google

Goal: provide visible, deterministic browser navigation.

- Open approved URLs and Google searches.
- Manage tabs, history, refresh, scrolling, and visible link selection.
- Report page identity and visible state needed for safe interaction.
- Gate form submissions, downloads, purchases, and outgoing messages appropriately.
- Add private Google-service adapters separately using least-privilege OAuth scopes.

## Phase 6 — Discord

Goal: support deliberate Discord communication and voice-state controls without self-bot behavior.

- Open or focus Discord and navigate to configured servers, channels, or direct messages.
- Draft one message visibly, allow edit/cancel, and require confirmation to send.
- Read and set microphone, deafen, and camera state where reliable state inspection is available.
- Mute and disable camera immediately; confirm before unmuting or enabling camera.
- Block personal-token automation, background sending, bulk messaging, and scraping.

## Phase 7 — USB packaging and hardening

Goal: turn the proven assistant into a reliable portable deployment.

- Package the assistant and required runtime assets for Windows.
- Verify USB identity and an application manifest before launch.
- Resolve all paths from the detected USB root rather than a fixed drive letter.
- Prevent duplicate launches and provide safe assistant shutdown before removal.
- Stage and verify updates before replacing the working version.
- Exercise missing files, changed drive letters, interrupted startup, and recovery.

## Quality gates for every phase

- no arbitrary shell execution
- no plaintext secrets committed or stored in portable configuration
- deterministic safety decision for every action
- unit tests using stubs for all command, policy, and routing behavior
- native Windows verification for Windows-specific integrations
- documentation updated when behavior or architecture changes
- clean Git diff limited to the active phase
