#!/usr/bin/env python3
"""Docs Management capability and source report tests."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from docs_management_test_support import (
    docs_management_service,
    make_repo,
    write_docs_scope_config,
    write_docs_viewer_browser_config,
    write_generated_docs,
)
from docs_management_capabilities_service import capability_scope_root_label

def test_capabilities_advertise_generated_data_reads() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_docs_scope_config(repo_root)
        write_generated_docs(repo_root)
        payload = docs_management_service.capabilities_payload(repo_root)

    assert payload["capabilities"]["generated_data_reads"] is True
    assert payload["capabilities"]["scopes"]["studio"]["generated_data_reads"] is True
    assert payload["capabilities"]["scopes"]["studio"]["generated_search_reads"] is True

def test_capabilities_advertise_source_config_reads() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_docs_scope_config(repo_root)
        payload = docs_management_service.capabilities_payload(repo_root)

    assert payload["capabilities"]["source_config_reads"] is True
    assert payload["capabilities"]["source_config_settings_reads"] is True
    assert payload["capabilities"]["source_config_settings_writes"] is True
    assert payload["capabilities"]["scope_lifecycle"]["manifest"] is True
    assert payload["capabilities"]["scope_lifecycle"]["create_preview"] is True
    assert payload["capabilities"]["scope_lifecycle"]["create_apply"] is True
    assert payload["capabilities"]["scope_lifecycle"]["rename_preview"] is True
    assert payload["capabilities"]["scope_lifecycle"]["rename_apply"] is True
    assert payload["capabilities"]["scope_lifecycle"]["delete_preview"] is True
    assert payload["capabilities"]["scope_lifecycle"]["delete_apply"] is True
    assert payload["capabilities"]["scope_lifecycle"]["sub_scope_create_preview"] is True
    assert payload["capabilities"]["scope_lifecycle"]["sub_scope_create_apply"] is True
    assert payload["capabilities"]["scope_lifecycle"]["sub_scope_delete_preview"] is True
    assert payload["capabilities"]["scope_lifecycle"]["sub_scope_delete_apply"] is True
    assert payload["capabilities"]["scope_lifecycle"]["publishing_modes"] == [
        "public_readonly",
        "local_external",
        "local_committed",
    ]
    assert payload["capabilities"]["scopes"]["studio"]["sub_scope_lifecycle"]["create_eligible"] is True
    assert payload["capabilities"]["scopes"]["studio"]["sub_scope_lifecycle"]["sub_scopes"] == []
    assert payload["capabilities"]["scopes"]["studio"]["scope_lifecycle"]["rename_eligible"] is False


def test_external_scope_capability_uses_portable_root_label() -> None:
    config = SimpleNamespace(
        scope_type="local_external",
        source=Path("/Users/example/external/docs-viewer/source/research"),
    )

    label = capability_scope_root_label(Path("/repo"), "research", config)

    assert label == "source/research"


def test_missing_external_workspace_disables_only_import_and_review_capabilities(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_docs_scope_config(repo_root)
        monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(tmp_path / "missing-projects"))

        payload = docs_management_service.capabilities_payload(repo_root)

    capabilities = payload["capabilities"]
    assert capabilities["docs_management"] is True
    assert capabilities["source_editor"] is True
    assert capabilities["html_import"] is False
    assert capabilities["library_import"] is False
    assert capabilities["docs_import"]["available"] is False
    assert capabilities["docs_review"]["available"] is False
    assert capabilities["scopes"]["studio"]["available"] is True

def test_source_config_report_reads_known_config_files() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_docs_scope_config(repo_root)
        write_docs_viewer_browser_config(repo_root)
        write_generated_docs(repo_root)
        payload = docs_management_service.docs_source_config_report.build_source_config_report(repo_root)

    assert payload["ok"] is True
    assert payload["schema_version"] == "docs_source_config_report_v1"
    assert payload["source_config_path"] == "docs-viewer/config/scopes/docs_scopes.json"
    assert payload["scopes"][0]["scope_id"] == "studio"
    assert payload["scopes"][0]["source_config"]["source"] == "docs-viewer/source/studio"
    assert payload["scopes"][0]["browser_config"]["index_tree_url"] == "/docs-viewer/generated/docs/studio/index-tree.json"
    assert payload["scopes"][0]["browser_config"]["recent_url"] == "/docs-viewer/generated/docs/studio/recent.json"
    assert payload["scopes"][0]["generated"]["docs_index_tree"] == "docs-viewer/generated/docs/studio/index-tree.json"
    assert payload["scopes"][0]["generated"]["recent"] == "docs-viewer/generated/docs/studio/recent.json"
    assert payload["scopes"][0]["generated"]["search_index"] == "docs-viewer/generated/search/studio/index.json"
    assert payload["scopes"][0]["warnings"] == []
