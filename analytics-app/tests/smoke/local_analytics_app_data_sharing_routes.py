#!/usr/bin/env python3
"""Smoke-check local Analytics Data Sharing route shells."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from http import HTTPStatus
from pathlib import Path
from threading import Thread
from urllib.parse import urlparse

from playwright.sync_api import expect, sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))
ANALYTICS_SERVER_DIR = REPO_ROOT / "analytics-app" / "app" / "server"
ANALYTICS_PACKAGE_DIR = ANALYTICS_SERVER_DIR / "analytics_app"
for path in (ANALYTICS_SERVER_DIR, ANALYTICS_PACKAGE_DIR):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

from analytics_app_server import AnalyticsAppServer  # noqa: E402
from tests.smoke.route_ready_helpers import wait_for_route_ready  # noqa: E402


def start_server() -> tuple[AnalyticsAppServer, str]:
    server = AnalyticsAppServer(("127.0.0.1", 0), REPO_ROOT)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def selectable_records_payload() -> dict[str, object]:
    return {
        "ok": True,
        "adapter_id": "documents",
        "selection_model": "documents",
        "records": [
            {
                "id": "library",
                "name": "Library",
                "doc_id": "library",
                "title": "Library",
                "published": True,
                "viewable": True,
                "content_text_length": 120,
                "summary": "",
            },
            {
                "id": "alpha",
                "name": "Alpha",
                "doc_id": "alpha",
                "parent_id": "library",
                "title": "Alpha",
                "published": True,
                "viewable": True,
                "content_text_length": 80,
                "summary": "Alpha summary.",
            },
        ],
    }


def config_payload() -> dict[str, object]:
    return {
        "ok": True,
        "schema_version": "data_sharing_adapters_v2",
        "docs_scopes": [
            {
                "id": "library",
                "label": "Library",
                "source": "docs-viewer/source/library",
            }
        ],
        "adapters": [
            {
                "id": "documents",
                "label": "Documents",
                "status": "active",
                "data_domains": {
                    "documents": {
                        "app": "docs-viewer",
                        "label": "Documents",
                        "status": "active",
                        "selection_model": "documents",
                        "record_selectors": {
                            "docs_scope": {
                                "source": "docs_scope_config",
                                "required": True,
                            }
                        },
                    }
                },
                "capabilities": [
                    {
                        "operation": "prepare",
                        "status": "active",
                        "message": "",
                        "selection_model": "documents",
                        "sharing_profiles": [
                            {
                                "id": "document-content",
                                "label": "Document content",
                                "enabled": True,
                                "data_domains": ["documents"],
                                "target": {"format": "jsonl", "supported_formats": ["jsonl", "json"]},
                                "selection": {
                                    "mode": "explicit_doc_ids",
                                    "include_descendants": True,
                                    "include_non_viewable": True,
                                    "supports_missing_summary_only": True,
                                },
                            }
                        ],
                    },
                    {
                        "operation": "list_returned",
                        "status": "active",
                        "message": "",
                        "selection_model": "none",
                    },
                    {
                        "operation": "apply",
                        "status": "active",
                        "message": "",
                        "selection_model": "records",
                        "apply_actions": [
                            {
                                "id": "summary_apply",
                                "label": "Update summaries",
                                "status": "active",
                                "title": "Update source document summaries from returned rows.",
                            },
                            {
                                "id": "hierarchy_apply",
                                "label": "Apply hierarchy",
                                "status": "active",
                                "title": "Update source document hierarchy from returned rows.",
                            },
                        ],
                    },
                ],
            }
        ],
    }


def prepare_payload() -> dict[str, object]:
    return {
        "ok": True,
        "target_format": "jsonl",
        "count_unit": "document",
        "counts": {
            "selected": 2,
            "exported": 2,
            "skipped": 0,
            "failed": 0,
            "truncated": 0,
        },
        "output_files": [
            "var/analytics/data-sharing/exports/local-smoke.jsonl",
        ],
        "warnings": [],
        "summary_text": "Package prepared.",
    }


def returned_packages_payload(files: list[dict[str, object]] | None = None) -> dict[str, object]:
    staged_files = files if files is not None else [
        {
            "filename": "content.jsonl",
            "path": "var/analytics/data-sharing/import-staging/content.jsonl",
            "format": "jsonl",
            "size_bytes": 512,
            "modified_utc": "2026-05-04T12:00:00Z",
            "metadata_ok": True,
            "metadata_file": "var/analytics/data-sharing/meta/ds_20260504T120000Z.meta.json",
            "export_id": "ds_20260504T120000Z",
            "app": "docs-viewer",
            "data_domain": "documents",
            "adapter_id": "documents",
            "config_id": "document-content",
            "profile_id": "document-content",
            "scope": "library",
            "target_format": "jsonl",
            "record_shape": "document_rows",
        }
    ]
    return {
        "ok": True,
        "staging_root": "var/analytics/data-sharing/import-staging",
        "meta_root": "var/analytics/data-sharing/meta",
        "files": staged_files,
    }


def review_payload() -> dict[str, object]:
    return {
        "ok": True,
        "scope": "library",
        "summary_text": "Generated Library returned package review.",
        "detected_import_type": "document_changes",
        "source_export_id": "ds_20260504T120000Z",
        "generated_at": "2026-05-04T12:05:00Z",
        "counts": {
            "records": 2,
            "parsed_records": 2,
            "malformed_records": 0,
            "warnings": 0,
            "errors": 0,
        },
        "issues": [],
        "review_rows": [
            {
                "id": "library-record-1",
                "type": "document",
                "title": "Library",
                "meta": "library",
                "record_index": 0,
                "selectable": True,
                "issues": [],
                "depth": 0,
            },
            {
                "id": "alpha-record-2",
                "type": "document",
                "title": "Alpha",
                "meta": "alpha",
                "record_index": 1,
                "selectable": True,
                "issues": [],
                "depth": 1,
            },
        ],
    }


def install_mock_data_sharing_api(page, returned_payload: dict[str, object] | None = None) -> list[dict[str, object]]:
    calls: list[dict[str, object]] = []
    returned_packages = returned_payload or returned_packages_payload()

    def handle(route) -> None:
        request = route.request
        parsed = urlparse(request.url)
        data_sharing_paths = {
            "/analytics/api/data-sharing/health",
            "/analytics/api/data-sharing/config",
            "/analytics/api/data-sharing/selectable-records",
            "/analytics/api/data-sharing/prepare",
            "/analytics/api/data-sharing/returned-packages",
            "/analytics/api/data-sharing/returned-records",
            "/analytics/api/data-sharing/review",
        }
        if parsed.path not in data_sharing_paths:
            route.continue_()
            return
        call: dict[str, object] = {"method": request.method, "path": parsed.path}
        if request.method == "POST":
            try:
                call["body"] = request.post_data_json
            except Exception:
                call["body"] = request.post_data
        calls.append(call)
        payload: dict[str, object]
        if parsed.path == "/analytics/api/data-sharing/health":
            payload = {"ok": True, "service": "analytics_data_sharing", "dry_run": False}
        elif parsed.path == "/analytics/api/data-sharing/config":
            payload = config_payload()
        elif parsed.path == "/analytics/api/data-sharing/selectable-records":
            payload = selectable_records_payload()
        elif parsed.path == "/analytics/api/data-sharing/prepare":
            payload = prepare_payload()
        elif parsed.path == "/analytics/api/data-sharing/returned-packages":
            payload = returned_packages
        elif parsed.path == "/analytics/api/data-sharing/returned-records":
            payload = review_payload()
        elif parsed.path == "/analytics/api/data-sharing/review":
            payload = review_payload()
            body = call.get("body") if isinstance(call.get("body"), dict) else {}
            if body.get("review_action") == "summaries":
                payload["summary_text"] = "Generated Library summaries review."
        else:
            payload = {"ok": False, "error": f"Unexpected Data Sharing API route: {parsed.path}"}
        route.fulfill(status=200, content_type="application/json", body=json.dumps(payload))

    page.route("**/*", handle)
    return calls


def assert_runtime_views(base_url: str) -> None:
    with urllib.request.urlopen(f"{base_url}/analytics/runtime-config.json", timeout=10) as response:
        runtime_config = json.loads(response.read().decode("utf-8"))
    views = runtime_config.get("app", {}).get("runtime", {}).get("views", [])
    by_id = {view.get("id"): view for view in views if isinstance(view, dict)}
    expected = {
        "data_sharing_prepare": "/analytics/data-sharing/prepare/",
        "data_sharing_review": "/analytics/data-sharing/review/",
    }
    for view_id, path in expected.items():
        view = by_id.get(view_id)
        if not view or view.get("path") != path:
            raise AssertionError(f"runtime config missing {view_id}: {views!r}")
        if view.get("shell_type") != "html-template":
            raise AssertionError(f"runtime config missing template shell type for {view_id}: {view!r}")
        if not str(view.get("template") or "").startswith("/analytics/app/frontend/routes/"):
            raise AssertionError(f"runtime config missing route template for {view_id}: {view!r}")
    services = runtime_config.get("app", {}).get("runtime", {}).get("services", {})
    data_sharing = services.get("data_sharing", {}) if isinstance(services, dict) else {}
    if data_sharing.get("health") != "/analytics/api/data-sharing/health":
        raise AssertionError(f"runtime config missing Analytics Data Sharing API endpoints: {data_sharing!r}")
    if data_sharing.get("config") != "/analytics/api/data-sharing/config":
        raise AssertionError(f"runtime config missing Analytics Data Sharing config endpoint: {data_sharing!r}")


def read_json_url(url: str) -> dict[str, object]:
    with urllib.request.urlopen(url, timeout=10) as response:
        if response.status != HTTPStatus.OK:
            raise AssertionError(f"unexpected status for {url}: {response.status}")
        return json.loads(response.read().decode("utf-8"))


def assert_data_sharing_api(base_url: str) -> None:
    health = read_json_url(f"{base_url}/analytics/api/data-sharing/health")
    if health.get("service") != "analytics_data_sharing":
        raise AssertionError(f"unexpected Data Sharing health payload: {health!r}")
    records = read_json_url(f"{base_url}/analytics/api/data-sharing/selectable-records?data_domain=documents&docs_scope=library")
    if records.get("adapter_id") != "documents" or records.get("selection_model") != "documents":
        raise AssertionError(f"unexpected selectable-record payload: {records!r}")
    if not records.get("records"):
        raise AssertionError(f"selectable-record payload is empty: {records!r}")


def assert_prepare(page, base_url: str) -> None:
    page.goto(f"{base_url}/analytics/data-sharing/prepare/", wait_until="domcontentloaded")
    if page.locator("[data-analytics-route-outlet]").count() != 1:
        raise AssertionError("prepare route did not render the static Analytics shell outlet")
    root = page.locator("#dataSharingPrepareRoot")
    wait_for_route_ready(page, "#dataSharingPrepareRoot", "data-analytics-ready", "data-analytics-busy")
    expect(root).to_have_attribute("data-analytics-service", "available", timeout=10_000)
    expect(root).to_have_attribute("data-analytics-record-loaded", "true", timeout=10_000)
    app_initial = page.locator("#dataSharingPrepareAppSelect").evaluate(
        "select => ({ value: select.value, selectedIndex: select.selectedIndex })"
    )
    if app_initial != {"value": "docs-viewer", "selectedIndex": 0}:
        raise AssertionError(f"prepare app select should start on the only available app: {app_initial!r}")
    page.locator("#dataSharingPrepareAppSelect").select_option("docs-viewer")
    page.locator("#dataSharingPrepareDataDomainSelect").select_option("documents")
    page.locator("#dataSharingPrepareConfigSelect").select_option("document-content")
    if page.locator("#dataSharingPrepareDocsScopeSelect").evaluate("select => select.value") != "":
        raise AssertionError("prepare docs scope select should start blank")
    page.locator("#dataSharingPrepareDocsScopeSelect").select_option("library")
    expect(root).to_have_attribute("data-analytics-record-loaded", "true", timeout=10_000)
    expect(page.locator("#dataSharingPrepareList [data-selectable-list-row='true']").first).to_be_visible(timeout=10_000)
    page.locator("#dataSharingPrepareSelectAll").click()
    expect(page.locator("#dataSharingPrepareSelectionSummary")).to_contain_text("2 records selected.", timeout=10_000)
    page.locator("#dataSharingPrepareMissingSummaryOnly").check()
    expect(page.locator("#dataSharingPrepareSelectionSummary")).to_contain_text("1 record selected.", timeout=10_000)
    page.locator("#dataSharingPrepareMissingSummaryOnly").uncheck()
    expect(page.locator("#dataSharingPrepareSelectionSummary")).to_contain_text("2 records selected.", timeout=10_000)
    parent_checkbox = page.locator("#dataSharingPrepareList input.sharedSelectableList__checkbox[value='library']")
    child_checkbox = page.locator("#dataSharingPrepareList input.sharedSelectableList__checkbox[value='alpha']")
    expect(page.locator("#dataSharingPrepareIncludeDescendants")).to_be_checked(timeout=10_000)
    parent_checkbox.check()
    expect(child_checkbox).to_be_checked(timeout=10_000)
    child_checkbox.uncheck()
    parent_state = parent_checkbox.evaluate("input => ({ checked: input.checked, indeterminate: input.indeterminate })")
    child_state = child_checkbox.evaluate("input => ({ checked: input.checked, indeterminate: input.indeterminate })")
    if parent_state != {"checked": True, "indeterminate": False}:
        raise AssertionError(f"parent checkbox should remain checked after deselecting child: {parent_state!r}")
    if child_state != {"checked": False, "indeterminate": False}:
        raise AssertionError(f"child checkbox should be unchecked after deselection: {child_state!r}")
    page.locator("#dataSharingPrepareRun").click()
    expect(page.locator("#dataSharingPrepareStatus")).to_contain_text("Package prepared.", timeout=10_000)


def assert_review(page, base_url: str) -> None:
    page.goto(f"{base_url}/analytics/data-sharing/review/?data_domain=documents", wait_until="domcontentloaded")
    if page.locator("[data-analytics-route-outlet]").count() != 1:
        raise AssertionError("review route did not render the static Analytics shell outlet")
    root = page.locator("#dataSharingReviewRoot")
    wait_for_route_ready(page, "#dataSharingReviewRoot", "data-analytics-ready", "data-analytics-busy")
    expect(root).to_have_attribute("data-analytics-service", "available", timeout=10_000)
    expect(root).to_have_attribute("data-analytics-record-loaded", "true", timeout=10_000)
    expect(page.locator("#dataSharingReviewFileSelect")).to_have_value("content.jsonl", timeout=10_000)
    review_list = page.locator("#dataSharingReviewList")
    if not review_list.evaluate("node => node.classList.contains('sharedSelectableList')"):
        raise AssertionError("review list should use the shared selectable list component")
    expect(review_list.locator("[data-selectable-list-row='true']")).to_have_count(2, timeout=10_000)
    expect(review_list.locator("input.sharedSelectableList__checkbox")).to_have_count(0, timeout=10_000)
    expect(review_list).to_contain_text("Library", timeout=10_000)
    expect(review_list).to_contain_text("Alpha", timeout=10_000)
    expect(page.locator("#dataSharingReviewRun")).to_be_enabled(timeout=10_000)
    page.locator("#dataSharingReviewRun").click()
    expect(page.locator("#dataSharingReviewMenu")).to_contain_text("Content", timeout=10_000)
    expect(page.locator("#dataSharingReviewMenu")).to_contain_text("Summaries", timeout=10_000)
    expect(page.locator("#dataSharingReviewMenu")).to_contain_text("Hierarchy", timeout=10_000)
    page.keyboard.press("Escape")
    expect(page.locator("#dataSharingReviewActionsButton")).to_be_enabled(timeout=10_000)
    page.locator("#dataSharingReviewActionsButton").click()
    expect(page.locator("#dataSharingReviewActionsMenu")).to_contain_text("Update summaries", timeout=10_000)
    expect(page.locator("#dataSharingReviewActionsMenu")).to_contain_text("Apply hierarchy", timeout=10_000)
    expect(page.locator("#dataSharingReviewActionsMenu")).not_to_contain_text("Create source docs", timeout=10_000)
    page.keyboard.press("Escape")
    page.locator("#dataSharingReviewRun").click()
    page.locator("#dataSharingReviewMenu [data-data-sharing-review-action='summaries']").click()
    expect(page.locator("#dataSharingReviewStatus")).to_contain_text(
        "Generated Library summaries review.",
        timeout=10_000,
    )


def assert_review_empty(page, base_url: str) -> None:
    page.goto(f"{base_url}/analytics/data-sharing/review/?data_domain=documents", wait_until="domcontentloaded")
    root = page.locator("#dataSharingReviewRoot")
    wait_for_route_ready(page, "#dataSharingReviewRoot", "data-analytics-ready", "data-analytics-busy")
    expect(root).to_have_attribute("data-analytics-service", "available", timeout=10_000)
    expect(root).to_have_attribute("data-analytics-record-loaded", "false", timeout=10_000)
    status = page.locator("#dataSharingReviewStatus")
    expect(status).to_contain_text(
        "No staged returned package files found under var/analytics/data-sharing/import-staging/.",
        timeout=10_000,
    )
    status_text = status.inner_text()
    if "{" in status_text or "}" in status_text:
        raise AssertionError(f"empty review status still contains unresolved tokens: {status_text!r}")
    expect(page.locator("#dataSharingReviewFileSelect")).to_be_hidden(timeout=10_000)
    expect(page.locator("#dataSharingReviewResolvedContext")).to_be_hidden(timeout=10_000)
    context_text = page.locator("#dataSharingReviewResolvedContext").inner_text().strip()
    if context_text:
        raise AssertionError(f"empty review context should not expose unresolved metadata: {context_text!r}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)

    server, base_url = start_server()
    try:
        assert_runtime_views(base_url)
        assert_data_sharing_api(base_url)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            console_errors: list[str] = []
            page_errors: list[str] = []
            requests: list[str] = []
            page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
            page.on("pageerror", lambda error: page_errors.append(str(error)))
            page.on("request", lambda request: requests.append(request.url))
            data_sharing_api_calls = install_mock_data_sharing_api(page)

            assert_prepare(page, base_url)
            assert_review(page, base_url)

            empty_page = browser.new_page()
            empty_page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
            empty_page.on("pageerror", lambda error: page_errors.append(str(error)))
            empty_page.on("request", lambda request: requests.append(request.url))
            data_sharing_api_calls.extend(
                install_mock_data_sharing_api(empty_page, returned_packages_payload(files=[]))
            )
            assert_review_empty(empty_page, base_url)
            browser.close()

        required_paths = {
            "/analytics/api/data-sharing/health",
            "/analytics/api/data-sharing/config",
            "/analytics/api/data-sharing/selectable-records",
            "/analytics/api/data-sharing/prepare",
            "/analytics/api/data-sharing/returned-packages",
            "/analytics/api/data-sharing/review",
        }
        seen_paths = {str(call["path"]) for call in data_sharing_api_calls}
        missing_paths = required_paths.difference(seen_paths)
        if missing_paths:
            raise AssertionError(f"missing Analytics Data Sharing API calls: {sorted(missing_paths)!r}; calls={data_sharing_api_calls!r}")
        if "/docs/generated/index" in seen_paths:
            raise AssertionError(f"prepare page still read the generic generated docs index: {data_sharing_api_calls!r}")
        prepare_calls = [call for call in data_sharing_api_calls if call["path"] == "/analytics/api/data-sharing/prepare"]
        if len(prepare_calls) != 1:
            raise AssertionError(f"unexpected prepare call count: {prepare_calls!r}")
        prepare_body = prepare_calls[0].get("body")
        selection = prepare_body.get("selection", {}) if isinstance(prepare_body, dict) else {}
        if selection.get("doc_ids") != ["library"]:
            raise AssertionError(f"prepare should post the final checked document ids only: {prepare_body!r}")
        static_config_requests = [request for request in requests if "/data-sharing/config/" in request]
        if static_config_requests:
            raise AssertionError(f"routes still requested static Data Sharing config: {static_config_requests!r}")
        if console_errors:
            raise AssertionError(f"console errors: {console_errors}")
        if page_errors:
            raise AssertionError(f"page errors: {page_errors}")
        print(f"local Analytics Data Sharing routes OK: {base_url}/analytics/data-sharing/prepare/")
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
