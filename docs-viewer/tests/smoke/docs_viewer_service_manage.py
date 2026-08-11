#!/usr/bin/env python3
"""Smoke-check the standalone Docs Viewer service manage route."""

from __future__ import annotations

import argparse
from dataclasses import replace
import json
import re
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
from docs_viewer_theme_smoke_helpers import (  # noqa: E402
    assert_docs_viewer_theme_pair,
    assert_docs_viewer_theme_state,
    read_docs_viewer_theme_state,
)
from tests.smoke.route_ready_helpers import wait_for_route_ready  # noqa: E402


DOCS_VIEWER_DOC_ID = "d-20000101-000000-000001"
DOCS_VIEWER_DOC_TITLE = "Docs Viewer Manage Smoke Fixture"
INLINE_MERMAID_DOC_ID = "d-20000101-000000-000002"
INLINE_MERMAID_DOC_TITLE = "Inline Mermaid Smoke Fixture"
INLINE_MERMAID_LINKED_DOC_ID = "d-20000101-000000-000003"
INLINE_MERMAID_LINKED_DOC_TITLE = "Diagram-free Smoke Fixture"
SUBSCOPE_REPORT_DOC_ID = "d-20000101-000000-000004"
SUBSCOPE_REPORT_DOC_TITLE = "Sub-Scope Editing Smoke Fixture"
SUBSCOPE_ID = "smoke-documents"
SUBSCOPE_DOC_ID = "d-20000101-000000-000005"
SUBSCOPE_DOC_TITLE = "Smoke Detail"
SUBSCOPE_SIBLING_DOC_ID = "d-20000101-000000-000006"
SUBSCOPE_SIBLING_DOC_TITLE = "Retained Smoke Sibling"
INVALID_SUBSCOPE_DOC_ID = "d-20000101-000000-invalid"


def smoke_document_payloads(
    *,
    include_subscope_report: bool = False,
) -> dict[str, dict[str, object]]:
    payloads: dict[str, dict[str, object]] = {
        DOCS_VIEWER_DOC_ID: {
            "doc_id": DOCS_VIEWER_DOC_ID,
            "title": DOCS_VIEWER_DOC_TITLE,
            "added_date": "2000-01-01 00:00:00",
            "last_updated": "2000-01-01 00:00:00",
            "viewer_url": f"/docs/?scope=studio&doc={DOCS_VIEWER_DOC_ID}",
            "summary": "Synthetic diagram-free document for the manage-route smoke.",
            "content_html": (
                f"<h1>{DOCS_VIEWER_DOC_TITLE}</h1>"
                "<p>Test-owned content exercises the managed document route.</p>"
            ),
        },
        INLINE_MERMAID_DOC_ID: {
            "doc_id": INLINE_MERMAID_DOC_ID,
            "title": INLINE_MERMAID_DOC_TITLE,
            "added_date": "2000-01-01 00:00:01",
            "last_updated": "2000-01-01 00:00:01",
            "viewer_url": f"/docs/?scope=studio&doc={INLINE_MERMAID_DOC_ID}",
            "summary": "Synthetic inline Mermaid document for the manage-route smoke.",
            "content_html": (
                f"<h1>{INLINE_MERMAID_DOC_TITLE}</h1>"
                "<p>Before the inline diagram.</p>"
                '<pre><code class="language-mermaid">flowchart LR\n'
                "    accTitle: Inline Mermaid diagram lifecycle\n"
                "    accDescr: A document mount registers a diagram and releases it on navigation.\n"
                '    Mount["Mount document"] --&gt; Release["Release document"]\n'
                "</code></pre>"
                "<p>After the inline diagram.</p>"
                f'<p><a href="/docs/?scope=studio&amp;doc={INLINE_MERMAID_LINKED_DOC_ID}">'
                f"{INLINE_MERMAID_LINKED_DOC_TITLE}</a></p>"
            ),
        },
        INLINE_MERMAID_LINKED_DOC_ID: {
            "doc_id": INLINE_MERMAID_LINKED_DOC_ID,
            "title": INLINE_MERMAID_LINKED_DOC_TITLE,
            "added_date": "2000-01-01 00:00:02",
            "last_updated": "2000-01-01 00:00:02",
            "viewer_url": f"/docs/?scope=studio&doc={INLINE_MERMAID_LINKED_DOC_ID}",
            "summary": "Synthetic diagram-free navigation target for the manage-route smoke.",
            "content_html": (
                f"<h1>{INLINE_MERMAID_LINKED_DOC_TITLE}</h1>"
                "<p>This linked fixture deliberately contains no diagram.</p>"
            ),
        },
    }
    if include_subscope_report:
        payloads[SUBSCOPE_REPORT_DOC_ID] = {
            "doc_id": SUBSCOPE_REPORT_DOC_ID,
            "title": SUBSCOPE_REPORT_DOC_TITLE,
            "added_date": "2000-01-01 00:00:03",
            "last_updated": "2000-01-01 00:00:03",
            "viewer_url": f"/docs/?scope=studio&doc={SUBSCOPE_REPORT_DOC_ID}",
            "summary": "Synthetic report for sub-scope editing integration.",
            "report": {
                "id": "docs_subscope",
                "access": "public",
                "scope": None,
                "preset": None,
                "sub_scope": SUBSCOPE_ID,
            },
            "content_html": (
                f"<h1>{SUBSCOPE_REPORT_DOC_TITLE}</h1>"
                "<p>Test-owned report content exercises managed sub-scope editing.</p>"
                '<section class="docsViewerReport" data-docs-viewer-report-host '
                'aria-label="Document report"></section>'
            ),
        }
    return payloads


def install_smoke_document_routes(
    page: Page,
    *,
    include_subscope_report: bool = False,
    include_subscope_sibling: bool = False,
) -> None:
    payloads = smoke_document_payloads(
        include_subscope_report=include_subscope_report,
    )
    subscope_state: dict[str, object] = {
        "title": SUBSCOPE_DOC_TITLE,
        "summary": "Test-owned sub-scope metadata.",
        "date": "2000-01-01",
        "date_display": "January 2000",
        "ui_status": "draft",
        "group": "subject",
        "tag_id": "absence",
        "source_body": "# Smoke Detail\n\nTest-owned sub-scope source.\n",
        "source_revision": "sha256:" + ("1" * 64),
        "detail_version": 1,
    }
    index_payload = {
        "schema": "docs_index_tree_v1",
        "viewer_options": {
            "non_loadable_doc_ids": [],
            "manage_only_tree_root_ids": [],
        },
        "docs": [
            {
                "doc_id": doc_id,
                "title": str(payload["title"]),
                "content_url": f"/docs/doc?scope=studio&doc_id={doc_id}",
            }
            for doc_id, payload in payloads.items()
        ],
    }

    def fulfill_json(route, payload: dict[str, object]) -> None:
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(payload),
        )

    def fulfill_document(route) -> None:
        doc_id = query_value(route.request.url, "doc_id") or query_value(
            route.request.url,
            "doc",
        )
        payload = payloads.get(doc_id)
        if payload is None:
            route.fulfill(status=404, content_type="application/json", body='{"error":"Not found"}')
            return
        fulfill_json(route, payload)

    def fulfill_source(route) -> None:
        doc_id = query_value(route.request.url, "doc_id") or query_value(
            route.request.url,
            "doc",
        )
        sub_scope = query_value(route.request.url, "sub_scope")
        if include_subscope_report and sub_scope == SUBSCOPE_ID and doc_id == SUBSCOPE_DOC_ID:
            fulfill_json(
                route,
                {
                    "ok": True,
                    "scope": "studio",
                    "sub_scope": SUBSCOPE_ID,
                    "doc_id": SUBSCOPE_DOC_ID,
                    "source_body": subscope_state["source_body"],
                    "source_revision": subscope_state["source_revision"],
                    "path": f"tests/smoke/fixtures/{SUBSCOPE_ID}/{SUBSCOPE_DOC_ID}.md",
                },
            )
            return
        payload = payloads.get(doc_id)
        if payload is None:
            route.fulfill(status=404, content_type="application/json", body='{"error":"Not found"}')
            return
        fulfill_json(
            route,
            {
                "ok": True,
                "scope": "studio",
                "doc_id": doc_id,
                "source_body": f"# {payload['title']}\n\nTest-owned source body.\n",
                "source_revision": f"sha256:smoke-{doc_id}",
                "path": f"tests/smoke/fixtures/{doc_id}.md",
            },
        )

    def fulfill_metadata(route) -> None:
        doc_id = query_value(route.request.url, "doc_id")
        sub_scope = query_value(route.request.url, "sub_scope")
        if include_subscope_report and sub_scope == SUBSCOPE_ID and doc_id == SUBSCOPE_DOC_ID:
            fulfill_json(
                route,
                {
                    "ok": True,
                    "scope": "studio",
                    "sub_scope": SUBSCOPE_ID,
                    "doc_id": SUBSCOPE_DOC_ID,
                    "source_revision": subscope_state["source_revision"],
                    "choices": {
                        "ui_status": ["draft", "done"],
                    },
                    "record": {
                        "doc_id": SUBSCOPE_DOC_ID,
                        "title": subscope_state["title"],
                        "summary": subscope_state["summary"],
                        "date": subscope_state["date"],
                        "date_display": subscope_state["date_display"],
                        "ui_status": subscope_state["ui_status"],
                        "customisation": {
                            "group": subscope_state["group"],
                            "tag_id": subscope_state["tag_id"],
                        },
                    },
                },
            )
            return
        payload = payloads.get(doc_id)
        if payload is None:
            route.fulfill(status=404, content_type="application/json", body='{"error":"Not found"}')
            return
        fulfill_json(
            route,
            {
                "ok": True,
                "scope": "studio",
                "doc_id": doc_id,
                "record": {
                    "doc_id": doc_id,
                    "title": payload["title"],
                    "summary": payload["summary"],
                    "date": "",
                    "date_display": "",
                    "ui_status": "",
                    "parent_id": "",
                },
            },
        )

    def request_json(route) -> dict[str, object]:
        return json.loads(route.request.post_data or "{}")

    def fulfill_source_rebuild(route) -> None:
        payload = request_json(route)
        if (
            not include_subscope_report
            or payload.get("scope") != "studio"
            or payload.get("sub_scope") != SUBSCOPE_ID
            or payload.get("doc_id") != SUBSCOPE_DOC_ID
        ):
            route.fulfill(status=404, content_type="application/json", body='{"error":"Not found"}')
            return
        subscope_state["source_body"] = payload.get("source_body", "")
        subscope_state["source_revision"] = "sha256:" + ("2" * 64)
        subscope_state["detail_version"] = int(subscope_state["detail_version"]) + 1
        fulfill_json(
            route,
            {
                "ok": True,
                "scope": "studio",
                "sub_scope": SUBSCOPE_ID,
                "doc_id": SUBSCOPE_DOC_ID,
                "source_revision": subscope_state["source_revision"],
                "summary_text": "Synthetic sub-scope source rebuilt.",
                "rebuild": {
                    "docs": {"mode": "sub_scope", "sub_scope": SUBSCOPE_ID},
                    "search": {"mode": "full", "doc_ids": []},
                },
            },
        )

    def fulfill_metadata_update(route) -> None:
        payload = request_json(route)
        if (
            not include_subscope_report
            or payload.get("scope") != "studio"
            or payload.get("sub_scope") != SUBSCOPE_ID
            or payload.get("doc_id") != SUBSCOPE_DOC_ID
        ):
            route.fulfill(status=404, content_type="application/json", body='{"error":"Not found"}')
            return
        for field in (
            "title",
            "summary",
            "date",
            "date_display",
            "ui_status",
        ):
            subscope_state[field] = payload.get(field)
        subscope_state["source_revision"] = "sha256:" + ("3" * 64)
        subscope_state["detail_version"] = int(subscope_state["detail_version"]) + 1
        fulfill_json(
            route,
            {
                "ok": True,
                "scope": "studio",
                "sub_scope": SUBSCOPE_ID,
                "doc_id": SUBSCOPE_DOC_ID,
                "source_revision": subscope_state["source_revision"],
                "record": {
                    "doc_id": SUBSCOPE_DOC_ID,
                    "title": subscope_state["title"],
                    "summary": subscope_state["summary"],
                    "date": subscope_state["date"],
                    "date_display": subscope_state["date_display"],
                    "ui_status": subscope_state["ui_status"],
                },
            },
        )

    def fulfill_assign_field_group(route) -> None:
        payload = request_json(route)
        group = (payload.get("fields") or {}).get("group")
        tag_id = (payload.get("fields") or {}).get("tag_id")
        if (
            not include_subscope_report
            or payload.get("scope") != "studio"
            or payload.get("sub_scope") != SUBSCOPE_ID
            or payload.get("doc_id") != SUBSCOPE_DOC_ID
            or payload.get("source_revision") != subscope_state["source_revision"]
            or payload.get("field_group") != "tag_fields"
            or payload.get("confirm") is not True
            or group not in {"", "subject", "domain", "form", "theme"}
            or tag_id not in {"", "absence", "presence"}
        ):
            route.fulfill(status=400, content_type="application/json", body='{"error":"Invalid Tag fields request"}')
            return
        subscope_state["group"] = group
        subscope_state["tag_id"] = tag_id
        subscope_state["source_revision"] = "sha256:" + ("4" * 64)
        subscope_state["detail_version"] = int(subscope_state["detail_version"]) + 1
        fulfill_json(
            route,
            {
                "ok": True,
                "scope": "studio",
                "sub_scope": SUBSCOPE_ID,
                "doc_id": SUBSCOPE_DOC_ID,
                "target": {
                    "scope": "studio",
                    "sub_scope": SUBSCOPE_ID,
                    "doc_id": SUBSCOPE_DOC_ID,
                },
                "field_group": "tag_fields",
                "fields": {"group": group, "tag_id": tag_id},
                "changes": {"group_changed": True, "tag_id_changed": False},
                "source_revision": subscope_state["source_revision"],
            },
        )

    def fulfill_subscope_manifest(route) -> None:
        if not include_subscope_report:
            route.fulfill(status=404, content_type="application/json", body='{"error":"Not found"}')
            return
        documents = [
            {
                "doc_id": SUBSCOPE_DOC_ID,
                "title": subscope_state["title"],
                "ui_status": subscope_state["ui_status"],
                "customisation": {
                    "group": subscope_state["group"],
                    "tag_id": subscope_state["tag_id"],
                },
            }
        ]
        if include_subscope_sibling:
            documents.append(
                {
                    "doc_id": SUBSCOPE_SIBLING_DOC_ID,
                    "title": SUBSCOPE_SIBLING_DOC_TITLE,
                    "ui_status": "done",
                }
            )
        fulfill_json(
            route,
            {
                "customisation": {
                    "id": "analysis_tags",
                    "data": {
                        "groups": ["subject", "domain", "form", "theme"],
                    },
                },
                "docs": documents,
            },
        )

    def fulfill_subscope_detail(route) -> None:
        detail_id = Path(urlparse(route.request.url).path).stem
        if not include_subscope_report or detail_id != SUBSCOPE_DOC_ID:
            route.fulfill(status=404, content_type="application/json", body='{"error":"Not found"}')
            return
        version = int(subscope_state["detail_version"])
        fulfill_json(
            route,
            {
                "doc_id": SUBSCOPE_DOC_ID,
                "title": subscope_state["title"],
                "last_updated": f"2000-01-01 00:00:0{version}",
                "content_html": (
                    f"<h1>{subscope_state['title']}</h1>"
                    f'<p data-smoke-detail-version="{version}">'
                    f"Synthetic detail version {version}.</p>"
                    '<p><a href="/series/?series=001"'
                    ' data-semantic-token-family="catalogue"'
                    ' data-semantic-token-target-type="series"'
                    ' data-semantic-token-target-id="001">Smoke Series</a></p>'
                ),
            },
        )

    def fulfill_tag_registry(route) -> None:
        fulfill_json(
            route,
            {
                "ok": True,
                "tag_registry_version": "tag_registry_v6",
                "tags": [
                    {"tag_id": "absence", "group": "theme"},
                    {"tag_id": "presence", "group": "subject"},
                ],
            },
        )

    def fulfill_diagram_sources(route) -> None:
        target: dict[str, object] = {
            "ok": True,
            "scope": query_value(route.request.url, "scope"),
            "doc_id": query_value(route.request.url, "doc_id"),
            "sources": [],
        }
        sub_scope = query_value(route.request.url, "sub_scope")
        if sub_scope:
            target["sub_scope"] = sub_scope
        fulfill_json(route, target)

    def fulfill_open_source(route) -> None:
        payload = request_json(route)
        fulfill_json(
            route,
            {
                "ok": True,
                "scope": payload.get("scope"),
                "sub_scope": payload.get("sub_scope"),
                "doc_id": payload.get("doc_id"),
                "editor": payload.get("editor"),
            },
        )

    def fulfill_viewer_config(route) -> None:
        response = route.fetch()
        payload = response.json()
        scopes = payload.get("scopes")
        if not isinstance(scopes, list):
            raise AssertionError("Docs Viewer config did not contain scopes")
        studio = next(
            (record for record in scopes if record.get("scope_id") == "studio"),
            None,
        )
        if not isinstance(studio, dict):
            raise AssertionError("Docs Viewer config did not contain Studio")
        studio["sub_scopes"] = [
            {
                "sub_scope": SUBSCOPE_ID,
                "title": "Smoke Documents",
                "manifest_url": "/__smoke/subscope/manifest.json",
                "by_id_url_base": "/__smoke/subscope/by-id",
                "sub_scope_customisation": {
                    "id": "analysis_tags",
                    "capabilities": {
                        "assignable_field_groups": ["tag_fields"],
                    },
                },
            }
        ]
        route.fulfill(
            status=response.status,
            content_type="application/json",
            body=json.dumps(payload),
        )

    if include_subscope_report:
        page.route(
            re.compile(r".*/docs-viewer/config/defaults/docs-viewer-config\.json(?:\?.*)?$"),
            fulfill_viewer_config,
        )
        page.route(
            re.compile(r".*/__smoke/subscope/manifest\.json(?:\?.*)?$"),
            fulfill_subscope_manifest,
        )
        page.route(
            re.compile(r".*/__smoke/subscope/by-id/[^/?]+\.json(?:\?.*)?$"),
            fulfill_subscope_detail,
        )
        page.route(
            re.compile(r".*/docs/source/rebuild(?:\?.*)?$"),
            fulfill_source_rebuild,
        )
        page.route(
            re.compile(r".*/docs/update-metadata(?:\?.*)?$"),
            fulfill_metadata_update,
        )
        page.route(
            re.compile(r".*/docs/assign-field-group(?:\?.*)?$"),
            fulfill_assign_field_group,
        )
        page.route(
            re.compile(r".*/studio/api/tags/tag-registry(?:\?.*)?$"),
            fulfill_tag_registry,
        )
        page.route(
            re.compile(r".*/docs/diagram-sources(?:\?.*)?$"),
            fulfill_diagram_sources,
        )
        page.route(
            re.compile(r".*/docs/open-source(?:\?.*)?$"),
            fulfill_open_source,
        )
    page.route(
        re.compile(
            r".*/(?:docs/index-tree|docs-viewer/scopes/studio/published/"
            r"documents/index-tree\.json)(?:\?.*)?$"
        ),
        lambda route: fulfill_json(route, index_payload),
    )
    page.route(re.compile(r".*/docs/doc(?:\?.*)?$"), fulfill_document)
    page.route(re.compile(r".*/docs/metadata(?:\?.*)?$"), fulfill_metadata)
    page.route(re.compile(r".*/docs/source(?:\?.*)?$"), fulfill_source)


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
    package_capability = capabilities.get("capabilities", {}).get("document_packages", {})
    if package_capability.get("atomic_return") is not True:
        raise AssertionError(f"expected atomic document-package capability: {package_capability!r}")

    package_config = read_json_url(f"{base_url}/docs/packages/config")
    profile_ids = {
        item.get("profile_id")
        for item in package_config.get("profiles", [])
        if isinstance(item, dict)
    }
    if package_config.get("ok") is not True or profile_ids != {"document-content", "document-tree"}:
        raise AssertionError(f"unexpected document-package config: {package_config!r}")

    documents = read_json_url(f"{base_url}/docs/packages/documents?scope=studio")
    records = documents.get("records")
    if documents.get("ok") is not True or not isinstance(records, list):
        raise AssertionError(f"expected the Studio package-source response shape: {documents!r}")


