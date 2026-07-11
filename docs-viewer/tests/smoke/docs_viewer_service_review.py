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
    write_json(package / "inventories/assets.json", {"schema_version": "asset_inventory_v1", "assets": []})
    return package


def start_server() -> tuple[DocsViewerServer, str]:
    config = DocsViewerServiceConfig(
        host="127.0.0.1",
        port=0,
        base_url="http://127.0.0.1:0",
        management_enabled=False,
        generated_reads_enabled=False,
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
        "sourceService": "true",
        "viewerScope": "review",
    }:
        raise AssertionError(f"unexpected Docs Review app context: {state!r}")
    if page.locator("#docsViewerReviewControlsMount select").input_value() != "fixture-review":
        raise AssertionError("Docs Review package selector did not retain package identity")
    canonical = page.locator("#docsViewerReviewControlsMount a", has_text="Open canonical")
    if canonical.get_attribute("href") != "/docs/?scope=library&doc=fixture-root":
        raise AssertionError("Docs Review canonical comparison link is incorrect")

    page.goto(
        f"{base_url}/docs-review/?package=fixture-review&doc=fixture-root&view=source",
        wait_until="domcontentloaded",
    )
    try:
        page.wait_for_selector("textarea.docsViewerSourceEditor__textarea", state="visible", timeout=timeout_ms)
    except Exception as error:
        diagnostics = page.evaluate(
            """() => ({
                status: document.querySelector('#docsViewerStatus')?.textContent || '',
                buttonHidden: document.querySelector('#docsViewerManageSourceButton')?.hidden,
                buttonDisabled: document.querySelector('#docsViewerManageSourceButton')?.disabled,
                content: document.querySelector('#docsViewerContent')?.innerHTML || '',
                url: location.href
            })"""
        )
        raise AssertionError(f"Markdown source mode did not open: {diagnostics!r}") from error
    if "view=source" not in page.url or "package=fixture-review" not in page.url:
        raise AssertionError(f"source route did not preserve review package identity: {page.url}")
    textarea = page.locator("textarea.docsViewerSourceEditor__textarea")
    textarea.fill("# Fixture root\n\nEdited in Docs Review.\n")
    page.locator("#docsViewerManageSourceSaveButton").click()
    page.wait_for_function(
        """() => {
            const content = document.querySelector('#docsViewerContent');
            return content && content.textContent.includes('Edited in Docs Review.');
        }""",
        timeout=timeout_ms,
    )
    if "view=source" in page.url or "package=fixture-review" not in page.url:
        raise AssertionError(f"rendered route did not preserve only package identity: {page.url}")

    if any("/docs/generated/" in url or "/docs/source" in url for url in requests):
        raise AssertionError("Docs Review crossed into configured-scope generated/source services")


def main() -> int:
    timeout_ms = 15000
    with tempfile.TemporaryDirectory() as temp_dir:
        os.environ["DOTLINEFORM_PROJECTS_BASE_DIR"] = temp_dir
        (Path(temp_dir) / "data-sharing").mkdir()
        write_fixture_package()
        server, base_url = start_server()
        try:
            capabilities = read_json(f"{base_url}/docs-review/capabilities")["capabilities"]
            if capabilities.get("review_source_write") is not True or capabilities.get("canonical_write") is not False:
                raise AssertionError(f"unexpected Docs Review backend authority: {capabilities!r}")
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
