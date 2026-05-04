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

    format_result = assert_format_controls(page)
    filter_result = assert_filter_flow(page, len(doc_ids))

    return {
        "config_ids": sorted(config_ids),
        "doc_count": len(doc_ids),
        "formats": format_result,
        "filters": filter_result,
        "run_disabled": bool(run_disabled),
    }


def format_controls(page) -> list[dict[str, object]]:
    return page.locator("input[name='libraryExportFormat']").evaluate_all(
        """inputs => inputs.map(input => ({
            value: input.value,
            checked: input.checked,
            disabled: input.disabled
        }))"""
    )


def assert_format_controls(page) -> dict[str, str]:
    def by_value() -> dict[str, dict[str, object]]:
        return {str(item["value"]): item for item in format_controls(page)}

    initial = by_value()
    if not initial["json"]["checked"] or initial["json"]["disabled"]:
        raise AssertionError(f"parent-child config should default to JSON: {initial!r}")
    if not initial["jsonl"]["disabled"]:
        raise AssertionError(f"parent-child config should disable JSONL: {initial!r}")

    page.locator("#libraryExportConfigSelect").select_option("library-full-document-content")
    page.wait_for_function(
        """() => {
            const jsonl = document.querySelector("input[name='libraryExportFormat'][value='jsonl']");
            const json = document.querySelector("input[name='libraryExportFormat'][value='json']");
            return jsonl && json && jsonl.checked && !jsonl.disabled && !json.disabled;
        }"""
    )
    full_content = by_value()

    page.locator("#libraryExportConfigSelect").select_option("library-document-summaries")
    page.wait_for_function(
        """() => {
            const jsonl = document.querySelector("input[name='libraryExportFormat'][value='jsonl']");
            const json = document.querySelector("input[name='libraryExportFormat'][value='json']");
            return jsonl && json && jsonl.checked && !jsonl.disabled && !json.disabled;
        }"""
    )

    page.locator("#libraryExportConfigSelect").select_option("library-parent-child-relationships")
    page.wait_for_function(
        """() => {
            const jsonl = document.querySelector("input[name='libraryExportFormat'][value='jsonl']");
            const json = document.querySelector("input[name='libraryExportFormat'][value='json']");
            return jsonl && json && json.checked && !json.disabled && jsonl.disabled;
        }"""
    )
    return {
        "parent_default": "json",
        "content_default": "jsonl" if full_content["jsonl"]["checked"] else "",
    }


def assert_filter_flow(page, total_docs: int) -> dict[str, int]:
    filter_keys = page.locator("[data-library-export-filter]").evaluate_all(
        "buttons => buttons.map(button => button.getAttribute('data-library-export-filter'))"
    )
    expected_keys = ["all", "no_content", "not_viewable"]
    if filter_keys != expected_keys:
        raise AssertionError(f"unexpected Library export filters: {filter_keys!r}")

    counts = page.locator("[data-library-export-doc]").evaluate_all(
        """rows => ({
            all: rows.length,
            no_content: rows.filter(row => row.dataset.libraryExportNoContent === "true").length,
            not_viewable: rows.filter(row => row.dataset.libraryExportViewable === "false").length
        })"""
    )
    if counts["all"] != total_docs:
        raise AssertionError(f"show all count mismatch: {counts!r}; total={total_docs!r}")

    filter_labels = page.locator("[data-library-export-filter]").evaluate_all(
        "buttons => buttons.map(button => button.textContent.trim())"
    )
    for key, label in zip(expected_keys, filter_labels):
        if f"[{counts[key]}]" not in label:
            raise AssertionError(f"filter {key!r} label lacks count {counts[key]!r}: {label!r}")

    def assert_filter(key: str, row_attribute: str, row_value: str, expected_count: int) -> None:
        page.locator(f"[data-library-export-filter='{key}']").click()
        page.wait_for_function(
            """([attr, expected]) => {
                const expectedValue = attr[1];
                const attrName = attr[0];
                const rows = Array.from(document.querySelectorAll("[data-library-export-doc]"));
                return rows.length === expected && rows.every(row => row.getAttribute(attrName) === expectedValue);
            }""",
            arg=[[row_attribute, row_value], expected_count],
        )
        page.locator("#libraryExportSelectAll").click()
        checked_count = page.locator("[data-library-export-doc] input[type='checkbox']:checked").count()
        if checked_count != expected_count:
            raise AssertionError(f"select all selected {checked_count} rows for {key}, expected {expected_count}")
        page.locator("#libraryExportClear").click()
        checked_after_clear = page.locator("[data-library-export-doc] input[type='checkbox']:checked").count()
        if checked_after_clear != 0:
            raise AssertionError(f"clear left {checked_after_clear} selected rows for {key}")

    assert_filter("no_content", "data-library-export-no-content", "true", counts["no_content"])
    assert_filter("not_viewable", "data-library-export-viewable", "false", counts["not_viewable"])
    page.locator("[data-library-export-filter='all']").click()
    page.wait_for_function(
        "expected => document.querySelectorAll('[data-library-export-doc]').length === expected",
        arg=total_docs,
    )
    return counts


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
