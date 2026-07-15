#!/usr/bin/env python3
"""Smoke-check public Docs Viewer routes boot read-only on compact payloads."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys
from threading import Thread
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import Page, sync_playwright

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from tests.smoke.route_ready_helpers import wait_for_route_ready


LIBRARY_DOC_ID = "d-20260330-172255-8399b7"
ANALYSIS_DOC_ID = "d-20260426-164043-e14f49"
TAGS_DOC_ID = "d-20260624-213316-478639"
BIRD_SUBDOC_ID = "d-20260624-204534-0d6ae2"
NERVE_SUBDOC_ID = "d-20260624-204534-ecfc12"
ORDERED_SUBDOC_ID = "d-20260624-204534-e3de0b"
MOMENTS_DOC_ID = "d-20260215-000000-8c3fcc"


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


def request_paths(urls: list[str]) -> set[str]:
    return {urlparse(url).path for url in urls}


def query_value(url: str, key: str) -> str:
    return (parse_qs(urlparse(url).query).get(key) or [""])[0]


def wait_for_rendered_doc(page: Page, doc_id: str, title: str, timeout_ms: int) -> None:
    wait_for_route_ready(
        page,
        "#docsViewerRoot",
        "data-docs-viewer-ready",
        "data-docs-viewer-busy",
        timeout_ms,
    )
    page.wait_for_function(
        """([docId, expectedTitle]) => {
            const heading = document.querySelector("#docsViewerContent h1");
            const active = document.querySelector(".docsViewer__navLink.is-active");
            return heading &&
                heading.textContent.trim() === expectedTitle &&
                active &&
                active.dataset.docId === docId;
        }""",
        arg=[doc_id, title],
        timeout=timeout_ms,
    )


def public_route_state(page: Page) -> dict[str, object]:
    return page.locator("#docsViewerRoot").evaluate(
        """async root => {
            const routeConfigUrl = root.dataset.routeConfigUrl || "";
            const payload = await fetch(routeConfigUrl).then(response => response.json());
            const routeConfig = (payload.routes || []).find(record => record.route_id === root.dataset.routeId) || {};
            const docsViewerConfigUrl = routeConfig.config_urls?.docs_viewer || "";
            const docsViewerConfig = docsViewerConfigUrl
                ? await fetch(docsViewerConfigUrl).then(response => response.json())
                : {};
            const scopeConfig = (docsViewerConfig.scopes || []).find(record => record.scope_id === root.dataset.viewerScope) || {};
            return {
                appKind: root.dataset.docsViewerAppKind || "",
                managementUi: root.dataset.managementUi || "",
                sourceService: root.dataset.sourceService || "",
                ready: root.dataset.docsViewerReady || "",
                busy: root.dataset.docsViewerBusy || "",
                routeId: root.dataset.routeId || "",
                routeConfigUrl,
                docsPaths: routeConfig.docs_paths || {},
                services: routeConfig.services || {},
                scopeConfig,
                viewerBaseUrl: routeConfig.viewer_base_url || "",
                managementControls: document.querySelectorAll(
                    ".docsViewer__manageActions, #docsViewerManageActionsButton, #docsViewerManageEditButton, #docsViewerStatusPills"
                ).length
            };
        }"""
    )


def assert_public_route_contract(route: str, state: dict[str, object]) -> None:
    route_id = route.strip("/").split("/", 1)[0] or route.strip("/?")
    docs_paths = state.get("docsPaths") if isinstance(state.get("docsPaths"), dict) else {}
    scope_config = state.get("scopeConfig") if isinstance(state.get("scopeConfig"), dict) else {}
    services = state.get("services") if isinstance(state.get("services"), dict) else {}
    if state["appKind"] != "public" or state["managementUi"] != "false" or state["sourceService"] != "false":
        raise AssertionError(f"{route} exposed the wrong app/service context: {state!r}")
    if any(str(surface.get("base_url") or "") for surface in services.values() if isinstance(surface, dict)):
        raise AssertionError(f"{route} exposed local service URLs: {state!r}")
    if state["ready"] != "true" or state["busy"] == "true":
        raise AssertionError(f"{route} did not expose ready route state: {state!r}")
    if state["viewerBaseUrl"] == "/docs/":
        raise AssertionError(f"{route} used management route base: {state!r}")
    if state["managementControls"]:
        raise AssertionError(f"{route} rendered management controls: {state!r}")
    if state["routeConfigUrl"] != "/docs-viewer/config/routes/docs-viewer-public-routes.json":
        raise AssertionError(f"{route} used unexpected route config: {state!r}")
    if state["routeId"] != route_id:
        raise AssertionError(f"{route} used unexpected route id: {state!r}")
    if not str(docs_paths.get("index_tree_url") or "").endswith("/index-tree.json"):
        raise AssertionError(f"{route} route config missing index_tree_url: {state!r}")
    if not str(docs_paths.get("recently_added_url") or "").endswith("/recently-added.json"):
        raise AssertionError(f"{route} route config missing recently_added_url: {state!r}")
    if not str(docs_paths.get("search_index_url") or "").endswith("/index.json"):
        raise AssertionError(f"{route} route config missing search_index_url: {state!r}")


def assert_payload_requests(route: str, paths: set[str], scope: str, doc_id: str) -> None:
    expected_tree = f"/assets/data/docs/scopes/{scope}/index-tree.json"
    expected_recent = f"/assets/data/docs/scopes/{scope}/recently-added.json"
    expected_doc = f"/assets/data/docs/scopes/{scope}/by-id/{doc_id}.json"
    expected_search = f"/assets/data/search/{scope}/index.json"
    missing = [path for path in [expected_tree, expected_recent, expected_doc, expected_search] if path not in paths]
    if missing:
        raise AssertionError(f"{route} missed expected compact payload requests {missing!r}; saw {sorted(paths)!r}")


def assert_public_info_panel(page: Page, route: str, title: str, timeout_ms: int) -> None:
    page.locator("#docsViewerInfoToggle").click()
    page.wait_for_function(
        """expectedTitle => {
            const root = document.querySelector("#docsViewerRoot");
            const panel = document.querySelector("#docsViewerInfoPanel");
            const title = panel?.querySelector(".docsViewer__metadataInfoTitle");
            return root?.dataset.infoPanelState === "open" &&
                panel &&
                !panel.hidden &&
                title &&
                title.textContent.trim() === expectedTitle;
        }""",
        arg=title,
        timeout=timeout_ms,
    )
    info_state = page.locator("#docsViewerInfoPanel").evaluate(
        """panel => ({
            terms: Array.from(panel.querySelectorAll("dt")).map((node) => node.textContent.trim()),
            text: panel.textContent || ""
        })"""
    )
    if info_state["terms"] != ["Summary", "Updated"]:
        raise AssertionError(f"{route} public info panel did not render public metadata terms: {info_state!r}")
    blocked = ["Doc ID", "Date", "Added", "Scope", "Parent path", "UI status", "Visibility", "Route"]
    leaked = [item for item in blocked if item in str(info_state["text"])]
    if leaked:
        raise AssertionError(f"{route} public info panel leaked management metadata {leaked!r}: {info_state!r}")


def exercise_search(page: Page, route: str, query: str, timeout_ms: int) -> None:
    page.locator("#docsViewerSearchInput").fill(query)
    page.wait_for_function(
        """query => {
            const input = document.querySelector("#docsViewerSearchInput");
            const status = document.querySelector("#docsViewerResultsStatus");
            return input &&
                input.value === query &&
                status &&
                !status.hidden &&
                /results?|No results/.test(status.textContent);
        }""",
        arg=query,
        timeout=timeout_ms,
    )


def exercise_public_route(
    page: Page,
    base_url: str,
    route: str,
    doc_id: str,
    title: str,
    timeout_ms: int,
    *,
    expect_document_controls: bool = True,
) -> None:
    request_urls: list[str] = []
    page.on("request", lambda request: request_urls.append(request.url))
    page.goto(route_url(base_url, route), wait_until="domcontentloaded")
    wait_for_rendered_doc(page, doc_id, title, timeout_ms)
    if query_value(page.url, "mode"):
        raise AssertionError(f"{route} should remove mode query state, got {page.url}")
    assert_public_route_contract(route, public_route_state(page))
    if expect_document_controls:
        assert_public_info_panel(page, route, title, timeout_ms)
    else:
        unexpected_controls = page.locator(
            "#docsViewerMainViewToolbar, #docsViewerPath, #docsViewerInfoToggle, #docsViewerBookmarkToggle"
        ).count()
        if unexpected_controls:
            raise AssertionError(f"{route} rendered intentionally hidden document controls")
    page.locator("#docsViewerRecentButton").click()
    page.wait_for_function(
        """() => {
            const status = document.querySelector("#docsViewerResultsStatus");
            return status && !status.hidden && /recently added docs?/.test(status.textContent);
        }""",
        timeout=timeout_ms,
    )
    exercise_search(page, route, title, timeout_ms)
    route_scope = urlparse(route).path.strip("/").split("/", 1)[0]
    assert_payload_requests(route, request_paths(request_urls), route_scope, doc_id)


def exercise_public_subscope_report(page: Page, base_url: str, timeout_ms: int) -> None:
    request_urls: list[str] = []
    page.on("request", lambda request: request_urls.append(request.url))
    page.goto(route_url(base_url, f"/analysis/?doc={TAGS_DOC_ID}"), wait_until="domcontentloaded")
    wait_for_rendered_doc(page, TAGS_DOC_ID, "Tags", timeout_ms)
    page.wait_for_function(
        f"""() => {{
            const report = document.querySelector(".docsViewerReport");
            const rows = Array.from(document.querySelectorAll(".docsViewerReport__row"));
            return report &&
                report.dataset.reportId === "docs_subscope" &&
                report.dataset.reportSubscope === "tags" &&
                rows.map((row) => row.dataset.reportSubdocId).join(",") === "{BIRD_SUBDOC_ID},{NERVE_SUBDOC_ID},{ORDERED_SUBDOC_ID}" &&
                rows.map((row) => (row.textContent || "").trim()).join(",") === "bird,nerve,ordered";
        }}""",
        timeout=timeout_ms,
    )
    if query_value(page.url, "doc") != TAGS_DOC_ID:
        raise AssertionError(f"public report parent doc should remain selected, got {page.url}")
    paths = request_paths(request_urls)
    if "/assets/data/docs/public-reports.json" not in paths:
        raise AssertionError(f"public report did not read public report registry; saw {sorted(paths)!r}")
    if "/assets/data/docs/scopes/analysis/tags/manifest.json" not in paths:
        raise AssertionError(f"public report did not read sub-scope manifest; saw {sorted(paths)!r}")
    page.locator(
        f".docsViewerReport__row[data-report-subdoc-id='{ORDERED_SUBDOC_ID}'] .docsViewerReport__subscopeButton"
    ).click()
    page.wait_for_function(
        f"""() => {{
            const report = document.querySelector(".docsViewerReport");
            const active = document.querySelector(".docsViewer__navLink.is-active");
            const detail = document.querySelector(".docsReportDetail__body");
            return report &&
                report.dataset.reportState === "detail" &&
                active &&
                active.dataset.docId === "{TAGS_DOC_ID}" &&
                detail &&
                /form:ordered/.test(detail.textContent || "") &&
                new URL(location.href).searchParams.get("doc") === "{TAGS_DOC_ID}" &&
                new URL(location.href).searchParams.get("subdoc") === "{ORDERED_SUBDOC_ID}";
        }}""",
        timeout=timeout_ms,
    )
    page.go_back(wait_until="domcontentloaded")
    page.wait_for_function(
        """() => {
            const report = document.querySelector(".docsViewerReport");
            return report &&
                report.dataset.reportState === "list" &&
                !new URL(location.href).searchParams.has("subdoc") &&
                document.querySelectorAll(".docsViewerReport__row").length === 3;
        }""",
        timeout=timeout_ms,
    )
    page.go_forward(wait_until="domcontentloaded")
    page.wait_for_function(
        f"""() => {{
            const detail = document.querySelector(".docsReportDetail__body");
            return document.querySelector(".docsViewerReport")?.dataset.reportState === "detail" &&
                /form:ordered/.test(detail?.textContent || "") &&
                new URL(location.href).searchParams.get("subdoc") === "{ORDERED_SUBDOC_ID}";
        }}""",
        timeout=timeout_ms,
    )
    page.locator(".docsReportDetail__back").click()
    page.wait_for_function(
        """() => document.querySelector(".docsViewerReport")?.dataset.reportState === "list" &&
            !new URL(location.href).searchParams.has("subdoc")""",
        timeout=timeout_ms,
    )
    page.goto(
        route_url(base_url, f"/analysis/?doc={TAGS_DOC_ID}&subdoc={BIRD_SUBDOC_ID}"),
        wait_until="domcontentloaded",
    )
    wait_for_rendered_doc(page, TAGS_DOC_ID, "Tags", timeout_ms)
    page.wait_for_function(
        f"""() => {{
            const active = document.querySelector(".docsViewer__navLink.is-active");
            const detail = document.querySelector(".docsReportDetail__body");
            return active &&
                active.dataset.docId === "{TAGS_DOC_ID}" &&
                document.querySelector(".docsViewerReport")?.dataset.reportState === "detail" &&
                /subject:bird/.test(detail?.textContent || "") &&
                new URL(location.href).searchParams.get("doc") === "{TAGS_DOC_ID}" &&
                new URL(location.href).searchParams.get("subdoc") === "{BIRD_SUBDOC_ID}";
        }}""",
        timeout=timeout_ms,
    )
    page.goto(
        route_url(base_url, f"/analysis/?doc={TAGS_DOC_ID}&subdoc=missing-detail"),
        wait_until="domcontentloaded",
    )
    wait_for_rendered_doc(page, TAGS_DOC_ID, "Tags", timeout_ms)
    page.wait_for_function(
        f"""() => document.querySelector(".docsViewerReport")?.dataset.reportState === "error" &&
            /missing-detail/.test(document.querySelector(".docsViewerReport")?.textContent || "") &&
            document.querySelector(".docsViewer__navLink.is-active")?.dataset.docId === "{TAGS_DOC_ID}" """,
        timeout=timeout_ms,
    )
    paths = request_paths(request_urls)
    blocked = [
        path for path in paths
        if path in {
            "/docs-viewer/runtime/js/reports/docs-viewer-reports.js",
            "/docs-viewer/runtime/js/reports/docs-viewer-report-service.js",
        }
    ]
    if blocked:
        raise AssertionError(f"public report loaded manage/local report runtime paths: {blocked!r}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-root", required=True, help="Built public site root to serve.")
    parser.add_argument("--timeout-ms", type=int, default=15000)
    args = parser.parse_args()

    static_server, base_url = start_static_server(Path(args.site_root))
    errors: list[str] = []
    request_failures: list[str] = []
    http_failures: list[str] = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                page.on("pageerror", lambda exc: errors.append(str(exc)))
                page.on("requestfailed", lambda request: request_failures.append(f"{request.url}: {request.failure}"))
                page.on(
                    "response",
                    lambda response: http_failures.append(f"{response.status}: {response.url}") if response.status >= 400 else None,
                )
                legacy_mode = "manage"
                exercise_public_route(
                    page,
                    base_url,
                    f"/library/?doc={LIBRARY_DOC_ID}&mode={legacy_mode}",
                    LIBRARY_DOC_ID,
                    "Library",
                    args.timeout_ms,
                )
                exercise_public_route(
                    page,
                    base_url,
                    f"/analysis/?doc={ANALYSIS_DOC_ID}",
                    ANALYSIS_DOC_ID,
                    "Analysis",
                    args.timeout_ms,
                )
                exercise_public_subscope_report(page, base_url, args.timeout_ms)
                exercise_public_route(
                    page,
                    base_url,
                    f"/moments/?doc={MOMENTS_DOC_ID}",
                    MOMENTS_DOC_ID,
                    "a feeling of free will",
                    args.timeout_ms,
                    expect_document_controls=False,
                )
            finally:
                browser.close()

        if errors:
            raise AssertionError(f"page errors during public Docs Viewer read-only smoke: {errors!r}")
        if request_failures:
            raise AssertionError(f"request failures during public Docs Viewer read-only smoke: {request_failures!r}")
        if http_failures:
            raise AssertionError(f"HTTP failures during public Docs Viewer read-only smoke: {http_failures!r}")
        print(
            "public Docs Viewer read-only OK: "
            f"{base_url}/library/, {base_url}/analysis/, and {base_url}/moments/"
        )
        return 0
    finally:
        static_server.shutdown()
        static_server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
