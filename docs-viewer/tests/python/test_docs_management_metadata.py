#!/usr/bin/env python3
"""Docs Management metadata mutation tests."""

from __future__ import annotations

from http import HTTPStatus
import json
from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_BUILD_DIR = REPO_ROOT / "docs-viewer" / "build"
if str(DOCS_BUILD_DIR) not in sys.path:
    sys.path.insert(0, str(DOCS_BUILD_DIR))

from repo_factory import (  # noqa: E402
    docs_scope_record,
    docs_sub_scope_record,
    read_json,
    write_docs_scope_config as write_scope_registry,
)
from docs_builder.sub_scope import SubScopeDocsBuilder, selected_sub_scope  # noqa: E402
from docs_scope_config import load_docs_scope_configs  # noqa: E402

from docs_management_test_support import (  # noqa: E402
    docs_management_mutations,
    docs_management_service,
    make_repo,
    write_docs_scope_config,
)

SUB_SCOPE_DOC_ID = "d-20260727-211500-a1b2c3"


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

def test_local_doc_is_editable_in_dry_run_without_publishable_metadata() -> None:
    with make_repo() as repo_name:
        repo_root = Path(repo_name)
        result = docs_management_service.handle_update_metadata(
            repo_root,
            {
                "scope": "studio",
                "doc_id": "non-publishable-doc",
                "title": "Non-publishable Doc",
                "parent_id": "",
            },
            dry_run=True,
        )

    assert result["ok"] is True
    assert result["doc_id"] == "non-publishable-doc"
    assert result["record"]["parent_id"] == ""
    assert "sub_scope" not in result
    assert set(result["record"]) == {
        "doc_id",
        "title",
        "parent_id",
        "summary",
        "date",
        "date_display",
        "ui_status",
    }

def test_update_metadata_rejects_publishable() -> None:
    with make_repo() as repo_name:
        repo_root = Path(repo_name)
        with pytest.raises(ValueError, match="not editable through metadata"):
            docs_management_service.handle_update_metadata(
                repo_root,
                {
                    "scope": "studio",
                    "doc_id": "other",
                    "title": "Other",
                    "parent_id": "",
                    "ui_status": "",
                    "publishable": False,
                },
                dry_run=True,
            )


