#!/usr/bin/env python3
"""Docs source import format tests."""

from __future__ import annotations

from pathlib import Path

import pytest

import docs_import_preview
import docs_import_source_service as import_source_service
import docs_management_service
import docs_write_rebuild as write_rebuild
from repo_factory import docs_scope_record, write_docs_scope_config

from docs_import_test_support import (
    handle_import_source,
    make_repo,
    stub_rebuild,
    write_library_doc,
    write_staged_bytes,
    write_staged_markdown,
    write_staged_text,
)

def test_markdown_import_create_wraps_body_with_generated_front_matter() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
        write_staged_markdown(
            root,
            "markdown-note.md",
            "# Imported Markdown\n\nBody from staged Markdown with [a link](https://example.com).\n",
        )
        original_rebuild = stub_rebuild()
        original_validation = docs_import_preview.validate_markdown_preview
        docs_import_preview.validate_markdown_preview = lambda markdown, *, title="": {
            "ok": True,
            "html_chars": len(markdown),
            "renderer": "stub",
        }
        try:
            payload = handle_import_source(
                root,
                {"scope": "library", "staged_filename": "markdown-note.md"},
                dry_run=False,
            )
        finally:
            write_rebuild.perform_source_write_and_rebuild = original_rebuild
            docs_import_preview.validate_markdown_preview = original_validation

        source_path = root / payload["path"]
        source_text = source_path.read_text(encoding="utf-8")

    assert payload["ok"] is True
    assert payload["operation"] == "create"
    assert payload["doc_id"].startswith("d-")
    assert payload["title"] == "Imported Markdown"
    assert payload["import_preview"]["source_format"] == "markdown"
    assert payload["import_preview"]["proposed_doc_id_source"] == "allocated-local-identity"
    assert payload["import_preview"]["source_doc_id"] == "markdown-note"
    assert f"doc_id: {payload['doc_id']}" in source_text
    assert "title: Imported Markdown" in source_text
    assert "# Imported Markdown" in source_text
    assert "Body from staged Markdown" in source_text


def test_markdown_import_create_returns_external_workspace_relative_path(tmp_path: Path) -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_docs_scope_config(
            root,
            [docs_scope_record("notes", scope_type="local_external")],
        )
        external_documents = tmp_path / "projects-base/docs-viewer/scopes/notes/source/documents"
        external_documents.mkdir(parents=True)
        write_staged_markdown(
            root,
            "external-note.md",
            "# External Note\n\nBody stored outside the repository.\n",
        )
        docs_management_service.refresh_source_model_scope_configs(root)
        original_rebuild = stub_rebuild()
        original_validation = docs_import_preview.validate_markdown_preview
        docs_import_preview.validate_markdown_preview = lambda markdown, *, title="": {
            "ok": True,
            "html_chars": len(markdown),
            "renderer": "stub",
        }
        try:
            payload = handle_import_source(
                root,
                {"scope": "notes", "staged_filename": "external-note.md"},
                dry_run=False,
            )
        finally:
            write_rebuild.perform_source_write_and_rebuild = original_rebuild
            docs_import_preview.validate_markdown_preview = original_validation

        target = external_documents / f"{payload['doc_id']}.md"

    assert payload["ok"] is True
    assert payload["path"] == f"scopes/notes/source/documents/{payload['doc_id']}.md"
    assert target.is_file()

def test_text_import_autolinks_plain_urls() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
        write_staged_text(root, "plain-note.txt", "Plain Note\n\nSee https://example.com/path.\n")
        original_rebuild = stub_rebuild()
        original_validation = docs_import_preview.validate_markdown_preview
        docs_import_preview.validate_markdown_preview = lambda markdown, *, title="": {
            "ok": True,
            "html_chars": len(markdown),
            "renderer": "stub",
        }
        try:
            payload = handle_import_source(
                root,
                {"scope": "library", "staged_filename": "plain-note.txt"},
                dry_run=False,
            )
        finally:
            write_rebuild.perform_source_write_and_rebuild = original_rebuild
            docs_import_preview.validate_markdown_preview = original_validation

        source_text = (root / payload["path"]).read_text(encoding="utf-8")

    assert payload["ok"] is True
    assert payload["import_preview"]["source_format"] == "text"
    assert "<https://example.com/path>" in source_text

@pytest.mark.parametrize(
    ("filename", "content"),
    [
        ("diagram.svg", b"<svg viewBox='0 0 10 10'></svg>"),
        ("reference-image.png", b"fake image"),
        ("reference-file.pdf", b"fake pdf"),
    ],
)
def test_docs_import_rejects_standalone_media(filename: str, content: bytes) -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged_bytes(root, filename, content)

        with pytest.raises(ValueError, match="staged file must use one of these extensions"):
            handle_import_source(
                root,
                {"scope": "library", "staged_filename": filename},
                dry_run=False,
            )
