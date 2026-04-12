# Architecture

## Overview
The system is split into two deployable components:

1. A local Windows starter/watcher installed on each laptop.
2. A USB-hosted main assistant that owns parsing, execution, and proposal logging.

The starter is intentionally narrow. It detects a trusted USB payload and launches the assistant from the USB. It does not perform automation itself and does not depend on unsafe autorun behavior.

## Phase-1 boundaries
Phase 1 is deterministic by design.

- Speech-to-text is only a boundary module, not yet a production integration.
- Command parsing is strict and rule-based.
- Execution routes only pre-approved commands.
- Unknown or unsupported commands are logged as reviewable proposals.
- Excel automation is represented by an object-level adapter interface before any fallback automation is considered.

## Module layout
- `voice_control_usb.starter`
  Local trusted USB validation and launch behavior.
- `voice_control_usb.assistant`
  Assistant orchestration and CLI entrypoint for USB-hosted runtime.
- `voice_control_usb.core`
  Shared command models, parser, registry, and proposal persistence.
- `voice_control_usb.executor`
  Deterministic routing from parsed commands to approved handlers.
- `voice_control_usb.excel`
  Excel automation abstraction, with a safe stub in phase 1.
- `voice_control_usb.audio`
  Future speech-to-text integration boundary kept outside the deterministic core.

## Runtime flow
1. The local starter checks for a trusted marker on the USB root.
2. The starter launches the USB-hosted assistant entrypoint.
3. Speech input is expected to become plain text before parsing.
4. The parser converts text into a normalized command or an unsupported proposal.
5. The executor runs only recognized commands through approved modules.
6. Unsupported input is appended to a proposal log for later review.

## Deployment model
- Windows is the target runtime for the starter and future Excel COM integration.
- WSL is the development environment.
- The repository keeps Windows-sensitive logic behind small interfaces so unit tests can run in WSL.

## Excel strategy
- Preferred path: COM or object-level APIs through a dedicated adapter.
- Deferred path: keyboard or mouse fallback only if an operation cannot be achieved safely through object control.
- Phase 1 ships only a stub adapter so parser and execution logic can be built and tested first.
