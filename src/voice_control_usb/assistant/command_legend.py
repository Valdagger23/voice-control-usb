"""Human-friendly command catalogue for the native assistant window."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LegendCommand:
    """One supported phrase with a useful example for quick insertion."""

    registry_name: str
    phrase: str
    example: str
    description: str
    badge: str = ""


@dataclass(frozen=True, slots=True)
class LegendSection:
    """A command category shown in the left-side command deck."""

    name: str
    short_name: str
    accent: str
    commands: tuple[LegendCommand, ...]


def _command(
    registry_name: str,
    phrase: str,
    example: str,
    description: str = "",
    badge: str = "",
) -> LegendCommand:
    return LegendCommand(registry_name, phrase, example, description, badge)


COMMAND_SECTIONS: tuple[LegendSection, ...] = (
    LegendSection(
        "Excel & Workflows",
        "Excel",
        "#22D3A7",
        (
            _command("open_excel", "open excel", "open excel", "Open or focus Excel."),
            _command("open_workbook", "open workbook <PATH>", "open workbook D:\\Reports\\book.xlsx", "Open a workbook by its full path."),
            _command("select_sheet", "select sheet <NAME>", "select sheet Sheet2", "Switch to a worksheet."),
            _command("save_workbook", "save workbook", "save workbook", "Save the active workbook."),
            _command("report_current_sheet", "report current sheet", "report current sheet", "Read the active sheet name."),
            _command("report_current_cell", "report current cell", "report current cell", "Read the selected cell and value."),
            _command("go_to_cell", "go to <CELL>", "go to A1", "Select a specific cell."),
            _command("type_pass", "type pass", "type pass", "Enter pass in the selected cell."),
            _command("type_fail", "type fail", "type fail", "Enter fail in the selected cell."),
            _command("type_not_applicable", "type n/a | type not applicable", "type n/a", "Enter N/A in the selected cell."),
            _command("enter_value", "enter <VALUE>", "enter 42", "Enter text or a number."),
            _command("undo_last_excel_change", "undo last change", "undo last change", "Undo the assistant's last cell edit."),
            _command("go_left", "go left", "go left", "Move one cell left."),
            _command("go_right", "go right", "go right", "Move one cell right."),
            _command("go_down", "go down", "go down", "Move one cell down."),
            _command("go_up", "go up", "go up", "Move one cell up."),
            _command("next_row_from_start", "next row from start", "next row from start", "Move down and return to the starting column."),
            _command("workflow_mark_pass_and_next_row", "mark pass and next row", "mark pass and next row", "Enter pass, then start the next row."),
            _command("workflow_mark_fail_and_next_row", "mark fail and next row", "mark fail and next row", "Enter fail, then start the next row."),
            _command("workflow_open_excel_and_go_to_a1", "open excel and go to A1", "open excel and go to A1", "Open Excel and select A1."),
            _command("create_workbook", "create workbook | new workbook", "create workbook"),
            _command("create_sheet", "create sheet <NAME>", "create sheet Results"),
            _command("rename_sheet", "rename current sheet <NAME>", "rename current sheet Summary"),
            _command("delete_sheet", "delete current sheet", "delete current sheet", badge="CONFIRM"),
            _command("select_range", "select range <RANGE>", "select range A1:C10"),
            _command("read_range", "read range <RANGE>", "read range A1:C10"),
            _command("clear_cell", "clear cell", "clear cell"),
            _command("clear_range", "clear range <RANGE>", "clear range A1:C10"),
            _command("copy_cell", "copy cell", "copy cell"),
            _command("copy_range", "copy range <RANGE>", "copy range A1:C10"),
            _command("paste_cells", "paste cells", "paste cells"),
            _command("fill_down", "fill down", "fill down"),
            _command("find_excel_value", "find <VALUE>", "find pending"),
            _command("replace_excel_value", "replace <OLD> with <NEW>", "replace pending with complete", badge="CONFIRM"),
            _command("enter_formula", "enter formula <FORMULA>", "enter formula SUM(A1:A10)"),
            _command("format_currency", "format as currency", "format as currency"),
            _command("format_bold", "make selection bold", "make selection bold"),
            _command("sort_by_column", "sort by column <COLUMN>", "sort by column A", badge="CONFIRM"),
            _command("filter_column", "filter column <COLUMN> by <VALUE>", "filter column B by pass"),
            _command("insert_row_above", "insert row above", "insert row above"),
            _command("insert_row_below", "insert row below", "insert row below"),
            _command("close_workbook", "close workbook", "close workbook", badge="CONFIRM"),
        ),
    ),
    LegendSection(
        "Browser & Google",
        "Browser",
        "#38BDF8",
        (
            _command("browser_open_url", "browse to <URL> | navigate to <URL>", "browse to https://example.com", "Open a complete web address."),
            _command("google_search", "google <WORDS> | search google for <WORDS>", "google weather tomorrow", "Run a visible Google search."),
            _command("browser_new_tab", "new browser tab", "new browser tab", "Open a new controlled tab."),
            _command("browser_close_tab", "close browser tab", "close browser tab", "Close the current controlled tab."),
            _command("browser_switch_tab", "switch to browser tab <NUMBER>", "switch to browser tab 2", "Switch to a numbered tab."),
            _command("browser_back", "go back | browser back", "go back", "Go to the previous page."),
            _command("browser_forward", "go forward | browser forward", "go forward", "Go to the next page."),
            _command("browser_refresh", "refresh | reload page", "refresh page", "Reload the current page."),
            _command("browser_scroll", "scroll page up | scroll page down", "scroll page down", "Scroll the visible page."),
            _command("browser_report_page", "report current page", "report current page", "Read the current page title and address."),
            _command("browser_list_tabs", "list browser tabs", "list browser tabs", "List every controlled tab."),
            _command("browser_list_links", "list visible links", "list visible links", "Number safe links on the page."),
            _command("browser_open_link", "open link <NUMBER>", "open link 1", "Open a link from the latest list."),
            _command("browser_open_website", "open [google | youtube | gmail | maps | spotify]", "open youtube"),
            _command("browser_switch_tab_title", "switch to tab named <TITLE>", "switch to tab named YouTube"),
            _command("browser_close_tab_index", "close tab <NUMBER>", "close tab 2"),
            _command("browser_duplicate_tab", "duplicate current tab", "duplicate current tab"),
            _command("browser_find_text", "find on page <TEXT>", "find on page pricing"),
            _command("browser_zoom_in", "zoom in", "zoom in"),
            _command("browser_zoom_out", "zoom out", "zoom out"),
            _command("browser_zoom_reset", "reset zoom", "reset zoom"),
            _command("browser_scroll_top", "scroll to top", "scroll to top"),
            _command("browser_scroll_bottom", "scroll to bottom", "scroll to bottom"),
            _command("browser_read_headings", "read page headings", "read page headings"),
            _command("browser_read_selection", "read selected text", "read selected text"),
            _command("browser_copy_page_url", "copy current page address", "copy current page address"),
            _command("browser_stop_loading", "stop loading", "stop loading"),
            _command("browser_reopen_tab", "reopen closed tab", "reopen closed tab"),
        ),
    ),
    LegendSection(
        "Media & Spotify",
        "Media",
        "#A78BFA",
        (
            _command("play_media", "music | play | play music | resume media", "play music", "Start or resume playback."),
            _command("pause_media", "pause | pause music", "pause music", "Pause playback."),
            _command("next_track", "next track | skip song", "next track", "Skip to the next item."),
            _command("previous_track", "previous track | previous song", "previous track", "Return to the previous item."),
            _command("mute_media", "mute | mute speakers", "mute speakers", "Mute Windows playback."),
            _command("unmute_media", "unmute | unmute speakers", "unmute speakers", "Unmute Windows playback."),
            _command("set_media_volume", "set volume to <0-100> percent", "set volume to 50 percent", "Set the speaker volume."),
            _command("report_media_volume", "report volume", "report volume", "Read volume and mute state."),
            _command("report_now_playing", "now playing", "now playing", "Read the current media session."),
            _command("increase_media_volume", "raise volume | increase volume", "raise volume"),
            _command("decrease_media_volume", "lower volume | decrease volume", "lower volume"),
            _command("spotify_play_song", "play song <NAME>", "play song Midnight City"),
            _command("spotify_play_artist", "play artist <NAME>", "play artist Daft Punk"),
            _command("spotify_play_album", "play album <NAME>", "play album Discovery"),
            _command("spotify_play_playlist", "play playlist <NAME>", "play playlist Favorites"),
            _command("spotify_shuffle_on", "shuffle on", "shuffle on"),
            _command("spotify_shuffle_off", "shuffle off", "shuffle off"),
            _command("spotify_repeat_track", "repeat track", "repeat track"),
            _command("spotify_repeat_context", "repeat playlist | repeat album", "repeat playlist"),
            _command("spotify_repeat_off", "repeat off", "repeat off"),
            _command("spotify_seek_forward", "seek forward <SECONDS> seconds", "seek forward 30 seconds"),
            _command("spotify_seek_backward", "seek backward <SECONDS> seconds", "seek backward 15 seconds"),
            _command("spotify_restart_song", "restart song", "restart song"),
            _command("spotify_like_song", "like this song", "like this song", badge="CONFIRM"),
            _command("spotify_add_to_playlist", "add this song to <PLAYLIST>", "add this song to Favorites", badge="CONFIRM"),
        ),
    ),
    LegendSection(
        "Discord & Calls",
        "Discord",
        "#F472B6",
        (
            _command("open_discord", "open discord", "open discord", "Open or focus Discord."),
            _command("discord_navigate", "go to discord <ALIAS>", "go to discord general", "Open an approved server, channel, or DM."),
            _command("discord_draft", "draft | edit discord message <TEXT>", "draft discord message Hello there", "Create or replace one visible draft."),
            _command("discord_cancel_draft", "cancel discord draft", "cancel discord draft", "Clear the visible draft."),
            _command("discord_prepare_send", "send | prepare discord draft", "send discord draft", "Prepare the reviewed draft; you press Enter.", "CONFIRM"),
            _command("discord_mute_microphone", "mute microphone", "mute microphone", "Mute the Discord microphone."),
            _command("discord_unmute_microphone", "unmute microphone", "unmute microphone", "Restore the Discord microphone.", "CONFIRM"),
            _command("discord_deafen", "deafen discord", "deafen discord", "Mute Discord listening and speaking."),
            _command("discord_undeafen", "undeafen discord", "undeafen discord", "Restore Discord listening.", "CONFIRM"),
            _command("discord_disable_camera", "disable | turn off camera", "disable camera", "Turn off the Discord camera."),
            _command("discord_enable_camera", "enable | turn on camera", "enable camera", "Turn on the Discord camera.", "CONFIRM"),
            _command("discord_report_status", "discord status", "discord status", "Read draft, microphone, and call state."),
            _command("discord_reject_user_token", "configure discord user token ...", "configure discord user token example", "Always blocked: personal-token automation.", "BLOCKED"),
            _command("discord_reject_bulk_send", "send discord messages ...", "send discord messages to everyone", "Always blocked: bulk messaging.", "BLOCKED"),
            _command("discord_join_channel", "join discord channel <ALIAS>", "join discord channel general"),
            _command("discord_leave_call", "leave discord call", "leave discord call"),
            _command("discord_switch_channel", "switch discord channel <ALIAS>", "switch discord channel general"),
            _command("discord_draft_reply", "draft reply <TEXT>", "draft reply Sounds good"),
            _command("discord_read_channel", "read current discord channel", "read current discord channel"),
            _command("discord_read_latest", "read latest discord message", "read latest discord message"),
            _command("discord_input_volume", "set discord input volume to <0-100>", "set discord input volume to 80"),
            _command("discord_output_volume", "set discord output volume to <0-100>", "set discord output volume to 60"),
            _command("discord_share_screen", "share current screen", "share current screen", badge="CONFIRM"),
        ),
    ),
    LegendSection(
        "Windows & Safety",
        "System",
        "#F59E0B",
        (
            _command("open_app", "open app <ALIAS>", "open app notepad", "Open an approved Windows app."),
            _command("open_url", "open url <URL>", "open url https://example.com", "Open an approved address in Windows."),
            _command("open_folder", "open folder <PATH>", "open folder D:\\Reports", "Open a folder by path."),
            _command("report_status", "status", "status", "Read the pending confirmation state."),
            _command("confirm_pending", "confirm", "confirm", "Approve the one pending risky action.", "CONFIRM"),
            _command("cancel_pending", "cancel", "cancel", "Cancel the pending risky action."),
            _command("reject_shutdown", "shutdown", "shutdown", "Request a controlled Windows shutdown.", "CONFIRM"),
            _command("reject_restart", "restart", "restart", "Request a controlled Windows restart.", "CONFIRM"),
            _command("reject_kill_process", "kill process ...", "kill process example", "Always blocked in the current safety model.", "BLOCKED"),
            _command("reject_run_command", "run command ...", "run command example", "Always blocked: arbitrary commands never run.", "BLOCKED"),
            _command("switch_app", "switch to <APP>", "switch to notepad"),
            _command("close_current_window", "close current window", "close current window", badge="CONFIRM"),
            _command("minimize_window", "minimize window", "minimize window"),
            _command("maximize_window", "maximize window", "maximize window"),
            _command("restore_window", "restore window", "restore window"),
            _command("snap_window_left", "snap window left", "snap window left"),
            _command("snap_window_right", "snap window right", "snap window right"),
            _command("show_desktop", "show desktop", "show desktop"),
            _command("desktop_copy", "copy", "copy"),
            _command("desktop_paste", "paste", "paste"),
            _command("desktop_select_all", "select all", "select all"),
            _command("take_screenshot", "take screenshot", "take screenshot"),
            _command("lock_computer", "lock computer", "lock computer", badge="CONFIRM"),
            _command("open_settings", "open settings <AREA>", "open settings sound"),
            _command("read_clipboard", "read clipboard", "read clipboard"),
            _command("clear_clipboard", "clear clipboard", "clear clipboard", badge="CONFIRM"),
            _command("repeat_response", "repeat that", "repeat that"),
            _command("repeat_last_command", "repeat last command", "repeat last command"),
            _command("undo_that", "undo that", "undo that"),
            _command("cancel_that", "cancel that", "cancel that"),
            _command("report_last_input", "what did you hear", "what did you hear"),
            _command("correct_last_input", "no, I said <CORRECTION>", "no, I said go to B15"),
            _command("show_commands", "show commands | what can I say", "show commands"),
            _command("show_category_commands", "show <CATEGORY> commands", "show excel commands"),
            _command("stop_listening", "stop listening", "stop listening"),
        ),
    ),
    LegendSection(
        "User Routines",
        "Routine",
        "#FB7185",
        (
            _command("create_user_routine", "create routine <NAME>", "create routine Morning setup"),
            _command("run_user_routine", "start <NAME> routine | run <NAME> routine", "start Morning setup routine"),
            _command("list_user_routines", "list routines", "list routines"),
            _command("edit_user_routine", "edit routine <NAME>", "edit routine Morning setup"),
            _command("delete_user_routine", "delete routine <NAME>", "delete routine Morning setup", badge="CONFIRM"),
        ),
    ),
)


def filter_command_sections(
    query: str = "",
    category: str = "All",
) -> tuple[LegendSection, ...]:
    """Return catalogue sections matching a category and free-text query."""

    normalized_query = query.strip().casefold()
    filtered: list[LegendSection] = []
    for section in COMMAND_SECTIONS:
        if category != "All" and category != section.short_name:
            continue
        commands = tuple(
            command
            for command in section.commands
            if not normalized_query
            or normalized_query
            in " ".join(
                (
                    command.phrase,
                    command.example,
                    command.description,
                    command.badge,
                )
            ).casefold()
        )
        if commands:
            filtered.append(
                LegendSection(section.name, section.short_name, section.accent, commands)
            )
    return tuple(filtered)


def registry_names_in_legend() -> set[str]:
    """Expose registry coverage for regression tests."""

    return {
        command.registry_name
        for section in COMMAND_SECTIONS
        for command in section.commands
    }
