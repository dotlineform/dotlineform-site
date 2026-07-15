#!/usr/bin/env python3
"""Focused checks for the repository document-identity migration planner."""

from __future__ import annotations

import json
from pathlib import Path

import docs_document_identity_migration as migration


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _source(doc_id: str, title: str, parent_id: str, body: str = "") -> str:
    parent_value = parent_id or '""'
    return (
        "---\n"
        f"doc_id: {doc_id}\n"
        f"title: {title}\n"
        "added_date: 2026-07-15\n"
        f"parent_id: {parent_value}\n"
        "---\n"
        f"# {title}\n\n{body}"
    )


def test_added_date_normalization_records_the_selected_evidence() -> None:
    assert migration.normalize_added_date("2026-07-15 09:44") == (
        "2026-07-15 09:44:00",
        "front-matter-time",
    )
    assert migration.normalize_added_date("2026-07-15", "2026-07-15T11:12:13+01:00") == (
        "2026-07-15 11:12:13",
        "git-time-on-matching-date",
    )
    assert migration.normalize_added_date("2026-07-15", "2026-07-16T11:12:13+01:00") == (
        "2026-07-15 00:00:00",
        "midnight-default",
    )


def test_plan_display_path_accepts_repo_relative_and_external_paths(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"

    assert migration._plan_display_path(repo_root, repo_root / "var/plan.json") == "var/plan.json"
    assert migration._plan_display_path(repo_root, tmp_path / "plan.json") == (tmp_path / "plan.json").as_posix()


def test_viewer_link_rewrite_maps_main_and_subscope_ids_without_touching_media() -> None:
    rows = [
        {
            "namespace": "analysis",
            "scope": "analysis",
            "sub_scope": "",
            "old_doc_id": "tags",
            "new_doc_id": "d-20260715-100000-aaaaaa",
        },
        {
            "namespace": "analysis/tags",
            "scope": "analysis",
            "sub_scope": "tags",
            "old_doc_id": "bird",
            "new_doc_id": "d-20260715-100001-bbbbbb",
        },
    ]
    source = (
        "[Bird](/analysis/?doc=tags&subdoc=bird)\n"
        "![Bird]([[media:docs/analysis/img/bird.webp]])\n"
    )

    rewritten, count = migration.rewrite_viewer_links(source, rows)

    assert count == 1
    assert "/analysis/?doc=d-20260715-100000-aaaaaa&subdoc=d-20260715-100001-bbbbbb" in rewritten
    assert "[[media:docs/analysis/img/bird.webp]]" in rewritten


def test_apply_plan_rewrites_source_hierarchy_links_and_config(tmp_path: Path) -> None:
    root = tmp_path
    source_root = root / "docs-viewer/source/studio"
    parent_source = _source("parent", "Parent", "")
    child_source = _source(
        "child",
        "Child",
        "parent",
        "[Parent](/docs/?scope=studio&doc=parent)\n",
    )
    _write(source_root / "parent.md", parent_source)
    _write(source_root / "child.md", child_source)
    scope_config = {
        "schema_version": "docs_scopes_v1",
        "scopes": [
            {
                "scope_id": "studio",
                "scope_type": "local",
                "source": "docs-viewer/source/studio",
                "default_doc_id": "parent",
                "non_loadable_doc_ids": [],
                "manage_only_tree_root_ids": [],
            }
        ],
    }
    _write(root / migration.SOURCE_CONFIG_PATH, json.dumps(scope_config) + "\n")
    _write(
        root / migration.SCOPE_MANIFEST_PATH,
        json.dumps(
            {
                "schema_version": "docs_scope_manifest_v1",
                "scopes": [
                    {
                        "scope_id": "studio",
                        "source_config": {"default_doc_id": "parent"},
                    }
                ],
            }
        )
        + "\n",
    )
    parent_id = "d-20260715-000000-aaaaaa"
    child_id = "d-20260715-000000-bbbbbb"
    rows = [
        {
            "namespace": "studio",
            "scope": "studio",
            "sub_scope": "",
            "source_path": "docs-viewer/source/studio/parent.md",
            "source_sha256": migration._sha256_text(parent_source),
            "old_doc_id": "parent",
            "new_doc_id": parent_id,
            "new_filename": f"{parent_id}.md",
            "old_parent_id": "",
            "new_parent_id": "",
            "normalized_added_date": "2026-07-15 00:00:00",
        },
        {
            "namespace": "studio",
            "scope": "studio",
            "sub_scope": "",
            "source_path": "docs-viewer/source/studio/child.md",
            "source_sha256": migration._sha256_text(child_source),
            "old_doc_id": "child",
            "new_doc_id": child_id,
            "new_filename": f"{child_id}.md",
            "old_parent_id": "parent",
            "new_parent_id": parent_id,
            "normalized_added_date": "2026-07-15 00:00:00",
        },
    ]

    result = migration.apply_plan(root, {"schema_version": migration.PLAN_SCHEMA, "documents": rows})

    assert result == {"documents": 2, "renamed": 2, "source_writes": 2, "config_writes": 2}
    assert not (source_root / "parent.md").exists()
    assert not (source_root / "child.md").exists()
    child_text = (source_root / f"{child_id}.md").read_text(encoding="utf-8")
    assert f"parent_id: {parent_id}" in child_text
    assert f"doc={parent_id}" in child_text
    updated_config = json.loads((root / migration.SOURCE_CONFIG_PATH).read_text(encoding="utf-8"))
    assert updated_config["scopes"][0]["default_doc_id"] == parent_id
    assert migration.verify_applied_plan(
        root,
        {"schema_version": migration.PLAN_SCHEMA, "documents": rows},
    ) == {
        "documents": 2,
        "source_paths": 2,
        "viewer_link_rewrites_remaining": 0,
        "config_files": 2,
    }