def assert_origin_rejection(base_url: str) -> None:
    payload = json.dumps({"scope": "studio", "doc_ids": [DOCS_VIEWER_DOC_ID]}).encode("utf-8")
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

    package_request = urllib.request.Request(
        f"{base_url}/docs/packages/config",
        headers={"Origin": "https://example.com"},
    )
    try:
        urllib.request.urlopen(package_request, timeout=10)
    except urllib.error.HTTPError as error:
        if error.code != 403:
            raise AssertionError(
                f"expected package API to reject disallowed Origin with 403, got {error.code}"
            ) from error
    else:
        raise AssertionError("document-package API should reject a disallowed Origin")

    metadata_request = urllib.request.Request(
        (
            f"{base_url}/docs/metadata"
            f"?scope=studio&doc_id={DOCS_VIEWER_DOC_ID}"
        ),
        headers={"Origin": "https://example.com"},
    )
    try:
        urllib.request.urlopen(metadata_request, timeout=10)
    except urllib.error.HTTPError as error:
        if error.code != 403:
            raise AssertionError(
                f"expected metadata read to reject disallowed Origin with 403, got {error.code}"
            ) from error
    else:
        raise AssertionError("metadata read should reject a disallowed Origin")


def assert_dedicated_publishability_endpoints_retired(base_url: str) -> None:
    payload = json.dumps({"scope": "studio", "doc_id": DOCS_VIEWER_DOC_ID}).encode("utf-8")
    for path in ("/docs/update-publishability", "/docs/update-publishability-bulk"):
        request = urllib.request.Request(
            f"{base_url}{path}",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urllib.request.urlopen(request, timeout=10)
        except urllib.error.HTTPError as error:
            if error.code != 404:
                raise AssertionError(f"expected retired {path} to return 404, got {error.code}") from error
        else:
            raise AssertionError(f"retired endpoint remained available: {path}")


def wait_for_manage_doc(page: Page, title: str, timeout_ms: int) -> None:
    wait_for_route_ready(
        page,
        "#docsViewerRoot",
        "data-docs-viewer-ready",
        "data-docs-viewer-busy",
        timeout_ms,
    )
    page.wait_for_function(
        """expectedTitle => {
            const heading = document.querySelector("#docsViewerContent h1");
            const actions = document.querySelector('[data-docs-viewer-control-surface-mount="app-management"]');
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


def assert_inline_mermaid_browser_review(page: Page, timeout_ms: int) -> None:
    def visual_state() -> dict[str, object]:
        return page.locator("#docsViewerContent").evaluate(
            """content => {
                const host = content.querySelector(
                    '.docsViewer__diagram[data-docs-viewer-diagram-kind="inline-mermaid"]'
                );
                const svg = host?.querySelector(':scope > svg');
                const viewport = host?.parentElement;
                const frame = viewport?.parentElement;
                const panelProbe = document.createElement('span');
                panelProbe.style.backgroundColor = 'var(--docs-viewer-panel)';
                content.appendChild(panelProbe);
                const panelBackground = getComputedStyle(panelProbe).backgroundColor;
                panelProbe.remove();
                const children = Array.from(content.children);
                const frameIndex = children.indexOf(frame);
                const focusableSelector = 'a[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"])';
                return {
                    theme: document.documentElement.getAttribute('data-theme') || '',
                    hostBackground: host ? getComputedStyle(host).backgroundColor : '',
                    panelBackground,
                    svgBackground: svg?.style.backgroundColor || '',
                    hostOverflowX: host ? getComputedStyle(host).overflowX : '',
                    viewportOverflowX: viewport ? getComputedStyle(viewport).overflowX : '',
                    svgDisplay: svg ? getComputedStyle(svg).display : '',
                    svgTitle: svg?.querySelector('title')?.textContent.trim() || '',
                    svgDescription: svg?.querySelector('desc')?.textContent.trim() || '',
                    detailControlHref: frame?.querySelector('.docsViewer__diagramDetailControl')
                        ?.getAttribute('href') || '',
                    detailControlLabel: frame?.querySelector('.docsViewer__diagramDetailControl')
                        ?.getAttribute('aria-label') || '',
                    detailControlTag: frame?.querySelector('.docsViewer__diagramDetailControl')
                        ?.tagName || '',
                    hostRole: host?.getAttribute('role'),
                    hostTabIndex: host?.getAttribute('tabindex'),
                    focusableCount: host?.querySelectorAll(focusableSelector).length ?? -1,
                    directViewportChild: viewport?.classList.contains('docsViewer__diagramViewport')
                        && host?.parentElement === viewport,
                    directFrameChild: frame?.classList.contains('docsViewer__diagramFrame')
                        && viewport?.parentElement === frame,
                    frameKind: frame?.dataset.docsViewerDiagramFrame || '',
                    frameDirectChild: frame?.parentElement === content,
                    frameIndex,
                    childCount: children.length,
                    previousText: frame?.previousElementSibling?.textContent.trim() || '',
                    nextText: frame?.nextElementSibling?.textContent.trim() || ''
                };
            }"""
        )

    def detail_state() -> dict[str, object]:
        return page.locator("#docsViewerContent").evaluate(
            """content => {
                const detail = content.querySelector('[data-docs-content-detail-view="diagram"]');
                const host = detail?.querySelector(
                    '.docsViewer__diagram[data-docs-viewer-diagram-kind="inline-mermaid"]'
                );
                const openNewTab = document.querySelector(
                    '[data-docs-viewer-control="content-detail-open-new-tab"]'
                );
                const back = document.querySelector(
                    '[data-docs-viewer-control="content-detail-back"]'
                );
                return {
                    active: content.dataset.docsContentDetailActive || '',
                    backLabel: back?.getAttribute('aria-label') || '',
                    detailKind: detail?.dataset.docsContentDetailView || '',
                    detailHref: openNewTab?.getAttribute('href') || '',
                    detailLabel: openNewTab?.getAttribute('aria-label') || '',
                    detailRel: openNewTab?.getAttribute('rel') || '',
                    detailTarget: openNewTab?.getAttribute('target') || '',
                    detailTag: openNewTab?.tagName || '',
                    movedExactHost: detail?.querySelector('.docsViewer__diagramDetailViewport')
                        ?.firstElementChild === host,
                    theme: document.documentElement.getAttribute('data-theme') || ''
                };
            }"""
        )

    initial = visual_state()
    if (
        initial["detailControlTag"] != "BUTTON"
        or initial["detailControlLabel"] != "Open diagram"
        or initial["detailControlHref"] != ""
    ):
        raise AssertionError(
            f"inline diagram source control did not use Content Detail: {initial!r}"
        )

    page.locator(
        '.docsViewer__diagramFrame[data-docs-viewer-diagram-frame="inline-mermaid"] '
        ".docsViewer__diagramDetailControl"
    ).click()
    page.wait_for_function(
        """() => {
            const content = document.querySelector('#docsViewerContent');
            const detail = content?.querySelector('[data-docs-content-detail-view="diagram"]');
            const link = document.querySelector(
                '[data-docs-viewer-control="content-detail-open-new-tab"]'
            );
            return content?.dataset.docsContentDetailActive === 'true'
                && detail?.querySelector(
                    '.docsViewer__diagram[data-docs-viewer-diagram-kind="inline-mermaid"]'
                )
                && link?.getAttribute('href')?.startsWith('blob:');
        }""",
        timeout=timeout_ms,
    )
    initial_detail = detail_state()

    theme_toggle = page.locator("[data-docs-viewer-theme-toggle]")
    if theme_toggle.count() != 1 or theme_toggle.is_hidden():
        raise AssertionError("Docs Viewer theme toggle is not available for diagram review")
    theme_toggle.click()
    page.wait_for_function(
        "previous => document.documentElement.getAttribute('data-theme') !== previous",
        arg=initial_detail["theme"],
        timeout=timeout_ms,
    )
    page.wait_for_function(
        """previous => {
            const link = document.querySelector(
                '[data-docs-viewer-control="content-detail-open-new-tab"]'
            );
            return link?.getAttribute('href')
                && link.getAttribute('href') !== previous;
        }""",
        arg=initial_detail["detailHref"],
        timeout=timeout_ms,
    )
    toggled_detail = detail_state()
    detail_states = [initial_detail, toggled_detail]
    for state in detail_states:
        if (
            state["active"] != "true"
            or state["backLabel"] != "Back to document"
            or state["detailKind"] != "diagram"
            or not str(state["detailHref"]).startswith("blob:")
            or state["detailLabel"] != "Open in new tab"
            or state["detailRel"] != "noopener"
            or state["detailTarget"] != "_blank"
            or state["detailTag"] != "A"
            or not state["movedExactHost"]
        ):
            raise AssertionError(
                f"inline diagram did not retain Content Detail ownership: {detail_states!r}"
            )
    if initial_detail["detailHref"] == toggled_detail["detailHref"]:
        raise AssertionError(
            f"theme change did not replace the active inline detail target: {detail_states!r}"
        )

    detail_markup = page.evaluate(
        """async target => {
            const response = await fetch(target);
            return response.text();
        }""",
        toggled_detail["detailHref"],
    )
    if (
        "Inline Mermaid diagram lifecycle" not in detail_markup
        or "viewBox=" not in detail_markup
        or "background-color" not in detail_markup
    ):
        raise AssertionError(
            "refreshed inline detail target lost accessible or themed SVG content"
        )

    page.locator('[data-docs-viewer-control="content-detail-back"]').click()
    page.wait_for_function(
        """() => {
            const content = document.querySelector('#docsViewerContent');
            const frame = content?.querySelector(
                '.docsViewer__diagramFrame[data-docs-viewer-diagram-frame="inline-mermaid"]'
            );
            return content && !content.hasAttribute('data-docs-content-detail-active')
                && frame?.querySelector(
                    '.docsViewer__diagram[data-docs-viewer-diagram-kind="inline-mermaid"]'
                );
        }""",
        timeout=timeout_ms,
    )
    restored = visual_state()
    states = {str(initial["theme"]): initial, str(restored["theme"]): restored}
    if set(states) != {"light", "dark"}:
        raise AssertionError(f"diagram review did not exercise both themes: {states!r}")
    for theme, state in states.items():
        if (
            state["hostBackground"] != state["panelBackground"]
            or state["svgBackground"] != state["panelBackground"]
            or state["svgDisplay"] != "block"
        ):
            raise AssertionError(f"inline diagram lost its themed readable surface in {theme}: {state!r}")
        if state["hostOverflowX"] != "visible" or state["viewportOverflowX"] != "auto":
            raise AssertionError(f"inline diagram overflow ownership changed in {theme}: {state!r}")
        if state["svgTitle"] != "Inline Mermaid diagram lifecycle" or not str(state["svgDescription"]).startswith(
            "A document mount registers"
        ):
            raise AssertionError(f"inline diagram accessible text changed in {theme}: {state!r}")

    reading_state = restored
    if (
        reading_state["hostRole"] is not None
        or reading_state["hostTabIndex"] is not None
        or reading_state["focusableCount"] != 0
        or not reading_state["directViewportChild"]
        or not reading_state["directFrameChild"]
        or reading_state["frameKind"] != "inline-mermaid"
        or not reading_state["frameDirectChild"]
        or not 0 < int(reading_state["frameIndex"]) < int(reading_state["childCount"]) - 1
        or not reading_state["previousText"]
        or not reading_state["nextText"]
    ):
        raise AssertionError(f"inline diagram changed keyboard or document reading order: {reading_state!r}")

def manage_route_state(page: Page) -> dict[str, object]:
    return page.locator("#docsViewerRoot").evaluate(
        """async root => {
            const routeConfigUrl = root.dataset.routeConfigUrl || "";
            const payload = await fetch(routeConfigUrl).then(response => response.json());
            const routeConfig = (payload.routes || []).find(record => record.route_id === root.dataset.routeId) || {};
            return {
                appKind: root.dataset.docsViewerAppKind || "",
                managementUi: root.dataset.managementUi || "",
                sourceService: root.dataset.sourceService || "",
                ready: root.dataset.docsViewerReady || "",
                busy: root.dataset.docsViewerBusy || "",
                includeScopeParam: root.dataset.includeScopeParam || "",
                routeId: root.dataset.routeId || "",
                routeConfigUrl,
                docsPaths: routeConfig.docs_paths || {},
                viewerBaseUrl: routeConfig.viewer_base_url || "",
                generatedBaseUrl: routeConfig.services?.generated_data?.base_url || "",
                sourceBaseUrl: routeConfig.services?.source?.base_url || "",
                managementBaseUrl: routeConfig.services?.management?.base_url || ""
            };
        }"""
    )


def assert_manage_route_contract(state: dict[str, object], base_url: str) -> None:
    docs_paths = state.get("docsPaths") if isinstance(state.get("docsPaths"), dict) else {}
    if state["appKind"] != "manage" or state["managementUi"] != "true" or state["sourceService"] != "true":
        raise AssertionError(f"manage route did not expose the manage app/service context: {state!r}")
    if state["viewerBaseUrl"] != "/docs/":
        raise AssertionError(f"manage route did not use the manage route: {state!r}")
    if state["ready"] != "true" or state["busy"] == "true":
        raise AssertionError(f"manage route did not expose ready route state: {state!r}")
    if state["includeScopeParam"] != "true":
        raise AssertionError(f"manage route did not include scope param: {state!r}")
    if state["routeId"] != "docs-manage":
        raise AssertionError(f"manage route used unexpected route id: {state!r}")
    if state["routeConfigUrl"] != "/docs-viewer/config/routes/docs-viewer-routes.json":
        raise AssertionError(f"manage route used unexpected route config: {state!r}")
    if (
        state["managementBaseUrl"] != base_url
        or state["generatedBaseUrl"] != base_url
        or state["sourceBaseUrl"] != base_url
    ):
        raise AssertionError(f"manage route did not receive service base URL: {state!r}")
    if docs_paths.get("index_tree_url") != "/docs-viewer/scopes/studio/published/documents/index-tree.json":
        raise AssertionError(f"manage route config missing index_tree_url: {state!r}")
    if docs_paths.get("recent_url") != "/docs-viewer/scopes/studio/published/documents/recent.json":
        raise AssertionError(f"manage route config missing recent_url: {state!r}")
    if docs_paths.get("search_index_url") != "/docs-viewer/scopes/studio/published/search/index.json":
        raise AssertionError(f"manage route config missing search_index_url: {state!r}")


def set_manage_theme(page: Page, theme: str, timeout_ms: int) -> None:
    toggle = page.locator("[data-docs-viewer-theme-toggle]")
    if toggle.count() != 1 or toggle.is_hidden():
        raise AssertionError("manage route did not render one visible theme toggle")
    current = page.locator("html").get_attribute("data-theme")
    if current != theme:
        toggle.click()
    page.wait_for_function(
        """expected => {
            const toggle = document.querySelector('[data-docs-viewer-theme-toggle]');
            const isDark = expected === 'dark';
            const visibleIcons = Array.from(
                toggle?.querySelectorAll('[data-docs-viewer-theme-icon]') || []
            ).filter(icon => !icon.hasAttribute('hidden'));
            return document.documentElement.getAttribute('data-theme') === expected &&
                toggle?.getAttribute('aria-pressed') === (isDark ? 'true' : 'false') &&
                toggle?.getAttribute('aria-label') === (
                    isDark ? 'Switch to light mode' : 'Switch to dark mode'
                ) &&
                visibleIcons.length === 1 &&
                visibleIcons[0].dataset.docsViewerThemeIcon === expected;
        }""",
        arg=theme,
        timeout=timeout_ms,
    )


def assert_manage_modal_theme(
    page: Page,
    theme_state: dict[str, object],
    timeout_ms: int,
) -> None:
    page.locator("#docsViewerManageSettingsButton").evaluate("button => button.click()")
    page.wait_for_function(
        """() => {
            const modal = document.querySelector('#docsViewerSettingsModal');
            const card = modal?.querySelector('.docsViewer__modalCard');
            const action = document.querySelector('#docsViewerSettingsSaveButton');
            return modal && !modal.hidden && card && action && !action.disabled;
        }""",
        timeout=timeout_ms,
    )
    modal_state = page.locator("#docsViewerSettingsModal").evaluate(
        """modal => {
            const card = modal.querySelector('.docsViewer__modalCard');
            const backdrop = modal.querySelector('.docsViewer__modalBackdrop');
            const field = modal.querySelector('.docsViewer__fieldInput');
            const action = modal.querySelector('#docsViewerSettingsSaveButton');
            return {
                backdrop: getComputedStyle(backdrop).backgroundColor,
                cardBackground: getComputedStyle(card).backgroundColor,
                cardColor: getComputedStyle(card).color,
                fieldBackground: getComputedStyle(field).backgroundColor,
                fieldColor: getComputedStyle(field).color,
                fieldBorder: getComputedStyle(field).borderColor,
                fieldColorScheme: getComputedStyle(field).colorScheme,
                actionBackground: getComputedStyle(action).backgroundColor,
                actionColor: getComputedStyle(action).color,
                actionBorder: getComputedStyle(action).borderColor
            };
        }"""
    )
    resolved = (
        theme_state.get("resolved")
        if isinstance(theme_state.get("resolved"), dict)
        else {}
    )
    expected = {
        "backdrop": resolved.get("overlay"),
        "cardBackground": resolved.get("surface"),
        "cardColor": resolved.get("text"),
        "fieldBackground": resolved.get("surface"),
        "fieldColor": resolved.get("text"),
        "fieldBorder": resolved.get("border"),
        "fieldColorScheme": theme_state.get("theme"),
        "actionBackground": resolved.get("surface"),
        "actionColor": resolved.get("text"),
        "actionBorder": resolved.get("border"),
    }
    if modal_state != expected:
        raise AssertionError(
            f"{theme_state.get('theme')} modal did not consume semantic theme roles: "
            f"{modal_state!r}"
        )
    page.locator("#docsViewerSettingsCancelButton").click()
    page.wait_for_selector("#docsViewerSettingsModal", state="hidden", timeout=timeout_ms)


def assert_manage_theme_contract(page: Page, timeout_ms: int) -> None:
    set_manage_theme(page, "light", timeout_ms)
    light = read_docs_viewer_theme_state(page)
    assert_docs_viewer_theme_state(
        light,
        theme="light",
        management_ui=True,
        body_uses_viewer_palette=True,
    )
    assert_manage_modal_theme(page, light, timeout_ms)

    set_manage_theme(page, "dark", timeout_ms)
    dark = read_docs_viewer_theme_state(page)
    assert_docs_viewer_theme_state(
        dark,
        theme="dark",
        management_ui=True,
        body_uses_viewer_palette=True,
    )
    assert_manage_modal_theme(page, dark, timeout_ms)
    assert_docs_viewer_theme_pair(light, dark)

    page.reload(wait_until="domcontentloaded")
    wait_for_manage_doc(page, DOCS_VIEWER_DOC_TITLE, timeout_ms)
    persisted_dark = read_docs_viewer_theme_state(page)
    assert_docs_viewer_theme_state(
        persisted_dark,
        theme="dark",
        management_ui=True,
        body_uses_viewer_palette=True,
    )
    if persisted_dark.get("tokens") != dark.get("tokens"):
        raise AssertionError(
            f"reloaded dark theme did not retain the shared palette: {persisted_dark!r}"
        )

    set_manage_theme(page, "light", timeout_ms)


def assert_generated_requests(paths: set[str]) -> None:
    for expected in ["/docs/index-tree", "/docs/doc"]:
        if expected not in paths:
            raise AssertionError(f"expected generated service request {expected!r}; saw {sorted(paths)!r}")


def assert_delete_uses_first_remaining_root(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const module = await import('/docs-viewer/runtime/js/management/docs-viewer-management-actions.js');
            const client = await import('/docs-viewer/runtime/js/management/docs-viewer-management-client.js');
            const modals = await import('/docs-viewer/runtime/js/management/docs-viewer-management-modals.js');
            const docs = [
                { doc_id: 'analytics', parent_id: '' },
                { doc_id: 'dlf', parent_id: '' },
                { doc_id: 'section', parent_id: '' },
                { doc_id: 'section-child', parent_id: 'section' }
            ];
            const resolveLoadableDocId = docId => docId === 'section' ? 'section-child' : docId;
            const requests = [];
            const fetch = (url, options) => {
                requests.push({ url, body: JSON.parse(options.body) });
                return Promise.resolve({
                    ok: true,
                    status: 200,
                    json: () => Promise.resolve({ ok: true })
                });
            };
            const clientOptions = {
                baseUrl: 'http://manage.test',
                scope: 'studio',
                fetch
            };
            await client.previewManagedDocDelete(['first', 'second'], clientOptions);
            await client.applyManagedDocDelete(['first', 'second'], clientOptions);
            return {
                afterDlf: module.firstRemainingRootDocId(docs, 'dlf', resolveLoadableDocId),
                afterAnalytics: module.firstRemainingRootDocId(docs, 'analytics', resolveLoadableDocId),
                afterOnly: module.firstRemainingRootDocId([{ doc_id: 'only', parent_id: '' }], 'only'),
                afterSubtree: module.firstRemainingRootDocId(
                    docs,
                    ['section', 'section-child'],
                    resolveLoadableDocId
                ),
                warningBody: modals.buildDocsViewerDeletePreviewBody({
                    warnings: [
                        'This permanently deletes 2 checked documents and 1 additional descendant document.'
                    ],
                    delete_documents: [
                        { doc_id: 'research', title: 'Research' },
                        { doc_id: 'one', title: 'One' },
                        { doc_id: 'two', title: 'Two' }
                    ],
                    public_cleanup: {
                        applicable: true,
                        projected_doc_ids: ['research', 'one'],
                        removed_urls: [
                            '/docs/?scope=studio&doc=research',
                            '/docs/?scope=studio&doc=one',
                            '/docs/?scope=studio&doc=one&subdoc=child'
                        ]
                    }
                }),
                localWarningBody: modals.buildDocsViewerDeletePreviewBody({
                    warnings: ['This permanently deletes 1 document.'],
                    public_cleanup: { applicable: false }
                }),
                completionMessage: modals.docsViewerDeleteCompletionMessage({
                    summary_text: 'Deleted 2 documents.',
                    public_cleanup: {
                        applicable: true,
                        projected_doc_ids: ['research', 'one', 'one'],
                        removed_urls: [
                            '/docs/?scope=studio&doc=research',
                            '/docs/?scope=studio&doc=one',
                            '/docs/?scope=studio&doc=one&subdoc=child'
                        ]
                    }
                }),
                localCompletionMessage: modals.docsViewerDeleteCompletionMessage({
                    summary_text: 'Deleted 1 document.',
                    public_cleanup: { applicable: false }
                }),
                publishBody: module.docsViewerPublishConfirmBody({
                    changed_count: 0,
                    excluded_count: 2,
                    removed_count: 99,
                    paths: {
                        working_docs_root: '/working',
                        published_docs_root: '/public'
                    }
                }),
                publishHasExclusions: module.docsViewerPublishHasChanges({
                    changed_count: 0,
                    excluded_count: 2
                }),
                publishIgnoresRemovedAlias: module.docsViewerPublishHasChanges({
                    changed_count: 0,
                    excluded_count: 0,
                    removed_count: 99
                }),
                requests
            };
        }"""
    )
    if result != {
        "afterDlf": "analytics",
        "afterAnalytics": "dlf",
        "afterOnly": "",
        "afterSubtree": "analytics",
        "warningBody": [
            "This permanently deletes 2 checked documents and 1 additional descendant document.",
            "Current public projections to remove immediately: 2",
            "Public document URLs to remove immediately: 3",
        ],
        "localWarningBody": ["This permanently deletes 1 document."],
        "completionMessage": (
            "Deleted 2 documents. Removed 2 current public projections immediately. "
            "Removed 3 public document URLs."
        ),
        "localCompletionMessage": "",
        "publishBody": (
            "Copy reviewed working docs to the site assets for this public route?\n\n"
            "Changed files: 0\n"
            "Files removed by current Publish exclusions: 2\n\n"
            "From: /working\n"
            "To: /public"
        ),
        "publishHasExclusions": True,
        "publishIgnoresRemovedAlias": False,
        "requests": [
            {
                "url": "http://manage.test/docs/delete-preview",
                "body": {"scope": "studio", "doc_ids": ["first", "second"]},
            },
            {
                "url": "http://manage.test/docs/delete-apply",
                "body": {
                    "scope": "studio",
                    "doc_ids": ["first", "second"],
                    "confirm": True,
                },
            },
        ],
    }:
        raise AssertionError(f"unexpected post-delete root fallback: {result!r}")


def assert_metadata_hydration_failure_is_safe(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const module = await import(
                '/docs-viewer/runtime/js/management/docs-viewer-management-metadata-workflow.js'
            );
            let modalOpened = false;
            let loadError = '';
            const workflow = module.createDocsViewerManagementMetadataWorkflow({
                documentIndex: {
                    allDocs: [{
                        doc_id: 'selected-fallback',
                        title: 'Must not be used'
                    }],
                    docsById: new Map([[
                        'selected-fallback',
                        {
                            doc_id: 'selected-fallback',
                            title: 'Must not be used'
                        }
                    ]])
                },
                management: {},
                callbacks: {
                    getModalController: () => ({
                        openMetadataModal: () => {
                            modalOpened = true;
                            return Promise.resolve(null);
                        }
                    }),
                    loadMetadataDoc: () => Promise.reject(
                        new Error('Full metadata unavailable')
                    ),
                    onLoadError: error => {
                        loadError = error.message;
                    }
                }
            });
            const payload = await workflow.openForTarget({
                scope: 'studio',
                sub_scope: 'tags',
                doc_id: 'metadata-doc'
            });
            return { loadError, modalOpened, payload };
        }"""
    )
    if result != {
        "loadError": "Full metadata unavailable",
        "modalOpened": False,
        "payload": None,
    }:
        raise AssertionError(f"metadata hydration failure opened an unsafe form: {result!r}")


def assert_metadata_workflow_uses_exact_sub_scope_target(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const workflowModule = await import(
                '/docs-viewer/runtime/js/management/docs-viewer-management-metadata-workflow.js'
            );
            const target = {
                scope: 'analysis',
                sub_scope: 'tags',
                doc_id: 'detail-doc'
            };
            const refs = {
                titleInput: { value: 'Renamed detail', focus: () => {} },
                summaryInput: { value: '  Full   summary  ' },
                dateInput: { value: '2026-07-27' },
                dateDisplayInput: { value: 'July 2026' },
                statusInput: { value: 'done' },
                parentInput: {
                    value: 'selected-fallback',
                    focus: () => {}
                }
            };
            let modalResolve = null;
            let opened = null;
            let saved = null;
            let loadedTarget = null;
            const modal = {
                closeMetadataModal: payload => modalResolve(payload),
                openMetadataModal: (doc, options) => {
                    opened = { doc, options };
                    return new Promise(resolve => {
                        modalResolve = resolve;
                    });
                },
                resolveMetadataParentId: () => {
                    throw new Error('Sub-scope metadata must not resolve Parent.');
                },
                setMetadataStatus: () => {}
            };
            const workflow = workflowModule.createDocsViewerManagementMetadataWorkflow({
                documentIndex: {
                    allDocs: [{
                        doc_id: 'selected-fallback',
                        title: 'Must not be used'
                    }],
                    docsById: new Map([[
                        'selected-fallback',
                        {
                            doc_id: 'selected-fallback',
                            title: 'Must not be used'
                        }
                    ]])
                },
                management: {},
                refs,
                callbacks: {
                    getModalController: () => modal,
                    loadMetadataDoc: requestedTarget => {
                        loadedTarget = requestedTarget;
                        return {
                            ok: true,
                            scope: 'analysis',
                            sub_scope: 'tags',
                            doc_id: 'detail-doc',
                            source_revision: 'sha256:' + 'a'.repeat(64),
                            choices: {
                                ui_status: ['draft', 'done']
                            },
                            record: {
                                doc_id: 'detail-doc',
                                title: 'Detail',
                                summary: 'Full local summary',
                                date: '2026-07-26',
                                date_display: 'July 2026',
                                ui_status: 'draft',
                                publishable: true
                            }
                        };
                    },
                    onSave: (savedTarget, payload) => {
                        saved = { target: savedTarget, payload };
                    }
                }
            });
            const pending = workflow.openForTarget(target);
            await new Promise(resolve => setTimeout(resolve, 0));
            workflow.confirm();
            const payload = await pending;
            return {
                loadedTarget,
                opened,
                saved,
                payload
            };
        }"""
    )
    expected_target = {
        "scope": "analysis",
        "sub_scope": "tags",
        "doc_id": "detail-doc",
    }
    expected_payload = {
        "title": "Renamed detail",
        "summary": "Full summary",
        "date": "2026-07-27",
        "date_display": "July 2026",
        "ui_status": "done",
        "source_revision": "sha256:" + ("a" * 64),
    }
    if result["loadedTarget"] != expected_target:
        raise AssertionError(f"metadata hydration did not use the exact target: {result!r}")
    if result["opened"] != {
        "doc": {
            "doc_id": "detail-doc",
            "title": "Detail",
            "summary": "Full local summary",
            "date": "2026-07-26",
            "date_display": "July 2026",
            "ui_status": "draft",
            "publishable": True,
        },
        "options": {
            "target": expected_target,
            "showParent": False,
            "choices": {
                "ui_status": ["draft", "done"],
            },
        },
    }:
        raise AssertionError(f"sub-scope metadata modal received the wrong contract: {result!r}")
    if result["saved"] != {
        "target": expected_target,
        "payload": expected_payload,
    }:
        raise AssertionError(f"sub-scope metadata save used the wrong target or fields: {result!r}")
    if result["payload"] != expected_payload:
        raise AssertionError(f"sub-scope metadata workflow returned the wrong payload: {result!r}")
    if "parent_id" in result["payload"]:
        raise AssertionError(f"sub-scope metadata payload included Parent: {result!r}")