def test_projects_subject_assignment_read_save_remove_and_strict_rejection(
    monkeypatch,
    tmp_path: Path,
) -> None:
    rebuild_calls: list[dict[str, object]] = []
    authored_body = (
        "# Architecture\n\n"
        "Existing [[catalogue:work:00638|3 symbols]] and "
        "[Folder](dlf-local:projects/architecture).\n"
    )

    def fake_sub_scope_rebuild(
        repo_root,
        scope,
        sub_scope,
        changed_paths,
        write_operation,
        **kwargs,
    ):
        write_operation()
        config = load_docs_scope_configs(repo_root, scope_ids=[scope])[scope]
        builder = SubScopeDocsBuilder(
            repo_root=repo_root,
            config=config,
            sub_scope=selected_sub_scope(config, sub_scope),
        )
        builder._parent_report_doc_id = ""
        builder.run(write=True)
        rebuild_calls.append(
            {
                "scope": scope,
                "sub_scope": sub_scope,
                "changed_paths": [path.name for path in changed_paths],
                "suppression_reason": kwargs.get("suppression_reason"),
            }
        )
        return {
            "ok": True,
            "docs": {"mode": "sub_scope", "sub_scope": sub_scope},
            "search": {"mode": "none", "doc_ids": []},
        }

    monkeypatch.setattr(
        docs_management_service.write_rebuild,
        "perform_sub_scope_source_write_and_rebuild",
        fake_sub_scope_rebuild,
    )
    projects_base = tmp_path / "Projects Base"
    projects_base.mkdir()
    monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(projects_base))

    with make_repo() as repo_name:
        repo_root = Path(repo_name)
        write_scope_registry(
            repo_root,
            [
                docs_scope_record(
                    "dotlineform",
                    sub_scopes=[
                        docs_sub_scope_record(
                            "dotlineform",
                            "projects",
                            sub_scope_customisation={
                                "id": "dotlineform_projects",
                                "settings": {},
                            },
                        )
                    ],
                )
            ],
        )
        source_path = repo_root / (
            "docs-viewer/scopes/dotlineform/source/sub-scopes/"
            f"projects/documents/{SUB_SCOPE_DOC_ID}.md"
        )
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_text(
            docs_management_mutations.source_model.format_source(
                {
                    "doc_id": SUB_SCOPE_DOC_ID,
                    "title": "Architecture",
                    "added_date": "2026-07-26 10:00:00",
                    "last_updated": "2026-07-26 11:00:00",
                    "folder_path": "projects/architecture",
                },
                authored_body,
            ),
            encoding="utf-8",
        )
        config = load_docs_scope_configs(repo_root, scope_ids=["dotlineform"])[
            "dotlineform"
        ]
        builder = SubScopeDocsBuilder(
            repo_root=repo_root,
            config=config,
            sub_scope=selected_sub_scope(config, "projects"),
        )
        builder._parent_report_doc_id = ""
        builder.run(write=True)

        metadata = docs_management_service.docs_management_get_payload(
            repo_root,
            docs_management_service.routes.METADATA_PATH,
            {
                "scope": ["dotlineform"],
                "sub_scope": ["projects"],
                "doc_id": [SUB_SCOPE_DOC_ID],
            },
        )
        revision = str(metadata["source_revision"])
        target_body = {
            "scope": "dotlineform",
            "sub_scope": "projects",
            "doc_id": SUB_SCOPE_DOC_ID,
            "source_revision": revision,
            "field_group": "authoring_subject",
            "confirm": True,
        }
        source_before_rejections = source_path.read_bytes()
        with pytest.raises(
            ValueError,
            match="fields owned by an assignable field group",
        ):
            docs_management_service.docs_management_post_response(
                repo_root,
                docs_management_service.routes.UPDATE_METADATA_PATH,
                {
                    "scope": "dotlineform",
                    "sub_scope": "projects",
                    "doc_id": SUB_SCOPE_DOC_ID,
                    "source_revision": revision,
                    "title": "Architecture",
                    "customisation": {"folder_path": "projects/other"},
                },
                dry_run=True,
            )
        invalid_assignments = [
            {
                **target_body,
                "confirm": False,
                "fields": {"folder_path": "", "work_id": "", "series_id": ""},
            },
            {
                **target_body,
                "field_group": "AUTHORING_SUBJECT",
                "fields": {"folder_path": "", "work_id": "", "series_id": ""},
            },
            {
                **target_body,
                "field_group": "unknown",
                "fields": {"folder_path": "", "work_id": "", "series_id": ""},
            },
            {
                **target_body,
                "fields": {
                    "folder_path": "",
                    "work_id": "",
                    "series_id": "",
                    "extra": "rejected",
                },
            },
            {
                **target_body,
                "fields": {
                    "folder_path": str(tmp_path / "outside"),
                    "work_id": "",
                    "series_id": "",
                },
            },
            {
                **target_body,
                "fields": {
                    "folder_path": "dlf-local:projects/architecture",
                    "work_id": "",
                    "series_id": "",
                },
            },
            {
                **target_body,
                "fields": {
                    "folder_path": "",
                    "work_id": "00123",
                    "series_id": "026",
                },
            },
        ]
        for body in invalid_assignments:
            with pytest.raises(ValueError):
                docs_management_service.docs_management_post_response(
                    repo_root,
                    docs_management_service.routes.ASSIGN_FIELD_GROUP_PATH,
                    body,
                    dry_run=True,
                )
        assert source_path.read_bytes() == source_before_rejections

        prospective = projects_base / "projects" / "Future Folder"
        status, result = docs_management_service.docs_management_post_response(
            repo_root,
            docs_management_service.routes.ASSIGN_FIELD_GROUP_PATH,
            {
                **target_body,
                "fields": {
                    "folder_path": prospective.as_uri(),
                    "work_id": "",
                    "series_id": "",
                },
            },
            dry_run=False,
        )
        linked_source = source_path.read_text(encoding="utf-8")
        linked_manifest = read_json(
            repo_root / (
                "docs-viewer/scopes/dotlineform/generated/documents/"
                "sub-scopes/projects/manage-manifest.json"
            )
        )
        linked_associations = read_json(
            repo_root / (
                "docs-viewer/scopes/dotlineform/generated/documents/"
                "sub-scopes/projects/subject-associations.json"
            )
        )

        stale_status, stale = docs_management_service.docs_management_post_response(
            repo_root,
            docs_management_service.routes.ASSIGN_FIELD_GROUP_PATH,
            {
                **target_body,
                "fields": {"folder_path": "", "work_id": "", "series_id": ""},
            },
            dry_run=False,
        )
        stale_source = source_path.read_text(encoding="utf-8")

        race_plan = docs_management_mutations.plan_assign_field_group(
            repo_root,
            {
            **target_body,
            "source_revision": result["source_revision"],
            "fields": {"folder_path": "", "work_id": "", "series_id": ""},
            },
        )
        linked_bytes = source_path.read_bytes()
        source_path.write_bytes(linked_bytes + b"\nConcurrent edit.\n")
        with pytest.raises(
            docs_management_mutations.ManagedDocumentRevisionConflict
        ) as race_error:
            docs_management_service.execute_management_mutation_plan(
                repo_root,
                race_plan,
                dry_run=False,
            )
        race_payload = race_error.value.payload
        source_path.write_bytes(linked_bytes)

        status_removed, removed = (
            docs_management_service.docs_management_post_response(
                repo_root,
                docs_management_service.routes.ASSIGN_FIELD_GROUP_PATH,
                {
                    **target_body,
                    "source_revision": result["source_revision"],
                    "fields": {"folder_path": "", "work_id": "", "series_id": ""},
                },
                dry_run=False,
            )
        )
        removed_source = source_path.read_text(encoding="utf-8")
        removed_manifest = read_json(
            repo_root / (
                "docs-viewer/scopes/dotlineform/generated/documents/"
                "sub-scopes/projects/manage-manifest.json"
            )
        )
        removed_associations = read_json(
            repo_root / (
                "docs-viewer/scopes/dotlineform/generated/documents/"
                "sub-scopes/projects/subject-associations.json"
            )
        )
        work_status, work_result = (
            docs_management_service.docs_management_post_response(
                repo_root,
                docs_management_service.routes.ASSIGN_FIELD_GROUP_PATH,
                {
                    **target_body,
                    "source_revision": removed["source_revision"],
                    "fields": {
                        "folder_path": "",
                        "work_id": "00123",
                        "series_id": "",
                    },
                },
                dry_run=False,
            )
        )
        work_source = source_path.read_text(encoding="utf-8")
        work_manifest = read_json(
            repo_root / (
                "docs-viewer/scopes/dotlineform/generated/documents/"
                "sub-scopes/projects/manage-manifest.json"
            )
        )
        work_associations = read_json(
            repo_root / (
                "docs-viewer/scopes/dotlineform/generated/documents/"
                "sub-scopes/projects/subject-associations.json"
            )
        )

    assert metadata["record"]["customisation"] == {
        "folder_path": "projects/architecture",
        "work_id": "",
        "series_id": "",
    }
    assert metadata["record"]["authoring_subject"] == {
        "state": "valid",
        "kind": "folder",
        "key": "projects/architecture",
        "fields": ["folder_path"],
    }
    assert status is HTTPStatus.OK
    assert result["target"] == {
        "scope": "dotlineform",
        "sub_scope": "projects",
        "doc_id": SUB_SCOPE_DOC_ID,
    }
    assert result["field_group"] == "authoring_subject"
    assert result["fields"] == {
        "folder_path": "projects/Future Folder",
        "work_id": "",
        "series_id": "",
    }
    assert result["changes"]["authoring_subject_changed"] is True
    assert "folder_path: projects/Future Folder" in linked_source
    assert linked_source.endswith(authored_body)
    assert 'last_updated: "2026-07-26 11:00:00"' in linked_source
    assert linked_manifest["docs"][0]["customisation"] == {
        "folder_path": "projects/Future Folder"
    }
    assert linked_associations["subject_generation"] == linked_manifest[
        "subject_generation"
    ]
    assert linked_associations["associations"][0]["subject"] == {
        "kind": "folder",
        "key": "projects/Future Folder",
    }
    assert stale_status is HTTPStatus.CONFLICT
    assert stale["operation"] == "assign_field_group"
    assert stale["retry_safe"] is False
    assert "folder_path: projects/Future Folder" in stale_source
    assert stale_source.endswith(authored_body)
    assert race_payload["operation"] == "assign_field_group"
    assert race_payload["error"] == (
        "managed document source changed before field group assignment"
    )
    assert race_payload["retry_safe"] is False
    assert status_removed is HTTPStatus.OK
    assert removed["fields"] == {
        "folder_path": "",
        "work_id": "",
        "series_id": "",
    }
    assert "folder_path:" not in removed_source
    assert removed_source.endswith(authored_body)
    assert "customisation" not in removed_manifest["docs"][0]
    assert removed_associations == {
        "schema_version": "docs_subject_associations_v1",
        "scope": "dotlineform",
        "sub_scope": "projects",
        "subject_generation": removed_manifest["subject_generation"],
        "associations": [],
    }
    assert work_status is HTTPStatus.OK
    assert work_result["fields"] == {
        "folder_path": "",
        "work_id": "00123",
        "series_id": "",
    }
    assert 'work_id: "00123"' in work_source
    assert work_source.endswith(authored_body)
    assert work_manifest["docs"][0]["authoring_subject"] == {
        "state": "valid",
        "kind": "work",
        "key": "00123",
        "fields": ["work_id"],
    }
    assert work_associations["subject_generation"] == work_manifest[
        "subject_generation"
    ]
    assert work_associations["associations"][0]["subject"] == {
        "kind": "work",
        "key": "00123",
    }
    assert rebuild_calls == [
        {
            "scope": "dotlineform",
            "sub_scope": "projects",
            "changed_paths": [f"{SUB_SCOPE_DOC_ID}.md"],
            "suppression_reason": "docs-assign-field-group",
        },
        {
            "scope": "dotlineform",
            "sub_scope": "projects",
            "changed_paths": [f"{SUB_SCOPE_DOC_ID}.md"],
            "suppression_reason": "docs-assign-field-group",
        },
        {
            "scope": "dotlineform",
            "sub_scope": "projects",
            "changed_paths": [f"{SUB_SCOPE_DOC_ID}.md"],
            "suppression_reason": "docs-assign-field-group",
        },
    ]


