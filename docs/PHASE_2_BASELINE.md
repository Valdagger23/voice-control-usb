# Phase 2 Baseline

## Outcome

Phase 2 delivers a usable typed Excel vertical slice on native Windows. The same deterministic parser, safety policy, capability registry, executor, and audit path now serve terminal sessions and a small visible Windows command shell.

## Delivered behavior

- Visible Windows shell with typed command entry, transcript, execution status, and error display.
- Native Excel COM control for opening Excel and workbooks, selecting sheets, saving, navigating, reporting, and editing cells.
- `enter <VALUE>` support for text, integers, and decimal values.
- Fixed `pass`, `fail`, and `N/A` entry commands.
- Left, right, up, and down movement with clear top/left worksheet boundary failures.
- Current-cell address and value reporting.
- One-level undo that restores the value before the last assistant-made cell edit, including after moving to another sheet.
- Deterministic rejection of out-of-bounds Excel cell references and oversized cell text.
- Clear failures for missing workbooks, protected worksheets, and disconnected Excel sessions.
- Existing row-entry workflows remain available through the capability contract.

## Safety and recovery boundary

Undo records only the most recent assistant-made cell edit. It does not invoke Excel's global undo stack and therefore does not undo unrelated user actions. Workbook saving remains explicit. The native verification uses a new isolated Excel process and a temporary workbook, then closes both without touching user workbooks.

## Verification completed

- Automated suite: 118 completed; 116 passed and 2 platform-documentation checks skipped on Windows.
- Native COM verification: passed using `scripts\verify_excel_com.py` with an isolated temporary workbook.
- Verified real Excel numeric and text entry, current-cell reporting, four-way movement, one-level undo including formula restoration, save, protected-sheet rejection, and missing-workbook rejection.
- Verified that the isolated Excel process and temporary workbook were removed after the check.

## Run the visible assistant

From `D:\VoiceControl` in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[windows]"
.\.venv\Scripts\python.exe -m voice_control_usb --window
```

On Windows, window mode chooses the native COM Excel adapter by default. To demonstrate the window without touching Excel, pass `--excel-adapter stub` explicitly.

Useful commands:

```text
open excel
open workbook C:\path\to\workbook.xlsx
select sheet Sheet1
go to A1
enter 42
report current cell
go right
type pass
go down
go left
type n/a
undo last change
save workbook
```

## Repeat native verification

```powershell
.\.venv\Scripts\python.exe scripts\verify_excel_com.py
```

The verification creates and closes its own hidden Excel instance and temporary workbook.
