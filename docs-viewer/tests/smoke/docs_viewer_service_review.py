#!/usr/bin/env python3
"""Fixture-backed browser smoke for the local Docs Review route."""

from __future__ import annotations

from dataclasses import replace
import json
import os
from pathlib import Path
import sys
import tempfile
from threading import Thread
import urllib.error
from urllib.parse import parse_qs, urlparse
import urllib.request

from playwright.sync_api import Page, sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "docs-viewer" / "services"))

from docs_viewer_service import DocsViewerServer, DocsViewerServiceConfig  # noqa: E402
from docs_document_packages.workspace import workspace_paths  # noqa: E402
from tests.smoke.route_ready_helpers import wait_for_route_ready  # noqa: E402


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_fixture_package() -> Path:
    package = workspace_paths().import_preview / "fixture-review"
    write_json(
        package / "manifest.json",
        {
            "schema_version": "docs_review_validated_package_v1",
            "package_id": "fixture-review",
            "status": "validated",
            "title": "Fixture review",
            "source_scope": "library",
            "supports_docs_review": True,
            "supports_return_import": True,
            "selected_doc_ids": ["fixture-root", "fixture-child"],
            "default_doc_id": "fixture-root",
            "source_export_id": "ds_20260712T190000Z",
            "staged_filename": "fixture-reviewed.jsonl",
        },
    )
    source = """---
doc_id: fixture-root
title: Fixture root
summary: Returned fixture summary.
added_date: 2026-07-11
last_updated: 2026-07-11
---
# Fixture root

Original review text.
"""
    (package / "source").mkdir(parents=True)
    (package / "source/fixture-root.md").write_text(source, encoding="utf-8")
    (package / "source/fixture-child.md").write_text(
        """---
doc_id: fixture-child
title: Fixture child
parent_id: fixture-root
added_date: 2026-07-11
last_updated: 2026-07-11
---
# Fixture child

Nested review text.
""",
        encoding="utf-8",
    )
    write_json(package / "inventories/assets.json", {"schema_version": "asset_inventory_v1", "assets": []})
    return package


def start_server() -> tuple[DocsViewerServer, str]:
    config = DocsViewerServiceConfig(
        host="127.0.0.1",
        port=0,
        base_url="http://127.0.0.1:0",
        management_enabled=True,
        generated_reads_enabled=True,
        watch_enabled=False,
        review_enabled=True,
    )
    server = DocsViewerServer(("127.0.0.1", 0), REPO_ROOT, config)
    base_url = f"http://127.0.0.1:{server.server_address[1]}"
    server.docs_viewer_config = replace(config, port=server.server_address[1], base_url=base_url)
    Thread(target=server.serve_forever, daemon=True).start()
    return server, base_url


