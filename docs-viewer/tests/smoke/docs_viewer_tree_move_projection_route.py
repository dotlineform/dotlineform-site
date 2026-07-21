#!/usr/bin/env python3
"""Smoke-check committed tree move projection through the real manage route."""

from __future__ import annotations

import argparse
import json
from urllib.parse import urlparse

from playwright.sync_api import Page, Route, sync_playwright

from docs_viewer_service_manage import DOCS_VIEWER_DOC_ID, start_server, wait_for_manage_doc


def request_path(url: str) -> str:
    return urlparse(url).path


def choose_route_move(page: Page) -> dict[str, str]:
    return page.evaluate(
        """() => {
            const nav = document.querySelector('#docsViewerNav');
            const rootList = nav?.querySelector(':scope > .docsViewer__navList');
            const rootItems = rootList ? Array.from(rootList.children) : [];
            const records = rootItems.map((item) => {
                const row = item.querySelector(':scope > [data-doc-row-id]');
                const link = row?.querySelector('[data-drag-doc-id]');
                return {
                    item,
                    row,
                    link,
                    docId: row?.dataset.docRowId || '',
                    containsActive: Boolean(item.querySelector('.docsViewer__navLink.is-active'))
                };
            }).filter((record) => record.docId && record.link);
            const moving = records.find((record) => !record.containsActive);
            const target = records.find((record) => record.docId !== moving?.docId);
            const unrelated = records.find((record) => (
                record.docId !== moving?.docId && record.docId !== target?.docId
            ));
            if (!moving || !target || !unrelated) {
                throw new Error('route smoke requires three draggable root documents outside search mode');
            }

            window.__docsViewerTreeMoveRouteSmoke = {
                activeLink: nav.querySelector('.docsViewer__navLink.is-active'),
                displayedDocId: new URLSearchParams(window.location.search).get('doc') || '',
                displayedHeading: document.querySelector('#docsViewerContent h1')?.textContent.trim() || '',
                movingItem: moving.item,
                targetItem: target.item,
                unrelatedItem: unrelated.item,
                url: window.location.href
            };
            window.__docsViewerTreeMoveRouteMarker = 'mounted-before-move';
            return {
                movingDocId: moving.docId,
                targetDocId: target.docId,
                unrelatedDocId: unrelated.docId
            };
        }"""
    )


def dispatch_route_move(page: Page, move: dict[str, str]) -> None:
    page.evaluate(
        """move => {
            const nav = document.querySelector('#docsViewerNav');
            const movingLink = nav.querySelector(
                `[data-drag-doc-id="${CSS.escape(move.movingDocId)}"]`
            );
            const targetRow = nav.querySelector(
                `[data-doc-row-id="${CSS.escape(move.targetDocId)}"]`
            );
            if (!movingLink || !targetRow) throw new Error('route smoke move rows are not mounted');
            const dataTransfer = new DataTransfer();
            movingLink.dispatchEvent(new DragEvent('dragstart', {
                bubbles: true,
                cancelable: true,
                dataTransfer
            }));
            targetRow.dispatchEvent(new DragEvent('dragover', {
                bubbles: true,
                cancelable: true,
                dataTransfer
            }));
            targetRow.dispatchEvent(new DragEvent('drop', {
                bubbles: true,
                cancelable: true,
                dataTransfer
            }));
        }""",
        move,
    )


def establish_move_selection(page: Page, move: dict[str, str]) -> list[str]:
    selected_doc_ids = [move["movingDocId"], move["unrelatedDocId"]]
    page.locator('[data-docs-viewer-selection-command="enter"]').click()
    for doc_id in selected_doc_ids:
        page.locator(f'[data-docs-viewer-selection-checkbox="{doc_id}"]').click()
    page.evaluate(
        """detail => {
            const nav = document.querySelector('#docsViewerNav');
            const before = window.__docsViewerTreeMoveRouteSmoke;
            before.activeLink = nav.querySelector('.docsViewer__navLink.is-active');
            before.movingItem = nav.querySelector(
                `[data-doc-row-id="${CSS.escape(detail.move.movingDocId)}"]`
            ).closest('.docsViewer__navItem');
            before.targetItem = nav.querySelector(
                `[data-doc-row-id="${CSS.escape(detail.move.targetDocId)}"]`
            ).closest('.docsViewer__navItem');
            before.unrelatedItem = nav.querySelector(
                `[data-doc-row-id="${CSS.escape(detail.move.unrelatedDocId)}"]`
            ).closest('.docsViewer__navItem');
        }""",
        {"move": move},
    )
    return selected_doc_ids


