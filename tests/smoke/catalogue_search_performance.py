#!/usr/bin/env python3
"""Smoke-check public catalogue search metrics with instrumentation enabled."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from playwright.sync_api import Page, expect, sync_playwright


def first_query(site_root: Path) -> str:
    index_path = site_root / "assets" / "data" / "search" / "catalogue" / "index.json"
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    for entry in payload.get("entries", []):
        title = str(entry.get("title", "")).strip()
        if title:
            return title.split()[0]
    return "work"


def assert_search_metrics(page: Page, base_url: str, query: str) -> None:
    path = f"/catalogue/search/?searchPerf=panel&q={query}"
    page.goto(f"{base_url.rstrip('/')}{path}", wait_until="domcontentloaded")
    root = page.locator("#studioSearchRoot")
    expect(root).to_be_visible(timeout=10_000)
    expect(page.locator("#studioSearchPerformance")).to_be_visible(timeout=10_000)
    expect(page.locator("#studioSearchResults .studioSearch__item").first).to_be_visible(timeout=10_000)
    page.wait_for_function(
        """() => {
            const report = document.getElementById('studioSearchPerformanceReport');
            return report && report.textContent.includes('recent queries:');
        }""",
        timeout=10_000,
    )
    metrics = page.evaluate(
        """() => {
            const report = document.getElementById('studioSearchPerformanceReport');
            const summary = document.getElementById('studioSearchPerformanceSummary');
            const status = document.getElementById('studioSearchStatus');
            return {
                report: report ? report.textContent : '',
                summary: summary ? summary.textContent : '',
                status: status ? status.textContent : '',
                resultCount: document.querySelectorAll('#studioSearchResults .studioSearch__item').length
            };
        }"""
    )
    assert "catalogue (static), loaded" in metrics["report"]
    assert "recent queries:" in metrics["report"]
    assert "matches" in metrics["report"]
    assert "Search performance:" in metrics["summary"]
    assert metrics["resultCount"] > 0
    assert metrics["status"]


def run(site_root: Path, base_url: str) -> None:
    query = first_query(site_root)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        assert_search_metrics(page, base_url, query)
        browser.close()
        if errors:
            raise AssertionError(f"page errors during catalogue search performance smoke: {errors!r}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-root", default=".", help="Site root for choosing a catalogue query.")
    parser.add_argument("--base-url", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run(Path(args.site_root), args.base_url)


if __name__ == "__main__":
    main()
