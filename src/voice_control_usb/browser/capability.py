"""Action contracts owned by the visible browser capability."""

from __future__ import annotations

from voice_control_usb.browser.adapter import BrowserAdapter, BrowserPage
from voice_control_usb.core.capabilities import ActionBinding, ActionResult, ActionSpec
from voice_control_usb.core.models import Command


def browser_action_specs() -> list[ActionSpec]:
    simple = {
        "browser_new_tab": "Open a blank browser tab.",
        "browser_close_tab": "Close the current browser tab.",
        "browser_back": "Navigate the current tab backward.",
        "browser_forward": "Navigate the current tab forward.",
        "browser_refresh": "Refresh the current page.",
        "browser_report_page": "Report the current page identity.",
        "browser_list_tabs": "List open assistant-controlled browser tabs.",
        "browser_list_links": "List safe visible navigation links.",
    }
    specs = [ActionSpec("browser", action, description) for action, description in simple.items()]
    specs.extend(
        [
            ActionSpec("browser", "browser_open_url", "Open a complete web URL.", argument_types={"url": str}),
            ActionSpec("browser", "google_search", "Search Google visibly.", argument_types={"query": str}),
            ActionSpec("browser", "browser_switch_tab", "Switch to a numbered tab.", argument_types={"index": int}),
            ActionSpec("browser", "browser_scroll", "Scroll the current page.", argument_types={"direction": str}),
            ActionSpec("browser", "browser_open_link", "Open a link from the latest visible list.", argument_types={"index": int}),
            ActionSpec("browser", "browser_open_website", "Open an approved website alias.", argument_types={"alias": str}),
            ActionSpec("browser", "browser_switch_tab_title", "Switch to a tab by title.", argument_types={"title": str}),
            ActionSpec("browser", "browser_close_tab_index", "Close a numbered tab.", argument_types={"index": int}),
            ActionSpec("browser", "browser_duplicate_tab", "Duplicate the current tab."),
            ActionSpec("browser", "browser_find_text", "Find text on the current page.", argument_types={"text": str}),
            ActionSpec("browser", "browser_zoom", "Change page zoom.", argument_types={"direction": str}),
            ActionSpec("browser", "browser_scroll_edge", "Scroll to a page edge.", argument_types={"position": str}),
            ActionSpec("browser", "browser_read_headings", "Read visible page headings."),
            ActionSpec("browser", "browser_read_selection", "Read selected page text."),
            ActionSpec("browser", "browser_copy_page_url", "Copy the current page address."),
            ActionSpec("browser", "browser_stop_loading", "Stop page loading."),
            ActionSpec("browser", "browser_reopen_tab", "Reopen the most recently closed tab."),
        ]
    )
    return specs


