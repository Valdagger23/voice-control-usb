# Safety

## Safety goals
- Keep phase 1 deterministic and auditable.
- Avoid silent escalation from text input to broad OS control.
- Prefer explicit rejection over unsafe guessing.
- Maintain a clean separation between trusted launch logic and automation behavior.

## USB safety
- Do not rely on USB autorun.
- Require explicit trusted USB validation before launch.
- Keep the local starter minimal so the USB payload does not inherit unnecessary host privileges.

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

## AI safety for early phases
- AI may help draft reviewed proposals later, but phase 1 does not allow live self-modifying code.
- Unknown commands must not trigger runtime rewrites.
- Proposal logs are inputs for human review, not direct execution.
