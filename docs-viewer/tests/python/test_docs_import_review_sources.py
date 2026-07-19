#!/usr/bin/env python3
"""Returned document-content review source folder tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from docs_import_test_support import handle_documents_import_preview, make_repo, write_staged
import docs_data_sharing.review_sources as review_sources
import docs_review_packages
import docs_source_model as source_model
from repo_factory import data_sharing_workspace_root, resolve_data_sharing_marker


def write_content_meta(
    root: Path,
    export_id: str,
    *,
    generated_at: str = "2026-06-27T20:50:10Z",
    metadata_export_id: str | None = None,
    data_domain: str = "documents",
    profile_id: str = "document-content",
    content_format: str = "markdown",
) -> None:
    del root
    path = data_sharing_workspace_root() / f"meta/{export_id}.meta.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "data_sharing_export_meta_v1",
                "export_id": metadata_export_id or export_id,
                "app": "docs-viewer",
                "adapter_id": "documents",
                "data_domain": data_domain,
                "config_id": profile_id,
                "profile_id": profile_id,
                "scope": "library",
                "target_format": "jsonl",
                "record_shape": "document_rows",
                "generated_at": generated_at,
                "supports_return_import": True,
                "content_format": content_format,
            }
        )
        + "\n",
        encoding="utf-8",
    )


def source_folder_body(root: Path, payload: dict[str, object], filename: str) -> str:
    del root
    source_path = resolve_data_sharing_marker(str(payload["source_path"])) / filename
    _, body = source_model.parse_source(source_path)
    return body


def raw_source_body(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    delimiter_count = 0
    for index, line in enumerate(lines):
        if line.strip() == "---":
            delimiter_count += 1
            if delimiter_count == 2:
                return "".join(lines[index + 1 :])
    raise AssertionError("source file is missing front matter delimiter")


def test_review_source_folder_rejects_missing_export_id() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged(root, "content.json", {"records": [{"doc_id": "alpha", "title": "Alpha", "content": "Body."}]})

        payload = handle_documents_import_preview(
            root,
            {"data_domain": "library", "operation": "review", "review_action": "source_folder", "staged_filename": "content.json"},
            dry_run=False,
        )

    assert payload["ok"] is False
    assert payload["review_source_folder_written"] is False
    assert payload["counts"]["errors"] == 1
    assert payload["issues"][0]["code"] == "missing_export_id"


def test_review_source_folder_rejects_missing_and_mismatched_metadata() -> None:
    with make_repo() as temp:
        root = Path(temp)
        missing_export_id = "ds_20260627T205010Z"
        write_staged(
            root,
            "missing-meta.jsonl",
            [
                {"record_type": "data_sharing_header", "export_id": missing_export_id},
                {"doc_id": "alpha", "title": "Alpha", "content": "Body."},
            ],
        )
        missing_payload = handle_documents_import_preview(
            root,
            {"data_domain": "library", "operation": "review", "review_action": "source_folder", "staged_filename": "missing-meta.jsonl"},
            dry_run=False,
        )

        mismatched_export_id = "ds_20260627T205011Z"
        write_staged(
            root,
            "mismatch.jsonl",
            [
                {"record_type": "data_sharing_header", "export_id": mismatched_export_id},
                {"doc_id": "alpha", "title": "Alpha", "content": "Body."},
            ],
        )
        write_content_meta(root, mismatched_export_id, metadata_export_id="ds_20260627T205012Z")
        mismatch_payload = handle_documents_import_preview(
            root,
            {"data_domain": "library", "operation": "review", "review_action": "source_folder", "staged_filename": "mismatch.jsonl"},
            dry_run=False,
        )

    assert missing_payload["ok"] is False
    assert missing_payload["issues"][0]["code"] == "missing_export_metadata"
    assert mismatch_payload["ok"] is False
    assert mismatch_payload["issues"][0]["code"] == "metadata_export_id_mismatch"


def test_review_source_folder_rejects_unsafe_metadata_derived_folder_id() -> None:
    with make_repo() as temp:
        root = Path(temp)
        export_id = "ds_20260627T205010Z"
        write_staged(
            root,
            "content.jsonl",
            [
                {"record_type": "data_sharing_header", "export_id": export_id},
                {"doc_id": "alpha", "title": "Alpha", "content": "Body."},
            ],
        )
        write_content_meta(root, export_id, profile_id="../document-content")

        payload = handle_documents_import_preview(
            root,
            {"data_domain": "library", "operation": "review", "review_action": "source_folder", "staged_filename": "content.jsonl"},
            dry_run=False,
        )

    assert payload["ok"] is False
    assert payload["review_source_folder_written"] is False
    assert [item["code"] for item in payload["issues"]] == ["invalid_folder_id"]


def test_review_source_folder_uses_shared_markdown_content_normalization() -> None:
    with make_repo() as temp:
        root = Path(temp)
        export_id = "ds_20260627T205010Z"
        returned_content = "\n# Returned Title\n\nKeep  two spaces.\n\n- item\n"
        write_staged(
            root,
            "renamed-return.jsonl",
            [
                {"record_type": "data_sharing_header", "export_id": export_id, "content_format": "plain_text"},
                {
                    "doc_id": "alpha",
                    "title": "Alpha",
                    "summary": "Returned summary.",
                    "viewable": False,
                    "content": returned_content,
                },
            ],
        )
        write_content_meta(root, export_id, content_format="markdown")

        payload = handle_documents_import_preview(
            root,
            {"data_domain": "library", "operation": "review", "review_action": "source_folder", "staged_filename": "renamed-return.jsonl"},
            dry_run=False,
        )
        manifest = json.loads(resolve_data_sharing_marker(str(payload["manifest_path"])).read_text(encoding="utf-8"))
        source_path = resolve_data_sharing_marker(str(payload["source_files"][0]["path"]))
        front_matter, _ = source_model.parse_source(source_path)
        raw_body = raw_source_body(source_path)
        listed = docs_review_packages.list_packages(root)
        generated = docs_review_packages.read_payload(root, payload["folder_id"], "alpha")

    assert payload["ok"] is True
    assert payload["folder_id"] == "20260627-215010-documents-document-content"
    assert payload["content_format"] == "markdown"
    assert payload["counts"] == {"records": 1, "valid_records": 1, "skipped_records": 0, "errors": 0, "warnings": 0}
    assert payload["review_source_folder_written"] is True
    assert payload["review_generated_written"] is True
    assert payload["generated"]["document_count"] == 1
    assert manifest["schema_version"] == "docs_review_validated_package_v1"
    assert manifest["package_id"] == payload["folder_id"]
    assert manifest["package_id_source"] == "export_metadata"
    assert manifest["status"] == "validated"
    assert manifest["source_scope"] == "library"
    assert manifest["default_doc_id"] == "alpha"
    assert manifest["source_projection"] == "rendered_derived_text_only"
    assert manifest["source_export_id"] == export_id
    assert manifest["staged_filename"] == "renamed-return.jsonl"
    assert manifest["delete_safe"] is True
    assert manifest["content_mapping"] == {
        "content_field": "content",
        "content_format_field": "content_format",
        "front_matter_fields": ["title", "parent_id", "summary", "viewable"],
    }
    assert front_matter["doc_id"] == "alpha"
    assert front_matter["title"] == "Alpha"
    assert "parent_id" not in front_matter
    assert front_matter["summary"] == "Returned summary."
    assert front_matter["viewable"] is False
    assert "children" not in front_matter
    assert raw_body == returned_content.strip()
    assert listed["packages"][0]["package_id"] == payload["folder_id"]
    assert listed["packages"][0]["built"] is True
    assert listed["rejected"] == []
    assert generated["payload"]["doc_id"] == "alpha"
    assert generated["generated_repaired"] is False


def test_review_source_folder_uses_full_source_adapter_mapping() -> None:
    with make_repo() as temp:
        root = Path(temp)
        export_id = "ds_20260627T205010Z"
        canonical = """---
