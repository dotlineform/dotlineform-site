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
    assert "sub_scope" not in result
    assert set(result["record"]) == {
        "doc_id",
        "title",
        "parent_id",
        "summary",
        "date",
        "date_display",
        "ui_status",
        "viewable",
    }

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


def test_sub_scope_metadata_write_rebuilds_detail_and_both_manifests(
    monkeypatch,
) -> None:
    rebuild_calls: list[dict[str, object]] = []

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
        build_result = builder.run(write=True)
        rebuild_calls.append(
            {
                "scope": scope,
                "sub_scope": sub_scope,
                "changed_paths": [path.name for path in changed_paths],
                "suppression_reason": kwargs.get("suppression_reason"),
                "changed_item_ids": build_result["write_plan"]["changed_item_ids"],
                "manifest_write": build_result["write_plan"]["manifest_write"],
            }
        )
        return {
            "ok": True,
            "docs": {"mode": "sub_scope", "sub_scope": sub_scope},
            "search": {"mode": "full", "doc_ids": []},
        }

    monkeypatch.setattr(
        docs_management_service.write_rebuild,
        "perform_sub_scope_source_write_and_rebuild",
        fake_sub_scope_rebuild,
    )
    monkeypatch.setattr(
        docs_management_mutations.source_model,
        "current_doc_timestamp",
        lambda: "2026-07-27 21:15:00",
    )

    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_scope_registry(
            repo_root,
            [
                docs_scope_record(
                    "studio",
                    allow_unresolved_parent_ids=True,
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
                    "summary": "Old summary",
                    "date": "2026-07-26",
                    "date_display": "July 2026",
                    "added_date": "2026-07-26 10:00",
                    "last_updated": "2026-07-26 11:00",
                    "ui_status": "draft",
                    "group": "subject",
                    "viewable": True,
                    "parent_id": "retained-parent",
                },
                "# Detail\n",
            ),
            encoding="utf-8",
        )
        config = load_docs_scope_configs(repo_root, scope_ids=["studio"])["studio"]
        initial_builder = SubScopeDocsBuilder(
            repo_root=repo_root,
            config=config,
            sub_scope=selected_sub_scope(config, "tags"),
        )
        initial_builder._parent_report_doc_id = ""
        initial_builder.run(write=True)
        manifest_before = read_json(
            repo_root
            / "docs-viewer/scopes/studio/published/documents/sub-scopes/tags/manifest.json"
        )
        result = docs_management_service.handle_update_metadata(
            repo_root,
            {
                "scope": "studio",
                "sub_scope": "tags",
                "doc_id": SUB_SCOPE_DOC_ID,
                "source_revision": (
                    docs_management_mutations.source_model.source_revision(
                        source_path.read_bytes()
                    )
                ),
                "title": "Renamed Detail",
                "summary": "New summary",
                "date": "2026-07-27",
                "date_display": "late July 2026",
                "ui_status": "done",
                "group": "theme",
                "viewable": False,
            },
            dry_run=False,
        )
        manage_manifest = read_json(
            repo_root
            / "docs-viewer/scopes/studio/published/documents/sub-scopes/tags/manage-manifest.json"
        )
        manifest = read_json(
            repo_root
            / "docs-viewer/scopes/studio/published/documents/sub-scopes/tags/manifest.json"
        )
        detail_payload = read_json(
            repo_root
            / f"docs-viewer/scopes/studio/published/documents/sub-scopes/tags/by-id/{SUB_SCOPE_DOC_ID}.json"
        )
        source_after = source_path.read_text(encoding="utf-8")

    assert result["record"] == {
        "doc_id": SUB_SCOPE_DOC_ID,
        "title": "Renamed Detail",
        "summary": "New summary",
        "date": "2026-07-27",
        "date_display": "late July 2026",
        "ui_status": "done",
        "group": "theme",
        "viewable": False,
    }
    assert result["sub_scope"] == "tags"
    assert manifest_before == {
        "docs": [{"doc_id": SUB_SCOPE_DOC_ID, "title": "Detail"}]
    }
    assert result["rebuild"]["docs"] == {"mode": "sub_scope", "sub_scope": "tags"}
    assert rebuild_calls == [
        {
            "scope": "studio",
            "sub_scope": "tags",
            "changed_paths": [f"{SUB_SCOPE_DOC_ID}.md"],
            "suppression_reason": "docs-update-metadata",
            "changed_item_ids": [SUB_SCOPE_DOC_ID],
            "manifest_write": True,
        }
    ]
    assert manage_manifest == {
        "customisation": {
            "id": "analysis_tags",
            "data": {
                "groups": ["subject", "domain", "form", "theme"],
            },
        },
        "docs": [
            {
                "doc_id": SUB_SCOPE_DOC_ID,
                "title": "Renamed Detail",
                "ui_status": "done",
                "viewable": False,
                "last_updated": "2026-07-27 21:15:00",
                "customisation": {"group": "theme"},
            }
        ],
    }
    assert manifest == {"docs": []}
    assert set(detail_payload) >= {"doc_id", "title", "content_html"}
    assert "viewable" not in manifest
    assert all(set(record) == {"doc_id", "title"} for record in manifest["docs"])
    assert "parent_id: retained-parent" in source_after
    assert 'last_updated: "2026-07-27 21:15:00"' in source_after


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
                "group": "theme",
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
        result = docs_management_mutations.plan_delete_preview(repo_root, "studio", ["non-viewable-doc"])

    assert result["allowed"] is True
    assert result["blockers"] == []
    assert result["delete_doc_ids"] == ["non-viewable-doc", "child"]
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
                "doc_ids": ["non-viewable-doc"],
                "confirm": True,
            },
            dry_run=False,
        )

        assert not (source_root / "non-viewable-doc.md").exists()
        assert not (source_root / "child.md").exists()
        assert (source_root / "other.md").exists()

    assert result["deleted_doc_ids"] == ["non-viewable-doc", "child"]
    assert rebuild_calls == [
        {
            "scope": "studio",
            "include_search": True,
            "search_doc_ids": ["non-viewable-doc", "child"],
            "docs_doc_ids": ["non-viewable-doc", "child"],
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
                "doc_ids": ["child", "non-viewable-doc", "other"],
                "confirm": True,
            },
            dry_run=False,
        )

        assert not (source_root / "non-viewable-doc.md").exists()
        assert not (source_root / "child.md").exists()
        assert not (source_root / "other.md").exists()

    assert result["requested_doc_ids"] == ["child", "non-viewable-doc", "other"]
    assert result["effective_root_doc_ids"] == ["non-viewable-doc", "other"]
    assert result["deleted_doc_ids"] == ["non-viewable-doc", "child", "other"]
    assert rebuild_calls == [
        {
            "scope": "studio",
            "include_search": True,
            "search_doc_ids": ["non-viewable-doc", "child", "other"],
            "docs_doc_ids": ["non-viewable-doc", "child", "other"],
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
