#!/usr/bin/env python3
"""Smoke-check the focused Missing Source Files report module."""

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
        page.goto(f"{base_url}/__docs_viewer_missing_source_files_smoke__.html", wait_until="domcontentloaded")
        result = page.evaluate(
            """async () => {
                const module = await import('/docs-viewer/runtime/js/reports/missing-source-files-report.js');
                const reportServiceModule = await import('/docs-viewer/runtime/js/reports/docs-viewer-report-service.js');
                const root = document.createElement('section');
                document.body.appendChild(root);
                let failRefresh = false;
                const service = {
                    runMissingSourceFiles: () => failRefresh
                        ? Promise.reject(new Error('fixture refresh failure'))
                        : Promise.resolve({
                            ok: true,
                            report: {
                                schema_version: 'docs_missing_source_files_report_v1',
                                rows: [
                                    {
                                        work_id: '00894',
                                        work_title: 'doll moiré reduced',
                                        expected_source_path: 'doll/doll moiré reduced.jpg'
                                    },
                                    {
                                        work_id: '01942',
                                        work_title: 'Missing nested source',
                                        expected_source_path: 'wa/ink/missing source.jpg'
                                    }
                                ]
                            }
                        })
                };
                await module.mountMissingSourceFilesReport({
                    reportRoot: root,
                    reportService: service,
                    studioBaseUrl: 'http://127.0.0.1:8765'
                });
                const initial = {
                    reportId: root.dataset.reportId,
                    columns: root.dataset.reportColumns,
                    headings: Array.from(root.querySelectorAll('.docsViewerReport__headLabel')).map(node => node.textContent),
                    rows: Array.from(root.querySelectorAll('.docsViewerReport__row')).map(row => ({
                        cells: Array.from(row.children).map(cell => cell.textContent),
                        links: Array.from(row.querySelectorAll('a')).map(link => ({ text: link.textContent, href: link.getAttribute('href') }))
                    })),
                    buttonLabels: Array.from(root.querySelectorAll('button')).map(button => button.getAttribute('aria-label')),
                    status: root.querySelector('.docsViewerReport__status').textContent,
                    text: root.textContent
                };

                failRefresh = true;
                root.querySelector('#docsMissingSourceFilesReportRun').click();
                await new Promise(resolve => setTimeout(resolve, 0));
                const failed = {
                    rowCount: root.querySelectorAll('.docsViewerReport__row').length,
                    status: root.querySelector('.docsViewerReport__status').textContent,
                    empty: root.querySelector('.docsViewerReport__empty').textContent,
                    emptyHidden: root.querySelector('.docsViewerReport__empty').hidden
                };

                let invalidMessage = '';
                try {
                    module.normalizeMissingSourceFilesResponse({
                        ok: true,
                        report: {
                            schema_version: 'docs_missing_source_files_report_v1',
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
                                schema_version: 'docs_missing_source_files_report_v1',
                                rows: []
                            }
                        })
                    });
                };
                const client = reportServiceModule.createDocsViewerReportService({
                    baseUrl: 'http://manage.local',
                    fetch
                });
                await client.runMissingSourceFiles();
                return { initial, failed, invalidMessage, requests };
            }"""
        )
        browser.close()

    assert result["initial"] == {
        "reportId": "missing_source_files",
        "columns": "3",
        "headings": ["Work ID", "Work title", "Expected source path"],
        "rows": [
            {
                "cells": ["00894", "doll moiré reduced", "doll/doll moiré reduced.jpg"],
                "links": [
                    {
                        "text": "00894",
                        "href": "http://127.0.0.1:8765/studio/catalogue-work/?work=00894",
                    }
                ],
            },
            {
                "cells": ["01942", "Missing nested source", "wa/ink/missing source.jpg"],
                "links": [
                    {
                        "text": "01942",
                        "href": "http://127.0.0.1:8765/studio/catalogue-work/?work=01942",
                    }
                ],
            },
        ],
        "buttonLabels": ["Run/Refresh"],
        "status": "",
        "text": (
            "🔄Work IDWork titleExpected source path"
            "00894doll moiré reduceddoll/doll moiré reduced.jpg"
            "01942Missing nested sourcewa/ink/missing source.jpg"
        ),
    }
    assert result["failed"] == {
        "rowCount": 0,
        "status": "fixture refresh failure",
        "empty": "The current Missing Source Files run could not complete.",
        "emptyHidden": False,
    }
    assert result["invalidMessage"] == "Missing Source Files report is invalid."
    assert result["requests"] == [
        {
            "url": "http://manage.local/docs/missing-source-files",
            "method": "POST",
            "body": "{}",
        }
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
    print("Docs Viewer Missing Source Files report modules OK")


if __name__ == "__main__":
    main()
