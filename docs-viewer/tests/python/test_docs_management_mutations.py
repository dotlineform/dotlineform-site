#!/usr/bin/env python3
"""Focused checks for Docs Management mutation planners."""

from __future__ import annotations

import sys
import tempfile
import re
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
if str(DOCS_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(DOCS_SERVICES_DIR))

import docs_management_mutations as mutations  # noqa: E402
import docs_source_model as source_model  # noqa: E402
from repo_factory import (  # noqa: E402
    docs_scope_record,
    docs_sub_scope_record,
    write_docs_scope_config,
)


def write_doc(
    root: Path,
    filename: str,
    front_matter: dict[str, object],
    body: str | None = None,
    scope: str = "studio",
) -> None:
    path = root / "docs-viewer/scopes" / scope / "source/documents" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        source_model.format_source(front_matter, body if body is not None else f"# {front_matter['title']}\n"),
        encoding="utf-8",
    )


def make_repo() -> tempfile.TemporaryDirectory[str]:
    temp_dir = tempfile.TemporaryDirectory()
    repo_root = Path(temp_dir.name)
    (repo_root / "site-tools/config").mkdir(parents=True, exist_ok=True)
    (repo_root / "site-tools/config/site-tools.json").write_text(
        "{\"schema_version\":\"site_tools_config_v1\"}\n",
        encoding="utf-8",
    )
    write_docs_scope_config(
        repo_root,
        [
            docs_scope_record(
                "studio",
                sub_scopes=[
                    docs_sub_scope_record(
                        "studio",
                        "tags",
                        analysis_tag_groups=["subject", "domain", "form", "theme"],
                    )
                ],
            ),
            docs_scope_record("scratch"),
        ],
    )
    write_doc(
        repo_root,
        "non-publishable-doc.md",
        {
            "doc_id": "non-publishable-doc",
            "title": "Non-publishable Doc",
        },
        scope="scratch",
    )
    write_doc(
        repo_root,
        "non-publishable-doc.md",
        {
            "doc_id": "non-publishable-doc",
            "title": "Non-publishable Doc",
        },
    )
    write_doc(
        repo_root,
        "parent.md",
        {
            "doc_id": "parent",
            "title": "Parent",
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
        },
    )
    write_doc(
        repo_root,
        "target.md",
        {
            "doc_id": "target",
            "title": "Target",
            "date": "2026-05-03",
            "date_display": "May 2026",
            "last_updated": "2026-05-01 10:00",
            "summary": "old summary",
            "ui_status": "ready",
        },
    )
    write_doc(
        repo_root,
        "target-child.md",
        {
            "doc_id": "target-child",
            "title": "Target Child",
            "parent_id": "target",
        },
    )
    write_doc(
        repo_root,
        "sibling.md",
        {
            "doc_id": "sibling",
            "title": "Sibling",
            "last_updated": "2026-05-02 11:00",
        },
    )
    sub_scope_path = (
        repo_root
        / "docs-viewer/scopes/studio/source/sub-scopes/tags/documents/detail.md"
    )
    sub_scope_path.parent.mkdir(parents=True, exist_ok=True)
    sub_scope_path.write_text(
        source_model.format_source(
            {
                "doc_id": "detail",
                "title": "Detail",
                "summary": "old detail summary",
                "date": "2026-05-03",
                "date_display": "May 2026",
                "added_date": "2026-05-01 09:00",
                "last_updated": "2026-05-01 10:00",
                "ui_status": "draft",
                "group": "subject",
                "parent_id": "retained-parent",
                "sort_order": 4,
            },
            "# Detail\n",
        ),
        encoding="utf-8",
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

    doc_id = plan.response["doc_id"]
    assert mutations.source_model.is_immutable_doc_id(doc_id)
    assert plan.response["record"]["parent_id"] == ""
    assert plan.search_doc_ids == [doc_id]
    assert plan.source_writes[0].path.name == f"{doc_id}.md"


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
                "date": "2026-05-04",
                "date_display": "early May 2026",
                "ui_status": "ready",
            },
    )

    assert plan.response["changes"]["title_changed"] is True
    assert plan.search_doc_ids == ["target", "target-child"]
    assert "title: Renamed Target" in plan.source_writes[0].text
    assert "date: 2026-05-04" in plan.source_writes[0].text
    assert "date_display: early May 2026" in plan.source_writes[0].text
    assert 'added_date: "2026-05-01 10:00"' in plan.source_writes[0].text
    assert 'last_updated: "2026-05-01 10:00"' not in plan.source_writes[0].text
    assert re.search(r'last_updated: "\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"', plan.source_writes[0].text)


