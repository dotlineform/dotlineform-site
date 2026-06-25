#!/usr/bin/env python3
"""Docs Management metadata mutation tests."""

from __future__ import annotations

from pathlib import Path

from docs_management_test_support import docs_management_mutations, docs_management_service, make_repo

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

def test_hidden_doc_viewability_can_be_changed_in_dry_run() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        result = docs_management_service.handle_update_viewability(
            repo_root,
            {
                "scope": "studio",
                "doc_id": "non-viewable-doc",
                "viewable": True,
            },
            dry_run=True,
        )

    assert result["ok"] is True
    assert result["changed_doc_ids"] == ["non-viewable-doc"]
    assert result["records"][0]["viewable"] is True

def test_hidden_parent_delete_is_blocked_only_by_children() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        result = docs_management_mutations.plan_delete_preview(repo_root, "studio", "non-viewable-doc")

    assert result["allowed"] is False
    assert result["blockers"] == ["1 child docs still depend on this parent"]
