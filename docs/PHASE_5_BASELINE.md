# Phase 5 Baseline

## Outcome

Phase 5 delivers visible browser and Google navigation as the second non-Excel capability. It uses the shared parser, safety policy, registry, structured results, audit history, typed input, and push-to-talk path.

## Delivered behavior

- Separate host-local persistent assistant browser profile using installed Chrome or Edge; cookies are not stored on the USB.
- Lazy visible startup with no automation of the default personal browser profile.
- Complete HTTP(S) URL navigation and encoded Google search.
- New, close, switch, and list-tab actions.
- Back, forward, refresh, scroll-up, and scroll-down actions.
- Current page title, URL, active tab, and tab-count reporting.
- Up to ten visible safe navigation links with text, URL, and stable numbering.
- Fresh-snapshot validation before numbered link navigation.
- Deterministic stub covering the same browser state transitions.

## Safety boundary

- No DOM button clicking or general selector execution.
- No form filling or submission.
- No downloads, purchases, authentication actions, or outgoing messages.
- Download anchors are excluded from visible-link results.
- Numbered links navigate directly to a recorded HTTP(S) URL and cannot run element click handlers.
- Google private services remain outside the general browser capability.

## Verification completed

- Automated suite: 158 completed; 156 passed and 2 expected native-adapter guard checks skipped.
- Native Chrome opened a local controlled test page visibly.
- A download anchor was excluded while the safe navigation link was reported.
- Numbered navigation, back, forward, refresh, scrolling, tab creation, switching, listing, and closing succeeded.
- A live Google search opened visibly in the second tab.
- Verification ended with no test Python or Chrome processes and removed the temporary browser profile.

## Run Phase 5

```powershell
cd D:\VoiceControl
.\.venv\Scripts\python.exe -m pip install -e ".[windows]"
.\.venv\Scripts\python.exe -m voice_control_usb --window
```
