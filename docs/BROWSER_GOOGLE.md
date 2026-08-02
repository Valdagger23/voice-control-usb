# Browser and Google

## Browser boundary

Voice Control launches a visible Chrome or Edge window with a separate profile under `%LOCALAPPDATA%\VoiceControlUSB\browser-profile`. It does not attach to the user's everyday browser profile and does not place browser cookies on the USB. `VOICE_CONTROL_USB_BROWSER_PROFILE` can override the local path for controlled testing.

The adapter starts lazily on the first browser command and preserves cookies, history, and tabs for that assistant profile. Chrome is the default; set `VOICE_CONTROL_USB_BROWSER_CHANNEL=msedge` or pass `--browser-channel msedge` to use Edge.

## Commands

```text
browse to https://example.com
google weather in Cork
new browser tab
list browser tabs
switch to browser tab 1
report current page
go back
go forward
refresh page
scroll page down
list visible links
open link 2
close browser tab
```

The native adapter is selected automatically in visible Windows mode. Select it explicitly for terminal use with `--browser-adapter playwright`.

## Link and submission safety

The assistant reports up to ten visible links with stable numbers. Only HTTP(S) anchors are included; anchors marked as downloads are excluded. The page URL must still match the link snapshot when `open link <NUMBER>` runs.

Opening a numbered link performs direct navigation to the recorded URL. It does not click the page element, so JavaScript click handlers, buttons, checkout actions, forms, downloads, and message controls do not execute.

Phase 5 deliberately provides no commands for entering passwords, submitting forms, purchasing, downloading, or sending messages. Unsupported requests remain proposals and execute nothing.

## Native verification

```powershell
.\.venv\Scripts\python.exe scripts\verify_windows_browser.py
```

The script uses a temporary visible browser profile and a local two-page test site. It verifies safe-link filtering, numbered navigation, history, refresh, scrolling, tabs, and a live Google search, then closes all test processes and removes the profile.
