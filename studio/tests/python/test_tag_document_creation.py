#!/usr/bin/env python3
"""Verify linked New Tag source planning, commit, and compensation."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Callable

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
STUDIO_SERVICES_DIR = REPO_ROOT / "studio" / "services"
DOCS_SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
for path in (STUDIO_SERVICES_DIR, DOCS_SERVICES_DIR):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

from tags import tag_document_creation as creation  # noqa: E402


NOW_UTC = "2026-07-29T12:00:00Z"
ADDED_DATE = "2026-07-29 13:00:00"
EXISTING_DOC_ID = "d-20260728-120000-000001"
NEW_DOC_ID = "d-20260729-130000-abcdef"


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_scope_config(repo_root: Path) -> None:
    write_json(
        repo_root / "docs-viewer/config/scopes/docs_scopes.json",
        {
            "schema_version": "docs_scopes_v3",
            "scopes": [
                {
                    "scope_id": "analysis",
                    "scope_type": "local",
                    "meta": "analysis",
                    "scope_root": {
                        "provider": "repository",
                        "path": "docs-viewer/scopes/analysis",
                    },
                    "source": {"build_media": {}},
                    "published": {
                        "media": {
                            "img": {
                                "reference_prefix": "docs/analysis/img",
                                "served_path_prefix": "/docs/media/analysis/img",
                                "build_inputs": [],
                            }
                        }
                    },
                    "public_projection": None,
                    "viewer_base_url": "/docs/",
                    "include_scope_param": True,
                    "default_doc_id": "",
                    "non_loadable_doc_ids": [],
                    "manage_only_tree_root_ids": [],
                    "allow_unresolved_parent_ids": False,
                    "sub_scopes": [
                        {
                            "sub_scope": "tags",
                            "title": "Tags",
                            "ui_statuses": [],
                            "document_groups": [
                                "subject",
                                "domain",
                                "form",
                                "theme",
                            ],
                            "public_projection": None,
                        }
                    ],
                }
            ],
        },
    )


def existing_document_source() -> str:
    return f"""---
doc_id: {EXISTING_DOC_ID}
title: trees
added_date: "2026-07-28 12:00:00"
last_updated: 2026-07-28
group: subject
parent_id: ""
viewable: true
---
# trees

