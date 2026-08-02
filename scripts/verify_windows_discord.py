"""Non-sending native verification for Discord accessibility state."""

from voice_control_usb.discord.registry import DiscordTargetRegistry
from voice_control_usb.discord.windows_adapter import WindowsDiscordAdapter


def main() -> int:
    adapter = WindowsDiscordAdapter(DiscordTargetRegistry({}))
    state = adapter.open()
    print(
        f"Discord visible: {ascii(state.target)}; mic_muted={state.microphone_muted}; "
        f"deafened={state.deafened}; camera_enabled={state.camera_enabled}",
        flush=True,
    )
    if state.microphone_muted is None or state.deafened is None:
        raise RuntimeError("Discord did not expose microphone and deafen state.")
    adapter.set_microphone_muted(state.microphone_muted)
    adapter.set_deafened(state.deafened)
    restored = adapter.report()
    if restored.microphone_muted != state.microphone_muted or restored.deafened != state.deafened:
        raise RuntimeError("Discord device state changed during read-only verification.")
    print("Existing microphone and deafen state preserved; no message was drafted or sent.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
