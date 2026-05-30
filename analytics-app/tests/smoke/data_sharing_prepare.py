#!/usr/bin/env python3
"""Smoke-check the data sharing prepare Analytics route."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
from threading import Thread
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

ANALYTICS_SERVER_DIR = REPO_ROOT / "analytics-app" / "app" / "server"
ANALYTICS_PACKAGE_DIR = ANALYTICS_SERVER_DIR / "analytics_app"
for path in (ANALYTICS_SERVER_DIR, ANALYTICS_PACKAGE_DIR):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

from analytics_app_server import AnalyticsAppServer  # noqa: E402

ROOT_SELECTOR = "#dataSharingPrepareRoot"
EXPECTED_CONFIG_IDS = {
    "library-parent-child-relationships",
    "library-document-summaries",
    "library-full-document-content",
}


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


def start_local_app_server() -> tuple[AnalyticsAppServer, str]:
    server = AnalyticsAppServer(("127.0.0.1", 0), REPO_ROOT)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def route_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}{path}"


def generated_docs_index() -> dict[str, object]:
    return {
        "docs": [
            {
                "doc_id": "modal-parent",
                "title": "Modal parent",
                "viewable": True,
                "content_text_length": 120,
                "summary": "Parent summary.",
            },
            {
                "doc_id": "modal-empty-child",
                "parent_id": "modal-parent",
                "title": "Modal empty child",
                "viewable": True,
                "content_text_length": 0,
                "summary": "",
            },
            {
                "doc_id": "modal-hidden-child",
                "parent_id": "modal-parent",
                "title": "Modal hidden child",
                "viewable": False,
                "content_text_length": 45,
                "summary": "Hidden summary.",
            },
        ],
    }


def selectable_records_payload() -> dict[str, object]:
    docs = generated_docs_index()["docs"]
    return {
        "ok": True,
        "data_domain": "library",
        "adapter_id": "documents",
        "scope": "library",
        "selection_model": "documents",
        "records": docs,
        "docs": docs,
        "source": {
            "kind": "adapter",
            "module": "documents",
            "source": "generated_docs_index",
            "scope": "library",
        },
    }


def prepare_result_payload() -> dict[str, object]:
    return {
        "ok": True,
        "target_format": "json",
        "count_unit": "document",
        "counts": {
            "selected": 3,
            "exported": 2,
            "skipped": 1,
            "failed": 0,
            "truncated": 0,
        },
        "output_files": [
            "var/studio/data-sharing/library/exports/modal-smoke.json",
        ],
        "warnings": ["Skipped 1 non-viewable document."],
        "summary_text": "Package prepared.",
    }


def install_mock_data_sharing_api(page) -> list[dict[str, object]]:
    prepare_requests: list[dict[str, object]] = []

    def handle(route):
        request = route.request
        parsed = urlparse(request.url)
        if parsed.path not in {
            "/analytics/api/data-sharing/health",
            "/analytics/api/data-sharing/selectable-records",
            "/analytics/api/data-sharing/prepare",
        }:
            route.continue_()
            return
        if parsed.path == "/analytics/api/data-sharing/health":
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"ok": True, "service": "analytics_data_sharing", "dry_run": True}),
            )
            return
        if parsed.path == "/analytics/api/data-sharing/selectable-records":
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(selectable_records_payload()),
            )
            return
        if parsed.path == "/analytics/api/data-sharing/prepare":
            post_data_json = request.post_data_json
            prepare_requests.append(post_data_json() if callable(post_data_json) else post_data_json)
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(prepare_result_payload()),
            )
            return
        route.fulfill(
            status=404,
            content_type="application/json",
            body=json.dumps({"ok": False, "error": "Unexpected mock Data Sharing API route"}),
        )

    page.route("**/*", handle)
    return prepare_requests


def block_data_sharing_api(route) -> None:
    parsed = urlparse(route.request.url)
    if parsed.path in {
        "/analytics/api/data-sharing/health",
        "/analytics/api/data-sharing/selectable-records",
        "/analytics/api/data-sharing/prepare",
    }:
        route.abort()
        return
    route.continue_()


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


def assert_ready_contract(attrs: dict[str, str], expect_unavailable_service: bool = False) -> None:
    if attrs["route"] != "data-sharing-prepare":
        raise AssertionError(f"unexpected route attribute: {attrs['route']!r}")
    if attrs["ready"] != "true":
        raise AssertionError(f"route did not become ready: {attrs!r}")
    if attrs["busy"] == "true":
        raise AssertionError(f"route stayed busy after ready: {attrs!r}")
    if attrs["mode"] != "documents":
        raise AssertionError(f"unexpected route mode: {attrs['mode']!r}")
    if attrs["service"] not in {"available", "unavailable"}:
        raise AssertionError(f"unexpected service state: {attrs['service']!r}")
    if not expect_unavailable_service and attrs["recordLoaded"] != "true":
        raise AssertionError(f"Library docs did not load before ready: {attrs!r}")


def assert_route_content(page, expect_unavailable_service: bool) -> dict[str, object]:
    config_ids = set(
        page.locator("#dataSharingPrepareConfigSelect option").evaluate_all(
            "options => options.map(option => option.value)"
        )
    )
    missing_config_ids = EXPECTED_CONFIG_IDS.difference(config_ids)
    if missing_config_ids:
        raise AssertionError(f"missing sharing profile ids: {sorted(missing_config_ids)!r}")

    doc_ids = page.locator("[data-data-sharing-prepare-doc]").evaluate_all(
        "rows => rows.map(row => row.getAttribute('data-data-sharing-prepare-doc'))"
    )
    if not doc_ids and not expect_unavailable_service:
        raise AssertionError("Data Sharing prepare document list is empty")
    run_disabled = page.locator("#dataSharingPrepareRun").evaluate("button => button.disabled")
    if expect_unavailable_service:
        if not run_disabled:
            raise AssertionError("run button should be disabled when the Analytics Data Sharing API is unavailable")
        status_text = page.locator("#dataSharingPrepareStatus").inner_text(timeout=5000)
        if "Analytics Data Sharing API unavailable" not in status_text:
            raise AssertionError(f"unexpected unavailable status text: {status_text!r}")
        return {
            "config_ids": sorted(config_ids),
            "doc_count": len(doc_ids),
            "filters": {},
            "formats": {},
            "run_disabled": bool(run_disabled),
            "status": status_text,
        }

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
    return page.locator("input[name='dataSharingPrepareFormat']").evaluate_all(
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

    page.locator("#dataSharingPrepareConfigSelect").select_option("library-full-document-content")
    page.wait_for_function(
        """() => {
            const jsonl = document.querySelector("input[name='dataSharingPrepareFormat'][value='jsonl']");
            const json = document.querySelector("input[name='dataSharingPrepareFormat'][value='json']");
            return jsonl && json && jsonl.checked && !jsonl.disabled && !json.disabled;
        }"""
    )
    full_content = by_value()

    page.locator("#dataSharingPrepareConfigSelect").select_option("library-document-summaries")
    page.wait_for_function(
        """() => {
            const jsonl = document.querySelector("input[name='dataSharingPrepareFormat'][value='jsonl']");
            const json = document.querySelector("input[name='dataSharingPrepareFormat'][value='json']");
            return jsonl && json && jsonl.checked && !jsonl.disabled && !json.disabled;
        }"""
    )

    page.locator("#dataSharingPrepareConfigSelect").select_option("library-parent-child-relationships")
    page.wait_for_function(
        """() => {
            const jsonl = document.querySelector("input[name='dataSharingPrepareFormat'][value='jsonl']");
            const json = document.querySelector("input[name='dataSharingPrepareFormat'][value='json']");
            return jsonl && json && json.checked && !json.disabled && jsonl.disabled;
        }"""
    )
    return {
        "parent_default": "json",
        "content_default": "jsonl" if full_content["jsonl"]["checked"] else "",
    }


def assert_filter_flow(page, total_docs: int) -> dict[str, int]:
    filter_keys = page.locator("[data-data-sharing-prepare-filter]").evaluate_all(
        "buttons => buttons.map(button => button.getAttribute('data-data-sharing-prepare-filter'))"
    )
    expected_keys = ["all", "no_content", "not_viewable"]
    if filter_keys != expected_keys:
        raise AssertionError(f"unexpected data sharing prepare filters: {filter_keys!r}")

    counts = page.locator("[data-data-sharing-prepare-doc]").evaluate_all(
        """rows => ({
            all: rows.length,
            no_content: rows.filter(row => row.dataset.dataSharingPrepareNoContent === "true").length,
            not_viewable: rows.filter(row => row.dataset.dataSharingPrepareViewable === "false").length
        })"""
    )
    if counts["all"] != total_docs:
        raise AssertionError(f"show all count mismatch: {counts!r}; total={total_docs!r}")

    filter_labels = page.locator("[data-data-sharing-prepare-filter]").evaluate_all(
        "buttons => buttons.map(button => button.textContent.trim())"
    )
    for key, label in zip(expected_keys, filter_labels):
        if f"[{counts[key]}]" not in label:
            raise AssertionError(f"filter {key!r} label lacks count {counts[key]!r}: {label!r}")

    def assert_filter(key: str, row_attribute: str, row_value: str, expected_count: int) -> None:
        page.locator(f"[data-data-sharing-prepare-filter='{key}']").click()
        page.wait_for_function(
            """([attr, expected]) => {
                const expectedValue = attr[1];
                const attrName = attr[0];
                const rows = Array.from(document.querySelectorAll("[data-data-sharing-prepare-doc]"));
                return rows.length === expected && rows.every(row => row.getAttribute(attrName) === expectedValue);
            }""",
            arg=[[row_attribute, row_value], expected_count],
        )
        page.locator("#dataSharingPrepareSelectAll").click()
        checked_count = page.locator("[data-data-sharing-prepare-doc] input[type='checkbox']:checked").count()
        if checked_count != expected_count:
            raise AssertionError(f"select all selected {checked_count} rows for {key}, expected {expected_count}")
        page.locator("#dataSharingPrepareClear").click()
        checked_after_clear = page.locator("[data-data-sharing-prepare-doc] input[type='checkbox']:checked").count()
        if checked_after_clear != 0:
            raise AssertionError(f"clear left {checked_after_clear} selected rows for {key}")

    assert_filter("no_content", "data-data-sharing-prepare-no-content", "true", counts["no_content"])
    assert_filter("not_viewable", "data-data-sharing-prepare-viewable", "false", counts["not_viewable"])
    page.locator("[data-data-sharing-prepare-filter='all']").click()
    page.wait_for_function(
        "expected => document.querySelectorAll('[data-data-sharing-prepare-doc]').length === expected",
        arg=total_docs,
    )
    return counts


def assert_prepare_result_modal(page, prepare_requests: list[dict[str, object]], timeout_ms: int) -> dict[str, object]:
    page.locator("#dataSharingPrepareSelectAll").click()
    page.locator("#dataSharingPrepareRun").click()
    page.wait_for_selector('[data-role="studio-modal"]', timeout=timeout_ms)

    modal_state = page.locator('[data-role="studio-modal"]').evaluate(
        """modal => {
            const dialog = modal.querySelector('[role="dialog"]');
            const title = modal.querySelector('.tagStudioModal__title');
            const actionButtons = Array.from(modal.querySelectorAll('.tagStudioModal__actions button'));
            const rows = Array.from(modal.querySelectorAll('.dataSharingPrepareModal__countRow'))
                .map(row => Array.from(row.children).map(node => node.textContent.trim()));
            const issues = Array.from(modal.querySelectorAll('.dataSharingPrepareModal__issues li'))
                .map(node => node.textContent.trim());
            const fileList = modal.querySelector('.dataSharingPrepareModal__fileList');
            return {
                role: dialog ? dialog.getAttribute('role') : "",
                modal: dialog ? dialog.getAttribute('aria-modal') : "",
                dialogClass: dialog ? dialog.className : "",
                labelledBy: dialog ? dialog.getAttribute('aria-labelledby') : "",
                titleId: title ? title.id : "",
                title: title ? title.textContent.trim() : "",
                actionLabels: actionButtons.map(button => button.textContent.trim()),
                actionClasses: actionButtons.map(button => button.className),
                rows,
                fileList: fileList ? fileList.value : "",
                readonlyFiles: fileList ? fileList.readOnly : false,
                issues,
                activeRole: document.activeElement ? document.activeElement.getAttribute('data-role') : ""
            };
        }"""
    )
    if modal_state["role"] != "dialog" or modal_state["modal"] != "true":
        raise AssertionError(f"prepare result modal lacks dialog semantics: {modal_state!r}")
    if not modal_state["labelledBy"] or modal_state["labelledBy"] != modal_state["titleId"]:
        raise AssertionError(f"prepare result modal is not labelled by its title: {modal_state!r}")
    if "tagStudioModal__dialog--" in modal_state["dialogClass"]:
        raise AssertionError(f"prepare result modal should use the default size contract: {modal_state!r}")
    if modal_state["title"] != "Package result":
        raise AssertionError(f"prepare result modal title mismatch: {modal_state!r}")
    if modal_state["actionLabels"] != ["Close"]:
        raise AssertionError(f"prepare result modal close action mismatch: {modal_state!r}")
    if not modal_state["actionClasses"] or "tagStudio__button--defaultWidth" not in modal_state["actionClasses"][0]:
        raise AssertionError(f"prepare result modal action is missing the default-width button contract: {modal_state!r}")
    if ["format", "JSON"] not in modal_state["rows"]:
        raise AssertionError(f"prepare result modal did not render the target format row: {modal_state!r}")
    if ["packaged", "2 documents"] not in modal_state["rows"]:
        raise AssertionError(f"prepare result modal did not render the packaged count: {modal_state!r}")
    if modal_state["fileList"] != "modal-smoke.json" or not modal_state["readonlyFiles"]:
        raise AssertionError(f"prepare result modal file list mismatch: {modal_state!r}")
    if modal_state["issues"] != ["Skipped 1 non-viewable document."]:
        raise AssertionError(f"prepare result modal warnings mismatch: {modal_state!r}")
    if modal_state["activeRole"] != "modal-cancel":
        raise AssertionError(f"prepare result modal did not focus the close action: {modal_state!r}")
    if not prepare_requests:
        raise AssertionError("prepare result modal smoke did not call the prepare endpoint")
    if prepare_requests[-1].get("data_domain") != "library" or prepare_requests[-1].get("config_id") != "library-parent-child-relationships":
        raise AssertionError(f"prepare request ownership changed unexpectedly: {prepare_requests[-1]!r}")

    page.keyboard.press("Escape")
    page.wait_for_selector('[data-role="studio-modal"]', state="detached", timeout=timeout_ms)
    focus_returned = page.evaluate("() => document.activeElement && document.activeElement.id")
    if focus_returned != "dataSharingPrepareRun":
        raise AssertionError(f"prepare result modal did not return focus to opener: {focus_returned!r}")

    page.locator("#dataSharingPrepareRun").click()
    page.wait_for_selector('[data-role="studio-modal"]', timeout=timeout_ms)
    page.locator(".tagStudioModal__backdrop").click(position={"x": 8, "y": 8})
    page.wait_for_selector('[data-role="studio-modal"]', state="detached", timeout=timeout_ms)

    page.locator("#dataSharingPrepareRun").click()
    page.wait_for_selector('[data-role="studio-modal"]', timeout=timeout_ms)
    page.locator('[data-role="modal-cancel"]').last.click()
    page.wait_for_selector('[data-role="studio-modal"]', state="detached", timeout=timeout_ms)

    return modal_state


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Smoke-check the Local Analytics Data Sharing prepare route. "
            "By default, this starts a temporary Local Analytics app server."
        )
    )
    host_group = parser.add_mutually_exclusive_group()
    host_group.add_argument("--base-url", help="Use an already running Local Analytics base URL.")
    host_group.add_argument("--site-root", help="Serve a built static site root on a temporary local HTTP server.")
    host_group.add_argument("--local-app", action="store_true", help="Serve the local Analytics app on a temporary local HTTP server.")
    parser.add_argument("--block-data-sharing-api", action="store_true")
    parser.add_argument("--mock-data-sharing-api", action="store_true")
    parser.add_argument("--timeout-ms", type=int, default=15000)
    args = parser.parse_args()

    static_server = None
    local_app_server = None
    base_url = args.base_url or ""
    if args.local_app or (not base_url and not args.site_root):
        local_app_server, base_url = start_local_app_server()
    elif args.site_root:
        static_server, base_url = start_static_server(Path(args.site_root))

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                prepare_requests: list[dict[str, object]] = []
                block_api = args.block_data_sharing_api
                mock_api = args.mock_data_sharing_api
                if mock_api:
                    prepare_requests = install_mock_data_sharing_api(page)
                elif block_api:
                    page.route("**/*", block_data_sharing_api)
                page.goto(route_url(base_url, "/analytics/data-sharing/prepare/?mode=manage"), wait_until="domcontentloaded")
                attrs = wait_for_studio_route_ready(page, ROOT_SELECTOR, args.timeout_ms)
                assert_ready_contract(attrs, block_api)
                if block_api and attrs["service"] != "unavailable":
                    raise AssertionError(f"expected unavailable service state: {attrs!r}")
                content = assert_route_content(page, block_api)
                modal = None
                if mock_api:
                    if attrs["service"] != "available":
                        raise AssertionError(f"expected available mock service state: {attrs!r}")
                    modal = assert_prepare_result_modal(page, prepare_requests, args.timeout_ms)
                print(json.dumps({"route": attrs, "content": content, "modal": modal}, sort_keys=True))
            finally:
                browser.close()
    finally:
        if static_server is not None:
            static_server.shutdown()
            static_server.server_close()
        if local_app_server is not None:
            local_app_server.shutdown()
            local_app_server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