def test_projects_malformed_subject_remains_ordinary_metadata_saveable() -> None:
    with make_repo() as repo_name:
        repo_root = Path(repo_name)
        write_scope_registry(
            repo_root,
            [
                docs_scope_record(
                    "dotlineform",
                    sub_scopes=[
                        docs_sub_scope_record(
                            "dotlineform",
                            "projects",
                            sub_scope_customisation={
                                "id": "dotlineform_projects",
                                "settings": {},
                            },
                        )
                    ],
                )
            ],
        )
        source_path = repo_root / (
            "docs-viewer/scopes/dotlineform/source/sub-scopes/"
            f"projects/documents/{SUB_SCOPE_DOC_ID}.md"
        )
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_text(
            f"""---
doc_id: {SUB_SCOPE_DOC_ID}
title: Malformed subject
work_id: 123
---
# Malformed subject
""",
            encoding="utf-8",
        )

        plan = docs_management_mutations.plan_update_metadata(
            repo_root,
            {
                "scope": "dotlineform",
                "sub_scope": "projects",
                "doc_id": SUB_SCOPE_DOC_ID,
                "source_revision": (
                    docs_management_mutations.source_model.source_revision(
                        source_path.read_bytes()
                    )
                ),
                "title": "Renamed malformed subject",
            },
        )

    assert plan.has_source_changes is True
    assert plan.response["changes"]["title_changed"] is True
    assert "title: Renamed malformed subject" in plan.source_writes[0].text
    assert "work_id: 123" in plan.source_writes[0].text


