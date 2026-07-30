#!/usr/bin/env python3
"""Smoke-check consolidated Docs Import on the real Docs Viewer manage route."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import tempfile
from urllib.parse import urlparse

from playwright.sync_api import Page, Route, sync_playwright


PROJECTS_DIR = tempfile.TemporaryDirectory(prefix="docs-viewer-import-route-")
os.environ["DOTLINEFORM_PROJECTS_BASE_DIR"] = PROJECTS_DIR.name
(Path(PROJECTS_DIR.name) / "docs-viewer").mkdir()
(Path(PROJECTS_DIR.name) / "data-sharing").mkdir()

from docs_import_multi_selection_modules import (  # noqa: E402
    blocked_candidate,
    ordinary_candidate,
    returned_candidate,
)
from docs_viewer_service_manage import (  # noqa: E402
    DOCS_VIEWER_DOC_ID,
    DOCS_VIEWER_DOC_TITLE,
    SUBSCOPE_DOC_ID,
    SUBSCOPE_DOC_TITLE,
    SUBSCOPE_ID,
    SUBSCOPE_REPORT_DOC_ID,
    install_smoke_document_routes,
    start_server,
    wait_for_manage_doc,
    wait_for_subscope_detail,
)


PARENT_SOURCE = "parent-source.md"
CHILD_SOURCE = "child-source.html"
REVIEWABLE_PACKAGE = "20260730-120000-document-content.jsonl"
IMPORT_ONLY_PACKAGE = "20260730-120100-document-content.jsonl"
EDITED_SOURCE_FOLDER = "20260730-120200-document-content"
BLOCKED_PACKAGE = "blocked-returned.jsonl"
IGNORED_MEDIA = "cover.png"


def edited_candidate() -> dict[str, object]:
    return {
        "filename": EDITED_SOURCE_FOLDER,
        "display_name": f"{EDITED_SOURCE_FOLDER} (reviewed)",
        "source_format": "edited_review_sources",
        "candidate_kind": "edited_review_source",
        "validation_state": "ready",
        "target_mode": "manifest_collection",
        "target": {"scope": "studio", "sub_scope": SUBSCOPE_ID},
        "target_label": "Studio / Smoke Documents",
        "scope": "studio",
        "sub_scope": SUBSCOPE_ID,
        "supports_docs_review": False,
        "supports_return_import": True,
        "docs_review_enabled": False,
        "docs_review_disabled_reason": "edited_review_source",
        "import_enabled": True,
        "import_disabled_reason": "",
        "disabled_reason": "",
        "diagnostics": [],
        "document_count": 1,
    }


def candidate_inventory() -> list[dict[str, object]]:
    blocked = blocked_candidate()
    blocked["filename"] = BLOCKED_PACKAGE
    import_only = returned_candidate(
        IMPORT_ONLY_PACKAGE,
        target={"scope": "library"},
        target_label="Library",
        supports_review=True,
        supports_import=True,
    )
    import_only["docs_review_enabled"] = False
    import_only["docs_review_disabled_reason"] = "review_materialization_unavailable"
    import_only["diagnostics"] = [
        {
            "code": "review_materialization_unavailable",
            "message": "Docs Review materialization is unavailable for this package.",
        }
    ]
    return [
        ordinary_candidate(PARENT_SOURCE, "markdown"),
        ordinary_candidate(CHILD_SOURCE, "html"),
        returned_candidate(
            REVIEWABLE_PACKAGE,
            target={"scope": "library"},
            target_label="Library",
            supports_review=True,
            supports_import=True,
        ),
        import_only,
        edited_candidate(),
        blocked,
    ]


def fulfill_json(route: Route, payload: object, *, status: int = 200) -> None:
    route.fulfill(
        status=status,
        content_type="application/json",
        body=json.dumps(payload),
    )


def collection_preview(
    *,
    source_format: str,
    target: dict[str, str],
) -> dict[str, object]:
    return {
        "ok": True,
        "collection": True,
        "preview_only": True,
        "source_format": source_format,
        "target": target,
        "package": {
            "export_id": "ds_20260730T120000Z",
            "source_sha256": "a" * 64,
            "trusted_metadata_sha256": "b" * 64,
        },
        "blockers": [],
        "warnings": [],
        "counts": {
            "records": 1,
            "creates": 0,
            "collisions": 1,
            "record_errors": 0,
            "media_plans": 0,
        },
        "planned_identities": [{"record_index": 0, "doc_id": SUBSCOPE_DOC_ID}],
        "planned_actions": [
            {
                "record_index": 0,
                "doc_id": SUBSCOPE_DOC_ID,
                "action": "overwrite",
            }
        ],
        "records": [
            {
                "record_index": 0,
                "doc_id": SUBSCOPE_DOC_ID,
                "title": SUBSCOPE_DOC_TITLE,
                "action": "overwrite",
            }
        ],
    }


def collection_result(
    *,
    filename: str,
    source_format: str,
    target: dict[str, str],
    viewer_url: str,
) -> dict[str, object]:
    return {
        "ok": True,
        "collection": True,
        "preview_only": False,
        "confirmed": True,
        "source_format": source_format,
        "target": target,
        "viewer_url": viewer_url,
        "staged_filename": filename,
        "outcome": "completed",
        "counts": {
            "created": 0,
            "overwritten": 1,
            "failed": 0,
            "not_attempted": 0,
        },
        "records": [
            {
                "record_index": 0,
                "doc_id": SUBSCOPE_DOC_ID,
                "title": SUBSCOPE_DOC_TITLE,
                "status": "overwritten",
                "warnings": [],
            }
        ],
        "warnings": [],
    }


def install_import_routes(
    page: Page,
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[str]]:
    imports: list[dict[str, object]] = []
    reviews: list[dict[str, object]] = []
    request_paths: list[str] = []
    review_attempt = 0
    candidates = candidate_inventory()

    page.on("request", lambda request: request_paths.append(urlparse(request.url).path))
    page.route(
        re.compile(r".*/docs/import-source-files(?:\?.*)?$"),
        lambda route: fulfill_json(
            route,
            {
                "ok": True,
                "available": True,
                "files": [{"filename": IGNORED_MEDIA}],
                "ignored_files": [{"filename": IGNORED_MEDIA, "reason": "media"}],
                "candidates": candidates,
            },
        ),
    )

    def fulfill_import(route: Route) -> None:
        body = route.request.post_data_json
        imports.append(body)
        filename = str(body.get("staged_filename") or "")
        if filename == PARENT_SOURCE:
            fulfill_json(
                route,
                {
                    "ok": True,
                    "collection": False,
                    "preview_only": False,
                    "staged_filename": filename,
                    "doc_id": DOCS_VIEWER_DOC_ID,
                    "target": {"scope": "studio", "doc_id": DOCS_VIEWER_DOC_ID},
                    "viewer_url": (
                        f"/docs/?scope=studio&doc={DOCS_VIEWER_DOC_ID}"
                    ),
                    "source_format": "markdown",
                    "summary_text": f"Imported {filename}.",
                    "import_preview": {
                        "source_format": "markdown",
                        "source_stats": {"chars": 40, "links": 0, "images": 0},
                        "warnings": [],
                    },
                },
            )
            return
        if filename == CHILD_SOURCE:
            fulfill_json(
                route,
                {
                    "ok": True,
                    "collection": False,
                    "preview_only": False,
                    "staged_filename": filename,
                    "doc_id": SUBSCOPE_DOC_ID,
                    "target": {
                        "scope": "studio",
                        "sub_scope": SUBSCOPE_ID,
                        "doc_id": SUBSCOPE_DOC_ID,
                    },
                    "viewer_url": (
                        f"/docs/?scope=studio&doc={SUBSCOPE_REPORT_DOC_ID}"
                        f"&subdoc={SUBSCOPE_DOC_ID}"
                    ),
                    "source_format": "html",
                    "summary_text": f"Imported {filename}.",
                    "import_preview": {
                        "source_format": "html",
                        "source_stats": {"chars": 50, "links": 0, "images": 0},
                        "warnings": [],
                    },
                },
            )
            return
        if filename in {REVIEWABLE_PACKAGE, IMPORT_ONLY_PACKAGE}:
            target = {"scope": "library"}
            if body.get("preview_only") is True:
                fulfill_json(
                    route,
                    collection_preview(
                        source_format="data_sharing_documents",
                        target=target,
                    ),
                )
                return
            fulfill_json(
                route,
                collection_result(
                    filename=filename,
                    source_format="data_sharing_documents",
                    target=target,
                    viewer_url="/docs/?scope=library",
                ),
            )
            return
        if filename == EDITED_SOURCE_FOLDER:
            target = {"scope": "studio", "sub_scope": SUBSCOPE_ID}
            if body.get("preview_only") is True:
                fulfill_json(
                    route,
                    collection_preview(
                        source_format="edited_review_sources",
                        target=target,
                    ),
                )
                return
            fulfill_json(
                route,
                collection_result(
                    filename=filename,
                    source_format="edited_review_sources",
                    target=target,
                    viewer_url=(
                        f"/docs/?scope=studio&doc={SUBSCOPE_REPORT_DOC_ID}"
                    ),
                ),
            )
            return
        fulfill_json(
            route,
            {"ok": False, "error": f"Unexpected import candidate: {filename}"},
            status=400,
        )

    page.route(re.compile(r".*/docs/import-source(?:\?.*)?$"), fulfill_import)

    def fulfill_review(route: Route) -> None:
        nonlocal review_attempt
        review_attempt += 1
        reviews.append(route.request.post_data_json)
        if review_attempt == 1:
            fulfill_json(
                route,
                {"ok": False, "error": "Synthetic review preparation failure."},
                status=500,
            )
            return
        fulfill_json(
            route,
            {
                "ok": True,
                "review_package_id": "20260730-120000-document-content",
                "review_url": (
                    "/docs-review/"
                    "?package=20260730-120000-document-content"
                ),
                "review_existing": True,
                "summary_text": "Docs Review package already exists.",
            },
        )

    page.route(
        re.compile(r".*/docs/packages/returned/review(?:\?.*)?$"),
        fulfill_review,
    )
    return imports, reviews, request_paths


def open_import(page: Page, timeout_ms: int) -> None:
    page.locator("#docsViewerManageImportButton").evaluate("button => button.click()")
    page.wait_for_function(
        """() => {
            const modal = document.querySelector('#docsViewerImportModal');
            const root = document.querySelector('#docsHtmlImportRoot');
            return modal && !modal.hidden
                && root?.dataset.studioReady === 'true'
                && root?.dataset.studioBusy === 'false';
        }""",
        timeout=timeout_ms,
    )


def close_import(page: Page) -> None:
    page.locator("#docsViewerImportCancelButton").evaluate("button => button.click()")


def select_candidate(page: Page, filename: str) -> None:
    page.locator("#docsHtmlImportFileSelect").select_option(filename)


def wait_for_import_idle(page: Page, timeout_ms: int) -> None:
    page.wait_for_function(
        "() => document.querySelector('#docsHtmlImportRoot')?.dataset.studioBusy === 'false'",
        timeout=timeout_ms,
    )


def confirm_collection(page: Page, timeout_ms: int) -> None:
    page.locator("#docsHtmlImportRun").click()
    page.locator("#docsViewerImportCollectionModal:not([hidden])").wait_for(
        timeout=timeout_ms,
    )
    page.locator("#docsImportCollectionConfirm").click()
    wait_for_import_idle(page, timeout_ms)


def close_collection(page: Page) -> None:
    page.locator("#docsImportCollectionClose").click()


def assert_inventory_surface(page: Page, request_paths: list[str]) -> None:
    expected = [
        PARENT_SOURCE,
        CHILD_SOURCE,
        REVIEWABLE_PACKAGE,
        IMPORT_ONLY_PACKAGE,
        EDITED_SOURCE_FOLDER,
        BLOCKED_PACKAGE,
    ]
    actual = page.locator("#docsHtmlImportFileSelect option").evaluate_all(
        "(options) => options.map(option => option.value)",
    )
    if actual != expected:
        state = page.evaluate(
            """() => ({
                boot: document.querySelector('#docsHtmlImportBootStatus')?.textContent || '',
                bootState: document.querySelector('#docsHtmlImportBootStatus')?.dataset.state || '',
                status: document.querySelector('#docsHtmlImportStatus')?.textContent || '',
                statusState: document.querySelector('#docsHtmlImportStatus')?.dataset.state || ''
            })"""
        )
        raise AssertionError(
            f"candidate inventory changed: {actual!r}; state={state!r}; "
            f"requests={request_paths!r}"
        )
    if IGNORED_MEDIA in actual:
        raise AssertionError("ignored media leaked into the Import chooser")
    if page.locator("#docsHtmlImportTypeSelect").count():
        raise AssertionError("consolidated Import restored a source-type selector")
    if page.locator("#docsHtmlImportScopeSelect").count():
        raise AssertionError("consolidated Import restored a destination selector")


def exercise_parent_import(
    page: Page,
    base_url: str,
    request_paths: list[str],
    timeout_ms: int,
) -> None:
    page.goto(
        f"{base_url}/docs/?scope=studio&doc={DOCS_VIEWER_DOC_ID}",
        wait_until="domcontentloaded",
    )
    wait_for_manage_doc(page, DOCS_VIEWER_DOC_TITLE, timeout_ms)
    open_import(page, timeout_ms)
    assert_inventory_surface(page, request_paths)
    index_reads = request_paths.count("/docs/index-tree")
    select_candidate(page, PARENT_SOURCE)
    page.locator("#docsHtmlImportRun").click()
    wait_for_import_idle(page, timeout_ms)
    destination = page.locator("[data-doc-destination-link]")
    expected_url = f"/docs/?scope=studio&doc={DOCS_VIEWER_DOC_ID}"
    if destination.get_attribute("href") != expected_url:
        raise AssertionError("ordinary parent result omitted its exact document link")
    if request_paths.count("/docs/index-tree") <= index_reads:
        raise AssertionError("ordinary parent import did not refresh the parent route")
    close_import(page)


def exercise_child_import(
    page: Page,
    base_url: str,
    request_paths: list[str],
    timeout_ms: int,
) -> None:
    page.goto(
        (
            f"{base_url}/docs/?scope=studio&doc={SUBSCOPE_REPORT_DOC_ID}"
            f"&subdoc={SUBSCOPE_DOC_ID}"
        ),
        wait_until="domcontentloaded",
    )
    wait_for_subscope_detail(
        page,
        title=SUBSCOPE_DOC_TITLE,
        version=1,
        timeout_ms=timeout_ms,
    )
    detail_reads = request_paths.count(
        f"/__smoke/subscope/by-id/{SUBSCOPE_DOC_ID}.json"
    )
    open_import(page, timeout_ms)
    select_candidate(page, CHILD_SOURCE)
    child_destination = (
        page.locator("#docsHtmlImportCandidateDestination").inner_text().strip()
    )
    if child_destination != "studio / Smoke Documents":
        raise AssertionError(
            "ordinary child source did not freeze the displayed child collection: "
            f"{child_destination!r}"
        )
    page.locator("#docsHtmlImportRun").click()
    wait_for_import_idle(page, timeout_ms)
    expected_url = (
        f"/docs/?scope=studio&doc={SUBSCOPE_REPORT_DOC_ID}"
        f"&subdoc={SUBSCOPE_DOC_ID}"
    )
    if page.locator("[data-doc-destination-link]").get_attribute("href") != expected_url:
        raise AssertionError("ordinary child result omitted its exact subdocument link")
    if request_paths.count(
        f"/__smoke/subscope/by-id/{SUBSCOPE_DOC_ID}.json"
    ) <= detail_reads:
        raise AssertionError("ordinary child import did not refresh its exact detail")
    if urlparse(page.url).query != urlparse(f"http://local{expected_url}").query:
        raise AssertionError("ordinary child refresh changed the displayed target")
    close_import(page)


def exercise_review_handoff(
    page: Page,
    reviews: list[dict[str, object]],
    timeout_ms: int,
) -> None:
    open_import(page, timeout_ms)
    select_candidate(page, REVIEWABLE_PACKAGE)
    if page.locator("#docsHtmlImportReview").is_disabled():
        raise AssertionError("reviewable returned package did not enable Docs Review")
    with page.expect_popup() as failed_popup_info:
        page.locator("#docsHtmlImportReview").click()
    failed_popup_info.value.wait_for_event("close")
    wait_for_import_idle(page, timeout_ms)
    if page.locator("#docsHtmlImportStatus").get_attribute("data-state") != "error":
        raise AssertionError("failed Docs Review handoff did not remain retryable")
    with page.expect_popup() as popup_info:
        page.locator("#docsHtmlImportReview").click()
    popup = popup_info.value
    popup.wait_for_url("**/docs-review/?package=20260730-120000-document-content")
    wait_for_import_idle(page, timeout_ms)
    popup.close()
    if reviews != [
        {
            "scope": "library",
            "staged_filename": REVIEWABLE_PACKAGE,
            "dry_run": False,
        },
        {
            "scope": "library",
            "staged_filename": REVIEWABLE_PACKAGE,
            "dry_run": False,
        },
    ]:
        raise AssertionError(f"Docs Review retry changed its exact candidate: {reviews!r}")
    close_import(page)


def exercise_import_only_package(
    page: Page,
    imports: list[dict[str, object]],
    timeout_ms: int,
) -> None:
    open_import(page, timeout_ms)
    select_candidate(page, IMPORT_ONLY_PACKAGE)
    if not page.locator("#docsHtmlImportReview").is_disabled():
        raise AssertionError("import-only returned package enabled Docs Review")
    route_before = page.url
    request_count = len(imports)
    confirm_collection(page, timeout_ms)
    package_requests = imports[request_count:]
    request_contracts = [
        {
            "scope": request.get("scope"),
            "staged_filename": request.get("staged_filename"),
            "preview_only": request.get("preview_only"),
            "confirm": request.get("confirm"),
        }
        for request in package_requests
    ]
    if request_contracts != [
        {
            "scope": "library",
            "staged_filename": IMPORT_ONLY_PACKAGE,
            "preview_only": True,
            "confirm": None,
        },
        {
            "scope": "library",
            "staged_filename": IMPORT_ONLY_PACKAGE,
            "preview_only": False,
            "confirm": True,
        },
    ]:
        raise AssertionError(
            "import-only returned package changed preview/apply routing: "
            f"{package_requests!r}"
        )
    apply_activity = package_requests[1].get("activity_context")
    if not isinstance(apply_activity, dict) or (
        apply_activity.get("action_id") != "import-docs-collection"
        or apply_activity.get("control_id") != "docsImportCollectionConfirm"
    ):
        raise AssertionError(
            f"collection confirmation lost its action attribution: {apply_activity!r}"
        )
    destination = page.locator("[data-collection-destination-link]")
    if destination.get_attribute("href") != "/docs/?scope=library":
        raise AssertionError("cross-context package result omitted its explicit collection link")
    if page.url != route_before:
        raise AssertionError("cross-context package import navigated away from the displayed collection")
    close_collection(page)


def exercise_edited_folder_and_blocked_candidate(
    page: Page,
    imports: list[dict[str, object]],
    request_paths: list[str],
    timeout_ms: int,
) -> None:
    open_import(page, timeout_ms)
    select_candidate(page, EDITED_SOURCE_FOLDER)
    manifest_reads = request_paths.count("/__smoke/subscope/manifest.json")
    request_count = len(imports)
    confirm_collection(page, timeout_ms)
    if [request["staged_filename"] for request in imports[request_count:]] != [
        EDITED_SOURCE_FOLDER,
        EDITED_SOURCE_FOLDER,
    ]:
        raise AssertionError("edited review-source folder did not preserve its staged identity")
    expected_url = f"/docs/?scope=studio&doc={SUBSCOPE_REPORT_DOC_ID}"
    if (
        page.locator("[data-collection-destination-link]").get_attribute("href")
        != expected_url
    ):
        raise AssertionError("edited folder result omitted its explicit report link")
    if request_paths.count("/__smoke/subscope/manifest.json") <= manifest_reads:
        raise AssertionError("same-context edited folder import did not refresh its collection")
    close_collection(page)

    open_import(page, timeout_ms)
    select_candidate(page, BLOCKED_PACKAGE)
    if not page.locator("#docsHtmlImportRun").is_disabled():
        raise AssertionError("blocked manifest enabled Import")
    if not page.locator("#docsHtmlImportReview").is_disabled():
        raise AssertionError("blocked manifest enabled Docs Review")
    if "Trusted export metadata is unavailable." not in page.locator(
        "#docsHtmlImportCandidateNote"
    ).inner_text():
        raise AssertionError("blocked manifest omitted its server diagnostic")
    blocked_request_count = len(imports)
    page.locator("#docsHtmlImportRun").evaluate("button => button.click()")
    if len(imports) != blocked_request_count:
        raise AssertionError("blocked manifest issued an import request")
    close_import(page)


def assert_request_matrix(imports: list[dict[str, object]]) -> None:
    ordinary = imports[:2]
    ordinary_contracts = [
        {
            "scope": request.get("scope"),
            "sub_scope": request.get("sub_scope"),
            "staged_filename": request.get("staged_filename"),
            "include_prompt_meta": request.get("include_prompt_meta"),
            "preview_only": request.get("preview_only"),
        }
        for request in ordinary
    ]
    if ordinary_contracts != [
        {
            "scope": "studio",
            "sub_scope": None,
            "staged_filename": PARENT_SOURCE,
            "include_prompt_meta": False,
            "preview_only": False,
        },
        {
            "scope": "studio",
            "sub_scope": SUBSCOPE_ID,
            "staged_filename": CHILD_SOURCE,
            "include_prompt_meta": False,
            "preview_only": False,
        },
    ]:
        raise AssertionError(f"ordinary parent/child requests changed: {ordinary!r}")
    for request in ordinary:
        activity = request.get("activity_context")
        if not isinstance(activity, dict) or (
            activity.get("action_id") != "import-docs-source"
            or activity.get("control_id") != "docsHtmlImportRun"
        ):
            raise AssertionError(
                f"ordinary import lost its action attribution: {activity!r}"
            )
    filenames = [str(request.get("staged_filename") or "") for request in imports]
    if BLOCKED_PACKAGE in filenames or IGNORED_MEDIA in filenames:
        raise AssertionError(f"blocked or ignored candidates reached Import: {filenames!r}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout-ms", type=int, default=15000)
    args = parser.parse_args(argv)

    server, base_url = start_server()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page_errors: list[str] = []
            try:
                page = browser.new_page()
                page.on("pageerror", lambda error: page_errors.append(str(error)))
                install_smoke_document_routes(page, include_subscope_report=True)
                imports, reviews, request_paths = install_import_routes(page)
                exercise_parent_import(page, base_url, request_paths, args.timeout_ms)
                exercise_child_import(page, base_url, request_paths, args.timeout_ms)
                exercise_review_handoff(page, reviews, args.timeout_ms)
                exercise_import_only_package(page, imports, args.timeout_ms)
                exercise_edited_folder_and_blocked_candidate(
                    page,
                    imports,
                    request_paths,
                    args.timeout_ms,
                )
                assert_request_matrix(imports)
            finally:
                browser.close()
        if page_errors:
            raise AssertionError(
                f"page errors during consolidated Import route smoke: {page_errors!r}"
            )
    finally:
        server.shutdown()
        server.server_close()
        PROJECTS_DIR.cleanup()
    print("Docs Viewer real manage-route consolidated Import workflow OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