def assert_metadata_workflow_collects_projects_customisation(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const workflowModule = await import(
                '/docs-viewer/runtime/js/management/docs-viewer-management-metadata-workflow.js'
            );
            const target = {
                scope: 'dotlineform',
                sub_scope: 'projects',
                doc_id: 'project-doc'
            };
            const refs = {
                titleInput: { value: 'Project', focus: () => {} },
                summaryInput: { value: '' },
                dateInput: { value: '' },
                dateDisplayInput: { value: '' },
                statusInput: { value: '' },
                parentInput: { value: '', focus: () => {} }
            };
            let modalResolve = null;
            let opened = null;
            let resolvedTarget = null;
            let saved = null;
            const contribution = {
                id: 'dotlineform_projects',
                mountMetadataEditor: () => ({ read: () => ({}), destroy: () => {} })
            };
            const modal = {
                closeMetadataModal: payload => modalResolve(payload),
                openMetadataModal: (doc, options) => {
                    opened = {
                        customisation: doc.customisation,
                        contributionId: options.metadataContribution.id,
                        target: options.target
                    };
                    return new Promise(resolve => {
                        modalResolve = resolve;
                    });
                },
                readMetadataCustomisation: () => ({
                    folder_path: 'projects/future'
                }),
                resolveMetadataParentId: () => {
                    throw new Error('Projects metadata must not resolve Parent.');
                },
                setMetadataStatus: () => {}
            };
            const workflow = workflowModule.createDocsViewerManagementMetadataWorkflow({
                documentIndex: { allDocs: [], docsById: new Map() },
                management: {},
                refs,
                callbacks: {
                    getModalController: () => modal,
                    loadMetadataDoc: () => ({
                        ok: true,
                        scope: 'dotlineform',
                        sub_scope: 'projects',
                        doc_id: 'project-doc',
                        source_revision: 'sha256:' + 'b'.repeat(64),
                        choices: { ui_status: [] },
                        record: {
                            doc_id: 'project-doc',
                            title: 'Project',
                            summary: '',
                            date: '',
                            date_display: '',
                            ui_status: '',
                            customisation: { folder_path: 'projects/current' }
                        }
                    }),
                    onSave: (savedTarget, payload) => {
                        saved = { target: savedTarget, payload };
                    },
                    resolveMetadataContribution: requestedTarget => {
                        resolvedTarget = requestedTarget;
                        return Promise.resolve(contribution);
                    }
                }
            });
            const pending = workflow.openForTarget(target);
            await new Promise(resolve => setTimeout(resolve, 0));
            workflow.confirm();
            const payload = await pending;
            return { opened, payload, resolvedTarget, saved };
        }"""
    )
    expected_target = {
        "scope": "dotlineform",
        "sub_scope": "projects",
        "doc_id": "project-doc",
    }
    expected_payload = {
        "title": "Project",
        "summary": "",
        "date": "",
        "date_display": "",
        "ui_status": "",
        "source_revision": "sha256:" + ("b" * 64),
        "customisation": {"folder_path": "projects/future"},
    }
    assert result == {
        "opened": {
            "customisation": {"folder_path": "projects/current"},
            "contributionId": "dotlineform_projects",
            "target": expected_target,
        },
        "payload": expected_payload,
        "resolvedTarget": expected_target,
        "saved": {"target": expected_target, "payload": expected_payload},
    }


def assert_metadata_client_uses_exact_target_requests(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const client = await import(
                '/docs-viewer/runtime/js/management/docs-viewer-management-client.js'
            );
            const requests = [];
            const fetch = async (url, options) => {
                requests.push({
                    url,
                    method: options.method,
                    body: options.body ? JSON.parse(options.body) : null
                });
                return {
                    ok: true,
                    status: 200,
                    json: async () => ({ ok: true })
                };
            };
            const options = {
                baseUrl: 'http://manage.test',
                scope: 'selected-fallback',
                fetch
            };
            await client.readManagedDocMetadata({
                scope: 'studio',
                doc_id: 'parent-report'
            }, options);
            await client.updateManagedDocMetadata({
                scope: 'analysis',
                sub_scope: 'tags',
                doc_id: 'detail-doc'
            }, {
                title: 'Detail',
                summary: 'Summary',
                date: '2026-07-27',
                date_display: 'July 2026',
                ui_status: 'done'
            }, options);
            await client.assignManagedDocFieldGroup({
                scope: 'dotlineform',
                sub_scope: 'projects',
                doc_id: 'project-doc'
            }, {
                source_revision: 'sha256:' + 'a'.repeat(64),
                field_group: 'authoring_subject',
                fields: {
                    folder_path: 'projects/example', work_id: '', series_id: ''
                },
                confirm: true
            }, options);
            let overrideError = '';
            try {
                await client.updateManagedDocMetadata({
                    scope: 'analysis',
                    sub_scope: 'tags',
                    doc_id: 'detail-doc'
                }, {
                    doc_id: 'selected-fallback',
                    title: 'Invalid'
                }, options);
            } catch (error) {
                overrideError = error.message;
            }
            return { requests, overrideError };
        }"""
    )
    if result != {
        "requests": [
            {
                "url": (
                    "http://manage.test/docs/metadata"
                    "?scope=studio&doc_id=parent-report"
                ),
                "method": "GET",
                "body": None,
            },
            {
                "url": "http://manage.test/docs/update-metadata",
                "method": "POST",
                "body": {
                    "scope": "analysis",
                    "doc_id": "detail-doc",
                    "sub_scope": "tags",
                    "title": "Detail",
                    "summary": "Summary",
                    "date": "2026-07-27",
                    "date_display": "July 2026",
                    "ui_status": "done",
                },
            },
            {
                "url": "http://manage.test/docs/assign-field-group",
                "method": "POST",
                "body": {
                    "scope": "dotlineform",
                    "doc_id": "project-doc",
                    "sub_scope": "projects",
                    "source_revision": "sha256:" + "a" * 64,
                    "field_group": "authoring_subject",
                    "fields": {
                        "folder_path": "projects/example",
                        "work_id": "",
                        "series_id": "",
                    },
                    "confirm": True,
                },
            },
        ],
        "overrideError": (
            "Managed document request payload must not replace target field doc_id."
        ),
    }:
        raise AssertionError(f"metadata client target contract changed: {result!r}")


