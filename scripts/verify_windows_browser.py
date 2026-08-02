"""Native Phase 5 verification using a visible isolated browser profile."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread

from voice_control_usb.browser.playwright_adapter import PlaywrightBrowserAdapter


PAGE_ONE = b"""<!doctype html><title>Voice Control One</title>
<h1>Browser verification</h1><p style='height:1200px'>Scrollable test page</p>
<a href='/two'>Continue safely</a><a href='/download' download>Download blocked</a>"""
PAGE_TWO = b"<!doctype html><title>Voice Control Two</title><h1>Second page</h1>"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        body = PAGE_TWO if self.path == "/two" else PAGE_ONE
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


def main() -> int:
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"
    try:
        Path("work").mkdir(exist_ok=True)
        with TemporaryDirectory(prefix="phase5-browser-", dir="work") as profile:
            adapter = PlaywrightBrowserAdapter(Path(profile))
            try:
                first = adapter.open_url(base_url)
                print(f"Opened local page: {ascii(first.title)}; {first.url}", flush=True)
                links = adapter.list_visible_links()
                if len(links) != 1 or links[0].text != "Continue safely":
                    raise RuntimeError("Visible-link filtering did not match the safe test link.")
                print("Download link excluded; one safe visible link reported.", flush=True)
                second = adapter.open_link(1)
                if second.title != "Voice Control Two":
                    raise RuntimeError("Numbered safe link did not open the expected page.")
                adapter.go_back()
                adapter.go_forward()
                adapter.refresh()
                adapter.scroll("down")
                adapter.scroll("up")
                adapter.new_tab()
                search = adapter.google_search("OpenAI voice control")
                if "google.com/search" not in search.url:
                    raise RuntimeError("Google search did not open the expected URL.")
                tabs = adapter.list_tabs()
                if len(tabs) != 2:
                    raise RuntimeError("Native browser tab state was not preserved.")
                print(f"Google search opened visibly; {len(tabs)} tabs reported.", flush=True)
                adapter.switch_tab(1)
                adapter.close_tab()
                print(
                    "History, refresh, scrolling, tab switching, and tab closing succeeded.",
                    flush=True,
                )
            finally:
                adapter.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
    print("Temporary browser profile removed.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
