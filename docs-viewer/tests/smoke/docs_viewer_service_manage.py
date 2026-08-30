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


def prepare_external_studio_snapshot() -> None:
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
    from docs_scope_publish import (  # noqa: PLC0415
        PUBLISH_MANIFEST_FILENAME,
        PUBLISH_MANIFEST_SCHEMA_VERSION,
        file_record,
        files_revision,
        utc_now,
    )

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

    for role in ("generated", "published"):
        role_root = scope_root / role
        write_json(role_root / "documents/index-tree.json", tree)
        write_json(role_root / f"documents/by-id/{DOC_ID}.json", document)
        write_json(role_root / "documents/recent.json", recent)
        write_json(role_root / "search/index.json", search)
    config = load_docs_scope_configs(repo_root, scope_ids=("studio",))["studio"]
    write_build_manifest(repo_root, config)

    published_root = scope_root / "published"
    published_files = {
        path.relative_to(published_root): path.read_bytes()
        for path in sorted(published_root.rglob("*"))
        if path.is_file() and path.name != PUBLISH_MANIFEST_FILENAME
    }
    records = [
        file_record(path.as_posix(), data)
        for path, data in sorted(published_files.items(), key=lambda item: item[0].as_posix())
    ]
    write_json(
        published_root / PUBLISH_MANIFEST_FILENAME,
        {
            "schema_version": PUBLISH_MANIFEST_SCHEMA_VERSION,
            "scope": "studio",
            "completed_at": utc_now(),
            "generated_revision": "manage-smoke",
            "published_revision": files_revision(published_files),
            "file_count": len(records),
            "files": records,
        },
    )


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
                snapshotValue: root.querySelector('#docsViewerSnapshotSelect')?.value || '',
                snapshotOptions: Array.from(
                    root.querySelector('#docsViewerSnapshotSelect')?.options || []
                ).map(option => option.value)
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
        "snapshotValue": "generated",
        "snapshotOptions": ["generated", "published"],
    }
    if state != expected:
        raise AssertionError(f"Docs Viewer Manage route boundary changed: {state!r}")


def assert_available_published_snapshot(page, timeout_ms: int, wait_for_document) -> None:
    with page.expect_response(
        lambda response: "/docs/published/index-tree?" in response.url,
        timeout=timeout_ms,
    ) as response_info:
        page.locator("#docsViewerSnapshotSelect").select_option("published")
    if response_info.value.status != 200:
        raise AssertionError(
            f"Published snapshot index returned HTTP {response_info.value.status}."
        )
    page.wait_for_url("**snapshot=published**", timeout=timeout_ms)
    wait_for_document(page, DOC_TITLE, timeout_ms)
    state = page.locator("#docsViewerRoot").evaluate(
        """root => ({
            snapshot: root.querySelector('#docsViewerSnapshotSelect')?.value || '',
            status: root.querySelector('#docsViewerStatus')?.textContent || '',
            nav: root.querySelector('#docsViewerNav')?.textContent || '',
            content: root.querySelector('#docsViewerContent')?.textContent || ''
        })"""
    )
    if state["snapshot"] != "published":
        raise AssertionError(f"Published snapshot selector is mislabeled: {state!r}")
    if DOC_TITLE not in state["nav"] and DOC_TITLE not in state["content"]:
        raise AssertionError(f"Published snapshot did not render the requested document: {state!r}")


def run_manage_smoke(projects_base: Path, *, timeout_ms: int) -> None:
    previous_projects_base = os.environ.get("DOTLINEFORM_PROJECTS_BASE_DIR")
    projects_base.mkdir(parents=True, exist_ok=True)
    os.environ["DOTLINEFORM_PROJECTS_BASE_DIR"] = str(projects_base)
    server = None
    base_url = ""
    errors: list[str] = []
    try:
        prepare_external_studio_snapshot()
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
                assert_available_published_snapshot(page, timeout_ms, wait_for_document)
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
