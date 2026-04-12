"""Registry of supported deterministic commands."""

from __future__ import annotations

from voice_control_usb.core.models import CommandName


SUPPORTED_COMMANDS: dict[CommandName, str] = {
    CommandName.OPEN_EXCEL: "Launch or attach to Microsoft Excel.",
    CommandName.READ_CELL: "Read a single cell from the active workbook.",
    CommandName.WRITE_CELL: "Write a value to a single cell in the active workbook.",
}
