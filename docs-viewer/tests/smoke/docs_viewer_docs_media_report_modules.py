#!/usr/bin/env python3
"""Smoke-check the focused Docs Media report module."""

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
        page.goto(base_url + "/?report_scope=dotlineform", wait_until="domcontentloaded")
        result = page.evaluate(
            """async () => {
                const reportModule = await import('/docs-viewer/runtime/js/reports/docs-media-report.js');
                const serviceModule = await import('/docs-viewer/runtime/js/reports/docs-viewer-report-service.js');
                const tick = () => new Promise(resolve => setTimeout(resolve, 0));
                const documentRecord = (title, docId, subScope = '') => ({
                    target: { scope: 'dotlineform', sub_scope: subScope, doc_id: docId },
                    title,
                    href: '/docs/?scope=dotlineform&doc=' + docId
                        + (subScope ? '&subdoc=' + subScope : '')
                });
                const row = (scope, mediaType, identity, documents = []) => ({
                    scope,
                    media_type: mediaType,
                    identity,
                    local_target: 'docs-viewer/media/' + scope + '/' + identity,
                    documents
                });
                const dotlineformRows = [
                    row('dotlineform', 'mermaid', 'maps/zeta.mmd'),
                    row('dotlineform', 'img', 'images/beta.webp', [
                        documentRecord('Alpha guide', 'd-alpha'),
                        documentRecord('Beta notes', 'd-beta', 'detail')
                    ]),
                    row('dotlineform', 'file', 'files/notes.pdf'),
                    row('dotlineform', 'img', 'images/alpha.webp', [
                        documentRecord('Alpha guide', 'd-alpha')
                    ])
                ];
                const payloadFor = scope => ({
                    ok: true,
                    dry_run: false,
                    summary_text: 'Docs Media refreshed.',
                    report: {
                        schema_version: 'docs_media_report_v1',
                        scope,
                        rows: scope === 'dotlineform'
                            ? dotlineformRows
                            : scope === 'analysis'
                                ? [row('analysis', 'file', 'reports/analysis.pdf')]
                                : []
                    }
                });
                const root = document.createElement('section');
                document.body.appendChild(root);
                const loadedScopes = [];
                const openedTargets = [];
                let failRefresh = false;
                const service = {
                    runDocsMedia: request => {
                        loadedScopes.push(request.scope);
                        return failRefresh
                            ? Promise.reject(new Error('fixture media failure'))
                            : Promise.resolve(payloadFor(request.scope));
                    },
                    openLocalTarget: target => {
                        openedTargets.push(target);
                        return Promise.resolve({ ok: true });
                    }
                };
                await reportModule.mountDocsMediaReport({
                    reportRoot: root,
                    reportService: service,
                    scopeConfigs: [
                        { scope_id: 'studio', title: 'Studio' },
                        { scope_id: 'dotlineform', title: 'Dotlineform' },
                        { scope_id: 'analysis', title: 'Analysis' }
                    ]
                });
                const readRows = () => Array.from(root.querySelectorAll('.docsViewerReport__row')).map(node => ({
                    type: node.dataset.docsMediaType,
                    identity: node.dataset.docsMediaIdentity,
                    documents: Array.from(node.querySelectorAll('[data-docs-viewer-doc-id]')).map(link => ({
                        title: link.textContent,
                        scope: link.dataset.docsViewerScope,
                        subScope: link.dataset.docsViewerSubscope,
                        docId: link.dataset.docsViewerDocId,
                        href: link.getAttribute('href')
                    }))
                }));
                const initial = {
                    reportId: root.dataset.reportId,
                    columns: root.dataset.reportColumns,
                    headings: Array.from(root.querySelectorAll('.docsViewerReport__sortButton')).map(
                        button => button.childNodes[0].textContent
                    ),
                    scopes: Array.from(root.querySelectorAll('#docsMediaReportScope option')).map(
                        option => [option.value, option.textContent]
                    ),
                    selectedScope: root.querySelector('#docsMediaReportScope').value,
                    status: root.querySelector('.docsViewerReport__status').textContent,
                    rows: readRows()
                };

                root.querySelector('[data-docs-media-target="docs-viewer/media/dotlineform/images/alpha.webp"]').click();
                await tick();

                const search = root.querySelector('#docsMediaReportSearch');
                search.value = 'Alpha guide';
                search.dispatchEvent(new Event('input', { bubbles: true }));
                const documentSearchRows = readRows().map(item => item.identity);
                search.value = 'img';
                search.dispatchEvent(new Event('input', { bubbles: true }));
                const typeSearch = {
                    rowCount: readRows().length,
                    empty: root.querySelector('.docsViewerReport__empty').textContent
                };
                root.querySelector('.docsViewerReport__searchClear').click();

                root.querySelector('[data-report-sort="file"]').click();
                root.querySelector('[data-report-sort="file"]').click();
                const fileDescending = readRows().map(item => item.identity);
                root.querySelector('[data-report-sort="documents"]').click();
                const documentsAscending = readRows().map(item => item.identity);
                root.querySelector('[data-report-sort="documents"]').click();
                const documentsDescending = readRows().map(item => item.identity);

                const scopeSelect = root.querySelector('#docsMediaReportScope');
                scopeSelect.value = 'analysis';
                scopeSelect.dispatchEvent(new Event('change', { bubbles: true }));
                await tick();
                search.value = 'analysis';
                search.dispatchEvent(new Event('input', { bubbles: true }));
                root.querySelector('[data-report-sort="file"]').click();
                root.querySelector('[data-report-sort="file"]').click();
                root.querySelector('#docsMediaReportRun').click();
                await tick();
                const refreshed = {
                    scope: scopeSelect.value,
                    search: search.value,
                    rows: readRows().map(item => item.identity),
                    route: window.location.search
                };

                scopeSelect.value = 'studio';
                scopeSelect.dispatchEvent(new Event('change', { bubbles: true }));
                await tick();
                const emptyScope = {
                    status: root.querySelector('.docsViewerReport__status').textContent,
                    empty: root.querySelector('.docsViewerReport__empty').textContent,
                    rowCount: readRows().length
                };

                failRefresh = true;
                root.querySelector('#docsMediaReportRun').click();
                await tick();
                const failed = {
                    status: root.querySelector('.docsViewerReport__status').textContent,
                    empty: root.querySelector('.docsViewerReport__empty').textContent,
                    rowCount: readRows().length
                };

                let invalidMessage = '';
                try {
                    reportModule.normalizeDocsMediaResponse({
                        ...payloadFor('dotlineform'),
                        extra: true
                    }, 'dotlineform');
                } catch (error) {
                    invalidMessage = error.message;
                }

                const requests = [];
                const fetch = (url, options) => {
                    requests.push({ url, method: options.method, body: options.body });
                    return Promise.resolve({
                        ok: true,
                        status: 200,
                        json: () => Promise.resolve(url.endsWith('/docs/media-report')
                            ? payloadFor('analysis')
                            : { ok: true })
                    });
                };
                const client = serviceModule.createDocsViewerReportService({
                    baseUrl: 'http://manage.local',
                    fetch
                });
                await client.runDocsMedia({ scope: 'analysis' });
                await client.openLocalTarget('docs-viewer/media/analysis/reports/analysis.pdf');
                return {
                    initial,
                    openedTargets,
                    documentSearchRows,
                    typeSearch,
                    fileDescending,
                    documentsAscending,
                    documentsDescending,
                    loadedScopes,
                    refreshed,
                    emptyScope,
                    failed,
                    invalidMessage,
                    requests
                };
            }"""
        )
        browser.close()

    assert result["initial"] == {
        "reportId": "docs_media",
        "columns": "3",
        "headings": ["Type", "File name", "Documents"],
        "scopes": [
            ["studio", "Studio"],
            ["dotlineform", "Dotlineform"],
            ["analysis", "Analysis"],
        ],
        "selectedScope": "dotlineform",
        "status": "4 media files in dotlineform.",
        "rows": [
            {"type": "file", "identity": "files/notes.pdf", "documents": []},
            {
                "type": "img",
                "identity": "images/alpha.webp",
                "documents": [
                    {
                        "title": "Alpha guide",
                        "scope": "dotlineform",
                        "subScope": "",
                        "docId": "d-alpha",
                        "href": "/docs/?scope=dotlineform&doc=d-alpha",
                    }
                ],
            },
            {
                "type": "img",
                "identity": "images/beta.webp",
                "documents": [
                    {
                        "title": "Alpha guide",
                        "scope": "dotlineform",
                        "subScope": "",
                        "docId": "d-alpha",
                        "href": "/docs/?scope=dotlineform&doc=d-alpha",
                    },
                    {
                        "title": "Beta notes",
                        "scope": "dotlineform",
                        "subScope": "detail",
                        "docId": "d-beta",
                        "href": "/docs/?scope=dotlineform&doc=d-beta&subdoc=detail",
                    },
                ],
            },
            {"type": "mermaid", "identity": "maps/zeta.mmd", "documents": []},
        ],
    }
    assert result["openedTargets"] == [
        "docs-viewer/media/dotlineform/images/alpha.webp"
    ]
    assert result["documentSearchRows"] == [
        "images/alpha.webp",
        "images/beta.webp",
    ]
    assert result["typeSearch"] == {
        "rowCount": 0,
        "empty": "No Docs Media rows match the current search.",
    }
    assert result["fileDescending"] == [
        "maps/zeta.mmd",
        "images/beta.webp",
        "images/alpha.webp",
        "files/notes.pdf",
    ]
    assert result["documentsAscending"] == [
        "images/alpha.webp",
        "images/beta.webp",
        "files/notes.pdf",
        "maps/zeta.mmd",
    ]
    assert result["documentsDescending"] == [
        "files/notes.pdf",
        "maps/zeta.mmd",
        "images/beta.webp",
        "images/alpha.webp",
    ]
    assert result["loadedScopes"] == [
        "dotlineform",
        "analysis",
        "analysis",
        "studio",
        "studio",
    ]
    assert result["refreshed"] == {
        "scope": "analysis",
        "search": "analysis",
        "rows": ["reports/analysis.pdf"],
        "route": "?report_scope=analysis&report_sort=file&report_dir=desc",
    }
    assert result["emptyScope"] == {
        "status": "0 media files in studio.",
        "empty": "No media files were found in studio.",
        "rowCount": 0,
    }
    assert result["failed"] == {
        "status": "fixture media failure",
        "empty": "The current Docs Media load could not complete.",
        "rowCount": 0,
    }
    assert result["invalidMessage"] == "Docs Media report is invalid."
    assert result["requests"] == [
        {
            "url": "http://manage.local/docs/media-report",
            "method": "POST",
            "body": '{"scope":"analysis"}',
        },
        {
            "url": "http://manage.local/docs/open-local-target",
            "method": "POST",
            "body": '{"target":"docs-viewer/media/analysis/reports/analysis.pdf"}',
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
    print("Docs Viewer Docs Media report modules OK")


if __name__ == "__main__":
    main()