def test_metadata_plan_removes_empty_date_fields() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        plan = mutations.plan_update_metadata(
            repo_root,
            {
                "scope": "studio",
                "doc_id": "target",
                "title": "Target",
                "parent_id": "",
                "date": "",
                "date_display": "",
            },
        )

    assert plan.response["changes"]["date_changed"] is True
    assert plan.response["changes"]["date_display_changed"] is True
    assert "\ndate:" not in plan.source_writes[0].text
    assert "\ndate_display:" not in plan.source_writes[0].text


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


def test_metadata_plan_rejects_publishable() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        with pytest.raises(ValueError, match="not editable through metadata"):
            mutations.plan_update_metadata(
                repo_root,
                {
                    "scope": "studio",
                    "doc_id": "target",
                    "title": "Target",
                    "parent_id": "",
                    "publishable": False,
                },
            )


def test_sub_scope_metadata_plan_updates_common_fields_without_parentage() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        source_path = (
            repo_root
            / "docs-viewer/scopes/studio/source/sub-scopes/tags/documents/detail.md"
        )
        plan = mutations.plan_update_metadata(
            repo_root,
            {
                "scope": "studio",
                "sub_scope": "tags",
                "doc_id": "detail",
                "source_revision": source_model.source_revision(
                    source_path.read_bytes()
                ),
                "title": "Renamed Detail",
                "summary": "new detail summary",
                "date": "2026-05-04",
                "date_display": "early May 2026",
                "ui_status": "done",
            },
        )

    assert plan.sub_scope == "tags"
    assert plan.response["sub_scope"] == "tags"
    assert plan.response["record"] == {
        "doc_id": "detail",
        "title": "Renamed Detail",
        "summary": "new detail summary",
        "date": "2026-05-04",
        "date_display": "early May 2026",
        "ui_status": "done",
    }
    assert plan.response["changes"] == {
        "title_changed": True,
        "parent_changed": False,
        "summary_changed": True,
        "date_changed": True,
        "date_display_changed": True,
        "status_changed": True,
    }
    assert plan.build_doc_ids == []
    assert plan.search_doc_ids == []
    assert "parent_id: retained-parent" in plan.source_writes[0].text
    assert "sort_order: 4" in plan.source_writes[0].text
    assert "group: subject" in plan.source_writes[0].text
    assert 'added_date: "2026-05-01 09:00"' in plan.source_writes[0].text
    assert 'last_updated: "2026-05-01 10:00"' not in plan.source_writes[0].text
    assert re.search(
        r'last_updated: "\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"',
        plan.source_writes[0].text,
    )


def test_sub_scope_metadata_plan_noops_without_advancing_timestamp() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        source_path = (
            repo_root
            / "docs-viewer/scopes/studio/source/sub-scopes/tags/documents/detail.md"
        )
        plan = mutations.plan_update_metadata(
            repo_root,
            {
                "scope": "studio",
                "sub_scope": "tags",
                "doc_id": "detail",
                "source_revision": source_model.source_revision(
                    source_path.read_bytes()
                ),
                "title": "Detail",
                "summary": "old detail summary",
                "date": "2026-05-03",
                "date_display": "May 2026",
                "ui_status": "draft",
            },
        )

    assert plan.source_writes == ()
    assert "publishable" not in plan.response["record"]
    assert "group" not in plan.response["record"]
    assert "parent_id" not in plan.response["record"]
    assert all(changed is False for changed in plan.response["changes"].values())


def test_generic_metadata_rejects_group_without_a_write() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        source_path = (
            repo_root
            / "docs-viewer/scopes/studio/source/sub-scopes/tags/documents/detail.md"
        )
        before = source_path.read_bytes()
        with pytest.raises(
            ValueError,
            match="group is not editable through generic metadata",
        ):
            mutations.plan_update_metadata(
                repo_root,
                {
                    "scope": "studio",
                    "sub_scope": "tags",
                    "doc_id": "detail",
                    "source_revision": source_model.source_revision(before),
                    "title": "Detail",
                    "group": "domain",
                },
            )
        assert source_path.read_bytes() == before


