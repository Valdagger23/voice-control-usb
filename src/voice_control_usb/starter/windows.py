"""Windows-only removable-drive discovery for the trusted USB starter."""

from __future__ import annotations

import ctypes
from pathlib import Path
import platform

from voice_control_usb.starter.service import UsbVolume

DRIVE_REMOVABLE = 2


class WindowsUsbVolumeProvider:
    """Enumerate removable drives and their volume labels on Windows."""

    def list_volumes(self) -> list[UsbVolume]:
        if platform.system() != "Windows":
            raise RuntimeError("Windows USB volume discovery is only available on Windows.")

        kernel32 = ctypes.windll.kernel32
        buffer = ctypes.create_unicode_buffer(512)
        length = kernel32.GetLogicalDriveStringsW(len(buffer), buffer)
        if length <= 0:
            return []

        # GetLogicalDriveStringsW returns a multi-string. ``buffer.value`` stops
        # at the first NUL and therefore hides every drive after the first one.
        drives = _split_logical_drive_strings("".join(buffer[:length]))
        volumes: list[UsbVolume] = []
        for drive in drives:
            if kernel32.GetDriveTypeW(ctypes.c_wchar_p(drive)) != DRIVE_REMOVABLE:
                continue

            label_buffer = ctypes.create_unicode_buffer(261)
            serial_number = ctypes.c_ulong()
            max_component_length = ctypes.c_ulong()
            filesystem_flags = ctypes.c_ulong()
            filesystem_name = ctypes.create_unicode_buffer(261)
            success = kernel32.GetVolumeInformationW(
                ctypes.c_wchar_p(drive),
                label_buffer,
                len(label_buffer),
                ctypes.byref(serial_number),
                ctypes.byref(max_component_length),
                ctypes.byref(filesystem_flags),
                filesystem_name,
                len(filesystem_name),
            )
            if not success:
                continue

            volumes.append(
                UsbVolume(
                    mount_path=Path(drive),
                    volume_label=label_buffer.value,
                )
            )

        return volumes


def _split_logical_drive_strings(raw: str) -> list[str]:
    """Split the NUL-delimited value returned by GetLogicalDriveStringsW."""

    return [entry for entry in raw.split("\x00") if entry]
