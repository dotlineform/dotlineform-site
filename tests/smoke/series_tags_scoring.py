#!/usr/bin/env python3
"""Smoke-check Series Tags scoring helpers."""

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
                    const scoring = await import('/assets/studio/js/analysis-tag-scoring.js');
                    const registry = new Map([
                        ['subject:trees', { group: 'subject', status: 'active' }],
                        ['domain:studio', { group: 'domain', status: 'active' }],
                        ['form:line', { group: 'form', status: 'active' }],
                        ['theme:memory', { group: 'theme', status: 'active' }],
                        ['theme:candidate', { group: 'theme', status: 'candidate' }]
                    ]);
                    const red = scoring.buildStudioTagScore([], registry, {});
                    const amber = scoring.buildStudioTagScore(['subject:trees'], registry, {});
                    const green = scoring.buildStudioTagScore(
                        ['subject:trees', 'domain:studio', 'form:line', 'theme:memory'],
                        registry,
                        {}
                    );
                    const unknown = scoring.buildStudioTagScore(['subject:unknown'], registry, {});
                    const deprecated = scoring.buildStudioTagScore(
                        ['subject:trees', 'domain:studio', 'form:line', 'theme:candidate'],
                        registry,
                        {}
                    );
                    const duplicate = scoring.buildStudioTagScore(
                        ['subject:trees', 'subject:trees'],
                        registry,
                        {}
                    );
                    return { red, amber, green, unknown, deprecated, duplicate };
                }"""
            )
        finally:
            browser.close()
            if server:
                server.shutdown()

    if errors:
        raise AssertionError(f"page errors during Series Tags scoring smoke: {errors!r}")

    expected = {
        "red": ("red", 0, "status RED:"),
        "amber": ("amber", 1, "status AMBER:"),
        "green": ("green", 2, "status GREEN:"),
        "unknown": ("red", 0, "unknown: 1"),
        "deprecated": ("amber", 1, "deprecated: 1"),
        "duplicate": ("amber", 1, "tags: 1"),
    }
    for key, (rag, rank, label_fragment) in expected.items():
        score = result[key]
        if score["rag"] != rag or score["ragRank"] != rank:
            raise AssertionError(f"{key} score mismatch: {score!r}")
        if label_fragment not in score["ragLabel"] and label_fragment not in score["tooltip"]:
            raise AssertionError(f"{key} score text mismatch: {score!r}")

    print("Series Tags scoring smoke OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
