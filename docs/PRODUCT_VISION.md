# Product Vision

## Purpose

VoiceControl is a portable, privacy-conscious Windows voice assistant for deliberate, user-initiated computer control. It should make common work and communication tasks faster while remaining visible, predictable, and reversible where possible.

## Product shape

- **Broad destination:** a modular Windows assistant.
- **Narrow first release:** basic Microsoft Excel control.
- **Next capabilities:** media/Spotify, browser/Google, and Discord.
- **Deployment:** main assistant on a trusted USB with a minimal starter on prepared Windows laptops.
- **Interaction:** typed fallback plus an assignable global key or mouse button for hold-to-talk or explicit listening toggle; no wake word.

## Experience principles

1. The user always knows whether VoiceControl is listening, processing, waiting for confirmation, or idle.
2. The assistant performs only validated actions exposed by installed capabilities.
3. It prefers explicit state-setting commands over blind toggles.
4. Outward-facing and privacy-sensitive actions receive extra confirmation.
5. Errors are reported clearly and do not silently change application state.
6. Unsupported requests become reviewable proposals, not runtime code changes.

## Initial capability roadmap

### Basic Excel

Open a workbook, select a worksheet and cell, enter a small set of values, navigate, complete a row-entry workflow, save, report context, and reverse the last assistant-made cell edit when possible.

### Media and Spotify

Play, pause, skip, change volume, and report the current track. Authenticated search, playlists, queue, and library actions follow later.

### Browser and Google

Open sites, search Google, manage tabs, navigate history, scroll, select visible links, and report the current page. Private Gmail, Drive, or Calendar actions are separate authenticated capabilities.

### Discord

Open and focus Discord, navigate to configured targets, draft and confirm individual messages, report voice state, mute immediately, and require confirmation before unmuting or enabling the camera.

## Non-goals

- unrestricted operating-system control
- arbitrary shell execution
- silent background messaging
- Discord self-bots or personal-token automation
- live self-modifying code
- unreviewed executable workflows
- plaintext account credentials on the USB
- unsafe USB autorun
