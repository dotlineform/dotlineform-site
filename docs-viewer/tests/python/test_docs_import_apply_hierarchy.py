#!/usr/bin/env python3
"""Docs returned hierarchy apply tests."""

from __future__ import annotations

from pathlib import Path

import docs_source_model as source_model
import docs_write_rebuild as write_rebuild

from docs_import_test_support import (
    handle_documents_import_apply,
    make_repo,
    stub_rebuild,
    write_library_doc,
    write_returned_jsonl,
)

def test_library_import_hierarchy_apply_preflight_reports_missing_target_doc() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
        write_library_doc(root, "alpha.md", {"doc_id": "alpha", "title": "Alpha", "parent_id": "library"})
        write_returned_jsonl(
            root,
            "hierarchy.jsonl",
            [
                {"doc_id": "alpha", "title": "Alpha", "parent_id": ""},
                {"doc_id": "missing", "title": "Missing", "parent_id": "library"},
            ],
        )
        payload = handle_documents_import_apply(
            root,
            {"data_domain": "library", "operation": "apply", "apply_action": "hierarchy_apply", "staged_filename": "hierarchy.jsonl", "record_indices": [0, 1]},
            dry_run=True,
        )

    assert payload["ok"] is False
    assert payload["counts"]["changed"] == 1
    assert payload["counts"]["errors"] == 1
    assert payload["errors"][0]["reason"] == "missing_target_doc"
    assert payload["hierarchy_apply_written"] is False

def test_library_import_hierarchy_apply_writes_source_placement() -> None:
    original_rebuild = stub_rebuild()
    try:
        with make_repo() as temp:
            root = Path(temp)
            write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
            write_library_doc(
                root,
                "alpha.md",
                {
                    "doc_id": "alpha",
                    "title": "Alpha",
                    "added_date": "2026-05-01",
                    "last_updated": "2026-05-01",
                    "parent_id": "library",
                    "sort_order": 30,
                },
            )
            write_returned_jsonl(
                root,
                "hierarchy.jsonl",
                [
                    {"doc_id": "library", "title": "Library", "parent_id": "external-root"},
                    {"doc_id": "alpha", "title": "Alpha", "parent_id": ""},
                ],
            )
            payload = handle_documents_import_apply(
                root,
                {"data_domain": "library", "operation": "apply", "apply_action": "hierarchy_apply", "staged_filename": "hierarchy.jsonl", "record_indices": [1], "confirm": True},
                dry_run=False,
            )
            alpha_front_matter, _ = source_model.parse_source(root / "docs-viewer/source/library/documents/alpha.md")
            library_front_matter, _ = source_model.parse_source(root / "docs-viewer/source/library/documents/library.md")
    finally:
        write_rebuild.perform_source_write_and_rebuild = original_rebuild

    assert payload["ok"] is True
    assert payload["hierarchy_apply_written"] is True
    assert payload["counts"]["changed"] == 1
    assert "backup_dir" not in payload
    assert payload["rebuild"]["docs"]["mode"] == "targeted"
    assert payload["rebuild"]["docs"]["doc_ids"] == ["alpha"]
    assert payload["rebuild"]["search"]["doc_ids"] == ["alpha"]
    assert payload["rebuild"]["diagnostics"]["search"]["mode"] == "targeted"
    assert alpha_front_matter["doc_id"] == "alpha"
    assert alpha_front_matter["title"] == "Alpha"
    assert alpha_front_matter["added_date"] == "2026-05-01"
    assert alpha_front_matter["last_updated"] == "2026-05-01"
    assert alpha_front_matter["parent_id"] == ""
    assert library_front_matter["parent_id"] == ""

def test_library_import_hierarchy_apply_allows_unknown_parent_and_dry_run_no_write() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "alpha.md", {"doc_id": "alpha", "title": "Alpha", "parent_id": "library"})
        write_returned_jsonl(root, "hierarchy.jsonl", [{"doc_id": "alpha", "title": "Alpha", "parent_id": "external-root"}])
        payload = handle_documents_import_apply(
            root,
            {"data_domain": "library", "operation": "apply", "apply_action": "hierarchy_apply", "staged_filename": "hierarchy.jsonl", "record_indices": [0], "confirm": True},
            dry_run=True,
        )
        source_text = (root / "docs-viewer/source/library/documents/alpha.md").read_text(encoding="utf-8")

    assert payload["ok"] is True
    assert payload["hierarchy_apply_written"] is False
    assert payload["counts"]["changed"] == 1
    assert payload["counts"]["warnings"] == 1
    assert payload["warnings"][0]["reason"] == "unknown_parent_id"
    assert "parent_id: library" in source_text

def test_library_import_hierarchy_apply_reports_unchanged_and_skipped_rows() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
        write_library_doc(root, "alpha.md", {"doc_id": "alpha", "title": "Alpha", "parent_id": "library"})
        write_returned_jsonl(
            root,
            "hierarchy.jsonl",
            [
                {"doc_id": "alpha", "title": "Alpha", "parent_id": "library"},
                {"doc_id": "library", "title": "Library", "parent_id": "library"},
            ],
        )
        payload = handle_documents_import_apply(
            root,
            {"data_domain": "library", "operation": "apply", "apply_action": "hierarchy_apply", "staged_filename": "hierarchy.jsonl", "record_indices": [0, 1]},
            dry_run=True,
        )

    assert payload["ok"] is True
    assert payload["counts"]["changed"] == 0
    assert payload["counts"]["unchanged"] == 1
    assert payload["counts"]["skipped"] == 1
    assert payload["skipped"][0]["reason"] == "self_parent_id"