def test_tag_fields_plan_updates_or_clears_only_the_exact_document() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        source_path = (
            repo_root
            / "docs-viewer/scopes/studio/source/sub-scopes/tags/documents/detail.md"
        )
        before = source_path.read_bytes()
        target = {
            "scope": "studio",
            "sub_scope": "tags",
            "doc_id": "detail",
            "source_revision": source_model.source_revision(before),
            "field_group": "tag_fields",
            "confirm": True,
        }
        updated = mutations.plan_assign_field_group(
            repo_root,
            {**target, "fields": {"group": "domain"}},
        )
        cleared = mutations.plan_assign_field_group(
            repo_root,
            {**target, "fields": {"group": ""}},
        )
        with pytest.raises(ValueError, match="not configured for the target"):
            mutations.plan_assign_field_group(
                repo_root,
                {**target, "fields": {"group": "retired"}},
            )
        with pytest.raises(
            mutations.ManagedDocumentRevisionConflict,
            match="source changed before field group assignment",
        ):
            mutations.plan_assign_field_group(
                repo_root,
                {
                    **target,
                    "source_revision": "sha256:" + ("0" * 64),
                    "fields": {"group": "domain"},
                },
            )

    assert updated.response["target"] == {
        "scope": "studio",
        "sub_scope": "tags",
        "doc_id": "detail",
    }
    assert updated.response["field_group"] == "tag_fields"
    assert updated.response["fields"] == {"group": "domain"}
    assert updated.response["changes"] == {"group_changed": True}
    assert updated.suppression_reason == "docs-assign-field-group"
    assert len(updated.source_writes) == 1
    assert updated.source_writes[0].path == source_path.resolve()
    assert "group: domain" in updated.source_writes[0].text
    assert 'last_updated: "2026-05-01 10:00"' in updated.source_writes[0].text
    assert "\ngroup:" not in cleared.source_writes[0].text


@pytest.mark.parametrize(
    ("changes", "error"),
    [
        ({"ui_status": ["draft"]}, "ui_status must be a scalar string"),
        ({"ui_status": "unknown"}, "Unknown ui_status"),
    ],
)
def test_sub_scope_metadata_plan_rejects_invalid_configured_choices(
    changes: dict[str, object],
    error: str,
) -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        source_path = (
            repo_root
            / "docs-viewer/scopes/studio/source/sub-scopes/tags/documents/detail.md"
        )
        before = source_path.read_bytes()
        with pytest.raises(ValueError, match=error):
            mutations.plan_update_metadata(
                repo_root,
                {
                    "scope": "studio",
                    "sub_scope": "tags",
                    "doc_id": "detail",
                    "source_revision": source_model.source_revision(before),
                    "title": "Detail",
                    **changes,
                },
            )
        assert source_path.read_bytes() == before


def test_sub_scope_metadata_plan_rejects_missing_or_stale_revision() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        source_path = (
            repo_root
            / "docs-viewer/scopes/studio/source/sub-scopes/tags/documents/detail.md"
        )
        before = source_path.read_bytes()
        with pytest.raises(ValueError, match="source_revision is required"):
            mutations.plan_update_metadata(
                repo_root,
                {
                    "scope": "studio",
                    "sub_scope": "tags",
                    "doc_id": "detail",
                    "title": "Detail",
                },
            )
        with pytest.raises(mutations.ManagedDocumentRevisionConflict):
            mutations.plan_update_metadata(
                repo_root,
                {
                    "scope": "studio",
                    "sub_scope": "tags",
                    "doc_id": "detail",
                    "source_revision": "sha256:" + ("0" * 64),
                    "title": "Detail",
                },
            )
        assert source_path.read_bytes() == before


def test_generic_metadata_rejects_group_for_unconfigured_collection() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_docs_scope_config(
            repo_root,
            [
                docs_scope_record(
                    "studio",
                    sub_scopes=[
                        docs_sub_scope_record(
                            "studio",
                            "tags",
                        )
                    ],
                ),
                docs_scope_record("scratch"),
            ],
        )
        source_path = (
            repo_root
            / "docs-viewer/scopes/studio/source/sub-scopes/tags/documents/detail.md"
        )
        source_path.write_text(
            source_path.read_text(encoding="utf-8").replace(
                "group: subject\n",
                "",
            ),
            encoding="utf-8",
        )
        before = source_path.read_bytes()
        with pytest.raises(
            ValueError,
            match="group is not editable through generic metadata",
        ):
            mutations.plan_update_metadata(
                repo_root,
                {
                    "scope": "studio",
                    "sub_scope": "tags",
                    "doc_id": "detail",
                    "source_revision": source_model.source_revision(before),
                    "title": "Detail",
                    "group": "",
                },
            )
        assert source_path.read_bytes() == before


