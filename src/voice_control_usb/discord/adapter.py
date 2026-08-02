"""Discord UI boundary and deterministic stub."""

from __future__ import annotations

from dataclasses import dataclass

from voice_control_usb.discord.registry import DiscordTargetRegistry


@dataclass(frozen=True, slots=True)
class DiscordSnapshot:
    target: str = ""
    draft: str = ""
    microphone_muted: bool | None = None
    deafened: bool | None = None
    camera_enabled: bool | None = None
    latest_message: str = ""
    input_volume: int | None = None
    output_volume: int | None = None
    in_call: bool | None = None


class DiscordAdapter:
    def open(self) -> DiscordSnapshot: raise NotImplementedError
    def navigate(self, alias: str) -> DiscordSnapshot: raise NotImplementedError
    def set_draft(self, text: str) -> DiscordSnapshot: raise NotImplementedError
    def cancel_draft(self) -> DiscordSnapshot: raise NotImplementedError
    def prepare_send(self) -> DiscordSnapshot: raise NotImplementedError
    def set_microphone_muted(self, muted: bool) -> DiscordSnapshot: raise NotImplementedError
    def set_deafened(self, deafened: bool) -> DiscordSnapshot: raise NotImplementedError
    def set_camera_enabled(self, enabled: bool) -> DiscordSnapshot: raise NotImplementedError
    def report(self) -> DiscordSnapshot: raise NotImplementedError
    def join_channel(self, alias: str) -> DiscordSnapshot: raise NotImplementedError
    def leave_call(self) -> DiscordSnapshot: raise NotImplementedError
    def read_channel(self) -> str: raise NotImplementedError
    def read_latest_message(self) -> str: raise NotImplementedError
    def set_input_volume(self, percent: int) -> DiscordSnapshot: raise NotImplementedError
    def set_output_volume(self, percent: int) -> DiscordSnapshot: raise NotImplementedError
    def prepare_screen_share(self) -> DiscordSnapshot: raise NotImplementedError


class StubDiscordAdapter(DiscordAdapter):
    def __init__(self, registry: DiscordTargetRegistry | None = None) -> None:
        self.registry = registry or DiscordTargetRegistry({})
        self.snapshot = DiscordSnapshot(
            microphone_muted=False,
            deafened=False,
            camera_enabled=False,
            latest_message="No visible messages",
            input_volume=100,
            output_volume=100,
            in_call=False,
        )

    def open(self) -> DiscordSnapshot:
        return self.snapshot

    def navigate(self, alias: str) -> DiscordSnapshot:
        target = self.registry.resolve(alias)
        if target is None:
            raise ValueError(f"Discord target alias is not configured: {alias}")
        self.snapshot = self._replace(target=target.label, draft="")
        return self.snapshot

    def set_draft(self, text: str) -> DiscordSnapshot:
        if not text.strip(): raise ValueError("Discord draft must not be empty.")
        self.snapshot = self._replace(draft=text)
        return self.snapshot

    def cancel_draft(self) -> DiscordSnapshot:
        self.snapshot = self._replace(draft="")
        return self.snapshot

    def prepare_send(self) -> DiscordSnapshot:
        if not self.snapshot.draft: raise RuntimeError("There is no Discord draft to prepare.")
        return self.snapshot

    def set_microphone_muted(self, muted: bool) -> DiscordSnapshot:
        self.snapshot = self._replace(microphone_muted=muted)
        return self.snapshot

    def set_deafened(self, deafened: bool) -> DiscordSnapshot:
        self.snapshot = self._replace(deafened=deafened)
        return self.snapshot

    def set_camera_enabled(self, enabled: bool) -> DiscordSnapshot:
        self.snapshot = self._replace(camera_enabled=enabled)
        return self.snapshot

    def report(self) -> DiscordSnapshot:
        return self.snapshot

    def join_channel(self, alias: str) -> DiscordSnapshot:
        target = self.registry.resolve(alias)
        if target is None:
            raise ValueError(f"Discord target alias is not configured: {alias}")
        self.snapshot = self._replace(target=target.label, in_call=True)
        return self.snapshot

    def leave_call(self) -> DiscordSnapshot:
        self.snapshot = self._replace(in_call=False, camera_enabled=False)
        return self.snapshot

    def read_channel(self) -> str:
        return self.snapshot.target or "current view"

    def read_latest_message(self) -> str:
        return self.snapshot.latest_message or "No visible Discord message."

    def set_input_volume(self, percent: int) -> DiscordSnapshot:
        self._validate_percent(percent)
        self.snapshot = self._replace(input_volume=percent)
        return self.snapshot

    def set_output_volume(self, percent: int) -> DiscordSnapshot:
        self._validate_percent(percent)
        self.snapshot = self._replace(output_volume=percent)
        return self.snapshot

    def prepare_screen_share(self) -> DiscordSnapshot:
        if not self.snapshot.in_call:
            raise RuntimeError("Join a Discord call before preparing screen share.")
        return self.snapshot

    def _replace(self, **changes) -> DiscordSnapshot:
        values = {name: getattr(self.snapshot, name) for name in self.snapshot.__dataclass_fields__}
        values.update(changes)
        return DiscordSnapshot(**values)

    @staticmethod
    def _validate_percent(percent: int) -> None:
        if not 0 <= percent <= 100:
            raise ValueError("Discord volume must be between 0 and 100 percent.")
