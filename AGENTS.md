# AGENTS.md

## Project
This repository builds a Windows-first voice-controlled automation system with strong support for Microsoft Excel workflows and a USB-portable deployment model.

## Current project stage
We are in early architecture + MVP implementation.
Do not jump to advanced autonomy before the deterministic core works.

## Primary goal
Build a reliable modular system with these layers:
1. local laptop starter/watcher
2. USB-hosted main assistant
3. speech-to-text input
4. strict command parsing
5. deterministic execution engine
6. Excel automation module
7. safe unsupported-command proposal flow

## Non-goals for early phases
Do not implement full self-modifying code.
Do not grant unrestricted OS control.
Do not build unsafe silent autorun behavior.
Do not use blind keyboard automation where direct Excel object control is possible.

## Architecture rules
- Prefer Python for the main implementation.
- Keep desktop starter and main assistant separate.
- Use COM/object-level Excel control before keyboard/mouse fallbacks.
- Keep command handling deterministic and testable.
- AI-assisted command generation must produce proposals, not live unsafe rewrites.
- Unknown commands should be logged and converted into reviewed proposals.

## Repository priorities
- Keep modules small and clear.
- Avoid broad exception swallowing.
- Surface errors clearly.
- Write code that is practical and runnable, not speculative pseudocode.
- Add tests for parser and command routing logic when behavior changes.

## Done means
A task is not done until:
- code is implemented
- affected files are updated
- relevant tests are added or updated
- the run/verify steps are stated clearly
- docs are updated if architecture or command behavior changed

## Working style
- For difficult tasks, plan first before coding.
- If the request is underspecified, ask targeted clarification questions only when blocking.
- Otherwise make the best reasonable implementation choice and state assumptions.
- Keep changes scoped. Do not refactor unrelated parts.
- When adding new project rules, update this AGENTS.md.

## Important project constraints
- Windows target environment
- Codex local work should assume WSL dev environment
- USB deployment is supported via a local trusted starter on each laptop
- No dangerous USB autorun assumptions
- Security and reliability take priority over cleverness