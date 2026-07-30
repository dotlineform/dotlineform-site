#!/usr/bin/env python3
"""Docs Import collection apply, revalidation, and result contract tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import docs_import_collection_apply as collection_apply
from docs_import_collection_result import safe_generation_result
import docs_import_preview
import docs_management_import_service as management_import
import docs_source_model
import docs_watch_suppression
import docs_write_rebuild
from docs_import_document_package_collection import (
    apply_document_package_collection,
    plan_document_package_collection,
)
from docs_document_packages.workspace import configured_workspace_paths

from docs_import_test_support import handle_import_source, make_repo, write_library_doc, write_staged
from repo_factory import data_sharing_workspace_root, docs_sub_scope_record


REPORT_DOC_ID = "d-20260730-180000-000001"


def write_collection_metadata(export_id: str, records: list[dict[str, object]]) -> None:
    path = data_sharing_workspace_root() / "meta" / f"{export_id}.meta.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "data_sharing_export_meta_v1",
                "export_id": export_id,
                "app": "docs-viewer",
                "adapter_id": "documents",
                "data_domain": "documents",
                "scope": "library",
                "profile_id": "document-content",
                "config_id": "document-content",
                "target_format": "jsonl",
                "record_shape": "document_rows",
                "supports_docs_review": True,
                "supports_return_import": True,
                "content_format": "markdown",
                "selected_doc_ids": list(
                    dict.fromkeys(
                        str(record.get("doc_id") or "").strip()
                        for record in records
                        if str(record.get("doc_id") or "").strip()
                    )
                ),
            }
        )
        + "\n",
        encoding="utf-8",
    )


def write_collection(root: Path, filename: str, records: list[dict[str, object]], export_id: str) -> None:
    write_collection_metadata(export_id, records)
    write_staged(
        root,
        filename,
        [{"record_type": "data_sharing_header", "export_id": export_id}, *records],
    )


def stub_markdown_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        docs_import_preview,
        "validate_markdown_preview",
        lambda markdown, *, title="": {"ok": True, "html_chars": len(markdown), "renderer": "stub"},
    )


def configure_importable_tags_collection(root: Path) -> dict[str, Path]:
    config_path = root / "docs-viewer/config/scopes/docs_scopes.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["scopes"][0]["sub_scopes"] = [
        docs_sub_scope_record(
            "library",
            "tags",
            title="Tags",
            supports_return_import=True,
            scope_type="public",
            public_docs_path="site/assets/data/docs/scopes/library/tags",
            ui_statuses=["draft", "done"],
            document_groups=["theme"],
        )
    ]
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    parent_source_root = root / "docs-viewer/scopes/library/source/documents"
    parent_source_root.mkdir(parents=True, exist_ok=True)
    (parent_source_root / f"{REPORT_DOC_ID}.md").write_text(
        docs_source_model.format_source(
            {
                "doc_id": REPORT_DOC_ID,
                "title": "Tags",
                "viewer_report": "docs_subscope",
                "viewer_report_subscope": "tags",
            },
            "# Tags\n",
        ),
        encoding="utf-8",
    )
    source_root = (
        root
        / "docs-viewer/scopes/library/source/sub-scopes/tags/documents"
    )
    source_root.mkdir(parents=True, exist_ok=True)
    paths = {
        "tag-a": source_root / "tag-a.md",
        "tag-b": source_root / "tag-b.md",
    }
    paths["tag-a"].write_text(
        docs_source_model.format_source(
            {
                "doc_id": "tag-a",
                "title": "Tag A",
                "added_date": "2026-07-01 10:00:00",
                "last_updated": "2026-07-29 10:00:00",
                "summary": "Original A.",
                "ui_status": "draft",
                "group": "theme",
                "viewable": False,
            },
            "# Tag A\n\nOriginal A body.\n",
        ),
        encoding="utf-8",
    )
    paths["tag-b"].write_text(
        docs_source_model.format_source(
            {
                "doc_id": "tag-b",
                "title": "Tag B",
                "added_date": "2026-07-02 10:00:00",
                "last_updated": "2026-07-29 11:00:00",
                "summary": "Original B.",
                "ui_status": "done",
                "group": "theme",
            },
            "# Tag B\n\nOriginal B body.\n",
        ),
        encoding="utf-8",
    )
    return paths


def write_sub_scope_collection(
    root: Path,
    filename: str,
    records: list[dict[str, object]],
    export_id: str,
    *,
    source_last_updated: dict[str, str] | None = None,
) -> None:
    paths = configured_workspace_paths(root)
    paths.meta.mkdir(parents=True, exist_ok=True)
    selected_doc_ids = [
        str(record.get("doc_id") or "").strip()
        for record in records
        if str(record.get("doc_id") or "").strip()
    ]
    (paths.meta / f"{export_id}.meta.json").write_text(
        json.dumps(
            {
                "schema_version": "data_sharing_export_meta_v1",
                "export_id": export_id,
                "app": "docs-viewer",
                "adapter_id": "documents",
                "data_domain": "documents",
                "scope": "library",
                "sub_scope": "tags",
                "profile_id": "document-content",
                "config_id": "document-content",
                "target_format": "jsonl",
                "record_shape": "document_rows",
                "supports_docs_review": True,
                "supports_return_import": True,
                "content_format": "markdown",
                "selected_doc_ids": selected_doc_ids,
                "source_last_updated": source_last_updated or {
                    "tag-a": "2026-07-29 10:00:00",
                    "tag-b": "2026-07-29 11:00:00",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    write_staged(
        root,
        filename,
        [
            {
                "record_type": "data_sharing_header",
                "schema_version": "data_sharing_returned_package_v1",
                "export_id": export_id,
            },
            *records,
        ],
    )


def sub_scope_preview(root: Path, filename: str) -> dict[str, object]:
    return management_import.handle_import_source(
        root,
        {
            "scope": "library",
            "sub_scope": "tags",
            "staged_filename": filename,
            "preview_only": True,
        },
        dry_run=False,
    )


def sub_scope_apply(
    root: Path,
    filename: str,
    preview: dict[str, object],
) -> dict[str, object]:
    package = preview["package"]
    assert isinstance(package, dict)
    return management_import.handle_import_source(
        root,
        {
            "scope": "library",
            "sub_scope": "tags",
            "staged_filename": filename,
            "preview_only": False,
            "confirm": True,
            "export_id": package["export_id"],
            "source_sha256": package["source_sha256"],
            **(
                {
                    "trusted_metadata_sha256": package[
                        "trusted_metadata_sha256"
                    ]
                }
                if package.get("trusted_metadata_sha256")
                else {}
            ),
            "planned_identities": preview["planned_identities"],
            "planned_actions": preview["planned_actions"],
        },
        dry_run=False,
    )


def successful_child_rebuild(calls: list[dict[str, object]]):
    def perform(repo_root, scope, sub_scope, changed_paths, write_operation, **kwargs):
        write_operation()
        calls.append(
            {
                "scope": scope,
                "sub_scope": sub_scope,
                "changed_paths": [path.name for path in changed_paths],
                "reason": kwargs.get("suppression_reason"),
            }
        )
        return {
            "ok": True,
            "docs": {
                "mode": "sub_scope",
                "sub_scope": sub_scope,
                "doc_ids": [],
            },
            "search": {"mode": "none", "doc_ids": []},
        }

    return perform


def fake_rebuild(calls: list[dict[str, object]], *, fail_generation: bool = False):
    def perform(repo_root, scope, changed_paths, write_operation, **kwargs):
        write_operation()
        calls.append(
            {
                "scope": scope,
                "changed_paths": [path.name for path in changed_paths],
                "docs_doc_ids": list(kwargs.get("docs_doc_ids") or []),
                "search_doc_ids": list(kwargs.get("search_doc_ids") or []),
            }
        )
        if fail_generation:
            raise RuntimeError("simulated generation failure")
        return {
            "ok": True,
            "docs": {"mode": "targeted", "doc_ids": list(kwargs.get("docs_doc_ids") or [])},
            "search": {"mode": "targeted", "doc_ids": list(kwargs.get("search_doc_ids") or [])},
        }

    return perform


def apply_package(
    root: Path,
    filename: str,
    *,
    rebuild,
    logs: list[tuple[str, dict[str, object]]] | None = None,
    export_id: str | None = None,
    source_sha256: str | None = None,
    planned_actions: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    paths = configured_workspace_paths(root)
    preview = plan_document_package_collection(
        root,
        scope="library",
        staged_filename=filename,
        staging_root=paths.import_staging,
        workspace_root=paths.root,
        metadata_root=paths.meta,
    ).as_dict()
    return apply_document_package_collection(
        root,
        scope="library",
        staged_filename=filename,
        body={
            "scope": "library",
            "staged_filename": filename,
            "preview_only": False,
            "confirm": True,
            "planned_identities": preview.get("planned_identities", []),
            "planned_actions": (
                planned_actions
                if planned_actions is not None
                else preview.get("planned_actions", [])
            ),
            "export_id": export_id if export_id is not None else preview.get("package", {}).get("export_id", ""),
            "source_sha256": source_sha256 if source_sha256 is not None else preview.get("package", {}).get("source_sha256", ""),
        },
        staging_root=paths.import_staging,
        workspace_root=paths.root,
        metadata_root=paths.meta,
        log_event=lambda _root, event, details: (logs.append((event, details)) if logs is not None else None),
        perform_source_write_and_rebuild=rebuild,
    )


def test_sub_scope_package_preview_and_apply_overwrites_every_exact_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stub_markdown_validation(monkeypatch)
    rebuild_calls: list[dict[str, object]] = []
    monkeypatch.setattr(
        docs_write_rebuild,
        "perform_source_write_and_rebuild",
        lambda *_args, **_kwargs: pytest.fail("parent rebuild must not run"),
    )
    monkeypatch.setattr(
        docs_write_rebuild,
        "perform_sub_scope_source_write_and_rebuild",
        successful_child_rebuild(rebuild_calls),
    )
    with make_repo() as temp:
        root = Path(temp)
        paths = configure_importable_tags_collection(root)
        original_sources = {
            doc_id: path.read_bytes()
            for doc_id, path in paths.items()
        }
        write_sub_scope_collection(
            root,
            "sub-scope-apply.jsonl",
            [
                {
                    "doc_id": "tag-a",
                    "title": "Returned Tag A",
                    "summary": "Returned A summary.",
                    "viewable": True,
                    "content": "# Returned Tag A\n\nReturned A body.",
                },
                {
                    "doc_id": "tag-b",
                    "title": "Returned Tag B",
                    "summary": "Returned B summary.",
                    "content": "# Returned Tag B\n\nReturned B body.",
                },
            ],
            "ds_20260730T180001Z",
        )

        preview = sub_scope_preview(root, "sub-scope-apply.jsonl")

        assert {doc_id: path.read_bytes() for doc_id, path in paths.items()} == original_sources
        assert preview["ready_for_confirmation"] is True
        assert preview["target"] == {"scope": "library", "sub_scope": "tags"}
        assert preview["counts"]["records"] == 2
        assert preview["counts"]["creates"] == 0
        assert preview["counts"]["collisions"] == 2
        assert [row["action"] for row in preview["records"]] == [
            "overwrite",
            "overwrite",
        ]
        assert preview["planned_identities"] == []

        payload = sub_scope_apply(root, "sub-scope-apply.jsonl", preview)
        tag_a_front_matter, tag_a_body = docs_source_model.parse_source(paths["tag-a"])
        tag_b_front_matter, tag_b_body = docs_source_model.parse_source(paths["tag-b"])

    assert payload["outcome"] == "completed"
    assert payload["target"] == {"scope": "library", "sub_scope": "tags"}
    assert payload["viewer_url"] == (
        f"/docs/?scope=library&doc={REPORT_DOC_ID}"
    )
    assert payload["counts"] == {
        "created": 0,
        "overwritten": 2,
        "failed": 0,
        "not_attempted": 0,
    }
    assert payload["rollback"]["status"] == "not-needed"
    assert rebuild_calls == [
        {
            "scope": "library",
            "sub_scope": "tags",
            "changed_paths": ["tag-a.md", "tag-b.md"],
            "reason": "docs-import-sub-scope-collection-apply",
        }
    ]
    assert tag_a_front_matter["doc_id"] == "tag-a"
    assert tag_a_front_matter["added_date"] == "2026-07-01 10:00:00"
    assert tag_a_front_matter["group"] == "theme"
    assert tag_a_front_matter["ui_status"] == "draft"
    assert tag_a_front_matter["viewable"] is False
    assert tag_a_front_matter["title"] == "Returned Tag A"
    assert tag_a_front_matter["summary"] == "Returned A summary."
    assert "Returned A body." in tag_a_body
    assert tag_b_front_matter["doc_id"] == "tag-b"
    assert tag_b_front_matter["added_date"] == "2026-07-02 10:00:00"
    assert tag_b_front_matter["group"] == "theme"
    assert tag_b_front_matter["ui_status"] == "done"
    assert tag_b_front_matter["title"] == "Returned Tag B"
    assert tag_b_front_matter["summary"] == "Returned B summary."
    assert "Returned B body." in tag_b_body


def test_sub_scope_package_apply_requires_exact_report_before_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stub_markdown_validation(monkeypatch)
    monkeypatch.setattr(
        docs_write_rebuild,
        "perform_sub_scope_source_write_and_rebuild",
        lambda *_args, **_kwargs: pytest.fail(
            "unroutable child collection must fail before writing"
        ),
    )
    with make_repo() as temp:
        root = Path(temp)
        paths = configure_importable_tags_collection(root)
        originals = {
            doc_id: path.read_bytes()
            for doc_id, path in paths.items()
        }
        (
            root
            / "docs-viewer/scopes/library/source/documents"
            / f"{REPORT_DOC_ID}.md"
        ).unlink()
        write_sub_scope_collection(
            root,
            "sub-scope-missing-report.jsonl",
            [
                {
                    "doc_id": "tag-a",
                    "title": "Returned Tag A",
                    "content": "Returned body.",
                },
            ],
            "ds_20260730T180010Z",
        )
        preview = sub_scope_preview(root, "sub-scope-missing-report.jsonl")

        with pytest.raises(
            ValueError,
            match=(
                "Docs Viewer sub-scope report must resolve exactly once "
                "for library/tags; found 0"
            ),
        ):
            sub_scope_apply(root, "sub-scope-missing-report.jsonl", preview)

        assert {
            doc_id: path.read_bytes()
            for doc_id, path in paths.items()
        } == originals


def test_sub_scope_package_blocks_stale_sources_and_hierarchy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stub_markdown_validation(monkeypatch)
    with make_repo() as temp:
        root = Path(temp)
        configure_importable_tags_collection(root)
        write_sub_scope_collection(
            root,
            "sub-scope-stale.jsonl",
            [
                {
                    "doc_id": "tag-a",
                    "title": "Returned Tag A",
                    "content": "Returned body.",
                },
            ],
            "ds_20260730T180002Z",
            source_last_updated={"tag-a": "2026-07-28 10:00:00"},
        )
        stale = sub_scope_preview(root, "sub-scope-stale.jsonl")

        write_sub_scope_collection(
            root,
            "sub-scope-hierarchy.jsonl",
            [
                {
                    "doc_id": "tag-b",
                    "title": "Returned Tag B",
                    "parent_id": "tag-a",
                    "content": "Returned body.",
                },
            ],
            "ds_20260730T180003Z",
            source_last_updated={"tag-b": "2026-07-29 11:00:00"},
        )
        hierarchy = sub_scope_preview(root, "sub-scope-hierarchy.jsonl")
        tag_b_path = (
            root
            / "docs-viewer/scopes/library/source/sub-scopes/tags/documents/tag-b.md"
        )
        tag_b_path.write_text(
            tag_b_path.read_text(encoding="utf-8").replace(
                "group: theme\n",
                "group: theme\nparent_id: tag-a\n",
            ),
            encoding="utf-8",
        )
        write_sub_scope_collection(
            root,
            "sub-scope-non-flat-target.jsonl",
            [
                {
                    "doc_id": "tag-b",
                    "title": "Returned Tag B",
                    "content": "Returned body.",
                },
            ],
            "ds_20260730T180008Z",
            source_last_updated={"tag-b": "2026-07-29 11:00:00"},
        )
        non_flat_target = sub_scope_preview(
            root,
            "sub-scope-non-flat-target.jsonl",
        )

    assert stale["ready_for_confirmation"] is False
    assert "stale_prepared_sources" in {
        blocker["code"]
        for blocker in stale["blockers"]
    }
    assert hierarchy["ready_for_confirmation"] is False
    assert hierarchy["counts"]["creates"] == 0
    assert "sub_scope_hierarchy_not_allowed" in {
        blocker["code"]
        for blocker in hierarchy["blockers"]
    }
    assert "non_flat_sub_scope_target" in {
        blocker["code"]
        for blocker in non_flat_target["blockers"]
    }


def test_sub_scope_package_apply_requires_reconfirmation_after_source_change(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stub_markdown_validation(monkeypatch)
    rebuild_calls: list[dict[str, object]] = []
    monkeypatch.setattr(
        docs_write_rebuild,
        "perform_sub_scope_source_write_and_rebuild",
        successful_child_rebuild(rebuild_calls),
    )
    with make_repo() as temp:
        root = Path(temp)
        paths = configure_importable_tags_collection(root)
        write_sub_scope_collection(
            root,
            "sub-scope-reconfirm.jsonl",
            [
                {
                    "doc_id": "tag-a",
                    "title": "Returned Tag A",
                    "content": "Returned body.",
                },
            ],
            "ds_20260730T180004Z",
            source_last_updated={"tag-a": "2026-07-29 10:00:00"},
        )
        preview = sub_scope_preview(root, "sub-scope-reconfirm.jsonl")
        paths["tag-a"].write_text(
            paths["tag-a"].read_text(encoding="utf-8").replace(
                "last_updated: \"2026-07-29 10:00:00\"",
                "last_updated: \"2026-07-30 18:00:00\"",
            ),
            encoding="utf-8",
        )

        refreshed = sub_scope_apply(root, "sub-scope-reconfirm.jsonl", preview)

    assert refreshed["preview_only"] is True
    assert refreshed["reconfirmation_required"] is True
    assert refreshed["ready_for_confirmation"] is False
    assert "stale_prepared_sources" in {
        blocker["code"]
        for blocker in refreshed["blockers"]
    }
    assert rebuild_calls == []


def test_sub_scope_package_apply_reconfirms_trusted_metadata_change(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stub_markdown_validation(monkeypatch)
    with make_repo() as temp:
        root = Path(temp)
        configure_importable_tags_collection(root)
        export_id = "ds_20260730T180009Z"
        write_sub_scope_collection(
            root,
            "sub-scope-metadata-change.jsonl",
            [
                {
                    "doc_id": "tag-a",
                    "title": "Returned Tag A",
                    "content": "Returned body.",
                },
            ],
            export_id,
            source_last_updated={"tag-a": "2026-07-29 10:00:00"},
        )
        preview = sub_scope_preview(root, "sub-scope-metadata-change.jsonl")
        metadata_path = configured_workspace_paths(root).meta / f"{export_id}.meta.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata["generated_at"] = "2026-07-30T18:00:09Z"
        metadata_path.write_text(json.dumps(metadata) + "\n", encoding="utf-8")

        refreshed = sub_scope_apply(
            root,
            "sub-scope-metadata-change.jsonl",
            preview,
        )

    assert refreshed["preview_only"] is True
    assert refreshed["reconfirmation_required"] is True
    assert refreshed["revalidation_issues"] == [
        {
            "level": "warning",
            "code": "package_identity_changed",
            "message": "trusted package metadata changed; review the refreshed plan",
        }
    ]


def test_sub_scope_package_apply_rechecks_snapshot_inside_write_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stub_markdown_validation(monkeypatch)
    original_boundary = docs_write_rebuild.perform_sub_scope_source_write_and_rebuild
    raced = False

    def race_boundary(
        repo_root,
        scope,
        sub_scope,
        changed_paths,
        write_operation,
        **kwargs,
    ):
        nonlocal raced
        snapshots = kwargs.get("source_snapshots")
        if isinstance(snapshots, dict) and not raced:
            raced = True
            first_path = next(iter(snapshots))
            first_path.write_text(
                first_path.read_text(encoding="utf-8") + "\nExternal concurrent edit.\n",
                encoding="utf-8",
            )
        return original_boundary(
            repo_root,
            scope,
            sub_scope,
            changed_paths,
            write_operation,
            **kwargs,
        )

    monkeypatch.setattr(
        docs_write_rebuild,
        "perform_sub_scope_source_write_and_rebuild",
        race_boundary,
    )
    with make_repo() as temp:
        root = Path(temp)
        paths = configure_importable_tags_collection(root)
        write_sub_scope_collection(
            root,
            "sub-scope-write-race.jsonl",
            [
                {
                    "doc_id": "tag-a",
                    "title": "Returned Tag A",
                    "content": "Returned body.",
                },
            ],
            "ds_20260730T180007Z",
            source_last_updated={"tag-a": "2026-07-29 10:00:00"},
        )
        preview = sub_scope_preview(root, "sub-scope-write-race.jsonl")

        refreshed = sub_scope_apply(root, "sub-scope-write-race.jsonl", preview)
        source_after = paths["tag-a"].read_text(encoding="utf-8")

    assert raced is True
    assert refreshed["preview_only"] is True
    assert refreshed["reconfirmation_required"] is True
    assert refreshed["revalidation_issues"][0]["code"] == "target_state_changed"
    assert "External concurrent edit." in source_after
    assert "Returned body." not in source_after


@pytest.mark.parametrize("failure_mode", ["source-write", "rebuild"])
def test_sub_scope_package_failure_restores_every_source_and_rebuilds_snapshot(
    monkeypatch: pytest.MonkeyPatch,
    failure_mode: str,
) -> None:
    stub_markdown_validation(monkeypatch)
    rebuild_attempts: list[str] = []
    original_apply = collection_apply.apply_import_document_source
    original_boundary = docs_write_rebuild.perform_sub_scope_source_write_and_rebuild
    source_write_count = 0
    rebuild_count = 0

    def apply_source(document_plan):
        nonlocal source_write_count
        source_write_count += 1
        if failure_mode == "source-write" and source_write_count == 2:
            raise RuntimeError("simulated second source-write failure")
        original_apply(document_plan)

    def rebuild_child(
        repo_root,
        scope,
        sub_scope,
        changed_paths,
        write_operation,
        **kwargs,
    ):
        rebuild_attempts.append(str(kwargs.get("suppression_reason") or ""))
        return original_boundary(
            repo_root,
            scope,
            sub_scope,
            changed_paths,
            write_operation,
            **kwargs,
        )

    def rebuild_outputs(repo_root, scope, sub_scope):
        nonlocal rebuild_count
        rebuild_count += 1
        if failure_mode == "rebuild" and rebuild_count == 1:
            raise RuntimeError("simulated confined rebuild failure")
        return {
            "ok": True,
            "docs": {
                "mode": "sub_scope",
                "sub_scope": sub_scope,
                "doc_ids": [],
            },
            "search": {"mode": "none", "doc_ids": []},
        }

    monkeypatch.setattr(collection_apply, "apply_import_document_source", apply_source)
    monkeypatch.setattr(
        docs_write_rebuild,
        "perform_sub_scope_source_write_and_rebuild",
        rebuild_child,
    )
    monkeypatch.setattr(
        docs_write_rebuild,
        "rebuild_sub_scope_outputs",
        rebuild_outputs,
    )
    with make_repo() as temp:
        root = Path(temp)
        paths = configure_importable_tags_collection(root)
        originals = {
            doc_id: path.read_bytes()
            for doc_id, path in paths.items()
        }
        write_sub_scope_collection(
            root,
            f"sub-scope-{failure_mode}.jsonl",
            [
                {
                    "doc_id": "tag-a",
                    "title": "Returned Tag A",
                    "content": "Returned A body.",
                },
                {
                    "doc_id": "tag-b",
                    "title": "Returned Tag B",
                    "content": "Returned B body.",
                },
            ],
            (
                "ds_20260730T180005Z"
                if failure_mode == "source-write"
                else "ds_20260730T180006Z"
            ),
        )
        filename = f"sub-scope-{failure_mode}.jsonl"
        preview = sub_scope_preview(root, filename)

        payload = sub_scope_apply(root, filename, preview)
        restored = {
            doc_id: path.read_bytes()
            for doc_id, path in paths.items()
        }
        suppressions = docs_watch_suppression.load_active_watch_suppressions(
            root,
            docs_watch_suppression.watch_suppression_owner("library", "tags"),
        )

    assert restored == originals
    assert payload["outcome"] == "generation-failed"
    assert payload["source_mutation"] == {
        "status": "failed",
        "applied": 0,
        "failed": 2,
        "not_attempted": 0,
    }
    assert payload["rollback"]["status"] == "completed"
    assert payload["rollback"]["sources_restored"] is True
    assert rebuild_attempts == ["docs-import-sub-scope-collection-apply"]
    assert rebuild_count == (1 if failure_mode == "source-write" else 2)
    assert set(suppressions) == {"tag-a.md", "tag-b.md"}
    assert {
        record["status"]
        for record in suppressions.values()
    } == {docs_watch_suppression.SUPPRESSION_COMPLETE}
    assert {
        record["reason"]
        for record in suppressions.values()
    } == {"docs-import-sub-scope-collection-apply-rollback"}


def test_collection_apply_creates_and_overwrites_complete_records_once(monkeypatch) -> None:
    stub_markdown_validation(monkeypatch)
    rebuild_calls: list[dict[str, object]] = []
    logs: list[tuple[str, dict[str, object]]] = []
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(
            root,
            "alpha.md",
            {
                "doc_id": "alpha",
                "title": "Old Alpha",
                "parent_id": "",
                "summary": "Old summary",
                "added_date": "2020-01-01",
            },
            body="# Old Alpha\n\nOld body.\n",
        )
        write_library_doc(root, "new-parent.md", {"doc_id": "new-parent", "title": "Parent", "parent_id": ""})
        write_collection(
            root,
            "apply.jsonl",
            [
                {
                    "doc_id": "alpha",
                    "title": "Alpha",
                    "summary": "Returned summary",
                    "parent_id": "new-parent",
                    "content": "# Alpha\n\nNew body.",
                },
                {"doc_id": "new-doc", "title": "New Doc", "content": "# New Doc\n\nBody."},
            ],
            "ds_20260712T160000Z",
        )

        payload = apply_package(
            root,
            "apply.jsonl",
            rebuild=fake_rebuild(rebuild_calls),
            logs=logs,
        )
        alpha_front_matter, alpha_body = docs_source_model.parse_source(root / "docs-viewer/scopes/library/source/documents/alpha.md")
        new_doc_id = payload["records"][1]["doc_id"]
        new_front_matter, new_body = docs_source_model.parse_source(
                root / "docs-viewer/scopes/library/source/documents" / f"{new_doc_id}.md"
        )
    assert payload["outcome"] == "completed"
    assert payload["counts"] == {
        "created": 1,
        "overwritten": 1,
        "failed": 0,
        "not_attempted": 0,
    }
    assert [record["status"] for record in payload["records"]] == ["overwritten", "created"]
    assert alpha_front_matter["added_date"] == "2020-01-01"
    assert alpha_front_matter["summary"] == "Returned summary"
    assert alpha_front_matter["parent_id"] == "new-parent"
    assert "New body." in alpha_body
    assert new_front_matter["doc_id"] == new_doc_id
    assert payload["records"][1]["source_doc_id"] == "new-doc"
    assert "Body." in new_body
    assert rebuild_calls == [
        {
            "scope": "library",
            "changed_paths": ["alpha.md", f"{new_doc_id}.md"],
            "docs_doc_ids": ["alpha", new_doc_id],
            "search_doc_ids": ["alpha", new_doc_id],
        }
    ]
    assert "report_path" not in payload
    assert not any(event == "docs-import-collection-record-skipped" for event, _details in logs)


def test_collection_confirmed_apply_dispatches_through_existing_import_post(monkeypatch) -> None:
    stub_markdown_validation(monkeypatch)
    rebuild_calls: list[dict[str, object]] = []
    monkeypatch.setattr(
        docs_write_rebuild,
        "perform_source_write_and_rebuild",
        fake_rebuild(rebuild_calls),
    )
    with make_repo() as temp:
        root = Path(temp)
        write_collection(
            root,
            "post-apply.jsonl",
            [{"doc_id": "post-applied", "title": "POST Applied", "content": "Body."}],
            "ds_20260712T160008Z",
        )
        preview = handle_import_source(
            root,
            {"scope": "library", "staged_filename": "post-apply.jsonl", "preview_only": True},
            False,
        )

        payload = handle_import_source(
            root,
            {
                "scope": "library",
                "staged_filename": "post-apply.jsonl",
                "preview_only": False,
                "confirm": True,
                "export_id": preview["package"]["export_id"],
                "source_sha256": preview["package"]["source_sha256"],
                "planned_identities": preview["planned_identities"],
                "planned_actions": preview["planned_actions"],
            },
            False,
        )

    assert payload["preview_only"] is False
    assert payload["records"][0]["status"] == "created"
    assert rebuild_calls[0]["docs_doc_ids"] == [payload["records"][0]["doc_id"]]


def test_collection_apply_returns_refreshed_plan_for_changed_action_or_package_identity(monkeypatch) -> None:
    stub_markdown_validation(monkeypatch)
    rebuild_calls: list[dict[str, object]] = []
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "alpha.md", {"doc_id": "alpha", "title": "Alpha", "parent_id": ""})
        write_collection(
            root,
            "drift.jsonl",
            [{"doc_id": "alpha", "title": "Returned Alpha", "content": "Body."}],
            "ds_20260712T160001Z",
        )

        missing = apply_package(
            root,
            "drift.jsonl",
            planned_actions=[],
            rebuild=fake_rebuild(rebuild_calls),
        )
        changed = apply_package(
            root,
            "drift.jsonl",
            planned_actions=[
                {
                    "record_index": 0,
                    "action": "overwrite",
                    "doc_id": "alpha",
                    "target_doc_id": "different",
                }
            ],
            rebuild=fake_rebuild(rebuild_calls),
        )
        package_changed = apply_package(
            root,
            "drift.jsonl",
            rebuild=fake_rebuild(rebuild_calls),
            source_sha256="different",
        )

    assert missing["preview_only"] is True
    assert missing["reconfirmation_required"] is True
    assert missing["revalidation_issues"][0]["code"] == "target_state_changed"
    assert changed["revalidation_issues"][0]["code"] == "target_state_changed"
    assert package_changed["revalidation_issues"][0]["code"] == "package_identity_changed"
    assert rebuild_calls == []


def test_preserve_existing_apply_uses_current_body_without_revision_reconfirmation(monkeypatch) -> None:
    stub_markdown_validation(monkeypatch)
    rebuild_calls: list[dict[str, object]] = []
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(
            root,
            "preserved.md",
            {
                "doc_id": "preserved",
                "title": "Old title",
                "parent_id": "library",
                "summary": "Current summary",
                "viewable": False,
                "custom_field": "before",
            },
            body="# Current\n\nInitial canonical body.\n",
        )
        write_collection(
            root,
            "preserve.jsonl",
            [{"doc_id": "preserved", "title": "Returned title"}],
            "ds_20260712T160009Z",
        )
        paths = configured_workspace_paths(root)
        preview = plan_document_package_collection(
            root,
            scope="library",
            staged_filename="preserve.jsonl",
            staging_root=paths.import_staging,
            workspace_root=paths.root,
            metadata_root=paths.meta,
        ).as_dict()
        write_library_doc(
            root,
            "preserved.md",
            {
                "doc_id": "preserved",
                "title": "Changed after preview",
                "parent_id": "library",
                "summary": "Newest summary",
                "viewable": False,
                "custom_field": "changed after preview",
            },
            body="# Current\n\nNewest canonical body.\n",
        )

        payload = apply_document_package_collection(
            root,
            scope="library",
            staged_filename="preserve.jsonl",
            body={
                "scope": "library",
                "staged_filename": "preserve.jsonl",
                "preview_only": False,
                "confirm": True,
                "export_id": preview["package"]["export_id"],
                "source_sha256": preview["package"]["source_sha256"],
                "planned_identities": preview.get("planned_identities", []),
                "planned_actions": preview["planned_actions"],
            },
            staging_root=paths.import_staging,
            workspace_root=paths.root,
            metadata_root=paths.meta,
            log_event=lambda *_args: None,
            perform_source_write_and_rebuild=fake_rebuild(rebuild_calls),
        )
        front_matter, body = docs_source_model.parse_source(root / "docs-viewer/scopes/library/source/documents/preserved.md")

    assert payload["preview_only"] is False
    assert payload["records"][0]["status"] == "overwritten"
    assert front_matter["title"] == "Returned title"
    assert front_matter["parent_id"] == "library"
    assert front_matter["summary"] == "Newest summary"
    assert front_matter["viewable"] is False
    assert front_matter["custom_field"] == "changed after preview"
    assert "Newest canonical body." in body


def test_collection_apply_stops_after_source_failure_and_rebuilds_completed_writes(monkeypatch) -> None:
    stub_markdown_validation(monkeypatch)
    rebuild_calls: list[dict[str, object]] = []
    original_write = collection_apply.apply_import_document_source

    def fail_epsilon(plan) -> None:
        if plan.record.provenance.get("source_doc_id") == "epsilon":
            raise OSError("simulated epsilon write failure")
        original_write(plan)

    monkeypatch.setattr(collection_apply, "apply_import_document_source", fail_epsilon)
    with make_repo() as temp:
        root = Path(temp)
        write_collection(
            root,
            "partial.jsonl",
            [
                {"doc_id": "delta", "title": "Delta", "content": "Delta."},
                {"doc_id": "epsilon", "title": "Epsilon", "content": "Epsilon."},
                {"doc_id": "zeta", "title": "Zeta", "content": "Zeta."},
            ],
            "ds_20260712T160002Z",
        )

        payload = apply_package(root, "partial.jsonl", rebuild=fake_rebuild(rebuild_calls))
        result_ids = [record["doc_id"] for record in payload["records"]]
        delta_exists, epsilon_exists, zeta_exists = [
                (root / "docs-viewer/scopes/library/source/documents" / f"{doc_id}.md").exists()
            for doc_id in result_ids
        ]

    assert payload["outcome"] == "partial"
    assert [record["status"] for record in payload["records"]] == ["created", "failed", "not-attempted"]
    assert delta_exists is True
    assert epsilon_exists is False
    assert zeta_exists is False
    assert rebuild_calls[0]["docs_doc_ids"] == [result_ids[0]]
    assert "report_path" not in payload


def test_collection_apply_keeps_source_success_when_generation_fails(monkeypatch) -> None:
    stub_markdown_validation(monkeypatch)
    rebuild_calls: list[dict[str, object]] = []
    with make_repo() as temp:
        root = Path(temp)
        write_collection(
            root,
            "generation.jsonl",
            [{"doc_id": "delta", "title": "Delta", "content": "Delta."}],
            "ds_20260712T160003Z",
        )

        payload = apply_package(
            root,
            "generation.jsonl",
            rebuild=fake_rebuild(rebuild_calls, fail_generation=True),
        )
        source_exists = (
            root / "docs-viewer/scopes/library/source/documents" / f"{payload['records'][0]['doc_id']}.md"
        ).exists()

    assert source_exists is True
    assert payload["records"][0]["status"] == "created"
    assert payload["outcome"] == "generation-failed"
    assert payload["generation"]["status"] == "failed"
    assert "report_path" not in payload


def test_collection_apply_materializes_inline_media_and_blocks_source_when_publication_fails(monkeypatch) -> None:
    stub_markdown_validation(monkeypatch)
    with make_repo() as temp:
        root = Path(temp)
        write_collection(
            root,
            "media.jsonl",
            [
                {
                    "doc_id": "media-doc",
                    "title": "Media Doc",
                    "content": "# Media Doc\n\n![Diagram](data:image/png;base64,aGVsbG8=)",
                }
            ],
            "ds_20260712T160006Z",
        )

        payload = apply_package(root, "media.jsonl", rebuild=fake_rebuild([]))
        local_doc_id = payload["records"][0]["doc_id"]
        media_path = root / "site/assets/data/docs/scopes/library/media/img" / f"{local_doc_id}-image-01.png"
        _front_matter, body = docs_source_model.parse_source(
                root / "docs-viewer/scopes/library/source/documents" / f"{payload['records'][0]['doc_id']}.md"
        )
        media_bytes = media_path.read_bytes()

    assert media_bytes == b"hello"
    assert f"[[media:docs/library/img/{local_doc_id}-image-01.png]]" in body
    assert payload["records"][0]["inline_media_written"][0]["source_path"] == media_path.name
    assert payload["records"][0]["inline_media_written"][0]["location_provider"] == "repository"
    assert payload["records"][0]["inline_media_written"][0]["publish_status"] == "uploaded"
    assert payload["manual_copy_instructions"] == []

    monkeypatch.setattr(
        collection_apply,
        "materialize_import_document_media",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("asset store unavailable")),
    )
    with make_repo() as temp:
        root = Path(temp)
        write_collection(
            root,
            "asset-failure.jsonl",
            [
                {
                    "doc_id": "asset-doc",
                    "title": "Asset Doc",
                    "content": "![Asset](data:image/png;base64,aGVsbG8=)",
                }
            ],
            "ds_20260712T160007Z",
        )
        asset_failure = apply_package(root, "asset-failure.jsonl", rebuild=fake_rebuild([]))
        asset_doc_id = asset_failure["records"][0]["doc_id"]
        source_path = root / "docs-viewer/scopes/library/source/documents" / f"{asset_doc_id}.md"
        source_exists = source_path.exists()

    assert source_exists is False
    assert asset_failure["outcome"] == "failed"
    assert asset_failure["records"][0]["status"] == "failed"
    assert asset_failure["records"][0]["error"] == "asset store unavailable"


def test_collection_apply_rejects_browser_plan_fields_and_blocks_invalid_package(monkeypatch) -> None:
    stub_markdown_validation(monkeypatch)
    with pytest.raises(ValueError, match="does not accept fields"):
        collection_apply._validated_confirmed_actions(
            {
                "scope": "library",
                "staged_filename": "unsafe.jsonl",
                "preview_only": False,
                "confirm": True,
                "planned_actions": [],
                "export_id": "ds_unsafe",
                "source_sha256": "unsafe",
                "target_path": "/tmp/unsafe.md",
            }
        )

    with make_repo() as temp:
        root = Path(temp)
        write_collection(
            root,
            "parent-skip.jsonl",
            [
                {"doc_id": "parent", "title": "Parent", "content": "", "viewable": "false"},
                {"doc_id": "child", "title": "Child", "parent_id": "parent", "content": "Child."},
            ],
            "ds_20260712T160005Z",
        )
        payload = apply_package(
            root,
            "parent-skip.jsonl",
            rebuild=fake_rebuild([]),
        )

    assert payload["preview_only"] is True
    assert payload["revalidation_issues"][-1]["code"] == "plan_blocked"


def test_collection_generation_projection_omits_commands_output_and_diagnostics() -> None:
    projected = safe_generation_result(
        {
            "status": "completed",
            "error": "",
            "rebuild": {
                "ok": True,
                "steps": [{"command": "/Users/example/python build.py", "stdout": "private"}],
                "docs": {"mode": "targeted", "doc_ids": ["alpha"], "reason": "/Users/example/output"},
                "search": {"mode": "targeted", "doc_ids": ["alpha"]},
                "diagnostics": {"path": "/Users/example/output"},
            },
        }
    )

    assert projected == {
        "status": "completed",
        "error": "",
        "rebuild": {
            "ok": True,
            "docs": {"mode": "targeted", "doc_ids": ["alpha"]},
            "search": {"mode": "targeted", "doc_ids": ["alpha"]},
        },
    }