def assert_metadata_response_refreshes_exact_target(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const actions = await import(
                '/docs-viewer/runtime/js/management/docs-viewer-management-actions.js'
            );
            const requests = [];
            const reloads = [];
            const target = {
                scope: 'studio',
                sub_scope: 'smoke-documents',
                doc_id: 'detail-doc'
            };
            const responsePayload = {
                ok: true,
                scope: 'studio',
                sub_scope: 'smoke-documents',
                doc_id: 'detail-doc'
            };
            const controller = actions.createDocsViewerManagementActionController({
                root: null,
                documentIndex: { docsById: new Map() },
                management: {},
                context: {},
                resolveAction: () => ({
                    enabled: true,
                    targetDocIds: ['selected-fallback']
                }),
                callbacks: {
                    managementClientOptions: () => ({
                        baseUrl: 'http://manage.test',
                        scope: 'selected-fallback',
                        fetch: async (url, options) => {
                            requests.push({
                                url,
                                method: options.method,
                                body: JSON.parse(options.body)
                            });
                            return {
                                ok: true,
                                status: 200,
                                json: async () => responsePayload
                            };
                        }
                    }),
                    reloadMetadataTarget: (reloadedTarget, response) => {
                        reloads.push({
                            target: Object.assign({}, reloadedTarget),
                            response: Object.assign({}, response)
                        });
                        return Promise.resolve('refreshed');
                    },
                    renderManagementUi: () => {},
                    setManagementBusy: () => {},
                    setManagementMessage: () => {}
                }
            });
            const result = await controller.handleEditMetadataSave(target, {
                title: 'Renamed detail',
                summary: 'Summary',
                date: '2026-07-27',
                date_display: 'July 2026',
                ui_status: 'done'
            });
            return { reloads, requests, result };
        }"""
    )
    target = {
        "scope": "studio",
        "sub_scope": SUBSCOPE_ID,
        "doc_id": "detail-doc",
    }
    response = {"ok": True, **target}
    if result != {
        "reloads": [{"target": target, "response": response}],
        "requests": [
            {
                "url": "http://manage.test/docs/update-metadata",
                "method": "POST",
                "body": {
                    **target,
                    "title": "Renamed detail",
                    "summary": "Summary",
                    "date": "2026-07-27",
                    "date_display": "July 2026",
                    "ui_status": "done",
                },
            }
        ],
        "result": "refreshed",
    }:
        raise AssertionError(
            "sub-scope metadata response did not refresh its exact target: "
            f"{result!r}"
        )


def assert_action_target_definitions(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const module = await import('/docs-viewer/runtime/js/management/docs-viewer-action-definitions.js');
            const definitions = module.listDocsViewerActionDefinitions();
            const groupedIds = (target, selectionPolicy = '') => definitions
                .filter(definition => definition.target === target && (definition.selectionPolicy || '') === selectionPolicy)
                .map(definition => definition.id)
                .sort();
            const multiContext = {
                activeDocId: 'active',
                primaryDocId: 'second',
                selectedDocIds: ['first', 'second', 'first']
            };
            const emptySelectionContext = module.createDocsViewerActionContext({ activeDocId: 'active' });
            const multiSelectionContext = module.createDocsViewerActionContext({
                activeDocId: 'active',
                primaryDocId: 'second',
                selectedDocIds: ['first', 'second', 'first']
            });
            const invocationContext = module.createDocsViewerActionContext({
                activeDocId: 'active',
                invocationDocId: 'context'
            });
            let unknownRejected = false;
            try {
                module.resolveDocsViewerAction('invented-action', emptySelectionContext);
            } catch (error) {
                unknownRejected = /Unknown Docs Viewer action/.test(String(error && error.message || ''));
            }
            const surfaceActionIds = Array.from(document.querySelectorAll('[data-docs-viewer-action]'))
                .map(node => node.dataset.docsViewerAction)
                .filter(Boolean);
            const unknownSurfaceActionIds = Array.from(new Set(surfaceActionIds.filter(actionId => (
                !module.getDocsViewerActionDefinition(actionId)
            )))).sort();
            return {
                active: groupedIds('active-document'),
                all: groupedIds('selection', 'all'),
                document: groupedIds('document'),
                exactlyOne: groupedIds('selection', 'exactly-one'),
                primary: groupedIds('selection', 'primary'),
                scope: groupedIds('scope'),
                emptySelectionContext,
                multiSelectionContext,
                invocationContext,
                resolutions: {
                    active: module.resolveDocsViewerAction('bookmark', multiContext),
                    copy: module.resolveDocsViewerAction('copy', multiContext),
                    all: module.resolveDocsViewerAction('prepare-document-package', multiContext),
                    deleteSelection: module.resolveDocsViewerAction('delete', multiContext),
                    primary: module.resolveDocsViewerAction('info', multiContext),
                    exportSelection: module.resolveDocsViewerAction('export-docs', multiContext),
                    emptyDelete: module.resolveDocsViewerAction('delete', emptySelectionContext),
                    emptyPrepare: module.resolveDocsViewerAction('prepare-document-package', emptySelectionContext),
                    multiPrepare: module.resolveDocsViewerAction('prepare-document-package', multiSelectionContext),
                    multiMove: module.resolveDocsViewerAction('move', multiSelectionContext),
                    contextCopy: module.resolveDocsViewerAction('copy-link', invocationContext),
                    toolbarOpenVsCode: module.resolveDocsViewerAction('open-vscode', emptySelectionContext),
                    contextOpenVsCode: module.resolveDocsViewerAction('open-vscode', invocationContext)
                },
                surfaceActionIds: Array.from(new Set(surfaceActionIds)).sort(),
                unknownRejected,
                unknownSurfaceActionIds
            };
        }"""
    )
    expected = {
        "active": [
            "bookmark",
            "edit-metadata",
            "info",
            "markdown-save",
            "markdown-source",
            "source-add-catalogue-image",
            "source-add-catalogue-token",
            "source-add-file",
            "source-add-image",
            "source-insert-subject-link",
        ],
        "all": [
            "copy",
            "delete",
            "export-docs",
            "move",
            "prepare-document-package",
            "set-publishable",
        ],
        "document": [
            "copy-link",
            "new-child",
            "new-sibling",
            "open",
            "open-vscode",
        ],
        "exactlyOne": [],
        "primary": [],
        "scope": [
            "delete-scope",
            "delete-sub-scope",
            "import",
            "new",
            "new-scope",
            "new-sub-scope",
            "publish-docs",
            "rebuild-docs",
            "rename-scope",
            "settings",
        ],
        "emptySelectionContext": {
            "activeDocId": "active",
            "invocationDocId": "",
            "primaryDocId": "",
            "selectedDocIds": [],
        },
        "multiSelectionContext": {
            "activeDocId": "active",
            "invocationDocId": "",
            "primaryDocId": "second",
            "selectedDocIds": ["first", "second"],
        },
        "invocationContext": {
            "activeDocId": "active",
            "invocationDocId": "context",
            "primaryDocId": "context",
            "selectedDocIds": [],
        },
        "resolutions": {
            "active": {
                "actionId": "bookmark",
                "disabledReason": "",
                "enabled": True,
                "selectionPolicy": "",
                "target": "active-document",
                "targetDocIds": ["active"],
            },
            "copy": {
                "actionId": "copy",
                "disabledReason": "",
                "enabled": True,
                "selectionPolicy": "all",
                "target": "selection",
                "targetDocIds": ["first", "second"],
            },
            "all": {
                "actionId": "prepare-document-package",
                "disabledReason": "",
                "enabled": True,
                "selectionPolicy": "all",
                "target": "selection",
                "targetDocIds": ["first", "second"],
            },
            "deleteSelection": {
                "actionId": "delete",
                "disabledReason": "",
                "enabled": True,
                "selectionPolicy": "all",
                "target": "selection",
                "targetDocIds": ["first", "second"],
            },
            "primary": {
                "actionId": "info",
                "disabledReason": "",
                "enabled": True,
                "selectionPolicy": "",
                "target": "active-document",
                "targetDocIds": ["active"],
            },
            "exportSelection": {
                "actionId": "export-docs",
                "disabledReason": "",
                "enabled": True,
                "selectionPolicy": "all",
                "target": "selection",
                "targetDocIds": ["first", "second"],
            },
            "emptyDelete": {
                "actionId": "delete",
                "disabledReason": "Select one or more documents.",
                "enabled": False,
                "selectionPolicy": "all",
                "target": "selection",
                "targetDocIds": [],
            },
            "emptyPrepare": {
                "actionId": "prepare-document-package",
                "disabledReason": "Select one or more documents.",
                "enabled": False,
                "selectionPolicy": "all",
                "target": "selection",
                "targetDocIds": [],
            },
            "multiPrepare": {
                "actionId": "prepare-document-package",
                "disabledReason": "",
                "enabled": True,
                "selectionPolicy": "all",
                "target": "selection",
                "targetDocIds": ["first", "second"],
            },
            "multiMove": {
                "actionId": "move",
                "disabledReason": "",
                "enabled": True,
                "selectionPolicy": "all",
                "target": "selection",
                "targetDocIds": ["first", "second"],
            },
            "contextCopy": {
                "actionId": "copy-link",
                "disabledReason": "",
                "enabled": True,
                "selectionPolicy": "",
                "target": "document",
                "targetDocIds": ["context"],
            },
            "toolbarOpenVsCode": {
                "actionId": "open-vscode",
                "disabledReason": "",
                "enabled": True,
                "selectionPolicy": "",
                "target": "document",
                "targetDocIds": ["active"],
            },
            "contextOpenVsCode": {
                "actionId": "open-vscode",
                "disabledReason": "",
                "enabled": True,
                "selectionPolicy": "",
                "target": "document",
                "targetDocIds": ["context"],
            },
        },
        "surfaceActionIds": [
            "bookmark",
            "copy",
            "copy-link",
            "delete",
            "delete-scope",
            "delete-sub-scope",
            "edit-metadata",
            "export-docs",
            "import",
            "info",
            "markdown-source",
            "move",
            "new",
            "new-child",
            "new-scope",
            "new-sibling",
            "new-sub-scope",
            "open",
            "open-vscode",
            "prepare-document-package",
            "publish-docs",
            "rebuild-docs",
            "rename-scope",
            "set-publishable",
            "settings",
        ],
        "unknownRejected": True,
        "unknownSurfaceActionIds": [],
    }
    if result != expected:
        raise AssertionError(f"unexpected Docs Viewer action target contract: {result!r}")


