#!/usr/bin/env python3
"""Smoke-check public catalogue search runtime helpers."""

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


def assert_catalogue_search_runtime(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const module = await import('/assets/js/search/catalogue-search-runtime.js');
            const entries = module.normalizeCatalogueSearchEntries([
                {
                    kind: 'work',
                    id: 'W-002',
                    title: 'Blue Field',
                    display_meta: '2025',
                    medium_type: 'print',
                    series_ids: ['s-1'],
                    series_titles: ['Field Series'],
                    search_terms: ['blue field'],
                    search_text: 'blue field print'
                },
                {
                    kind: 'work',
                    id: 'W-001',
                    title: 'Blue',
                    display_meta: '2024',
                    medium_type: 'drawing',
                    search_terms: ['blue'],
                    search_text: 'blue drawing'
                },
                {
                    kind: 'series',
                    id: 'S-001',
                    title: 'Field Series',
                    series_type: 'study',
                    search_text: 'field series study'
                },
                {
                    kind: '',
                    id: 'missing',
                    title: 'ignored',
                    href: '/ignored/'
                }
            ], { scope: 'catalogue', scopeLabel: 'catalogue' });
            const messages = {
                prompt: 'Enter a search query.',
                no_results: 'No results.',
                results_count_one: '1 result',
                results_count_visible: 'Showing {visible} of {count} results',
                results_count: '{count} results',
                load_more: 'more',
                result_meta_separator: ' / ',
                result_kind_work: 'work',
                result_kind_series: 'series'
            };
            const text = (key, fallback, tokens) => {
                const template = messages[key] || fallback;
                if (!tokens) return template;
                return Object.entries(tokens).reduce(
                    (value, [token, replacement]) => value.replace(`{${token}}`, replacement),
                    template
                );
            };
            const timer = () => ({ end: () => 0.25 });
            const projection = module.createCatalogueSearchResultsProjection({
                entries,
                queryText: 'blue',
                visibleCount: 1,
                runtimePolicy: { minQueryLength: 1 },
                baseurl: '/base',
                resultCollator: module.createCatalogueSearchResultCollator(),
                timer,
                text
            });
            const cached = module.createCatalogueSearchResultsProjection({
                entries,
                queryText: 'blue',
                visibleCount: 2,
                runtimePolicy: { minQueryLength: 1 },
                matchCache: projection.matchCache,
                resultCollator: module.createCatalogueSearchResultCollator(),
                timer,
                text
            });
            const noResults = module.createCatalogueSearchResultsProjection({
                entries,
                queryText: 'orange',
                visibleCount: 2,
                runtimePolicy: { minQueryLength: 1 },
                timer,
                text
            });
            const prompt = module.createCatalogueSearchResultsProjection({
                entries,
                queryText: '',
                visibleCount: 2,
                runtimePolicy: { minQueryLength: 1 },
                timer,
                text
            });
            return {
                normalizedCount: entries.length,
                firstTitleNorm: entries[0].titleNorm,
                firstSeriesNorm: entries[0].seriesTitleNorms,
                projectionStatus: projection.status.text,
                projectionHtml: projection.resultsHtml,
                moreHtml: projection.moreHtml,
                metrics: projection.metrics,
                cachedStatus: cached.status.text,
                cachedEvaluateMs: cached.metrics.evaluateMs,
                noResultsStatus: noResults.status.text,
                noResultsVisible: noResults.metrics.visibleCount,
                promptStatus: prompt.status.text,
                promptMetrics: prompt.metrics,
                normalizedQuery: module.normalizeCatalogueSearchText('  Blue!! Field  ')
            };
        }"""
    )
    assert result["normalizedCount"] == 3
    assert result["firstTitleNorm"] == "blue field"
    assert result["firstSeriesNorm"] == ["field series"]
    assert result["projectionStatus"] == "Showing 1 of 2 results"
    assert "Blue" in result["projectionHtml"]
    assert "/base/works/?work=W-001" in result["projectionHtml"]
    assert "studioSearch__moreBtn" in result["moreHtml"]
    assert result["metrics"]["queryLength"] == 4
    assert result["metrics"]["entryCount"] == 3
    assert result["metrics"]["matchCount"] == 2
    assert result["metrics"]["visibleCount"] == 1
    assert result["cachedStatus"] == "2 results"
    assert result["cachedEvaluateMs"] == 0
    assert result["noResultsStatus"] == "No results."
    assert result["noResultsVisible"] == 0
    assert result["promptStatus"] == "Enter a search query."
    assert result["promptMetrics"] is None
    assert result["normalizedQuery"] == "blue field"


def run(site_root: Path) -> None:
    server, base_url = start_static_server(site_root)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{base_url}/series/", wait_until="domcontentloaded")
            errors: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            assert_catalogue_search_runtime(page)
            browser.close()
            if errors:
                raise AssertionError(f"page errors during catalogue search runtime smoke: {errors!r}")
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
