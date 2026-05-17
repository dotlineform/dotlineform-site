#!/usr/bin/env python3
"""Focused checks for Docs Management mutation planners."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DOCS_DIR = REPO_ROOT / "scripts" / "docs"
if str(SCRIPTS_DOCS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DOCS_DIR))

import docs_management_mutations as mutations  # noqa: E402
import docs_source_model as source_model  # noqa: E402


def write_doc(root: Path, filename: str, front_matter: dict[str, object], body: str | None = None) -> None:
    path = root / "_docs" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        source_model.format_source(front_matter, body if body is not None else f"# {front_matter['title']}\n"),
        encoding="utf-8",
    )


def make_repo() -> tempfile.TemporaryDirectory[str]:
    temp_dir = tempfile.TemporaryDirectory()
    repo_root = Path(temp_dir.name)
    (repo_root / "_config.yml").write_text("title: test\n", encoding="utf-8")
    write_doc(
        repo_root,
        "archive.md",
        {
            "doc_id": "archive",
            "title": "Archive",
            "sort_order": 90,
            "published": True,
            "viewable": False,
        },
    )
    write_doc(
        repo_root,
        "parent.md",
        {
            "doc_id": "parent",
            "title": "Parent",
            "sort_order": 10,
            "published": True,
            "viewable": True,
        },
        "See /docs/?scope=studio&doc=target-child and target-child.md\n",
    )
    write_doc(
        repo_root,
        "child.md",
        {
            "doc_id": "child",
            "title": "Child",
            "parent_id": "parent",
            "sort_order": 10,
            "published": True,
            "viewable": True,
        },
    )
    write_doc(
        repo_root,
        "target.md",
        {
            "doc_id": "target",
            "title": "Target",
            "last_updated": "2026-05-01 10:00",
            "sort_order": 20,
            "summary": "old summary",
            "ui_status": "ready",
            "published": True,
            "viewable": True,
        },
    )
    write_doc(
        repo_root,
        "target-child.md",
        {
            "doc_id": "target-child",
            "title": "Target Child",
            "parent_id": "target",
            "sort_order": 10,
            "published": True,
            "viewable": True,
        },
    )
    write_doc(
        repo_root,
        "sibling.md",
        {
            "doc_id": "sibling",
            "title": "Sibling",
            "last_updated": "2026-05-02 11:00",
            "sort_order": 30,
            "published": True,
            "viewable": False,
        },
    )
    return temp_dir


def test_create_plan_selects_unique_source_path_backup_metadata_and_search_target() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        plan = mutations.plan_create(
            repo_root,
            {
                "scope": "studio",
                "title": "Target",
                "after_doc_id": "parent",
            },
        )

    assert plan.response["doc_id"] == "target-2"
    assert plan.response["record"]["parent_id"] == ""
    assert plan.response["record"]["sort_order"] == 15
    assert plan.backup_operation == "create"
    assert plan.backup_metadata is not None
    assert plan.backup_metadata["path"] == "_docs/target-2.md"
    assert plan.search_doc_ids == ["target-2"]
    assert plan.source_writes[0].path.name == "target-2.md"


def test_metadata_plan_keeps_child_search_target_for_title_changes() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        plan = mutations.plan_update_metadata(
            repo_root,
            {
                "scope": "studio",
                "doc_id": "target",
                "title": "Renamed Target",
                "parent_id": "",
                "sort_order": 20,
                "summary": "new summary",
                "ui_status": "ready",
                "viewable": True,
            },
        )

    assert plan.response["changes"]["title_changed"] is True
    assert plan.backup_docs[0].doc_id == "target"
    assert plan.backup_metadata is not None
    assert plan.backup_metadata["from_title"] == "Target"
    assert plan.search_doc_ids == ["target", "target-child"]
    assert "title: Renamed Target" in plan.source_writes[0].text
    assert 'last_updated: "2026-05-01 10:00"' in plan.source_writes[0].text


def test_metadata_status_only_plan_suppresses_search_target() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        plan = mutations.plan_update_metadata(
            repo_root,
            {
                "scope": "studio",
                "doc_id": "target",
                "title": "Target",
                "parent_id": "",
                "sort_order": 20,
                "ui_status": "review",
            },
        )

    assert plan.response["changes"]["status_changed"] is True
    assert plan.search_doc_ids == []
    assert 'last_updated: "2026-05-01 10:00"' in plan.source_writes[0].text


def test_metadata_hidden_plan_writes_hidden_and_removes_legacy_viewable() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        plan = mutations.plan_update_metadata(
            repo_root,
            {
                "scope": "studio",
                "doc_id": "target",
                "title": "Target",
                "parent_id": "",
                "sort_order": 20,
                "hidden": True,
            },
        )

    assert plan.response["record"]["hidden"] is True
    assert plan.response["record"]["viewable"] is False
    assert plan.response["changes"]["hidden_changed"] is True
    assert "hidden: true" in plan.source_writes[0].text
    assert "viewable:" not in plan.source_writes[0].text


def test_viewability_bulk_plan_expands_descendants_and_skips_unchanged_docs() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        plan = mutations.plan_update_viewability_bulk(
            repo_root,
            {
                "scope": "studio",
                "doc_ids": ["target", "target"],
                "viewable": False,
                "include_descendants": True,
            },
        )

    assert plan.response["doc_ids"] == ["target", "target-child"]
    assert plan.response["changed_doc_ids"] == ["target", "target-child"]
    assert plan.backup_operation == "update-viewability-bulk"
    assert plan.backup_metadata is not None
    assert plan.backup_metadata["requested_doc_ids"] == ["target"]
    assert plan.search_doc_ids == ["target", "target-child"]


def test_move_plan_writes_only_moved_doc_for_sparse_same_parent_reorder() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        plan = mutations.plan_move(
            repo_root,
            {
                "scope": "studio",
                "doc_id": "sibling",
                "target_doc_id": "parent",
                "position": "after",
            },
        )

    assert plan.response["record"] == {"doc_id": "sibling", "parent_id": "", "sort_order": 15}
    assert [record["doc_id"] for record in plan.response["undo_records"]] == ["sibling"]
    assert [write.path.name for write in plan.source_writes] == ["sibling.md"]
    assert plan.backup_operation is None
    assert plan.backup_metadata is None
    assert plan.search_doc_ids == []


def test_move_plan_keeps_search_target_for_reparent() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        plan = mutations.plan_move(
            repo_root,
            {
                "scope": "studio",
                "doc_id": "sibling",
                "target_doc_id": "parent",
                "position": "inside",
            },
        )

    assert plan.response["record"] == {"doc_id": "sibling", "parent_id": "parent", "sort_order": 1010}
    assert [record["doc_id"] for record in plan.response["undo_records"]] == ["sibling"]
    assert [write.path.name for write in plan.source_writes] == ["sibling.md"]
    assert plan.backup_operation is None
    assert plan.search_doc_ids == ["sibling"]


def test_normalize_order_plan_repairs_single_sibling_group_without_backup_or_search() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        plan = mutations.plan_normalize_order(
            repo_root,
            {
                "scope": "studio",
                "parent_id": "",
            },
        )

    assert plan.response["changed_doc_ids"] == ["parent", "target", "sibling", "archive"]
    assert [record["sort_order"] for record in plan.response["records"]] == [1000, 2000, 3000, 4000]
    assert [write.path.name for write in plan.source_writes] == ["parent.md", "target.md", "sibling.md", "archive.md"]
    assert plan.backup_operation is None
    assert plan.search_doc_ids == []


def test_restore_move_plan_deduplicates_records_and_searches_changed_docs() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        plan = mutations.plan_restore_move(
            repo_root,
            {
                "scope": "studio",
                "focus_doc_id": "sibling",
                "records": [
                    {"doc_id": "sibling", "parent_id": "parent", "sort_order": 40},
                    {"doc_id": "sibling", "parent_id": "", "sort_order": 30},
                ],
            },
        )

    assert plan.response["doc_id"] == "sibling"
    assert plan.response["records"] == [{"doc_id": "sibling", "parent_id": "parent", "sort_order": 40}]
    assert plan.response["changed_doc_ids"] == ["sibling"]
    assert plan.backup_operation is None
    assert plan.search_doc_ids == ["sibling"]


def test_archive_plan_preserves_already_archived_noop() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        plan = mutations.plan_archive(
            repo_root,
            {
                "scope": "studio",
                "doc_id": "archive",
            },
        )

    assert plan.has_source_changes is False
    assert plan.include_write_result_keys is False
    assert plan.response["summary_text"] == "archive is the archive parent and was not changed."


def test_archive_plan_preserves_last_updated_for_tree_metadata_change() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        plan = mutations.plan_archive(
            repo_root,
            {
                "scope": "studio",
                "doc_id": "sibling",
            },
        )

    assert plan.source_writes
    assert 'last_updated: "2026-05-02 11:00"' in plan.source_writes[0].text
    assert "parent_id: archive" in plan.source_writes[0].text


def test_delete_preview_preserves_child_blocker_and_inbound_warning() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        parent_preview = mutations.plan_delete_preview(repo_root, "studio", "target")
        target_preview = mutations.plan_delete_preview(repo_root, "studio", "target-child")

    assert parent_preview["allowed"] is False
    assert parent_preview["blockers"] == ["1 child docs still depend on this parent"]
    assert target_preview["allowed"] is True
    assert target_preview["warnings"] == ["1 inbound markdown references will become broken"]
    assert target_preview["inbound_refs"][0]["doc_id"] == "parent"


def test_delete_apply_plan_selects_backup_doc_delete_path_and_search_target() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        plan = mutations.plan_delete_apply(
            repo_root,
            {
                "scope": "studio",
                "doc_id": "target-child",
                "confirm": True,
            },
        )

    assert plan.backup_operation == "delete"
    assert plan.backup_docs[0].doc_id == "target-child"
    assert plan.backup_metadata is not None
    assert plan.backup_metadata["inbound_ref_count"] == 1
    assert plan.source_deletes[0].path.name == "target-child.md"
    assert plan.search_doc_ids == ["target-child"]


def main() -> None:
    tests = [
        test_create_plan_selects_unique_source_path_backup_metadata_and_search_target,
        test_metadata_plan_keeps_child_search_target_for_title_changes,
        test_metadata_status_only_plan_suppresses_search_target,
        test_metadata_hidden_plan_writes_hidden_and_removes_legacy_viewable,
        test_viewability_bulk_plan_expands_descendants_and_skips_unchanged_docs,
        test_move_plan_writes_only_moved_doc_for_sparse_same_parent_reorder,
        test_move_plan_keeps_search_target_for_reparent,
        test_normalize_order_plan_repairs_single_sibling_group_without_backup_or_search,
        test_restore_move_plan_deduplicates_records_and_searches_changed_docs,
        test_archive_plan_preserves_already_archived_noop,
        test_archive_plan_preserves_last_updated_for_tree_metadata_change,
        test_delete_preview_preserves_child_blocker_and_inbound_warning,
        test_delete_apply_plan_selects_backup_doc_delete_path_and_search_target,
    ]
    for test in tests:
        test()


if __name__ == "__main__":
    main()
