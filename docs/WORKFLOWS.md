# Workflows

## Overview
Voice Control supports two deterministic sequence types:

- built-in workflows shipped with the application
- editable user routines assembled from supported command phrases

Both execute through the normal parser, safety policy, executor, and adapter boundaries.

Examples:
- `mark pass and next row`
- `mark fail and next row`
- `open excel and go to A1`

## Base commands vs workflows
- Base commands map directly to one deterministic action.
- Workflows map to `run_workflow`, which expands into a sequence of existing approved actions.
- User routines store ordered command phrases and resolve each phrase through the current command registry when run.

The executor still performs each step through the same handler table used by base commands.

## User routine builder

Open the `ROUTINES` column in the Windows command console, then:

1. Enter a name and select `NEW`.
2. Drag command cards from the command deck into the sequence lane.
3. Read the cards from left to right; their step numbers are the execution order.
4. Drag a step onto another position to reorder it.
5. Select a step to edit its phrase, remove it, or move it with the arrow controls.
6. Select `RUN`, or say `start <NAME> routine`.

Routines are saved to `runtime/routines.json` (or the selected `--runtime-dir`) and are restored the next time the assistant starts.

Voice management phrases:

- `create routine <NAME>`
- `edit routine <NAME>`
- `list routines`
- `start <NAME> routine`
- `run <NAME> routine`
- `delete routine <NAME>`

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
- nested routines or routine-management commands inside a routine
- actions that do not exist in the approved engine action set

Workflows inherit the same safety policy as base commands.
If a workflow step requires confirmation, the workflow is paused behind the confirmation gate.
If a workflow step is blocked in MVP, the workflow is blocked as well.

A user routine follows the same inheritance rule. If any step requires confirmation, Voice Control presents one confirmation for the routine before running the chain. Any blocked or unsupported step prevents the routine from being saved or run.

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

User routines do not require registry-file edits. Add, edit, and reorder them in the visible builder; each step must already be a supported command.

## Verification
WSL:

```bash
PYTHONPATH=src .venv/bin/python -m voice_control_usb "open excel and go to A1"
```

Single-process workflow example:

```bash
printf 'go to A5\nmark fail and next row\nquit\n' | PYTHONPATH=src .venv/bin/python -m voice_control_usb --session
```
