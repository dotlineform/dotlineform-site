#!/usr/bin/env python3
"""Smoke-check report New through the real manage route and temporary sources."""

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
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import Page, Route, sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "docs-viewer" / "services"))
sys.path.insert(0, str(REPO_ROOT / "docs-viewer" / "tests" / "fixtures"))

PROJECTS_DIR = tempfile.TemporaryDirectory(prefix="docs-viewer-subscope-create-route-")
os.environ["DOTLINEFORM_PROJECTS_BASE_DIR"] = PROJECTS_DIR.name
(Path(PROJECTS_DIR.name) / "docs-viewer").mkdir()
(Path(PROJECTS_DIR.name) / "data-sharing").mkdir()

import docs_management_mutations as mutations  # noqa: E402
import docs_source_model as source_model  # noqa: E402
import docs_write_rebuild  # noqa: E402
from docs_viewer_service import DocsViewerServer, DocsViewerServiceConfig  # noqa: E402
from docs_viewer_service_manage import start_server, wait_for_manage_doc  # noqa: E402
from repo_factory import (  # noqa: E402
    docs_scope_record,
    docs_sub_scope_record,
    read_json,
    write_docs_scope_config,
    write_site_tools_config,
    write_text,
)


REPORT_DOC_ID = "d-20000101-000000-c00000"
REPORT_TITLE = "Create Workflow Smoke Fixture"
SUB_SCOPE = "smoke-documents"
FIRST_DOC_ID = "d-20000101-000000-c00001"
SECOND_DOC_ID = "d-20000101-000000-c00002"
THIRD_DOC_ID = "d-20000101-000000-c00003"
FIRST_TITLE = "First Created Smoke Document"
SECOND_TITLE = "Second Created Smoke Document"
THIRD_TITLE = "Recoverable Created Smoke Document"
SECOND_BODY = "# Second Created Smoke Document\n\nSaved from NDS-3 route evidence.\n"


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


