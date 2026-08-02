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


class StubDiscordAdapter(DiscordAdapter):
    def __init__(self, registry: DiscordTargetRegistry | None = None) -> None:
        self.registry = registry or DiscordTargetRegistry({})
        self.snapshot = DiscordSnapshot(
            microphone_muted=False,
            deafened=False,
            camera_enabled=False,
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

    def _replace(self, **changes) -> DiscordSnapshot:
        values = {name: getattr(self.snapshot, name) for name in self.snapshot.__dataclass_fields__}
        values.update(changes)
        return DiscordSnapshot(**values)
