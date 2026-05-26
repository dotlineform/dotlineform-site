#!/usr/bin/env python3
"""Smoke-check local Studio Data Sharing route shells."""

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

from studio.app.server.studio.studio_app_server import StudioAppServer  # noqa: E402


def start_server() -> tuple[StudioAppServer, str]:
    server = StudioAppServer(("127.0.0.1", 0), REPO_ROOT)
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
                "doc_id": "library",
                "title": "Library",
                "published": True,
                "viewable": True,
                "content_text_length": 120,
                "summary": "Library root.",
            },
            {
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


def prepare_payload() -> dict[str, object]:
    return {
        "ok": True,
        "target_format": "json",
        "count_unit": "document",
        "counts": {
            "selected": 2,
            "exported": 2,
            "skipped": 0,
            "failed": 0,
            "truncated": 0,
        },
        "output_files": [
            "var/studio/data-sharing/library/exports/local-smoke.json",
        ],
        "warnings": [],
        "summary_text": "Package prepared.",
    }


def returned_packages_payload() -> dict[str, object]:
    return {
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


def review_payload() -> dict[str, object]:
    return {
        "ok": True,
        "scope": "library",
        "summary_text": "Generated 2 Library returned package review files.",
        "detected_import_type": "parent_child_relationships",
        "source_export_id": "library-parent-child-relationships",
        "generated_at": "2026-05-04T12:05:00Z",
        "counts": {
            "records": 2,
            "parsed_records": 2,
            "malformed_records": 0,
            "warnings": 0,
            "errors": 0,
        },
        "issues": [],
        "records": [],
        "preview_files": [],
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


def install_mock_data_sharing_api(page) -> list[dict[str, object]]:
    calls: list[dict[str, object]] = []

    def handle(route) -> None:
        request = route.request
        parsed = urlparse(request.url)
        data_sharing_paths = {
            "/studio/api/data-sharing/health",
            "/studio/api/data-sharing/selectable-records",
            "/studio/api/data-sharing/prepare",
            "/studio/api/data-sharing/returned-packages",
            "/studio/api/data-sharing/review",
        }
        if parsed.path not in data_sharing_paths:
            route.continue_()
            return
        calls.append({"method": request.method, "path": parsed.path})
        payload: dict[str, object]
        if parsed.path == "/studio/api/data-sharing/health":
            payload = {"ok": True, "service": "studio_data_sharing", "dry_run": False}
        elif parsed.path == "/studio/api/data-sharing/selectable-records":
            payload = selectable_records_payload()
        elif parsed.path == "/studio/api/data-sharing/prepare":
            payload = prepare_payload()
        elif parsed.path == "/studio/api/data-sharing/returned-packages":
            payload = returned_packages_payload()
        elif parsed.path == "/studio/api/data-sharing/review":
            payload = review_payload()
        else:
            payload = {"ok": False, "error": f"Unexpected Data Sharing API route: {parsed.path}"}
        route.fulfill(status=200, content_type="application/json", body=json.dumps(payload))

    page.route("**/*", handle)
    return calls


def assert_runtime_views(base_url: str) -> None:
    with urllib.request.urlopen(f"{base_url}/studio/runtime-config.json", timeout=10) as response:
        runtime_config = json.loads(response.read().decode("utf-8"))
    views = runtime_config.get("app", {}).get("runtime", {}).get("views", [])
    by_id = {view.get("id"): view for view in views if isinstance(view, dict)}
    expected = {
        "data_sharing_prepare": "/studio/data-sharing/prepare/?mode=manage",
        "data_sharing_review": "/studio/data-sharing/review/?mode=manage",
    }
    for view_id, path in expected.items():
        view = by_id.get(view_id)
        if not view or view.get("path") != path:
            raise AssertionError(f"runtime config missing {view_id}: {views!r}")
    if "data_sharing" in by_id:
        raise AssertionError(f"runtime config still exposes retired data sharing dashboard: {views!r}")
    services = runtime_config.get("app", {}).get("runtime", {}).get("services", {})
    data_sharing = services.get("data_sharing", {}) if isinstance(services, dict) else {}
    if data_sharing.get("health") != "/studio/api/data-sharing/health":
        raise AssertionError(f"runtime config missing Studio Data Sharing API endpoints: {data_sharing!r}")


def read_json_url(url: str) -> dict[str, object]:
    with urllib.request.urlopen(url, timeout=10) as response:
        if response.status != HTTPStatus.OK:
            raise AssertionError(f"unexpected status for {url}: {response.status}")
        return json.loads(response.read().decode("utf-8"))


def assert_data_sharing_api(base_url: str) -> None:
    health = read_json_url(f"{base_url}/studio/api/data-sharing/health")
    if health.get("service") != "studio_data_sharing":
        raise AssertionError(f"unexpected Data Sharing health payload: {health!r}")
    records = read_json_url(f"{base_url}/studio/api/data-sharing/selectable-records?data_domain=library")
    if records.get("adapter_id") != "documents" or records.get("selection_model") != "documents":
        raise AssertionError(f"unexpected selectable-record payload: {records!r}")
    if not records.get("records"):
        raise AssertionError(f"selectable-record payload is empty: {records!r}")


def assert_prepare(page, base_url: str) -> None:
    page.goto(f"{base_url}/studio/data-sharing/prepare/?mode=manage&scope=library", wait_until="domcontentloaded")
    root = page.locator("#dataSharingPrepareRoot")
    expect(root).to_be_visible(timeout=10_000)
    expect(root).to_have_attribute("data-studio-ready", "true", timeout=10_000)
    expect(root).to_have_attribute("data-studio-service", "available", timeout=10_000)
    expect(root).to_have_attribute("data-studio-record-loaded", "true", timeout=10_000)
    expect(page.locator("[data-data-sharing-prepare-doc]").first).to_be_visible(timeout=10_000)
    page.locator("#dataSharingPrepareSelectAll").click()
    page.locator("#dataSharingPrepareRun").click()
    expect(page.locator("[data-role='studio-modal']")).to_be_visible(timeout=10_000)
    title = page.locator("[data-role='studio-modal'] .tagStudioModal__title").first.inner_text(timeout=10_000)
    if title != "Package result":
        raise AssertionError(f"unexpected prepare modal title: {title!r}")


def assert_review(page, base_url: str) -> None:
    page.goto(f"{base_url}/studio/data-sharing/review/?mode=manage&scope=library", wait_until="domcontentloaded")
    root = page.locator("#dataSharingReviewRoot")
    expect(root).to_be_visible(timeout=10_000)
    expect(root).to_have_attribute("data-studio-ready", "true", timeout=10_000)
    expect(root).to_have_attribute("data-studio-service", "available", timeout=10_000)
    expect(root).to_have_attribute("data-studio-record-loaded", "true", timeout=10_000)
    page.locator("#dataSharingReviewRun").click()
    expect(page.locator("[data-data-sharing-review-preview]").first).to_be_visible(timeout=10_000)
    title = page.locator("[data-role='studio-modal'] .tagStudioModal__title").first.inner_text(timeout=10_000)
    if title != "Returned package review":
        raise AssertionError(f"unexpected review modal title: {title!r}")


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
            page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
            page.on("pageerror", lambda error: page_errors.append(str(error)))
            data_sharing_api_calls = install_mock_data_sharing_api(page)

            assert_prepare(page, base_url)
            assert_review(page, base_url)
            browser.close()

        required_paths = {
            "/studio/api/data-sharing/health",
            "/studio/api/data-sharing/selectable-records",
            "/studio/api/data-sharing/prepare",
            "/studio/api/data-sharing/returned-packages",
            "/studio/api/data-sharing/review",
        }
        seen_paths = {str(call["path"]) for call in data_sharing_api_calls}
        missing_paths = required_paths.difference(seen_paths)
        if missing_paths:
            raise AssertionError(f"missing Studio Data Sharing API calls: {sorted(missing_paths)!r}; calls={data_sharing_api_calls!r}")
        if "/docs/generated/index" in seen_paths:
            raise AssertionError(f"prepare page still read the generic generated docs index: {data_sharing_api_calls!r}")
        if console_errors:
            raise AssertionError(f"console errors: {console_errors}")
        if page_errors:
            raise AssertionError(f"page errors: {page_errors}")
        print(f"local Studio Data Sharing routes OK: {base_url}/studio/data-sharing/prepare/?mode=manage")
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
