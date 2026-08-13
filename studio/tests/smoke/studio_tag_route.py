#!/usr/bin/env python3
"""Smoke-check local Studio Tag route boot and service isolation."""

from __future__ import annotations

import argparse
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

from studio_route_smoke_support import start_studio_server, wait_for_studio_route


def assert_tag_route(page, base_url: str, timeout_ms: int) -> None:
    request_urls: list[str] = []
    page.on("request", lambda request: request_urls.append(request.url))
    page.goto(f"{base_url}/studio/tag-registry/", wait_until="domcontentloaded")
    wait_for_studio_route(page, "#tag-registry", timeout_ms)
    state = page.locator("#tag-registry").evaluate(
        """root => ({
            appShell: Boolean(root.closest('#studioApp')),
            busy: root.dataset.studioBusy || '',
            mode: root.dataset.studioMode || '',
            ready: root.dataset.studioReady || '',
            recordLoaded: root.dataset.studioRecordLoaded || ''
        })"""
    )
    expected = {
        "appShell": True,
        "busy": "false",
        "mode": "list",
        "ready": "true",
        "recordLoaded": "true",
    }
    if state != expected:
        raise AssertionError(f"Studio Tag route boundary changed: {state!r}")

    requests = [(urlparse(url).netloc, urlparse(url).path) for url in request_urls]
    tag_requests = [record for record in requests if record[1].startswith("/studio/api/tags/")]
    if not tag_requests:
        raise AssertionError("Studio Tag route made no local Tag API request")
    expected_netloc = urlparse(base_url).netloc
    if any(netloc != expected_netloc for netloc, _path in tag_requests):
        raise AssertionError(f"Studio Tag route used a cross-origin API: {tag_requests!r}")
    public_reads = sorted(
        path
        for _netloc, path in requests
        if path == "/assets/data/series_index.json"
        or path.startswith("/assets/works/index/")
        or path.startswith("/assets/series/index/")
    )
    if public_reads:
        raise AssertionError(f"Studio Tag route requested public projections: {public_reads!r}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout-ms", type=int, default=15000)
    args = parser.parse_args(argv)

    server, base_url = start_studio_server()
    errors: list[str] = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                page.on("pageerror", lambda error: errors.append(str(error)))
                assert_tag_route(page, base_url, args.timeout_ms)
            finally:
                browser.close()
        if errors:
            raise AssertionError(f"page errors during Studio Tag boot: {errors!r}")
    finally:
        server.shutdown()
        server.server_close()

    print("Studio Tag route boundary OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
