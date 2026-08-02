"""Browser control boundary and deterministic in-memory stub."""

from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import quote_plus, urlparse


@dataclass(frozen=True, slots=True)
class BrowserPage:
    title: str
    url: str
    tab_index: int
    tab_count: int


@dataclass(frozen=True, slots=True)
class BrowserLink:
    index: int
    text: str
    url: str


class BrowserAdapter:
    def open_url(self, url: str) -> BrowserPage:
        raise NotImplementedError

    def google_search(self, query: str) -> BrowserPage:
        return self.open_url(f"https://www.google.com/search?q={quote_plus(query)}")

    def new_tab(self) -> BrowserPage:
        raise NotImplementedError

    def close_tab(self) -> BrowserPage:
        raise NotImplementedError

    def switch_tab(self, index: int) -> BrowserPage:
        raise NotImplementedError

    def go_back(self) -> BrowserPage:
        raise NotImplementedError

    def go_forward(self) -> BrowserPage:
        raise NotImplementedError

    def refresh(self) -> BrowserPage:
        raise NotImplementedError

    def scroll(self, direction: str) -> BrowserPage:
        raise NotImplementedError

    def report_page(self) -> BrowserPage:
        raise NotImplementedError

    def list_tabs(self) -> tuple[BrowserPage, ...]:
        raise NotImplementedError

    def list_visible_links(self) -> tuple[BrowserLink, ...]:
        raise NotImplementedError

    def open_link(self, index: int) -> BrowserPage:
        raise NotImplementedError

    def switch_tab_title(self, title: str) -> BrowserPage: raise NotImplementedError
    def close_tab_index(self, index: int) -> BrowserPage: raise NotImplementedError
    def duplicate_tab(self) -> BrowserPage: raise NotImplementedError
    def find_text(self, text: str) -> int: raise NotImplementedError
    def zoom(self, direction: str) -> tuple[BrowserPage, int]: raise NotImplementedError
    def scroll_edge(self, position: str) -> BrowserPage: raise NotImplementedError
    def read_headings(self) -> tuple[str, ...]: raise NotImplementedError
    def read_selection(self) -> str: raise NotImplementedError
    def copy_page_url(self) -> str: raise NotImplementedError
    def stop_loading(self) -> BrowserPage: raise NotImplementedError
    def reopen_closed_tab(self) -> BrowserPage: raise NotImplementedError

    def close(self) -> None:
        return


@dataclass
class _StubTab:
    history: list[str] = field(default_factory=lambda: ["about:blank"])
    position: int = 0

    @property
    def url(self) -> str:
        return self.history[self.position]

    def navigate(self, url: str) -> None:
        del self.history[self.position + 1 :]
        self.history.append(url)
        self.position += 1


