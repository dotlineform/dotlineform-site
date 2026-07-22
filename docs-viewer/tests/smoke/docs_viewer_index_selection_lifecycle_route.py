#!/usr/bin/env python3
"""Smoke-check manage-index selection reload and lifecycle behavior on the real route."""

from __future__ import annotations

import argparse
import json
from urllib.parse import urlparse

from playwright.sync_api import Page, Route, sync_playwright

from docs_viewer_service_manage import DOCS_VIEWER_DOC_ID, start_server, wait_for_manage_doc


def request_path(url: str) -> str:
    return urlparse(url).path


def click_selection_command(page: Page, command: str) -> None:
    page.locator(f'[data-docs-viewer-selection-command="{command}"]').click()


def checked_doc_ids(page: Page) -> list[str]:
    return page.locator("[data-docs-viewer-selection-checkbox]:checked").evaluate_all(
        "checkboxes => checkboxes.map(checkbox => checkbox.dataset.docsViewerSelectionCheckbox)"
    )


def nested_index_doc_ids(records: list[dict[str, object]]) -> list[str]:
    doc_ids: list[str] = []
    for record in records:
        doc_id = str(record.get("doc_id") or "").strip()
        if doc_id:
            doc_ids.append(doc_id)
        children = record.get("children")
        if isinstance(children, list):
            doc_ids.extend(
                nested_index_doc_ids([child for child in children if isinstance(child, dict)])
            )
    return doc_ids


def choose_selection_docs(page: Page) -> dict[str, str]:
    result = page.evaluate(
        """() => {
            const nav = document.querySelector('#docsViewerNav');
            const activeDocId = nav?.querySelector('.docsViewer__navLink.is-active')?.dataset.docId || '';
            const records = Array.from(nav?.querySelectorAll('[data-docs-viewer-selection-checkbox]') || [])
                .filter(checkbox => {
                    const gutter = checkbox.closest('[data-docs-viewer-selection-gutter]');
                    return gutter && !gutter.hidden && !checkbox.disabled;
                })
                .map(checkbox => {
                    const item = checkbox.closest('.docsViewer__navItem');
                    return {
                        docId: checkbox.dataset.docsViewerSelectionCheckbox || '',
                        leaf: !item?.querySelector(':scope > .docsViewer__navList--child')
                    };
                })
                .filter(record => record.docId && record.docId !== activeDocId);
            const pruned = records.find(record => record.leaf);
            const preserved = records.find(record => record.docId !== pruned?.docId);
            const shiftTarget = records.slice().reverse().find(record => (
                record.docId !== pruned?.docId && record.docId !== preserved?.docId
            ));
            if (!pruned || !preserved || !shiftTarget) {
                throw new Error('selection lifecycle route smoke requires three visible non-active documents');
            }
            return {
                preservedDocId: preserved.docId,
                prunedDocId: pruned.docId,
                shiftTargetDocId: shiftTarget.docId
            };
        }"""
    )
    return {key: str(value) for key, value in result.items()}


def click_checkbox(page: Page, doc_id: str, *, shift: bool = False) -> None:
    selector = f'[data-docs-viewer-selection-checkbox="{doc_id}"]'
    if shift:
        page.locator(selector).click(modifiers=["Shift"])
    else:
        page.locator(selector).click()


