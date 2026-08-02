# Phase 1 Baseline

Recorded: 2026-08-02

## Goal

Generalize the deterministic runtime into capability-neutral contracts without changing existing user-visible command behavior.

## Delivered

- Stable capability and action identifiers.
- `ActionSpec` metadata with declared safety, reversibility, and argument types.
- `ActionBinding` and `Capability` interfaces for modular action packs.
- `CapabilityRegistry` declaration, handler binding, validation, and execution routing.
- Structured `ActionResult` values with a compatibility string boundary.
- Excel, desktop, workflow, and assistant-control action ownership.
- Safety policy backed by the running action catalog.
- Application-neutral `SessionContext` with namespaced capability state.
- Structured audit events with in-memory and JSONL stores.
- Explicit USB runtime audit path: `runtime/audit/events.jsonl`.
- Startup validation of workflow action existence and argument types.

## Compatibility

- Existing command phrases and output messages are unchanged.
- Existing Excel and desktop adapters remain in use behind capability bindings.
- `ExecutionEngine.execute()` still returns a message string; new integrations use `execute_result()`.
- The legacy direct `SafetyPolicy` construction path remains available while the running assistant uses capability metadata.

## Verification

```powershell
.\.venv\Scripts\python.exe -m compileall -q src tests
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Result:

- 109 tests passed.
- 2 existing live Windows adapter checks remain intentionally skipped for native verification.
- Legacy parser, assistant, confirmation, workflow, starter, and CLI tests remain green.
- New tests cover registry contracts, argument validation, structured result identity, safety metadata, workflow contract validation, auditing, and neutral session state.

## Next phase

Phase 2 delivers the basic Excel vertical slice on native Windows: visible assistant shell, completed COM operations, current-cell reporting, reversible assistant-made cell edits, and real-workbook failure handling.
