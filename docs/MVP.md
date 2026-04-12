# MVP

## Phase-1 objective
Ship a practical deterministic skeleton that proves the architecture without overbuilding autonomy.

## Included in phase 1
- Trusted USB starter validation skeleton.
- USB-hosted assistant CLI shell.
- Strict parser for a very small approved command set.
- Deterministic execution engine.
- Excel adapter interface with a safe stub implementation for WSL and a Windows COM-backed implementation for object-level Excel control.
- Workbook and worksheet context handling behind the Excel adapter boundary.
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
- `open workbook <PATH>`
- `select sheet <NAME>`
- `save workbook`
- `report current sheet`
- `go to <CELL>`
- `type pass`
- `type fail`
- `go right`
- `go down`
- `next row from start`

## Ordered next implementation steps
1. Expand the parser with a reviewed command grammar for workbook save-as and worksheet creation or rename actions.
2. Add starter configuration loading and USB metadata validation beyond a single trust marker.
3. Introduce a speech-to-text adapter that outputs plain text into the same deterministic parser path.
4. Add structured proposal review tooling so unsupported commands can become reviewed grammar additions.
