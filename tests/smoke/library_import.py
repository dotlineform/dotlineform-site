#!/usr/bin/env python3
"""Smoke-check the Library import Studio route."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from threading import Thread
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright


ROOT_SELECTOR = "#libraryImportRoot"


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
    if attrs["route"] != "library-import":
        raise AssertionError(f"unexpected route attribute: {attrs['route']!r}")
    if attrs["ready"] != "true":
        raise AssertionError(f"route did not become ready: {attrs!r}")
    if attrs["busy"] == "true":
        raise AssertionError(f"route stayed busy after ready: {attrs!r}")
    if attrs["mode"] not in {"selection", "result"}:
        raise AssertionError(f"unexpected route mode: {attrs['mode']!r}")
    if attrs["service"] not in {"available", "unavailable"}:
        raise AssertionError(f"unexpected service state: {attrs['service']!r}")
    if attrs["recordLoaded"] not in {"true", "false"}:
        raise AssertionError(f"unexpected record loaded state: {attrs['recordLoaded']!r}")


def assert_route_content(page, expect_unavailable_service: bool) -> dict[str, object]:
    preview_disabled = page.locator("#libraryImportPreview").evaluate("button => button.disabled")
    select_all_disabled = page.locator("#libraryImportSelectAll").evaluate("button => button.disabled")
    clear_disabled = page.locator("#libraryImportClear").evaluate("button => button.disabled")
    update_summary_disabled = page.locator("#libraryImportUpdateSummary").evaluate("button => button.disabled")
    apply_hierarchy_disabled = page.locator("#libraryImportApplyHierarchy").evaluate("button => button.disabled")
    file_option_count = page.locator("#libraryImportFileSelect option").count()
    list_exists = page.locator("#libraryImportList").count() == 1
    if not list_exists:
        raise AssertionError("preview list shell is missing")
    if expect_unavailable_service and not preview_disabled:
        raise AssertionError("preview button should be disabled when docs-management service is unavailable")
    if not update_summary_disabled:
        raise AssertionError("update summary should stay disabled until its service contract exists")
    if not apply_hierarchy_disabled:
        raise AssertionError("apply hierarchy should stay disabled until its service contract exists")
    return {
        "file_option_count": file_option_count,
        "preview_disabled": bool(preview_disabled),
        "select_all_disabled": bool(select_all_disabled),
        "clear_disabled": bool(clear_disabled),
        "update_summary_disabled": bool(update_summary_disabled),
        "apply_hierarchy_disabled": bool(apply_hierarchy_disabled),
        "list_exists": list_exists,
    }


def install_mock_docs_service(page) -> None:
    def handle(route):
        parsed = urlparse(route.request.url)
        if parsed.path == "/health":
            payload = {"ok": True}
        elif parsed.path == "/docs/library-import/files":
            payload = {
                "ok": True,
                "scope": "library",
                "staging_root": "var/docs/import-staging/library",
                "files": [
                    {
                        "filename": "summaries.jsonl",
                        "path": "var/docs/import-staging/library/summaries.jsonl",
                        "format": "jsonl",
                        "size_bytes": 512,
                        "modified_utc": "2026-05-04T12:00:00Z",
                    }
                ],
            }
        elif parsed.path == "/docs/library-import/preview":
            payload = {
                "ok": True,
                "scope": "library",
                "summary_text": "Generated 1 Library import preview file(s).",
                "detected_import_type": "document_summaries",
                "source_export_id": "library-document-summaries",
                "generated_at": "2026-05-04T12:05:00Z",
                "counts": {
                    "records": 1,
                    "parsed_records": 1,
                    "malformed_records": 0,
                    "warnings": 0,
                    "errors": 0,
                },
                "issues": [],
                "records": [{"doc_id": "alpha", "title": "Alpha", "metadata": {"summary": "Preview summary."}}],
                "preview_files": [
                    {
                        "path": "var/docs/import-preview/library/alpha-20260504-120500.md",
                        "record_index": 0,
                        "doc_id": "alpha",
                        "kind": "document",
                    }
                ],
            }
        else:
            payload = {"ok": False, "error": f"Unhandled mock route: {parsed.path}"}
        route.fulfill(status=200, content_type="application/json", body=json.dumps(payload))

    page.route("http://127.0.0.1:8789/**", handle)


def assert_mock_preview_flow(page) -> dict[str, object]:
    page.locator("#libraryImportPreview").click()
    page.wait_for_selector("[data-library-import-preview]", timeout=5000)
    rows = page.locator("[data-library-import-preview]").count()
    title = page.locator(".libraryImportList__title").first.text_content()
    if rows != 1:
        raise AssertionError(f"expected one preview row, found {rows}")
    if title != "Alpha":
        raise AssertionError(f"unexpected preview row title: {title!r}")
    page.locator("#libraryImportSelectAll").click()
    selection = page.locator("#libraryImportSelectionSummary").text_content()
    if selection != "1 preview selected.":
        raise AssertionError(f"unexpected selection summary: {selection!r}")
    update_summary_disabled = page.locator("#libraryImportUpdateSummary").evaluate("button => button.disabled")
    apply_hierarchy_disabled = page.locator("#libraryImportApplyHierarchy").evaluate("button => button.disabled")
    if not update_summary_disabled or not apply_hierarchy_disabled:
        raise AssertionError("future source-write actions should stay disabled after preview generation")
    return {"preview_rows": rows, "selected_summary": selection}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:4000")
    parser.add_argument("--site-root", help="Serve a built site root on a temporary local HTTP server.")
    parser.add_argument("--block-docs-service", action="store_true")
    parser.add_argument("--mock-docs-service", action="store_true")
    parser.add_argument("--timeout-ms", type=int, default=15000)
    args = parser.parse_args()

    static_server = None
    base_url = args.base_url
    if args.site_root:
        static_server, base_url = start_static_server(Path(args.site_root))

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                if args.block_docs_service:
                    page.route("http://127.0.0.1:8789/**", lambda route: route.abort())
                elif args.mock_docs_service:
                    install_mock_docs_service(page)
                page.goto(route_url(base_url, "/studio/library-import/"), wait_until="domcontentloaded")
                attrs = wait_for_studio_route_ready(page, ROOT_SELECTOR, args.timeout_ms)
                assert_ready_contract(attrs)
                if args.block_docs_service and attrs["service"] != "unavailable":
                    raise AssertionError(f"expected unavailable service state: {attrs!r}")
                content = assert_route_content(page, args.block_docs_service)
                if args.mock_docs_service:
                    content["mock_preview"] = assert_mock_preview_flow(page)
                print(json.dumps({"route": attrs, "content": content}, sort_keys=True))
            finally:
                browser.close()
    finally:
        if static_server is not None:
            static_server.shutdown()
            static_server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
