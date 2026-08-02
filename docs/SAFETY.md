# Safety

## Safety goals
- Keep phase 1 deterministic and auditable.
- Avoid silent escalation from text input to broad OS control.
- Prefer explicit rejection over unsafe guessing.
- Maintain a clean separation between trusted launch logic and automation behavior.
- Make privacy-sensitive and outward-facing actions visible and deliberate.
- Keep credentials out of portable plaintext storage.

## USB safety
- Do not rely on USB autorun.
- Require explicit trusted USB validation before launch.
- Keep the local starter minimal so the USB payload does not inherit unnecessary host privileges.
- Trust the USB only when both the configured volume label and marker file match.
- Launch the packaged USB assistant through a direct executable path, not through arbitrary shell execution.
- Pass the USB root and runtime directory explicitly to the assistant instead of relying on implicit shell state.
- Keep runtime data lookups explicit so bundled registries and allowlists fail loudly when missing.

## Command safety
- Parse only approved command grammar.
- Reject ambiguous or unsupported inputs.
- Log unsupported requests as proposals for review instead of mutating the system automatically.
- Classify approved actions deterministically as allowed immediately, requires confirmation, or blocked in MVP.
- Require explicit `confirm` before executing risky commands such as `shutdown` or `restart`.
- Keep `kill process <NAME>` and `run command <TEXT>` blocked in MVP.
- Allow workflows to reuse only existing approved actions from the deterministic engine.
- Do not allow nested workflows or arbitrary execution hooks in workflow definitions.
- Apply the same safety policy to workflow steps so a risky step cannot bypass confirmation.
- Treat capability action metadata as the running source of truth for allowed, confirmation-required, and blocked classifications.
- Reject unregistered actions and arguments that do not satisfy their declared types.
- Validate workflow step contracts at startup before any workflow can partially execute.
- Record supported, blocked, confirmation, cancellation, failure, and unsupported outcomes in the structured audit log.

## Confirmation flow
- One-shot mode never executes confirm-required actions immediately.
- One-shot risky commands return a `[CONFIRMATION REQUIRED]` response and exit.
- Session mode stores one pending risky action at a time.
- `status` reports the current pending confirmation state without changing it.
- `confirm` executes the pending action through the normal engine path.
- `cancel` clears the pending action without executing it.
- If there is no pending action, `confirm` and `cancel` return a deterministic no-op response.
- Pending-action timeout support is wired into the assistant flow but disabled by default.
- If timeout is enabled, expired pending actions are cleared before the next command is processed.

## Excel safety
- Prefer object-level Excel APIs.
- Do not default to blind keyboard or mouse automation.
- Keep workbook mutation commands narrow and explicit.
- Use the stub adapter by default in WSL so automated tests do not depend on a live Excel process.
- Require explicit adapter selection before using the Windows COM path.
- Keep workbook and sheet targeting explicit so save and sheet-selection commands operate on a known active context.

## Desktop safety
- Launch desktop apps only through allowlisted aliases.
- Do not use arbitrary shell execution.
- Do not use `shell=True`.
- Limit URLs to approved `http` and `https` forms.
- Keep destructive OS-control actions gated or blocked even when the parser recognizes them.

## Media and Spotify safety

- Use explicit play, pause, mute, unmute, and volume state commands; do not expose arbitrary media-key injection.
- Treat the current Windows media session as the only native playback target and report clearly when no session exists.
- Keep ordinary local media control independent of Spotify account authorization.
- Use Spotify Authorization Code with PKCE without a client secret in the desktop assistant.
- Request only `user-read-playback-state` and `user-modify-playback-state`.
- Keep the Spotify access token in memory and store only the refresh token in Windows Credential Manager.
- Never copy Spotify tokens to the repository, USB runtime, audit log, or console output.

## Communication and privacy safety

- Draft outgoing messages visibly and require explicit confirmation before sending.
- Do not implement background or bulk messaging.
- Do not automate Discord user accounts through personal tokens or self-bot behavior.
- Mute microphones and disable cameras immediately when requested.
- Require confirmation before unmuting a microphone or enabling a camera.
- Prefer explicit desired-state commands over blind toggles.
- If current microphone or camera state cannot be verified, report uncertainty instead of guessing.

## Credential safety

- Store OAuth refresh tokens and service credentials in a Windows credential store.
- Do not store account tokens, passwords, or client secrets as plaintext on the USB.
- Request the least privilege required by each capability.
- Treat Google services, Spotify, and Discord as separate authorization boundaries.

## AI safety for early phases
- AI may help draft reviewed proposals later, but phase 1 does not allow live self-modifying code.
- Unknown commands must not trigger runtime rewrites.
- Proposal logs are inputs for human review, not direct execution.
