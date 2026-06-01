#!/usr/bin/env python3
"""Smoke-check the simplified public catalogue route contract."""

from __future__ import annotations

import argparse
from functools import partial
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import Page, expect, sync_playwright


class PublicStaticHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A003
        return

    def send_error(self, code, message=None, explain=None):  # noqa: A003
        if code == HTTPStatus.NOT_FOUND:
            not_found = Path(self.directory) / "404.html"  # type: ignore[attr-defined]
            if not_found.exists():
                body = not_found.read_bytes()
                self.send_response(HTTPStatus.NOT_FOUND)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
        super().send_error(code, message, explain)


def start_static_server(site_root: Path) -> tuple[ThreadingHTTPServer, str]:
    resolved_root = site_root.expanduser().resolve()
    if not resolved_root.exists():
        raise FileNotFoundError(f"site root does not exist: {resolved_root}")
    handler = partial(PublicStaticHandler, directory=str(resolved_root))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def goto(page: Page, base_url: str, path: str) -> None:
    page.goto(f"{base_url.rstrip('/')}{path}", wait_until="domcontentloaded")


def first_href(page: Page, selector: str) -> str:
    href = page.locator(selector).first.get_attribute("href")
    if not href:
        raise AssertionError(f"missing href for {selector}")
    return href


def show_list_view(page: Page) -> None:
    page.locator("[data-role='catalog-index-view-btn'][data-view='list']").click()
    expect(page.locator("[data-role='catalog-index-view-btn'][data-view='list']")).to_have_attribute("aria-pressed", "true")


def assert_public_routes(page: Page, base_url: str) -> None:
    goto(page, base_url, "/series/")
    expect(page.locator("#seriesIndexRoot")).to_be_visible(timeout=10_000)
    show_list_view(page)
    expect(page.locator("#seriesIndexList .seriesIndexItem").first).to_be_visible(timeout=10_000)

    goto(page, base_url, "/series/?mode=moments")
    expect(page.locator("#seriesIndexRoot")).to_be_visible(timeout=10_000)
    show_list_view(page)
    expect(page.locator("[data-role='catalog-index-mode-btn'][data-mode='moments']")).to_have_attribute("aria-pressed", "true")
    expect(page.locator("#seriesIndexList .seriesIndexItem").first).to_be_visible(timeout=10_000)
    moment_href = first_href(page, "#seriesIndexList .seriesIndexItem")
    if "/moments/" not in moment_href or "?mode=moments" in moment_href:
        raise AssertionError(f"moment browse link should open an individual moment page: {moment_href!r}")

    goto(page, base_url, "/series/?series=009&from=recent")
    expect(page.locator("#seriesIndexRoot")).to_be_visible(timeout=10_000)
    show_list_view(page)
    expect(page.locator("#seriesIndexList .seriesIndexItem").first).to_contain_text("a poem divided into 4 parts", timeout=10_000)
    series_work_href = first_href(page, "#seriesIndexList .seriesIndexItem")
    if "/works/?" not in series_work_href or "work=" not in series_work_href or "series=009" not in series_work_href:
        raise AssertionError(f"selected-series work link is not canonical: {series_work_href!r}")
    works_nav_href = first_href(page, ".site-nav .nav-item[href$='/series/']")
    if not works_nav_href.endswith("/series/"):
        raise AssertionError(f"works top nav should be a reset link on selected-series state: {works_nav_href!r}")
    page.locator("[data-role='catalog-index-mode-btn'][data-mode='works']").click()
    page.wait_for_url("**/series/", timeout=10_000)
    expect(page.locator("#seriesIndexRoot")).to_be_visible(timeout=10_000)

    goto(page, base_url, "/works/?work=00001")
    expect(page.locator("#selectedWorkRoot")).to_be_visible(timeout=10_000)
    expect(page.locator("#selectedWorkTitleText")).to_contain_text("a poem divided into 4 parts", timeout=10_000)
    work_back_href = first_href(page, "#pageBackLink")
    if "/series/?" not in work_back_href or "series=009" not in work_back_href:
        raise AssertionError(f"work back link should fall back to canonical series state: {work_back_href!r}")

    goto(page, base_url, "/works/?work=00001&series=009")
    expect(page.locator("#selectedWorkRoot")).to_be_visible(timeout=10_000)
    expect(page.locator("#seriesNav")).to_be_visible(timeout=10_000)
    nav_href = first_href(page, "#seriesNavNext")
    if "/works/?" not in nav_href or "work=00002" not in nav_href or "series=009" not in nav_href:
        raise AssertionError(f"series navigation link is not canonical: {nav_href!r}")

    goto(page, base_url, "/work-details/?detail=00001-001&from_work=00001&series=009")
    expect(page.locator("#detailPageRoot")).to_be_visible(timeout=10_000)
    expect(page.locator("#detailTitleText")).to_contain_text("a poem divided into 4 parts", timeout=10_000)
    detail_back_href = first_href(page, "#detailBackLink")
    if "/works/?" not in detail_back_href or "work=00001" not in detail_back_href or "series=009" not in detail_back_href:
        raise AssertionError(f"detail back link is not canonical: {detail_back_href!r}")

    goto(page, base_url, "/moments/a-doll-story/")
    expect(page.locator("#momentPageRoot")).to_be_visible(timeout=10_000)
    expect(page.locator("#momentTitleText")).to_contain_text("a doll story", timeout=10_000)

    response = page.context.request.get(f"{base_url.rstrip('/')}/moments/")
    body = response.text()
    if response.status != 200 or 'id="momentsRecoveryLink"' not in body or "/series/?mode=moments" not in body:
        raise AssertionError("moments recovery route did not include the visible fallback link")
    goto(page, base_url, "/moments/")
    page.wait_for_url("**/series/?mode=moments", timeout=10_000)
    expect(page.locator("#seriesIndexRoot")).to_be_visible(timeout=10_000)

    goto(page, base_url, "/catalogue/search/")
    expect(page.locator("#studioSearchRoot")).to_be_visible(timeout=10_000)
    page.locator("#studioSearchInput").fill("00001")
    expect(page.locator("#studioSearchResults .studioSearch__title").first).to_be_visible(timeout=10_000)
    search_href = first_href(page, "#studioSearchResults .studioSearch__title")
    if "/works/?" not in search_href or "work=00001" not in search_href:
        raise AssertionError(f"catalogue search result link is not canonical: {search_href!r}")

    goto(page, base_url, "/work_details/not-a-real-detail/")
    expect(page.locator("body")).to_contain_text("page unavailable", timeout=10_000)
    expect(page.locator("article.page a[href$='/series/']")).to_contain_text("return to works")


def run(site_root: Path) -> None:
    server, base_url = start_static_server(site_root)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            errors: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            assert_public_routes(page, base_url)
            browser.close()
            if errors:
                raise AssertionError(f"page errors during public route smoke: {errors!r}")
    finally:
        server.shutdown()
        server.server_close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-root", default=".", help="Built public site root to serve.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run(Path(args.site_root))


if __name__ == "__main__":
    main()