def test_sub_scope_metadata_service_rejects_parent_without_writing(
    monkeypatch,
) -> None:
    def fail_rebuild(*_args, **_kwargs):
        raise AssertionError("rebuild must not run for a rejected sub-scope parent")

    monkeypatch.setattr(
        docs_management_service.write_rebuild,
        "perform_sub_scope_source_write_and_rebuild",
        fail_rebuild,
    )

    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_scope_registry(
            repo_root,
            [
                docs_scope_record(
                    "studio",
                    sub_scopes=[docs_sub_scope_record("studio", "tags")],
                )
            ],
        )
        source_path = (
            repo_root
            / f"docs-viewer/scopes/studio/source/sub-scopes/tags/documents/{SUB_SCOPE_DOC_ID}.md"
        )
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_text(
            docs_management_mutations.source_model.format_source(
                {
                    "doc_id": SUB_SCOPE_DOC_ID,
                    "title": "Detail",
                    "parent_id": "retained-parent",
                },
                "# Detail\n",
            ),
            encoding="utf-8",
        )
        before = source_path.read_bytes()
        with pytest.raises(
            ValueError,
            match="parent_id is not editable for a sub-scope document",
        ):
            docs_management_service.handle_update_metadata(
                repo_root,
                {
                    "scope": "studio",
                    "sub_scope": "tags",
                    "doc_id": SUB_SCOPE_DOC_ID,
                    "title": "Detail",
                    "parent_id": "",
                },
                dry_run=False,
            )
        assert source_path.read_bytes() == before