doc_id: alpha
title: Canonical Alpha
parent_id: ""
summary: Returned full source.
---
# Canonical Alpha

Full-source body.
"""
        write_staged(
            root,
            "full-source.jsonl",
            [
                {
                    "record_type": "data_sharing_header",
                    "schema_version": "documents_full_package_v1",
                    "export_id": export_id,
                    "profile_id": "document-full-source",
                },
                {
                    "record_type": "document",
                    "doc_id": "alpha",
                    "document": {"title": "Duplicated title", "parent_id": ""},
                    "canonical_markdown": canonical,
                },
            ],
        )
        write_content_meta(root, export_id, profile_id="document-full-source")

        payload = handle_documents_import_preview(
            root,
            {
                "data_domain": "library",
                "operation": "review",
                "review_action": "source_folder",
                "staged_filename": "full-source.jsonl",
            },
            dry_run=False,
        )
        manifest = json.loads(resolve_data_sharing_marker(str(payload["manifest_path"])).read_text(encoding="utf-8"))
        source_path = resolve_data_sharing_marker(str(payload["source_files"][0]["path"]))
        front_matter, body = source_model.parse_source(source_path)

    assert payload["ok"] is True
    assert front_matter["title"] == "Canonical Alpha"
    assert front_matter["summary"] == "Returned full source."
    assert body == "# Canonical Alpha\n\nFull-source body."
    assert manifest["source_projection"] == "canonical_full_source"
    assert manifest["content_mapping"]["content_field"] == "canonical_markdown"
    assert manifest["source_files"][0]["content_intent"] == "replace"


def test_review_source_folder_roots_parent_outside_compact_package_and_warns() -> None:
    with make_repo() as temp:
        root = Path(temp)
        export_id = "ds_20260627T205010Z"
        write_staged(
            root,
            "content.jsonl",
            [
                {"record_type": "data_sharing_header", "export_id": export_id},
                {"doc_id": "alpha", "title": "Alpha", "parent_id": "missing", "content": "Body."},
            ],
        )
        write_content_meta(root, export_id)
        payload = handle_documents_import_preview(
            root,
            {"data_domain": "library", "operation": "review", "review_action": "source_folder", "staged_filename": "content.jsonl"},
            dry_run=False,
        )
        source_path = resolve_data_sharing_marker(str(payload["source_files"][0]["path"]))
        front_matter, _ = source_model.parse_source(source_path)
        generated = docs_review_packages.read_index_tree(root, payload["folder_id"])

    assert payload["ok"] is True
    assert payload["review_source_folder_written"] is True
    assert payload["counts"]["warnings"] == 1
    assert payload["issues"] == [
        {
            "level": "warning",
            "code": "parent_outside_materialized_package",
            "message": "materialized review document was rooted because parent_id is outside the package: missing",
            "record_index": 0,
            "doc_id": "alpha",
            "parent_id": "missing",
        }
    ]
    assert "parent_id" not in front_matter
    assert generated["generated_repaired"] is False


def test_persistent_review_reads_survive_staged_package_deletion_without_reconversion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_repo() as temp:
        root = Path(temp)
        export_id = "ds_20260627T205010Z"
        write_staged(
            root,
            "content.jsonl",
            [
                {"record_type": "data_sharing_header", "export_id": export_id},
                {"doc_id": "alpha", "title": "Alpha", "content": "Persistent body."},
            ],
        )
        write_content_meta(root, export_id)
        payload = handle_documents_import_preview(
            root,
            {"data_domain": "library", "operation": "review", "review_action": "source_folder", "staged_filename": "content.jsonl"},
            dry_run=False,
        )
        staged_path = data_sharing_workspace_root() / "import-staging/content.jsonl"
        staged_path.unlink()
        (data_sharing_workspace_root() / f"meta/{export_id}.meta.json").unlink()

        def reject_unnecessary_rebuild(*_args, **_kwargs):
            raise AssertionError("persistent generated output should not rebuild during ordinary reads")

        monkeypatch.setattr(docs_review_packages, "_rebuild_generated_package", reject_unnecessary_rebuild)

        first_tree = docs_review_packages.read_index_tree(root, payload["folder_id"])
        first_document = docs_review_packages.read_payload(root, payload["folder_id"], "alpha")
        second_tree = docs_review_packages.read_index_tree(root, payload["folder_id"])
        second_document = docs_review_packages.read_payload(root, payload["folder_id"], "alpha")

    assert first_tree["generated_repaired"] is False
    assert first_document["generated_repaired"] is False
    assert second_tree["index_tree"] == first_tree["index_tree"]
    assert second_document["payload"] == first_document["payload"]
    assert second_tree["generated_repaired"] is False
    assert second_document["generated_repaired"] is False


def test_persistent_review_build_failure_publishes_no_partial_package(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_repo() as temp:
        root = Path(temp)
        export_id = "ds_20260627T205010Z"
        write_staged(
            root,
            "content.jsonl",
            [
                {"record_type": "data_sharing_header", "export_id": export_id},
                {"doc_id": "alpha", "title": "Alpha", "content": "Body."},
            ],
        )
        write_content_meta(root, export_id)

        def fail_publication(*_args, **_kwargs):
            raise RuntimeError("simulated generated build failure")

        monkeypatch.setattr(review_sources, "publish_review_package", fail_publication)
        payload = handle_documents_import_preview(
            root,
            {"data_domain": "library", "operation": "review", "review_action": "source_folder", "staged_filename": "content.jsonl"},
            dry_run=False,
        )
        package_path = resolve_data_sharing_marker(str(payload["folder_path"]))
        preview_root = data_sharing_workspace_root() / "import-preview"

    assert payload["ok"] is False
    assert payload["review_source_folder_written"] is False
    assert payload["review_generated_written"] is False
    assert payload["generated"] == {}
    assert [item["code"] for item in payload["issues"]] == ["review_package_build_failed"]
    assert package_path.exists() is False
    assert list(preview_root.glob(".*.publishing-*")) == []


def test_review_source_folder_preserves_existing_body_and_materializes_empty_new_record() -> None:
    with make_repo() as temp:
        root = Path(temp)
        export_id = "ds_20260627T205010Z"
        write_staged(
            root,
            "hierarchy-only.jsonl",
            [
                {"record_type": "data_sharing_header", "export_id": export_id},
                {"doc_id": "new-parent", "title": "New Parent", "parent_id": ""},
                {"doc_id": "alpha", "title": "Alpha", "parent_id": "new-parent"},
            ],
        )
        write_content_meta(root, export_id)
        _current_front_matter, current_alpha_body = source_model.parse_source(
            root / "docs-viewer/scopes/library/source/documents/alpha.md"
        )

        payload = handle_documents_import_preview(
            root,
            {
                "data_domain": "library",
                "operation": "review",
                "review_action": "source_folder",
                "staged_filename": "hierarchy-only.jsonl",
            },
            dry_run=False,
        )
        manifest = json.loads(resolve_data_sharing_marker(str(payload["manifest_path"])).read_text(encoding="utf-8"))
        alpha_path = resolve_data_sharing_marker(str(payload["source_path"])) / "alpha.md"
        alpha_front_matter, alpha_body = source_model.parse_source(alpha_path)
        new_body = source_folder_body(root, payload, "new-parent.md")

    assert payload["ok"] is True
    assert payload["counts"] == {"records": 2, "valid_records": 2, "skipped_records": 0, "errors": 0, "warnings": 0}
    assert alpha_front_matter["parent_id"] == "new-parent"
    assert alpha_body == current_alpha_body
    assert new_body == ""
    assert [record["content_intent"] for record in manifest["source_files"]] == [
        "empty-new",
        "preserve-existing",
    ]


def test_review_source_folder_rejects_package_local_hierarchy_cycle() -> None:
    with make_repo() as temp:
        root = Path(temp)
        export_id = "ds_20260627T205010Z"
        write_staged(
            root,
            "content.jsonl",
            [
                {"record_type": "data_sharing_header", "export_id": export_id},
                {"doc_id": "alpha", "title": "Alpha", "parent_id": "beta", "content": "Alpha body."},
                {"doc_id": "beta", "title": "Beta", "parent_id": "alpha", "content": "Beta body."},
            ],
        )
        write_content_meta(root, export_id)

        payload = handle_documents_import_preview(
            root,
            {"data_domain": "library", "operation": "review", "review_action": "source_folder", "staged_filename": "content.jsonl"},
            dry_run=False,
        )

    assert payload["ok"] is False
    assert payload["review_source_folder_written"] is False
    assert {item["code"] for item in payload["issues"]} == {"materialized_hierarchy_cycle"}


def test_review_source_folder_skips_invalid_rows_and_does_not_write() -> None:
    with make_repo() as temp:
        root = Path(temp)
        export_id = "ds_20260627T205010Z"
        write_staged(
            root,
            "content.jsonl",
            [
                {"record_type": "data_sharing_header", "export_id": export_id},
                {"doc_id": "alpha", "title": "Alpha", "content": "Body."},
                {"title": "Missing id", "content": "Body."},
                {"doc_id": "missing-title", "content": "Body."},
                {"doc_id": "missing-content", "title": "Missing content"},
            ],
        )
        write_content_meta(root, export_id)

        payload = handle_documents_import_preview(
            root,
            {"data_domain": "library", "operation": "review", "review_action": "source_folder", "staged_filename": "content.jsonl"},
            dry_run=False,
        )

    assert payload["ok"] is False
    assert payload["review_source_folder_written"] is False
    assert payload["counts"] == {"records": 4, "valid_records": 2, "skipped_records": 2, "errors": 2, "warnings": 0}
    assert [item["code"] for item in payload["skipped_records"]] == ["missing_doc_id", "missing_title"]


def test_review_source_folder_rejects_existing_timestamped_package() -> None:
    with make_repo() as temp:
        root = Path(temp)
        export_id = "ds_20260627T205010Z"
        write_content_meta(root, export_id)
        write_staged(
            root,
            "content.jsonl",
            [
                {"record_type": "data_sharing_header", "export_id": export_id},
                {"doc_id": "alpha", "title": "Alpha", "content": "First body."},
            ],
        )
        first = handle_documents_import_preview(
            root,
            {"data_domain": "library", "operation": "review", "review_action": "source_folder", "staged_filename": "content.jsonl"},
            dry_run=False,
        )
        stale_path = resolve_data_sharing_marker(str(first["folder_path"])) / "source" / "stale.md"
        stale_path.write_text("stale\n", encoding="utf-8")
        write_staged(
            root,
            "content.jsonl",
            [
                {"record_type": "data_sharing_header", "export_id": export_id},
                {"doc_id": "beta", "title": "Beta", "content": "Second body."},
            ],
        )

        second = handle_documents_import_preview(
            root,
            {"data_domain": "library", "operation": "review", "review_action": "source_folder", "staged_filename": "content.jsonl"},
            dry_run=False,
        )
        first_body = source_folder_body(root, first, "alpha.md")
        beta_path = resolve_data_sharing_marker(str(second["source_path"])) / "beta.md"

    assert first["folder_id"] == second["folder_id"]
    assert second["ok"] is False
    assert second["review_source_folder_written"] is False
    assert second["counts"]["errors"] == 1
    assert [item["code"] for item in second["issues"]] == ["review_package_exists"]
    assert stale_path.exists() is True
    assert first_body == "First body."
    assert beta_path.exists() is False
