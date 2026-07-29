#!/usr/bin/env python3
"""Smoke-check exact sub-scope Delete from the real manage route to a temporary service."""

from __future__ import annotations

import argparse
from dataclasses import replace
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from threading import Thread
from urllib.parse import urlparse

from playwright.sync_api import Page, Route, sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "docs-viewer" / "services"))
sys.path.insert(0, str(REPO_ROOT / "docs-viewer" / "tests" / "fixtures"))

PROJECTS_DIR = tempfile.TemporaryDirectory(prefix="docs-viewer-subscope-delete-route-")
os.environ["DOTLINEFORM_PROJECTS_BASE_DIR"] = PROJECTS_DIR.name
(Path(PROJECTS_DIR.name) / "docs-viewer").mkdir()
(Path(PROJECTS_DIR.name) / "data-sharing").mkdir()

import docs_write_rebuild  # noqa: E402
from docs_viewer_service import DocsViewerServer, DocsViewerServiceConfig  # noqa: E402
from docs_viewer_service_manage import (  # noqa: E402
    SUBSCOPE_DOC_ID,
    SUBSCOPE_DOC_TITLE,
    SUBSCOPE_ID,
    SUBSCOPE_REPORT_DOC_ID,
    SUBSCOPE_REPORT_DOC_TITLE,
    SUBSCOPE_SIBLING_DOC_ID,
    SUBSCOPE_SIBLING_DOC_TITLE,
    install_smoke_document_routes,
    start_server,
    wait_for_manage_doc,
)
from repo_factory import (  # noqa: E402
    docs_scope_record,
    docs_sub_scope_record,
    read_json,
    write_docs_scope_config,
    write_site_tools_config,
    write_text,
)


def source_text(doc_id: str, title: str, body: str, **metadata: str) -> str:
    fields = {
        "doc_id": doc_id,
        "title": title,
        "added_date": '"2000-01-01 00:00:00"',
        "last_updated": '"2000-01-01 00:00:00"',
        **metadata,
    }
    front_matter = "\n".join(f"{key}: {value}" for key, value in fields.items())
    return f"---\n{front_matter}\n---\n{body.rstrip()}\n"


def prepare_delete_repo(repo_root: Path) -> dict[str, object]:
    write_site_tools_config(repo_root)
    write_docs_scope_config(
        repo_root,
        [
            docs_scope_record(
                "studio",
                default_doc_id=SUBSCOPE_REPORT_DOC_ID,
                sub_scopes=[
                    docs_sub_scope_record(
                        "studio",
                        SUBSCOPE_ID,
                        title="Smoke Documents",
                    )
                ],
            )
        ],
        {"recent_limit": 10},
    )

    report_path = (
        repo_root
        / f"docs-viewer/scopes/studio/source/documents/{SUBSCOPE_REPORT_DOC_ID}.md"
    )
    write_text(
        report_path,
        source_text(
            SUBSCOPE_REPORT_DOC_ID,
            SUBSCOPE_REPORT_DOC_TITLE,
            f"# {SUBSCOPE_REPORT_DOC_TITLE}",
            viewer_report="docs_subscope",
            viewer_report_subscope=SUBSCOPE_ID,
        ),
    )
    child_root = (
        repo_root
        / f"docs-viewer/scopes/studio/source/sub-scopes/{SUBSCOPE_ID}/documents"
    )
    target_path = child_root / f"{SUBSCOPE_DOC_ID}.md"
    sibling_path = child_root / f"{SUBSCOPE_SIBLING_DOC_ID}.md"
    write_text(
        target_path,
        source_text(
            SUBSCOPE_DOC_ID,
            SUBSCOPE_DOC_TITLE,
            "# Smoke Detail\n\nDelete only this synthetic source.",
            summary="Synthetic exact-delete target.",
            ui_status="draft",
            viewable="true",
        ),
    )
    write_text(
        sibling_path,
        source_text(
            SUBSCOPE_SIBLING_DOC_ID,
            SUBSCOPE_SIBLING_DOC_TITLE,
            "# Retained Smoke Sibling\n\nThis sibling must survive.",
            summary="Synthetic retained sibling.",
            ui_status="done",
            viewable="true",
        ),
    )

    build_link = repo_root / "docs-viewer/build"
    build_link.parent.mkdir(parents=True, exist_ok=True)
    build_link.symlink_to(REPO_ROOT / "docs-viewer/build", target_is_directory=True)
    docs_write_rebuild.rebuild_sub_scope_outputs(
        repo_root,
        "studio",
        SUBSCOPE_ID,
    )

    parent_sentinels = (
        repo_root / "docs-viewer/scopes/studio/published/documents/index-tree.json",
        repo_root / "docs-viewer/scopes/studio/published/documents/recent.json",
        repo_root / "docs-viewer/scopes/studio/published/search/index.json",
        repo_root / "docs-viewer/config/defaults/docs-viewer-config.json",
        repo_root / "docs-viewer/config/defaults/docs-viewer-public-config.json",
        repo_root / "site/docs-viewer/config/defaults/docs-viewer-public-config.json",
        repo_root / "studio/data/canonical/tags/tag-registry.json",
    )
    for index, path in enumerate(parent_sentinels):
        write_text(path, f"synthetic-parent-or-external-sentinel-{index}\n")

    target_payload_path = (
        repo_root
        / (
            "docs-viewer/scopes/studio/published/documents/sub-scopes/"
            f"{SUBSCOPE_ID}/by-id/{SUBSCOPE_DOC_ID}.json"
        )
    )
    sibling_payload_path = (
        repo_root
        / (
            "docs-viewer/scopes/studio/published/documents/sub-scopes/"
            f"{SUBSCOPE_ID}/by-id/{SUBSCOPE_SIBLING_DOC_ID}.json"
        )
    )
    return {
        "target_path": target_path,
        "target_payload_path": target_payload_path,
        "sibling_path": sibling_path,
        "sibling_payload_path": sibling_payload_path,
        "manifest_path": (
            repo_root
            / (
                "docs-viewer/scopes/studio/published/documents/sub-scopes/"
                f"{SUBSCOPE_ID}/manifest.json"
            )
        ),
        "parent_sentinels": parent_sentinels,
        "parent_before": {
            path: path.read_bytes()
            for path in parent_sentinels
        },
        "sibling_source_before": sibling_path.read_bytes(),
        "sibling_payload_before": sibling_payload_path.read_bytes(),
    }