def test_sub_scope_metadata_service_returns_conflict_for_write_race(
    monkeypatch,
) -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_scope_registry(
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
                )
            ],
        )
        source_path = (
            repo_root
            / f"docs-viewer/scopes/studio/source/sub-scopes/tags/documents/{SUB_SCOPE_DOC_ID}.md"
        )
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_text(
            docs_management_mutations.source_model.format_source(
                {
                    "doc_id": SUB_SCOPE_DOC_ID,
                    "title": "Detail",
                    "ui_status": "draft",
                    "group": "subject",
                },
                "# Detail\n",
            ),
            encoding="utf-8",
        )
        original_bytes = source_path.read_bytes()
        concurrent_text = source_path.read_text(encoding="utf-8") + "\nConcurrent edit.\n"

        def race_before_write(
            _repo_root,
            _scope,
            _sub_scope,
            _changed_paths,
            write_operation,
            **_kwargs,
        ):
            source_path.write_text(concurrent_text, encoding="utf-8")
            write_operation()
            raise AssertionError("revision conflict must stop the rebuild")

        monkeypatch.setattr(
            docs_management_service.write_rebuild,
            "perform_sub_scope_source_write_and_rebuild",
            race_before_write,
        )
        status, payload = docs_management_service.docs_management_post_response(
            repo_root,
            docs_management_service.routes.UPDATE_METADATA_PATH,
            {
                "scope": "studio",
                "sub_scope": "tags",
                "doc_id": SUB_SCOPE_DOC_ID,
                "source_revision": (
                    docs_management_mutations.source_model.source_revision(
                        original_bytes
                    )
                ),
                "title": "Renamed Detail",
            },
        )

        assert status is HTTPStatus.CONFLICT
        assert payload["operation"] == "update_metadata"
        assert payload["error"] == "managed document source changed before metadata save"
        assert payload["target"] == {
            "scope": "studio",
            "sub_scope": "tags",
            "doc_id": SUB_SCOPE_DOC_ID,
        }
        assert source_path.read_text(encoding="utf-8") == concurrent_text
        assert "Renamed Detail" not in concurrent_text