def prepare_create_repo(repo_root: Path) -> dict[str, object]:
    write_site_tools_config(repo_root)
    write_docs_scope_config(
        repo_root,
        [
            docs_scope_record(
                "studio",
                default_doc_id=REPORT_DOC_ID,
                sub_scopes=[
                    docs_sub_scope_record(
                        "studio",
                        SUB_SCOPE,
                        title="Smoke Documents",
                    )
                ],
            )
        ],
        {"recent_limit": 10},
    )

    report_path = (
        repo_root
        / f"docs-viewer/scopes/studio/source/documents/{REPORT_DOC_ID}.md"
    )
    write_text(
        report_path,
        source_text(
            REPORT_DOC_ID,
            REPORT_TITLE,
            (
                f"# {REPORT_TITLE}\n\n"
                ":::report\n"
                "id: docs_subscope\n"
                "access: public\n"
                f"sub_scope: {SUB_SCOPE}\n"
                ":::\n"
            ),
        ),
    )
    child_root = (
        repo_root
        / f"docs-viewer/scopes/studio/source/sub-scopes/{SUB_SCOPE}/documents"
    )
    child_root.mkdir(parents=True, exist_ok=True)

    build_link = repo_root / "docs-viewer/build"
    build_link.parent.mkdir(parents=True, exist_ok=True)
    build_link.symlink_to(REPO_ROOT / "docs-viewer/build", target_is_directory=True)
    docs_write_rebuild.rebuild_sub_scope_outputs(
        repo_root,
        "studio",
        SUB_SCOPE,
    )

    parent_sentinels = (
        repo_root / "docs-viewer/scopes/studio/published/documents/index-tree.json",
        repo_root / "docs-viewer/scopes/studio/published/documents/recent.json",
        repo_root / "docs-viewer/scopes/studio/published/search/index.json",
        repo_root / "studio/data/canonical/tags/tag-registry.json",
    )
    for index, path in enumerate(parent_sentinels):
        write_text(path, f"synthetic-parent-or-tag-sentinel-{index}\n")

    output_root = (
        repo_root
        / (
            "docs-viewer/scopes/studio/published/documents/sub-scopes/"
            f"{SUB_SCOPE}"
        )
    )
    return {
        "child_root": child_root,
        "manage_manifest": output_root / "manage-manifest.json",
        "public_manifest": output_root / "manifest.json",
        "by_id_root": output_root / "by-id",
        "parent_sentinels": parent_sentinels,
        "parent_before": {
            path: path.read_bytes()
            for path in parent_sentinels
        },
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


def fulfill_json(route: Route, payload: object, status: int = 200) -> None:
    route.fulfill(
        status=status,
        content_type="application/json",
        body=json.dumps(payload),
    )


def install_route_config(
    page: Page,
    management_base_url: str,
) -> None:
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
        services = manage.get("services") if isinstance(manage, dict) else None
        management = services.get("management") if isinstance(services, dict) else None
        source = services.get("source") if isinstance(services, dict) else None
        if not isinstance(management, dict) or not isinstance(source, dict):
            raise AssertionError("docs-manage route omitted write services")
        management["base_url"] = management_base_url
        source["base_url"] = management_base_url
        fulfill_json(route, payload, response.status)

    page.route(
        re.compile(
            r".*/docs-viewer/config/routes/docs-viewer-routes\.json(?:\?.*)?$"
        ),
        fulfill_route_config,
    )


def install_report_routes(page: Page, paths: dict[str, object]) -> None:
    report_payload = {
        "doc_id": REPORT_DOC_ID,
        "title": REPORT_TITLE,
        "added_date": "2000-01-01 00:00:00",
        "last_updated": "2000-01-01 00:00:00",
        "viewer_url": f"/docs/?scope=studio&doc={REPORT_DOC_ID}",
        "summary": "Synthetic empty collection for report New.",
        "report": {
            "id": "docs_subscope",
            "access": "public",
            "scope": None,
            "preset": None,
            "sub_scope": SUB_SCOPE,
        },
        "content_html": (
            f"<h1>{REPORT_TITLE}</h1>"
            "<p>Test-owned report content exercises exact collection creation.</p>"
            '<section class="docsViewerReport" data-docs-viewer-report-host '
            'aria-label="Document report"></section>'
        ),
    }
    index_payload = {
        "schema": "docs_index_tree_v1",
        "viewer_options": {
            "non_loadable_doc_ids": [],
            "manage_only_tree_root_ids": [],
        },
        "docs": [
            {
                "doc_id": REPORT_DOC_ID,
                "title": REPORT_TITLE,
                "content_url": (
                    f"/docs/doc?scope=studio&doc_id={REPORT_DOC_ID}"
                ),
            }
        ],
    }

    def fulfill_viewer_config(route: Route) -> None:
        response = route.fetch()
        payload = response.json()
        scopes = payload.get("scopes")
        studio = next(
            (
                record
                for record in scopes or []
                if isinstance(record, dict) and record.get("scope_id") == "studio"
            ),
            None,
        )
        if not isinstance(studio, dict):
            raise AssertionError("Docs Viewer config omitted Studio")
        studio["sub_scopes"] = [
            {
                "sub_scope": SUB_SCOPE,
                "title": "Smoke Documents",
                "manifest_url": "/__smoke/create/manifest.json",
                "by_id_url_base": "/__smoke/create/by-id",
            }
        ]
        fulfill_json(route, payload, response.status)

    def fulfill_manifest(route: Route) -> None:
        fulfill_json(route, read_json(Path(paths["manage_manifest"])))

    def fulfill_by_id(route: Route) -> None:
        doc_id = Path(urlparse(route.request.url).path).stem
        payload_path = Path(paths["by_id_root"]) / f"{doc_id}.json"
        if not payload_path.is_file():
            fulfill_json(route, {"error": "Not found"}, 404)
            return
        fulfill_json(route, read_json(payload_path))

    page.route(
        re.compile(
            r".*/docs-viewer/config/defaults/docs-viewer-config\.json(?:\?.*)?$"
        ),
        fulfill_viewer_config,
    )
    page.route(
        re.compile(r".*/__smoke/create/manifest\.json(?:\?.*)?$"),
        fulfill_manifest,
    )
    page.route(
        re.compile(r".*/__smoke/create/by-id/[^/?]+\.json(?:\?.*)?$"),
        fulfill_by_id,
    )
    page.route(
        re.compile(
            r".*/(?:docs/index-tree|docs-viewer/scopes/studio/published/"
            r"documents/index-tree\.json)(?:\?.*)?$"
        ),
        lambda route: fulfill_json(route, index_payload),
    )
    page.route(
        re.compile(r".*/docs/doc(?:\?.*)?$"),
        lambda route: fulfill_json(route, report_payload),
    )


def save_screenshot(page: Page, directory: Path | None, name: str) -> None:
    if directory is None:
        return
    directory.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(directory / f"{name}.png"), full_page=True)


def request_record(request) -> dict[str, object] | None:
    parsed = urlparse(request.url)
    tracked = {
        "/docs/index-tree",
        "/docs/doc",
        "/__smoke/create/manifest.json",
        "/docs/create",
        "/docs/source",
        "/docs/source/rebuild",
    }
    if parsed.path not in tracked and not parsed.path.startswith(
        "/__smoke/create/by-id/"
    ):
        return None
    query = parse_qs(parsed.query)
    return {
        "method": request.method,
        "path": parsed.path,
        "query": {
            key: values[0]
            for key in ("scope", "sub_scope", "doc_id")
            if (values := query.get(key))
        },
        "body": request.post_data_json if request.post_data else None,
    }


