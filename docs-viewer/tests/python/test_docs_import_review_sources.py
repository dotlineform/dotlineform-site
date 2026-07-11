#!/usr/bin/env python3
"""Returned document-content review source folder tests."""

from __future__ import annotations

import json
from pathlib import Path

from docs_import_test_support import handle_documents_import_preview, make_repo, write_staged
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


def test_review_source_folder_writes_manifest_and_verbatim_markdown_body() -> None:
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
                    "parent_id": "library",
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

    assert payload["ok"] is True
    assert payload["folder_id"] == "20260627-215010-documents-document-content"
    assert payload["content_format"] == "markdown"
    assert payload["counts"] == {"records": 1, "valid_records": 1, "skipped_records": 0, "errors": 0, "warnings": 0}
    assert payload["review_source_folder_written"] is True
    assert manifest["folder_id_source"] == "export_metadata"
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
    assert front_matter["parent_id"] == "library"
    assert front_matter["summary"] == "Returned summary."
    assert front_matter["viewable"] is False
    assert "children" not in front_matter
    assert raw_body == returned_content


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
    assert payload["counts"] == {"records": 4, "valid_records": 1, "skipped_records": 3, "errors": 3, "warnings": 0}
    assert [item["code"] for item in payload["skipped_records"]] == ["missing_doc_id", "missing_title", "missing_content"]


def test_review_source_folder_replaces_existing_folder_explicitly() -> None:
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
        second_body = source_folder_body(root, second, "beta.md")

    assert first["folder_id"] == second["folder_id"]
    assert second["ok"] is True
    assert second["source_files"] == [
        {
            "record_index": 0,
            "doc_id": "beta",
            "path": "$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-preview/20260627-215010-documents-document-content/source/beta.md",
        }
    ]
    assert stale_path.exists() is False
    assert second_body == "Second body."
