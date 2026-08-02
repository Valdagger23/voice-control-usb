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
    description: str,
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
        ),
    ),
    LegendSection(
        "Media & Spotify",
        "Media",
        "#A78BFA",
        (
            _command("play_media", "play | play music | resume media", "play music", "Start or resume playback."),
            _command("pause_media", "pause | pause music", "pause music", "Pause playback."),
            _command("next_track", "next track | skip song", "next track", "Skip to the next item."),
            _command("previous_track", "previous track | previous song", "previous track", "Return to the previous item."),
            _command("mute_media", "mute | mute speakers", "mute speakers", "Mute Windows playback."),
            _command("unmute_media", "unmute | unmute speakers", "unmute speakers", "Unmute Windows playback."),
            _command("set_media_volume", "set volume to <0-100> percent", "set volume to 50 percent", "Set the speaker volume."),
            _command("report_media_volume", "report volume", "report volume", "Read volume and mute state."),
            _command("report_now_playing", "now playing", "now playing", "Read the current media session."),
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
