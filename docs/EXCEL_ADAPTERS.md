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

Examples:
- `PYTHONPATH=src .venv/bin/python -m voice_control_usb "open excel"`
- `python -m voice_control_usb --excel-adapter com "open excel"`

You can also select the adapter through:
- `VOICE_CONTROL_USB_EXCEL_ADAPTER=stub`
- `VOICE_CONTROL_USB_EXCEL_ADAPTER=com`

## WSL behavior
WSL development and tests continue to use the stub adapter.
The stub preserves deterministic movement semantics for:

- `open excel`
- `go to A123`
- `type pass`
- `type fail`
- `go right`
- `go down`
- `next row from start`

No live Excel process is controlled in WSL.

## Windows COM behavior
The COM adapter uses `win32com.client.Dispatch("Excel.Application")` and works through object-level Excel control.
It does not use keyboard or mouse automation as the primary control path.

Implemented commands:
- `open excel`
- `go to A123`
- `type pass`
- `type fail`
- `go right`
- `go down`
- `next row from start`

`next row from start` preserves the same anchor semantics as the stub adapter by remembering the column established by `go to <CELL>`.

## Windows setup
Install the Windows dependency in a Windows Python environment:

- `pip install pywin32`

Or:

- `pip install .[windows]`

## Manual Windows verification
Run these in a Windows shell from the repository root:

```powershell
python -m pip install pywin32
$env:PYTHONPATH = "src"
python -m voice_control_usb --excel-adapter com "open excel"
python -m voice_control_usb --excel-adapter com "go to A123"
python -m voice_control_usb --excel-adapter com "type pass"
python -m voice_control_usb --excel-adapter com "go right"
python -m voice_control_usb --excel-adapter com "type fail"
python -m voice_control_usb --excel-adapter com "next row from start"
```

Expected behavior:
- Excel opens visibly.
- Selection moves to `A123`.
- `pass` is written to `A123`.
- Selection moves to `B123`.
- `fail` is written to `B123`.
- `next row from start` moves selection to `A124`.
