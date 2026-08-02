# AGENTS.md

## Project
This repository builds a modular Windows voice assistant with a USB-portable deployment model. Basic Microsoft Excel control is the first production capability, not the limit of the product.

## Current project stage
Phase 1 capability-core implementation is complete. The deterministic runtime now routes through typed capability contracts while preserving the earlier user-visible behavior. Phase 2 is the basic Excel vertical slice on native Windows.

Do not broaden implementation scope before the basic Excel vertical slice works on native Windows.

## Primary goal
Build a reliable modular system with these layers:
1. local laptop starter/watcher
2. USB-hosted Windows assistant shell
3. typed and push-to-talk input adapters
4. validated command and context model
5. deterministic policy and execution engine
6. capability registry and adapter boundary
7. basic Excel capability first
8. media/Spotify, browser/Google, and Discord capabilities later
9. audit, recovery, and unsupported-command proposal flow

## Non-goals for early phases
Do not implement full self-modifying code.
Do not grant unrestricted OS control.
Do not build unsafe silent autorun behavior.
Do not use blind keyboard automation where direct Excel object control is possible.
Do not automate Discord user accounts through personal tokens or self-bot behavior.
Do not implement background or bulk messaging.
Do not store account tokens as plaintext on the USB.

## Architecture rules
- Prefer Python for the main implementation.
- Keep desktop starter and main assistant separate.
- Keep the assistant core independent of Excel and every other individual capability.
- Add Windows features through explicit capability interfaces with declared actions and safety classes.
- Keep action specifications beside their owning capability and bind them through `CapabilityRegistry`.
- Return structured `ActionResult` values at the capability boundary; unwrap messages only at compatibility/UI boundaries.
- Record command decisions and outcomes through the audit-store boundary.
- Use COM/object-level Excel control before keyboard/mouse fallbacks.
- Keep command handling deterministic and testable.
- AI-assisted command generation must produce proposals, not live unsafe rewrites.
- Unknown commands should be logged and converted into reviewed proposals.
- Prefer explicit state-setting commands such as `mute microphone` over blind toggle commands.
- Require confirmation before privacy-sensitive or outward-facing actions such as enabling a camera, unmuting a microphone, or sending a message.
- Store OAuth tokens and other secrets in a Windows credential store, not in repository files or portable plaintext configuration.

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
