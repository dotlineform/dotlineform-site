#!/usr/bin/env python3
"""Smoke-check Docs Review route boot and its isolated authority boundary."""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
from urllib.parse import urlparse
import urllib.request

from playwright.sync_api import sync_playwright


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_fixture_package(projects_base: Path) -> None:
    package = projects_base / "data-sharing/import-preview/fixture-review"
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
            "selected_doc_ids": ["fixture-root"],
            "default_doc_id": "fixture-root",
            "source_export_id": "ds_20260712T190000Z",
            "staged_filename": "fixture-reviewed.jsonl",
        },
    )
    (package / "source").mkdir(parents=True)
    (package / "source/fixture-root.md").write_text(
        """---
doc_id: fixture-root
title: Fixture root
added_date: 2026-07-11
last_updated: 2026-07-11
---
# Fixture root

Review boundary proof.
""",
        encoding="utf-8",
    )
    write_json(
        package / "inventories/assets.json",
        {"schema_version": "asset_inventory_v1", "assets": []},
    )


def read_json(url: str) -> dict[str, object]:
    with urllib.request.urlopen(url, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def assert_review_capabilities(base_url: str) -> None:
    payload = read_json(f"{base_url}/docs-review/capabilities")
    capabilities = payload.get("capabilities")
    if not isinstance(capabilities, dict):
        raise AssertionError(f"Docs Review returned no capability map: {payload!r}")
    expected = {
        "review_generated_read": True,
        "review_source_open": True,
        "canonical_write": False,
        "management": False,
        "publish": False,
    }
    actual = {name: capabilities.get(name) for name in expected}
    if actual != expected:
        raise AssertionError(f"Docs Review authority changed: {actual!r}")


def assert_review_route(page, base_url: str, timeout_ms: int, wait_for_document) -> None:
    request_urls: list[str] = []
    page.on("request", lambda request: request_urls.append(request.url))
    page.goto(
        f"{base_url}/docs-review/?package=fixture-review&doc=fixture-root",
        wait_until="domcontentloaded",
    )
    wait_for_document(page, "Fixture root", timeout_ms)
    state = page.locator("#docsViewerRoot").evaluate(
        """root => ({
            appKind: root.dataset.docsViewerAppKind || '',
            managementUi: root.dataset.managementUi || '',
            sourceService: root.dataset.sourceService || '',
            viewerScope: root.dataset.viewerScope || '',
            managementControls: document.querySelectorAll(
                '.docsViewer__manageActions, #docsViewerManageActionsButton, '
                + '#docsViewerManageEditButton, #docsViewerStatusPills'
            ).length
        })"""
    )
    expected_state = {
        "appKind": "review",
        "managementUi": "false",
        "sourceService": "false",
        "viewerScope": "review",
        "managementControls": 0,
    }
    if state != expected_state:
        raise AssertionError(f"Docs Review browser boundary changed: {state!r}")

    paths = {urlparse(url).path for url in request_urls}
    expected_paths = {
        "/docs-review/packages/index-tree",
        "/docs-review/packages/payload",
    }
    if not expected_paths.issubset(paths):
        raise AssertionError(f"Docs Review missed provider reads: {sorted(expected_paths - paths)!r}")
    blocked = sorted(
        path
        for path in paths
        if path.startswith("/docs/")
        or (
            path.startswith("/docs-viewer/runtime/js/management/")
            and path.endswith(".js")
        )
    )
    if blocked:
        raise AssertionError(f"Docs Review requested management capability: {blocked!r}")


def main() -> int:
    timeout_ms = 15000
    previous_projects_base = os.environ.get("DOTLINEFORM_PROJECTS_BASE_DIR")
    with tempfile.TemporaryDirectory(prefix="docs-viewer-review-") as temp_dir:
        projects_base = Path(temp_dir)
        os.environ["DOTLINEFORM_PROJECTS_BASE_DIR"] = str(projects_base)
        (projects_base / "data-sharing").mkdir()
        (projects_base / "docs-viewer").mkdir()
        write_fixture_package(projects_base)
        try:
            from docs_viewer_route_smoke_support import (  # noqa: PLC0415
                start_docs_viewer_server,
                wait_for_document,
            )

            server, base_url = start_docs_viewer_server(review_enabled=True)
            try:
                assert_review_capabilities(base_url)
                with sync_playwright() as playwright:
                    browser = playwright.chromium.launch(headless=True)
                    errors: list[str] = []
                    try:
                        page = browser.new_page(viewport={"width": 1280, "height": 900})
                        page.on("pageerror", lambda error: errors.append(str(error)))
                        assert_review_route(page, base_url, timeout_ms, wait_for_document)
                    finally:
                        browser.close()
                if errors:
                    raise AssertionError(f"page errors during Docs Review boot: {errors!r}")
            finally:
                server.shutdown()
                server.server_close()
        finally:
            if previous_projects_base is None:
                os.environ.pop("DOTLINEFORM_PROJECTS_BASE_DIR", None)
            else:
                os.environ["DOTLINEFORM_PROJECTS_BASE_DIR"] = previous_projects_base

    print("Docs Review authority boundary OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
