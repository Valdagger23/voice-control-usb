# Workflows

## Overview
Workflows are approved multi-step deterministic macros.
They let one command expand into several existing deterministic actions without bypassing the executor or adapter boundaries.

Examples:
- `mark pass and next row`
- `mark fail and next row`
- `open excel and go to A1`

## Base commands vs workflows
- Base commands map directly to one deterministic action.
- Workflows map to `run_workflow`, which expands into a sequence of existing approved actions.

The executor still performs each step through the same handler table used by base commands.

## Where workflows are defined
Workflow definitions live in:

- `src/voice_control_usb/core/workflow_registry.json`

Each workflow contains:
- `name`
- `description`
- ordered `steps`

Each step contains:
- `action`
- `arguments`

## Safety rules
Allowed:
- reference existing approved engine actions only
- chain Excel and safe desktop actions already supported by the runtime

Not allowed:
- arbitrary code execution
- arbitrary shell commands
- nested workflows
- actions that do not exist in the approved engine action set

Workflows inherit the same safety policy as base commands.
If a workflow step requires confirmation, the workflow is paused behind the confirmation gate.
If a workflow step is blocked in MVP, the workflow is blocked as well.

## Initial workflows

### `mark pass and next row`
Expands to:
1. `type_text` with `value=pass`
2. `next_row_from_start`

### `mark fail and next row`
Expands to:
1. `type_text` with `value=fail`
2. `next_row_from_start`

### `open excel and go to A1`
Expands to:
1. `open_excel`
2. `go_to_cell` with `cell=A1`

## Adding new workflows safely
1. Add a new workflow definition to `workflow_registry.json`.
2. Add a matching approved phrase to `command_registry.json` with `action=run_workflow`.
3. Keep workflow steps limited to existing approved actions.
4. Add tests for parsing, execution order, and context effects.
5. Do not add nested workflows or free-form execution hooks.

## Verification
WSL:

```bash
PYTHONPATH=src .venv/bin/python -m voice_control_usb "open excel and go to A1"
```

Single-process workflow example:

```bash
printf 'go to A5\nmark fail and next row\nquit\n' | PYTHONPATH=src .venv/bin/python -m voice_control_usb --session
```
