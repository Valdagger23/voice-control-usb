"""Native Windows verification for Phase 4 media and credential boundaries."""

from __future__ import annotations

import argparse
import uuid

from voice_control_usb.media.windows_adapter import WindowsMediaAdapter
from voice_control_usb.spotify.credentials import WindowsCredentialStore


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--exercise-play-pause",
        action="store_true",
        help="Briefly change playback state and restore it.",
    )
    args = parser.parse_args()

    adapter = WindowsMediaAdapter()
    volume = adapter.get_volume()
    print(
        f"Default speakers: {volume.device_name}; volume {volume.percent}%; "
        f"muted={volume.muted}"
    )
    adapter.set_volume(volume.percent)
    adapter.set_muted(volume.muted)
    print("Speaker set operations returned the existing state without changing it.")

    media = adapter.now_playing()
    print(
        "Current session: "
        f"{media.source_app}; {ascii(media.title)}; {ascii(media.artist)}; "
        f"{media.playback_status}"
    )
    if args.exercise_play_pause:
        if media.playback_status == "playing":
            adapter.pause()
            adapter.play()
        elif media.playback_status == "paused":
            adapter.play()
            adapter.pause()
        else:
            raise RuntimeError(
                "Current playback state cannot be safely restored by this verification."
            )
        restored = adapter.now_playing()
        if restored.playback_status != media.playback_status:
            raise RuntimeError(
                "Playback state did not return to its original value after verification."
            )
        print(f"Play/pause succeeded and restored state to {restored.playback_status}.")

    target = f"voice-control-usb/verification/{uuid.uuid4()}"
    store = WindowsCredentialStore(target)
    try:
        store.set_refresh_token("temporary-phase-4-verification-token")
        if store.get_refresh_token() != "temporary-phase-4-verification-token":
            raise RuntimeError("Windows Credential Manager round-trip did not match.")
        print("Windows Credential Manager round-trip succeeded.")
    finally:
        if not store.delete_refresh_token():
            raise RuntimeError("Temporary verification credential could not be removed.")
    print("Temporary verification credential removed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
