# Commands

## Command design rules
- Commands must parse deterministically.
- Each command must map to one approved handler.
- Ambiguous natural language should be rejected and logged as a proposal.
- Excel-oriented actions should target object-level operations first.

## Supported phase-1 commands

### `open excel`
Opens or attaches to an Excel session.

### `go to <CELL>`
Moves the active Excel location to a specific cell and sets the start column for the current row-entry block.

Examples:
- `go to A123`
- `go to C7`

### `type pass`
Types `pass` into the current active cell.

### `type fail`
Types `fail` into the current active cell.

### `go right`
Moves one column to the right from the current active cell.

### `go down`
Moves one row down from the current active cell.

### `next row from start`
Moves to the next row and returns to the original start column established by `go to <CELL>`.

Examples:
- `open excel`
- `go to A123`
- `type pass`
- `go right`
- `type fail`
- `next row from start`

## Unsupported command handling
If the text does not match the approved grammar, the assistant must not guess.
It should create a proposal entry containing:

- original text
- rejection reason
- timestamp or surrounding runtime metadata in later phases

## Near-term planned commands
- open workbook
- save workbook
- select worksheet
- go left
- repeat current row pattern
