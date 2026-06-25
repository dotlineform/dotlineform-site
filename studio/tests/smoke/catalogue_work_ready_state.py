#!/usr/bin/env python3
"""Smoke-check the catalogue work editor route-ready contract."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from tests.smoke.route_ready_helpers import wait_for_route_ready  # noqa: E402


ROOT_SELECTOR = "#catalogueWorkRoot"


def route_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}{path}"


def wait_for_studio_route_ready(page, root_selector: str, timeout_ms: int) -> dict[str, str]:
    attrs = wait_for_route_ready(
        page,
        root_selector,
        "data-studio-ready",
        "data-studio-busy",
        timeout_ms,
    )
    return {
        "route": attrs.get("data-studio-route", ""),
        "ready": attrs.get("data-studio-ready", ""),
        "busy": attrs.get("data-studio-busy", ""),
        "mode": attrs.get("data-studio-mode", ""),
        "service": attrs.get("data-studio-service", ""),
        "recordLoaded": attrs.get("data-studio-record-loaded", ""),
    }


def assert_ready_contract(attrs: dict[str, str]) -> None:
    if attrs["route"] != "catalogue-work":
        raise AssertionError(f"unexpected route attribute: {attrs['route']!r}")
    if attrs["ready"] != "true":
        raise AssertionError(f"route did not become ready: {attrs!r}")
    if attrs["busy"] == "true":
        raise AssertionError(f"route stayed busy after ready: {attrs!r}")
    if attrs["mode"] not in {"empty", "single", "bulk", "new"}:
        raise AssertionError(f"unexpected route mode: {attrs['mode']!r}")
    if attrs["service"] not in {"available", "unavailable"}:
        raise AssertionError(f"unexpected service state: {attrs['service']!r}")
    if attrs["recordLoaded"] not in {"true", "false"}:
        raise AssertionError(f"unexpected record-loaded state: {attrs['recordLoaded']!r}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:4000")
    parser.add_argument("--block-catalogue-service", action="store_true")
    parser.add_argument("--timeout-ms", type=int, default=15000)
    parser.add_argument("--work-id", default="")
    args = parser.parse_args()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            if args.block_catalogue_service:
                page.route("http://127.0.0.1:8788/**", lambda route: route.abort())
            route_path = "/studio/catalogue-work/"
            if args.work_id:
                route_path = f"{route_path}?work={args.work_id}"
            page.goto(route_url(args.base_url, route_path), wait_until="domcontentloaded")
            attrs = wait_for_studio_route_ready(page, ROOT_SELECTOR, args.timeout_ms)
            assert_ready_contract(attrs)
            if args.block_catalogue_service and attrs["service"] != "unavailable":
                raise AssertionError(f"expected unavailable service state: {attrs!r}")
            if args.work_id and not args.block_catalogue_service:
                if attrs["service"] != "available":
                    raise AssertionError(f"focused work check requires available service state: {attrs!r}")
                if attrs["mode"] != "single" or attrs["recordLoaded"] != "true":
                    raise AssertionError(f"focused work was not loaded before ready: {attrs!r}")
            print(json.dumps(attrs, sort_keys=True))
        finally:
            browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
