#!/usr/bin/env python3
"""Focused checks for the repository document-identity migration planner."""

from __future__ import annotations

import json
from pathlib import Path

import docs_document_identity_migration as migration
from repo_factory import docs_scope_record


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
        "schema_version": "docs_scopes_v2",
        "scopes": [
            docs_scope_record("studio", default_doc_id="parent")
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


def test_external_scope_plan_apply_and_verify_use_configured_marker(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo_root = tmp_path / "repo"
    projects_root = tmp_path / "projects"
    external_source = projects_root / "docs-viewer/source/notes"
    monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", projects_root.as_posix())

    parent_source = _source("tmp", "Temporary Notes", "")
    child_source = _source(
        "child",
        "Child",
        "tmp",
        (
            "[Parent](/docs/?scope=notes&doc=tmp)\n"
            "[Studio](/docs/?scope=studio&doc=legacy-studio)\n"
        ),
    )
    _write(external_source / "tmp.md", parent_source)
    _write(external_source / "child.md", child_source)
    _write(
        repo_root / migration.SOURCE_CONFIG_PATH,
        json.dumps(
            {
                "schema_version": "docs_scopes_v2",
                "scopes": [
                    docs_scope_record("notes", scope_type="local_external", default_doc_id="tmp")
                ],
            }
        )
        + "\n",
    )
    _write(
        repo_root / migration.SCOPE_MANIFEST_PATH,
        json.dumps(
            {
                "schema_version": "docs_scope_manifest_v1",
                "scopes": [
                    {
                        "scope_id": "notes",
                        "source_config": {"default_doc_id": "tmp"},
                        "source_file": (external_source / "tmp.md").as_posix(),
                    }
                ],
            }
        )
        + "\n",
    )

    studio_id = "d-20260714-120000-cccccc"
    plan = migration.build_plan(
        repo_root,
        include_external=True,
        scope_ids={"notes"},
        additional_link_rows=[
            {
                "namespace": "studio",
                "scope": "studio",
                "sub_scope": "",
                "old_doc_id": "legacy-studio",
                "new_doc_id": studio_id,
            }
        ],
    )
    rows = plan["documents"]
    by_old_id = {row["old_doc_id"]: row for row in rows}
    parent_id = by_old_id["tmp"]["new_doc_id"]
    child_id = by_old_id["child"]["new_doc_id"]

    assert plan["summary"]["scopes"] == ["notes"]
    assert plan["summary"]["renames"] == 2
    assert plan["summary"]["viewer_link_rewrites"] == 2
    assert any(
        row["namespace"] == "studio" and row["new_doc_id"] == studio_id
        for row in plan["viewer_link_mappings"]
    )
    assert by_old_id["tmp"]["source_path"] == (
        "$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/source/notes/tmp.md"
    )
    assert by_old_id["tmp"]["normalized_added_date"] == "2026-07-15 00:00:00"
    assert by_old_id["tmp"]["timestamp_evidence"] == "midnight-default"
    assert by_old_id["child"]["new_parent_id"] == parent_id
    assert migration.is_immutable_doc_id(parent_id)
    assert migration.is_immutable_doc_id(child_id)

    result = migration.apply_plan(repo_root, plan)

    assert result == {"documents": 2, "renamed": 2, "source_writes": 2, "config_writes": 2}
    assert not (external_source / "tmp.md").exists()
    assert not (external_source / "child.md").exists()
    child_text = (external_source / f"{child_id}.md").read_text(encoding="utf-8")
    assert f"parent_id: {parent_id}" in child_text
    assert f"scope=notes&doc={parent_id}" in child_text
    assert f"scope=studio&doc={studio_id}" in child_text
    updated_config = json.loads(
        (repo_root / migration.SOURCE_CONFIG_PATH).read_text(encoding="utf-8")
    )
    assert updated_config["scopes"][0]["default_doc_id"] == parent_id
    updated_manifest = json.loads(
        (repo_root / migration.SCOPE_MANIFEST_PATH).read_text(encoding="utf-8")
    )
    assert updated_manifest["scopes"][0]["source_file"] == (
        external_source / f"{parent_id}.md"
    ).as_posix()
    assert migration.verify_applied_plan(repo_root, plan) == {
        "documents": 2,
        "source_paths": 2,
        "viewer_link_rewrites_remaining": 0,
        "config_files": 2,
    }
