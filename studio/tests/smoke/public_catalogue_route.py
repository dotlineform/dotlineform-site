#!/usr/bin/env python3
"""Smoke-check one representative public Catalogue route boundary."""

from __future__ import annotations

import argparse
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

from studio_route_smoke_support import start_public_server


def representative_work_id(site_root: Path) -> str:
    payloads = sorted((site_root / "assets/works/index").glob("*.json"))
    if not payloads:
        raise FileNotFoundError("public Catalogue has no Work payloads")
    return payloads[0].stem


def assert_public_catalogue_route(
    page,
    base_url: str,
    work_id: str,
    timeout_ms: int,
) -> None:
    request_urls: list[str] = []
    page.on("request", lambda request: request_urls.append(request.url))
    page.goto(
        f"{base_url}/works/?work={work_id}",
        wait_until="domcontentloaded",
    )
    page.locator("#selectedWorkRoot").wait_for(state="visible", timeout=timeout_ms)

    paths = {urlparse(url).path for url in request_urls}
    expected_payload = f"/assets/works/index/{work_id}.json"
    if expected_payload not in paths:
        raise AssertionError(f"public Catalogue missed exact Work payload: {sorted(paths)!r}")
    blocked = sorted(
        path
        for path in paths
        if path.startswith("/studio/api/")
        or path.startswith("/studio/app/")
    )
    if blocked:
        raise AssertionError(f"public Catalogue requested local Studio capability: {blocked!r}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-root", required=True)
    parser.add_argument("--timeout-ms", type=int, default=15000)
    args = parser.parse_args()

    site_root = Path(args.site_root).expanduser().resolve()
    work_id = representative_work_id(site_root)
    server, base_url = start_public_server(site_root)
    errors: list[str] = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                page.on("pageerror", lambda error: errors.append(str(error)))
                assert_public_catalogue_route(
                    page,
                    base_url,
                    work_id,
                    args.timeout_ms,
                )
            finally:
                browser.close()
        if errors:
            raise AssertionError(f"page errors during public Catalogue boot: {errors!r}")
    finally:
        server.shutdown()
        server.server_close()

    print("public Catalogue route boundary OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
