#!/usr/bin/env python3
"""Focused safety checks for the one-time Project Notes migration."""

from __future__ import annotations

import base64
import importlib.util
import json
from pathlib import Path
import sys

import pytest

import docs_source_model as source_model
from repo_factory import (
    docs_scope_record,
    docs_sub_scope_record,
    write_docs_scope_config,
    write_site_tools_config,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = (
    REPO_ROOT
    / "docs-viewer/migrations/migrate_dotlineform_project_notes.py"
)
SPEC = importlib.util.spec_from_file_location(
    "migrate_dotlineform_project_notes",
    SCRIPT_PATH,
)
assert SPEC and SPEC.loader
migration = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = migration
SPEC.loader.exec_module(migration)


def _write(path: Path, content: str | bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")


def _fixture(tmp_path: Path, projects_base: Path) -> migration.MigrationPaths:
    repo_root = tmp_path / "repo"
    write_site_tools_config(repo_root)
    write_docs_scope_config(
        repo_root,
        [
            docs_scope_record(
                "dotlineform",
                scope_type="local_external",
                sub_scopes=[
                    docs_sub_scope_record(
                        "dotlineform",
                        "projects",
                        title="Projects",
                        sub_scope_customisation={
                            "id": "dotlineform_projects",
                            "settings": {},
                        },
                    )
                ],
            )
        ],
    )
    source_root = (
        projects_base
        / "docs-viewer/scopes/dotlineform/source/sub-scopes/projects/documents"
    )
    _write(
        source_root / "d-20260801-080000-000001.md",
        source_model.format_source(
            {
                "doc_id": "d-20260801-080000-000001",
                "title": "Existing project note",
                "added_date": "2026-08-01 08:00:00",
                "folder_path": "projects/Alpha",
            },
            "# Existing project note\n",
        ),
    )
    (projects_base / "projects/Alpha").mkdir(parents=True)
    export_root = projects_base / migration.EXPORT_RELATIVE_PATH
    _write(
        export_root / "Alpha/one.md",
        "# First note\n\nBody.\n\n![Pixel](images/pixel.png)\n\n"
        "[[media:docs/dotlineform/files/already-there.pdf]]\n",
    )
    _write(
        export_root / "Alpha/images/pixel.png",
        base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        ),
    )
    _write(
        export_root / "Alpha/two.md",
        "---\ntitle: Front matter title\n---\n\nBody.\n\n"
        "[Attachment](files/context.pdf)\n\n[Missing](files/missing.pdf)\n\n"
        "[Unsupported](files/archive.rtf)\n\n[Lost](sandbox:/mnt/data/lost.txt)\n\n"
        "[Lost again](sandbox:/mnt/data/lost.txt)\n",
    )
    _write(export_root / "Alpha/files/context.pdf", b"test-pdf")
    _write(export_root / "Alpha/files/archive.rtf", b"{\\rtf1 unsupported}")
    _write(export_root / "Orphan/note.md", "No heading, filename fallback.\n")
    return migration.MigrationPaths.resolve(
        repo_root,
        projects_base=projects_base,
        artifacts_dir=repo_root / "artifacts",
    )


def _final_plan(paths: migration.MigrationPaths) -> dict[str, object]:
    blocked = migration.plan_migration(paths)
    assert blocked == {
        "ok": False,
        "status": "review_required",
        "folders": ["Orphan"],
    }
    mapping = json.loads(paths.mapping_path.read_text(encoding="utf-8"))
    orphan = next(row for row in mapping["folders"] if row["export_folder"] == "Orphan")
    orphan["decision"] = "no_current_folder"
    paths.mapping_path.write_text(json.dumps(mapping, indent=2) + "\n", encoding="utf-8")
    tokens = iter(("a1b2c3", "b2c3d4", "c3d4e5"))
    result = migration.plan_migration(
        paths,
        added_date="2026-08-01 12:00:00",
        token_factory=lambda _size: next(tokens),
    )
    assert result["ok"] is True
    return result["plan"]


def _write_generated_manifests(
    paths: migration.MigrationPaths,
    plan: dict[str, object],
) -> None:
    output = (
        paths.projects_base
        / "docs-viewer/scopes/dotlineform/published/documents/sub-scopes/projects"
    )
    documents = plan["documents"]
    public_rows = [
        {"doc_id": document["doc_id"], "title": document["title"]}
        for document in documents
    ]
    manage_rows = []
    for document in documents:
        row = {
            "doc_id": document["doc_id"],
            "title": document["title"],
            "ui_status": "",
            "publishable": True,
            "last_updated": "",
        }
        if document["folder_path"]:
            row["customisation"] = {"folder_path": document["folder_path"]}
        manage_rows.append(row)
    _write(output / "manifest.json", json.dumps({"docs": public_rows}) + "\n")
    _write(
        output / "manage-manifest.json",
        json.dumps(
            {
                "customisation": {"id": "dotlineform_projects", "data": {}},
                "docs": manage_rows,
            }
        )
        + "\n",
    )


def test_plan_blocks_for_review_then_freezes_stable_create_only_operations(
    tmp_path: Path,
    external_data_sharing_workspace: Path,
) -> None:
    paths = _fixture(tmp_path, external_data_sharing_workspace.parent)
    plan = _final_plan(paths)
    documents = plan["documents"]

    assert [document["doc_id"] for document in documents] == [
        "d-20260801-120000-a1b2c3",
        "d-20260801-120000-b2c3d4",
        "d-20260801-120000-c3d4e5",
    ]
    assert [document["title"] for document in documents] == [
        "First note",
        "Front matter title",
        "Note",
    ]
    assert [document["folder_path"] for document in documents] == [
        "projects/Alpha",
        "projects/Alpha",
        "",
    ]
    assert any(
        exception["scheme"] == "sandbox"
        for exception in documents[1]["exceptions"]
    )
    assert sum(
        exception["scheme"] == "sandbox"
        for exception in documents[1]["exceptions"]
    ) == 2
    assert any(
        "not found" in exception["target"]
        for exception in documents[1]["exceptions"]
    )
    assert any(
        "Unsupported" in exception["target"]
        for exception in documents[1]["exceptions"]
    )
    assert any(
        exception["kind"] == "media_token"
        for exception in documents[0]["exceptions"]
    )
    assert documents[1]["media"][0]["plan"]["source_original_path"].endswith(
        "/Alpha/files/context.pdf"
    )
    assert "folder_path: projects/Alpha" in documents[0]["source_text"]
    assert "folder_path:" not in documents[2]["source_text"]
    assert not any(
        Path(document["target_source_path"].replace(
            "$DOTLINEFORM_PROJECTS_BASE_DIR",
            str(paths.projects_base),
        )).exists()
        for document in documents
    )
    media_target = migration._media_target(paths, documents[1]["media"][0]["plan"])
    assert not media_target.exists()

    repeated = migration.plan_migration(
        paths,
        token_factory=lambda _size: pytest.fail("existing plan reallocated an identity"),
    )
    assert repeated["existing"] is True
    assert repeated["plan"]["plan_revision"] == plan["plan_revision"]


def test_apply_refuses_complete_set_media_collision_before_any_write(
    tmp_path: Path,
    external_data_sharing_workspace: Path,
) -> None:
    paths = _fixture(tmp_path, external_data_sharing_workspace.parent)
    plan = _final_plan(paths)
    document = plan["documents"][1]
    media_target = migration._media_target(paths, document["media"][0]["plan"])
    _write(media_target, b"different-existing-bytes")

    with pytest.raises(RuntimeError, match="complete migration media preflight"):
        migration.apply_migration(paths)

    assert not paths.receipt_path.exists()
    assert all(
        not migration._resolve_marker_path(paths, item["target_source_path"]).exists()
        for item in plan["documents"]
    )


def test_apply_refuses_mismatched_committed_source_before_any_new_write(
    tmp_path: Path,
    external_data_sharing_workspace: Path,
) -> None:
    paths = _fixture(tmp_path, external_data_sharing_workspace.parent)
    plan = _final_plan(paths)
    first_target = migration._resolve_marker_path(
        paths,
        plan["documents"][0]["target_source_path"],
    )
    _write(first_target, "mismatched source\n")

    with pytest.raises(ValueError, match="planned source target differs"):
        migration.apply_migration(paths)

    assert not paths.receipt_path.exists()
    assert all(
        not migration._resolve_marker_path(paths, item["target_source_path"]).exists()
        for item in plan["documents"][1:]
    )


def test_apply_recovers_receipt_lag_and_retries_only_failed_rebuild(
    tmp_path: Path,
    external_data_sharing_workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = _fixture(tmp_path, external_data_sharing_workspace.parent)
    plan = _final_plan(paths)
    first = plan["documents"][0]
    first_target = migration._resolve_marker_path(paths, first["target_source_path"])
    source_model.write_text_atomic_new(first_target, first["source_text"])

    monkeypatch.setattr(
        migration.write_rebuild,
        "rebuild_sub_scope_outputs",
        lambda *_args: (_ for _ in ()).throw(RuntimeError("planned rebuild failure")),
    )
    with pytest.raises(RuntimeError, match="planned rebuild failure"):
        migration.apply_migration(paths)

    receipt = json.loads(paths.receipt_path.read_text(encoding="utf-8"))
    assert receipt["rebuild"]["status"] == "failed"
    assert set(receipt["documents"]) == {
        document["doc_id"] for document in plan["documents"]
    }

    monkeypatch.setattr(
        migration,
        "materialize_import_document_media",
        lambda *_args, **_kwargs: pytest.fail("rebuild-only retry rematerialized media"),
    )

    def rebuild_stub(*_args: object) -> dict[str, object]:
        _write_generated_manifests(paths, plan)
        return {"ok": True}

    parent_search_rebuilds: list[tuple[str, dict[str, object]]] = []

    def parent_search_stub(
        _repo_root: Path,
        scope: str,
        rebuild: dict[str, object],
    ) -> dict[str, object]:
        parent_search_rebuilds.append((scope, rebuild))
        return {**rebuild, "search": {"mode": "full", "doc_ids": []}}

    monkeypatch.setattr(
        migration.write_rebuild,
        "rebuild_sub_scope_outputs",
        rebuild_stub,
    )
    monkeypatch.setattr(
        migration.write_rebuild,
        "rebuild_parent_search_after_sub_scope",
        parent_search_stub,
    )
    result = migration.apply_migration(paths)
    validation = migration.validate_migration(paths)

    assert result["rebuild"] == "complete"
    assert parent_search_rebuilds == [("dotlineform", {"ok": True})]
    assert validation["status"] == "validated"
    assert "Explicit no-current-folder imports" in paths.result_report_path.read_text(
        encoding="utf-8"
    )
