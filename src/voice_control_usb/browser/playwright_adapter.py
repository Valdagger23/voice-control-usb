"""Visible Playwright adapter using a separate persistent Chrome profile."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urljoin, urlparse

from voice_control_usb.browser.adapter import (
    BrowserAdapter,
    BrowserLink,
    BrowserPage,
    _validate_web_url,
)


class PlaywrightBrowserAdapter(BrowserAdapter):
    """Control a visible, isolated Chrome/Edge context without DOM-side mutations."""

    def __init__(self, profile_dir: Path, channel: str = "chrome") -> None:
        if channel not in {"chrome", "msedge"}:
            raise ValueError("Browser channel must be chrome or msedge.")
        self.profile_dir = profile_dir.resolve()
        self.channel = channel
        self._playwright = None
        self._context = None
        self._page = None
        self._link_snapshot_url = ""
        self._link_snapshot: tuple[BrowserLink, ...] = ()

    def open_url(self, url: str) -> BrowserPage:
        target = _validate_web_url(url)
        self._current_page().goto(target, wait_until="domcontentloaded")
        self._clear_links()
        return self.report_page()

    def new_tab(self) -> BrowserPage:
        self._ensure_started()
        self._page = self._context.new_page()
        self._page.bring_to_front()
        self._clear_links()
        return self.report_page()

    def close_tab(self) -> BrowserPage:
        page = self._current_page()
        pages = self._live_pages()
        if len(pages) == 1:
            page.goto("about:blank")
        else:
            current_index = pages.index(page)
            page.close()
            remaining = self._live_pages()
            self._page = remaining[min(current_index, len(remaining) - 1)]
            self._page.bring_to_front()
        self._clear_links()
        return self.report_page()

    def switch_tab(self, index: int) -> BrowserPage:
        pages = self._live_pages()
        if not 1 <= index <= len(pages):
            raise ValueError(f"Browser tab must be between 1 and {len(pages)}.")
        self._page = pages[index - 1]
        self._page.bring_to_front()
        self._clear_links()
        return self.report_page()

    def go_back(self) -> BrowserPage:
        if self._current_page().go_back(wait_until="domcontentloaded") is None:
            raise RuntimeError("The current browser tab has no earlier page.")
        self._clear_links()
        return self.report_page()

    def go_forward(self) -> BrowserPage:
        if self._current_page().go_forward(wait_until="domcontentloaded") is None:
            raise RuntimeError("The current browser tab has no later page.")
        self._clear_links()
        return self.report_page()

    def refresh(self) -> BrowserPage:
        self._current_page().reload(wait_until="domcontentloaded")
        self._clear_links()
        return self.report_page()

    def scroll(self, direction: str) -> BrowserPage:
        if direction not in {"up", "down"}:
            raise ValueError("Browser scroll direction must be up or down.")
        delta = 700 if direction == "down" else -700
        self._current_page().mouse.wheel(0, delta)
        return self.report_page()

    def report_page(self) -> BrowserPage:
        page = self._current_page()
        pages = self._live_pages()
        return BrowserPage(
            title=page.title() or "Untitled page",
            url=page.url,
            tab_index=pages.index(page) + 1,
            tab_count=len(pages),
        )

    def list_tabs(self) -> tuple[BrowserPage, ...]:
        pages = self._live_pages()
        return tuple(
            BrowserPage(
                title=page.title() or "Untitled page",
                url=page.url,
                tab_index=index,
                tab_count=len(pages),
            )
            for index, page in enumerate(pages, start=1)
        )

    def list_visible_links(self) -> tuple[BrowserLink, ...]:
        page = self._current_page()
        locator = page.get_by_role("link")
        links: list[BrowserLink] = []
        seen: set[tuple[str, str]] = set()
        for item_index in range(min(locator.count(), 100)):
            item = locator.nth(item_index)
            if not item.is_visible() or item.get_attribute("download") is not None:
                continue
            href = item.get_attribute("href") or ""
            absolute_url = urljoin(page.url, href)
            parsed = urlparse(absolute_url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                continue
            text = " ".join((item.get_attribute("aria-label") or item.inner_text()).split())
            if not text:
                text = parsed.netloc
            identity = (text.casefold(), absolute_url)
            if identity in seen:
                continue
            seen.add(identity)
            links.append(BrowserLink(len(links) + 1, text[:120], absolute_url))
            if len(links) == 10:
                break
        self._link_snapshot_url = page.url
        self._link_snapshot = tuple(links)
        return self._link_snapshot

    def open_link(self, index: int) -> BrowserPage:
        page = self._current_page()
        if page.url != self._link_snapshot_url:
            raise RuntimeError("Visible links changed; list links again before opening one.")
        link = next((item for item in self._link_snapshot if item.index == index), None)
        if link is None:
            raise ValueError("Link number is not in the most recent visible link list.")
        return self.open_url(link.url)

    def close(self) -> None:
        if self._context is not None:
            for page in self._context.pages:
                if not page.is_closed():
                    page.close(run_before_unload=False)
            self._context.close()
        if self._playwright is not None:
            self._playwright.stop()
        self._context = None
        self._playwright = None
        self._page = None

    def _current_page(self):
        self._ensure_started()
        if self._page is None or self._page.is_closed():
            pages = self._live_pages()
            self._page = pages[-1]
        return self._page

    def _live_pages(self):
        self._ensure_started()
        pages = [page for page in self._context.pages if not page.is_closed()]
        if not pages:
            pages = [self._context.new_page()]
        return pages

    def _ensure_started(self) -> None:
        if self._context is not None:
            return
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as error:
            raise ImportError(
                "Visible browser control requires Playwright. Install the project "
                "with 'pip install .[windows]'."
            ) from error
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self._playwright = sync_playwright().start()
        try:
            self._context = self._playwright.chromium.launch_persistent_context(
                self.profile_dir,
                channel=self.channel,
                headless=False,
                accept_downloads=False,
                no_viewport=True,
            )
        except Exception:
            self._playwright.stop()
            self._playwright = None
            raise
        self._context.set_default_navigation_timeout(20_000)
        self._page = self._context.pages[0] if self._context.pages else self._context.new_page()
        self._page.bring_to_front()

    def _clear_links(self) -> None:
        self._link_snapshot_url = ""
        self._link_snapshot = ()
