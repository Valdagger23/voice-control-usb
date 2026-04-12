# MVP

## Phase-1 objective
Ship a practical deterministic skeleton that proves the architecture without overbuilding autonomy.

## Included in phase 1
- Trusted USB starter validation skeleton.
- USB-hosted assistant CLI shell.
- Strict parser for a very small approved command set.
- Deterministic execution engine.
- Excel adapter interface with a safe stub implementation.
- Unsupported-command proposal logging.
- Parser and execution tests.

## Explicitly deferred
- Production speech-to-text integration.
- Live AI-driven code rewriting.
- Broad operating system control.
- Keyboard automation as a default Excel strategy.
- Background autonomy beyond the starter launch flow.

## Initial command scope
- `open excel`
- `read cell <CELL>`
- `write cell <CELL> value <TEXT>`

## Ordered next implementation steps
1. Replace the stub Excel adapter with a Windows COM-backed adapter behind the same interface.
2. Add workbook, worksheet, and active-context models so commands can target explicit Excel state.
3. Expand the parser with a reviewed command grammar for workbook open/save/select actions.
4. Add starter configuration loading and USB metadata validation beyond a single trust marker.
5. Introduce a speech-to-text adapter that outputs plain text into the same deterministic parser path.
6. Add structured proposal review tooling so unsupported commands can become reviewed grammar additions.
