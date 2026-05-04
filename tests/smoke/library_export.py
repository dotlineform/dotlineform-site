#!/usr/bin/env python3
"""Smoke-check the Library export Studio route."""

from __future__ import annotations

import argparse
import json

from playwright.sync_api import sync_playwright


ROOT_SELECTOR = "#libraryExportRoot"
EXPECTED_CONFIG_IDS = {
    "library-parent-child-relationships",
    "library-document-summaries",
    "library-full-document-content",
}


def route_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}{path}"


def wait_for_studio_route_ready(page, root_selector: str, timeout_ms: int) -> dict[str, str]:
    page.wait_for_selector(f"{root_selector}:not([hidden])", timeout=timeout_ms)
    page.wait_for_selector(f"{root_selector}[data-studio-ready='true']", timeout=timeout_ms)
    page.wait_for_function(
        "selector => document.querySelector(selector)?.dataset.studioBusy !== 'true'",
        arg=root_selector,
        timeout=timeout_ms,
    )
    return page.locator(root_selector).evaluate(
        """root => ({
            route: root.dataset.studioRoute || "",
            ready: root.dataset.studioReady || "",
            busy: root.dataset.studioBusy || "",
            mode: root.dataset.studioMode || "",
            service: root.dataset.studioService || "",
            recordLoaded: root.dataset.studioRecordLoaded || ""
        })"""
    )


def assert_ready_contract(attrs: dict[str, str]) -> None:
    if attrs["route"] != "library-export":
        raise AssertionError(f"unexpected route attribute: {attrs['route']!r}")
    if attrs["ready"] != "true":
        raise AssertionError(f"route did not become ready: {attrs!r}")
    if attrs["busy"] == "true":
        raise AssertionError(f"route stayed busy after ready: {attrs!r}")
    if attrs["mode"] != "selection":
        raise AssertionError(f"unexpected route mode: {attrs['mode']!r}")
    if attrs["service"] not in {"available", "unavailable"}:
        raise AssertionError(f"unexpected service state: {attrs['service']!r}")
    if attrs["recordLoaded"] != "true":
        raise AssertionError(f"Library docs did not load before ready: {attrs!r}")


def assert_route_content(page, expect_unavailable_service: bool) -> dict[str, object]:
    config_ids = set(
        page.locator("#libraryExportConfigSelect option").evaluate_all(
            "options => options.map(option => option.value)"
        )
    )
    missing_config_ids = EXPECTED_CONFIG_IDS.difference(config_ids)
    if missing_config_ids:
        raise AssertionError(f"missing export config ids: {sorted(missing_config_ids)!r}")

    doc_ids = page.locator("[data-library-export-doc]").evaluate_all(
        "rows => rows.map(row => row.getAttribute('data-library-export-doc'))"
    )
    if not doc_ids:
        raise AssertionError("Library export document list is empty")
    run_disabled = page.locator("#libraryExportRun").evaluate("button => button.disabled")
    if expect_unavailable_service and not run_disabled:
        raise AssertionError("run button should be disabled when docs-management service is unavailable")

    return {
        "config_ids": sorted(config_ids),
        "doc_count": len(doc_ids),
        "run_disabled": bool(run_disabled),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:4000")
    parser.add_argument("--block-docs-service", action="store_true")
    parser.add_argument("--timeout-ms", type=int, default=15000)
    args = parser.parse_args()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            if args.block_docs_service:
                page.route("http://127.0.0.1:8789/**", lambda route: route.abort())
            page.goto(route_url(args.base_url, "/studio/library-export/"), wait_until="domcontentloaded")
            attrs = wait_for_studio_route_ready(page, ROOT_SELECTOR, args.timeout_ms)
            assert_ready_contract(attrs)
            if args.block_docs_service and attrs["service"] != "unavailable":
                raise AssertionError(f"expected unavailable service state: {attrs!r}")
            content = assert_route_content(page, args.block_docs_service)
            print(json.dumps({"route": attrs, "content": content}, sort_keys=True))
        finally:
            browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