def assert_open_source_target_handoff(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const definitions = await import('/docs-viewer/runtime/js/management/docs-viewer-action-definitions.js');
            const actions = await import('/docs-viewer/runtime/js/management/docs-viewer-management-actions.js');
            const requests = [];
            const sourceModes = [];
            let hiddenCount = 0;
            const controller = actions.createDocsViewerManagementActionController({
                root: null,
                documentIndex: {
                    docsById: new Map([
                        ['active', { doc_id: 'active', title: 'Active' }],
                        ['invoked', { doc_id: 'invoked', title: 'Invoked' }]
                    ])
                },
                management: {},
                selectedDocument: {},
                context: {
                    requestDocumentMode: (modeId, options) => {
                        sourceModes.push({
                            modeId,
                            sourceTarget: options && options.context
                                ? options.context.sourceTarget
                                : null
                        });
                    }
                },
                resolveAction: function (actionId, targetDocId) {
                    const options = { activeDocId: 'active', selectedDocIds: [] };
                    if (arguments.length > 1) options.invocationDocId = targetDocId;
                    return definitions.resolveDocsViewerAction(
                        actionId,
                        definitions.createDocsViewerActionContext(options)
                    );
                },
                callbacks: {
                    hideContextMenu: () => { hiddenCount += 1; },
                    managementClientOptions: () => ({
                        baseUrl: 'http://docs.test',
                        scope: 'studio',
                        fetch: (url, options) => {
                            requests.push({ url, body: JSON.parse(options.body) });
                            return Promise.resolve({
                                ok: true,
                                status: 200,
                                json: () => Promise.resolve({ ok: true })
                            });
                        }
                    }),
                    renderManagementUi: () => {},
                    setManagementBusy: () => {},
                    setManagementMessage: () => {}
                }
            });
            await controller.handleOpenSource(
                'vscode',
                { scope: 'studio', doc_id: 'active' },
                'Active'
            );
            await controller.handleOpenSource(
                'vscode',
                { scope: 'studio', sub_scope: 'tags', doc_id: 'invoked' },
                'Invoked'
            );
            controller.handleMarkdownSource({
                scope: 'studio',
                sub_scope: 'tags',
                doc_id: 'invoked'
            });
            controller.handleReturnToDoc();
            return { hiddenCount, requests, sourceModes };
        }"""
    )
    expected = {
        "hiddenCount": 4,
        "requests": [
            {
                "url": "http://docs.test/docs/open-source",
                "body": {"scope": "studio", "doc_id": "active", "editor": "vscode"},
            },
            {
                "url": "http://docs.test/docs/open-source",
                "body": {
                    "scope": "studio",
                    "sub_scope": "tags",
                    "doc_id": "invoked",
                    "editor": "vscode",
                },
            },
        ],
        "sourceModes": [
            {
                "modeId": "markdown-source",
                "sourceTarget": {
                    "scope": "studio",
                    "sub_scope": "tags",
                    "doc_id": "invoked",
                },
            },
            {
                "modeId": "rendered-document",
                "sourceTarget": None,
            },
        ],
    }
    if result != expected:
        raise AssertionError(f"unexpected source-open target handoff: {result!r}")


def assert_copy_link_success_is_silent(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const actions = await import(
                '/docs-viewer/runtime/js/management/docs-viewer-management-actions.js'
            );
            const copied = [];
            const statuses = [];
            let hiddenCount = 0;
            const originalClipboard = Object.getOwnPropertyDescriptor(
                window.navigator,
                'clipboard'
            );
            Object.defineProperty(window.navigator, 'clipboard', {
                configurable: true,
                value: {
                    writeText: (text) => {
                        copied.push(text);
                        return Promise.resolve();
                    }
                }
            });
            try {
                const doc = { doc_id: 'copy-doc', title: 'Copy Doc' };
                const controller = actions.createDocsViewerManagementActionController({
                    root: null,
                    documentIndex: { docsById: new Map([[doc.doc_id, doc]]) },
                    management: {},
                    context: {
                        markdownDocLink: () => (
                            '[Copy Doc](/docs/?scope=studio&doc=copy-doc)'
                        )
                    },
                    resolveAction: () => ({
                        enabled: true,
                        targetDocIds: [doc.doc_id]
                    }),
                    callbacks: {
                        currentContextMenuDoc: () => doc,
                        hideContextMenu: () => { hiddenCount += 1; },
                        setManagementMessage: (message, isError) => {
                            statuses.push({ message, isError });
                        }
                    }
                });
                controller.handleCopyLink();
                await new Promise((resolve) => window.setTimeout(resolve, 0));
                return { copied, hiddenCount, statuses };
            } finally {
                if (originalClipboard) {
                    Object.defineProperty(
                        window.navigator,
                        'clipboard',
                        originalClipboard
                    );
                } else {
                    delete window.navigator.clipboard;
                }
            }
        }"""
    )
    expected = {
        "copied": ["[Copy Doc](/docs/?scope=studio&doc=copy-doc)"],
        "hiddenCount": 1,
        "statuses": [],
    }
    if result != expected:
        raise AssertionError(f"Copy Link success feedback changed: {result!r}")


def assert_public_docs_links_activate_in_manage(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const links = await import(
                '/docs-viewer/runtime/js/management/'
                + 'docs-viewer-management-document-links.js'
            );
            const root = document.createElement('div');
            root.innerHTML = `
              <a data-case="document" href="/analysis/?doc=analysis-doc#section">Document</a>
              <a data-case="subdoc" href="/analysis/?doc=report&subdoc=child">Subdoc</a>
              <a data-case="manage" href="/docs/?scope=analysis&doc=managed">Manage</a>
              <a data-case="external" href="https://example.com/analysis/?doc=external">External</a>
              <a data-case="missing" href="/analysis/">Missing</a>
            `;
            const calls = [];
            const mounted = links.mountManagedDocsViewerDocumentLinks(root, {
                currentHref: 'http://127.0.0.1:8776/docs/?scope=analysis&doc=current',
                scopeConfigsById: new Map([
                    ['analysis', {
                        scopeId: 'analysis',
                        viewerBaseUrl: '/analysis/'
                    }],
                    ['studio', {
                        scopeId: 'studio',
                        viewerBaseUrl: '/docs/'
                    }]
                ]),
                viewerUrlForScope: (scope, docId, options) => {
                    calls.push({ scope, docId, manage: options.manage });
                    return '/docs/?scope=' + scope + '&doc=' + docId;
                }
            });
            return {
                mounted,
                calls,
                hrefs: Object.fromEntries(
                    [...root.querySelectorAll('a')].map((link) => [
                        link.dataset.case,
                        link.getAttribute('href')
                    ])
                )
            };
        }"""
    )
    expected = {
        "mounted": 2,
        "calls": [
            {"scope": "analysis", "docId": "analysis-doc", "manage": True},
            {"scope": "analysis", "docId": "report", "manage": True},
        ],
        "hrefs": {
            "document": "/docs/?scope=analysis&doc=analysis-doc#section",
            "subdoc": "/docs/?scope=analysis&doc=report&subdoc=child",
            "manage": "/docs/?scope=analysis&doc=managed",
            "external": "https://example.com/analysis/?doc=external",
            "missing": "/analysis/",
        },
    }
    if result != expected:
        raise AssertionError(f"Manage public Docs link activation changed: {result!r}")


def assert_source_editor_media_presentation(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const sourceEditorMedia = await import(
                '/docs-viewer/runtime/js/management/source-editor/source-editor-media.js'
            );

            async function runCase(kind, mode) {
                const root = document.createElement('div');
                root.className = 'docsViewer';
                document.body.appendChild(root);
                let applyRequest = null;
                let inserted = '';
                let previewRequest = null;
                const filename = kind === 'image' ? 'photo.png' : 'notes.pdf';
                const label = kind === 'image' ? 'Photo' : 'Notes';
                const provider = {
                    listStagedMedia: () => Promise.resolve({
                        files: [{ filename, suggested_label: label }]
                    }),
                    previewStagedMedia: request => {
                        previewRequest = Object.assign({}, request);
                        return Promise.resolve({
                            collision: 'new',
                            requires_replace_confirmation: false
                        });
                    },
                    applyStagedMedia: request => {
                        applyRequest = Object.assign({}, request);
                        const markdown = kind === 'file'
                            ? '[Notes]([[media:docs/studio/files/notes.pdf]])'
                            : request.add_caption
                            ? `<figure data-server-fragment="${request.placement}"></figure>`
                            : '![Photo]([[media:docs/studio/img/photo.png]])';
                        return Promise.resolve({ markdown });
                    }
                };
                const adapter = {
                    replaceSelection: value => {
                        inserted = value;
                        return true;
                    }
                };
                const publishing = sourceEditorMedia.publishAndInsertStagedMedia({
                    adapter,
                    mediaKind: kind,
                    provider,
                    root
                });
                await new Promise(resolve => setTimeout(resolve, 0));
                const host = root.querySelector('[data-docs-viewer-management-modal-host="true"]');
                const checkbox = host?.querySelector('[data-role="staged-media-caption"]') || null;
                const caption = host?.querySelector('[data-role="staged-media-caption-text"]') || null;
                const labelInput = host?.querySelector('[data-role="staged-media-label"]') || null;
                const presentation = host?.querySelector('[data-role="staged-media-presentation"]') || null;
                const summary = host?.querySelector('[data-role="staged-media-summary"]') || null;
                const fillWidth = host?.querySelector('[data-role="staged-media-fill-width"]') || null;
                const placementInputs = Array.from(
                    host?.querySelectorAll('[data-role="staged-media-placement"]') || []
                );
                const initialChecked = checkbox ? checkbox.checked : null;
                const initialCaption = caption ? caption.value : null;
                const initialPlacement = placementInputs.find(input => input.checked)?.value || null;
                const initialFillWidth = fillWidth ? fillWidth.checked : null;
                let labelAfterCaption = null;
                let suggestedAfterAlt = null;
                if (mode === 'custom') {
                    labelInput.value = 'Alternative text';
                    labelInput.dispatchEvent(new Event('input', { bubbles: true }));
                    suggestedAfterAlt = caption.value;
                    caption.value = 'Visible caption';
                    caption.dispatchEvent(new Event('input', { bubbles: true }));
                    labelAfterCaption = labelInput.value;
                    summary.value = 'Supporting copy';
                    placementInputs.find(input => input.value === 'right').checked = true;
                    fillWidth.checked = false;
                }
                if (checkbox && mode === 'unchecked') {
                    checkbox.checked = false;
                    checkbox.dispatchEvent(new Event('change', { bubbles: true }));
                }
                const submittedChecked = checkbox ? checkbox.checked : null;
                const presentationControlsDisabled = presentation
                    ? Array.from(presentation.querySelectorAll('input, textarea')).every(control => control.disabled)
                    : null;
                const presentationHidden = presentation ? presentation.hidden : null;
                host?.querySelector('button[data-role="modal-primary"]')?.click();
                await publishing;
                const state = {
                    captionPresent: Boolean(checkbox),
                    applyRequest,
                    initialChecked,
                    initialCaption,
                    initialFillWidth,
                    initialPlacement,
                    inserted,
                    labelAfterCaption,
                    presentationControlsDisabled,
                    presentationHidden,
                    presentationPresent: Boolean(presentation),
                    previewRequest,
                    suggestedAfterAlt,
                    submittedChecked,
                    submittedFillWidth: fillWidth ? fillWidth.checked : null
                };
                root.remove();
                return state;
            }

            return {
                file: await runCase('file', 'default'),
                imageCustom: await runCase('image', 'custom'),
                imageDefault: await runCase('image', 'default'),
                imageUnchecked: await runCase('image', 'unchecked')
            };
        }"""
    )
    expected = {
        "file": {
            "captionPresent": False,
            "applyRequest": {
                "media_kind": "file",
                "staged_filename": "notes.pdf",
                "label": "Notes",
                "confirm_replace": False,
            },
            "initialChecked": None,
            "initialCaption": None,
            "initialFillWidth": None,
            "initialPlacement": None,
            "inserted": "[Notes]([[media:docs/studio/files/notes.pdf]])",
            "labelAfterCaption": None,
            "presentationControlsDisabled": None,
            "presentationHidden": None,
            "presentationPresent": False,
            "previewRequest": {
                "media_kind": "file",
                "staged_filename": "notes.pdf",
                "label": "Notes",
            },
            "suggestedAfterAlt": None,
            "submittedChecked": None,
            "submittedFillWidth": None,
        },
        "imageCustom": {
            "captionPresent": True,
            "applyRequest": {
                "media_kind": "image",
                "staged_filename": "photo.png",
                "label": "Alternative text",
                "add_caption": True,
                "caption": "Visible caption",
                "summary": "Supporting copy",
                "placement": "right",
                "fill_width": False,
                "confirm_replace": False,
            },
            "initialChecked": True,
            "initialCaption": "Photo",
            "initialFillWidth": True,
            "initialPlacement": "full",
            "inserted": '<figure data-server-fragment="right"></figure>',
            "labelAfterCaption": "Alternative text",
            "presentationControlsDisabled": False,
            "presentationHidden": False,
            "presentationPresent": True,
            "previewRequest": {
                "media_kind": "image",
                "staged_filename": "photo.png",
                "label": "Alternative text",
                "add_caption": True,
                "caption": "Visible caption",
                "summary": "Supporting copy",
                "placement": "right",
                "fill_width": False,
            },
            "suggestedAfterAlt": "Alternative text",
            "submittedChecked": True,
            "submittedFillWidth": False,
        },
        "imageDefault": {
            "captionPresent": True,
            "applyRequest": {
                "media_kind": "image",
                "staged_filename": "photo.png",
                "label": "Photo",
                "add_caption": True,
                "caption": "Photo",
                "summary": "",
                "placement": "full",
                "fill_width": True,
                "confirm_replace": False,
            },
            "initialChecked": True,
            "initialCaption": "Photo",
            "initialFillWidth": True,
            "initialPlacement": "full",
            "inserted": '<figure data-server-fragment="full"></figure>',
            "labelAfterCaption": None,
            "presentationControlsDisabled": False,
            "presentationHidden": False,
            "presentationPresent": True,
            "previewRequest": {
                "media_kind": "image",
                "staged_filename": "photo.png",
                "label": "Photo",
                "add_caption": True,
                "caption": "Photo",
                "summary": "",
                "placement": "full",
                "fill_width": True,
            },
            "suggestedAfterAlt": None,
            "submittedChecked": True,
            "submittedFillWidth": True,
        },
        "imageUnchecked": {
            "captionPresent": True,
            "applyRequest": {
                "media_kind": "image",
                "staged_filename": "photo.png",
                "label": "Photo",
                "add_caption": False,
                "confirm_replace": False,
            },
            "initialChecked": True,
            "initialCaption": "Photo",
            "initialFillWidth": True,
            "initialPlacement": "full",
            "inserted": "![Photo]([[media:docs/studio/img/photo.png]])",
            "labelAfterCaption": None,
            "presentationControlsDisabled": True,
            "presentationHidden": True,
            "presentationPresent": True,
            "previewRequest": {
                "media_kind": "image",
                "staged_filename": "photo.png",
                "label": "Photo",
                "add_caption": False,
            },
            "suggestedAfterAlt": None,
            "submittedChecked": False,
            "submittedFillWidth": True,
        },
    }
    if result != expected:
        raise AssertionError(f"source-editor media presentation changed: {result!r}")


