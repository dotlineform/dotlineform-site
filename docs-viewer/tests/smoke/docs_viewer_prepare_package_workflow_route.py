#!/usr/bin/env python3
"""Smoke-check Prepare package wiring on the real Docs Viewer manage route."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import tempfile
import time
from urllib.parse import urlparse

from playwright.sync_api import Page, Route, sync_playwright


PROJECTS_DIR = tempfile.TemporaryDirectory(prefix="docs-viewer-prepare-route-")
os.environ["DOTLINEFORM_PROJECTS_BASE_DIR"] = PROJECTS_DIR.name
(Path(PROJECTS_DIR.name) / "docs-viewer").mkdir()
(Path(PROJECTS_DIR.name) / "data-sharing").mkdir()

from docs_viewer_service_manage import DOCS_VIEWER_DOC_ID, start_server, wait_for_manage_doc


def select_one_document(page: Page, timeout_ms: int) -> str:
    page.locator('[data-docs-viewer-selection-command="enter"]').click()
    doc_id = page.evaluate(
        """() => {
            const checkbox = Array.from(document.querySelectorAll(
                '[data-docs-viewer-selection-checkbox]'
            )).find(node => {
                const gutter = node.closest('[data-docs-viewer-selection-gutter]');
                return gutter && !gutter.hidden && !node.disabled;
            });
            return checkbox?.dataset.docsViewerSelectionCheckbox || '';
        }"""
    )
    if not doc_id:
        raise AssertionError("Prepare route smoke could not find an eligible index document")
    page.locator(f'[data-docs-viewer-selection-checkbox="{doc_id}"]').click()
    page.wait_for_function(
        """expectedId => {
            const prepare = document.querySelector('#docsViewerManagePreparePackageButton');
            const checkbox = document.querySelector(
                `[data-docs-viewer-selection-checkbox="${CSS.escape(expectedId)}"]`
            );
            return checkbox?.checked === true && prepare && !prepare.disabled;
        }""",
        arg=doc_id,
        timeout=timeout_ms,
    )
    return str(doc_id)


def install_busy_observer(page: Page) -> None:
    page.evaluate(
        """() => {
            const root = document.querySelector('#docsViewerRoot');
            window.__prepareBusyStates = [root?.dataset.managementBusy || ''];
            window.__prepareBusyObserver?.disconnect();
            window.__prepareBusyObserver = new MutationObserver(() => {
                window.__prepareBusyStates.push(root?.dataset.managementBusy || '');
            });
            window.__prepareBusyObserver.observe(root, {
                attributes: true,
                attributeFilter: ['data-management-busy']
            });
        }"""
    )


def exercise_prepare_action(page: Page, base_url: str, timeout_ms: int) -> None:
    prepare_requests: list[dict[str, object]] = []
    requested_paths: list[str] = []
    page.on("request", lambda request: requested_paths.append(urlparse(request.url).path))

    def fulfill_prepare(route: Route) -> None:
        request = route.request
        prepare_requests.append(
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
                    "summary_text": "Prepared package with 1 document(s).",
                    "counts": {"selected": 1, "exported": 1, "failed": 0},
                    "output_file": "$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/exports/smoke.jsonl",
                    "metadata_file": "$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/meta/smoke.meta.json",
                    "output_written": True,
                }
            ),
        )

    page.route("**/docs/packages/prepare", fulfill_prepare)
    page.goto(
        f"{base_url}/docs/?scope=studio&doc={DOCS_VIEWER_DOC_ID}",
        wait_until="domcontentloaded",
    )
    wait_for_manage_doc(page, "Docs Viewer", timeout_ms)
    selected_doc_id = select_one_document(page, timeout_ms)

    page.locator("#docsViewerManageActionsButton").click()
    prepare_button = page.locator("#docsViewerManagePreparePackageButton")
    prepare_button.wait_for(state="visible", timeout=timeout_ms)
    if prepare_button.get_attribute("href") is not None:
        raise AssertionError("Prepare package remained route navigation instead of an Action")
    prepare_button.click()

    page.wait_for_selector(
        '[data-role="docs-viewer-management-modal"] h2:text("Prepare package")',
        timeout=timeout_ms,
    )
    option_modal = page.locator('[data-role="docs-viewer-management-modal"]')
    if option_modal.locator("[data-docs-viewer-selection-checkbox]").count():
        raise AssertionError("Prepare modal rendered a second document selection")
    if option_modal.locator('input[type="checkbox"]').count() != 3:
        raise AssertionError("Prepare modal should contain descendants and both content filters")
    if option_modal.locator("[data-package-missing-summary-only]").is_checked():
        raise AssertionError("missing-summary filter should default off")
    if not option_modal.locator("[data-package-include-non-viewable]").is_checked():
        raise AssertionError("non-viewable inclusion should default on")
    option_modal.locator("[data-package-include-descendants]").uncheck()

    install_busy_observer(page)
    option_modal.locator('[data-role="modal-primary"]').click()
    page.wait_for_selector(
        '[data-role="docs-viewer-management-modal"] h2:text("Document package prepared")',
        timeout=timeout_ms,
    )

    result_text = page.locator('[data-role="docs-viewer-management-modal"]').inner_text()
    state = page.locator("#docsViewerRoot").evaluate(
        """root => ({
            ready: root.dataset.docsViewerReady || '',
            managementBusy: root.dataset.managementBusy || '',
            busyStates: window.__prepareBusyStates || [],
            selectionMode: Boolean(document.querySelector(
                '[data-docs-viewer-selection-command="done"]'
            )),
            checkedDocIds: Array.from(document.querySelectorAll(
                '[data-docs-viewer-selection-checkbox]:checked'
            )).map(node => node.dataset.docsViewerSelectionCheckbox)
        })"""
    )
    page.locator('[data-role="modal-primary"]').click()

    if len(prepare_requests) != 1:
        raise AssertionError(f"Prepare Action issued unexpected requests: {prepare_requests!r}")
    request = prepare_requests[0]
    body = request.get("body") if isinstance(request.get("body"), dict) else {}
    if request.get("method") != "POST" or request.get("path") != "/docs/packages/prepare":
        raise AssertionError(f"Prepare Action used the wrong endpoint: {request!r}")
    if body.get("scope") != "studio" or body.get("doc_ids") != [selected_doc_id]:
        raise AssertionError(f"Prepare Action did not submit the checked Studio document: {body!r}")
    if body.get("select_all") is not False or body.get("dry_run") is not False:
        raise AssertionError(f"Prepare Action changed the package request contract: {body!r}")
    activity = body.get("activity_context") if isinstance(body.get("activity_context"), dict) else {}
    if (
        activity.get("page_id") != "docs-manage"
        or activity.get("action_id") != "prepare-document-package"
        or activity.get("control_id") != "docsViewerManagePreparePackageButton"
    ):
        raise AssertionError(f"Prepare Action activity attribution is incorrect: {activity!r}")
    for expected_path in ("/docs/packages/config", "/docs/packages/documents", "/docs/packages/prepare"):
        if expected_path not in requested_paths:
            raise AssertionError(f"Prepare workflow omitted {expected_path}: {requested_paths!r}")
    if "true" not in state["busyStates"] or state["managementBusy"] == "true":
        raise AssertionError(f"Prepare Action did not project and clear management busy state: {state!r}")
    if state["ready"] != "true" or state["checkedDocIds"] != [selected_doc_id] or not state["selectionMode"]:
        raise AssertionError(f"Prepare Action changed ready or selection state: {state!r}")
    if "Prepared package with 1 document(s)." not in result_text or "smoke.jsonl" not in result_text:
        raise AssertionError(f"Prepare result omitted service detail: {result_text!r}")


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
                exercise_prepare_action(page, base_url, args.timeout_ms)
            finally:
                browser.close()
        if page_errors:
            raise AssertionError(f"page errors during Prepare route smoke: {page_errors!r}")
    finally:
        server.shutdown()
        server.server_close()
        PROJECTS_DIR.cleanup()
    print("Docs Viewer real manage-route Prepare package workflow OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
