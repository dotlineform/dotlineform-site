#!/usr/bin/env python3
"""Browser smoke for the local Catalogue Works report module."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import sync_playwright


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
        page.goto(
            f"{base_url}/__docs_viewer_catalogue_works_smoke__.html",
            wait_until="domcontentloaded",
        )
        result = page.evaluate(
            """async () => {
                const module = await import('/docs-viewer/runtime/js/reports/catalogue-works-report.js');
                const worksPayload = {
                    header: { schema: 'catalogue_source_works_v1', count: 4 },
                    works: {
                        '00008': {
                            work_id: '00008', title: 'Shared Work', year: 1990,
                            year_display: '1990–1995', status: 'published',
                            series_ids: ['105', '026'], storage_location: 'Shelf 1',
                            medium_type: 'drawing', medium_caption: 'pencil on paper'
                        },
                        '00009': {
                            work_id: '00009', title: 'Second Work', year: 2001,
                            year_display: '2001', status: 'published', series_ids: ['001'],
                            storage_location: 'Shelf 2', medium_type: 'painting',
                            medium_caption: 'acrylic on canvas'
                        },
                        '00010': {
                            work_id: '00010', title: 'Alphabet Study', year: 1985,
                            year_display: '1985', status: 'published', series_ids: [],
                            storage_location: null, medium_type: null, medium_caption: null
                        },
                        '00011': {
                            work_id: '00011', title: 'Draft Work', year: 2002,
                            year_display: '2002', status: 'draft', series_ids: ['001'],
                            storage_location: null, medium_type: 'print',
                            medium_caption: 'ink on paper'
                        }
                    }
                };
                const seriesPayload = {
                    header: { schema: 'catalogue_source_series_v1', count: 3 },
                    series: {
                        '001': { series_id: '001', title: 'Beta', status: 'published' },
                        '026': { series_id: '026', title: 'Collected', status: 'published' },
                        '105': { series_id: '105', title: 'Alpha', status: 'published' }
                    }
                };
                const requests = [];
                let phase = 'success';
                window.fetch = (url, options) => {
                    const requestUrl = String(url);
                    requests.push({
                        accept: options.headers.Accept,
                        cache: options.cache,
                        url: requestUrl
                    });
                    let payload = seriesPayload;
                    if (requestUrl.includes('key=catalogue_works')) payload = worksPayload;
                    if (requestUrl.includes('key=catalogue_series')) payload = seriesPayload;
                    if (phase === 'invalid' && requestUrl.includes('key=catalogue_works')) {
                        payload = { ...worksPayload, header: { ...worksPayload.header, count: 99 } };
                    }
                    return Promise.resolve({ ok: true, json: () => Promise.resolve(payload) });
                };
                const copied = [];
                Object.defineProperty(window.navigator, 'clipboard', {
                    configurable: true,
                    value: { writeText: (text) => { copied.push(text); return Promise.resolve(); } }
                });
                const root = document.createElement('section');
                document.body.appendChild(root);
                const mountResult = await module.mountCatalogueWorksReport({
                    reportRoot: root,
                    studioBaseUrl: 'http://127.0.0.1:8765',
                    publicPreviewBase: 'http://127.0.0.1:4000',
                    window
                });
                let refreshCount = 0;
                const unsubscribe = mountResult.expandedPresentation.subscribe(() => {
                    refreshCount += 1;
                });
                const initial = {
                    copyDisabled: root.querySelector('#docsCatalogueWorksReportCopy').disabled,
                    prompt: root.querySelector('.docsViewerReport__empty').textContent,
                    reportId: root.dataset.reportId,
                    presentation: root.dataset.reportPresentation,
                    rowCount: root.querySelectorAll('tbody tr').length,
                    status: root.querySelector('.docsViewerReport__status').textContent,
                    tableHidden: root.querySelector('table').hidden,
                    tableTag: root.querySelector('table').tagName,
                    headTag: root.querySelector('thead').tagName,
                    bodyTag: root.querySelector('tbody').tagName,
                    headings: Array.from(root.querySelectorAll('th')).map((node) => node.textContent.trim()),
                    presentationColumns: mountResult.expandedPresentation.columns,
                    presentationKind: mountResult.expandedPresentation.kind,
                    presentationTableExact: mountResult.expandedPresentation.table === root.querySelector('table'),
                    sortableCount: root.querySelectorAll('[data-report-sort]').length
                };

                const search = root.querySelector('#docsCatalogueWorksReportSearch');
                search.value = 'shared';
                search.dispatchEvent(new Event('input', { bubbles: true }));
                const plural = {
                    workId: root.querySelector('tbody tr').dataset.workId,
                    workHref: root.querySelector('tbody td a').getAttribute('href'),
                    titleHref: root.querySelector('tbody td:nth-child(3) a').getAttribute('href'),
                    series: Array.from(root.querySelectorAll('[data-series-id]')).map((link) => ({
                        id: link.dataset.seriesId,
                        href: link.getAttribute('href'),
                        text: link.textContent
                    })),
                    status: root.querySelector('.docsViewerReport__status').textContent,
                    mediumType: root.querySelector('tbody td:nth-child(6)').textContent,
                    mediumCaption: root.querySelector('tbody td:nth-child(7)').textContent,
                    columnIds: Array.from(root.querySelectorAll('tbody td')).map((cell) => cell.dataset.reportColumnId),
                    visibility: Array.from(root.querySelectorAll('tbody td')).map((cell) => cell.dataset.reportColumnVisibility)
                };

                search.value = '0';
                search.dispatchEvent(new Event('input', { bubbles: true }));
                root.querySelector('[data-report-sort="year"]').click();
                const yearAscending = {
                    ariaSort: root.querySelector('[data-report-sort="year"]').closest('th').getAttribute('aria-sort'),
                    rowIds: Array.from(root.querySelectorAll('tbody tr')).map((row) => row.dataset.workId)
                };
                root.querySelector('[data-report-sort="year"]').click();
                const yearDescending = {
                    ariaSort: root.querySelector('[data-report-sort="year"]').closest('th').getAttribute('aria-sort'),
                    rowIds: Array.from(root.querySelectorAll('tbody tr')).map((row) => row.dataset.workId)
                };
                root.querySelector('#docsCatalogueWorksReportCopy').click();
                await new Promise((resolve) => setTimeout(resolve, 0));
                const expandedViewport = document.createElement('div');
                expandedViewport.className = 'docsViewerReport__expandedViewport';
                expandedViewport.appendChild(root);
                document.body.appendChild(expandedViewport);
                root.querySelector('#docsCatalogueWorksReportCopy').click();
                await new Promise((resolve) => setTimeout(resolve, 0));

                root.querySelector('#docsCatalogueWorksReportClear').click();
                const cleared = {
                    rowCount: root.querySelectorAll('tbody tr').length,
                    prompt: root.querySelector('.docsViewerReport__empty').textContent,
                    tableHidden: root.querySelector('table').hidden
                };

                const pureRows = module.normalizeCatalogueWorksInputs(worksPayload, seriesPayload);
                const seriesSearch = module.buildCatalogueWorksProjection(pureRows, {
                    searchText: 'collected', sortKey: 'work', sortDir: 'asc'
                });
                const hiddenMediumSearch = module.buildCatalogueWorksProjection(pureRows, {
                    searchText: 'pencil', sortKey: 'work', sortDir: 'asc'
                });
                const invalidMessages = [];
                try {
                    module.normalizeCatalogueWorksInputs(
                        {
                            ...worksPayload,
                            works: {
                                ...worksPayload.works,
                                '00008': { ...worksPayload.works['00008'], series_ids: ['105', '105'] }
                            }
                        },
                        seriesPayload
                    );
                } catch (error) { invalidMessages.push(error.message); }
                try {
                    module.normalizeCatalogueWorksInputs(
                        {
                            ...worksPayload,
                            works: {
                                ...worksPayload.works,
                                '00010': { ...worksPayload.works['00010'], medium_caption: 2 }
                            }
                        },
                        seriesPayload
                    );
                } catch (error) { invalidMessages.push(error.message); }

                unsubscribe();
                try {
                    module.normalizeCatalogueWorksInputs(
                        {
                            ...worksPayload,
                            works: {
                                ...worksPayload.works,
                                '00009': { ...worksPayload.works['00009'], storage_location: 2 }
                            }
                        },
                        seriesPayload
                    );
                } catch (error) { invalidMessages.push(error.message); }

                phase = 'invalid';
                const failedRoot = document.createElement('section');
                document.body.appendChild(failedRoot);
                await module.mountCatalogueWorksReport({
                    reportRoot: failedRoot,
                    studioBaseUrl: 'http://127.0.0.1:8765',
                    publicPreviewBase: 'http://127.0.0.1:4000',
                    window
                });
                const failed = {
                    empty: failedRoot.querySelector('.docsViewerReport__empty').textContent,
                    rowCount: failedRoot.querySelectorAll('tbody tr').length,
                    searchDisabled: failedRoot.querySelector('input').disabled,
                    status: failedRoot.querySelector('.docsViewerReport__status').textContent,
                    tableHidden: failedRoot.querySelector('table').hidden
                };
                return {
                    cleared,
                    copied,
                    failed,
                    initial,
                    invalidMessages,
                    hiddenMediumSearchIds: hiddenMediumSearch.rows.map((row) => row.workId),
                    plural,
                    refreshCount,
                    requests,
                    seriesSearchIds: seriesSearch.rows.map((row) => row.workId),
                    yearAscending,
                    yearDescending
                };
            }"""
        )
        browser.close()

    assert result["initial"] == {
        "copyDisabled": True,
        "prompt": "Search by Work or Series to show Catalogue Works.",
        "reportId": "catalogue_works",
        "presentation": "table",
        "rowCount": 0,
        "status": "3 published Works loaded.",
        "tableHidden": True,
        "tableTag": "TABLE",
        "headTag": "THEAD",
        "bodyTag": "TBODY",
        "headings": [
            "Work▲",
            "Year",
            "Title",
            "Series",
            "Storage",
            "Medium type",
            "Medium caption",
        ],
        "presentationColumns": [
            {"id": "work", "label": "Work", "visibility": "both"},
            {"id": "year", "label": "Year", "visibility": "both"},
            {"id": "title", "label": "Title", "visibility": "both"},
            {"id": "series", "label": "Series", "visibility": "both"},
            {"id": "storage", "label": "Storage", "visibility": "both"},
            {"id": "medium_type", "label": "Medium type", "visibility": "expanded"},
            {
                "id": "medium_caption",
                "label": "Medium caption",
                "visibility": "expanded",
            },
        ],
        "presentationKind": "semantic-table",
        "presentationTableExact": True,
        "sortableCount": 5,
    }
    assert result["plural"] == {
        "workId": "00008",
        "workHref": "http://127.0.0.1:4000/works/?work=00008",
        "titleHref": "http://127.0.0.1:4000/works/?work=00008",
        "series": [
            {
                "id": "105",
                "href": "http://127.0.0.1:4000/series/?series=105",
                "text": "Alpha [105]",
            },
            {
                "id": "026",
                "href": "http://127.0.0.1:4000/series/?series=026",
                "text": "Collected [026]",
            },
        ],
        "status": "1 of 3 published Works",
        "mediumType": "drawing",
        "mediumCaption": "pencil on paper",
        "columnIds": [
            "work",
            "year",
            "title",
            "series",
            "storage",
            "medium_type",
            "medium_caption",
        ],
        "visibility": ["both", "both", "both", "both", "both", "expanded", "expanded"],
    }
    assert result["seriesSearchIds"] == ["00008"]
    assert result["hiddenMediumSearchIds"] == []
    assert result["yearAscending"] == {
        "ariaSort": "ascending",
        "rowIds": ["00010", "00008", "00009"],
    }
    assert result["yearDescending"] == {
        "ariaSort": "descending",
        "rowIds": ["00009", "00008", "00010"],
    }
    assert result["copied"] == [
        "Work\tYear\tTitle\tSeries\tStorage\n"
        "00009\t2001\tSecond Work\tBeta [001]\tShelf 2\n"
        "00008\t1990–1995\tShared Work\tAlpha [105]; Collected [026]\tShelf 1\n"
        "00010\t1985\tAlphabet Study\t—\t—",
        "Work\tYear\tTitle\tSeries\tStorage\tMedium type\tMedium caption\n"
        "00009\t2001\tSecond Work\tBeta [001]\tShelf 2\tpainting\tacrylic on canvas\n"
        "00008\t1990–1995\tShared Work\tAlpha [105]; Collected [026]\tShelf 1\t"
        "drawing\tpencil on paper\n"
        "00010\t1985\tAlphabet Study\t—\t—\t—\t—",
    ]
    assert result["cleared"] == {
        "rowCount": 0,
        "prompt": "Search by Work or Series to show Catalogue Works.",
        "tableHidden": True,
    }
    assert result["invalidMessages"] == [
        "Catalogue Works input is invalid.",
        "Catalogue Works input is invalid.",
        "Catalogue Works input is invalid.",
    ]
    assert result["refreshCount"] == 5
    assert result["failed"] == {
        "empty": "The current Catalogue Works report could not complete.",
        "rowCount": 0,
        "searchDisabled": True,
        "status": "Catalogue Works input is invalid.",
        "tableHidden": True,
    }
    assert [request["url"] for request in result["requests"][:2]] == [
        "http://127.0.0.1:8765/studio/api/catalogue/read?key=catalogue_works",
        "http://127.0.0.1:8765/studio/api/catalogue/read?key=catalogue_series",
    ]
    assert all(request["cache"] == "no-store" for request in result["requests"])
    assert all(request["accept"] == "application/json" for request in result["requests"])
    assert not any("/assets/data/" in request["url"] for request in result["requests"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-root", default=".")
    args = parser.parse_args()
    server, base_url = start_static_server(Path(args.site_root))
    try:
        run_smoke(base_url)
    finally:
        server.shutdown()
        server.server_close()
    print("Docs Viewer Catalogue Works report modules OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