def assert_document_transfer_module_contract(page: Page) -> None:
    result = page.evaluate(
        """async () => {
            const capabilities = await import('/docs-viewer/runtime/js/management/docs-viewer-management-capabilities.js');
            const client = await import('/docs-viewer/runtime/js/management/docs-viewer-management-client.js');
            const payload = {
                document_transfer: { preview: true, apply: true },
                scopes: {
                    studio: {
                        scope_type: 'local',
                        available: true,
                        document_transfer: {
                            collections: [{
                                target: { scope: 'studio', sub_scope: 'projects' },
                                label: 'studio / Projects',
                                copy_source: true,
                                move_source: false,
                                copy_target: true,
                                move_target: false
                            }]
                        },
                        root: 'scopes/studio'
                    },
                    public: {
                        scope_type: 'public',
                        available: true,
                        document_transfer: { collections: [{
                            target: { scope: 'public' }, label: 'public',
                            copy_source: true, move_source: false,
                            copy_target: true, move_target: false
                        }] },
                        root: 'scopes/public'
                    },
                    notes: {
                        scope_type: 'local_external',
                        available: true,
                        document_transfer: { collections: [{
                            target: { scope: 'notes', sub_scope: 'works' },
                            label: 'notes / Works', copy_source: true, move_source: false,
                            copy_target: true, move_target: false
                        }] },
                        root: 'scopes/notes'
                    },
                    processing: {
                        scope_type: 'local',
                        available: true,
                        document_transfer: { collections: [{
                            target: { scope: 'processing' }, label: 'processing',
                            copy_source: true, move_source: true,
                            copy_target: true, move_target: true
                        }] },
                        root: 'scopes/processing'
                    },
                    missing: {
                        scope_type: 'local',
                        available: false,
                        document_transfer: { collections: [] },
                        root: 'scopes/missing'
                    },
                    readonly: {
                        scope_type: 'local',
                        available: true,
                        document_transfer: { collections: [{
                            target: { scope: 'readonly' }, label: 'readonly',
                            copy_source: true, move_source: false,
                            copy_target: false, move_target: false
                        }] },
                        root: 'scopes/readonly'
                    }
                }
            };
            const requests = [];
            const fetch = (url, options) => {
                requests.push({ url, body: JSON.parse(options.body) });
                return Promise.resolve({
                    ok: true,
                    status: 200,
                    json: () => Promise.resolve({ ok: true })
                });
            };
            await client.previewManagedDocumentTransfer(
                { scope: 'studio', sub_scope: 'projects' },
                ['source-a', 'source-b'],
                { scope: 'notes', sub_scope: 'works' },
                'copy',
                false,
                { baseUrl: 'http://manage.test', fetch }
            );
            await client.applyManagedDocumentTransfer({
                schema_version: 'receipt',
                source: { scope: 'studio', sub_scope: 'projects' }
            }, {
                baseUrl: 'http://manage.test', fetch
            });
            return {
                supported: capabilities.documentTransferSupported(payload),
                copySource: capabilities.documentTransferSourceSupported(
                    payload, { scope: 'studio', sub_scope: 'projects' }, 'copy'
                ),
                moveSource: capabilities.documentTransferSourceSupported(
                    payload, { scope: 'public' }, 'move'
                ),
                targets: capabilities.documentTransferTargets(
                    payload, { scope: 'studio', sub_scope: 'projects' }, 'copy'
                ),
                requests
            };
        }"""
    )
    expected = {
        "supported": True,
        "copySource": True,
        "moveSource": False,
        "targets": [
            {"target": {"scope": "notes", "sub_scope": "works"}, "label": "notes / Works"},
            {"target": {"scope": "processing"}, "label": "processing"},
            {"target": {"scope": "public"}, "label": "public"},
        ],
        "requests": [
            {
                "url": "http://manage.test/docs/document-transfer-preview",
                "body": {
                    "scope": "studio",
                    "sub_scope": "projects",
                    "doc_ids": ["source-a", "source-b"],
                    "target_scope": "notes",
                    "target_sub_scope": "works",
                    "transfer_mode": "copy",
                    "include_descendants": False,
                },
            },
            {
                "url": "http://manage.test/docs/document-transfer-apply",
                "body": {
                    "scope": "studio",
                    "sub_scope": "projects",
                    "apply_plan": {
                        "schema_version": "receipt",
                        "source": {"scope": "studio", "sub_scope": "projects"},
                    },
                    "confirm": True,
                },
            },
        ],
    }
    if result != expected:
        raise AssertionError(f"unexpected document transfer module contract: {result!r}")


def assert_subscope_route_state(
    page: Page,
    *,
    subdoc_id: str,
    display_mode: str,
) -> None:
    state = page.evaluate(
        """() => {
            const params = new URL(location.href).searchParams;
            return {
                scope: params.get('scope') || '',
                doc: params.get('doc') || '',
                subdoc: params.get('subdoc') || '',
                mode: params.get('mode') || '',
                displayMode: document.querySelector('#docsViewerRoot')
                    ?.dataset.documentDisplayMode || '',
                activeDocId: document.querySelector(
                    '#docsViewerNav .docsViewer__navLink.is-active'
                )?.dataset.docId || '',
                subdocIndexEntries: document.querySelectorAll(
                    `#docsViewerNav [data-doc-id="${CSS.escape(params.get('subdoc') || '')}"]`
                ).length
            };
        }"""
    )
    expected = {
        "scope": "studio",
        "doc": SUBSCOPE_REPORT_DOC_ID,
        "subdoc": subdoc_id,
        "mode": "",
        "displayMode": display_mode,
        "activeDocId": SUBSCOPE_REPORT_DOC_ID,
        "subdocIndexEntries": 0,
    }
    if state != expected:
        raise AssertionError(f"sub-scope edit route drifted: {state!r}")


def wait_for_subscope_detail(
    page: Page,
    *,
    title: str,
    version: int,
    timeout_ms: int,
) -> None:
    wait_for_manage_doc(page, SUBSCOPE_REPORT_DOC_TITLE, timeout_ms)
    page.wait_for_function(
        """([expectedTitle, expectedVersion]) => {
            const report = document.querySelector('.docsViewerReport');
            const detail = document.querySelector('.docsReportDetail');
            const versionNode = document.querySelector('[data-smoke-detail-version]');
            const parentSource = document.querySelector('#docsViewerManageSourceButton');
            const subdocSource = document.querySelector('#docsViewerManageSubdocSourceButton');
            const semanticLink = detail?.querySelector(
                'a[data-semantic-token-family="catalogue"]'
            );
            return report?.dataset.reportState === 'detail'
                && detail?.dataset.reportSubdocTitle === expectedTitle
                && versionNode?.dataset.smokeDetailVersion === String(expectedVersion)
                && semanticLink?.href === 'http://127.0.0.1:4000/series/?series=001'
                && parentSource?.getAttribute('aria-label') === 'Parent Source'
                && subdocSource?.disabled === false;
        }""",
        arg=[title, version],
        timeout=timeout_ms,
    )
    assert_subscope_route_state(
        page,
        subdoc_id=SUBSCOPE_DOC_ID,
        display_mode="rendered-document",
    )


def normalized_subscope_request(request) -> dict[str, object] | None:
    parsed = urlparse(request.url)
    tracked_paths = {
        "/docs/index-tree",
        "/docs/doc",
        "/__smoke/subscope/manifest.json",
        "/docs/source",
        "/docs/source/rebuild",
        "/docs/open-source",
        "/docs/metadata",
        "/docs/update-metadata",
        "/docs/assign-field-group",
        f"/__smoke/subscope/by-id/{SUBSCOPE_DOC_ID}.json",
    }
    if parsed.path not in tracked_paths:
        return None
    query = parse_qs(parsed.query)
    target_query = {
        key: values[0]
        for key in ("scope", "sub_scope", "doc_id")
        if (values := query.get(key))
    }
    body = json.loads(request.post_data) if request.post_data else None
    return {
        "method": request.method,
        "path": parsed.path,
        "query": target_query,
        "body": body,
    }