def test_sub_scope_metadata_plan_rejects_any_parent_field_without_a_write() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        target_path = (
            repo_root
            / "docs-viewer/scopes/studio/source/sub-scopes/tags/documents/detail.md"
        )
        before = target_path.read_bytes()
        with pytest.raises(
            ValueError,
            match="parent_id is not editable for a sub-scope document",
        ):
            mutations.plan_update_metadata(
                repo_root,
                {
                    "scope": "studio",
                    "sub_scope": "tags",
                    "doc_id": "detail",
                    "title": "Detail",
                    "parent_id": "",
                },
            )
        assert target_path.read_bytes() == before


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


def test_delete_preview_includes_ordered_subtree_and_warning() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        parent_preview = mutations.plan_delete_preview(repo_root, "studio", ["target"])
        target_preview = mutations.plan_delete_preview(repo_root, "studio", ["target-child"])

    assert parent_preview["allowed"] is True
    assert parent_preview["blockers"] == []
    assert parent_preview["requested_doc_ids"] == ["target"]
    assert parent_preview["effective_root_doc_ids"] == ["target"]
    assert parent_preview["delete_doc_ids"] == ["target", "target-child"]
    assert parent_preview["delete_count"] == 2
    assert parent_preview["additional_descendant_count"] == 1
    assert parent_preview["warnings"] == [
        "This permanently deletes the selected document and 1 additional descendant document."
    ]
    assert target_preview["allowed"] is True
    assert target_preview["delete_doc_ids"] == ["target-child"]
    assert target_preview["warnings"] == ["This permanently deletes the selected document."]


def test_delete_preview_unions_checked_subtrees_without_duplicate_descendant_roots() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        preview = mutations.plan_delete_preview(
            repo_root,
            "studio",
            ["target-child", "target", "sibling"],
        )

    assert preview["requested_doc_ids"] == ["target-child", "target", "sibling"]
    assert preview["effective_root_doc_ids"] == ["target", "sibling"]
    assert preview["delete_doc_ids"] == ["target", "target-child", "sibling"]
    assert preview["requested_doc_count"] == 3
    assert preview["effective_root_count"] == 2
    assert preview["additional_descendant_count"] == 0
    assert preview["warnings"] == ["This permanently deletes 3 checked documents."]


def test_delete_apply_plan_selects_subtree_delete_paths_and_rebuild_targets() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        plan = mutations.plan_delete_apply(
            repo_root,
            {
                "scope": "studio",
                "doc_ids": ["target"],
                "confirm": True,
            },
        )

    assert [item.path.name for item in plan.source_deletes] == ["target.md", "target-child.md"]
    assert plan.build_doc_ids == ["target", "target-child"]
    assert plan.search_doc_ids == ["target", "target-child"]
    assert plan.response["deleted_doc_ids"] == ["target", "target-child"]
    assert plan.response["summary_text"] == "Deleted 2 documents."


def test_delete_preview_clears_default_when_descendant_is_configured_default() -> None:
    original_configured_default_doc_id = mutations.configured_default_doc_id
    mutations.configured_default_doc_id = lambda _repo_root, _scope: "target-child"
    try:
        with make_repo() as temp_path:
            repo_root = Path(temp_path)
            preview = mutations.plan_delete_preview(repo_root, "studio", ["target"])
    finally:
        mutations.configured_default_doc_id = original_configured_default_doc_id

    assert preview["default_doc_id_changed"] is True
    assert preview["default_doc_id"] == ""


def main() -> None:
    tests = [
        test_create_plan_selects_unique_source_path_and_search_target,
        test_metadata_plan_keeps_child_search_target_for_title_changes,
        test_metadata_plan_removes_empty_date_fields,
        test_metadata_status_only_plan_suppresses_search_target,
        test_metadata_plan_rejects_publishable,
        test_move_plan_noops_when_parent_is_unchanged,
        test_move_plan_keeps_search_target_for_reparent,
        test_move_plan_supports_moving_parent_subtree,
        test_delete_preview_includes_ordered_subtree_and_warning,
        test_delete_preview_unions_checked_subtrees_without_duplicate_descendant_roots,
        test_delete_apply_plan_selects_subtree_delete_paths_and_rebuild_targets,
        test_delete_preview_clears_default_when_descendant_is_configured_default,
    ]
    for test in tests:
        test()


if __name__ == "__main__":
    main()