def start_mutation_server(repo_root: Path) -> tuple[DocsViewerServer, str]:
    config = DocsViewerServiceConfig(
        host="127.0.0.1",
        port=0,
        base_url="http://127.0.0.1:0",
        management_enabled=True,
        generated_reads_enabled=True,
        watch_enabled=False,
    )
    server = DocsViewerServer(("127.0.0.1", 0), repo_root, config)
    base_url = f"http://127.0.0.1:{server.server_address[1]}"
    server.docs_viewer_config = replace(
        config,
        port=server.server_address[1],
        base_url=base_url,
    )
    Thread(target=server.serve_forever, daemon=True).start()
    return server, base_url


def install_management_base_route(page: Page, management_base_url: str) -> None:
    def fulfill_route_config(route: Route) -> None:
        response = route.fetch()
        payload = response.json()
        routes = payload.get("routes")
        if not isinstance(routes, list):
            raise AssertionError("Docs Viewer route registry omitted routes")
        manage = next(
            (
                record
                for record in routes
                if isinstance(record, dict) and record.get("route_id") == "docs-manage"
            ),
            None,
        )
        if not isinstance(manage, dict):
            raise AssertionError("Docs Viewer route registry omitted docs-manage")
        services = manage.get("services")
        if not isinstance(services, dict):
            raise AssertionError("docs-manage route omitted services")
        management = services.get("management")
        if not isinstance(management, dict):
            raise AssertionError("docs-manage route omitted management service")
        management["base_url"] = management_base_url
        route.fulfill(
            status=response.status,
            content_type="application/json",
            body=json.dumps(payload),
        )

    page.route(
        re.compile(
            r".*/docs-viewer/config/routes/docs-viewer-routes\.json(?:\?.*)?$"
        ),
        fulfill_route_config,
    )