def test_hidden_parent_delete_includes_children() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        result = docs_management_mutations.plan_delete_preview(repo_root, "studio", ["non-publishable-doc"])

    assert result["allowed"] is True
    assert result["blockers"] == []
    assert result["delete_doc_ids"] == ["non-publishable-doc", "child"]
    assert result["delete_count"] == 2
    assert result["additional_descendant_count"] == 1


def test_parent_delete_removes_subtree_and_rebuilds_every_deleted_id(monkeypatch) -> None:
    rebuild_calls = []

    def rebuild_scope_outputs(_repo_root, scope, **kwargs):
        rebuild_calls.append({"scope": scope, **kwargs})
        return {"ok": True}

    monkeypatch.setattr(
        docs_management_service.write_rebuild,
        "rebuild_scope_outputs",
        rebuild_scope_outputs,
    )

    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        source_root = repo_root / "docs-viewer/scopes/studio/source/documents"
        result = docs_management_service.handle_delete_apply(
            repo_root,
            {
                "scope": "studio",
                "doc_ids": ["non-publishable-doc"],
                "confirm": True,
            },
            dry_run=False,
        )

        assert not (source_root / "non-publishable-doc.md").exists()
        assert not (source_root / "child.md").exists()
        assert (source_root / "other.md").exists()

    assert result["deleted_doc_ids"] == ["non-publishable-doc", "child"]
    assert rebuild_calls == [
        {
            "scope": "studio",
            "include_search": False,
            "docs_doc_ids": ["non-publishable-doc", "child"],
            "skip_media_builds": False,
        }
    ]


def test_multi_selection_delete_applies_union_once(monkeypatch) -> None:
    rebuild_calls = []

    def rebuild_scope_outputs(_repo_root, scope, **kwargs):
        rebuild_calls.append({"scope": scope, **kwargs})
        return {"ok": True}

    monkeypatch.setattr(
        docs_management_service.write_rebuild,
        "rebuild_scope_outputs",
        rebuild_scope_outputs,
    )

    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        source_root = repo_root / "docs-viewer/scopes/studio/source/documents"
        result = docs_management_service.handle_delete_apply(
            repo_root,
            {
                "scope": "studio",
                "doc_ids": ["child", "non-publishable-doc", "other"],
                "confirm": True,
            },
            dry_run=False,
        )

        assert not (source_root / "non-publishable-doc.md").exists()
        assert not (source_root / "child.md").exists()
        assert not (source_root / "other.md").exists()

    assert result["requested_doc_ids"] == ["child", "non-publishable-doc", "other"]
    assert result["effective_root_doc_ids"] == ["non-publishable-doc", "other"]
    assert result["deleted_doc_ids"] == ["non-publishable-doc", "child", "other"]
    assert rebuild_calls == [
        {
            "scope": "studio",
            "include_search": False,
            "docs_doc_ids": ["non-publishable-doc", "child", "other"],
            "skip_media_builds": False,
        }
    ]


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
                "schema_version": "docs_scopes_v5",
                "scopes": [
                    docs_scope_record(
                        "dlf",
                        scope_type="local",
                        scope_root_provider="external_local",
                        default_doc_id="dlf",
                    )
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
        preview = docs_management_mutations.plan_delete_preview(repo_root, "dlf", ["dlf"])
        result = docs_management_service.handle_delete_apply(
            repo_root,
            {
                "scope": "dlf",
                "doc_ids": ["dlf"],
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

    assert preview["delete_documents"][0]["path"] == "scopes/dlf/source/documents/dlf.md"
    assert preview["default_doc_id_changed"] is True
    assert result["paths"] == ["scopes/dlf/source/documents/dlf.md"]
    assert result["default_doc_id_changed"] is True
    assert result["default_doc_id"] == ""
    assert result["rebuild"] == {"ok": True}
    assert not target_path.exists()
    assert json.loads(config_path.read_text(encoding="utf-8"))["scopes"][0]["default_doc_id"] == ""