class StubBrowserAdapter(BrowserAdapter):
    """Stateful stub that preserves browser context without opening a browser."""

    def __init__(self) -> None:
        self.tabs = [_StubTab()]
        self.active_index = 0
        self.visible_links = (
            BrowserLink(1, "Example link", "https://example.com/next"),
            BrowserLink(2, "Documentation", "https://example.com/docs"),
        )
        self.link_snapshot_url = "about:blank"
        self.closed_urls: list[str] = []
        self.zoom_percent = 100
        self.selected_text = "Example selected text"
        self.copied_url = ""

    def open_url(self, url: str) -> BrowserPage:
        _validate_web_url(url)
        self._tab.navigate(url)
        return self.report_page()

    def new_tab(self) -> BrowserPage:
        self.tabs.append(_StubTab())
        self.active_index = len(self.tabs) - 1
        return self.report_page()

    def close_tab(self) -> BrowserPage:
        self.closed_urls.append(self._tab.url)
        if len(self.tabs) == 1:
            self.tabs[0] = _StubTab()
        else:
            del self.tabs[self.active_index]
            self.active_index = min(self.active_index, len(self.tabs) - 1)
        return self.report_page()

    def switch_tab(self, index: int) -> BrowserPage:
        if not 1 <= index <= len(self.tabs):
            raise ValueError(f"Browser tab must be between 1 and {len(self.tabs)}.")
        self.active_index = index - 1
        return self.report_page()

    def go_back(self) -> BrowserPage:
        if self._tab.position == 0:
            raise RuntimeError("The current browser tab has no earlier page.")
        self._tab.position -= 1
        return self.report_page()

    def go_forward(self) -> BrowserPage:
        if self._tab.position >= len(self._tab.history) - 1:
            raise RuntimeError("The current browser tab has no later page.")
        self._tab.position += 1
        return self.report_page()

    def refresh(self) -> BrowserPage:
        return self.report_page()

    def scroll(self, direction: str) -> BrowserPage:
        if direction not in {"up", "down"}:
            raise ValueError("Browser scroll direction must be up or down.")
        return self.report_page()

    def report_page(self) -> BrowserPage:
        url = self._tab.url
        title = "New Tab" if url == "about:blank" else urlparse(url).netloc
        return BrowserPage(title, url, self.active_index + 1, len(self.tabs))

    def list_tabs(self) -> tuple[BrowserPage, ...]:
        active = self.active_index
        pages = []
        for index in range(len(self.tabs)):
            self.active_index = index
            pages.append(self.report_page())
        self.active_index = active
        return tuple(pages)

    def list_visible_links(self) -> tuple[BrowserLink, ...]:
        self.link_snapshot_url = self._tab.url
        return self.visible_links

    def open_link(self, index: int) -> BrowserPage:
        if self._tab.url != self.link_snapshot_url:
            raise RuntimeError("Visible links changed; list links again before opening one.")
        link = next((item for item in self.visible_links if item.index == index), None)
        if link is None:
            raise ValueError("Link number is not in the most recent visible link list.")
        return self.open_url(link.url)

    def switch_tab_title(self, title: str) -> BrowserPage:
        matches = [
            page
            for page in self.list_tabs()
            if title.casefold() in page.title.casefold()
        ]
        if not matches:
            raise ValueError(f"No browser tab title contains: {title}")
        if len(matches) > 1:
            raise ValueError(f"Multiple browser tab titles contain: {title}")
        return self.switch_tab(matches[0].tab_index)

    def close_tab_index(self, index: int) -> BrowserPage:
        self.switch_tab(index)
        return self.close_tab()

    def duplicate_tab(self) -> BrowserPage:
        url = self._tab.url
        self.new_tab()
        if url != "about:blank":
            return self.open_url(url)
        return self.report_page()

    def find_text(self, text: str) -> int:
        haystack = f"Example link Documentation {self._tab.url}"
        return haystack.casefold().count(text.casefold())

    def zoom(self, direction: str) -> tuple[BrowserPage, int]:
        if direction == "in":
            self.zoom_percent = min(500, self.zoom_percent + 10)
        elif direction == "out":
            self.zoom_percent = max(25, self.zoom_percent - 10)
        elif direction == "reset":
            self.zoom_percent = 100
        else:
            raise ValueError("Browser zoom direction must be in, out, or reset.")
        return self.report_page(), self.zoom_percent

    def scroll_edge(self, position: str) -> BrowserPage:
        if position not in {"top", "bottom"}:
            raise ValueError("Browser scroll position must be top or bottom.")
        return self.report_page()

    def read_headings(self) -> tuple[str, ...]:
        return ("Example heading", "Documentation")

    def read_selection(self) -> str:
        return self.selected_text

    def copy_page_url(self) -> str:
        self.copied_url = self._tab.url
        return self.copied_url

    def stop_loading(self) -> BrowserPage:
        return self.report_page()

    def reopen_closed_tab(self) -> BrowserPage:
        if not self.closed_urls:
            raise RuntimeError("There is no recently closed browser tab.")
        url = self.closed_urls.pop()
        self.new_tab()
        return self.open_url(url) if url != "about:blank" else self.report_page()

    @property
    def _tab(self) -> _StubTab:
        return self.tabs[self.active_index]


def _validate_web_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Browser URL must be a complete http or https address.")
    return url.strip()
