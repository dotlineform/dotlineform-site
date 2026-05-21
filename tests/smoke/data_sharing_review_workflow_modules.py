#!/usr/bin/env python3
"""Smoke-check Data Sharing review workflow JavaScript helpers."""

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


def assert_data_sharing_review_workflow(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            document.body.innerHTML = `
              <select id="scope"></select>
              <select id="file"><option value="returned.json">returned.json</option></select>
              <button id="preview"></button>
              <button id="actions" aria-expanded="false"></button>
              <div id="menu" hidden></div>
              <button id="resultButton" hidden></button>
              <button id="selectAll"></button>
              <button id="clear"></button>
              <p id="summary"></p>
              <ul id="list">
                <li data-data-sharing-review-preview="row-a"><input type="checkbox" value="row-a"></li>
                <li data-data-sharing-review-preview="tree-a"><input type="checkbox" value="tree-a"></li>
              </ul>
            `;
            const module = await import('/assets/studio/js/data-sharing-review-workflow.js');
            const applyActions = module.dataSharingReviewApplyActionsForCapability({
                apply_actions: [
                    {
                        id: 'apply_docs',
                        status: 'ACTIVE',
                        label: 'Apply documents',
                        title: 'Apply selected documents',
                        ui: {
                            selection_required_message: 'Pick at least one row.'
                        },
                        result: {
                            title: 'Apply result',
                            count_rows: [{ key: 'changed' }]
                        }
                    },
                    {
                        id: 'disabled_action',
                        status: 'disabled',
                        label: 'Disabled action'
                    }
                ]
            });
            const state = {
                config: {
                    ui_text: {
                        data_sharing_review: {
                            scope_library: 'library',
                            scope_tags: 'tags'
                        }
                    }
                },
                scope: 'library',
                workflowScopes: module.DATA_SHARING_REVIEW_SCOPES,
                applyActions,
                applyButtons: new Map(),
                files: [{ filename: 'returned.json' }],
                previewRows: [
                    { id: 'row-a', selectable: true, recordIndex: 0 },
                    { id: 'tree-a', selectable: false, recordIndex: null }
                ],
                selectedPreviewIds: new Set(),
                serviceAvailable: true,
                isRunning: false,
                scopeSelect: document.getElementById('scope'),
                fileSelect: document.getElementById('file'),
                previewButton: document.getElementById('preview'),
                actionMenuButton: document.getElementById('actions'),
                applyActionMenu: document.getElementById('menu'),
                resultButton: document.getElementById('resultButton'),
                selectAllButton: document.getElementById('selectAll'),
                clearButton: document.getElementById('clear'),
                selectionSummary: document.getElementById('summary'),
                listNode: document.getElementById('list'),
                lastImportResult: null
            };
            module.renderDataSharingReviewScopeSelect(state);
            module.renderDataSharingReviewApplyActions(state);
            module.setDataSharingReviewControlsDisabled(state, false);
            const beforeSelection = {
                actionMenuDisabled: state.actionMenuButton.disabled,
                firstActionDisabled: state.applyButtons.get('apply_docs').disabled,
                firstActionTitle: state.applyButtons.get('apply_docs').title
            };
            module.selectAllDataSharingReviewPreviewRows(state);
            const afterSelection = {
                selected: Array.from(state.selectedPreviewIds),
                checkboxA: state.listNode.querySelector('[value="row-a"]').checked,
                checkboxTree: state.listNode.querySelector('[value="tree-a"]').checked,
                summary: state.selectionSummary.textContent,
                actionMenuDisabled: state.actionMenuButton.disabled,
                firstActionDisabled: state.applyButtons.get('apply_docs').disabled,
                firstActionTitle: state.applyButtons.get('apply_docs').title
            };
            module.toggleDataSharingReviewApplyActionsMenu(state);
            const menuOpen = {
                hidden: state.applyActionMenu.hidden,
                expanded: state.actionMenuButton.getAttribute('aria-expanded'),
                minWidth: state.applyActionMenu.style.minWidth
            };
            module.hideDataSharingReviewApplyActionsMenu(state);
            const menuClosed = {
                hidden: state.applyActionMenu.hidden,
                expanded: state.actionMenuButton.getAttribute('aria-expanded')
            };
            module.clearDataSharingReviewPreviewSelection(state);
            state.lastImportResult = { summary: '2 previews generated.' };
            module.maybeShowDataSharingReviewResultButton(state, '2 previews generated.');
            const resultVisible = !state.resultButton.hidden;
            module.maybeShowDataSharingReviewResultButton(state, 'different summary');
            const resultHiddenAfterMismatch = state.resultButton.hidden;
            return {
                actionIds: applyActions.map((action) => action.id),
                actionStatuses: applyActions.map((action) => action.status),
                actionControlIds: applyActions.map((action) => action.controlId),
                actionResultRows: applyActions[0].countRows.length,
                scopeOptions: Array.from(state.scopeSelect.options).map((option) => `${option.value}:${option.textContent}:${option.selected}`),
                selectedFile: module.selectedDataSharingReviewFile(state).filename,
                beforeSelection,
                afterSelection,
                menuOpen,
                menuClosed,
                selectedAfterClear: Array.from(state.selectedPreviewIds),
                summaryAfterClear: state.selectionSummary.textContent,
                resultVisible,
                resultHiddenAfterMismatch,
                label: module.dataSharingReviewScopeLabel(state),
                title: module.dataSharingReviewScopeTitle(state),
                normalized: module.normalizeDataSharingReviewText('  tags  ')
            };
        }"""
    )
    assert result["actionIds"] == ["apply_docs", "disabled_action"]
    assert result["actionStatuses"] == ["active", "disabled"]
    assert result["actionControlIds"] == [
        "dataSharingReviewApplyAction1",
        "dataSharingReviewApplyAction2",
    ]
    assert result["actionResultRows"] == 1
    assert result["scopeOptions"] == ["library:library:true", "tags:tags:false"]
    assert result["selectedFile"] == "returned.json"
    assert result["beforeSelection"] == {
        "actionMenuDisabled": False,
        "firstActionDisabled": True,
        "firstActionTitle": "Pick at least one row.",
    }
    assert result["afterSelection"]["selected"] == ["row-a"]
    assert result["afterSelection"]["checkboxA"] is True
    assert result["afterSelection"]["checkboxTree"] is False
    assert result["afterSelection"]["summary"] == "1 preview selected."
    assert result["afterSelection"]["actionMenuDisabled"] is False
    assert result["afterSelection"]["firstActionDisabled"] is False
    assert result["afterSelection"]["firstActionTitle"] == "Apply selected documents"
    assert result["menuOpen"]["hidden"] is False
    assert result["menuOpen"]["expanded"] == "true"
    assert result["menuOpen"]["minWidth"] != ""
    assert result["menuClosed"] == {"hidden": True, "expanded": "false"}
    assert result["selectedAfterClear"] == []
    assert result["summaryAfterClear"] == "0 previews selected."
    assert result["resultVisible"] is True
    assert result["resultHiddenAfterMismatch"] is True
    assert result["label"] == "library"
    assert result["title"] == "Library"
    assert result["normalized"] == "tags"


def run(site_root: Path) -> None:
    server, base_url = start_static_server(site_root)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{base_url}/", wait_until="domcontentloaded")
            errors: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            assert_data_sharing_review_workflow(page)
            browser.close()
            if errors:
                raise AssertionError(f"page errors during Data Sharing review workflow smoke: {errors!r}")
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
