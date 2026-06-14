#!/usr/bin/env python3
"""Smoke-check the shared Record List JavaScript component contract."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import Page, sync_playwright


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


def assert_shared_record_list_contract(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            document.body.innerHTML = `
              <div id="recordListSmoke"></div>
              <div id="recordListActionsSmoke"></div>
            `;
            const module = await import('/shared/frontend/js/record-list.js');
            const root = document.getElementById('recordListSmoke');
            const actionsRoot = document.getElementById('recordListActionsSmoke');
            const selectionEvents = [];
            const actionEvents = [];
            const list = module.createRecordList(root, {
                id: 'recordListSmoke',
                records: [
                    { id: 'pdf', filename: 'nerve.pdf', href: 'https://example.com/nerve.pdf' },
                    { id: 'unsafe', filename: 'unsafe.pdf', href: 'javascript:alert(1)' }
                ],
                selectionMode: 'single',
                columns: [
                    { key: 'filename', label: 'filename', truncate: true },
                    { key: 'href', label: 'url', type: 'link', truncate: true }
                ],
                onSelectionChange: ({ selection }) => {
                    selectionEvents.push(selection ? { id: selection.id, index: selection.index } : null);
                }
            });
            const actions = module.createRecordListActions(actionsRoot, {
                id: 'recordListActionsSmoke',
                list,
                actions: [
                    { key: 'add', label: 'Add', requiresSelection: false },
                    { key: 'view', label: 'View' },
                    { key: 'delete', label: 'Delete', tone: 'danger' }
                ],
                onAction: ({ actionKey, selection, records }) => {
                    actionEvents.push({
                        actionKey,
                        selectionId: selection ? selection.id : '',
                        selectionIndex: selection ? selection.index : -1,
                        recordCount: records.length
                    });
                }
            });

            const initialDisabled = Array.from(actionsRoot.querySelectorAll('[data-record-list-action]')).map((button) => ({
                key: button.dataset.recordListAction,
                disabled: button.disabled,
                text: button.textContent
            }));

            root.querySelector('[data-record-list-record-id="pdf"]').click();
            const afterSelectionDisabled = Array.from(actionsRoot.querySelectorAll('[data-record-list-action]')).map((button) => ({
                key: button.dataset.recordListAction,
                disabled: button.disabled
            }));
            actionsRoot.querySelector('[data-record-list-action="view"]').click();

            const safeLink = root.querySelector('a[href="https://example.com/nerve.pdf"]');
            const unsafeLink = Array.from(root.querySelectorAll('[data-record-list-row="true"]'))[1].querySelector('a');
            const state = {
                actionEvents,
                afterSelectionDisabled,
                headerLabels: Array.from(root.querySelectorAll('[data-record-list-header]')).map((node) => node.textContent),
                initialDisabled,
                role: root.getAttribute('role'),
                rowCount: root.querySelectorAll('[data-record-list-row="true"]').length,
                safeLinkRel: safeLink ? safeLink.getAttribute('rel') : '',
                safeLinkTarget: safeLink ? safeLink.getAttribute('target') : '',
                selectedId: root.dataset.recordListSelectedId,
                selectionEvents,
                unsafeLinkRendered: Boolean(unsafeLink)
            };
            actions.destroy();
            list.destroy();
            state.destroyed = {
                listChildren: root.children.length,
                actionsChildren: actionsRoot.children.length
            };
            return state;
        }"""
    )
    assert result["role"] == "grid"
    assert result["rowCount"] == 2
    assert result["headerLabels"] == ["filename", "url"]
    assert result["safeLinkTarget"] == "_blank"
    assert result["safeLinkRel"] == "noopener noreferrer"
    assert result["unsafeLinkRendered"] is False
    assert result["initialDisabled"] == [
        {"key": "add", "disabled": False, "text": "Add"},
        {"key": "view", "disabled": True, "text": "View"},
        {"key": "delete", "disabled": True, "text": "Delete"},
    ]
    assert result["selectedId"] == "pdf"
    assert result["selectionEvents"] == [{"id": "pdf", "index": 0}]
    assert result["afterSelectionDisabled"] == [
        {"key": "add", "disabled": False},
        {"key": "view", "disabled": False},
        {"key": "delete", "disabled": False},
    ]
    assert result["actionEvents"] == [
        {"actionKey": "view", "selectionId": "pdf", "selectionIndex": 0, "recordCount": 2}
    ]
    assert result["destroyed"] == {"listChildren": 0, "actionsChildren": 0}


def run(site_root: Path) -> None:
    server, base_url = start_static_server(site_root)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{base_url}/", wait_until="domcontentloaded")
            assert_shared_record_list_contract(page)
            browser.close()
    finally:
        server.shutdown()
        server.server_close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-root", default=".", help="Site root to serve for module imports.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run(Path(args.site_root))


if __name__ == "__main__":
    main()
