#!/usr/bin/env python3
"""Smoke-check that the public Docs Viewer boots without local capability."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys
from threading import Thread
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from tests.smoke.route_ready_helpers import wait_for_route_ready  # noqa: E402


DOC_ID = "d-20260426-164043-e14f49"


class QuietStaticHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A003
        return


def start_static_server(site_root: Path) -> tuple[ThreadingHTTPServer, str]:
    root = site_root.expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"site root does not exist: {root}")
    handler = partial(QuietStaticHandler, directory=str(root))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def public_route_state(page) -> dict[str, object]:
    return page.locator("#docsViewerRoot").evaluate(
        """async root => {
            const configUrl = root.dataset.routeConfigUrl || '';
            const payload = await fetch(configUrl).then(response => response.json());
            const route = (payload.routes || []).find(record => (
                record.route_id === root.dataset.routeId
            )) || {};
            return {
                appKind: root.dataset.docsViewerAppKind || '',
                managementUi: root.dataset.managementUi || '',
                sourceService: root.dataset.sourceService || '',
                ready: root.dataset.docsViewerReady || '',
                busy: root.dataset.docsViewerBusy || '',
                routeId: root.dataset.routeId || '',
                routeConfigUrl: configUrl,
                services: route.services || {},
                managementControls: document.querySelectorAll(
                    '.docsViewer__manageActions, #docsViewerManageActionsButton, '
                    + '#docsViewerManageEditButton, #docsViewerStatusPills'
                ).length
            };
        }"""
    )


def assert_public_boundary(state: dict[str, object], request_paths: set[str]) -> None:
    if (
        state["appKind"] != "public"
        or state["managementUi"] != "false"
        or state["sourceService"] != "false"
        or state["ready"] != "true"
        or state["busy"] == "true"
        or state["routeId"] != "analysis"
        or state["routeConfigUrl"]
        != "/docs-viewer/config/routes/docs-viewer-public-routes.json"
        or state["managementControls"] != 0
    ):
        raise AssertionError(f"public Docs Viewer capability boundary changed: {state!r}")
    services = state["services"] if isinstance(state["services"], dict) else {}
    if any(
        str(surface.get("base_url") or "")
        for surface in services.values()
        if isinstance(surface, dict)
    ):
        raise AssertionError(f"public Docs Viewer exposed local service URLs: {state!r}")

    expected = {
        "/assets/data/docs/scopes/analysis/index-tree.json",
        f"/assets/data/docs/scopes/analysis/by-id/{DOC_ID}.json",
    }
    if not expected.issubset(request_paths):
        raise AssertionError(
            f"public Docs Viewer missed compact payloads: {sorted(expected - request_paths)!r}"
        )
    blocked = sorted(
        path
        for path in request_paths
        if path.startswith("/docs-viewer/runtime/js/management/")
        or path.startswith("/docs/")
    )
    if blocked:
        raise AssertionError(f"public Docs Viewer requested local capability: {blocked!r}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-root", required=True)
    parser.add_argument("--timeout-ms", type=int, default=15000)
    args = parser.parse_args()

    server, base_url = start_static_server(Path(args.site_root))
    errors: list[str] = []
    request_urls: list[str] = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.on("request", lambda request: request_urls.append(request.url))
                page.goto(
                    f"{base_url}/analysis/?doc={DOC_ID}",
                    wait_until="domcontentloaded",
                )
                wait_for_route_ready(
                    page,
                    "#docsViewerRoot",
                    "data-docs-viewer-ready",
                    "data-docs-viewer-busy",
                    args.timeout_ms,
                )
                assert_public_boundary(
                    public_route_state(page),
                    {urlparse(url).path for url in request_urls},
                )
            finally:
                browser.close()
        if errors:
            raise AssertionError(f"page errors during public Docs Viewer boot: {errors!r}")
    finally:
        server.shutdown()
        server.server_close()

    print(f"public Docs Viewer boundary OK: {base_url}/analysis/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
