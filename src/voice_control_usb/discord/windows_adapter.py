"""State-aware visible Discord control through Windows UI Automation."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import time

from voice_control_usb.discord.adapter import DiscordAdapter, DiscordSnapshot
from voice_control_usb.discord.registry import DiscordTargetRegistry


class WindowsDiscordAdapter(DiscordAdapter):
    def __init__(self, registry: DiscordTargetRegistry) -> None:
        self.registry = registry
        self.target = ""
        self.draft = ""
        self.input_volume: int | None = None
        self.output_volume: int | None = None

    def open(self) -> DiscordSnapshot:
        window = self._window(launch=True)
        window.SetActive()
        return self.report()

    def navigate(self, alias: str) -> DiscordSnapshot:
        target = self.registry.resolve(alias)
        if target is None:
            raise ValueError(f"Discord target alias is not configured: {alias}")
        self._window(launch=True)
        os.startfile(target.uri)
        self.target = target.label
        self.draft = ""
        time.sleep(1)
        self._window().SetActive()
        return self.report()

    def set_draft(self, text: str) -> DiscordSnapshot:
        if not text.strip(): raise ValueError("Discord draft must not be empty.")
        composer = self._composer()
        pattern = self._editable_value_pattern(composer)
        pattern.SetValue(text)
        self.draft = text
        composer.SetFocus()
        return self.report()

    def cancel_draft(self) -> DiscordSnapshot:
        composer = self._composer()
        self._editable_value_pattern(composer).SetValue("")
        self.draft = ""
        return self.report()

    def prepare_send(self) -> DiscordSnapshot:
        if not self.draft: raise RuntimeError("There is no Discord draft to prepare.")
        composer = self._composer()
        current = self._editable_value_pattern(composer).Value
        if current != self.draft:
            raise RuntimeError("Discord draft changed; review and draft it again before sending.")
        composer.SetFocus()
        return self.report()

    def set_microphone_muted(self, muted: bool) -> DiscordSnapshot:
        self._set_binary_button(muted, enabled_name="Unmute", disabled_name="Mute", label="microphone")
        return self.report()

    def set_deafened(self, deafened: bool) -> DiscordSnapshot:
        self._set_binary_button(deafened, enabled_name="Undeafen", disabled_name="Deafen", label="deafen")
        return self.report()

    def set_camera_enabled(self, enabled: bool) -> DiscordSnapshot:
        self._set_binary_button(
            enabled,
            enabled_name="Turn Off Camera",
            disabled_name="Turn On Camera",
            label="camera",
        )
        return self.report()

    def report(self) -> DiscordSnapshot:
        window = self._window()
        return DiscordSnapshot(
            target=self.target or window.Name.removesuffix(" - Discord"),
            draft=self.draft,
            microphone_muted=self._button_state("Unmute", "Mute"),
            deafened=self._button_state("Undeafen", "Deafen"),
            camera_enabled=self._button_state("Turn Off Camera", "Turn On Camera"),
            input_volume=self.input_volume,
            output_volume=self.output_volume,
            in_call=self._disconnect_button() is not None,
        )

    def join_channel(self, alias: str) -> DiscordSnapshot:
        self.navigate(alias)
        window = self._window()
        button = window.ButtonControl(RegexName=r"^(?:Join Voice|Connect)$", searchDepth=30)
        if button.Exists(2):
            button.GetInvokePattern().Invoke()
            time.sleep(1)
        if self._disconnect_button() is None:
            raise RuntimeError("Discord did not expose a reliable voice-channel join control.")
        return self.report()

    def leave_call(self) -> DiscordSnapshot:
        button = self._disconnect_button()
        if button is None:
            raise RuntimeError("Discord is not currently exposing an active call.")
        button.GetInvokePattern().Invoke()
        time.sleep(0.5)
        return self.report()

    def read_channel(self) -> str:
        return self.target or self._window().Name.removesuffix(" - Discord")

    def read_latest_message(self) -> str:
        try:
            import uiautomation as auto
        except ImportError as error:
            raise ImportError("Windows Discord control requires uiautomation.") from error
        candidates: list[str] = []
        try:
            for control, depth in auto.WalkControl(self._window(), includeTop=False, maxDepth=35):
                if depth > 35 or control.ControlTypeName not in {"TextControl", "DocumentControl"}:
                    continue
                name = " ".join(str(control.Name or "").split())
                if name and len(name) <= 500 and control.IsEnabled:
                    candidates.append(name)
        except Exception as error:
            raise RuntimeError(f"Discord message accessibility scan failed: {error}") from error
        if not candidates:
            raise RuntimeError("No readable Discord message is visible in the current channel.")
        return candidates[-1]

    def set_input_volume(self, percent: int) -> DiscordSnapshot:
        self._set_settings_slider("Input Volume", percent)
        self.input_volume = percent
        return self.report()

    def set_output_volume(self, percent: int) -> DiscordSnapshot:
        self._set_settings_slider("Output Volume", percent)
        self.output_volume = percent
        return self.report()

    def prepare_screen_share(self) -> DiscordSnapshot:
        if self._disconnect_button() is None:
            raise RuntimeError("Join a Discord call before preparing screen share.")
        button = self._window().ButtonControl(
            RegexName=r"^(?:Share Your Screen|Share Screen|Screen)$",
            searchDepth=30,
        )
        if not button.Exists(2):
            raise RuntimeError("Discord does not expose a screen-share button in the current call view.")
        button.GetInvokePattern().Invoke()
        return self.report()

    def _set_binary_button(self, desired: bool, *, enabled_name: str, disabled_name: str, label: str) -> None:
        current = self._button_state(enabled_name, disabled_name)
        if current is None:
            raise RuntimeError(f"Discord does not expose reliable {label} state in the current view.")
        if current == desired:
            return
        action_name = disabled_name if desired else enabled_name
        button = self._window().ButtonControl(Name=action_name, searchDepth=30)
        if not button.Exists(1):
            raise RuntimeError(f"Discord {label} state changed before the action could run.")
        button.GetInvokePattern().Invoke()

    def _button_state(self, enabled_name: str, disabled_name: str) -> bool | None:
        window = self._window()
        if window.ButtonControl(Name=enabled_name, searchDepth=30).Exists(0): return True
        if window.ButtonControl(Name=disabled_name, searchDepth=30).Exists(0): return False
        return None

    def _disconnect_button(self):
        button = self._window().ButtonControl(
            RegexName=r"^(?:Disconnect|Leave Call)$",
            searchDepth=30,
        )
        return button if button.Exists(0) else None

    def _set_settings_slider(self, name: str, percent: int) -> None:
        if not 0 <= percent <= 100:
            raise ValueError("Discord volume must be between 0 and 100 percent.")
        window = self._window()
        slider = window.SliderControl(Name=name, searchDepth=35)
        if not slider.Exists(0):
            settings = window.ButtonControl(Name="User Settings", searchDepth=30)
            if not settings.Exists(2):
                raise RuntimeError("Discord does not expose the User Settings control.")
            settings.GetInvokePattern().Invoke()
            time.sleep(0.8)
            slider = self._window().SliderControl(Name=name, searchDepth=35)
        if not slider.Exists(2):
            raise RuntimeError(f"Discord does not expose the {name} slider.")
        pattern = slider.GetRangeValuePattern()
        if pattern is None or pattern.IsReadOnly:
            raise RuntimeError(f"Discord {name} is not safely adjustable.")
        minimum, maximum = float(pattern.Minimum), float(pattern.Maximum)
        pattern.SetValue(minimum + ((maximum - minimum) * percent / 100))

    def _composer(self):
        composer = self._window().EditControl(RegexName=r"^Message(?: |$)", searchDepth=30)
        if not composer.Exists(2):
            raise RuntimeError("No accessible Discord message composer is visible. Open a configured text target first.")
        return composer

    @staticmethod
    def _editable_value_pattern(composer):
        pattern = composer.GetValuePattern()
        if pattern is None or pattern.IsReadOnly:
            raise RuntimeError("Discord message composer does not expose safe editable text state.")
        return pattern

    def _window(self, *, launch: bool = False):
        try:
            import uiautomation as auto
        except ImportError as error:
            raise ImportError("Windows Discord control requires uiautomation.") from error
        window = auto.WindowControl(searchDepth=1, RegexName=r".+ - Discord$")
        if not window.Exists(1) and launch:
            self._launch_discord()
            window = auto.WindowControl(searchDepth=1, RegexName=r".+ - Discord$")
            window.Exists(15)
        if not window.Exists(0):
            raise RuntimeError("Discord is not running with a visible main window.")
        root = window.DocumentControl(AutomationId="RootWebArea", searchDepth=15)
        if not root.Exists(1) or not root.Name:
            raise RuntimeError(
                "Discord accessibility state is unavailable. Fully exit Discord, then open it through Voice Control."
            )
        return window

    @staticmethod
    def _launch_discord() -> None:
        local_app_data = os.environ.get("LOCALAPPDATA")
        if not local_app_data:
            raise RuntimeError("Windows LOCALAPPDATA is required to locate Discord.")
        update = Path(local_app_data) / "Discord" / "Update.exe"
        if not update.is_file():
            raise FileNotFoundError(f"Discord launcher was not found: {update}")
        subprocess.Popen(
            [
                str(update),
                "--processStart",
                "Discord.exe",
                "--process-start-args",
                "--force-renderer-accessibility",
            ],
            shell=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