def exercise_exact_delete(
    page: Page,
    viewer_base_url: str,
    management_base_url: str,
    paths: dict[str, object],
    timeout_ms: int,
) -> None:
    install_management_base_route(page, management_base_url)
    install_smoke_document_routes(
        page,
        include_subscope_report=True,
        include_subscope_sibling=True,
    )
    requests: list[dict[str, object]] = []

    def record_request(request) -> None:
        path = urlparse(request.url).path
        if path not in {
            "/docs/index-tree",
            "/docs/doc",
            "/__smoke/subscope/manifest.json",
            "/docs/delete-preview",
            "/docs/delete-apply",
        }:
            return
        requests.append(
            {
                "method": request.method,
                "path": path,
                "body": request.post_data_json if request.post_data else None,
            }
        )

    page.on("request", record_request)
    page.goto(
        (
            f"{viewer_base_url}/docs/?scope=studio"
            f"&doc={SUBSCOPE_REPORT_DOC_ID}"
            f"&subdoc={SUBSCOPE_DOC_ID}"
        ),
        wait_until="domcontentloaded",
    )
    wait_for_manage_doc(page, SUBSCOPE_REPORT_DOC_TITLE, timeout_ms)
    page.wait_for_function(
        """() => {
            const report = document.querySelector('.docsViewerReport');
            const button = document.querySelector('[data-docs-subscope-delete="true"]');
            return report?.dataset.reportState === 'detail'
                && button
                && !button.disabled;
        }""",
        timeout=timeout_ms,
    )
    delete_button = page.locator('[data-docs-subscope-delete="true"]')
    baseline_counts = {
        path: sum(record["path"] == path for record in requests)
        for path in (
            "/docs/index-tree",
            "/docs/doc",
            "/__smoke/subscope/manifest.json",
        )
    }

    delete_button.click()
    modal = page.locator('[data-role="docs-viewer-management-modal"]')
    modal.wait_for(state="visible", timeout=timeout_ms)
    page.wait_for_function(
        """() => document.querySelector(
            '[data-role="docs-viewer-management-modal"] [data-role="modal-primary"]'
        )?.disabled === false""",
        timeout=timeout_ms,
    )
    modal_text = modal.inner_text()
    if SUBSCOPE_DOC_ID not in modal_text or f"studio/{SUBSCOPE_ID}" not in modal_text:
        raise AssertionError(f"Delete confirmation omitted the exact target: {modal_text!r}")
    if not Path(paths["target_path"]).is_file():
        raise AssertionError("write-free Delete preview removed the temporary source")
    if not Path(paths["target_payload_path"]).is_file():
        raise AssertionError("write-free Delete preview removed the temporary by-ID payload")

    modal.locator('[data-role="modal-primary"]').click()
    page.wait_for_function(
        """expectedSibling => {
            const report = document.querySelector('.docsViewerReport');
            const rowIds = Array.from(document.querySelectorAll(
                '.docsViewerReport__row[data-report-subdoc-id]'
            )).map(row => row.dataset.reportSubdocId);
            return report?.dataset.reportState === 'list'
                && rowIds.length === 1
                && rowIds[0] === expectedSibling
                && !new URL(location.href).searchParams.has('subdoc');
        }""",
        arg=SUBSCOPE_SIBLING_DOC_ID,
        timeout=timeout_ms,
    )

    target = {
        "scope": "studio",
        "sub_scope": SUBSCOPE_ID,
        "doc_id": SUBSCOPE_DOC_ID,
    }
    delete_requests = [
        record
        for record in requests
        if record["path"] in {"/docs/delete-preview", "/docs/delete-apply"}
    ]
    if len(delete_requests) != 2:
        raise AssertionError(f"Delete issued unexpected mutation requests: {delete_requests!r}")
    preview_request, apply_request = delete_requests
    if preview_request != {
        "method": "POST",
        "path": "/docs/delete-preview",
        "body": target,
    }:
        raise AssertionError(f"Delete preview target changed: {preview_request!r}")
    apply_body = apply_request.get("body")
    if (
        apply_request.get("method") != "POST"
        or apply_request.get("path") != "/docs/delete-apply"
        or not isinstance(apply_body, dict)
        or {
            key: apply_body.get(key)
            for key in ("scope", "sub_scope", "doc_id")
        }
        != target
        or apply_body.get("confirm") is not True
        or not re.fullmatch(r"sha256:[0-9a-f]{64}", str(apply_body.get("source_revision") or ""))
        or set(apply_body) != {
            "scope",
            "sub_scope",
            "doc_id",
            "source_revision",
            "confirm",
        }
    ):
        raise AssertionError(f"Delete apply target changed: {apply_request!r}")

    final_counts = {
        path: sum(record["path"] == path for record in requests)
        for path in baseline_counts
    }
    if final_counts != baseline_counts:
        raise AssertionError(
            "successful local row removal reloaded parent or child manifest: "
            f"before={baseline_counts!r}, after={final_counts!r}"
        )
    if Path(paths["target_path"]).exists() or Path(paths["target_payload_path"]).exists():
        raise AssertionError("confirmed Delete retained the exact temporary target")
    if Path(paths["sibling_path"]).read_bytes() != paths["sibling_source_before"]:
        raise AssertionError("confirmed Delete changed the retained sibling source")
    if Path(paths["sibling_payload_path"]).read_bytes() != paths["sibling_payload_before"]:
        raise AssertionError("confirmed Delete changed the retained sibling payload")
    if read_json(Path(paths["manifest_path"])) != {
        "docs": [
            {
                "doc_id": SUBSCOPE_SIBLING_DOC_ID,
                "title": SUBSCOPE_SIBLING_DOC_TITLE,
            }
        ]
    }:
        raise AssertionError("confirmed Delete did not reconcile the child manifest")
    parent_after = {
        path: path.read_bytes()
        for path in paths["parent_sentinels"]
    }
    if parent_after != paths["parent_before"]:
        raise AssertionError("confirmed Delete changed a parent or external sentinel")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout-ms", type=int, default=30000)
    args = parser.parse_args(argv)

    with tempfile.TemporaryDirectory(prefix="docs-viewer-subscope-delete-repo-") as temp_dir:
        repo_root = Path(temp_dir)
        paths = prepare_delete_repo(repo_root)
        viewer_server, viewer_base_url = start_server()
        mutation_server, management_base_url = start_mutation_server(repo_root)
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                page_errors: list[str] = []
                try:
                    page = browser.new_page()
                    page.on("pageerror", lambda error: page_errors.append(str(error)))
                    exercise_exact_delete(
                        page,
                        viewer_base_url,
                        management_base_url,
                        paths,
                        args.timeout_ms,
                    )
                finally:
                    browser.close()
            if page_errors:
                raise AssertionError(
                    f"page errors during sub-scope Delete route smoke: {page_errors!r}"
                )
        finally:
            mutation_server.shutdown()
            mutation_server.server_close()
            viewer_server.shutdown()
            viewer_server.server_close()
            PROJECTS_DIR.cleanup()
    print("Docs Viewer exact sub-scope Delete route workflow OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
