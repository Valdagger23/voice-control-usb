# Commands

Voice Control exposes 158 deterministic commands. The command deck in the Windows console is the live, searchable catalogue; this file mirrors its phrases. Text in angle brackets is replaced with the requested value.

## Excel & workflows

- `open excel`
- `open workbook <PATH>`
- `select sheet <NAME>`
- `save workbook`
- `report current sheet`
- `report current cell`
- `go to <CELL>`
- `type pass`
- `type fail`
- `type n/a` or `type not applicable`
- `enter <VALUE>`
- `undo last change`
- `go left`
- `go right`
- `go down`
- `go up`
- `next row from start`
- `mark pass and next row`
- `mark fail and next row`
- `open excel and go to A1`
- `create workbook` or `new workbook`
- `create sheet <NAME>`
- `rename current sheet <NAME>`
- `delete current sheet` — confirmation required
- `select range <RANGE>`
- `read range <RANGE>`
- `clear cell`
- `clear range <RANGE>`
- `copy cell`
- `copy range <RANGE>`
- `paste cells`
- `fill down`
- `find <VALUE>`
- `replace <OLD> with <NEW>` — confirmation required
- `enter formula <FORMULA>`
- `format as currency`
- `make selection bold`
- `sort by column <COLUMN>` — confirmation required
- `filter column <COLUMN> by <VALUE>`
- `insert row above`
- `insert row below`
- `close workbook` — confirmation required

## Browser & Google

- `browse to <URL>` or `navigate to <URL>`
- `google <WORDS>` or `search google for <WORDS>`
- `new browser tab`
- `close browser tab`
- `switch to browser tab <NUMBER>`
- `go back` or `browser back`
- `go forward` or `browser forward`
- `refresh` or `reload page`
- `scroll page up`
- `scroll page down`
- `report current page`
- `list browser tabs`
- `list visible links`
- `open link <NUMBER>`
- `open google`
- `open youtube`
- `open gmail`
- `open maps`
- `open spotify`
- `switch to tab named <TITLE>`
- `close tab <NUMBER>`
- `duplicate current tab`
- `find on page <TEXT>`
- `zoom in`
- `zoom out`
- `reset zoom`
- `scroll to top`
- `scroll to bottom`
- `read page headings`
- `read selected text`
- `copy current page address`
- `stop loading`
- `reopen closed tab`

Visible-link commands operate on a fresh list of HTTP(S) navigation links. They do not submit forms, purchase items, download files, or send messages.

## Media & Spotify

- `play`, `play music`, or `resume media`
- `pause` or `pause music`
- `next track` or `skip song`
- `previous track` or `previous song`
- `mute` or `mute speakers`
- `unmute` or `unmute speakers`
- `set volume to <0-100> percent`
- `report volume`
- `now playing`
- `raise volume` or `increase volume`
- `lower volume` or `decrease volume`
- `play song <NAME>`
- `play artist <NAME>`
- `play album <NAME>`
- `play playlist <NAME>`
- `shuffle on`
- `shuffle off`
- `repeat track`
- `repeat playlist` or `repeat album`
- `repeat off`
- `seek forward <SECONDS> seconds`
- `seek backward <SECONDS> seconds`
- `restart song`
- `like this song` — confirmation required
- `add this song to <PLAYLIST>` — confirmation required

Generic media commands use the current Windows media session. Spotify-specific search, playback, library, and playlist commands use the configured Spotify connection.

## Discord & calls

- `open discord`
- `go to discord <ALIAS>`
- `draft discord message <TEXT>`
- `edit discord message <TEXT>`
- `cancel discord draft`
- `send discord draft` or `prepare discord draft` — confirmation required; physical Enter still sends
- `mute microphone`
- `unmute microphone` — confirmation required
- `deafen discord`
- `undeafen discord` — confirmation required
- `disable camera` or `turn off camera`
- `enable camera` or `turn on camera` — confirmation required
- `discord status`
- `join discord channel <ALIAS>`
- `leave discord call`
- `switch discord channel <ALIAS>`
- `draft reply <TEXT>`
- `read current discord channel`
- `read latest discord message`
- `set discord input volume to <0-100>`
- `set discord output volume to <0-100>`
- `share current screen` — confirmation opens the share picker but does not choose a screen
- `configure discord user token ...` — blocked
- `send discord messages ...` — blocked

Discord aliases come from `VOICE_CONTROL_USB_DISCORD_TARGETS`. Voice Control does not use a personal user token, operate as a self-bot, submit a normal user's message, or bulk-send messages.

## Windows & safety

- `open app <ALIAS>`
- `open url <URL>`
- `open folder <PATH>`
- `status`
- `confirm`
- `cancel`
- `shutdown` — confirmation required
- `restart` — confirmation required
- `switch to <APP>`
- `close current window` — confirmation required
- `minimize window`
- `maximize window`
- `restore window`
- `snap window left`
- `snap window right`
- `show desktop`
- `copy`
- `paste`
- `select all`
- `take screenshot`
- `lock computer` — confirmation required
- `open settings <AREA>`
- `read clipboard`
- `clear clipboard` — confirmation required
- `repeat that`
- `repeat last command`
- `undo that`
- `cancel that`
- `what did you hear`
- `no, I said <CORRECTION>`
- `show commands` or `what can I say`
- `show <CATEGORY> commands`
- `stop listening`
- `kill process ...` — blocked
- `run command ...` — blocked

`confirm`, `cancel`, and `status` manage one pending confirmation in a persistent session. `undo that` automatically reverses only the most recent supported assistant edit and reports when an action has no safe automatic undo.

## User routines

- `create routine <NAME>`
- `start <NAME> routine` or `run <NAME> routine`
- `list routines`
- `edit routine <NAME>`
- `delete routine <NAME>` — confirmation required

Create and edit routines in the collapsible routine builder. Drag commands from the deck into the lane, arrange the numbered cards from left to right, and select `RUN`. Routines persist in the selected runtime directory. Nested routines, routine-management steps, blocked commands, and unsupported phrases cannot be added.

## Safety behavior

- Safe commands run immediately.
- Confirmation-required commands wait for an explicit `confirm` in a persistent session.
- A routine containing one or more confirmation-required steps requests one confirmation for the complete chain.
- Blocked commands never execute.
- Unsupported or ambiguous phrases are rejected instead of guessed and are logged as proposals.
