#!/usr/bin/env python3
"""Focused checks for the local Studio app server."""

from __future__ import annotations

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.studio import studio_docs_api  # noqa: E402


def test_docs_capabilities_report_scopes_but_disable_unmigrated_writes() -> None:
    payload = studio_docs_api.docs_capabilities_payload(REPO_ROOT)
    capabilities = payload["capabilities"]
    studio = capabilities["scopes"]["studio"]

    assert payload["ok"] is True
    assert studio["available"] is True
    assert studio["root"] == "_docs"
    assert capabilities["docs_management"] is False
    assert capabilities["generated_data_reads"] is True
    assert capabilities["html_import"] is False
    assert capabilities["scope_lifecycle"]["create_apply"] is False
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


if __name__ == "__main__":
    test_docs_capabilities_report_scopes_but_disable_unmigrated_writes()
    test_docs_generated_read_routes_return_existing_payloads()
    print("studio app server tests OK")
