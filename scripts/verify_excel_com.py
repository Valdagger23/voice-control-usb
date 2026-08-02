"""Safely verify the Phase 2 Excel commands in an isolated Windows Excel process."""

from __future__ import annotations

from pathlib import Path
import sys
from tempfile import TemporaryDirectory

from voice_control_usb.excel.com_adapter import ComExcelAdapter


def expect(actual: str, expected: str) -> None:
    print(actual)
    assert actual == expected, f"Expected {expected!r}; received {actual!r}"


def main() -> int:
    if sys.platform != "win32":
        print("SKIP: native Excel COM verification requires Windows.")
        return 0

    import win32com.client  # type: ignore[import-not-found]

    excel = win32com.client.DispatchEx("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    try:
        with TemporaryDirectory(prefix="voice-control-excel-") as folder:
            workbook_path = Path(folder) / "phase2-verification.xlsx"
            workbook = excel.Workbooks.Add()
            try:
                workbook.SaveAs(str(workbook_path))

                adapter = ComExcelAdapter(visible=False, _excel=excel)
                expect(adapter.go_to_cell("B2"), "Moved to B2")
                expect(adapter.type_text(42), "Typed 42 into B2")
                expect(adapter.report_current_cell(), "Current cell: B2 (value: 42)")
                expect(adapter.go_right(), "Moved right to C2")
                expect(adapter.go_down(), "Moved down to C3")
                expect(adapter.go_left(), "Moved left to B3")
                expect(adapter.go_up(), "Moved up to B2")
                expect(adapter.type_text("N/A"), "Typed 'N/A' into B2")
                expect(
                    adapter.undo_last_change(),
                    "Undid last Excel change in Sheet1!B2.",
                )
                expect(adapter.report_current_cell(), "Current cell: B2 (value: 42)")

                workbook.Worksheets("Sheet1").Range("B2").Formula = "=40+2"
                expect(adapter.type_text("temporary"), "Typed 'temporary' into B2")
                expect(
                    adapter.undo_last_change(),
                    "Undid last Excel change in Sheet1!B2.",
                )
                assert workbook.Worksheets("Sheet1").Range("B2").Formula == "=40+2"
                assert adapter.save_workbook().startswith("Saved workbook:")

                workbook.Worksheets("Sheet1").Protect()
                try:
                    adapter.type_text("blocked")
                except ValueError as error:
                    assert "protected" in str(error).lower()
                else:
                    raise AssertionError("Protected worksheet edit was not rejected.")
                workbook.Worksheets("Sheet1").Unprotect()

                missing_path = Path(folder) / "missing.xlsx"
                try:
                    adapter.open_workbook(str(missing_path))
                except FileNotFoundError:
                    pass
                else:
                    raise AssertionError("Missing workbook was not rejected.")

                print("PASS: isolated native Excel COM vertical slice verified.")
            finally:
                workbook.Close(SaveChanges=False)
            return 0
    finally:
        excel.Quit()


if __name__ == "__main__":
    raise SystemExit(main())