def exercise_subscope_editing_route(
    page: Page,
    base_url: str,
    timeout_ms: int,
) -> list[dict[str, object]]:
    install_smoke_document_routes(page, include_subscope_report=True)
    request_log: list[dict[str, object]] = []

    def record_request(request) -> None:
        record = normalized_subscope_request(request)
        if record is not None:
            request_log.append(record)

    page.on("request", record_request)
    detail_url = (
        f"{base_url}/docs/?scope=studio"
        f"&doc={SUBSCOPE_REPORT_DOC_ID}"
        f"&subdoc={SUBSCOPE_DOC_ID}"
    )
    page.goto(detail_url, wait_until="domcontentloaded")
    wait_for_subscope_detail(
        page,
        title=SUBSCOPE_DOC_TITLE,
        version=1,
        timeout_ms=timeout_ms,
    )

    parent_source = page.locator("#docsViewerManageSourceButton")
    subdoc_source = page.locator("#docsViewerManageSubdocSourceButton")
    if parent_source.get_attribute("aria-label") != "Parent Source":
        raise AssertionError("detail view did not retain the explicit Parent Source action")
    if subdoc_source.is_disabled():
        raise AssertionError("valid detail did not enable Subdoc Source")
    vscode_source = page.locator("#docsViewerManageOpenVsCodeButton")
    if vscode_source.is_disabled():
        raise AssertionError("valid detail did not enable Open in VS Code")
    with page.expect_request(
        re.compile(r".*/docs/open-source$")
    ):
        vscode_source.click()

    parent_source.click()
    page.wait_for_function(
        f"""() => document.querySelector('#docsViewerRoot')?.dataset.documentDisplayMode === 'markdown-source'
            && document.querySelector('.docsViewerSourceEditor__textarea')?.value.includes(
                '{SUBSCOPE_REPORT_DOC_TITLE}'
            )""",
        timeout=timeout_ms,
    )
    assert_subscope_route_state(
        page,
        subdoc_id=SUBSCOPE_DOC_ID,
        display_mode="markdown-source",
    )
    page.locator("#docsViewerManageReturnToDocButton").click()
    wait_for_subscope_detail(
        page,
        title=SUBSCOPE_DOC_TITLE,
        version=1,
        timeout_ms=timeout_ms,
    )

    page.locator("#docsViewerManageSubdocSourceButton").click()
    page.wait_for_function(
        """() => document.querySelector('#docsViewerRoot')?.dataset.documentDisplayMode === 'markdown-source'
            && document.querySelector('.docsViewerSourceEditor__textarea')?.value.includes(
                'Test-owned sub-scope source.'
            )""",
        timeout=timeout_ms,
    )
    assert_subscope_route_state(
        page,
        subdoc_id=SUBSCOPE_DOC_ID,
        display_mode="markdown-source",
    )
    source_textarea = page.locator(".docsViewerSourceEditor__textarea")
    source_textarea.fill("# Dirty source must remain fixed.\n")
    requests_before_cancel = len(request_log)
    page.locator("#docsViewerManageReturnToDocButton").click()
    prompt = page.locator('[data-role="docs-viewer-management-modal"]')
    prompt.wait_for(state="visible", timeout=timeout_ms)
    if prompt.locator(".docsViewer__modalTitle").inner_text().strip() != "Return to doc?":
        raise AssertionError("dirty Return did not use the dedicated confirmation")
    prompt_style = prompt.evaluate(
        """modal => {
            const card = modal.querySelector('.docsViewer__modalCard');
            const backdrop = modal.querySelector('.docsViewer__modalBackdrop');
            return {
                viewerOwned: Boolean(modal.closest('#docsViewerRoot')),
                cardBackground: card ? getComputedStyle(card).backgroundColor : '',
                backdropBackground: backdrop ? getComputedStyle(backdrop).backgroundColor : ''
            };
        }"""
    )
    if not prompt_style["viewerOwned"]:
        raise AssertionError(
            f"dirty Return modal escaped the themed viewer root: {prompt_style!r}"
        )
    transparent_backgrounds = {"", "transparent", "rgba(0, 0, 0, 0)"}
    if prompt_style["cardBackground"] in transparent_backgrounds:
        raise AssertionError(
            f"dirty Return modal card is transparent: {prompt_style!r}"
        )
    if prompt_style["backdropBackground"] in transparent_backgrounds:
        raise AssertionError(
            f"dirty Return modal backdrop is transparent: {prompt_style!r}"
        )
    if prompt.locator('[data-role="modal-primary"]').inner_text().strip() != "Return to doc":
        raise AssertionError("dirty Return confirmation did not expose its exact action")
    if prompt.locator('button[data-role="modal-cancel"]').inner_text().strip() != "Cancel":
        raise AssertionError("dirty Return confirmation did not expose Cancel")
    prompt.locator('button[data-role="modal-cancel"]').click()
    prompt.wait_for(state="detached", timeout=timeout_ms)
    if len(request_log) != requests_before_cancel:
        raise AssertionError("cancelling dirty Return issued a refresh request")
    if source_textarea.input_value() != "# Dirty source must remain fixed.\n":
        raise AssertionError("cancelling dirty Return replaced the fixed source buffer")
    assert_subscope_route_state(
        page,
        subdoc_id=SUBSCOPE_DOC_ID,
        display_mode="markdown-source",
    )

    page.locator("#docsViewerManageReturnToDocButton").click()
    prompt = page.locator('[data-role="docs-viewer-management-modal"]')
    prompt.wait_for(state="visible", timeout=timeout_ms)
    prompt.locator('[data-role="modal-primary"]').click()
    wait_for_subscope_detail(
        page,
        title=SUBSCOPE_DOC_TITLE,
        version=1,
        timeout_ms=timeout_ms,
    )
    if any(record["path"] == "/docs/source/rebuild" for record in request_log):
        raise AssertionError("confirmed dirty Return rebuilt instead of discarding")

    page.locator("#docsViewerManageSubdocSourceButton").click()
    page.wait_for_selector(".docsViewerSourceEditor__textarea", state="visible", timeout=timeout_ms)
    page.locator(".docsViewerSourceEditor__textarea").fill("# Saved smoke detail.\n")
    page.locator("#docsViewerManageSourceSaveButton").click()
    wait_for_subscope_detail(
        page,
        title=SUBSCOPE_DOC_TITLE,
        version=2,
        timeout_ms=timeout_ms,
    )

    page.locator("#docsViewerManageEditButton").click()
    page.wait_for_selector("#docsViewerMetadataModal", state="visible", timeout=timeout_ms)
    assert_subscope_route_state(
        page,
        subdoc_id=SUBSCOPE_DOC_ID,
        display_mode="rendered-document",
    )
    if not page.locator("#docsViewerMetadataParentField").is_hidden():
        raise AssertionError("sub-scope metadata form exposed Parent")
    if page.locator("#docsViewerMetadataGroupField").count() != 0:
        raise AssertionError("generic metadata form retained its retired Group field")
    page.locator("#docsViewerMetadataTitleInput").fill("Renamed Smoke Detail")
    page.locator("#docsViewerMetadataSummaryInput").fill("Refreshed synthetic metadata")
    page.locator("#docsViewerMetadataDateInput").fill("2026-07-27")
    page.locator("#docsViewerMetadataDateDisplayInput").fill("July 2026")
    page.locator("#docsViewerMetadataStatusInput").select_option("done")
    page.locator("#docsViewerMetadataSaveButton").click()
    wait_for_subscope_detail(
        page,
        title="Renamed Smoke Detail",
        version=3,
        timeout_ms=timeout_ms,
    )

    tag_fields_button = page.locator("[data-docs-tag-fields]")
    if tag_fields_button.is_disabled() or tag_fields_button.inner_text().strip() != "Tag fields":
        raise AssertionError("configured Tag fields action was not available")
    tag_fields_button.click()
    tag_fields_modal = page.locator('[data-role="docs-viewer-management-modal"]')
    tag_fields_modal.wait_for(state="visible", timeout=timeout_ms)
    if tag_fields_modal.locator(".docsViewer__modalTitle").inner_text().strip() != "Tag fields":
        raise AssertionError("Tag fields action opened the wrong modal")
    group_select = tag_fields_modal.locator("[data-docs-tag-fields-group]")
    tag_select = tag_fields_modal.locator("[data-docs-tag-fields-tag]")
    if group_select.locator("option").evaluate_all(
        "options => options.map(option => option.value)"
    ) != ["", "subject", "domain", "form", "theme"]:
        raise AssertionError("Tag fields modal did not preserve configured group order")
    if tag_select.locator("option").evaluate_all(
        "options => options.map(option => option.value)"
    ) != ["", "absence", "presence"] or tag_select.input_value() != "absence":
        raise AssertionError("Tag fields modal did not load canonical Tags")
    group_select.select_option("theme")
    tag_fields_modal.locator('button[data-role="modal-cancel"]').click()
    tag_fields_modal.wait_for(state="detached", timeout=timeout_ms)

    tag_fields_button.click()
    tag_fields_modal = page.locator('[data-role="docs-viewer-management-modal"]')
    tag_fields_modal.wait_for(state="visible", timeout=timeout_ms)
    tag_fields_modal.locator("[data-docs-tag-fields-group]").select_option("theme")
    tag_fields_modal.locator('[data-role="modal-primary"]').click()
    tag_fields_modal.wait_for(state="detached", timeout=timeout_ms)
    page.wait_for_function(
        """() => {
            const report = document.querySelector('.docsViewerReport');
            const detail = document.querySelector('.docsReportDetail');
            const versionNode = document.querySelector('[data-smoke-detail-version]');
            return report?.dataset.reportState === 'detail'
                && detail?.dataset.reportSubdocTitle === 'Renamed Smoke Detail'
                && versionNode?.dataset.smokeDetailVersion === '4';
        }""",
        timeout=timeout_ms,
    )
    assert_subscope_route_state(
        page,
        subdoc_id=SUBSCOPE_DOC_ID,
        display_mode="rendered-document",
    )
    page.locator(".docsReportDetail__back").click()
    page.wait_for_function(
        """() => document.querySelector('.docsViewerReport')?.dataset.reportState === 'list'
            && !new URL(location.href).searchParams.has('subdoc')""",
        timeout=timeout_ms,
    )
    refreshed_manifest_row = page.locator(
        f'.docsViewerReport__row[data-report-subdoc-id="{SUBSCOPE_DOC_ID}"]'
    )
    if "Renamed Smoke Detail" not in refreshed_manifest_row.inner_text():
        raise AssertionError("metadata rebuild did not refresh the Manage manifest row")
    if refreshed_manifest_row.locator(".docsViewer__navStatus").count() != 1:
        raise AssertionError("metadata rebuild did not refresh the manifest status icon")
    if refreshed_manifest_row.locator(".docsViewer__publishableExclusion").count() != 0:
        raise AssertionError("local metadata rebuild exposed a publication-exclusion icon")
    page.go_back(wait_until="domcontentloaded")
    wait_for_subscope_detail(
        page,
        title="Renamed Smoke Detail",
        version=4,
        timeout_ms=timeout_ms,
    )

    page.goto(
        (
            f"{base_url}/docs/?scope=studio"
            f"&doc={SUBSCOPE_REPORT_DOC_ID}"
            f"&subdoc={INVALID_SUBSCOPE_DOC_ID}"
        ),
        wait_until="domcontentloaded",
    )
    wait_for_manage_doc(page, SUBSCOPE_REPORT_DOC_TITLE, timeout_ms)
    page.wait_for_function(
        f"""() => document.querySelector('.docsViewerReport')?.dataset.reportState === 'error'
            && document.querySelector('.docsViewerReport')?.textContent.includes(
                '{INVALID_SUBSCOPE_DOC_ID}'
            )""",
        timeout=timeout_ms,
    )
    assert_subscope_route_state(
        page,
        subdoc_id=INVALID_SUBSCOPE_DOC_ID,
        display_mode="rendered-document",
    )
    if not page.locator("#docsViewerManageEditButton").is_disabled():
        raise AssertionError("invalid detail did not disable Edit metadata")
    if not page.locator("#docsViewerManageSubdocSourceButton").is_disabled():
        raise AssertionError("invalid detail did not disable Subdoc Source")
    if not page.locator("#docsViewerManageOpenVsCodeButton").is_disabled():
        raise AssertionError("invalid detail did not disable Open in VS Code")

    return request_log


def assert_subscope_request_log(request_log: list[dict[str, object]]) -> None:
    def get_requests(path: str, method: str = "GET") -> list[dict[str, object]]:
        return [
            record
            for record in request_log
            if record["path"] == path and record["method"] == method
        ]

    source_reads = get_requests("/docs/source")
    expected_source_queries = [
        {"scope": "studio", "doc_id": SUBSCOPE_REPORT_DOC_ID},
        {
            "scope": "studio",
            "sub_scope": SUBSCOPE_ID,
            "doc_id": SUBSCOPE_DOC_ID,
        },
        {
            "scope": "studio",
            "sub_scope": SUBSCOPE_ID,
            "doc_id": SUBSCOPE_DOC_ID,
        },
    ]
    if [record["query"] for record in source_reads] != expected_source_queries:
        raise AssertionError(f"source target request log changed: {request_log!r}")

    rebuilds = get_requests("/docs/source/rebuild", "POST")
    if rebuilds != [
        {
            "method": "POST",
            "path": "/docs/source/rebuild",
            "query": {},
            "body": {
                "scope": "studio",
                "sub_scope": SUBSCOPE_ID,
                "doc_id": SUBSCOPE_DOC_ID,
                "source_revision": "sha256:" + ("1" * 64),
                "source_body": "# Saved smoke detail.\n",
            },
        }
    ]:
        raise AssertionError(f"source rebuild request log changed: {request_log!r}")

    open_sources = get_requests("/docs/open-source", "POST")
    if open_sources != [
        {
            "method": "POST",
            "path": "/docs/open-source",
            "query": {},
            "body": {
                "scope": "studio",
                "sub_scope": SUBSCOPE_ID,
                "doc_id": SUBSCOPE_DOC_ID,
                "editor": "vscode",
            },
        }
    ]:
        raise AssertionError(f"Open in VS Code target log changed: {request_log!r}")

    metadata_reads = get_requests("/docs/metadata")
    expected_metadata_query = {
        "scope": "studio",
        "sub_scope": SUBSCOPE_ID,
        "doc_id": SUBSCOPE_DOC_ID,
    }
    if [record["query"] for record in metadata_reads] != [
        expected_metadata_query,
        expected_metadata_query,
        expected_metadata_query,
    ]:
        raise AssertionError(f"metadata read target log changed: {request_log!r}")
    metadata_updates = get_requests("/docs/update-metadata", "POST")
    if metadata_updates != [
        {
            "method": "POST",
            "path": "/docs/update-metadata",
            "query": {},
            "body": {
                "scope": "studio",
                "sub_scope": SUBSCOPE_ID,
                "doc_id": SUBSCOPE_DOC_ID,
                "title": "Renamed Smoke Detail",
                "summary": "Refreshed synthetic metadata",
                "date": "2026-07-27",
                "date_display": "July 2026",
                "ui_status": "done",
                "source_revision": "sha256:" + ("2" * 64),
            },
        }
    ]:
        raise AssertionError(f"metadata update request log changed: {request_log!r}")

    tag_field_updates = get_requests("/docs/assign-field-group", "POST")
    if tag_field_updates != [
        {
            "method": "POST",
            "path": "/docs/assign-field-group",
            "query": {},
            "body": {
                "scope": "studio",
                "sub_scope": SUBSCOPE_ID,
                "doc_id": SUBSCOPE_DOC_ID,
                "source_revision": "sha256:" + ("3" * 64),
                "field_group": "tag_fields",
                "fields": {"group": "theme", "tag_id": "absence"},
                "confirm": True,
            },
        }
    ]:
        raise AssertionError(f"Tag fields request log changed: {request_log!r}")

    manifests = get_requests("/__smoke/subscope/manifest.json")
    if len(manifests) != 8 or any(record["query"] for record in manifests):
        raise AssertionError(f"Manage manifest refresh log changed: {request_log!r}")
    details = get_requests(f"/__smoke/subscope/by-id/{SUBSCOPE_DOC_ID}.json")
    if len(details) != 7:
        raise AssertionError(f"targeted detail refresh log changed: {request_log!r}")
    indexes = get_requests("/docs/index-tree")
    parent_docs = get_requests("/docs/doc")
    if len(indexes) != 6 or len(parent_docs) != 6 or any(
        record["query"] != {
            "scope": "studio",
            "doc_id": SUBSCOPE_REPORT_DOC_ID,
        }
        for record in parent_docs
    ):
        raise AssertionError(f"parent remount request log changed: {request_log!r}")