def read_json(url: str) -> dict[str, object]:
    with urllib.request.urlopen(url, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def assert_source_endpoints_retired(base_url: str) -> None:
    requests = [
        urllib.request.Request(
            f"{base_url}/docs-review/packages/source?package_id=fixture-review&doc_id=fixture-root"
        ),
        urllib.request.Request(
            f"{base_url}/docs-review/packages/source",
            data=json.dumps({"package_id": "fixture-review"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        ),
    ]
    for request in requests:
        try:
            urllib.request.urlopen(request, timeout=10)
        except urllib.error.HTTPError as error:
            if error.code != 404:
                raise AssertionError(f"retired review source endpoint returned {error.code}") from error
        else:
            raise AssertionError("retired review source endpoint remained reachable")


def exercise_review_route(page: Page, base_url: str, timeout_ms: int) -> None:
    requests: list[str] = []
    build_requests: list[dict[str, object]] = []
    open_source_requests: list[dict[str, object]] = []

    def record_request(request) -> None:
        requests.append(request.url)
        if urlparse(request.url).path == "/docs-review/packages/build":
            build_requests.append(json.loads(request.post_data or "{}"))

    def handle_open_source(route, request) -> None:
        payload = json.loads(request.post_data or "{}")
        open_source_requests.append(payload)
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "ok": True,
                    "package_id": payload.get("package_id"),
                    "doc_id": payload.get("doc_id"),
                    "editor": "vscode",
                    "summary_text": f"Opened {payload.get('doc_id')} source.",
                }
            ),
        )

    page.on("request", record_request)
    page.route("**/docs-review/packages/open-source", handle_open_source)
    page.add_init_script(
        """const key = 'docsReviewRouteLoads';
        sessionStorage.setItem(key, String(Number(sessionStorage.getItem(key) || 0) + 1));"""
    )
    page.goto(
        f"{base_url}/docs-review/?package=fixture-review&doc=fixture-root",
        wait_until="domcontentloaded",
    )
    wait_for_route_ready(
        page,
        "#docsViewerRoot",
        "data-docs-viewer-ready",
        "data-docs-viewer-busy",
        timeout_ms,
    )
    page.wait_for_selector("#docsViewerContent h1", state="visible", timeout=timeout_ms)
    if page.locator("#docsViewerContent h1").inner_text().strip() != "Fixture root":
        raise AssertionError("Docs Review did not render the fixture document")
    if page.locator('[data-toggle-doc-id="fixture-root"]').count() != 1:
        raise AssertionError("Docs Review did not render the nested fixture tree toggle")
    child_link = page.locator('#docsViewerNav [data-doc-id="fixture-child"]')
    if child_link.count() != 1 or not child_link.is_visible():
        raise AssertionError("Docs Review did not render the nested fixture document")
    state = page.locator("#docsViewerRoot").evaluate(
        """root => ({
            appKind: root.dataset.docsViewerAppKind,
            managementUi: root.dataset.managementUi,
            sourceService: root.dataset.sourceService,
            viewerScope: root.dataset.viewerScope
        })"""
    )
    if state != {
        "appKind": "review",
        "managementUi": "false",
        "sourceService": "false",
        "viewerScope": "review",
    }:
        raise AssertionError(f"unexpected Docs Review app context: {state!r}")
    package_select = page.locator("#docsViewerReviewControlsMount select")
    if package_select.input_value() != "fixture-review":
        raise AssertionError("Docs Review package selector did not retain package identity")
    package_select_layout = package_select.evaluate(
        """select => ({
            flexBasis: getComputedStyle(select).flexBasis,
            rootFontSize: getComputedStyle(document.documentElement).fontSize
        })"""
    )
    expected_flex_basis = 25 * float(
        package_select_layout["rootFontSize"].removesuffix("px")
    )
    actual_flex_basis = float(
        package_select_layout["flexBasis"].removesuffix("px")
    )
    if abs(actual_flex_basis - expected_flex_basis) > 0.5:
        raise AssertionError(
            f"Docs Review package selector did not use its 25rem width: "
            f"{package_select_layout!r}"
        )
    canonical = page.locator("#docsViewerReviewControlsMount a", has_text="Open canonical")
    if canonical.get_attribute("href") != "/docs/?scope=library&doc=fixture-root":
        raise AssertionError("Docs Review canonical comparison link is incorrect")
    if page.locator("#docsViewerReviewControlsMount a", has_text="Import").count() != 0:
        raise AssertionError("Docs Review still exposed an Import action")
    vscode_button = page.locator("#docsViewerReviewOpenVsCodeButton")
    if vscode_button.count() != 1 or vscode_button.is_hidden() or vscode_button.is_disabled():
        raise AssertionError(
            "Docs Review did not expose an enabled Open in VS Code action: "
            f"count={vscode_button.count()} "
            f"hidden={vscode_button.is_hidden() if vscode_button.count() else 'missing'} "
            f"disabled={vscode_button.is_disabled() if vscode_button.count() else 'missing'}"
        )
    if vscode_button.get_attribute("data-docs-viewer-action") != "open-vscode":
        raise AssertionError("Docs Review Open in VS Code lost the shared action identity")
    if vscode_button.get_attribute("title") != "Open in VS Code":
        raise AssertionError("Docs Review Open in VS Code action has no explicit label")
    page.wait_for_function(
        """() => {
            const icon = document.querySelector('#docsViewerReviewOpenVsCodeButton img');
            return icon && icon.complete && icon.naturalWidth === 100 && icon.naturalHeight === 100;
        }""",
        timeout=timeout_ms,
    )
    vscode_icon = vscode_button.locator("img")
    if not vscode_icon.get_attribute("src").endswith(
        "/docs-viewer/runtime/js/management/icons/vscode.svg"
    ):
        raise AssertionError("Docs Review Open in VS Code did not reuse the official icon")
    if vscode_icon.get_attribute("alt") != "" or vscode_icon.get_attribute("aria-hidden") != "true":
        raise AssertionError("Docs Review VS Code icon did not remain decorative")
    vscode_button.click()
    page.wait_for_function(
        """() => document.querySelector('#docsViewerStatus')?.textContent
            === 'Opened fixture-root source.'""",
        timeout=timeout_ms,
    )
    if open_source_requests != [
        {
            "package_id": "fixture-review",
            "doc_id": "fixture-root",
        }
    ]:
        raise AssertionError(
            f"Docs Review did not open the exact selected package document: {open_source_requests!r}"
        )
    review_payload = read_json(
        f"{base_url}/docs-review/packages/payload?package_id=fixture-review&doc_id=fixture-root"
    )["payload"]
    if review_payload.get("summary") != "Returned fixture summary.":
        raise AssertionError(f"Docs Review lost returned summary metadata: {review_payload!r}")

    page.goto(
        f"{base_url}/docs-review/?package=fixture-review&doc=fixture-root&view=source",
        wait_until="domcontentloaded",
    )
    wait_for_route_ready(
        page,
        "#docsViewerRoot",
        "data-docs-viewer-ready",
        "data-docs-viewer-busy",
        timeout_ms,
    )
    page.wait_for_selector("#docsViewerContent h1", state="visible", timeout=timeout_ms)
    if "view=source" in page.url or "package=fixture-review" not in page.url:
        raise AssertionError(f"read-only review route did not discard source mode: {page.url}")
    if page.locator("textarea.docsViewerSourceEditor__textarea").count() != 0:
        raise AssertionError("Docs Review still mounted a Markdown source editor")
    if page.locator("#docsViewerManageSourceButton, #docsViewerManageSourceSaveButton").count() != 0:
        raise AssertionError("Docs Review still rendered source-edit controls")

    configured_scope_paths = (
        "/docs/index-tree",
        "/docs/recent",
        "/docs/doc",
        "/docs/search",
        "/docs/semantic-tokens",
        "/docs/source",
    )
    if any(any(path in url for path in configured_scope_paths) for url in requests):
        raise AssertionError("Docs Review crossed into configured-scope generated/source services")
    if any("/docs-review/packages/source" in url for url in requests):
        raise AssertionError("Docs Review requested a retired package source endpoint")
    if any("/docs-review/packages/build" in url for url in requests):
        raise AssertionError("ordinary Docs Review reads invoked the explicit repair endpoint")
    if any("/management/source-editor/" in url for url in requests):
        raise AssertionError("Docs Review loaded management source-editor modules")
    if any(
        stylesheet in url
        for url in requests
        for stylesheet in (
            "docs-viewer-manage.css",
            "docs-viewer-source-editor.css",
            "docs-viewer-import.css",
        )
    ):
        raise AssertionError("Docs Review loaded management-only CSS")
    if not any("docs-viewer-review.css" in url for url in requests):
        raise AssertionError("Docs Review did not load its focused read-only route CSS")
    source_path = (
        workspace_paths().import_preview / "fixture-review/source/fixture-root.md"
    )
    source_text = source_path.read_text(encoding="utf-8")
    if "Original review text." not in source_text or "Edited in Docs Review" in source_text:
        raise AssertionError("read-only Docs Review changed its persistent source projection")

    edited_source_text = source_text.replace(
        "Original review text.",
        "Edited externally before explicit Build.",
    )
    source_path.write_text(edited_source_text, encoding="utf-8")
    edited_source_bytes = source_path.read_bytes()
    canonical_path = (
        workspace_paths().root.parent
        / "docs-viewer/scopes/library/source/documents/fixture-root.md"
    )
    canonical_path.parent.mkdir(parents=True)
    canonical_path.write_text(
        "---\ndoc_id: fixture-root\nlast_updated: 2026-07-10\n---\nCanonical sentinel.\n",
        encoding="utf-8",
    )
    canonical_source_bytes = canonical_path.read_bytes()
    build_button = page.locator(
        '[data-docs-viewer-review-action="build"]'
    )
    if build_button.inner_text() != "Build" or build_button.is_disabled():
        raise AssertionError("healthy Docs Review package did not expose enabled Build")
    route_loads = page.evaluate(
        "() => Number(sessionStorage.getItem('docsReviewRouteLoads') || 0)"
    )
    with page.expect_response(
        lambda response: urlparse(response.url).path
        == "/docs-review/packages/build",
        timeout=timeout_ms,
    ) as response_info:
        build_button.click()
        page.wait_for_function(
            """() => document.querySelector(
                '[data-docs-viewer-review-action="build"]'
            )?.disabled === true""",
            timeout=timeout_ms,
        )
    build_status = response_info.value.status
    page.wait_for_function(
        """expected => Number(
            sessionStorage.getItem('docsReviewRouteLoads') || 0
        ) > expected""",
        arg=route_loads,
        timeout=timeout_ms,
    )
    wait_for_route_ready(
        page,
        "#docsViewerRoot",
        "data-docs-viewer-ready",
        "data-docs-viewer-busy",
        timeout_ms,
    )
    page.wait_for_selector("#docsViewerContent h1", state="visible", timeout=timeout_ms)
    current_url = urlparse(page.url)
    current_query = parse_qs(current_url.query)
    if (
        current_url.path != "/docs-review/"
        or current_query.get("package") != ["fixture-review"]
        or current_query.get("doc") != ["fixture-root"]
    ):
        raise AssertionError(f"Build did not preserve the active review route: {page.url}")
    if "Edited externally before explicit Build." not in page.locator(
        "#docsViewerContent"
    ).inner_text():
        raise AssertionError("explicit Build did not refresh the edited retained preview")
    if build_requests != [{"package_id": "fixture-review"}]:
        raise AssertionError(f"Build did not freeze the exact package identity: {build_requests!r}")
    if build_status != 200:
        raise AssertionError(f"unexpected explicit Build response status: {build_status}")
    if source_path.read_bytes() != edited_source_bytes:
        raise AssertionError("explicit Build rewrote package-local review source")
    if canonical_path.read_bytes() != canonical_source_bytes:
        raise AssertionError("explicit Build changed the canonical timestamp sentinel")


def main() -> int:
    timeout_ms = 15000
    with tempfile.TemporaryDirectory() as temp_dir:
        os.environ["DOTLINEFORM_PROJECTS_BASE_DIR"] = temp_dir
        (Path(temp_dir) / "data-sharing").mkdir()
        (Path(temp_dir) / "docs-viewer").mkdir()
        write_fixture_package()
        server, base_url = start_server()
        try:
            capabilities = read_json(f"{base_url}/docs-review/capabilities")["capabilities"]
            if (
                "review_source_read" in capabilities
                or "review_source_write" in capabilities
                or capabilities.get("review_source_open") is not True
                or capabilities.get("canonical_write") is not False
            ):
                raise AssertionError(f"unexpected Docs Review backend authority: {capabilities!r}")
            assert_source_endpoints_retired(base_url)
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                errors: list[str] = []
                try:
                    page = browser.new_page()
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    exercise_review_route(page, base_url, timeout_ms)
                finally:
                    browser.close()
            if errors:
                raise AssertionError(f"page errors during Docs Review smoke: {errors!r}")
        finally:
            server.shutdown()
            server.server_close()
    print("Docs Viewer service review shell OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
