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
        }
        return [ActionBinding(spec, handlers[spec.action_id]) for spec in browser_action_specs()]

    def _scroll(self, command: Command) -> ActionResult:
        direction = self._str(command, "direction")
        page = self._invoke(lambda: self.adapter.scroll(direction))
        return self._page(command, page, f"Scrolled {direction} on")

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
