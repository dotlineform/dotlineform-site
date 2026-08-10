#!/usr/bin/env python3
"""Smoke-check the focused browser-composed Works report module."""

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
        page.goto(f"{base_url}/__docs_viewer_works_smoke__.html", wait_until="domcontentloaded")
        result = page.evaluate(
            """async () => {
                const module = await import('/docs-viewer/runtime/js/reports/works-report.js');
                const seriesItems = [
                    { series_id: '026', title: 'Alpha', series_type: 'primary', status: 'published', primary_work_id: '00008' },
                    { series_id: '105', title: 'Alpha', series_type: 'primary', status: 'published', primary_work_id: '00008' },
                    { series_id: '001', title: 'Blank', series_type: 'primary', status: 'published', primary_work_id: '00010' },
                    { series_id: '009', title: 'Series coverage', series_type: 'primary', status: 'published', primary_work_id: '' },
                    { series_id: '999', title: 'Draft Series', series_type: 'primary', status: 'draft', primary_work_id: '' }
                ];
                const workItems = [
                    { work_id: '00008', title: 'Shared Work', year_display: '1990', status: 'published', series_ids: ['105', '026'] },
                    { work_id: '00009', title: 'Second Work', year_display: '1991', status: 'published', series_ids: ['026'] },
                    { work_id: '00010', title: 'Undocumented Work', year_display: '1992', status: 'published', series_ids: ['001'] },
                    { work_id: '00011', title: 'Draft Work', year_display: '1993', status: 'draft', series_ids: ['001'] },
                    { work_id: '00012', title: 'Draft-Series Work', year_display: '1994', status: 'published', series_ids: ['999'] },
                    { work_id: '00013', title: 'Unknown-Series Work', year_display: '1995', status: 'published', series_ids: ['777'] }
                ];
                const subject = (kind, key) => ({
                    state: 'valid', kind, key,
                    fields: [{ folder: 'folder_path', work: 'work_id', series: 'series_id' }[kind]]
                });
                const record = (docId, title, authoringSubject) => ({
                    doc_id: docId,
                    title,
                    ui_status: '',
                    last_updated: '2026-08-10 15:03:46',
                    authoring_subject: authoringSubject
                });
                const projectDocs = [
                    {
                        ...record('d-20260801-010101-a1b2c3', 'A work note', subject('work', '00008')),
                        customisation: { publication_targets: [] }
                    },
                    record('d-20260801-010102-b2c3d4', 'B work note', subject('work', '00009')),
                    record('d-20260801-010103-c3d4e5', 'Series note', subject('series', '026')),
                    record('d-20260801-010104-d4e5f6', 'Other Series note', subject('series', '009')),
                    record('d-20260801-010105-e5f6a7', 'Draft Work note', subject('work', '00011')),
                    record('d-20260801-010106-f6a7b8', 'Draft Series note', subject('series', '999')),
                    record('d-20260801-010107-a7b8c9', 'Unknown Work note', subject('work', '09999')),
                    record('d-20260801-010108-b8c9d0', 'Unknown Series note', subject('series', '777')),
                    record('d-20260801-010109-c9d0e1', 'Folder note', subject('folder', 'projects/alpha')),
                    record('d-20260801-010110-d0e1f2', 'No subject', {
                        state: 'none', kind: 'none', key: '', fields: []
                    }),
                    record('d-20260801-010111-e1f2a3', 'Malformed subject', {
                        state: 'malformed', kind: 'work', key: '', fields: ['work_id'],
                        evidence: { work_id: 8 }
                    })
                ];
                const seriesPayload = {
                    header: { schema: 'studio_catalogue_lookup_series_search_v1', count: seriesItems.length },
                    items: seriesItems
                };
                const workPayload = {
                    header: { schema: 'studio_catalogue_lookup_work_search_v1', count: workItems.length },
                    items: workItems
                };
                const manifestPayload = {
                    customisation: { id: 'dotlineform_projects', data: {} },
                    docs: projectDocs,
                    subject_generation: 'sha256:fixture'
                };
                let phase = 'success';
                const requests = [];
                window.fetch = (url, options) => {
                    const requestUrl = String(url);
                    requests.push({
                        url: requestUrl,
                        cache: options.cache,
                        accept: options.headers.Accept,
                        phase
                    });
                    if (phase === 'fail-work' && requestUrl.includes('catalogue_lookup_work_search')) {
                        return Promise.reject(new Error('fixture Work failure'));
                    }
                    let payload = manifestPayload;
                    if (requestUrl.includes('catalogue_lookup_series_search')) payload = seriesPayload;
                    if (requestUrl.includes('catalogue_lookup_work_search')) payload = workPayload;
                    if (phase === 'empty-docs' && requestUrl === '/projects/manage-manifest.json') {
                        payload = { ...manifestPayload, docs: [] };
                    }
                    return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(payload) });
                };
                const viewerCalls = [];
                const root = document.createElement('section');
                document.body.appendChild(root);
                await module.mountWorksReport({
                    reportRoot: root,
                    scopeConfigs: [{
                        scopeId: 'dotlineform',
                        subScopes: [{ subScope: 'projects', manifestUrl: '/projects/manage-manifest.json' }]
                    }],
                    studioBaseUrl: 'http://127.0.0.1:8765',
                    publicPreviewBase: 'http://127.0.0.1:4000',
                    viewerUrlForScope: (scope, docId, options) => {
                        viewerCalls.push({ scope, docId, options });
                        return `/docs/?scope=${scope}&doc=${docId}`;
                    }
                });
                const initial = {
                    reportId: root.dataset.reportId,
                    columns: root.dataset.reportColumns,
                    headings: Array.from(root.querySelectorAll('.docsViewerReport__headLabel')).map(node => node.textContent),
                    status: root.querySelector('.docsViewerReport__status').textContent,
                    rowIds: Array.from(root.querySelectorAll('.docsViewerReport__row')).map(row => row.dataset.seriesId),
                    rows: Array.from(root.querySelectorAll('.docsViewerReport__row')).map(row => ({
                        seriesHref: row.querySelector(':scope > a').getAttribute('href'),
                        docLinks: Array.from(row.querySelectorAll('[data-project-doc-id]')).map(link => ({
                            docId: link.dataset.projectDocId,
                            href: link.getAttribute('href'),
                            kind: link.dataset.projectSubjectKind,
                            key: link.dataset.projectSubjectKey,
                            icon: link.querySelector('[data-project-subject-icon]')?.dataset.projectSubjectIcon,
                            text: link.textContent
                        })),
                        blankLabel: row.children[1].getAttribute('aria-label')
                    }))
                };
                const duplicateProjection = module.composeWorksProjection(
                    [{ seriesId: '026', title: 'Alpha', status: 'published' }],
                    [{ workId: '00008', title: 'Shared', status: 'published', seriesIds: ['026', '026'] }],
                    [{
                        docId: 'd-20260801-010101-a1b2c3', title: 'A work note',
                        subject: { state: 'valid', kind: 'work', key: '00008', fields: ['work_id'] }
                    }]
                );
                const invalidMessages = [];
                try {
                    module.normalizeWorksSeriesLookup({ ...seriesPayload, header: { ...seriesPayload.header, count: 99 } });
                } catch (error) { invalidMessages.push(error.message); }
                try {
                    module.normalizeWorksWorkLookup({
                        header: { schema: 'studio_catalogue_lookup_work_search_v1', count: 1 },
                        items: [{ ...workItems[0], series_ids: ['026', '026'] }]
                    });
                } catch (error) { invalidMessages.push(error.message); }
                try {
                    module.normalizeWorksProjectsManifest({
                        ...manifestPayload,
                        docs: [{ ...projectDocs[0], viewer_url: '/inferred' }]
                    });
                } catch (error) { invalidMessages.push(error.message); }
                try {
                    module.normalizeWorksProjectsManifest({
                        ...manifestPayload,
                        docs: [{ ...projectDocs[0], customisation: [] }]
                    });
                } catch (error) { invalidMessages.push(error.message); }

                phase = 'fail-work';
                root.querySelector('#docsWorksReportRefresh').click();
                const clearedImmediately = root.querySelectorAll('.docsViewerReport__row').length;
                await new Promise(resolve => setTimeout(resolve, 0));
                const failed = {
                    rowCount: root.querySelectorAll('.docsViewerReport__row').length,
                    status: root.querySelector('.docsViewerReport__status').textContent,
                    empty: root.querySelector('.docsViewerReport__empty').textContent,
                    emptyHidden: root.querySelector('.docsViewerReport__empty').hidden
                };

                phase = 'empty-docs';
                root.querySelector('#docsWorksReportRefresh').click();
                await new Promise(resolve => setTimeout(resolve, 0));
                const refreshed = {
                    rowCount: root.querySelectorAll('.docsViewerReport__row').length,
                    documentCount: root.querySelectorAll('[data-project-doc-id]').length,
                    blankCount: root.querySelectorAll('[aria-label="No Project documents"]').length,
                    status: root.querySelector('.docsViewerReport__status').textContent
                };
                return {
                    initial,
                    duplicateDocumentCount: duplicateProjection.rows[0].documents.length,
                    invalidMessages,
                    clearedImmediately,
                    failed,
                    refreshed,
                    requests,
                    viewerCalls
                };
            }"""
        )
        browser.close()

    assert result["initial"]["reportId"] == "works"
    assert result["initial"]["columns"] == "2"
    assert result["initial"]["headings"] == ["Series", "Docs"]
    assert result["initial"]["status"] == "4 published Series"
    assert result["initial"]["rowIds"] == ["026", "105", "001", "009"]

    rows = result["initial"]["rows"]
    assert rows[0]["seriesHref"] == "http://127.0.0.1:4000/series/?series=026"
    assert [(row["docId"], row["kind"], row["key"], row["icon"]) for row in rows[0]["docLinks"]] == [
        ("d-20260801-010101-a1b2c3", "work", "00008", "work"),
        ("d-20260801-010102-b2c3d4", "work", "00009", "work"),
        ("d-20260801-010103-c3d4e5", "series", "026", "series"),
    ]
    assert rows[1]["docLinks"][0]["docId"] == "d-20260801-010101-a1b2c3"
    assert rows[2]["docLinks"] == []
    assert rows[2]["blankLabel"] == "No Project documents"
    assert rows[3]["docLinks"][0]["docId"] == "d-20260801-010104-d4e5f6"
    assert rows[0]["docLinks"][0]["href"] == (
        "/docs/?scope=dotlineform&doc=d-20260801-073826-8865a8"
        "&subdoc=d-20260801-010101-a1b2c3"
    )

    assert result["duplicateDocumentCount"] == 1
    assert result["invalidMessages"] == [
        "Works Series lookup is invalid.",
        "Works Work lookup is invalid.",
        "Works Projects manifest is invalid.",
        "Works Projects manifest is invalid.",
    ]
    assert result["clearedImmediately"] == 0
    assert result["failed"] == {
        "rowCount": 0,
        "status": "fixture Work failure",
        "empty": "The current Works report could not complete.",
        "emptyHidden": False,
    }
    assert result["refreshed"] == {
        "rowCount": 4,
        "documentCount": 0,
        "blankCount": 4,
        "status": "4 published Series",
    }

    expected_urls = [
        "http://127.0.0.1:8765/studio/api/catalogue/read?key=catalogue_lookup_series_search",
        "http://127.0.0.1:8765/studio/api/catalogue/read?key=catalogue_lookup_work_search",
        "/projects/manage-manifest.json",
    ]
    assert [request["url"] for request in result["requests"]] == expected_urls * 3
    assert all(request["cache"] == "no-store" for request in result["requests"])
    assert all(request["accept"] == "application/json" for request in result["requests"])
    assert len(result["viewerCalls"]) == 5
    assert all(call == {
        "scope": "dotlineform",
        "docId": "d-20260801-073826-8865a8",
        "options": {"manage": True},
    } for call in result["viewerCalls"])


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
    print("Docs Viewer Works report modules OK")


if __name__ == "__main__":
    main()
