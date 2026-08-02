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
- Safety decisions must stay deterministic: allowed immediately, requires confirmation, or blocked in MVP.

## Supported commands

### Discord commands

- `open discord`
- `go to discord <ALIAS>`
- `draft discord message <TEXT>`
- `edit discord message <TEXT>`
- `cancel discord draft`
- `send discord draft` (confirmation prepares and focuses it; you press Enter)
- `mute microphone`
- `unmute microphone` (confirmation required)
- `deafen discord`
- `undeafen discord` (confirmation required)
- `disable camera`
- `enable camera` (confirmation required)
- `discord status`

Discord target aliases come from `VOICE_CONTROL_USB_DISCORD_TARGETS`. Message submission is never automated for a normal Discord account. User-token and bulk-send phrases are explicitly blocked.

### Browser and Google commands

- `browse to https://example.com`
- `google <search terms>`
- `search google for <search terms>`
- `new browser tab`
- `close browser tab`
- `switch to browser tab <NUMBER>`
- `go back`
- `go forward`
- `refresh page`
- `scroll page up`
- `scroll page down`
- `report current page`
- `list browser tabs`
- `list visible links`
- `open link <NUMBER>`

`list visible links` returns at most ten visible HTTP(S) navigation links and excludes anchors marked as downloads. `open link <NUMBER>` only works against that fresh page snapshot and navigates directly to the recorded URL. It does not click buttons, submit forms, start purchases, download files, or send messages.

### Media and speaker commands

- `play media` or `play music`
- `pause media` or `pause music`
- `next track`
- `previous track`
- `mute speakers`
- `unmute speakers`
- `set volume to <0-100> percent`
- `report volume`
- `now playing`

Playback commands target the current Windows media session, which can be Spotify or a supported browser/player. Mute and volume commands target the default Windows playback device. These commands are allowed immediately and return visible, audited results.

### Excel and desktop commands

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

### `report current cell`
Reports the active cell address and its current displayed value. Empty cells are reported as `<empty>`.

### `go to <CELL>`
Moves the active Excel location to a specific cell in the active worksheet and sets the start column for the current row-entry block.

Examples:
- `go to A123`
- `go to C7`

### `type pass`
Types `pass` into the current active cell.

### `type fail`
Types `fail` into the current active cell.

### `type n/a`
Types `N/A` into the current active cell. `type not applicable` is an equivalent approved phrase.

### `enter <VALUE>`
Enters text or a number into the active cell. Integer and decimal phrases are stored as numeric Excel values; all other input is stored as text.

Examples:
- `enter inspection complete`
- `enter 42`
- `enter -3.5`

### `undo last change`
Restores the value that existed before the most recent assistant-made Excel cell edit. Undo is deliberately limited to one assistant edit and does not invoke Excel's global undo history. `undo last excel change` is an equivalent approved phrase.

### `go left`
Moves one column to the left. Moving left from column A is rejected clearly.

### `go right`
Moves one column to the right from the current active cell.

### `go down`
Moves one row down from the current active cell.

### `go up`
Moves one row up. Moving up from row 1 is rejected clearly.

### `next row from start`
Moves to the next row and returns to the original start column established by `go to <CELL>`.

### `confirm`
Confirms the current pending risky action in session mode.
If nothing is pending, the assistant returns `No pending action to confirm.`

### `cancel`
Cancels the current pending risky action in session mode.
If nothing is pending, the assistant returns `No pending action to cancel.`

### `status`
Reports whether a risky action is currently pending confirmation.
If one is pending, the response includes the queued action and next step.
If none is pending, the assistant returns `No pending confirmation action.`

## Approved workflows

### `mark pass and next row`
Runs an approved deterministic workflow that types `pass` and moves to the next anchored row.

### `mark fail and next row`
Runs an approved deterministic workflow that types `fail` and moves to the next anchored row.

### `open excel and go to A1`
Runs an approved deterministic workflow that opens Excel and moves to `A1`.

Examples:
- `open excel`
- `open excel and go to A1`
- `mark pass and next row`
- `mark fail and next row`
- `open app notepad`
- `open url https://example.com`
- `open folder C:\Users`
- `open workbook C:\Data\audit.xlsx`
- `select sheet Sheet2`
- `report current sheet`
- `report current cell`
- `go to A123`
- `type pass`
- `go right`
- `type fail`
- `go down`
- `go left`
- `go up`
- `enter 42`
- `type n/a`
- `undo last change`
- `save workbook`
- `next row from start`
- `confirm`
- `cancel`
- `status`

## Unsupported command handling
If the text does not match the approved grammar, the assistant must not guess.
It should create a proposal entry containing:

- original text
- rejection reason
- timestamp or surrounding runtime metadata in later phases

## Safety handling
Safe commands execute immediately.

Risky commands currently requiring confirmation:
- `shutdown`
- `restart`

Blocked commands remain blocked in MVP:
- `kill process <NAME>`
- `run command <TEXT>`

One-shot mode:
- `shutdown` and `restart` return a `[CONFIRMATION REQUIRED]` response and do not execute.
- `status` reports that no pending confirmation exists because one-shot mode does not preserve state after the command finishes.

Session mode:
- `shutdown` or `restart` create a pending action and surface a clear confirmation alert.
- `confirm` executes the pending action.
- `cancel` clears the pending action without executing it.
- `status` reports the currently pending action, if any.

Pending-action expiry:
- Session mode supports an optional pending-action timeout structure.
- The current runtime keeps timeout disabled by default.
- If enabled by configuration, expired pending actions are cleared before the next command is handled.

Workflows inherit the same policy.
If any workflow step requires confirmation, the workflow pauses behind the same confirmation gate instead of bypassing it.
If any workflow step is blocked in MVP, the workflow is blocked as well.

## Explicit MVP blocked commands
The runtime contains explicit deterministic handling for blocked desktop actions such as:

- `kill process <NAME>`
- `run command <TEXT>`

These do not execute.
They return a `blocked in MVP` response instead.

## Near-term planned commands
- save workbook as
- create worksheet
- rename worksheet
- repeat current row pattern
