# Commands

## Command design rules
- Commands must parse deterministically.
- Each command must map to one approved handler.
- Ambiguous natural language should be rejected and logged as a proposal.
- Excel-oriented actions should target object-level operations first.
- Workbook and worksheet context are maintained within the active assistant process.
- Session mode preserves that context across multiple commands in one runtime.
- Speech session mode must feed recognized text into the same typed command handling path.
- Push-to-talk speech mode must use explicit activation and the same post-transcription command path.

## Supported phase-1 commands

### `open excel`
Opens or attaches to an Excel session.

### `open app <ALIAS>`
Opens an allowlisted desktop app alias through the desktop adapter.

Examples:
- `open app notepad`
- `open app calculator`

### `open url <URL>`
Opens an approved `http` or `https` URL through the desktop adapter.

Example:
- `open url https://example.com`

### `open folder <PATH>`
Opens a folder path through the desktop adapter.

Example:
- `open folder /tmp`
- `open folder C:\Users`

### `open workbook <PATH>`
Opens a workbook and makes it the active workbook context for later sheet selection, saving, and navigation commands.

Examples:
- `open workbook C:\Data\audit.xlsx`
- `open workbook /tmp/context.xlsx`

### `select sheet <NAME>`
Selects a worksheet inside the active workbook context.

Examples:
- `select sheet Sheet2`
- `select sheet Summary`

### `save workbook`
Saves the active workbook.
If the workbook has no path yet, the adapter rejects the command instead of guessing a save destination.

### `report current sheet`
Reports the current active worksheet together with the active workbook name.

### `go to <CELL>`
Moves the active Excel location to a specific cell in the active worksheet and sets the start column for the current row-entry block.

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
- `open app notepad`
- `open url https://example.com`
- `open folder C:\Users`
- `open workbook C:\Data\audit.xlsx`
- `select sheet Sheet2`
- `report current sheet`
- `go to A123`
- `type pass`
- `go right`
- `type fail`
- `save workbook`
- `next row from start`

## Unsupported command handling
If the text does not match the approved grammar, the assistant must not guess.
It should create a proposal entry containing:

- original text
- rejection reason
- timestamp or surrounding runtime metadata in later phases

## Explicit MVP rejections
The runtime also contains explicit deterministic rejections for risky desktop actions such as:

- `shutdown`
- `restart`
- `kill process <NAME>`
- `run command <TEXT>`

These do not execute. They return a `not approved in MVP` response instead.

## Near-term planned commands
- save workbook as
- create worksheet
- rename worksheet
- go left
- repeat current row pattern
