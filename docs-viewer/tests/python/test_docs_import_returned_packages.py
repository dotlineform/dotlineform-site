#!/usr/bin/env python3
"""Docs returned-package import tests."""

from __future__ import annotations

from pathlib import Path

from docs_import_test_support import (
    handle_docs_export,
    handle_documents_import_files,
    handle_documents_import_preview,
    make_repo,
    write_staged,
)


def write_content_meta(root: Path, export_id: str, generated_at: str = "2026-06-27T20:50:10Z") -> None:
    path = root / f"var/analytics/data-sharing/meta/{export_id}.meta.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        (
            '{"export_id": "'
            + export_id
            + '", "app": "docs-viewer", "adapter_id": "documents", "data_domain": "documents", '
            + '"config_id": "document-content", "profile_id": "document-content", "scope": "library", '
            + '"generated_at": "'
            + generated_at
            + '"}\n'
        ),
        encoding="utf-8",
    )


def test_library_import_files_lists_json_and_jsonl_only() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged(root, "content.jsonl", [{"doc_id": "alpha", "title": "Alpha", "content": "Body."}])
        write_staged(root, "relationships.json", {"records": []})
        (root / "var/analytics/data-sharing/import-staging/notes.txt").write_text("ignore\n", encoding="utf-8")
        payload = handle_documents_import_files(root, "library")

    assert payload["ok"] is True
    assert payload["scope"] == "library"
    assert payload["staging_root"] == "var/analytics/data-sharing/import-staging"
    assert [item["filename"] for item in payload["files"]] == ["content.jsonl", "relationships.json"]
    assert {item["filename"]: item["format"] for item in payload["files"]} == {
        "content.jsonl": "jsonl",
        "relationships.json": "json",
    }

def test_library_import_review_writes_selected_record_document() -> None:
    with make_repo() as temp:
        root = Path(temp)
        export_id = "ds_20260627T205010Z"
        write_staged(
            root,
            "content.jsonl",
            [
                {
                    "record_type": "data_sharing_header",
                    "schema_version": "data_sharing_returned_package_v1",
                    "export_id": export_id,
                },
                {"doc_id": "alpha", "title": "Alpha", "parent_id": "library", "summary": "Preview summary.", "content": "Preview body."},
            ],
        )
        write_content_meta(root, export_id)
        payload = handle_documents_import_preview(
            root,
            {"data_domain": "library", "operation": "review", "staged_filename": "content.jsonl", "record_indices": [0]},
            dry_run=False,
        )
        review_path = root / str(payload["review_file"])
        review_text = review_path.read_text(encoding="utf-8")

    assert payload["ok"] is True
    assert payload["summary_text"] == "Generated Library import review for 1 selected document."
    assert payload["review_rows"][0]["record_index"] == 0
    assert payload["selected_records"] == [{"record_index": 0, "doc_id": "alpha"}]
    assert payload["review_written"] is True
    assert "preview_files" not in payload
    assert "preview_written" not in payload
    assert review_path.name == "20260627-215010-library-document-content.md"
    assert "| alpha | Alpha | Preview summary. | library |" in review_text


def test_library_import_review_defaults_to_all_records_and_appends_issues() -> None:
    with make_repo() as temp:
        root = Path(temp)
        export_id = "ds_20260627T205010Z"
        write_staged(
            root,
            "content.jsonl",
            [
                {
                    "record_type": "data_sharing_header",
                    "schema_version": "data_sharing_returned_package_v1",
                    "export_id": export_id,
                },
                {"doc_id": "alpha", "title": "Alpha", "parent_id": "library", "summary": "Preview summary.", "content": "Preview body."},
                {"doc_id": "", "title": "Missing", "summary": "Missing id."},
            ],
        )
        write_content_meta(root, export_id)
        payload = handle_documents_import_preview(
            root,
            {"data_domain": "library", "operation": "review", "review_action": "summaries", "staged_filename": "content.jsonl"},
            dry_run=False,
        )
        review_text = (root / str(payload["review_file"])).read_text(encoding="utf-8")

    assert payload["ok"] is True
    assert payload["selected_records"] == [
        {"record_index": 0, "doc_id": "alpha"},
        {"record_index": 1, "doc_id": ""},
    ]
    assert "## Issues" in review_text
    assert "| warning | missing_doc_id | 2 |  | Missing | record is missing doc_id |" in review_text

def test_documents_import_rejects_unconfigured_data_domain() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged(root, "works.jsonl", [{"doc_id": "work-1", "title": "Work 1"}], scope="catalogue")
        try:
            handle_documents_import_preview(
                root,
                {"data_domain": "catalogue", "staged_filename": "works.jsonl"},
                dry_run=True,
            )
        except ValueError as error:
            message = str(error)
        else:
            raise AssertionError("unconfigured data domain should fail closed")

    assert "no Data Sharing adapter configured for catalogue/review" in message

def test_docs_export_summary_text_uses_context_aware_document_plural() -> None:
    with make_repo() as temp:
        root = Path(temp)
        singular = handle_docs_export(
            root,
            {
                "data_domain": "library",
                "config_id": "document-content",
                "selection": {
                    "docs_scope": "library",
                    "doc_ids": ["alpha"],
                    "select_all": False,
                    "missing_summary_only": None,
                },
            },
            dry_run=True,
        )
        plural = handle_docs_export(
            root,
            {
                "data_domain": "library",
                "config_id": "document-content",
                "selection": {
                    "docs_scope": "library",
                    "doc_ids": ["library", "alpha"],
                    "select_all": False,
                    "missing_summary_only": None,
                },
            },
            dry_run=True,
        )

    assert singular["summary_text"].startswith("Validated package 1 document to ")
    assert plural["summary_text"].startswith("Validated package 2 documents to ")