def projected_route_state(page: Page, move: dict[str, str]) -> dict[str, object]:
    return page.evaluate(
        """move => {
            const nav = document.querySelector('#docsViewerNav');
            const before = window.__docsViewerTreeMoveRouteSmoke;
            const movingItem = nav.querySelector(
                `[data-doc-row-id="${CSS.escape(move.movingDocId)}"]`
            )?.closest('.docsViewer__navItem');
            const targetItem = nav.querySelector(
                `[data-doc-row-id="${CSS.escape(move.targetDocId)}"]`
            )?.closest('.docsViewer__navItem');
            const unrelatedItem = nav.querySelector(
                `[data-doc-row-id="${CSS.escape(move.unrelatedDocId)}"]`
            )?.closest('.docsViewer__navItem');
            const targetList = targetItem?.querySelector(':scope > .docsViewer__navList--child');
            const directTargetChildren = targetList ? Array.from(targetList.children) : [];
            const targetToggle = targetItem?.querySelector(
                `:scope > .docsViewer__navRow > [data-toggle-doc-id="${CSS.escape(move.targetDocId)}"]`
            );
            return {
                activeIdentityPreserved: nav.querySelector('.docsViewer__navLink.is-active') === before.activeLink,
                displayedDocId: new URLSearchParams(window.location.search).get('doc') || '',
                displayedHeading: document.querySelector('#docsViewerContent h1')?.textContent.trim() || '',
                marker: window.__docsViewerTreeMoveRouteMarker || '',
                movingIdentityPreserved: movingItem === before.movingItem,
                movingIsDirectTargetChild: directTargetChildren.includes(movingItem),
                targetExpanded: targetToggle?.getAttribute('aria-expanded') || '',
                targetIdentityPreserved: targetItem === before.targetItem,
                unrelatedIdentityPreserved: unrelatedItem === before.unrelatedItem,
                checkedDocIds: Array.from(nav.querySelectorAll(
                    '[data-docs-viewer-selection-checkbox]:checked'
                )).map(checkbox => checkbox.dataset.docsViewerSelectionCheckbox),
                selectionCount: document.querySelector(
                    '.docsViewer__indexSelectionCount'
                )?.textContent.trim() || '',
                url: window.location.href,
                beforeDisplayedDocId: before.displayedDocId,
                beforeDisplayedHeading: before.displayedHeading,
                beforeUrl: before.url
            };
        }""",
        move,
    )


def assert_real_manage_route_projection(page: Page, base_url: str, timeout_ms: int) -> None:
    index_requests: list[str] = []
    move_requests: list[dict[str, object]] = []
    page_errors: list[str] = []
    page.on(
        "request",
        lambda request: index_requests.append(request.url)
        if (
            request_path(request.url) == "/docs/index-tree"
            or request_path(request.url).endswith("/index-tree.json")
        )
        else None,
    )
    page.on("pageerror", lambda error: page_errors.append(error.stack or str(error)))

    def fulfill_move(route: Route) -> None:
        body = route.request.post_data_json
        move_requests.append(body)
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "ok": True,
                    "scope": body.get("scope"),
                    "doc_id": body.get("doc_id"),
                    "record": {
                        "doc_id": body.get("doc_id"),
                        "parent_id": body.get("parent_id"),
                    },
                    "changed_doc_ids": [body.get("doc_id")],
                    "summary_text": f"Moved {body.get('doc_id')}.",
                }
            ),
        )

    page.route("**/docs/move", fulfill_move)
    page.goto(f"{base_url}/docs/?scope=studio&doc={DOCS_VIEWER_DOC_ID}", wait_until="domcontentloaded")
    wait_for_manage_doc(page, "Docs Viewer", timeout_ms)
    move = choose_route_move(page)
    selected_doc_ids = establish_move_selection(page, move)
    index_count_before = len(index_requests)

    dispatch_route_move(page, move)
    page.wait_for_function(
        """move => {
            const nav = document.querySelector('#docsViewerNav');
            const movingItem = nav?.querySelector(
                `[data-doc-row-id="${CSS.escape(move.movingDocId)}"]`
            )?.closest('.docsViewer__navItem');
            const targetItem = nav?.querySelector(
                `[data-doc-row-id="${CSS.escape(move.targetDocId)}"]`
            )?.closest('.docsViewer__navItem');
            const targetList = targetItem?.querySelector(':scope > .docsViewer__navList--child');
            const root = document.querySelector('#docsViewerRoot');
            return movingItem && targetList && Array.from(targetList.children).includes(movingItem) &&
                root?.dataset.managementBusy !== 'true';
        }""",
        arg=move,
        timeout=timeout_ms,
    )

    state = projected_route_state(page, move)
    expected_request = {
        "scope": "studio",
        "doc_id": move["movingDocId"],
        "parent_id": move["targetDocId"],
    }
    if move_requests != [expected_request]:
        raise AssertionError(f"route move did not send one canonical request: {move_requests!r}")
    if len(index_requests) != index_count_before:
        raise AssertionError(f"successful route move re-read index-tree: {index_requests!r}")
    required_truthy = (
        "activeIdentityPreserved",
        "movingIdentityPreserved",
        "movingIsDirectTargetChild",
        "targetIdentityPreserved",
        "unrelatedIdentityPreserved",
    )
    if any(not state[key] for key in required_truthy):
        raise AssertionError(f"real route did not preserve local tree identity: {state!r}")
    if state["targetExpanded"] != "true":
        raise AssertionError(f"real route did not reveal the committed destination: {state!r}")
    if state["url"] != state["beforeUrl"] or state["displayedDocId"] != state["beforeDisplayedDocId"]:
        raise AssertionError(f"real route move changed the displayed route: {state!r}")
    if state["displayedHeading"] != state["beforeDisplayedHeading"]:
        raise AssertionError(f"real route move changed the displayed document: {state!r}")
    if sorted(state["checkedDocIds"]) != sorted(selected_doc_ids):
        raise AssertionError(f"successful local move changed the checked set: {state!r}")
    if state["selectionCount"] != "2 selected":
        raise AssertionError(f"successful local move changed selection mode or count: {state!r}")
    if state["marker"] != "mounted-before-move":
        raise AssertionError(f"real route move reloaded the browser: {state!r}")
    if page_errors:
        raise AssertionError(f"page errors during route move projection: {page_errors!r}")


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
                assert_real_manage_route_projection(page, base_url, args.timeout_ms)
            finally:
                browser.close()
        print("Docs Viewer real manage-route tree move projection OK")
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
