#!/usr/bin/env python3
"""Smoke-check Series Tags report rendering."""

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
    resolved_root = site_root.expanduser().resolve()
    if not resolved_root.exists():
        raise FileNotFoundError(f"site root does not exist: {resolved_root}")
    handler = partial(QuietStaticHandler, directory=str(resolved_root))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def route_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}{path}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:4000")
    parser.add_argument("--site-root", help="Serve a site or repository root on a temporary local HTTP server.")
    args = parser.parse_args()

    server = None
    base_url = args.base_url
    if args.site_root:
        server, base_url = start_static_server(Path(args.site_root))

    errors: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(route_url(base_url, "/"), wait_until="domcontentloaded")
            result = page.evaluate(
                """async () => {
                    document.body.innerHTML = '<main><div id="mount"></div></main>';
                    const render = await import('/studio/app/frontend/js/series-tags-render.js');
                    const registry = new Map([
                        ['subject:trees', { group: 'subject', label: 'trees', status: 'active' }],
                        ['domain:studio', { group: 'domain', label: 'studio', status: 'active' }],
                        ['form:line', { group: 'form', label: 'line', status: 'active' }],
                        ['theme:memory', { group: 'theme', label: 'memory', status: 'active' }],
                        ['theme:old', { group: 'theme', label: 'old', status: 'candidate' }]
                    ]);
                    const reportInput = {
                        mount: document.querySelector('#mount'),
                        config: {
                            ui_text: {
                                series_tags: {
                                    table_heading_series: 'series',
                                    table_heading_status: 'status',
                                    table_heading_tags: 'tags',
                                    filter_all_tags: 'All tags',
                                    chip_caption_local: 'local',
                                    chip_caption_delete: 'delete',
                                    group_info_title: 'Open groups',
                                    group_info_aria_label: 'Open groups'
                                }
                            }
                        },
                        studioGroups: ['subject', 'domain', 'form', 'theme'],
                        groupInfoPagePath: '/studio/analytics/tag-groups/',
                        groupDescriptions: new Map([
                            ['subject', 'Subject group'],
                            ['domain', 'Domain group']
                        ]),
                        seriesData: [
                            { seriesId: 'red', title: 'Red Series', url: '/red/' },
                            { seriesId: 'amber', title: 'Amber Series', url: '/amber/' },
                            { seriesId: 'green', title: 'Green Series', url: '/green/' }
                        ],
                        assignmentsSeries: {
                            red: { tags: [] },
                            amber: { tags: [{ tag_id: 'subject:trees', w_manual: 1 }] },
                            green: {
                                tags: [
                                    { tag_id: 'subject:trees', w_manual: 1 },
                                    { tag_id: 'domain:studio', w_manual: 1 },
                                    { tag_id: 'form:line', w_manual: 1 },
                                    { tag_id: 'theme:memory', w_manual: 1 }
                                ]
                            }
                        },
                        offlineSession: {
                            series: {
                                amber: {
                                    staged_row: {
                                        tags: [
                                            { tag_id: 'subject:trees', w_manual: 2 },
                                            { tag_id: 'theme:old', w_manual: 1 }
                                        ]
                                    }
                                }
                            }
                        },
                        registry,
                        filterGroup: 'all',
                        sortKey: 'status',
                        sortDir: 'asc'
                    };
                    render.renderSeriesTagsReport(reportInput);
                    const allRows = Array.from(document.querySelectorAll('.seriesTags__row')).map(row => ({
                        title: row.querySelector('.seriesTags__col--title')?.textContent.trim() || '',
                        ragClass: row.querySelector('.rag')?.className || '',
                        ragTitle: row.querySelector('.rag')?.getAttribute('title') || '',
                        ragLabel: row.querySelector('.rag')?.getAttribute('aria-label') || '',
                        chips: Array.from(row.querySelectorAll('.tagStudio__chip')).map(chip => chip.textContent.replace(/\\s+/g, ' ').trim())
                    }));
                    reportInput.filterGroup = 'theme';
                    render.renderSeriesTagsReport(reportInput);
                    const themeRows = Array.from(document.querySelectorAll('.seriesTags__row')).map(row => ({
                        title: row.querySelector('.seriesTags__col--title')?.textContent.trim() || '',
                        chips: Array.from(row.querySelectorAll('.tagStudio__chip')).map(chip => chip.textContent.replace(/\\s+/g, ' ').trim())
                    }));
                    return {
                        allRows,
                        themeRows,
                        activeFilter: document.querySelector('[data-group="theme"]')?.dataset.state || '',
                        groupInfoHref: document.querySelector('.tagStudio__keyInfoBtn')?.getAttribute('href') || '',
                        subjectTitle: document.querySelector('[data-group="subject"]')?.getAttribute('title') || ''
                    };
                }"""
            )
        finally:
            browser.close()
            if server:
                server.shutdown()

    if errors:
        raise AssertionError(f"page errors during Series Tags render smoke: {errors!r}")

    if [row["title"] for row in result["allRows"]] != ["Red Series", "Amber Series", "Green Series"]:
        raise AssertionError(f"status sort order mismatch: {result!r}")
    if "rag--red" not in result["allRows"][0]["ragClass"] or "status RED:" not in result["allRows"][0]["ragLabel"]:
        raise AssertionError(f"red RAG output mismatch: {result!r}")
    if "rag--amber" not in result["allRows"][1]["ragClass"] or "deprecated: 1" not in result["allRows"][1]["ragTitle"]:
        raise AssertionError(f"amber RAG output mismatch: {result!r}")
    if "old local" not in result["allRows"][1]["chips"]:
        raise AssertionError(f"local chip output mismatch: {result!r}")
    if result["themeRows"][1]["chips"] != ["old local"] or result["themeRows"][0]["chips"] != []:
        raise AssertionError(f"theme filter output mismatch: {result!r}")
    if result["activeFilter"] != "active" or result["groupInfoHref"] != "/studio/analytics/tag-groups/":
        raise AssertionError(f"filter controls mismatch: {result!r}")
    if result["subjectTitle"] != "Subject group":
        raise AssertionError(f"group description title mismatch: {result!r}")

    print("Series Tags render smoke OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
