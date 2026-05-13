#!/usr/bin/env python3
"""Smoke-check the data sharing review Studio route."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from threading import Thread
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright


ROOT_SELECTOR = "#dataSharingReviewRoot"


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
    if attrs["route"] != "data-sharing-review":
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
    preview_disabled = page.locator("#dataSharingReviewRun").evaluate("button => button.disabled")
    select_all_disabled = page.locator("#dataSharingReviewSelectAll").evaluate("button => button.disabled")
    clear_disabled = page.locator("#dataSharingReviewClear").evaluate("button => button.disabled")
    update_summary_disabled = page.locator("#dataSharingReviewUpdateSummary").evaluate("button => button.disabled")
    apply_hierarchy_disabled = page.locator("#dataSharingReviewApplyHierarchy").evaluate("button => button.disabled")
    file_option_count = page.locator("#dataSharingReviewFileSelect option").count()
    list_exists = page.locator("#dataSharingReviewList").count() == 1
    if not list_exists:
        raise AssertionError("preview list shell is missing")
    if expect_unavailable_service and not preview_disabled:
        raise AssertionError("preview button should be disabled when docs-management service is unavailable")
    if not update_summary_disabled:
        raise AssertionError("update summary should stay disabled until document previews are selected")
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


def assert_unsupported_adapter_state(page, expected_status: str) -> dict[str, object]:
    preview_disabled = page.locator("#dataSharingReviewRun").evaluate("button => button.disabled")
    update_summary_disabled = page.locator("#dataSharingReviewUpdateSummary").evaluate("button => button.disabled")
    apply_hierarchy_disabled = page.locator("#dataSharingReviewApplyHierarchy").evaluate("button => button.disabled")
    file_select_disabled = page.locator("#dataSharingReviewFileSelect").evaluate("select => select.disabled")
    status_text = page.locator("#dataSharingReviewStatus").text_content()
    if status_text != expected_status:
        raise AssertionError(f"unexpected unsupported-adapter status: {status_text!r}")
    if not preview_disabled or not update_summary_disabled or not apply_hierarchy_disabled or not file_select_disabled:
        raise AssertionError("future adapter controls should be disabled")
    return {
        "status": status_text,
        "preview_disabled": bool(preview_disabled),
        "update_summary_disabled": bool(update_summary_disabled),
        "apply_hierarchy_disabled": bool(apply_hierarchy_disabled),
        "file_select_disabled": bool(file_select_disabled),
    }


def install_mock_docs_service(page) -> None:
    def handle(route):
        parsed = urlparse(route.request.url)
        if parsed.path == "/health":
            payload = {"ok": True}
        elif parsed.path == "/docs/import/files":
            payload = {
                "ok": True,
                "scope": "library",
                "staging_root": "var/studio/data-sharing/library/import-staging",
                "files": [
                    {
                        "filename": "summaries.jsonl",
                        "path": "var/studio/data-sharing/library/import-staging/summaries.jsonl",
                        "format": "jsonl",
                        "size_bytes": 512,
                        "modified_utc": "2026-05-04T12:00:00Z",
                    }
                ],
            }
        elif parsed.path == "/docs/import/preview":
            payload = {
                "ok": True,
                "scope": "library",
                "summary_text": "Generated 3 Library returned package review files.",
                "detected_import_type": "parent_child_relationships",
                "source_export_id": "library-parent-child-relationships",
                "generated_at": "2026-05-04T12:05:00Z",
                "counts": {
                    "records": 3,
                    "parsed_records": 3,
                    "malformed_records": 0,
                    "warnings": 1,
                    "errors": 0,
                },
                "issues": [
                    {
                        "level": "warning",
                        "code": "unknown_doc_id",
                        "message": "record doc_id is not in the current Library index: beta",
                        "record_index": 2,
                        "doc_id": "beta",
                    }
                ],
                "records": [
                    {
                        "record_index": 0,
                        "doc_id": "library",
                        "title": "Library",
                        "parent_id": "",
                        "current_library": {"exists": True},
                    },
                    {
                        "record_index": 1,
                        "doc_id": "alpha",
                        "title": "Alpha",
                        "parent_id": "library",
                        "current_library": {"exists": True},
                    },
                    {
                        "record_index": 2,
                        "doc_id": "beta",
                        "title": "Beta",
                        "parent_id": "alpha",
                        "current_library": {"exists": False},
                    },
                ],
                "preview_files": [
                    {
                        "path": "var/studio/data-sharing/library/import-preview/relationships-tree.md",
                        "record_count": 3,
                        "kind": "relationship_tree",
                    },
                    {
                        "path": "var/studio/data-sharing/library/import-preview/alpha-20260504-120500.md",
                        "record_index": 1,
                        "doc_id": "alpha",
                        "kind": "document",
                    },
                    {
                        "path": "var/studio/data-sharing/library/import-preview/beta-20260504-120500.md",
                        "record_index": 2,
                        "doc_id": "beta",
                        "kind": "document",
                    }
                ],
            }
        elif parsed.path == "/docs/import/apply":
            request_body = {}
            try:
                post_data_json = route.request.post_data_json
                request_body = post_data_json() if callable(post_data_json) else post_data_json
            except (AttributeError, json.JSONDecodeError):
                post_data = getattr(route.request, "post_data", "") or "{}"
                if callable(post_data):
                    post_data = post_data()
                request_body = json.loads(post_data or "{}")
            if request_body.get("operation") == "hierarchy_apply":
                payload = {
                    "ok": True,
                    "scope": "library",
                    "staged_filename": "summaries.jsonl",
                    "operation": "hierarchy_apply",
                    "confirmed": bool(request_body.get("confirm")),
                    "dry_run": False,
                    "selected_records": [
                        {"record_index": 0, "doc_id": "library"},
                        {"record_index": 1, "doc_id": "alpha"},
                        {"record_index": 2, "doc_id": "beta"},
                    ],
                    "updates": [
                        {"record_index": 1, "doc_id": "alpha", "from_parent_id": "", "to_parent_id": "library"}
                    ],
                    "unchanged": [
                        {"record_index": 0, "doc_id": "library", "parent_id": ""}
                    ],
                    "skipped": [],
                    "errors": [],
                    "warnings": [
                        {
                            "record_index": 2,
                            "doc_id": "beta",
                            "parent_id": "external-root",
                            "reason": "unknown_parent_id",
                            "message": "parent_id is not a current Library source doc and will render at root level: external-root",
                        }
                    ],
                    "counts": {"selected": 3, "changed": 1, "updates": 1, "unchanged": 1, "skipped": 0, "errors": 0, "warnings": 1},
                    "backup_dir": "var/docs/backups/library/20260504-120700-documents-hierarchy-apply",
                    "rebuild": {"ok": True},
                    "hierarchy_apply_written": bool(request_body.get("confirm")),
                    "requires_confirmation": not bool(request_body.get("confirm")),
                    "summary_text": "Updated 1 Library hierarchy change(s)." if request_body.get("confirm") else "Validated 1 Library hierarchy change(s) without writing.",
                }
            else:
                payload = {
                    "ok": True,
                    "scope": "library",
                    "staged_filename": "summaries.jsonl",
                    "operation": "summary_apply",
                    "confirmed": bool(request_body.get("confirm")),
                    "dry_run": False,
                    "selected_records": [
                        {"record_index": 0, "doc_id": "library"},
                        {"record_index": 1, "doc_id": "alpha"},
                        {"record_index": 2, "doc_id": "beta"},
                    ],
                    "updates": [
                        {"record_index": 0, "doc_id": "library"},
                        {"record_index": 1, "doc_id": "alpha"},
                    ],
                    "skipped": [
                        {"record_index": 2, "doc_id": "beta", "reason": "missing_summary"}
                    ],
                    "errors": [],
                    "warnings": [],
                    "counts": {"selected": 3, "updates": 2, "skipped": 1, "errors": 0, "warnings": 1},
                    "backup_dir": "var/docs/backups/library/20260504-120600-documents-summary-apply",
                    "rebuild": {"ok": True},
                    "summary_apply_written": bool(request_body.get("confirm")),
                    "requires_confirmation": not bool(request_body.get("confirm")),
                    "summary_text": "Updated 2 Library summary update(s)." if request_body.get("confirm") else "Validated 2 Library summary update(s) without writing.",
                }
        else:
            payload = {"ok": False, "error": f"Unhandled mock route: {parsed.path}"}
        route.fulfill(status=200, content_type="application/json", body=json.dumps(payload))

    page.route("http://127.0.0.1:8789/**", handle)


def assert_mock_preview_flow(page) -> dict[str, object]:
    page.locator("#dataSharingReviewRun").click()
    page.wait_for_selector("[data-data-sharing-review-preview]", timeout=5000)
    page.wait_for_selector('[data-role="studio-modal"]', timeout=5000)
    preview_modal_title = page.locator("#studioModalTitle").text_content()
    preview_count_labels = page.locator(".dataSharingReviewResultModal__counts dt").evaluate_all(
        "nodes => nodes.map(node => node.textContent)"
    )
    preview_count_values = page.locator(".dataSharingReviewResultModal__counts dd").evaluate_all(
        "nodes => nodes.map(node => node.textContent)"
    )
    preview_issue_text = " ".join(page.locator(".dataSharingReviewResultModal__issues li").evaluate_all("nodes => nodes.map(node => node.textContent)"))
    if preview_modal_title != "Returned package review":
        raise AssertionError(f"unexpected preview result modal title: {preview_modal_title!r}")
    if preview_count_labels != ["records", "parsed", "malformed", "warnings", "errors"]:
        raise AssertionError(f"unexpected preview count labels: {preview_count_labels!r}")
    if preview_count_values != ["3", "3", "0", "1", "0"]:
        raise AssertionError(f"unexpected preview count values: {preview_count_values!r}")
    if "unknown_doc_id" not in preview_issue_text:
        raise AssertionError(f"preview warning missing from modal issues: {preview_issue_text!r}")
    page.locator('[data-role="modal-cancel"]').last.click()
    page.wait_for_selector('[data-role="studio-modal"]', state="detached", timeout=5000)
    result_button = page.locator("#dataSharingReviewResults")
    if result_button.is_hidden() or result_button.text_content() != "results":
        raise AssertionError("preview results button should be visible after successful preview status")
    result_button.click()
    page.wait_for_selector('[data-role="studio-modal"]', timeout=5000)
    reopened_title = page.locator("#studioModalTitle").text_content()
    reopened_summary = page.locator(".dataSharingReviewResultModal__summary").text_content()
    if reopened_title != "Returned package review" or reopened_summary != "Generated 3 Library returned package review files.":
        raise AssertionError(f"unexpected reopened results modal: {reopened_title!r}, {reopened_summary!r}")
    page.locator('[data-role="modal-cancel"]').last.click()
    page.wait_for_selector('[data-role="studio-modal"]', state="detached", timeout=5000)
    rows = page.locator("[data-data-sharing-review-preview]").count()
    titles = page.locator(".dataSharingReviewList__title").evaluate_all("nodes => nodes.map(node => node.textContent)")
    depths = page.locator("[data-data-sharing-review-preview]").evaluate_all(
        "nodes => nodes.map(node => Number(node.dataset.dataSharingReviewDepth || 0))"
    )
    meta = page.locator(".dataSharingReviewList__meta").evaluate_all("nodes => nodes.map(node => node.textContent)")
    if rows != 4:
        raise AssertionError(f"expected four preview rows, found {rows}")
    if titles != ["Relationship tree", "Library", "Alpha", "Beta"]:
        raise AssertionError(f"unexpected preview row titles: {titles!r}")
    if depths != [0, 0, 1, 2]:
        raise AssertionError(f"unexpected hierarchy depths: {depths!r}")
    if "not in current Library" not in meta[-1]:
        raise AssertionError(f"unknown current-Library state was not surfaced: {meta!r}")
    page.locator("#dataSharingReviewSelectAll").click()
    selection = page.locator("#dataSharingReviewSelectionSummary").text_content()
    if selection != "4 previews selected.":
        raise AssertionError(f"unexpected selection summary: {selection!r}")
    update_summary_disabled = page.locator("#dataSharingReviewUpdateSummary").evaluate("button => button.disabled")
    apply_hierarchy_disabled = page.locator("#dataSharingReviewApplyHierarchy").evaluate("button => button.disabled")
    if update_summary_disabled or apply_hierarchy_disabled:
        raise AssertionError("summary and hierarchy apply should enable for selected document previews")
    page.locator("#dataSharingReviewUpdateSummary").click()
    page.wait_for_selector('[data-role="studio-modal"]', timeout=5000)
    modal_title = page.locator("#studioModalTitle").text_content()
    if modal_title != "Update summaries?":
        raise AssertionError(f"unexpected summary apply modal title: {modal_title!r}")
    page.locator('[data-role="modal-cancel"]').last.click()
    page.wait_for_selector('[data-role="studio-modal"]', state="detached", timeout=5000)
    cancelled_status = page.locator("#dataSharingReviewStatus").text_content()
    if cancelled_status != "Summary update cancelled.":
        raise AssertionError(f"unexpected cancelled status: {cancelled_status!r}")
    page.locator("#dataSharingReviewUpdateSummary").click()
    page.wait_for_selector('[data-role="studio-modal"]', timeout=5000)
    page.locator('[data-role="modal-primary"]').click()
    page.wait_for_function(
        "selector => document.querySelector(selector)?.textContent === 'Updated 2 Library summary update(s).'",
        arg="#dataSharingReviewStatus",
        timeout=5000,
    )
    page.wait_for_selector('[data-role="studio-modal"]', timeout=5000)
    summary_modal_title = page.locator("#studioModalTitle").text_content()
    summary_count_labels = page.locator(".dataSharingReviewResultModal__counts dt").evaluate_all(
        "nodes => nodes.map(node => node.textContent)"
    )
    summary_count_values = page.locator(".dataSharingReviewResultModal__counts dd").evaluate_all(
        "nodes => nodes.map(node => node.textContent)"
    )
    applied_status = page.locator("#dataSharingReviewStatus").text_content()
    summary = page.locator(".dataSharingReviewResultModal__summary").text_content()
    issue_text = " ".join(page.locator(".dataSharingReviewResultModal__issues li").evaluate_all("nodes => nodes.map(node => node.textContent)"))
    if applied_status != "Updated 2 Library summary update(s).":
        raise AssertionError(f"unexpected applied status: {applied_status!r}")
    if summary_modal_title != "Summary update complete":
        raise AssertionError(f"unexpected summary result modal title: {summary_modal_title!r}")
    if summary_count_labels != ["updates", "skipped", "errors"]:
        raise AssertionError(f"unexpected summary count labels: {summary_count_labels!r}")
    if summary_count_values != ["2", "1", "0"]:
        raise AssertionError(f"unexpected summary count values: {summary_count_values!r}")
    if "2 updates; 1 skipped; 0 errors." not in summary:
        raise AssertionError(f"summary apply counts missing from summary: {summary!r}")
    if "missing_summary" not in issue_text:
        raise AssertionError(f"summary apply skipped row missing from issues: {issue_text!r}")
    page.locator('[data-role="modal-cancel"]').last.click()
    page.wait_for_selector('[data-role="studio-modal"]', state="detached", timeout=5000)
    page.locator("#dataSharingReviewApplyHierarchy").click()
    page.wait_for_selector('[data-role="studio-modal"]', timeout=5000)
    hierarchy_modal_title = page.locator("#studioModalTitle").text_content()
    if hierarchy_modal_title != "Update hierarchy?":
        raise AssertionError(f"unexpected hierarchy apply modal title: {hierarchy_modal_title!r}")
    page.locator('[data-role="modal-cancel"]').last.click()
    page.wait_for_selector('[data-role="studio-modal"]', state="detached", timeout=5000)
    hierarchy_cancelled_status = page.locator("#dataSharingReviewStatus").text_content()
    if hierarchy_cancelled_status != "Hierarchy update cancelled.":
        raise AssertionError(f"unexpected hierarchy cancelled status: {hierarchy_cancelled_status!r}")
    page.locator("#dataSharingReviewApplyHierarchy").click()
    page.wait_for_selector('[data-role="studio-modal"]', timeout=5000)
    page.locator('[data-role="modal-primary"]').click()
    page.wait_for_function(
        "selector => document.querySelector(selector)?.textContent === 'Updated 1 Library hierarchy change(s).'",
        arg="#dataSharingReviewStatus",
        timeout=5000,
    )
    page.wait_for_selector('[data-role="studio-modal"]', timeout=5000)
    hierarchy_result_title = page.locator("#studioModalTitle").text_content()
    hierarchy_count_labels = page.locator(".dataSharingReviewResultModal__counts dt").evaluate_all(
        "nodes => nodes.map(node => node.textContent)"
    )
    hierarchy_count_values = page.locator(".dataSharingReviewResultModal__counts dd").evaluate_all(
        "nodes => nodes.map(node => node.textContent)"
    )
    hierarchy_status = page.locator("#dataSharingReviewStatus").text_content()
    hierarchy_summary = page.locator(".dataSharingReviewResultModal__summary").text_content()
    hierarchy_issue_text = " ".join(page.locator(".dataSharingReviewResultModal__issues li").evaluate_all("nodes => nodes.map(node => node.textContent)"))
    if hierarchy_result_title != "Hierarchy update complete":
        raise AssertionError(f"unexpected hierarchy result modal title: {hierarchy_result_title!r}")
    if hierarchy_count_labels != ["changed", "unchanged", "skipped", "warnings", "errors"]:
        raise AssertionError(f"unexpected hierarchy count labels: {hierarchy_count_labels!r}")
    if hierarchy_count_values != ["1", "1", "0", "1", "0"]:
        raise AssertionError(f"unexpected hierarchy count values: {hierarchy_count_values!r}")
    if "1 changed; 1 unchanged; 0 skipped; 1 warnings; 0 errors." not in hierarchy_summary:
        raise AssertionError(f"hierarchy apply counts missing from summary: {hierarchy_summary!r}")
    if "unknown_parent_id" not in hierarchy_issue_text:
        raise AssertionError(f"hierarchy apply warning missing from issues: {hierarchy_issue_text!r}")
    page.locator('[data-role="modal-cancel"]').last.click()
    page.wait_for_selector('[data-role="studio-modal"]', state="detached", timeout=5000)
    return {
        "preview_rows": rows,
        "selected_summary": selection,
        "depths": depths,
        "summary_apply": applied_status,
        "hierarchy_apply": hierarchy_status,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:4000")
    parser.add_argument("--site-root", help="Serve a built site root on a temporary local HTTP server.")
    parser.add_argument("--block-docs-service", action="store_true")
    parser.add_argument("--mock-docs-service", action="store_true")
    parser.add_argument("--route-path", default="/studio/data-sharing/review/")
    parser.add_argument("--expect-unsupported", default="")
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
                page.goto(route_url(base_url, args.route_path), wait_until="domcontentloaded")
                attrs = wait_for_studio_route_ready(page, ROOT_SELECTOR, args.timeout_ms)
                assert_ready_contract(attrs)
                if args.block_docs_service and attrs["service"] != "unavailable":
                    raise AssertionError(f"expected unavailable service state: {attrs!r}")
                content = assert_route_content(page, args.block_docs_service)
                if args.expect_unsupported:
                    content["unsupported_adapter"] = assert_unsupported_adapter_state(page, args.expect_unsupported)
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