def exercise_report_create(
    page: Page,
    viewer_base_url: str,
    management_base_url: str,
    paths: dict[str, object],
    timeout_ms: int,
    screenshot_dir: Path | None,
) -> None:
    install_route_config(page, management_base_url)
    install_report_routes(page, paths)
    requests: list[dict[str, object]] = []

    def record_request(request) -> None:
        record = request_record(request)
        if record is not None:
            requests.append(record)

    page.on("request", record_request)
    page.goto(
        f"{viewer_base_url}/docs/?scope=studio&doc={REPORT_DOC_ID}",
        wait_until="domcontentloaded",
    )
    wait_for_manage_doc(page, REPORT_TITLE, timeout_ms)
    page.wait_for_function(
        """() => {
            const report = document.querySelector('.docsViewerReport');
            const newButton = document.querySelector(
                '[data-docs-subscope-new="true"]'
            );
            const actions = document.querySelector(
                '[data-docs-subscope-actions]'
            );
            return report?.dataset.reportState === 'list'
                && newButton
                && !newButton.disabled
                && actions?.disabled
                && document.querySelectorAll(
                    '[data-report-subdoc-id]'
                ).length === 0;
        }""",
        timeout=timeout_ms,
    )
    save_screenshot(page, screenshot_dir, "01-empty-list")

    new_button = page.locator('[data-docs-subscope-new="true"]')
    new_button.click()
    modal = page.locator('[data-role="docs-viewer-management-modal"]')
    modal.wait_for(state="visible", timeout=timeout_ms)
    title_input = modal.locator(".docsViewer__fieldInput")
    if title_input.input_value() != "New Doc":
        raise AssertionError("report New did not reuse the ordinary title modal")
    save_screenshot(page, screenshot_dir, "02-title-modal")
    modal.locator('button[data-role="modal-cancel"]').click()
    modal.wait_for(state="detached", timeout=timeout_ms)
    if any(record["path"] == "/docs/create" for record in requests):
        raise AssertionError("cancelling report New issued a create request")
    if list(Path(paths["child_root"]).glob("*.md")):
        raise AssertionError("cancelling report New created a temporary source")

    baseline_parent_requests = {
        path: sum(record["path"] == path for record in requests)
        for path in ("/docs/index-tree", "/docs/doc")
    }
    new_button.click()
    modal = page.locator('[data-role="docs-viewer-management-modal"]')
    modal.wait_for(state="visible", timeout=timeout_ms)
    modal.locator(".docsViewer__fieldInput").fill(FIRST_TITLE)
    modal.locator('[data-role="modal-primary"]').click()
    page.wait_for_function(
        """expected => {
            const url = new URL(location.href);
            return document.querySelector(
                '#docsViewerRoot'
            )?.dataset.documentDisplayMode === 'markdown-source'
                && url.searchParams.get('doc') === expected.parent
                && url.searchParams.get('subdoc') === expected.child
                && document.querySelector(
                    '.docsViewerSourceEditor__textarea'
                )?.value === expected.source;
        }""",
        arg={
            "parent": REPORT_DOC_ID,
            "child": FIRST_DOC_ID,
            "source": f"# {FIRST_TITLE}\n",
        },
        timeout=timeout_ms,
    )
    if {
        path: sum(record["path"] == path for record in requests)
        for path in baseline_parent_requests
    } != baseline_parent_requests:
        raise AssertionError("report New reloaded the parent index or document")
    save_screenshot(page, screenshot_dir, "03-created-source")

    page.locator("#docsViewerManageReturnToDocButton").click()
    page.wait_for_function(
        """expected => {
            const detail = document.querySelector('.docsReportDetail');
            return document.querySelector(
                '#docsViewerRoot'
            )?.dataset.documentDisplayMode === 'rendered-document'
                && detail?.dataset.reportSubdocId === expected.id
                && detail.querySelector('h1')?.textContent === expected.title;
        }""",
        arg={"id": FIRST_DOC_ID, "title": FIRST_TITLE},
        timeout=timeout_ms,
    )
    save_screenshot(page, screenshot_dir, "04-returned-detail")

    page.locator(".docsReportDetail__back").click()
    page.wait_for_function(
        """expected => {
            const report = document.querySelector('.docsViewerReport');
            const ids = Array.from(document.querySelectorAll(
                '.docsViewerReport__row[data-report-subdoc-id]'
            )).map(row => row.dataset.reportSubdocId);
            return report?.dataset.reportState === 'list'
                && ids.length === 1
                && ids[0] === expected
                && !new URL(location.href).searchParams.has('subdoc');
        }""",
        arg=FIRST_DOC_ID,
        timeout=timeout_ms,
    )

    page.locator('[data-docs-subscope-new="true"]').click()
    modal = page.locator('[data-role="docs-viewer-management-modal"]')
    modal.wait_for(state="visible", timeout=timeout_ms)
    modal.locator(".docsViewer__fieldInput").fill(SECOND_TITLE)
    modal.locator('[data-role="modal-primary"]').click()
    page.wait_for_function(
        """expected => {
            const textarea = document.querySelector(
                '.docsViewerSourceEditor__textarea'
            );
            const save = document.querySelector(
                '#docsViewerManageSourceSaveButton'
            );
            return document.querySelector(
                '#docsViewerRoot'
            )?.dataset.documentDisplayMode === 'markdown-source'
                && new URL(location.href).searchParams.get('subdoc') === expected.id
                && textarea?.value === expected.source
                && save
                && !save.disabled;
        }""",
        arg={
            "id": SECOND_DOC_ID,
            "source": f"# {SECOND_TITLE}\n",
        },
        timeout=timeout_ms,
    )
    page.locator(".docsViewerSourceEditor__textarea").fill(SECOND_BODY)
    page.locator("#docsViewerManageSourceSaveButton").click()
    page.wait_for_function(
        """expected => {
            const detail = document.querySelector('.docsReportDetail');
            return document.querySelector(
                '#docsViewerRoot'
            )?.dataset.documentDisplayMode === 'rendered-document'
                && detail?.dataset.reportSubdocId === expected
                && detail.textContent.includes('Saved from NDS-3 route evidence.');
        }""",
        arg=SECOND_DOC_ID,
        timeout=timeout_ms,
    )
    save_screenshot(page, screenshot_dir, "05-saved-detail")

    page.locator(".docsReportDetail__back").click()
    page.wait_for_function(
        """() => {
            const report = document.querySelector('.docsViewerReport');
            return report?.dataset.reportState === 'list'
                && document.querySelectorAll(
                    '.docsViewerReport__row[data-report-subdoc-id]'
                ).length === 2;
        }""",
        timeout=timeout_ms,
    )
    original_run_rebuild_command = docs_write_rebuild.run_rebuild_command
    try:
        docs_write_rebuild.run_rebuild_command = lambda _command, _root: {
            "returncode": 1,
            "stdout": "",
            "stderr": "forced NDS-3 committed-create rebuild failure",
        }
        page.locator('[data-docs-subscope-new="true"]').click()
        modal = page.locator('[data-role="docs-viewer-management-modal"]')
        modal.wait_for(state="visible", timeout=timeout_ms)
        modal.locator(".docsViewer__fieldInput").fill(THIRD_TITLE)
        modal.locator('[data-role="modal-primary"]').click()
        page.wait_for_function(
            """expected => {
                const status = document.querySelector('#docsViewerStatus');
                const root = document.querySelector('#docsViewerRoot');
                return status?.classList.contains('is-error')
                    && status.textContent.startsWith(expected)
                    && root?.dataset.documentDisplayMode === 'rendered-document'
                    && !new URL(location.href).searchParams.has('subdoc');
            }""",
            arg="Document created, but could not be opened in Source.",
            timeout=timeout_ms,
        )
        save_screenshot(page, screenshot_dir, "06-committed-recovery-copy")
    finally:
        docs_write_rebuild.run_rebuild_command = original_run_rebuild_command

    create_requests = [
        record
        for record in requests
        if record["path"] == "/docs/create"
    ]
    if create_requests != [
        {
            "method": "POST",
            "path": "/docs/create",
            "query": {},
            "body": {
                "scope": "studio",
                "title": FIRST_TITLE,
                "sub_scope": SUB_SCOPE,
            },
        },
        {
            "method": "POST",
            "path": "/docs/create",
            "query": {},
            "body": {
                "scope": "studio",
                "title": SECOND_TITLE,
                "sub_scope": SUB_SCOPE,
            },
        },
        {
            "method": "POST",
            "path": "/docs/create",
            "query": {},
            "body": {
                "scope": "studio",
                "title": THIRD_TITLE,
                "sub_scope": SUB_SCOPE,
            },
        },
    ]:
        raise AssertionError(f"report New request contract changed: {create_requests!r}")

    source_targets = [
        record["query"]
        for record in requests
        if record["path"] == "/docs/source" and record["method"] == "GET"
    ]
    expected_targets = [
        {
            "scope": "studio",
            "sub_scope": SUB_SCOPE,
            "doc_id": FIRST_DOC_ID,
        },
        {
            "scope": "studio",
            "sub_scope": SUB_SCOPE,
            "doc_id": SECOND_DOC_ID,
        },
    ]
    if source_targets != expected_targets:
        raise AssertionError(f"Source entry targets changed: {source_targets!r}")

    first_source = Path(paths["child_root"]) / f"{FIRST_DOC_ID}.md"
    second_source = Path(paths["child_root"]) / f"{SECOND_DOC_ID}.md"
    third_source = Path(paths["child_root"]) / f"{THIRD_DOC_ID}.md"
    first_metadata, first_body = source_model.parse_source(first_source)
    second_metadata, second_body = source_model.parse_source(second_source)
    third_metadata, third_body = source_model.parse_source(third_source)
    if (
        first_metadata.get("title") != FIRST_TITLE
        or source_model.doc_is_publishable(first_metadata) is not True
        or first_body != f"# {FIRST_TITLE}\n"
    ):
        raise AssertionError("first created source did not retain its generated start")
    if (
        second_metadata.get("title") != SECOND_TITLE
        or source_model.doc_is_publishable(second_metadata) is not True
        or second_body != SECOND_BODY
    ):
        raise AssertionError("second created source did not retain its saved body")
    if (
        third_metadata.get("title") != THIRD_TITLE
        or source_model.doc_is_publishable(third_metadata) is not True
        or third_body != f"# {THIRD_TITLE}\n"
    ):
        raise AssertionError(
            "committed recovery source did not retain its generated start"
        )

    manage_docs = read_json(Path(paths["manage_manifest"])).get("docs")
    if [
        (record.get("doc_id"), record.get("title"), record.get("publishable"))
        for record in manage_docs or []
    ] != [
        (FIRST_DOC_ID, FIRST_TITLE, None),
        (SECOND_DOC_ID, SECOND_TITLE, None),
    ]:
        raise AssertionError(f"manage manifest did not retain both creates: {manage_docs!r}")
    public_docs = read_json(Path(paths["public_manifest"])).get("docs")
    if [
        (record.get("doc_id"), record.get("title"))
        for record in public_docs or []
    ] != [
        (FIRST_DOC_ID, FIRST_TITLE),
        (SECOND_DOC_ID, SECOND_TITLE),
    ]:
        raise AssertionError(
            "created documents did not preserve the configured public eligibility "
            f"default: {public_docs!r}"
        )
    parent_after = {
        path: path.read_bytes()
        for path in paths["parent_sentinels"]
    }
    if parent_after != paths["parent_before"]:
        raise AssertionError("report New changed parent discovery or Tag Registry sentinels")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout-ms", type=int, default=30000)
    parser.add_argument("--screenshot-dir", type=Path)
    args = parser.parse_args(argv)

    created_ids = iter((FIRST_DOC_ID, SECOND_DOC_ID, THIRD_DOC_ID))
    original_allocate_doc_id = mutations.source_model.allocate_doc_id
    mutations.source_model.allocate_doc_id = lambda _timestamp, _used: next(
        created_ids
    )
    try:
        with tempfile.TemporaryDirectory(
            prefix="docs-viewer-subscope-create-repo-"
        ) as temp_dir:
            repo_root = Path(temp_dir)
            paths = prepare_create_repo(repo_root)
            viewer_server, viewer_base_url = start_server()
            mutation_server, management_base_url = start_mutation_server(repo_root)
            try:
                with sync_playwright() as playwright:
                    browser = playwright.chromium.launch(headless=True)
                    page_errors: list[str] = []
                    try:
                        page = browser.new_page(viewport={"width": 1440, "height": 1000})
                        page.on(
                            "pageerror",
                            lambda error: page_errors.append(str(error)),
                        )
                        exercise_report_create(
                            page,
                            viewer_base_url,
                            management_base_url,
                            paths,
                            args.timeout_ms,
                            args.screenshot_dir,
                        )
                    finally:
                        browser.close()
                if page_errors:
                    raise AssertionError(
                        "page errors during sub-scope create route smoke: "
                        f"{page_errors!r}"
                    )
            finally:
                mutation_server.shutdown()
                mutation_server.server_close()
                viewer_server.shutdown()
                viewer_server.server_close()
                PROJECTS_DIR.cleanup()
    finally:
        mutations.source_model.allocate_doc_id = original_allocate_doc_id

    print("Docs Viewer sub-scope report New route workflow OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
