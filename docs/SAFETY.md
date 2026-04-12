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

## Excel safety
- Prefer object-level Excel APIs.
- Do not default to blind keyboard or mouse automation.
- Keep workbook mutation commands narrow and explicit.
- Use the stub adapter by default in WSL so automated tests do not depend on a live Excel process.
- Require explicit adapter selection before using the Windows COM path.

## AI safety for early phases
- AI may help draft reviewed proposals later, but phase 1 does not allow live self-modifying code.
- Unknown commands must not trigger runtime rewrites.
- Proposal logs are inputs for human review, not direct execution.
