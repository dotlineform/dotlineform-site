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


def write_content_meta(root: Path, export_id: str) -> None:
    path = root / f"var/analytics/data-sharing/meta/{export_id}.meta.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        (
            '{"export_id": "'
            + export_id
            + '", "app": "docs-viewer", "adapter_id": "documents", "data_domain": "documents", '
            + '"config_id": "document-content", "profile_id": "document-content", "scope": "library"}\n'
        ),
        encoding="utf-8",
    )


def test_library_import_files_lists_json_and_jsonl_only() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged(root, "content.jsonl", [{"doc_id": "alpha", "title": "Alpha", "source_text": "Body."}])
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

def test_library_import_review_returns_rows_without_preview_artifacts() -> None:
    with make_repo() as temp:
        root = Path(temp)
        export_id = "ds_20260627T120010Z"
        write_staged(
            root,
            "content.jsonl",
            [
                {
                    "record_type": "data_sharing_header",
                    "schema_version": "data_sharing_returned_package_v1",
                    "export_id": export_id,
                },
                {"doc_id": "alpha", "title": "Alpha", "parent_id": "library", "summary": "Preview summary.", "source_text": "Preview body."},
            ],
        )
        write_content_meta(root, export_id)
        payload = handle_documents_import_preview(
            root,
            {"data_domain": "library", "operation": "review", "staged_filename": "content.jsonl"},
            dry_run=False,
        )
        preview_paths = sorted((root / "var/analytics/data-sharing/import-preview").glob("*-alpha.md"))

    assert payload["ok"] is True
    assert payload["summary_text"] == "Validated 1 Library import review row."
    assert payload["review_rows"][0]["record_index"] == 0
    assert "preview_files" not in payload
    assert "preview_written" not in payload
    assert preview_paths == []

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
