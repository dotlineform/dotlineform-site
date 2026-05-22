#!/usr/bin/env python3
"""Focused checks for the local Studio app server."""

from __future__ import annotations

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.studio import studio_docs_api  # noqa: E402


def test_docs_capabilities_report_scopes_and_management_api() -> None:
    payload = studio_docs_api.docs_capabilities_payload(REPO_ROOT)
    capabilities = payload["capabilities"]
    studio = capabilities["scopes"]["studio"]

    assert payload["ok"] is True
    assert studio["available"] is True
    assert studio["root"] == "_docs"
    assert capabilities["docs_management"] is True
    assert capabilities["generated_data_reads"] is True
    assert capabilities["html_import"] is True
    assert capabilities["source_config_settings_reads"] is True
    assert capabilities["scope_lifecycle"]["create_apply"] is True
    assert studio["generated_data_reads"] is True
    assert studio["generated_search_reads"] is True


def test_docs_generated_read_routes_return_existing_payloads() -> None:
    params = {"scope": ["studio"]}
    index_payload = studio_docs_api.docs_generated_read_payload(
        REPO_ROOT,
        "/docs/generated/index",
        params,
    )
    search_payload = studio_docs_api.docs_generated_read_payload(
        REPO_ROOT,
        "/docs/generated/search",
        params,
    )
    doc_payload = studio_docs_api.docs_generated_read_payload(
        REPO_ROOT,
        "/docs/generated/payload",
        {"scope": ["studio"], "doc_id": ["docs-viewer"]},
    )

    assert any(doc["doc_id"] == "docs-viewer" for doc in index_payload["docs"])
    assert "entries" in search_payload
    assert doc_payload["doc_id"] == "docs-viewer"


def test_docs_management_settings_and_dry_run_mutation_routes() -> None:
    settings_payload = studio_docs_api.docs_management_get_payload(
        REPO_ROOT,
        "/docs/source-config-settings",
        {"scope": ["studio"]},
    )
    preview_status, preview_payload = studio_docs_api.docs_management_post_response(
        REPO_ROOT,
        "/docs/delete-preview",
        {"scope": "studio", "doc_id": "docs-viewer"},
        dry_run=True,
    )

    assert settings_payload["ok"] is True
    assert any(scope["scope_id"] == "studio" for scope in settings_payload["scopes"])
    assert preview_status == studio_docs_api.HTTPStatus.OK
    assert preview_payload["ok"] is True
    assert preview_payload["doc_id"] == "docs-viewer"
    assert "blockers" in preview_payload


def test_docs_api_post_rejects_disallowed_origin() -> None:
    assert studio_docs_api.docs_allowed_origin(REPO_ROOT, "http://127.0.0.1:8765") == "http://127.0.0.1:8765"
    assert studio_docs_api.docs_allowed_origin(REPO_ROOT, "https://example.com") == ""


if __name__ == "__main__":
    test_docs_capabilities_report_scopes_and_management_api()
    test_docs_generated_read_routes_return_existing_payloads()
    test_docs_management_settings_and_dry_run_mutation_routes()
    test_docs_api_post_rejects_disallowed_origin()
    print("studio app server tests OK")
