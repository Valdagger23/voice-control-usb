"""Declared Discord actions and privacy safety classes."""

from __future__ import annotations

from voice_control_usb.core.capabilities import ActionBinding, ActionResult, ActionSpec, SafetyClass
from voice_control_usb.core.models import Command
from voice_control_usb.discord.adapter import DiscordAdapter, DiscordSnapshot


def discord_action_specs() -> list[ActionSpec]:
    confirm = SafetyClass.REQUIRES_CONFIRMATION
    return [
        ActionSpec("discord", "open_discord", "Open or focus Discord."),
        ActionSpec("discord", "discord_navigate", "Navigate to an allowlisted Discord target.", argument_types={"alias": str}),
        ActionSpec("discord", "discord_set_draft", "Place one visible unsent Discord draft.", reversible=True, argument_types={"text": str}),
        ActionSpec("discord", "discord_cancel_draft", "Clear the current Discord draft.", reversible=True),
        ActionSpec("discord", "discord_prepare_send", "Prepare a confirmed draft for the user's physical send action.", safety_class=confirm),
        ActionSpec("discord", "discord_mute_microphone", "Mute the Discord microphone.", reversible=True),
        ActionSpec("discord", "discord_unmute_microphone", "Unmute the Discord microphone.", safety_class=confirm, reversible=True),
        ActionSpec("discord", "discord_deafen", "Deafen Discord.", reversible=True),
        ActionSpec("discord", "discord_undeafen", "Undeafen Discord.", safety_class=confirm, reversible=True),
        ActionSpec("discord", "discord_disable_camera", "Disable the Discord camera.", reversible=True),
        ActionSpec("discord", "discord_enable_camera", "Enable the Discord camera.", safety_class=confirm, reversible=True),
        ActionSpec("discord", "discord_report_status", "Report visible Discord draft and device state."),
        ActionSpec("discord", "discord_blocked_action", "Reject self-bot, bulk, or token automation.", safety_class=SafetyClass.BLOCKED, argument_types={"request": str}),
    ]


class DiscordCapability:
    capability_id = "discord"

    def __init__(self, adapter: DiscordAdapter) -> None: self.adapter = adapter

    def bindings(self) -> list[ActionBinding]:
        handlers = {
            "open_discord": lambda c: self._result(c, self.adapter.open(), "Discord ready"),
            "discord_navigate": lambda c: self._result(c, self.adapter.navigate(self._text(c, "alias")), "Discord target opened"),
            "discord_set_draft": lambda c: self._result(c, self.adapter.set_draft(self._text(c, "text")), "Discord draft visible"),
            "discord_cancel_draft": lambda c: self._result(c, self.adapter.cancel_draft(), "Discord draft canceled"),
            "discord_prepare_send": lambda c: self._result(c, self.adapter.prepare_send(), "Discord draft ready; press Enter yourself to send"),
            "discord_mute_microphone": lambda c: self._result(c, self.adapter.set_microphone_muted(True), "Discord microphone muted"),
            "discord_unmute_microphone": lambda c: self._result(c, self.adapter.set_microphone_muted(False), "Discord microphone unmuted"),
            "discord_deafen": lambda c: self._result(c, self.adapter.set_deafened(True), "Discord deafened"),
            "discord_undeafen": lambda c: self._result(c, self.adapter.set_deafened(False), "Discord undeafened"),
            "discord_disable_camera": lambda c: self._result(c, self.adapter.set_camera_enabled(False), "Discord camera disabled"),
            "discord_enable_camera": lambda c: self._result(c, self.adapter.set_camera_enabled(True), "Discord camera enabled"),
            "discord_report_status": lambda c: self._result(c, self.adapter.report(), "Discord status"),
            "discord_blocked_action": lambda c: ActionResult("discord", c.action, f"Discord action is blocked: {self._text(c, 'request')}", succeeded=False),
        }
        return [ActionBinding(spec, handlers[spec.action_id]) for spec in discord_action_specs()]

    def _result(self, command: Command, state: DiscordSnapshot, prefix: str) -> ActionResult:
        details = {
            "target": state.target,
            "draft_present": bool(state.draft),
            "microphone_muted": state.microphone_muted,
            "deafened": state.deafened,
            "camera_enabled": state.camera_enabled,
        }
        draft = "draft present" if state.draft else "no draft"
        message = f"{prefix}: {state.target or 'current view'}; {draft}; mic={self._state(state.microphone_muted)}, deafened={self._state(state.deafened)}, camera={self._state(state.camera_enabled)}."
        return ActionResult("discord", command.action, message, details=details)

    @staticmethod
    def _state(value: bool | None) -> str:
        return "unknown" if value is None else ("on" if value else "off")

    @staticmethod
    def _text(command: Command, name: str) -> str:
        value = command.arguments.get(name)
        if not isinstance(value, str): raise ValueError(f"Discord argument '{name}' must be text.")
        return value
