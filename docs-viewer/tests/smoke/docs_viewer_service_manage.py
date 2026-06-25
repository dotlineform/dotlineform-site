#!/usr/bin/env python3
"""Smoke-check the standalone Docs Viewer service manage route."""

from __future__ import annotations

import argparse
from dataclasses import replace
import json
import sys
from pathlib import Path
from threading import Thread
import urllib.error
import urllib.request
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import Page, sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "docs-viewer" / "services"))

from docs_viewer_service import DocsViewerServer, DocsViewerServiceConfig  # noqa: E402


def start_server() -> tuple[DocsViewerServer, str]:
    config = DocsViewerServiceConfig(
        host="127.0.0.1",
        port=0,
        base_url="http://127.0.0.1:0",
        management_enabled=True,
        generated_reads_enabled=True,
        watch_enabled=True,
    )
    server = DocsViewerServer(("127.0.0.1", 0), REPO_ROOT, config)
    base_url = f"http://127.0.0.1:{server.server_address[1]}"
    server.docs_viewer_config = replace(config, port=server.server_address[1], base_url=base_url)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, base_url


def query_value(url: str, key: str) -> str:
    return (parse_qs(urlparse(url).query).get(key) or [""])[0]


def request_paths(urls: list[str]) -> set[str]:
    return {urlparse(url).path for url in urls}


def read_json_url(url: str) -> dict[str, object]:
    with urllib.request.urlopen(url, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def assert_service_basics(base_url: str) -> None:
    health = read_json_url(f"{base_url}/health")
    if health.get("service") != "docs_viewer" or health.get("ok") is not True:
        raise AssertionError(f"unexpected health response: {health!r}")

    capabilities = read_json_url(f"{base_url}/capabilities")
    studio_caps = capabilities.get("capabilities", {}).get("scopes", {}).get("studio", {})
    if capabilities.get("capabilities", {}).get("docs_management") is not True:
        raise AssertionError(f"expected Docs Viewer management to be enabled: {capabilities!r}")
    if studio_caps.get("available") is not True or studio_caps.get("generated_data_reads") is not True:
        raise AssertionError(f"expected real Studio generated data reads: {studio_caps!r}")


def assert_origin_rejection(base_url: str) -> None:
    payload = json.dumps({"scope": "studio", "doc_id": "docs-viewer"}).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url}/docs/delete-preview",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Origin": "https://example.com",
        },
        method="POST",
    )
    try:
        urllib.request.urlopen(request, timeout=10)
    except urllib.error.HTTPError as error:
        if error.code != 403:
            raise AssertionError(f"expected disallowed Origin to return 403, got {error.code}") from error
    else:
        raise AssertionError("disallowed Origin should be rejected")


def wait_for_manage_doc(page: Page, title: str, timeout_ms: int) -> None:
    page.wait_for_selector("#docsViewerRoot:not([hidden])", timeout=timeout_ms)
    page.wait_for_function(
        """expectedTitle => {
            const heading = document.querySelector("#docsViewerContent h1");
            const actions = document.querySelector(".docsViewer__manageActions");
            const button = document.querySelector("#docsViewerManageActionsButton");
            return heading &&
                heading.textContent.trim() === expectedTitle &&
                actions &&
                !actions.hidden &&
                button &&
                !button.disabled;
        }""",
        arg=title,
        timeout=timeout_ms,
    )


def manage_route_state(page: Page) -> dict[str, object]:
    return page.locator("#docsViewerRoot").evaluate(
        """async root => {
            const routeConfigUrl = root.dataset.routeConfigUrl || "";
            const payload = await fetch(routeConfigUrl).then(response => response.json());
            const routeConfig = (payload.routes || []).find(record => record.route_id === root.dataset.routeId) || {};
            return {
                allowManagement: root.dataset.allowManagement || "",
                includeScopeParam: root.dataset.includeScopeParam || "",
                routeId: root.dataset.routeId || "",
                routeConfigUrl,
                docsPaths: routeConfig.docs_paths || {},
                viewerBaseUrl: routeConfig.viewer_base_url || "",
                managementBaseUrl: routeConfig.access?.management_base_url || "",
                generatedBaseUrl: routeConfig.generated_base_url || ""
            };
        }"""
    )


def assert_manage_route_contract(state: dict[str, object], base_url: str) -> None:
    docs_paths = state.get("docsPaths") if isinstance(state.get("docsPaths"), dict) else {}
    if state["allowManagement"] != "true" or state["viewerBaseUrl"] != "/docs/":
        raise AssertionError(f"manage route did not expose management access: {state!r}")
    if state["includeScopeParam"] != "true":
        raise AssertionError(f"manage route did not include scope param: {state!r}")
    if state["routeId"] != "docs-manage":
        raise AssertionError(f"manage route used unexpected route id: {state!r}")
    if state["routeConfigUrl"] != "/docs-viewer/config/routes/docs-viewer-routes.json":
        raise AssertionError(f"manage route used unexpected route config: {state!r}")
    if state["managementBaseUrl"] != base_url or state["generatedBaseUrl"] != base_url:
        raise AssertionError(f"manage route did not receive service base URL: {state!r}")
    if docs_paths.get("index_tree_url") != "/docs-viewer/generated/docs/studio/index-tree.json":
        raise AssertionError(f"manage route config missing index_tree_url: {state!r}")
    if docs_paths.get("recently_added_url") != "/docs-viewer/generated/docs/studio/recently-added.json":
        raise AssertionError(f"manage route config missing recently_added_url: {state!r}")
    if docs_paths.get("search_index_url") != "/docs-viewer/generated/search/studio/index.json":
        raise AssertionError(f"manage route config missing search_index_url: {state!r}")


def assert_generated_requests(paths: set[str]) -> None:
    for expected in ["/docs/generated/index-tree", "/docs/generated/payload"]:
        if expected not in paths:
            raise AssertionError(f"expected generated service request {expected!r}; saw {sorted(paths)!r}")


def exercise_manage_route(page: Page, base_url: str, timeout_ms: int) -> tuple[set[str], str]:
    generated_requests: list[str] = []
    page.on(
        "request",
        lambda request: generated_requests.append(request.url)
        if "/docs/generated/" in request.url
        else None,
    )

    page.goto(f"{base_url}/docs/?scope=studio&doc=docs-viewer", wait_until="domcontentloaded")
    wait_for_manage_doc(page, "Docs Viewer", timeout_ms)
    assert_manage_route_contract(manage_route_state(page), base_url)
    return request_paths(generated_requests), page.url


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout-ms", type=int, default=15000)
    args = parser.parse_args(argv)

    server, base_url = start_server()
    try:
        assert_service_basics(base_url)
        assert_origin_rejection(base_url)

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            errors: list[str] = []
            try:
                page = browser.new_page()
                page.on("pageerror", lambda exc: errors.append(str(exc)))
                generated_paths, final_url = exercise_manage_route(page, base_url, args.timeout_ms)
            finally:
                browser.close()

        assert_generated_requests(generated_paths)
        if query_value(final_url, "mode"):
            raise AssertionError(f"expected clean manage URL without mode query, got {final_url}")
        if errors:
            raise AssertionError(f"page errors during Docs Viewer service smoke: {errors!r}")
        print(f"Docs Viewer service manage shell OK: {base_url}/docs/?scope=studio&doc=docs-viewer")
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