def exercise_manage_route(
    page: Page,
    base_url: str,
    timeout_ms: int,
) -> tuple[set[str], set[str], set[str], set[str], set[str], str]:
    install_smoke_document_routes(page)
    generated_requests: list[str] = []
    import_module_requests: list[str] = []
    scope_lifecycle_requests: list[str] = []
    document_transfer_requests: list[str] = []
    inline_mermaid_requests: list[str] = []
    page.on(
        "request",
        lambda request: generated_requests.append(request.url)
        if any(path in request.url for path in ("/docs/index-tree", "/docs/doc"))
        else None,
    )
    page.on(
        "request",
        lambda request: import_module_requests.append(request.url)
        if "/docs-viewer/runtime/js/import/" in request.url
        else None,
    )
    page.on(
        "request",
        lambda request: scope_lifecycle_requests.append(request.url)
        if "/docs-viewer/runtime/js/management/docs-viewer-scope-lifecycle.js" in request.url
        else None,
    )
    page.on(
        "request",
        lambda request: document_transfer_requests.append(request.url)
        if "/docs-viewer/runtime/js/management/docs-viewer-document-transfer-workflow.js" in request.url
        else None,
    )
    page.on(
        "request",
        lambda request: inline_mermaid_requests.append(request.url)
        if "/docs-viewer/runtime/vendor/mermaid/" in request.url
        else None,
    )

    page.goto(f"{base_url}/docs/?scope=studio&doc={DOCS_VIEWER_DOC_ID}", wait_until="domcontentloaded")
    wait_for_manage_doc(page, DOCS_VIEWER_DOC_TITLE, timeout_ms)
    assert_action_target_definitions(page)
    assert_metadata_hydration_failure_is_safe(page)
    assert_metadata_workflow_uses_exact_sub_scope_target(page)
    assert_metadata_workflow_collects_projects_customisation(page)
    assert_metadata_client_uses_exact_target_requests(page)
    assert_metadata_response_refreshes_exact_target(page)
    assert_source_editor_media_presentation(page)
    assert_copy_link_success_is_silent(page)
    assert_public_docs_links_activate_in_manage(page)
    assert_open_source_target_handoff(page)
    assert_delete_uses_first_remaining_root(page)
    assert_manage_route_contract(manage_route_state(page), base_url)
    assert_manage_theme_contract(page, timeout_ms)
    if inline_mermaid_requests:
        raise AssertionError(f"diagram-free local document loaded Mermaid: {inline_mermaid_requests!r}")
    if import_module_requests:
        raise AssertionError(f"Docs Import modules loaded before the import action: {import_module_requests!r}")
    if scope_lifecycle_requests:
        raise AssertionError(f"scope lifecycle flow loaded before a lifecycle action: {scope_lifecycle_requests!r}")
    if document_transfer_requests:
        raise AssertionError(
            f"document transfer flow loaded before the Copy action: {document_transfer_requests!r}"
        )

    vscode_button = page.locator("#docsViewerManageOpenVsCodeButton")
    if vscode_button.count() != 1 or vscode_button.is_hidden() or vscode_button.is_disabled():
        raise AssertionError("Open in VS Code should be an enabled document-toolbar action")
    if vscode_button.get_attribute("data-docs-viewer-control-surface") != "main-view":
        raise AssertionError("Open in VS Code should be owned by the main-view control surface")
    if vscode_button.get_attribute("data-docs-viewer-action") != "open-vscode":
        raise AssertionError("Document-toolbar control should invoke the shared open-vscode action")
    if vscode_button.get_attribute("title") != "Open in VS Code":
        raise AssertionError("Open in VS Code document-toolbar action should have an explicit label")
    page.wait_for_function(
        """() => {
            const icon = document.querySelector('#docsViewerManageOpenVsCodeButton img');
            return icon && icon.complete && icon.naturalWidth === 100 && icon.naturalHeight === 100;
        }""",
        timeout=timeout_ms,
    )
    vscode_icon = vscode_button.locator("img")
    if not vscode_icon.get_attribute("src").endswith("/docs-viewer/runtime/js/management/icons/vscode.svg"):
        raise AssertionError("Open in VS Code should use the official stable icon asset")
    if vscode_icon.get_attribute("alt") != "" or vscode_icon.get_attribute("aria-hidden") != "true":
        raise AssertionError("Decorative VS Code icon should defer its accessible name to the button")

    index_actions_button = page.locator("#docsViewerIndexActionsButton")
    if (
        index_actions_button.count() != 1
        or index_actions_button.is_hidden()
        or index_actions_button.is_disabled()
    ):
        raise AssertionError("Index actions should remain an enabled index-toolbar icon button")
    if index_actions_button.get_attribute("aria-label") != "Index actions":
        raise AssertionError("Index actions icon button should expose its explicit accessible name")
    if page.locator("#docsViewerManageCopySubtreeButton").count():
        raise AssertionError("singular Copy subtree control should be retired")
    index_toolbar = page.locator('[data-docs-viewer-control-surface-mount="index-view"]')
    index_panel_toggle = page.locator("#docsViewerSidebarToggle")
    index_panel_toggle.click()
    page.wait_for_function(
        """() => {
            const root = document.querySelector('#docsViewerRoot');
            const toolbar = document.querySelector('[data-docs-viewer-control-surface-mount="index-view"]');
            const toggle = document.querySelector('#docsViewerSidebarToggle');
            return root?.dataset.indexPanelState === 'collapsed' &&
                toolbar && getComputedStyle(toolbar).display === 'none' &&
                toggle && !toggle.hidden && toggle.getAttribute('aria-label') === 'Restore index panel';
        }""",
        timeout=timeout_ms,
    )
    if not index_actions_button.is_hidden():
        raise AssertionError("Collapsed index panel should hide the complete index-view toolbar")
    index_panel_toggle.click()
    page.wait_for_function(
        """() => {
            const root = document.querySelector('#docsViewerRoot');
            const toolbar = document.querySelector('[data-docs-viewer-control-surface-mount="index-view"]');
            return root?.dataset.indexPanelState === 'normal' &&
                toolbar && getComputedStyle(toolbar).display !== 'none';
        }""",
        timeout=timeout_ms,
    )
    if index_toolbar.is_hidden() or index_actions_button.is_hidden():
        raise AssertionError("Restored index panel should show its index-view toolbar")

    index_actions_button.click()
    page.wait_for_function(
        """() => {
            const activeDocId = document.querySelector(
                '#docsViewerNav .docsViewer__navLink.is-active'
            )?.dataset.docId || '';
            const checkbox = document.querySelector(
                `[data-docs-viewer-selection-checkbox="${CSS.escape(activeDocId)}"]`
            );
            const controls = document.querySelector(
                '[data-docs-viewer-control="index-selection"]'
            );
            return checkbox?.checked
                && controls
                && !controls.hidden
                && document.querySelector('#docsViewerIndexCopyButton')?.disabled === false;
        }""",
        timeout=timeout_ms,
    )
    with page.expect_request(
        lambda request: urlparse(request.url).path.endswith(
            "/docs-viewer-document-transfer-workflow.js"
        ),
        timeout=timeout_ms,
    ):
        page.locator("#docsViewerIndexCopyButton").click()
    page.goto(f"{base_url}/docs/?scope=studio&doc={DOCS_VIEWER_DOC_ID}", wait_until="domcontentloaded")
    wait_for_manage_doc(page, DOCS_VIEWER_DOC_TITLE, timeout_ms)
    assert_document_transfer_module_contract(page)

    page.locator("#docsViewerManageActionsButton").click()
    page.wait_for_function(
        '() => document.querySelector("#docsViewerManageActionsMenu")?.hidden === false',
        timeout=timeout_ms,
    )
    page.locator("#docsViewerContent h1").click()
    page.wait_for_function(
        '() => document.querySelector("#docsViewerManageActionsMenu")?.hidden === true',
        timeout=timeout_ms,
    )
    page.locator("#docsViewerManageActionsButton").click()
    page.keyboard.press("Escape")
    page.wait_for_function(
        '() => document.querySelector("#docsViewerManageActionsMenu")?.hidden === true',
        timeout=timeout_ms,
    )

    page.locator("#docsViewerManageImportButton").evaluate("button => button.click()")
    page.wait_for_function(
        """() => {
            const modal = document.querySelector("#docsViewerImportModal");
            const root = document.querySelector("#docsHtmlImportRoot");
            return modal && !modal.hidden && root && root.dataset.studioReady === "true";
        }""",
        timeout=timeout_ms,
    )
    page.locator("#docsViewerImportCancelButton").evaluate("button => button.click()")

    page.locator("#docsViewerManageEditButton").evaluate("button => button.click()")
    page.wait_for_function(
        """() => {
            const modal = document.querySelector("#docsViewerMetadataModal");
            const title = document.querySelector("#docsViewerMetadataTitleInput");
            return modal && !modal.hidden && title && title.value.trim();
        }""",
        timeout=timeout_ms,
    )
    metadata_summary = page.locator("#docsViewerMetadataSummaryInput").input_value()
    if metadata_summary != smoke_document_payloads()[DOCS_VIEWER_DOC_ID]["summary"]:
        raise AssertionError(
            "Edit metadata did not hydrate summary from the local source record: "
            f"{metadata_summary!r}"
        )
    if page.locator("#docsViewerMetadataNonPublishableInput").count() != 0:
        raise AssertionError("Edit metadata retained the retired publication checkbox")
    page.locator("#docsViewerMetadataCancelButton").evaluate("button => button.click()")

    page.locator("#docsViewerManageSourceButton").evaluate("button => button.click()")
    page.wait_for_function(
        """() => {
            const root = document.querySelector('#docsViewerRoot');
            const actions = document.querySelector('[data-docs-viewer-control-surface-mount="main-view"]');
            return root?.dataset.documentDisplayMode === 'markdown-source'
                && actions
                && Array.from(actions.children).map(node => node.dataset.docsViewerControl).join(',') === 'open-vscode,source-add-image,source-add-catalogue-image,source-add-file,source-add-catalogue-token,source-insert-subject-link,source-directives,save-markdown-source,markdown-source,subdoc-source,return-to-doc,info'
                && !document.querySelector('#docsViewerManageSourceSaveButton')?.disabled
                && !document.querySelector('#docsViewerManageSourceDirectivesButton')?.disabled
                && document.querySelector('#docsViewerManageSourceButton')?.disabled
                && !document.querySelector('#docsViewerManageReturnToDocButton')?.disabled;
        }""",
        timeout=timeout_ms,
    )
    page.locator("#docsViewerManageSourceDirectivesButton").click()
    page.wait_for_selector(
        "#docsViewerManageSourceDirectivesMenu:not([hidden]) [role='menuitem']",
        state="visible",
        timeout=timeout_ms,
    )
    page.keyboard.press("Escape")
    page.wait_for_function(
        """() => document.querySelector('#docsViewerManageSourceDirectivesMenu')?.hidden === true
            && document.activeElement?.id === 'docsViewerManageSourceDirectivesButton'""",
        timeout=timeout_ms,
    )
    page.locator("#docsViewerManageSourceDirectivesButton").click()
    page.locator('[data-docs-viewer-directive-action="table-detail"]').click()
    page.wait_for_function(
        r"""() => {
            const textarea = document.querySelector('.docsViewerSourceEditor__textarea');
            return textarea?.value.startsWith('<!-- dotlineform:table-detail -->\n\n# ')
                && textarea.selectionStart === 35
                && textarea.selectionEnd === 35
                && document.activeElement === textarea
                && !document.querySelector('.docsViewerSourceEditor__dirty')?.hidden;
        }""",
        timeout=timeout_ms,
    )
    page.locator("#docsViewerManageSourceAddCatalogueTokenButton").evaluate(
        "button => button.click()"
    )
    page.wait_for_selector(
        "#catalogue-token-add-modal",
        state="visible",
        timeout=timeout_ms,
    )
    page.locator(
        "#catalogue-token-add-modal button[data-role='modal-cancel']"
    ).evaluate("button => button.click()")
    page.locator("#docsViewerManageSourceDirectivesButton").click()
    page.locator("#docsViewerManageReturnToDocButton").evaluate("button => button.click()")
    page.locator('[data-role="docs-viewer-management-modal"] [data-role="modal-primary"]').click()
    page.wait_for_function(
        """() => document.querySelector('#docsViewerRoot')?.dataset.documentDisplayMode === 'rendered-document'
            && !document.querySelector('[data-docs-viewer-control="source-directives"]')""",
        timeout=timeout_ms,
    )

    page.locator("#docsViewerManageSettingsButton").evaluate("button => button.click()")
    page.wait_for_function(
        """() => {
            const modal = document.querySelector("#docsViewerSettingsModal");
            const save = document.querySelector("#docsViewerSettingsSaveButton");
            const textInput = document.querySelector("#docsViewerSettingsTextInput");
            const booleanInput = document.querySelector("#docsViewerSettingsBooleanInput");
            return modal && !modal.hidden && save && !save.disabled &&
                ((textInput && !textInput.disabled) || (booleanInput && !booleanInput.disabled));
        }""",
        timeout=timeout_ms,
    )
    page.locator("#docsViewerSettingsCancelButton").evaluate("button => button.click()")

    page.locator("#docsViewerManageNewScopeButton").evaluate("button => button.click()")
    page.wait_for_selector(
        '[data-docs-viewer-management-modal-host="true"] [data-role="scope-id"]',
        state="visible",
        timeout=timeout_ms,
    )
    page.locator(
        '[data-docs-viewer-management-modal-host="true"] button[data-role="modal-cancel"]'
    ).evaluate("button => button.click()")

    page.locator("#docsViewerManageRenameScopeButton").evaluate("button => button.click()")
    rename_host = page.locator('[data-docs-viewer-management-modal-host="true"]')
    page.wait_for_selector(
        '[data-docs-viewer-management-modal-host="true"] [data-role="scope-rename-new-id"]',
        state="visible",
        timeout=timeout_ms,
    )
    if rename_host.locator('[data-role="scope-rename-target"]').count() != 1:
        raise AssertionError("Rename scope modal should contain one scope selector")
    if rename_host.locator(".docsViewerScopeLifecycle__section").count() != 0:
        raise AssertionError("Rename scope modal should not render lifecycle preview sections")
    if "Links containing the old scope id are not rewritten." not in rename_host.inner_text():
        raise AssertionError("Rename scope modal should state the manual link-rewrite boundary")
    if rename_host.locator('button[data-role="modal-primary"]').inner_text().strip() != "Rename":
        raise AssertionError("Rename scope modal should use a direct Rename action")
    rename_host.locator('button[data-role="modal-cancel"]').evaluate("button => button.click()")

    page.locator("#docsViewerManageDeleteScopeButton").evaluate("button => button.click()")
    delete_host = page.locator('[data-docs-viewer-management-modal-host="true"]')
    page.wait_for_selector(
        '[data-docs-viewer-management-modal-host="true"] [data-role="scope-delete-target"]',
        state="visible",
        timeout=timeout_ms,
    )
    delete_options = delete_host.locator('[data-role="scope-delete-target"] option').all_inner_texts()
    if not any(" - scopes/" in label for label in delete_options):
        raise AssertionError(f"External delete target should use a portable root label: {delete_options!r}")
    if any("/Users/" in label for label in delete_options):
        raise AssertionError(f"Delete target labels should not expose user-specific roots: {delete_options!r}")
    delete_host.locator('button[data-role="modal-cancel"]').evaluate("button => button.click()")

    page.goto(f"{base_url}/docs/?scope=studio&doc={INLINE_MERMAID_DOC_ID}", wait_until="domcontentloaded")
    wait_for_manage_doc(page, INLINE_MERMAID_DOC_TITLE, timeout_ms)
    page.wait_for_function(
        """() => {
            const host = document.querySelector(
                '.docsViewer__diagram[data-docs-viewer-diagram-kind="inline-mermaid"]'
            );
            return host &&
                host.children.length === 1 &&
                host.firstElementChild?.localName === 'svg' &&
                host.querySelector('title')?.textContent.trim() === 'Inline Mermaid diagram lifecycle' &&
                host.querySelector('desc')?.textContent.trim().startsWith('A document mount registers');
        }""",
        timeout=timeout_ms,
    )
    inline_state = page.locator("#docsViewerContent").evaluate(
        """content => ({
            diagrams: content.querySelectorAll(
                '.docsViewer__diagram[data-docs-viewer-diagram-kind="inline-mermaid"]'
            ).length,
            remainingFences: content.querySelectorAll('pre > code.language-mermaid').length,
            failureCount: content.querySelectorAll('.docsViewer__diagramError').length
        })"""
    )
    if inline_state != {"diagrams": 1, "remainingFences": 0, "failureCount": 0}:
        raise AssertionError(f"Studio inline Mermaid proof did not render cleanly: {inline_state!r}")
    assert_inline_mermaid_browser_review(page, timeout_ms)

    delivery_link = page.locator(
        f'#docsViewerContent a[href*="doc={INLINE_MERMAID_LINKED_DOC_ID}"]'
    ).first
    if delivery_link.count() != 1:
        raise AssertionError("Inline Mermaid theme delivery should link to its Mermaid feature")
    delivery_link.click()
    wait_for_manage_doc(page, INLINE_MERMAID_LINKED_DOC_TITLE, timeout_ms)
    if page.locator("#docsViewerContent .docsViewer__diagram").count() != 0:
        raise AssertionError("diagram-free Mermaid feature document should not acquire an inline diagram")
    page.go_back()
    wait_for_manage_doc(page, INLINE_MERMAID_DOC_TITLE, timeout_ms)
    page.wait_for_selector(
        '.docsViewer__diagram[data-docs-viewer-diagram-kind="inline-mermaid"]',
        state="visible",
        timeout=timeout_ms,
    )
    if len(inline_mermaid_requests) != 1:
        raise AssertionError(
            f"repeated mounts did not reuse the session Mermaid asset: {inline_mermaid_requests!r}"
        )
    return (
        request_paths(generated_requests),
        request_paths(import_module_requests),
        request_paths(scope_lifecycle_requests),
        request_paths(document_transfer_requests),
        request_paths(inline_mermaid_requests),
        page.url,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout-ms", type=int, default=15000)
    parser.add_argument(
        "--subscope-only",
        action="store_true",
        help="Run only the maintained managed sub-scope editing route.",
    )
    args = parser.parse_args(argv)

    server, base_url = start_server()
    try:
        assert_service_basics(base_url)
        assert_origin_rejection(base_url)
        assert_dedicated_publishability_endpoints_retired(base_url)

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            errors: list[str] = []
            if args.subscope_only:
                try:
                    page = browser.new_page()
                    page.on(
                        "pageerror",
                        lambda exc: errors.append(exc.stack or str(exc)),
                    )
                    subscope_request_log = exercise_subscope_editing_route(
                        page,
                        base_url,
                        args.timeout_ms,
                    )
                finally:
                    browser.close()
                assert_subscope_request_log(subscope_request_log)
                if errors:
                    raise AssertionError(
                        f"page errors during managed sub-scope smoke: {errors!r}"
                    )
                print(
                    "Docs Viewer managed sub-scope route OK: "
                    f"{base_url}/docs/?scope=studio"
                    f"&doc={SUBSCOPE_REPORT_DOC_ID}"
                )
                return 0
            try:
                page = browser.new_page()
                page.on("pageerror", lambda exc: errors.append(exc.stack or str(exc)))
                (
                    generated_paths,
                    import_module_paths,
                    scope_lifecycle_paths,
                    document_transfer_paths,
                    inline_mermaid_paths,
                    final_url,
                ) = exercise_manage_route(
                    page,
                    base_url,
                    args.timeout_ms,
                )
                subscope_page = browser.new_page()
                subscope_page.on(
                    "pageerror",
                    lambda exc: errors.append(exc.stack or str(exc)),
                )
                subscope_request_log = exercise_subscope_editing_route(
                    subscope_page,
                    base_url,
                    args.timeout_ms,
                )
                subscope_page.close()
            finally:
                browser.close()

        assert_generated_requests(generated_paths)
        assert_subscope_request_log(subscope_request_log)
        if "/docs-viewer/runtime/js/import/docs-html-import.js" not in import_module_paths:
            raise AssertionError(f"expected lazy Docs Import module request; saw {sorted(import_module_paths)!r}")
        if "/docs-viewer/runtime/js/management/docs-viewer-scope-lifecycle.js" not in scope_lifecycle_paths:
            raise AssertionError(f"expected lazy scope lifecycle module request; saw {sorted(scope_lifecycle_paths)!r}")
        if (
            "/docs-viewer/runtime/js/management/docs-viewer-document-transfer-workflow.js"
            not in document_transfer_paths
        ):
            raise AssertionError(
                "expected lazy document transfer module request; "
                f"saw {sorted(document_transfer_paths)!r}"
            )
        expected_mermaid_path = "/docs-viewer/runtime/vendor/mermaid/11.16.0/mermaid.min.js"
        if inline_mermaid_paths != {expected_mermaid_path}:
            raise AssertionError(f"Studio proof did not load the one checked Mermaid asset: {sorted(inline_mermaid_paths)!r}")
        if query_value(final_url, "mode"):
            raise AssertionError(f"expected clean manage URL without mode query, got {final_url}")
        if errors:
            raise AssertionError(f"page errors during Docs Viewer service smoke: {errors!r}")
        print(f"Docs Viewer service manage shell OK: {base_url}/docs/?scope=studio&doc={DOCS_VIEWER_DOC_ID}")
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
