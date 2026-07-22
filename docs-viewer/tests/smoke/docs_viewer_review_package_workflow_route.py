#!/usr/bin/env python3
"""Smoke-check Review package wiring on the real Docs Viewer manage route."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import tempfile
import time
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import Page, Route, sync_playwright


PROJECTS_DIR = tempfile.TemporaryDirectory(prefix="docs-viewer-review-route-")
os.environ["DOTLINEFORM_PROJECTS_BASE_DIR"] = PROJECTS_DIR.name
(Path(PROJECTS_DIR.name) / "docs-viewer").mkdir()
(Path(PROJECTS_DIR.name) / "data-sharing").mkdir()

from docs_viewer_service_manage import DOCS_VIEWER_DOC_ID, start_server, wait_for_manage_doc


REVIEW_WORKFLOW_PATH = "/docs-viewer/runtime/js/packages/document-package-review-workflow.js"
REVIEW_PACKAGE_ID = "20260722-204025-documents-document-content"


def install_busy_observer(page: Page) -> None:
    page.evaluate(
        """() => {
            const root = document.querySelector('#docsViewerRoot');
            window.__reviewBusyStates = [root?.dataset.managementBusy || ''];
            window.__reviewBusyObserver?.disconnect();
            window.__reviewBusyObserver = new MutationObserver(() => {
                window.__reviewBusyStates.push(root?.dataset.managementBusy || '');
            });
            window.__reviewBusyObserver.observe(root, {
                attributes: true,
                attributeFilter: ['data-management-busy']
            });
        }"""
    )


def exercise_review_action(page: Page, base_url: str, timeout_ms: int) -> None:
    review_requests: list[dict[str, object]] = []
    requested_paths: list[str] = []
    page.on("request", lambda request: requested_paths.append(urlparse(request.url).path))

    def fulfill_config(route: Route) -> None:
        time.sleep(0.05)
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "ok": True,
                    "workspace": {"available": True, "message": ""},
                    "scopes": [{"scope": "studio", "label": "Studio"}],
                }
            ),
        )

    def fulfill_returned(route: Route) -> None:
        time.sleep(0.05)
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "ok": True,
                    "scope": "studio",
                    "files": [
                        {
                            "filename": "reviewable.jsonl",
                            "document_count": 2,
                            "supports_return_import": True,
                        },
                        {
                            "filename": "tree.json",
                            "document_count": 3,
                            "supports_return_import": False,
                        },
                    ],
                    "blocked_files": [{"filename": "blocked.jsonl"}],
                    "unassigned_files": [{"filename": "orphan.jsonl"}],
                }
            ),
        )

    def fulfill_review(route: Route) -> None:
        request = route.request
        review_requests.append(
            {
                "method": request.method,
                "path": urlparse(request.url).path,
                "body": request.post_data_json,
            }
        )
        time.sleep(0.05)
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "ok": True,
                    "review_package_id": REVIEW_PACKAGE_ID,
                    "review_url": f"/docs-review/?package={REVIEW_PACKAGE_ID}",
                    "review_existing": False,
                    "counts": {"records": 2, "valid_records": 2, "errors": 0, "warnings": 0},
                    "issues": [],
                    "summary_text": f"Prepared Docs Review package {REVIEW_PACKAGE_ID}.",
                }
            ),
        )

    page.route("**/docs/packages/config", fulfill_config)
    page.route(
        re.compile(r".*/docs/packages/returned(?:\?.*)?$"),
        fulfill_returned,
    )
    page.route("**/docs/packages/returned/review", fulfill_review)
    page.goto(
        f"{base_url}/docs/?scope=studio&doc={DOCS_VIEWER_DOC_ID}",
        wait_until="domcontentloaded",
    )
    wait_for_manage_doc(page, "Docs Viewer", timeout_ms)

    if REVIEW_WORKFLOW_PATH in requested_paths:
        raise AssertionError("Review package workflow loaded before its Action was invoked")

    install_busy_observer(page)
    page.locator("#docsViewerManageActionsButton").click()
    review_button = page.locator("#docsViewerManageReviewPackageButton")
    review_button.wait_for(state="visible", timeout=timeout_ms)
    if review_button.is_disabled() or review_button.get_attribute("href") is not None:
        raise AssertionError("Review package is not an enabled manage Action")
    review_button.click()

    page.wait_for_selector(
        '[data-role="docs-viewer-management-modal"] h2:text("Review package")',
        timeout=timeout_ms,
    )
    if REVIEW_WORKFLOW_PATH not in requested_paths:
        raise AssertionError("Review package Action did not lazily load its workflow module")
    modal = page.locator('[data-role="docs-viewer-management-modal"]')
    if modal.locator("th").all_text_contents() != ["File name", "Documents"]:
        raise AssertionError("Review package modal changed its accepted columns")
    rows = modal.locator("tbody tr")
    if rows.count() != 1 or "reviewable.jsonl" not in rows.first.inner_text():
        raise AssertionError("Review package modal did not project only the reviewable package")
    selected = modal.locator('input[name="docsViewerReviewPackage"]:checked')
    if selected.count() != 1 or selected.get_attribute("value") != "reviewable.jsonl":
        raise AssertionError("Review package modal did not select one whole package")

    modal.locator('[data-role="modal-primary"]').click()
    page.wait_for_selector(
        '[data-role="docs-viewer-management-modal"] h2:text("Review package prepared")',
        timeout=timeout_ms,
    )
    result_modal = page.locator('[data-role="docs-viewer-management-modal"]')
    result_link = result_modal.locator(".docsViewerReviewPackage__resultLink a")
    expected_review_path = f"/docs-review/?package={REVIEW_PACKAGE_ID}"
    if (
        result_link.inner_text() != "Open in Docs Review"
        or result_link.get_attribute("href") != expected_review_path
        or result_link.get_attribute("target") != "_blank"
        or result_link.get_attribute("rel") != "noopener noreferrer"
    ):
        raise AssertionError("Review package result changed its safe new-tab link contract")

    state = page.locator("#docsViewerRoot").evaluate(
        """root => ({
            ready: root.dataset.docsViewerReady || '',
            managementBusy: root.dataset.managementBusy || '',
            busyStates: window.__reviewBusyStates || []
        })"""
    )
    if "true" not in state["busyStates"] or state["managementBusy"] == "true":
        raise AssertionError(f"Review package did not project and clear busy state: {state!r}")
    if state["ready"] != "true":
        raise AssertionError(f"Review package changed the manage-route ready state: {state!r}")

    if len(review_requests) != 1:
        raise AssertionError(f"Review package issued unexpected review requests: {review_requests!r}")
    request = review_requests[0]
    body = request.get("body") if isinstance(request.get("body"), dict) else {}
    if request.get("method") != "POST" or request.get("path") != "/docs/packages/returned/review":
        raise AssertionError(f"Review package used the wrong endpoint: {request!r}")
    if body != {
        "scope": "studio",
        "staged_filename": "reviewable.jsonl",
        "dry_run": False,
    }:
        raise AssertionError(f"Review package changed its whole-package request: {body!r}")
    for expected_path in (
        "/docs/packages/config",
        "/docs/packages/returned",
        "/docs/packages/returned/review",
    ):
        if expected_path not in requested_paths:
            raise AssertionError(f"Review package omitted {expected_path}: {requested_paths!r}")
    for retired_path in (
        "/docs/packages/returned/",
        "/docs/packages/returned/inspect",
        "/docs/packages/returned/apply",
    ):
        if retired_path in requested_paths:
            raise AssertionError(f"Review package requested retired path {retired_path}")

    with page.expect_popup(timeout=timeout_ms) as popup_info:
        result_link.click()
    popup = popup_info.value
    popup.wait_for_load_state("domcontentloaded", timeout=timeout_ms)
    popup_url = urlparse(popup.url)
    popup_package = (parse_qs(popup_url.query).get("package") or [""])[0]
    if popup_url.path != "/docs-review/" or popup_package != REVIEW_PACKAGE_ID:
        raise AssertionError(f"Review package opened the wrong new-tab URL: {popup.url}")
    popup.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout-ms", type=int, default=15000)
    args = parser.parse_args(argv)

    server, base_url = start_server()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page_errors: list[str] = []
            try:
                page = browser.new_page()
                page.on("pageerror", lambda error: page_errors.append(str(error)))
                exercise_review_action(page, base_url, args.timeout_ms)
            finally:
                browser.close()
        if page_errors:
            raise AssertionError(f"page errors during Review package route smoke: {page_errors!r}")
    finally:
        server.shutdown()
        server.server_close()
        PROJECTS_DIR.cleanup()
    print("Docs Viewer real manage-route Review package workflow OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
