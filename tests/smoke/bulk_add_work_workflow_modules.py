#!/usr/bin/env python3
"""Smoke-check Bulk Add Work workflow JavaScript helpers."""

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


def assert_bulk_add_work_workflow(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            document.body.innerHTML = `
              <button id="preview"></button>
              <button id="apply"></button>
              <div id="summary"></div>
              <div id="details"></div>
              <p id="status"></p>
              <p id="warning"></p>
              <p id="result"></p>
            `;
            const module = await import('/assets/studio/js/bulk-add-work-workflow.js');
            const state = {
                mode: 'works',
                workbookPath: 'data/works_bulk_import.xlsx',
                serverAvailable: true,
                isBusy: false,
                preview: {
                    mode: 'works',
                    ready_to_apply: true,
                    workbook_path: 'data/sample_bulk_import.xlsx',
                    summary: {
                        candidate_rows: 4,
                        importable_count: 2,
                        duplicate_count: 1,
                        blocked_count: 1
                    },
                    importable_ids: ['00001', '00002'],
                    duplicates: {
                        sample_ids: ['00003']
                    },
                    blocked: {
                        count: 1,
                        reason_counts: {
                            missing_title: 1
                        },
                        rows: [
                            { id: 'draft-1', message: 'Missing title' }
                        ],
                        validation_errors: ['Bad row']
                    }
                },
                previewButton: document.getElementById('preview'),
                applyButton: document.getElementById('apply'),
                summaryNode: document.getElementById('summary'),
                previewDetailsNode: document.getElementById('details'),
                statusNode: document.getElementById('status'),
                warningNode: document.getElementById('warning'),
                resultNode: document.getElementById('result')
            };
            const textOptions = {
                text(key, fallback, tokens) {
                    if (!tokens) return fallback;
                    return Object.entries(tokens).reduce(
                        (value, [token, replacement]) => value.replace(`{${token}}`, replacement),
                        fallback
                    );
                }
            };
            const runState = module.applyBulkAddWorkRunState(state);
            module.renderBulkAddWorkPreviewState(state, textOptions);
            const previewProjection = module.projectBulkAddWorkPreviewSuccess(state, state.preview, textOptions);
            module.applyBulkAddWorkStatusProjection(state, previewProjection);
            const applyProjection = module.projectBulkAddWorkApplySuccess(state, {
                imported_count: 2,
                duplicate_count: 1
            }, textOptions);
            module.applyBulkAddWorkStatusProjection(state, applyProjection);
            state.preview.mode = 'work_details';
            const blockedProjection = module.projectBulkAddWorkApplyBlocked(state, textOptions);
            module.applyBulkAddWorkRunState(state);
            return {
                runState,
                canApplyBeforeModeMismatch: module.canApplyBulkAddWorkPreview({
                    ...state,
                    preview: { ...state.preview, mode: 'works' }
                }),
                summaryText: state.summaryNode.textContent,
                detailsText: state.previewDetailsNode.textContent,
                statusText: state.statusNode.textContent,
                statusState: state.statusNode.dataset.state,
                warningText: state.warningNode.textContent,
                warningState: state.warningNode.dataset.state,
                resultText: state.resultNode.textContent,
                resultState: state.resultNode.dataset.state,
                blockedProjection,
                applyDisabledAfterModeMismatch: state.applyButton.disabled,
                normalized: module.normalizeBulkAddWorkText('  works  '),
                workbookPath: module.bulkAddWorkWorkbookPath(state, state.preview)
            };
        }"""
    )
    assert result["runState"]["preview"]["disabled"] is False
    assert result["runState"]["apply"]["disabled"] is False
    assert result["canApplyBeforeModeMismatch"] is True
    assert "data/sample_bulk_import.xlsx" in result["summaryText"]
    assert "2" in result["summaryText"]
    assert "missing_title" in result["detailsText"]
    assert "draft-1" in result["detailsText"]
    assert "Missing title" in result["detailsText"]
    assert "Bad row" in result["detailsText"]
    assert result["statusText"] == "Workbook import completed."
    assert result["statusState"] == "success"
    assert result["warningText"] == (
        "Clear the imported rows from data/sample_bulk_import.xlsx after you confirm the result."
    )
    assert result["warningState"] == "warn"
    assert result["resultText"] == "Imported 2 record(s); 1 duplicate record(s) already existed."
    assert result["resultState"] == "success"
    assert result["blockedProjection"] == {
        "status": {
            "state": "error",
            "text": "Run preview for the current mode before apply.",
        }
    }
    assert result["applyDisabledAfterModeMismatch"] is True
    assert result["normalized"] == "works"
    assert result["workbookPath"] == "data/sample_bulk_import.xlsx"


def run(site_root: Path) -> None:
    server, base_url = start_static_server(site_root)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{base_url}/", wait_until="domcontentloaded")
            errors: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            assert_bulk_add_work_workflow(page)
            browser.close()
            if errors:
                raise AssertionError(f"page errors during bulk add work workflow smoke: {errors!r}")
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
