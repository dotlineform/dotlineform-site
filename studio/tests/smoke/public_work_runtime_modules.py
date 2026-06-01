#!/usr/bin/env python3
"""Smoke-check public work navigation projection helpers."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import Page, sync_playwright


class QuietStaticHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A003
        return


def start_static_server(site_root: Path) -> tuple[ThreadingHTTPServer, str]:
    resolved_root = site_root.expanduser().resolve()
    if not resolved_root.exists():
        raise FileNotFoundError(f"site root does not exist: {resolved_root}")
    handler = partial(QuietStaticHandler, directory=str(resolved_root))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def assert_public_work_runtime(page: Page, base_url: str) -> None:
    page.add_script_tag(url=f"{base_url}/assets/js/public-catalogue-runtime.js")
    result = page.evaluate(
        """() => {
            const runtime = window.__dlfPublicCatalogueRuntime;
            const payload = {
                series: {
                    '009': {
                        title: 'Poems',
                        works: ['00001', '00002', '00003']
                    },
                    solo: {
                        title: 'Solo',
                        works: ['01000']
                    }
                }
            };
            return {
                ids: runtime.seriesIndexWorkIds(payload, '009'),
                title: runtime.seriesIndexTitle(payload, '009'),
                link: runtime.projectWorkSeriesLink(payload, '009', '/base'),
                soloLink: runtime.projectWorkSeriesLink(payload, 'solo', '/base'),
                emptyLink: runtime.projectWorkSeriesLink(payload, '', '/base'),
                backFromQuery: runtime.projectWorkBackLink(payload, {
                    seriesId: '009',
                    seriesFromQuery: '009',
                    fromContext: '',
                    baseurl: '/base'
                }),
                backDefault: runtime.projectWorkBackLink(payload, {
                    seriesId: '009',
                    seriesFromQuery: '',
                    fromContext: '',
                    baseurl: '/base'
                }),
                nav: runtime.projectWorkSeriesNavigation(['00001', '00002', '00003'], '00002', {
                    seriesId: '009',
                    seriesPage: 2,
                    baseurl: '/base'
                }),
                hiddenNav: runtime.projectWorkSeriesNavigation(['00001'], '00001', {
                    seriesId: '009',
                    baseurl: '/base'
                })
            };
        }"""
    )
    assert result["ids"] == ["00001", "00002", "00003"]
    assert result["title"] == "Poems"
    assert result["link"] == {
        "label": "Poems",
        "href": "/base/series/?series=009",
        "hidden": False,
    }
    assert result["soloLink"]["hidden"] is True
    assert result["emptyLink"] == {
        "label": "",
        "href": "/base/series/",
        "hidden": True,
    }
    assert result["backFromQuery"] == {
        "label": "\u2190 Poems",
        "seriesLabel": "Poems",
        "href": "",
    }
    assert result["backDefault"] == {
        "label": "\u2190 Poems",
        "seriesLabel": "Poems",
        "href": "/base/series/?series=009",
    }
    assert result["nav"] == {
        "hidden": False,
        "counterHidden": False,
        "prevHref": "/base/works/?series=009&series_page=2&work=00001",
        "nextHref": "/base/works/?series=009&series_page=2&work=00003",
        "counterText": "2/3",
    }
    assert result["hiddenNav"] == {"hidden": True, "counterHidden": True}


def run(site_root: Path) -> None:
    server, base_url = start_static_server(site_root)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{base_url}/series/", wait_until="domcontentloaded")
            errors: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            assert_public_work_runtime(page, base_url)
            browser.close()
            if errors:
                raise AssertionError(f"page errors during public work runtime smoke: {errors!r}")
    finally:
        server.shutdown()
        server.server_close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-root", default=".", help="Site root to serve for runtime script imports.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run(Path(args.site_root))


if __name__ == "__main__":
    main()
