#!/usr/bin/env python3
"""Docs Management metadata mutation tests."""

from __future__ import annotations

import json
from pathlib import Path

from repo_factory import docs_scope_record

from docs_management_test_support import (
    docs_management_mutations,
    docs_management_service,
    make_repo,
    write_docs_scope_config,
)


def test_management_request_refreshes_scope_model_from_config() -> None:
    source_model = docs_management_mutations.source_model
    original_configs = dict(source_model.DOCS_SCOPE_CONFIGS)
    original_roots = dict(source_model.DOCUMENT_SOURCE_ROOTS)
    try:
        with make_repo() as temp_path:
            repo_root = Path(temp_path)
            write_docs_scope_config(repo_root)
            source_model.DOCUMENT_SOURCE_ROOTS["retired"] = Path("docs-viewer/scopes/retired/source/documents")
            docs_management_service.refresh_source_model_scope_configs(repo_root)
            assert list(source_model.DOCUMENT_SOURCE_ROOTS) == ["studio"]
            assert source_model.DOCUMENT_SOURCE_ROOTS["studio"] == Path("docs-viewer/scopes/studio/source/documents")
    finally:
        source_model.DOCS_SCOPE_CONFIGS.clear()
        source_model.DOCS_SCOPE_CONFIGS.update(original_configs)
        source_model.DOCUMENT_SOURCE_ROOTS.clear()
        source_model.DOCUMENT_SOURCE_ROOTS.update(original_roots)

def test_hidden_doc_is_editable_in_dry_run() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        result = docs_management_service.handle_update_metadata(
            repo_root,
            {
                "scope": "studio",
                "doc_id": "non-viewable-doc",
                "title": "Non-viewable Doc",
                "parent_id": "",
            },
            dry_run=True,
        )

    assert result["ok"] is True
    assert result["doc_id"] == "non-viewable-doc"
    assert result["record"]["parent_id"] == ""

def test_update_metadata_can_change_viewability_in_dry_run() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        result = docs_management_service.handle_update_metadata(
            repo_root,
            {
                "scope": "studio",
                "doc_id": "other",
                "title": "Other",
                "parent_id": "",
                "ui_status": "",
                "viewable": False,
            },
            dry_run=True,
        )

    assert result["ok"] is True
    assert result["record"]["viewable"] is False
    assert result["changes"]["viewable_changed"] is True
    assert result["changes"]["status_changed"] is False

def test_hidden_parent_delete_is_blocked_only_by_children() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        result = docs_management_mutations.plan_delete_preview(repo_root, "studio", "non-viewable-doc")

    assert result["allowed"] is False
    assert result["blockers"] == ["1 child docs still depend on this parent"]


def test_external_scope_default_doc_delete_uses_workspace_relative_path(tmp_path: Path, monkeypatch) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / "site-tools/config").mkdir(parents=True)
    (repo_root / "site-tools/config/site-tools.json").write_text(
        '{"schema_version":"site_tools_config_v1"}\n',
        encoding="utf-8",
    )
    projects_base = tmp_path / "projects-base"
    external_root = projects_base / "docs-viewer"
    source_root = external_root / "scopes/dlf/source"
    documents_root = source_root / "documents"
    documents_root.mkdir(parents=True)
    target_path = documents_root / "dlf.md"
    target_path.write_text(
        docs_management_mutations.source_model.format_source(
            {
                "doc_id": "dlf",
                "title": "dlf",
                "parent_id": "",
            },
            "# dlf\n",
        ),
        encoding="utf-8",
    )
    (documents_root / "analytics.md").write_text(
        docs_management_mutations.source_model.format_source(
            {
                "doc_id": "analytics",
                "title": "analytics",
                "parent_id": "",
            },
            "# analytics\n",
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(projects_base))
    config_path = repo_root / "docs-viewer/config/scopes/docs_scopes.json"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        json.dumps(
            {
                "schema_version": "docs_scopes_v3",
                "scopes": [
                    docs_scope_record("dlf", scope_type="local_external", default_doc_id="dlf")
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    source_model = docs_management_mutations.source_model
    original_configs = dict(source_model.DOCS_SCOPE_CONFIGS)
    original_roots = dict(source_model.DOCUMENT_SOURCE_ROOTS)
    original_rebuild = docs_management_service.write_rebuild.rebuild_scope_outputs
    docs_management_service.refresh_source_model_scope_configs(repo_root)
    docs_management_service.write_rebuild.rebuild_scope_outputs = lambda *_args, **_kwargs: {"ok": True}
    try:
        preview = docs_management_mutations.plan_delete_preview(repo_root, "dlf", "dlf")
        result = docs_management_service.handle_delete_apply(
            repo_root,
            {
                "scope": "dlf",
                "doc_id": "dlf",
                "confirm": True,
            },
            dry_run=False,
        )
    finally:
        source_model.DOCS_SCOPE_CONFIGS.clear()
        source_model.DOCS_SCOPE_CONFIGS.update(original_configs)
        source_model.DOCUMENT_SOURCE_ROOTS.clear()
        source_model.DOCUMENT_SOURCE_ROOTS.update(original_roots)
        docs_management_service.write_rebuild.rebuild_scope_outputs = original_rebuild

    assert preview["path"] == "scopes/dlf/source/documents/dlf.md"
    assert preview["default_doc_id_changed"] is True
    assert result["path"] == "scopes/dlf/source/documents/dlf.md"
    assert result["default_doc_id_changed"] is True
    assert result["default_doc_id"] == ""
    assert result["rebuild"] == {"ok": True}
    assert not target_path.exists()
    assert json.loads(config_path.read_text(encoding="utf-8"))["scopes"][0]["default_doc_id"] == ""
