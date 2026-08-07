#!/usr/bin/env python3
"""Smoke-check the focused Uncataloged Files report module."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[3]


class QuietStaticHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A003
        return


def start_static_server(site_root: Path) -> tuple[ThreadingHTTPServer, str]:
    handler = partial(QuietStaticHandler, directory=str(site_root.resolve()))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def run_smoke(base_url: str) -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(base_url, wait_until="domcontentloaded")
        result = page.evaluate(
            """async () => {
                const module = await import('/docs-viewer/runtime/js/reports/uncataloged-files-report.js');
                const reportServiceModule = await import('/docs-viewer/runtime/js/reports/docs-viewer-report-service.js');
                const root = document.createElement('section');
                document.body.appendChild(root);
                const openedTargets = [];
                let failRefresh = false;
                const service = {
                    runUncatalogedFiles: () => failRefresh
                        ? Promise.reject(new Error('fixture refresh failure'))
                        : Promise.resolve({
                            ok: true,
                            report: {
                                schema_version: 'docs_uncataloged_files_report_v1',
                                rows: [
                                    {
                                        folder: 'alpha',
                                        file_name: 'notes.pdf',
                                        local_target: 'projects/alpha/notes.pdf'
                                    },
                                    {
                                        folder: 'wa/ink',
                                        file_name: 'working file.docx',
                                        local_target: 'projects/wa/ink/working%20file.docx'
                                    }
                                ]
                            }
                        }),
                    openLocalTarget: target => {
                        openedTargets.push(target);
                        return Promise.resolve({ ok: true });
                    }
                };
                await module.mountUncatalogedFilesReport({ reportRoot: root, reportService: service });
                const initial = {
                    reportId: root.dataset.reportId,
                    columns: root.dataset.reportColumns,
                    headings: Array.from(root.querySelectorAll('.docsViewerReport__headLabel')).map(node => node.textContent),
                    rows: Array.from(root.querySelectorAll('.docsViewerReport__row')).map(row => ({
                        cells: Array.from(row.children).map(cell => cell.textContent),
                        target: row.querySelector('[data-uncataloged-file-target]').dataset.uncatalogedFileTarget
                    })),
                    buttonLabels: Array.from(root.querySelectorAll('button')).map(button => button.getAttribute('aria-label')),
                    status: root.querySelector('.docsViewerReport__status').textContent,
                    text: root.textContent
                };

                root.querySelectorAll('[data-uncataloged-file-target]')[1].click();
                await new Promise(resolve => setTimeout(resolve, 0));

                failRefresh = true;
                root.querySelector('#docsUncatalogedFilesReportRun').click();
                await new Promise(resolve => setTimeout(resolve, 0));
                const failed = {
                    rowCount: root.querySelectorAll('.docsViewerReport__row').length,
                    status: root.querySelector('.docsViewerReport__status').textContent,
                    empty: root.querySelector('.docsViewerReport__empty').textContent,
                    emptyHidden: root.querySelector('.docsViewerReport__empty').hidden
                };

                let invalidMessage = '';
                try {
                    module.normalizeUncatalogedFilesResponse({
                        ok: true,
                        report: {
                            schema_version: 'docs_uncataloged_files_report_v1',
                            rows: [],
                            summary: { count: 0 }
                        }
                    });
                } catch (error) {
                    invalidMessage = error.message;
                }

                const requests = [];
                const fetch = (url, options) => {
                    requests.push({ url, method: options.method, body: options.body });
                    return Promise.resolve({
                        ok: true,
                        status: 200,
                        json: () => Promise.resolve({
                            ok: true,
                            report: {
                                schema_version: 'docs_uncataloged_files_report_v1',
                                rows: []
                            }
                        })
                    });
                };
                const client = reportServiceModule.createDocsViewerReportService({
                    baseUrl: 'http://manage.local',
                    fetch
                });
                await client.runUncatalogedFiles();
                await client.openLocalTarget('projects/alpha/notes.pdf');
                return { initial, openedTargets, failed, invalidMessage, requests };
            }"""
        )
        browser.close()

    assert result["initial"] == {
        "reportId": "uncataloged_files",
        "columns": "2",
        "headings": ["Folder", "File name"],
        "rows": [
            {
                "cells": ["alpha", "notes.pdf"],
                "target": "projects/alpha/notes.pdf",
            },
            {
                "cells": ["wa/ink", "working file.docx"],
                "target": "projects/wa/ink/working%20file.docx",
            },
        ],
        "buttonLabels": ["Run/Refresh"],
        "status": "",
        "text": "🔄FolderFile namealphanotes.pdfwa/inkworking file.docx",
    }
    assert result["openedTargets"] == ["projects/wa/ink/working%20file.docx"]
    assert result["failed"] == {
        "rowCount": 0,
        "status": "fixture refresh failure",
        "empty": "The current Uncataloged Files run could not complete.",
        "emptyHidden": False,
    }
    assert result["invalidMessage"] == "Uncataloged Files report is invalid."
    assert result["requests"] == [
        {
            "url": "http://manage.local/docs/uncataloged-files",
            "method": "POST",
            "body": "{}",
        },
        {
            "url": "http://manage.local/docs/open-local-target",
            "method": "POST",
            "body": '{"target":"projects/alpha/notes.pdf"}',
        },
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-root", default=str(REPO_ROOT))
    args = parser.parse_args()
    server, base_url = start_static_server(Path(args.site_root))
    try:
        run_smoke(base_url)
    finally:
        server.shutdown()
        server.server_close()
    print("Docs Viewer Uncataloged Files report modules OK")


if __name__ == "__main__":
    main()
