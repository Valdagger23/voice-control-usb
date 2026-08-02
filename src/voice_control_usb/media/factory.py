"""Media adapter selection for deterministic and native Windows runtimes."""

from __future__ import annotations

import importlib.util
import sys

from voice_control_usb.media.adapter import MediaAdapter, StubMediaAdapter
from voice_control_usb.media.windows_adapter import WindowsMediaAdapter


def create_media_adapter(selection: str = "stub") -> MediaAdapter:
    """Create the configured media adapter implementation."""

    normalized = selection.strip().lower()
    if normalized == "stub":
        return StubMediaAdapter()
    if normalized == "windows":
        if sys.platform != "win32":
            raise RuntimeError("The Windows media adapter is only available on Windows.")
        missing = []
        for package in ("winrt.windows.media.control", "pycaw"):
            try:
                available = importlib.util.find_spec(package) is not None
            except ModuleNotFoundError:
                available = False
            if not available:
                missing.append(package)
        if missing:
            raise ImportError(
                "Windows media dependencies are missing. Install the project with "
                "'pip install .[windows]'."
            )
        return WindowsMediaAdapter()
    raise ValueError(
        "Unknown media adapter selection. Expected one of: 'stub', 'windows'."
    )