Trees
"""


def prepare_repo(repo_root: Path) -> tuple[Path, Path, bytes, bytes]:
    write_json(
        repo_root / "site-tools/config/site-tools.json",
        {
            "schema_version": "site_tools_config_v1",
            "media": {"base": "https://media.example.test"},
        },
    )
    write_scope_config(repo_root)
    registry_path = (
        repo_root
        / "studio/data/canonical/tags/tag-registry.json"
    )
    write_json(
        registry_path,
        {
            "tag_registry_version": "tag_registry_v4",
            "updated_at_utc": "2026-07-28T12:00:00Z",
            "policy": {
                "allowed_groups": [
                    "subject",
                    "domain",
                    "form",
                    "theme",
                ]
            },
            "tags": [
                {
                    "tag_id": "trees",
                    "group": "subject",
                    "description": "Trees",
                    "doc_id": EXISTING_DOC_ID,
                }
            ],
        },
    )
    documents_root = (
        repo_root
        / "docs-viewer/scopes/analysis/source/sub-scopes/tags/documents"
    )
    documents_root.mkdir(parents=True)
    existing_path = documents_root / f"{EXISTING_DOC_ID}.md"
    existing_path.write_text(existing_document_source(), encoding="utf-8")
    return (
        registry_path,
        existing_path,
        registry_path.read_bytes(),
        existing_path.read_bytes(),
    )


def build_plan(repo_root: Path) -> creation.TagDocumentCreatePlan:
    return creation.build_tag_document_create_plan(
        repo_root,
        group=" Theme ",
        tag_id="Renewal",
        description=" Renewal cycle ",
        now_utc=NOW_UTC,
        added_date=ADDED_DATE,
        token_factory=lambda _size: "abcdef",
    )


def successful_rebuild(
    _repo_root: Path,
    scope: str,
    sub_scope: str,
    _changed_paths: list[Path],
    write_operation: Callable[[], Any],
    *,
    suppression_reason: str,
) -> dict[str, Any]:
    write_operation()
    return {
        "ok": True,
        "scope": scope,
        "sub_scope": sub_scope,
        "suppression_reason": suppression_reason,
    }


def test_plan_seeds_linked_registry_row_and_grouped_document(
    tmp_path: Path,
) -> None:
    registry_path, existing_path, registry_before, existing_before = (
        prepare_repo(tmp_path)
    )

    plan = build_plan(tmp_path)

    assert plan.stats == {
        "action": "create",
        "tag_id": "renewal",
        "group": "theme",
        "description": "Renewal cycle",
        "doc_id": NEW_DOC_ID,
        "added": 1,
        "final_total": 2,
    }
    assert plan.updated_registry["tags"][0]["tag_id"] == "trees"
    assert plan.updated_registry["tags"][1]["doc_id"] == NEW_DOC_ID
    front_matter, body = creation.docs_source.parse_source_text(
        plan.document_source
    )
    assert front_matter == {
        "doc_id": NEW_DOC_ID,
        "title": "renewal",
        "added_date": ADDED_DATE,
        "last_updated": "2026-07-29",
        "group": "theme",
        "parent_id": "",
        "viewable": True,
    }
    assert body == "# renewal\n\nRenewal cycle\n"
    assert registry_path.read_bytes() == registry_before
    assert existing_path.read_bytes() == existing_before
    assert not plan.document_path.exists()


def test_execute_commits_both_sources_and_preserves_existing_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry_path, existing_path, _registry_before, existing_before = (
        prepare_repo(tmp_path)
    )
    plan = build_plan(tmp_path)
    monkeypatch.setattr(
        creation.write_rebuild,
        "perform_sub_scope_source_write_and_rebuild",
        successful_rebuild,
    )

    result = creation.execute_tag_document_create(tmp_path, plan)

    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    assert registry["tags"][1]["doc_id"] == NEW_DOC_ID
    assert plan.document_path.read_text(encoding="utf-8") == plan.document_source
    assert existing_path.read_bytes() == existing_before
    assert result["document_target"] == {
        "scope": "analysis",
        "sub_scope": "tags",
        "doc_id": NEW_DOC_ID,
    }
    assert result["rebuild"]["ok"] is True


def test_rebuild_failure_restores_both_sources_and_reconciles_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry_path, existing_path, registry_before, existing_before = (
        prepare_repo(tmp_path)
    )
    plan = build_plan(tmp_path)
    calls = 0

    def fail_then_recover(
        _repo_root: Path,
        _scope: str,
        _sub_scope: str,
        _changed_paths: list[Path],
        write_operation: Callable[[], Any],
        *,
        suppression_reason: str,
    ) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        write_operation()
        if calls == 1:
            raise RuntimeError("synthetic builder failure")
        return {
            "ok": True,
            "suppression_reason": suppression_reason,
        }

    monkeypatch.setattr(
        creation.write_rebuild,
        "perform_sub_scope_source_write_and_rebuild",
        fail_then_recover,
    )

    with pytest.raises(creation.TagDocumentCreateApplyError) as captured:
        creation.execute_tag_document_create(tmp_path, plan)

    assert captured.value.payload["source_restored"] is True
    assert captured.value.payload["recovery_rebuild"]["ok"] is True
    assert captured.value.payload["retry_safe"] is True
    assert registry_path.read_bytes() == registry_before
    assert not plan.document_path.exists()
    assert existing_path.read_bytes() == existing_before


def test_existing_destination_refuses_partial_overwrite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry_path, existing_path, registry_before, existing_before = (
        prepare_repo(tmp_path)
    )
    plan = build_plan(tmp_path)
    destination_bytes = b"maintainer-owned collision\n"
    plan.document_path.write_bytes(destination_bytes)
    monkeypatch.setattr(
        creation.write_rebuild,
        "perform_sub_scope_source_write_and_rebuild",
        successful_rebuild,
    )

    with pytest.raises(creation.TagDocumentCreateApplyError) as captured:
        creation.execute_tag_document_create(tmp_path, plan)

    assert captured.value.payload["source_restored"] is False
    assert captured.value.payload["retry_safe"] is False
    assert registry_path.read_bytes() == registry_before
    assert plan.document_path.read_bytes() == destination_bytes
    assert existing_path.read_bytes() == existing_before


def test_plan_refuses_existing_partial_registry_link(
    tmp_path: Path,
) -> None:
    registry_path, existing_path, registry_before, existing_before = (
        prepare_repo(tmp_path)
    )
    existing_path.unlink()

    with pytest.raises(
        ValueError,
        match="references missing Analysis tag documents",
    ):
        build_plan(tmp_path)

    assert registry_path.read_bytes() == registry_before
    assert not existing_path.exists()
    assert existing_before


def test_execute_real_sub_scope_builder_projects_linked_document(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry_path, existing_path, _registry_before, existing_before = (
        prepare_repo(tmp_path)
    )
    report_doc_id = "d-20260728-110000-000099"
    report_path = (
        tmp_path
        / "docs-viewer/scopes/analysis/source/documents"
        / f"{report_doc_id}.md"
    )
    report_path.parent.mkdir(parents=True)
    report_path.write_text(
        f"""---
doc_id: {report_doc_id}
title: Tags
added_date: "2026-07-28 11:00:00"
last_updated: 2026-07-28
parent_id: ""
viewable: true
viewer_report: docs_subscope
viewer_report_subscope: tags
---
# Tags
""",
        encoding="utf-8",
    )
    plan = build_plan(tmp_path)
    monkeypatch.setattr(
        creation.write_rebuild,
        "DOCS_BUILDER_SCRIPT",
        str(REPO_ROOT / "docs-viewer/build/build_docs.py"),
    )

    result = creation.execute_tag_document_create(tmp_path, plan)

    manifest_path = (
        tmp_path
        / "docs-viewer/scopes/analysis/published/documents/sub-scopes/tags"
        / "manifest.json"
    )
    by_id_path = manifest_path.parent / "by-id" / f"{NEW_DOC_ID}.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    projected = json.loads(by_id_path.read_text(encoding="utf-8"))
    registry = json.loads(registry_path.read_text(encoding="utf-8"))

    assert [row["doc_id"] for row in manifest["docs"]] == [
        NEW_DOC_ID,
        EXISTING_DOC_ID,
    ]
    assert projected["doc_id"] == NEW_DOC_ID
    assert projected["title"] == "renewal"
    assert "Renewal cycle" in projected["content_html"]
    assert registry["tags"][1]["doc_id"] == NEW_DOC_ID
    assert existing_path.read_bytes() == existing_before
    assert result["rebuild"]["docs"]["mode"] == "sub_scope"
