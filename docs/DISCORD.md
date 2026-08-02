# Discord

## Safety boundary

Voice Control operates the visible installed Discord client through Windows accessibility. It never reads or stores a personal Discord token, connects to the user-account API, scrapes messages, sends in the background, or performs bulk messaging.

Discord forbids self-bot automation of normal accounts. Voice Control therefore prepares one visible draft but never presses Enter or submits it. After `send discord draft` and `confirm`, the unchanged composer is focused and the user physically presses Enter.

## Target configuration

Create a local JSON file and point `VOICE_CONTROL_USB_DISCORD_TARGETS` to it:

```json
{
  "targets": [
    {"alias": "team", "guild_id": "123456789", "channel_id": "987654321", "label": "Team chat"},
    {"alias": "alex", "guild_id": "@me", "channel_id": "1122334455", "label": "Alex DM"}
  ]
}
```

IDs are navigation identifiers, not credentials. Keep aliases deliberate and limited.

## Device state

Discord is launched with renderer accessibility enabled. The visible button name determines state: `Mute` versus `Unmute`, `Deafen` versus `Undeafen`, and `Turn On Camera` versus `Turn Off Camera`.

Muting, deafening, and disabling camera run immediately. Unmuting, undeafening, and enabling camera require confirmation. If Discord does not expose a state—for example camera controls outside a call—the command fails without guessing or toggling.

## Native verification

```powershell
.\.venv\Scripts\python.exe scripts\verify_windows_discord.py
```

This focuses Discord, reads microphone/deafen/camera state, reapplies the current microphone and deafen values as no-ops, and sends nothing.
