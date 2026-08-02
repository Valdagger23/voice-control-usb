"""Tests for browser capability routing and state."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from voice_control_usb.assistant.app import AssistantApp
from voice_control_usb.browser.adapter import StubBrowserAdapter
from voice_control_usb.core.models import Command
from voice_control_usb.desktop.adapter import StubDesktopAdapter
from voice_control_usb.desktop.registry import AppAliasRegistry
from voice_control_usb.excel.adapter import StubExcelAdapter
from voice_control_usb.executor.engine import ExecutionEngine


class BrowserCapabilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.browser = StubBrowserAdapter()
        self.engine = ExecutionEngine(
            StubExcelAdapter(),
            StubDesktopAdapter(AppAliasRegistry.load_default()),
            browser=self.browser,
        )

    def execute(self, action: str, arguments: dict[str, object] | None = None) -> str:
        return self.engine.execute(Command(action, action, arguments or {}))

    def test_navigation_tabs_history_and_reporting_preserve_context(self) -> None:
        self.execute("browser_open_url", {"url": "https://example.com/one"})
        self.execute("browser_open_url", {"url": "https://example.com/two"})
        self.assertIn("example.com/one", self.execute("browser_back"))
        self.assertIn("example.com/two", self.execute("browser_forward"))

        self.execute("browser_new_tab")
        self.execute("google_search", {"query": "voice control"})
        tabs = self.engine.execute_result(Command("tabs", "browser_list_tabs"))

        self.assertEqual(len(tabs.details["tabs"]), 2)
        self.assertIn("google.com/search", tabs.message)
        self.assertIn("tab 1 of 2", self.execute("browser_switch_tab", {"index": 1}))

    def test_link_numbers_require_a_fresh_visible_snapshot(self) -> None:
        self.execute("browser_open_url", {"url": "https://example.com"})
        links = self.engine.execute_result(Command("links", "browser_list_links"))
        self.assertEqual(len(links.details["links"]), 2)

        opened = self.execute("browser_open_link", {"index": 2})
        self.assertIn("example.com/docs", opened)

        with self.assertRaisesRegex(RuntimeError, "list links again"):
            self.execute("browser_open_link", {"index": 1})

    def test_invalid_tab_and_link_numbers_fail_clearly(self) -> None:
        with self.assertRaisesRegex(ValueError, "between 1 and 1"):
            self.execute("browser_switch_tab", {"index": 2})
        self.execute("browser_list_links")
        with self.assertRaisesRegex(ValueError, "most recent visible link list"):
            self.execute("browser_open_link", {"index": 99})

    def test_submission_download_purchase_and_message_requests_never_execute(self) -> None:
        with TemporaryDirectory() as temp_dir:
            app = AssistantApp(Path(temp_dir) / "proposals.jsonl", browser=self.browser)
            for phrase in (
                "submit browser form",
                "download current page",
                "buy this item",
                "send browser message hello",
            ):
                with self.subTest(phrase=phrase):
                    self.assertIn("Unsupported command logged", app.handle_text(phrase))
        self.assertEqual(self.browser.report_page().url, "about:blank")


if __name__ == "__main__":
    unittest.main()
