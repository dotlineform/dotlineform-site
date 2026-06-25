#!/usr/bin/env python3
"""Docs returned summary apply tests."""

from __future__ import annotations

from pathlib import Path

import docs_write_rebuild as write_rebuild

from docs_import_test_support import (
    handle_documents_import_apply,
    make_repo,
    stub_rebuild,
    write_library_doc,
    write_staged,
)

def test_library_import_summary_apply_preflight_reports_missing_target_doc() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "alpha.md", {"doc_id": "alpha", "title": "Alpha", "summary": "Old summary."})
        write_staged(
            root,
            "summaries.jsonl",
            [
                {"doc_id": "alpha", "title": "Alpha", "summary": "New summary."},
                {"doc_id": "missing", "title": "Missing", "summary": "Missing summary."},
            ],
        )
        payload = handle_documents_import_apply(
            root,
            {"data_domain": "library", "operation": "apply", "apply_action": "summary_apply", "staged_filename": "summaries.jsonl", "record_indices": [0, 1]},
            dry_run=True,
        )

    assert payload["ok"] is False
    assert payload["counts"]["updates"] == 1
    assert payload["counts"]["errors"] == 1
    assert payload["errors"][0]["reason"] == "missing_target_doc"
    assert payload["summary_apply_written"] is False

def test_library_import_summary_apply_writes_source() -> None:
    original_rebuild = stub_rebuild()
    try:
        with make_repo() as temp:
            root = Path(temp)
            write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library"})
            write_library_doc(
                root,
                "alpha.md",
                {
                    "doc_id": "alpha",
                    "title": "Alpha",
                    "added_date": "2026-05-01",
                    "last_updated": "2026-05-01",
                    "summary": "Old summary.",
                    "parent_id": "library",
                },
            )
            write_staged(root, "summaries.jsonl", [{"doc_id": "alpha", "title": "Alpha", "summary": "New summary."}])
            payload = handle_documents_import_apply(
                root,
                {"data_domain": "library", "operation": "apply", "apply_action": "summary_apply", "staged_filename": "summaries.jsonl", "record_indices": [0], "confirm": True},
                dry_run=False,
            )
            source_text = (root / "docs-viewer/source/library/alpha.md").read_text(encoding="utf-8")
    finally:
        write_rebuild.perform_source_write_and_rebuild = original_rebuild

    assert payload["ok"] is True
    assert payload["summary_apply_written"] is True
    assert payload["counts"]["updates"] == 1
    assert "backup_dir" not in payload
    assert payload["rebuild"]["docs"]["mode"] == "targeted"
    assert payload["rebuild"]["docs"]["doc_ids"] == ["alpha"]
    assert payload["rebuild"]["search"]["doc_ids"] == ["alpha"]
    assert payload["rebuild"]["diagnostics"]["docs"]["build_mode"] == "targeted"
    assert "last_updated: 2026-05-01" in source_text
    assert "summary: New summary." in source_text

def test_documents_data_sharing_apply_uses_python_docs_rebuild_commands() -> None:
    original_run_rebuild_command = write_rebuild.run_rebuild_command
    commands: list[list[str]] = []

    def fake_run_rebuild_command(command: list[str], repo_root: Path) -> dict[str, object]:
        del repo_root
        commands.append(command)
        stdout = ""
        if command[1] == write_rebuild.DOCS_BUILDER_SCRIPT:
            stdout = 'Docs builder diagnostics: {"scope": "library", "build_mode": "targeted"}'
        elif command[1] == write_rebuild.SEARCH_BUILDER_SCRIPT:
            stdout = "Changed: 1. Removed: 0. Unchanged: 0. Full fallback: 0\nwith 1 docs search entries"
        return {
            "command": " ".join(command),
            "returncode": 0,
            "stdout": stdout,
            "stderr": "",
            "elapsed_seconds": 0.001,
        }

    write_rebuild.run_rebuild_command = fake_run_rebuild_command
    try:
        with make_repo() as temp:
            root = Path(temp)
            references_index = root / "site/assets/data/docs/scopes/library/references/index.json"
            references_index.parent.mkdir(parents=True, exist_ok=True)
            references_index.write_text('{"references": []}\n', encoding="utf-8")
            write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library"})
            write_library_doc(
                root,
                "alpha.md",
                {
                    "doc_id": "alpha",
                    "title": "Alpha",
                    "added_date": "2026-05-01",
                    "last_updated": "2026-05-01",
                    "summary": "Old summary.",
                    "parent_id": "library",
                },
            )
            write_staged(root, "summaries.jsonl", [{"doc_id": "alpha", "title": "Alpha", "summary": "New summary."}])
            payload = handle_documents_import_apply(
                root,
                {"data_domain": "library", "operation": "apply", "apply_action": "summary_apply", "staged_filename": "summaries.jsonl", "record_indices": [0], "confirm": True},
                dry_run=False,
            )
    finally:
        write_rebuild.run_rebuild_command = original_run_rebuild_command

    command_texts = [" ".join(command) for command in commands]
    assert payload["ok"] is True
    assert payload["summary_apply_written"] is True
    assert any(command[1] == write_rebuild.DOCS_BUILDER_SCRIPT for command in commands)
    assert any(command[1] == write_rebuild.SEARCH_BUILDER_SCRIPT for command in commands)
    assert any("--only-doc-ids alpha" in text for text in command_texts)
    assert not any("bundle" in text or "ruby" in text or ".rb" in text for text in command_texts)

def test_library_import_summary_apply_skips_unchanged_and_missing_summary_rows() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "alpha.md", {"doc_id": "alpha", "title": "Alpha", "summary": "Same summary."})
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library"})
        write_staged(
            root,
            "summaries.jsonl",
            [
                {"doc_id": "alpha", "title": "Alpha", "summary": "Same summary."},
                {"doc_id": "library", "title": "Library"},
            ],
        )
        payload = handle_documents_import_apply(
            root,
            {"data_domain": "library", "operation": "apply", "apply_action": "summary_apply", "staged_filename": "summaries.jsonl", "record_indices": [0, 1]},
            dry_run=True,
        )

    assert payload["ok"] is True
    assert payload["counts"]["updates"] == 0
    assert payload["counts"]["skipped"] == 2
    assert {item["reason"] for item in payload["skipped"]} == {"unchanged", "missing_summary"}
