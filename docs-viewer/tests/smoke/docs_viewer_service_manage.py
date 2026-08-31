#!/usr/bin/env python3
"""Smoke-check standalone Docs Viewer Manage route boot and service projection."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

from playwright.sync_api import sync_playwright


DOC_ID = "d-20260501-174746-efd581"
DOC_TITLE = "Testing"


def source_text() -> str:
    return f"""---
doc_id: {DOC_ID}
title: {DOC_TITLE}
added_date: "2026-05-01 17:47:46"
last_updated: "2026-05-01 17:47:46"
ui_status: in-progress
parent_id: ""
---
# {DOC_TITLE}

Isolated Docs Viewer Manage route fixture.
"""


def prepare_external_studio_generated_data() -> None:
    projects_base = Path(os.environ["DOTLINEFORM_PROJECTS_BASE_DIR"])
    scope_root = projects_base / "docs-viewer/scopes/studio"
    documents_root = scope_root / "source/documents"
    documents_root.mkdir(parents=True, exist_ok=True)
    (scope_root / "generated").mkdir(parents=True, exist_ok=True)
    (scope_root / "published").mkdir(parents=True, exist_ok=True)
    (documents_root / f"{DOC_ID}.md").write_text(source_text(), encoding="utf-8")
    for media_type in ("files", "html", "img", "svg"):
        (scope_root / "source/media" / media_type).mkdir(parents=True, exist_ok=True)
    (scope_root / "source/media/build-source/mermaid").mkdir(parents=True, exist_ok=True)

    repo_root = Path(__file__).resolve().parents[3]
    services_root = repo_root / "docs-viewer/services"
    if str(services_root) not in sys.path:
        sys.path.insert(0, str(services_root))

    from docs_scope_build_manifest import write_build_manifest  # noqa: PLC0415
    from docs_scope_config import load_docs_scope_configs  # noqa: PLC0415

    tree = {
        "schema": "docs_index_tree_v1",
        "viewer_options": {
            "non_loadable_doc_ids": [],
            "manage_only_tree_root_ids": [],
        },
        "docs": [
            {
                "scope": "studio",
                "doc_id": DOC_ID,
                "title": DOC_TITLE,
                "content_url": f"/docs/doc?scope=studio&doc_id={DOC_ID}",
            }
        ],
    }
    document = {
        "doc_id": DOC_ID,
        "title": DOC_TITLE,
        "content_html": f'<h1 id="testing">{DOC_TITLE}</h1><p>Manage smoke fixture.</p>',
    }
    recent = {
        "schema": "docs_recent_v1",
        "basis": "edited",
        "limit": 10,
        "docs": tree["docs"],
    }
    search = {
        "header": {
            "schema": "docs_viewer_search_index_v2",
            "scope": "studio",
            "version": "manage-smoke",
            "count": 1,
        },
        "fields": ["title"],
        "docs": [{"id": DOC_ID, "title": DOC_TITLE}],
        "terms": {"testing": {"title": [0]}},
    }

    def write_json(path: Path, payload: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    generated_root = scope_root / "generated"
    write_json(generated_root / "documents/index-tree.json", tree)
    write_json(generated_root / f"documents/by-id/{DOC_ID}.json", document)
    write_json(generated_root / "documents/recent.json", recent)
    write_json(generated_root / "search/index.json", search)
    config = load_docs_scope_configs(repo_root, scope_ids=("studio",))["studio"]
    write_build_manifest(repo_root, config)


def manage_route_state(page) -> dict[str, object]:
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
                viewerBaseUrl: route.viewer_base_url || '',
                generatedBaseUrl: route.services?.generated_data?.base_url || '',
                sourceBaseUrl: route.services?.source?.base_url || '',
                managementBaseUrl: route.services?.management?.base_url || '',
                snapshotSelectPresent: Boolean(root.querySelector('#docsViewerSnapshotSelect'))
            };
        }"""
    )


def assert_manage_route_boundary(state: dict[str, object], base_url: str) -> None:
    expected = {
        "appKind": "manage",
        "managementUi": "true",
        "sourceService": "true",
        "ready": "true",
        "busy": "false",
        "routeId": "docs-manage",
        "routeConfigUrl": "/docs-viewer/config/routes/docs-viewer-routes.json",
        "viewerBaseUrl": "/docs/",
        "generatedBaseUrl": base_url,
        "sourceBaseUrl": base_url,
        "managementBaseUrl": base_url,
        "snapshotSelectPresent": False,
    }
    if state != expected:
        raise AssertionError(f"Docs Viewer Manage route boundary changed: {state!r}")


def run_manage_smoke(projects_base: Path, *, timeout_ms: int) -> None:
    previous_projects_base = os.environ.get("DOTLINEFORM_PROJECTS_BASE_DIR")
    projects_base.mkdir(parents=True, exist_ok=True)
    os.environ["DOTLINEFORM_PROJECTS_BASE_DIR"] = str(projects_base)
    server = None
    base_url = ""
    errors: list[str] = []
    try:
        prepare_external_studio_generated_data()
        from docs_viewer_route_smoke_support import (  # noqa: PLC0415
            start_docs_viewer_server,
            wait_for_document,
        )

        server, base_url = start_docs_viewer_server()
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                page.on("pageerror", lambda error: errors.append(error.stack or str(error)))
                page.goto(
                    f"{base_url}/docs/?scope=studio&doc={DOC_ID}",
                    wait_until="domcontentloaded",
                )
                wait_for_document(page, DOC_TITLE, timeout_ms)
                assert_manage_route_boundary(manage_route_state(page), base_url)
            finally:
                browser.close()
        if errors:
            raise AssertionError(f"page errors during Docs Viewer Manage boot: {errors!r}")
    finally:
        if server is not None:
            server.shutdown()
            server.server_close()
        if previous_projects_base is None:
            os.environ.pop("DOTLINEFORM_PROJECTS_BASE_DIR", None)
        else:
            os.environ["DOTLINEFORM_PROJECTS_BASE_DIR"] = previous_projects_base

    print(f"Docs Viewer Manage route boundary OK: {base_url}/docs/")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout-ms", type=int, default=15000)
    parser.add_argument("--projects-base-dir")
    args = parser.parse_args(argv)

    if args.projects_base_dir:
        run_manage_smoke(
            Path(args.projects_base_dir).resolve(),
            timeout_ms=args.timeout_ms,
        )
    else:
        with TemporaryDirectory(prefix="docs-viewer-manage-smoke-") as temporary_directory:
            run_manage_smoke(
                Path(temporary_directory) / "Projects",
                timeout_ms=args.timeout_ms,
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
