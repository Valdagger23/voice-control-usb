# Commands

## Command design rules
- Commands must parse deterministically.
- Each command must map to one approved handler.
- Ambiguous natural language should be rejected and logged as a proposal.
- Excel-oriented actions should target object-level operations first.

## Supported phase-1 commands

### `open excel`
Opens or attaches to an Excel session.

### `read cell <CELL>`
Reads a single cell from the active worksheet.

Examples:
- `read cell A1`
- `read cell AA10`

### `write cell <CELL> value <TEXT>`
Writes plain text to a single cell in the active worksheet.

Examples:
- `write cell B2 value hello`
- `write cell C10 value quarterly total`

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
- read range
- write range
