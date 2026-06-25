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

def test_library_import_files_lists_json_and_jsonl_only() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged(root, "summaries.jsonl", [{"doc_id": "alpha", "title": "Alpha"}])
        write_staged(root, "relationships.json", {"documents": []})
        (root / "var/analytics/data-sharing/import-staging/notes.txt").write_text("ignore\n", encoding="utf-8")
        payload = handle_documents_import_files(root, "library")

    assert payload["ok"] is True
    assert payload["scope"] == "library"
    assert payload["staging_root"] == "var/analytics/data-sharing/import-staging"
    assert [item["filename"] for item in payload["files"]] == ["relationships.json", "summaries.jsonl"]
    assert [item["format"] for item in payload["files"]] == ["json", "jsonl"]

def test_library_import_preview_writes_when_not_dry_run() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged(
            root,
            "summaries.jsonl",
            [{"doc_id": "alpha", "title": "Alpha", "parent_id": "library", "summary": "Preview summary."}],
        )
        payload = handle_documents_import_preview(
            root,
            {"data_domain": "library", "operation": "review", "staged_filename": "summaries.jsonl"},
            dry_run=False,
        )
        preview_paths = sorted((root / "var/analytics/data-sharing/import-preview").glob("alpha-*.md"))
        tree_paths = sorted((root / "var/analytics/data-sharing/import-preview").glob("summaries-tree-*.md"))
        preview_text = preview_paths[0].read_text(encoding="utf-8")

    assert payload["ok"] is True
    assert payload["preview_written"] is True
    assert len(preview_paths) == 1
    assert len(tree_paths) == 1
    assert f"var/analytics/data-sharing/import-preview/{preview_paths[0].name}" in [
        item["path"] for item in payload["preview_files"]
    ]
    assert payload["summary_text"] == "Generated 2 Library import preview files."
    assert "Preview summary." in preview_text

def test_library_import_preview_dry_run_reports_without_writing() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged(root, "summaries.jsonl", [{"doc_id": "alpha", "title": "Alpha"}])
        payload = handle_documents_import_preview(
            root,
            {"data_domain": "library", "operation": "review", "staged_filename": "summaries.jsonl"},
            dry_run=True,
        )
        preview_exists = list((root / "var/analytics/data-sharing/import-preview").glob("alpha-*.md"))

    assert payload["ok"] is True
    assert payload["preview_written"] is False
    assert payload["preview_files"][0]["path"].startswith("var/analytics/data-sharing/import-preview/alpha-")
    assert payload["preview_files"][0]["path"].endswith(".md")
    assert payload["summary_text"] == "Validated 1 Library import preview file without writing."
    assert preview_exists == []

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
                "config_id": "library-document-summaries",
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
                "config_id": "library-document-summaries",
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
