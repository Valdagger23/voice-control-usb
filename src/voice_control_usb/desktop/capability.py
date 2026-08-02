"""Action contracts declared by the Windows desktop capability."""

from __future__ import annotations

from voice_control_usb.core.capabilities import ActionBinding, ActionSpec, SafetyClass
from voice_control_usb.core.models import Command
from voice_control_usb.desktop.adapter import DesktopAdapter


def desktop_action_specs() -> list[ActionSpec]:
    specs = [
        ActionSpec(
            capability_id="desktop",
            action_id="open_app",
            description="Open an allowlisted desktop application.",
            argument_types={"app_alias": str},
        ),
        ActionSpec(
            capability_id="desktop",
            action_id="open_url",
            description="Open an approved URL.",
            argument_types={"url": str},
        ),
        ActionSpec(
            capability_id="desktop",
            action_id="open_folder",
            description="Open a folder.",
            argument_types={"path": str},
        ),
        ActionSpec(
            capability_id="desktop",
            action_id="shutdown",
            description="Shut down Windows.",
            safety_class=SafetyClass.REQUIRES_CONFIRMATION,
        ),
        ActionSpec(
            capability_id="desktop",
            action_id="restart",
            description="Restart Windows.",
            safety_class=SafetyClass.REQUIRES_CONFIRMATION,
        ),
        ActionSpec(
            capability_id="desktop",
            action_id="blocked_desktop_action",
            description="Represent an explicitly blocked desktop request.",
            safety_class=SafetyClass.BLOCKED,
            argument_types={"request": str},
        ),
    ]
    specs.extend(
        [
            ActionSpec("desktop", "switch_app", "Switch to an approved app.", argument_types={"app_alias": str}),
            ActionSpec("desktop", "close_current_window", "Close the foreground window.", safety_class=SafetyClass.REQUIRES_CONFIRMATION),
            ActionSpec("desktop", "minimize_window", "Minimize the foreground window.", reversible=True),
            ActionSpec("desktop", "maximize_window", "Maximize the foreground window.", reversible=True),
            ActionSpec("desktop", "restore_window", "Restore the foreground window.", reversible=True),
            ActionSpec("desktop", "snap_window", "Snap the foreground window.", reversible=True, argument_types={"side": str}),
            ActionSpec("desktop", "show_desktop", "Show the Windows desktop.", reversible=True),
            ActionSpec("desktop", "desktop_shortcut", "Send an approved editing shortcut.", reversible=True, argument_types={"shortcut": str}),
            ActionSpec("desktop", "take_screenshot", "Capture the desktop to a local file."),
            ActionSpec("desktop", "lock_computer", "Lock the Windows session.", safety_class=SafetyClass.REQUIRES_CONFIRMATION),
            ActionSpec("desktop", "open_settings", "Open an approved Settings area.", argument_types={"area": str}),
            ActionSpec("desktop", "read_clipboard", "Read local clipboard text."),
            ActionSpec("desktop", "clear_clipboard", "Clear the local clipboard.", safety_class=SafetyClass.REQUIRES_CONFIRMATION, reversible=True),
        ]
    )
    return specs


class DesktopCapability:
    """Expose allowlisted Windows desktop operations as capability bindings."""

    capability_id = "desktop"

    def __init__(self, adapter: DesktopAdapter) -> None:
        self.adapter = adapter

    def bindings(self) -> list[ActionBinding]:
        handlers = {
            "open_app": self._open_app,
            "open_url": self._open_url,
            "open_folder": self._open_folder,
            "shutdown": self._shutdown,
            "restart": self._restart,
            "blocked_desktop_action": self._blocked_desktop_action,
            "switch_app": lambda c: self.adapter.switch_app(self._string_argument(c, "app_alias")),
            "close_current_window": lambda c: self.adapter.close_current_window(),
            "minimize_window": lambda c: self.adapter.set_window_state("minimized"),
            "maximize_window": lambda c: self.adapter.set_window_state("maximized"),
            "restore_window": lambda c: self.adapter.set_window_state("restored"),
            "snap_window": lambda c: self.adapter.snap_window(self._string_argument(c, "side")),
            "show_desktop": lambda c: self.adapter.show_desktop(),
            "desktop_shortcut": lambda c: self.adapter.send_shortcut(self._string_argument(c, "shortcut")),
            "take_screenshot": lambda c: self.adapter.take_screenshot(),
            "lock_computer": lambda c: self.adapter.lock_computer(),
            "open_settings": lambda c: self.adapter.open_settings(self._string_argument(c, "area")),
            "read_clipboard": lambda c: self.adapter.read_clipboard(),
            "clear_clipboard": lambda c: self.adapter.clear_clipboard(),
        }
        return [ActionBinding(spec, handlers[spec.action_id]) for spec in desktop_action_specs()]

    def _open_app(self, command: Command) -> str:
        return self.adapter.open_app(self._string_argument(command, "app_alias"))

    def _open_url(self, command: Command) -> str:
        return self.adapter.open_url(self._string_argument(command, "url"))

    def _open_folder(self, command: Command) -> str:
        return self.adapter.open_folder(self._string_argument(command, "path"))

    def _shutdown(self, command: Command) -> str:
        return self.adapter.shutdown()

    def _restart(self, command: Command) -> str:
        return self.adapter.restart()

    def _blocked_desktop_action(self, command: Command) -> str:
        request = self._string_argument(command, "request")
        return f"Desktop action is blocked in MVP: {request}"

    @staticmethod
    def _string_argument(command: Command, name: str) -> str:
        value = command.arguments.get(name)
        if not isinstance(value, str):
            raise ValueError(f"Action '{command.action}' argument '{name}' must be str.")
        return value