class BrowserCapability:
    capability_id = "browser"

    def __init__(self, adapter: BrowserAdapter) -> None:
        self.adapter = adapter

    def bindings(self) -> list[ActionBinding]:
        handlers = {
            "browser_open_url": lambda c: self._page(c, self._invoke(lambda: self.adapter.open_url(self._str(c, "url"))), "Opened"),
            "google_search": lambda c: self._page(c, self._invoke(lambda: self.adapter.google_search(self._str(c, "query"))), "Google search opened"),
            "browser_new_tab": lambda c: self._page(c, self._invoke(self.adapter.new_tab), "Opened new tab"),
            "browser_close_tab": lambda c: self._page(c, self._invoke(self.adapter.close_tab), "Closed tab"),
            "browser_switch_tab": lambda c: self._page(c, self._invoke(lambda: self.adapter.switch_tab(self._int(c, "index"))), "Switched"),
            "browser_back": lambda c: self._page(c, self._invoke(self.adapter.go_back), "Went back to"),
            "browser_forward": lambda c: self._page(c, self._invoke(self.adapter.go_forward), "Went forward to"),
            "browser_refresh": lambda c: self._page(c, self._invoke(self.adapter.refresh), "Refreshed"),
            "browser_scroll": self._scroll,
            "browser_report_page": lambda c: self._page(c, self._invoke(self.adapter.report_page), "Current page"),
            "browser_list_tabs": self._list_tabs,
            "browser_list_links": self._list_links,
            "browser_open_link": lambda c: self._page(c, self._invoke(lambda: self.adapter.open_link(self._int(c, "index"))), "Opened link"),
            "browser_open_website": self._open_website,
            "browser_switch_tab_title": lambda c: self._page(c, self._invoke(lambda: self.adapter.switch_tab_title(self._str(c, "title"))), "Switched"),
            "browser_close_tab_index": lambda c: self._page(c, self._invoke(lambda: self.adapter.close_tab_index(self._int(c, "index"))), "Closed tab"),
            "browser_duplicate_tab": lambda c: self._page(c, self._invoke(self.adapter.duplicate_tab), "Duplicated tab"),
            "browser_find_text": self._find_text,
            "browser_zoom": self._zoom,
            "browser_scroll_edge": self._scroll_edge,
            "browser_read_headings": self._read_headings,
            "browser_read_selection": self._read_selection,
            "browser_copy_page_url": self._copy_page_url,
            "browser_stop_loading": lambda c: self._page(c, self._invoke(self.adapter.stop_loading), "Stopped loading"),
            "browser_reopen_tab": lambda c: self._page(c, self._invoke(self.adapter.reopen_closed_tab), "Reopened tab"),
        }
        return [ActionBinding(spec, handlers[spec.action_id]) for spec in browser_action_specs()]

    def _scroll(self, command: Command) -> ActionResult:
        direction = self._str(command, "direction")
        page = self._invoke(lambda: self.adapter.scroll(direction))
        return self._page(command, page, f"Scrolled {direction} on")

    def _open_website(self, command: Command) -> ActionResult:
        websites = {
            "google": "https://www.google.com",
            "youtube": "https://www.youtube.com",
            "gmail": "https://mail.google.com",
            "maps": "https://maps.google.com",
            "spotify": "https://open.spotify.com",
        }
        alias = self._str(command, "alias")
        url = websites.get(alias)
        if url is None:
            raise ValueError(f"Website alias is not approved: {alias}")
        return self._page(command, self._invoke(lambda: self.adapter.open_url(url)), "Opened website")

    def _find_text(self, command: Command) -> ActionResult:
        text = self._str(command, "text")
        count = self._invoke(lambda: self.adapter.find_text(text))
        return self._result(command, f"Found {count} visible occurrence(s) of '{text}'.", {"query": text, "count": count})

    def _zoom(self, command: Command) -> ActionResult:
        direction = self._str(command, "direction")
        page, percent = self._invoke(lambda: self.adapter.zoom(direction))
        return self._result(command, f"Page zoom is {percent} percent: {page.title}.", {**self._page_details(page), "zoom_percent": percent})

    def _scroll_edge(self, command: Command) -> ActionResult:
        position = self._str(command, "position")
        page = self._invoke(lambda: self.adapter.scroll_edge(position))
        return self._page(command, page, f"Scrolled to {position} on")

    def _read_headings(self, command: Command) -> ActionResult:
        headings = self._invoke(self.adapter.read_headings)
        message = "Page headings: " + ("; ".join(headings) if headings else "<none>")
        return self._result(command, message, {"headings": list(headings)})

    def _read_selection(self, command: Command) -> ActionResult:
        selected = self._invoke(self.adapter.read_selection)
        return self._result(command, f"Selected text: {selected or '<none>'}", {"selected_text": selected})

    def _copy_page_url(self, command: Command) -> ActionResult:
        url = self._invoke(self.adapter.copy_page_url)
        return self._result(command, f"Copied current page address: {url}", {"url": url})

    def _list_tabs(self, command: Command) -> ActionResult:
        tabs = self._invoke(self.adapter.list_tabs)
        message = "Browser tabs: " + "; ".join(
            f"{tab.tab_index}: {tab.title} ({tab.url})" for tab in tabs
        )
        return self._result(command, message, {"tabs": [self._page_details(tab) for tab in tabs]})

    def _list_links(self, command: Command) -> ActionResult:
        links = self._invoke(self.adapter.list_visible_links)
        if not links:
            return self._result(command, "No safe visible links found.", {"links": []})
        message = "Visible links: " + "; ".join(f"{link.index}: {link.text}" for link in links)
        return self._result(
            command,
            message,
            {
                "links": [
                    {"index": link.index, "text": link.text, "url": link.url}
                    for link in links
                ]
            },
        )

    def _page(self, command: Command, page: BrowserPage, prefix: str) -> ActionResult:
        return self._result(
            command,
            f"{prefix}: {page.title} ({page.url}) [tab {page.tab_index} of {page.tab_count}].",
            self._page_details(page),
        )

    @staticmethod
    def _page_details(page: BrowserPage) -> dict[str, object]:
        return {"title": page.title, "url": page.url, "tab_index": page.tab_index, "tab_count": page.tab_count}

    @staticmethod
    def _result(command: Command, message: str, details: dict[str, object]) -> ActionResult:
        return ActionResult("browser", command.action, message, details=details)

    @staticmethod
    def _invoke(operation):
        try:
            return operation()
        except Exception as error:
            if type(error).__module__.startswith("playwright"):
                raise RuntimeError(f"Visible browser control failed: {error}") from error
            raise

    @staticmethod
    def _str(command: Command, name: str) -> str:
        value = command.arguments.get(name)
        if not isinstance(value, str):
            raise ValueError(f"Browser argument '{name}' must be text.")
        return value

    @staticmethod
    def _int(command: Command, name: str) -> int:
        value = command.arguments.get(name)
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError(f"Browser argument '{name}' must be a whole number.")
        return value
