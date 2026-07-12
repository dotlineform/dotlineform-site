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
import urllib.request

from playwright.sync_api import Page, sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "docs-viewer" / "services"))

from docs_viewer_service import DocsViewerServer, DocsViewerServiceConfig  # noqa: E402
from services.paths import workspace_paths  # noqa: E402
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
            "default_doc_id": "fixture-root",
            "source_export_id": "ds_20260712T190000Z",
            "staged_filename": "fixture-reviewed.jsonl",
        },
    )
    source = """---
doc_id: fixture-root
title: Fixture root
added_date: 2026-07-11
last_updated: 2026-07-11
viewable: true
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
viewable: true
---
# Fixture child

Nested review text.
""",
        encoding="utf-8",
    )
    write_json(package / "inventories/assets.json", {"schema_version": "asset_inventory_v1", "assets": []})
    return package


def write_fixture_staged_package() -> Path:
    paths = workspace_paths()
    staged = paths.import_staging / "fixture-reviewed.jsonl"
    staged.parent.mkdir(parents=True, exist_ok=True)
    staged.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "record_type": "data_sharing_header",
                        "schema_version": "data_sharing_returned_package_v1",
                        "export_id": "ds_20260712T190000Z",
                    }
                ),
                json.dumps(
                    {
                        "doc_id": "fixture-root",
                        "title": "Fixture root",
                        "content": "# Fixture root\n\nReturned content.\n",
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    write_json(
        paths.meta / "ds_20260712T190000Z.meta.json",
        {
            "schema_version": "data_sharing_export_meta_v1",
            "export_id": "ds_20260712T190000Z",
            "app": "docs-viewer",
            "adapter_id": "documents",
            "data_domain": "library",
            "profile_id": "document-content",
            "config_id": "document-content",
            "scope": "library",
            "target_format": "jsonl",
            "record_shape": "document_rows",
            "supports_return_import": True,
            "generated_at": "2026-07-12T19:00:00Z",
        },
    )
    return staged


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
    page.on("request", lambda request: requests.append(request.url))
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
    if page.locator("#docsViewerReviewControlsMount select").input_value() != "fixture-review":
        raise AssertionError("Docs Review package selector did not retain package identity")
    canonical = page.locator("#docsViewerReviewControlsMount a", has_text="Open canonical")
    if canonical.get_attribute("href") != "/docs/?scope=library&doc=fixture-root":
        raise AssertionError("Docs Review canonical comparison link is incorrect")
    import_link = page.locator("#docsViewerReviewControlsMount a", has_text="Import")
    if import_link.get_attribute("href") != "/docs/?import=1&review_package=fixture-review":
        raise AssertionError("Docs Review import handoff did not contain only the safe package identity")

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

    if any("/docs/generated/" in url or "/docs/source" in url for url in requests):
        raise AssertionError("Docs Review crossed into configured-scope generated/source services")
    if any("/docs-review/packages/source" in url for url in requests):
        raise AssertionError("Docs Review requested a retired package source endpoint")
    if any("/docs-review/packages/build" in url for url in requests):
        raise AssertionError("ordinary Docs Review reads invoked the explicit repair endpoint")
    if any("/management/source-editor/" in url for url in requests):
        raise AssertionError("Docs Review loaded management source-editor modules")
    if any("docs-viewer-manage.css" in url for url in requests):
        raise AssertionError("Docs Review loaded management-only CSS")
    if not any("docs-viewer-review.css" in url for url in requests):
        raise AssertionError("Docs Review did not load its focused read-only route CSS")
    source_text = (
        workspace_paths().import_preview / "fixture-review/source/fixture-root.md"
    ).read_text(encoding="utf-8")
    if "Original review text." not in source_text or "Edited in Docs Review" in source_text:
        raise AssertionError("read-only Docs Review changed its persistent source projection")


def exercise_import_handoff(page: Page, base_url: str, staged: Path, timeout_ms: int) -> None:
    handoff_url = f"{base_url}/docs/?import=1&review_package=fixture-review"
    page.goto(handoff_url, wait_until="domcontentloaded")
    page.wait_for_function(
        """() => {
            const modal = document.querySelector('#docsViewerImportModal');
            const root = document.querySelector('#docsHtmlImportRoot');
            return modal && !modal.hidden && root && root.dataset.studioReady === 'true';
        }""",
        timeout=timeout_ms,
    )
    if page.locator("#docsHtmlImportFileSelect").input_value() != "fixture-reviewed.jsonl":
        raise AssertionError("managed Docs Import did not preselect the server-associated staged record")
    if "Reviewed package selected" not in page.locator("#docsHtmlImportStatus").inner_text():
        raise AssertionError("managed Docs Import did not report the review handoff selection")

    staged.unlink()
    page.goto(handoff_url, wait_until="domcontentloaded")
    page.wait_for_function(
        """() => {
            const modal = document.querySelector('#docsViewerImportModal');
            const root = document.querySelector('#docsHtmlImportRoot');
            return modal && !modal.hidden && root && root.dataset.studioReady === 'true';
        }""",
        timeout=timeout_ms,
    )
    status = page.locator("#docsHtmlImportStatus").inner_text()
    if "Import unavailable" not in status or "associated" not in status:
        raise AssertionError(f"deleted staged-file handoff was not reported safely: {status!r}")

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
        raise AssertionError("persistent Docs Review became unreadable after the staged file was deleted")


def main() -> int:
    timeout_ms = 15000
    with tempfile.TemporaryDirectory() as temp_dir:
        os.environ["DOTLINEFORM_PROJECTS_BASE_DIR"] = temp_dir
        (Path(temp_dir) / "data-sharing").mkdir()
        write_fixture_package()
        staged = write_fixture_staged_package()
        server, base_url = start_server()
        try:
            capabilities = read_json(f"{base_url}/docs-review/capabilities")["capabilities"]
            if (
                "review_source_read" in capabilities
                or "review_source_write" in capabilities
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
                    exercise_import_handoff(page, base_url, staged, timeout_ms)
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
