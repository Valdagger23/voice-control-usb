# Excel Adapters

## Overview
The deterministic engine talks to Excel through the `ExcelAdapter` interface.
Two implementations now exist:

- `stub`
  Default adapter for WSL development and automated tests.
- `com`
  Windows-only adapter that drives Excel through COM object APIs.

## Adapter selection
The CLI defaults to the stub adapter.
One-shot CLI invocations run a single command and exit.
Session mode keeps one assistant process alive, so workbook and worksheet context persists across commands in that session.
Speech session mode reuses the same assistant process and adapter state after transcription.

Examples:
- `PYTHONPATH=src .venv/bin/python -m voice_control_usb "open excel"`
- `printf 'open excel\nquit\n' | PYTHONPATH=src .venv/bin/python -m voice_control_usb --session`
- `printf 'record open excel\nquit\n' | PYTHONPATH=src .venv/bin/python -m voice_control_usb --session --input-mode speech`
- `python -m voice_control_usb --session --input-mode speech --speech-provider speech_recognition`
- `python -m voice_control_usb --excel-adapter com "open excel"`
- `python -m voice_control_usb --excel-adapter com --session`
- `python -m voice_control_usb --excel-adapter com --session --input-mode speech`

You can also select the adapter through:
- `VOICE_CONTROL_USB_EXCEL_ADAPTER=stub`
- `VOICE_CONTROL_USB_EXCEL_ADAPTER=com`

## WSL behavior
WSL development and tests continue to use the stub adapter.
The stub preserves deterministic workbook, sheet, and movement semantics for:

- `open excel`
- `open workbook <PATH>`
- `select sheet <NAME>`
- `save workbook`
- `report current sheet`
- `go to A123`
- `type pass`
- `type fail`
- `go right`
- `go down`
- `next row from start`

No live Excel process is controlled in WSL.
Speech input is also stubbed in WSL through a manual text transcriber.

## Manual WSL verification
Run these from the repository root:

```bash
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
printf 'open workbook /tmp/context.xlsx\nselect sheet Sheet2\nreport current sheet\ngo to A123\ntype pass\ngo right\ntype fail\nsave workbook\nnext row from start\nquit\n' | PYTHONPATH=src .venv/bin/python -m voice_control_usb --session
printf 'record open workbook /tmp/context.xlsx\nrecord select sheet Sheet2\nrecord report current sheet\nrecord go to A123\nrecord type pass\nquit\n' | PYTHONPATH=src .venv/bin/python -m voice_control_usb --session --input-mode speech
```

Expected behavior:
- The stub opens `context.xlsx` as the active workbook context.
- `Sheet2` becomes the active sheet.
- `report current sheet` reports `Sheet2` and `context.xlsx`.
- `pass` and `fail` are written into stub-managed cell storage.
- `save workbook` succeeds because the workbook was opened with a path.

## Windows COM behavior
The COM adapter uses `win32com.client.Dispatch("Excel.Application")` and works through object-level Excel control.
It does not use keyboard or mouse automation as the primary control path.

Implemented commands:
- `open excel`
- `open workbook <PATH>`
- `select sheet <NAME>`
- `save workbook`
- `report current sheet`
- `go to A123`
- `type pass`
- `type fail`
- `go right`
- `go down`
- `next row from start`

`next row from start` preserves the same anchor semantics as the stub adapter by remembering the column established by `go to <CELL>`.
Workbook and worksheet context are explicit, so commands like `select sheet <NAME>` and `report current sheet` operate against the active workbook instead of assuming only a single active selection.

## Windows setup
Install the Windows dependency in a Windows Python environment:

- `pip install pywin32`

Or:

- `pip install .[windows]`

## Manual Windows verification
Run these in a Windows shell from the repository root.
Use a single Python process for context-sensitive workflows:

```powershell
python -m pip install pywin32
$env:PYTHONPATH = "src"
@"
open excel
open workbook C:\path\to\context.xlsx
select sheet Sheet2
report current sheet
go to A123
type pass
go right
type fail
save workbook
next row from start
quit
"@ | python -m voice_control_usb --excel-adapter com --session

@"
record open excel
record open workbook C:\path\to\context.xlsx
record select sheet Sheet2
record report current sheet
record go to A123
record type pass
quit
"@ | python -m voice_control_usb --excel-adapter com --session --input-mode speech
```

Expected behavior:
- Excel opens visibly.
- The requested workbook becomes active.
- `Sheet2` becomes the active sheet.
- `report current sheet` reports the active workbook and sheet.
- Selection moves to `A123`.
- `pass` is written to `A123`.
- Selection moves to `B123`.
- `fail` is written to `B123`.
- `save workbook` saves the active workbook through COM.
- `next row from start` moves selection to `A124`.
