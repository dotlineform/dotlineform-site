#!/usr/bin/env python3
"""Focused checks for Docs Management mutation planners."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
if str(DOCS_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(DOCS_SERVICES_DIR))

import docs_management_mutations as mutations  # noqa: E402
import docs_source_model as source_model  # noqa: E402


def write_doc(
    root: Path,
    filename: str,
    front_matter: dict[str, object],
    body: str | None = None,
    scope: str = "studio",
) -> None:
    path = root / "docs-viewer/source" / scope / filename
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
        "hidden-doc.md",
        {
            "doc_id": "hidden-doc",
            "title": "Hidden Doc",
            "viewable": False,
        },
        scope="scratch",
    )
    write_doc(
        repo_root,
        "hidden-doc.md",
        {
            "doc_id": "hidden-doc",
            "title": "Hidden Doc",
            "viewable": False,
        },
    )
    write_doc(
        repo_root,
        "parent.md",
        {
            "doc_id": "parent",
            "title": "Parent",
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
            "summary": "old summary",
            "ui_status": "ready",
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
            "viewable": False,
        },
    )
    return temp_dir


def test_create_plan_selects_unique_source_path_and_search_target() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        plan = mutations.plan_create(
            repo_root,
            {
                "scope": "studio",
                "title": "Target",
                "parent_id": "",
            },
        )

    assert plan.response["doc_id"] == "target-2"
    assert plan.response["record"]["parent_id"] == ""
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
                "summary": "new summary",
                "ui_status": "ready",
                "viewable": True,
            },
    )

    assert plan.response["changes"]["title_changed"] is True
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
                "ui_status": "review",
            },
        )

    assert plan.response["changes"]["status_changed"] is True
    assert plan.search_doc_ids == []
    assert 'last_updated: "2026-05-01 10:00"' in plan.source_writes[0].text


def test_metadata_viewable_plan_writes_current_viewability() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        plan = mutations.plan_update_metadata(
            repo_root,
            {
                "scope": "studio",
                "doc_id": "target",
                "title": "Target",
                "parent_id": "",
                "viewable": False,
            },
        )

    assert plan.response["record"]["hidden"] is True
    assert plan.response["record"]["viewable"] is False
    assert plan.response["changes"]["hidden_changed"] is True
    assert "viewable: false" in plan.source_writes[0].text
    assert "hidden:" not in plan.source_writes[0].text


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
    assert plan.search_doc_ids == ["target", "target-child"]
    for write in plan.source_writes:
        assert "viewable: false" in write.text
        assert "hidden:" not in write.text


def test_move_plan_noops_when_parent_is_unchanged() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        plan = mutations.plan_move(
            repo_root,
            {
                "scope": "studio",
                "doc_id": "sibling",
                "parent_id": "",
            },
    )

    assert plan.response["record"] == {"doc_id": "sibling", "parent_id": ""}
    assert plan.source_writes == ()
    assert plan.search_doc_ids == []


def test_move_plan_keeps_search_target_for_reparent() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        plan = mutations.plan_move(
            repo_root,
            {
                "scope": "studio",
                "doc_id": "sibling",
                "parent_id": "parent",
            },
    )

    assert plan.response["record"] == {"doc_id": "sibling", "parent_id": "parent"}
    assert [write.path.name for write in plan.source_writes] == ["sibling.md"]
    assert plan.search_doc_ids == ["sibling"]


def test_move_plan_supports_moving_parent_subtree() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        plan = mutations.plan_move(
            repo_root,
            {
                "scope": "studio",
                "doc_id": "target",
                "parent_id": "parent",
            },
        )

    assert plan.response["record"] == {"doc_id": "target", "parent_id": "parent"}
    assert [write.path.name for write in plan.source_writes] == ["target.md"]
    assert plan.search_doc_ids == ["target", "target-child"]


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


def test_delete_apply_plan_selects_doc_delete_path_and_search_target() -> None:
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

    assert plan.source_deletes[0].path.name == "target-child.md"
    assert plan.search_doc_ids == ["target-child"]


def main() -> None:
    tests = [
        test_create_plan_selects_unique_source_path_and_search_target,
        test_metadata_plan_keeps_child_search_target_for_title_changes,
        test_metadata_status_only_plan_suppresses_search_target,
        test_metadata_viewable_plan_writes_current_viewability,
        test_viewability_bulk_plan_expands_descendants_and_skips_unchanged_docs,
        test_move_plan_noops_when_parent_is_unchanged,
        test_move_plan_keeps_search_target_for_reparent,
        test_move_plan_supports_moving_parent_subtree,
        test_delete_preview_preserves_child_blocker_and_inbound_warning,
        test_delete_apply_plan_selects_doc_delete_path_and_search_target,
    ]
    for test in tests:
        test()


if __name__ == "__main__":
    main()