def assert_selection_lifecycle(page: Page, base_url: str, timeout_ms: int) -> None:
    index_request_count = 0
    initial_index_docs: list[dict[str, object]] = []
    prune_doc_id = ""
    prune_reloads = False
    page_errors: list[str] = []
    page.on("pageerror", lambda error: page_errors.append(error.stack or str(error)))

    def fulfill_index(route: Route) -> None:
        nonlocal index_request_count, initial_index_docs
        index_request_count += 1
        response = route.fetch()
        payload = response.json()
        if not initial_index_docs:
            initial_index_docs = [
                dict(record) for record in payload.get("docs", []) if isinstance(record, dict)
            ]
        if prune_reloads and prune_doc_id:
            payload["docs"] = [
                record
                for record in payload.get("docs", [])
                if record.get("doc_id") != prune_doc_id
            ]
        route.fulfill(response=response, json=payload)

    def fulfill_rebuild(route: Route) -> None:
        nonlocal prune_reloads
        prune_reloads = True
        body = route.request.post_data_json or {}
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({"ok": True, "scope": body.get("scope")}),
        )

    page.route("**/docs/index-tree*", fulfill_index)
    page.route("**/docs/rebuild", fulfill_rebuild)
    page.goto(f"{base_url}/docs/?scope=studio&doc={DOCS_VIEWER_DOC_ID}", wait_until="domcontentloaded")
    wait_for_manage_doc(page, "Docs Viewer", timeout_ms)

    if page.locator('[data-docs-viewer-control="manage-show-non-viewable"]').count():
        raise AssertionError("manage route retained the Show non-viewable control")
    if page.locator("#docsViewerDraftToggle").count():
        raise AssertionError("manage route retained the Show non-viewable input")
    if not initial_index_docs:
        raise AssertionError("manage route did not load the canonical index population")
    click_selection_command(page, "enter")
    click_selection_command(page, "select-all")
    selection_projection = page.evaluate(
        """() => ({
            count: document.querySelector('.docsViewer__indexSelectionCount')?.textContent.trim(),
            selectAllDisabled: document.querySelector(
                '[data-docs-viewer-selection-command="select-all"]'
            )?.disabled
        })"""
    )
    canonical_doc_ids = nested_index_doc_ids(initial_index_docs)
    expected_selection_count = f"{len(set(canonical_doc_ids))} selected"
    if selection_projection != {
        "count": expected_selection_count,
        "selectAllDisabled": True,
    }:
        raise AssertionError(
            "Select all did not project the complete manage-index population: "
            f"expected {expected_selection_count!r}, got {selection_projection!r}"
        )
    if page.locator("[data-docs-viewer-selection-checkbox]:not(:checked)").count():
        raise AssertionError("Select all left a rendered manage-index row unchecked")
    click_selection_command(page, "clear")
    selection_docs = choose_selection_docs(page)
    prune_doc_id = selection_docs["prunedDocId"]
    click_checkbox(page, selection_docs["preservedDocId"])
    click_checkbox(page, prune_doc_id)
    selected_before_navigation = [selection_docs["preservedDocId"], prune_doc_id]
    if sorted(checked_doc_ids(page)) != sorted(selected_before_navigation):
        raise AssertionError("route smoke did not establish the checked set before reload")

    page.locator("#docsViewerRecentButton").click()
    page.wait_for_function(
        "document.querySelector('#docsViewerRecentButton')?.getAttribute('aria-pressed') === 'true'",
        timeout=timeout_ms,
    )
    if sorted(checked_doc_ids(page)) != sorted(selected_before_navigation):
        raise AssertionError("Recent mode changed the checked set")

    search_input = page.locator("#docsViewerSearchInput")
    search_input.fill("selection lifecycle")
    page.wait_for_function(
        "new URLSearchParams(window.location.search).get('q') === 'selection lifecycle'",
        timeout=timeout_ms,
    )
    if sorted(checked_doc_ids(page)) != sorted(selected_before_navigation):
        raise AssertionError("Search mode changed the checked set")
    search_input.fill("")
    page.wait_for_function(
        "!new URLSearchParams(window.location.search).has('q')",
        timeout=timeout_ms,
    )

    requests_before_reload = index_request_count
    page.locator("#docsViewerManageRebuildButton").evaluate("button => button.click()")
    page.wait_for_function(
        """expectedId => {
            const root = document.querySelector('#docsViewerRoot');
            const output = document.querySelector('.docsViewer__indexSelectionCount');
            const checked = Array.from(document.querySelectorAll(
                '[data-docs-viewer-selection-checkbox]:checked'
            )).map(checkbox => checkbox.dataset.docsViewerSelectionCheckbox);
            return root?.dataset.managementBusy !== 'true'
                && output?.textContent.trim() === '1 selected'
                && checked.length === 1
                && checked[0] === expectedId;
        }""",
        arg=selection_docs["preservedDocId"],
        timeout=timeout_ms,
    )
    if index_request_count != requests_before_reload + 1:
        raise AssertionError(f"rebuild did not perform one index replacement: {index_request_count}")
    if page.locator(f'[data-docs-viewer-selection-checkbox="{prune_doc_id}"]').count():
        raise AssertionError("missing document remained in the refreshed manage index")

    click_checkbox(page, selection_docs["shiftTargetDocId"], shift=True)
    expected_after_missing_anchor = [
        selection_docs["preservedDocId"],
        selection_docs["shiftTargetDocId"],
    ]
    if sorted(checked_doc_ids(page)) != sorted(expected_after_missing_anchor):
        raise AssertionError(
            "Shift-click after anchor pruning did not behave as an ordinary toggle: "
            f"{checked_doc_ids(page)!r}"
        )

    page.locator("#docsViewerIndexViewToggle").click()
    page.wait_for_function(
        "document.querySelector('#docsViewerRoot')?.dataset.indexPanelView === 'index-graph'",
        timeout=timeout_ms,
    )
    page.locator("#docsViewerIndexViewToggle").click()
    page.wait_for_function(
        """() => document.querySelector('#docsViewerRoot')?.dataset.indexPanelView === 'index-tree'
            && Boolean(document.querySelector('[data-docs-viewer-selection-command="enter"]'))""",
        timeout=timeout_ms,
    )
    if checked_doc_ids(page):
        raise AssertionError("leaving the owning index view did not clear selection")

    click_selection_command(page, "enter")
    click_checkbox(page, selection_docs["preservedDocId"])
    page.reload(wait_until="domcontentloaded")
    wait_for_manage_doc(page, "Docs Viewer", timeout_ms)
    if page.locator('[data-docs-viewer-selection-command="enter"]').count() != 1:
        raise AssertionError("full browser reload did not return with selection mode off")
    if checked_doc_ids(page):
        raise AssertionError("full browser reload persisted checked ids")
    visible_gutters = page.locator(
        "[data-docs-viewer-selection-gutter]:not([hidden])"
    ).count()
    if visible_gutters:
        raise AssertionError("full browser reload persisted the selection gutter state")
    if page_errors:
        raise AssertionError(f"page errors during selection lifecycle route smoke: {page_errors!r}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout-ms", type=int, default=15000)
    args = parser.parse_args(argv)

    server, base_url = start_server()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                assert_selection_lifecycle(page, base_url, args.timeout_ms)
            finally:
                browser.close()
        print("Docs Viewer real manage-route index selection lifecycle OK")
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
