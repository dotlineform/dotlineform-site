#!/usr/bin/env python3
"""Docs source import format tests."""

from __future__ import annotations

from pathlib import Path

import docs_import_preview
import docs_import_source_service as import_source_service
import docs_write_rebuild as write_rebuild

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

def test_svg_import_strips_unsafe_content() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
        write_staged_text(
            root,
            "diagram.svg",
            """
            <svg viewBox="0 0 10 10" onclick="alert(1)">
              <title>Unsafe Diagram</title>
              <script>alert(1)</script>
              <rect width="10" height="10" />
            </svg>
            """,
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
                {"scope": "library", "staged_filename": "diagram.svg"},
                dry_run=False,
            )
        finally:
            write_rebuild.perform_source_write_and_rebuild = original_rebuild
            docs_import_preview.validate_markdown_preview = original_validation

        source_text = (root / payload["path"]).read_text(encoding="utf-8")

    assert payload["ok"] is True
    assert payload["title"] == "Unsafe Diagram"
    assert payload["import_preview"]["source_format"] == "svg"
    assert "<script" not in source_text
    assert "onclick" not in source_text
    assert "<title>Unsafe Diagram</title>" in source_text
    assert any("script" in warning for warning in payload["import_preview"]["warnings"])

def test_image_import_creates_media_path_plan_wrapper() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
        write_staged_bytes(root, "reference-image.png", b"fake image")
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
                {"scope": "library", "staged_filename": "reference-image.png"},
                dry_run=False,
            )
        finally:
            write_rebuild.perform_source_write_and_rebuild = original_rebuild
            docs_import_preview.validate_markdown_preview = original_validation

        source_text = (root / payload["path"]).read_text(encoding="utf-8")

    assert payload["ok"] is True
    assert payload["import_preview"]["source_format"] == "image"
    assert payload["import_preview"]["media_plan"]["media_path"] == "docs/library/img/reference-image.png"
    assert "[[media:docs/library/img/reference-image.png]]" in source_text

def test_file_media_import_creates_file_media_path_plan_wrapper() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
        write_staged_bytes(root, "reference-file.pdf", b"fake pdf")
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
                {"scope": "library", "staged_filename": "reference-file.pdf"},
                dry_run=False,
            )
        finally:
            write_rebuild.perform_source_write_and_rebuild = original_rebuild
            docs_import_preview.validate_markdown_preview = original_validation

        source_text = (root / payload["path"]).read_text(encoding="utf-8")

    assert payload["ok"] is True
    assert payload["import_preview"]["source_format"] == "file"
    assert payload["import_preview"]["media_plan"]["media_path"] == "docs/library/files/reference-file.pdf"
    assert "[[media:docs/library/files/reference-file.pdf]]" in source_text

def test_import_collision_prompts_for_replacement_doc_id() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
        write_library_doc(root, "reference-file.md", {"doc_id": "reference-file", "title": "Reference File", "parent_id": ""})
        write_staged_bytes(root, "reference-file.pdf", b"fake pdf")
        original_rebuild = stub_rebuild()
        original_validation = docs_import_preview.validate_markdown_preview
        docs_import_preview.validate_markdown_preview = lambda markdown, *, title="": {
            "ok": True,
            "html_chars": len(markdown),
            "renderer": "stub",
        }
        try:
            preview_payload = handle_import_source(
                root,
                {"scope": "library", "staged_filename": "reference-file.pdf"},
                dry_run=False,
            )
            apply_payload = handle_import_source(
                root,
                {
                    "scope": "library",
                    "staged_filename": "reference-file.pdf",
                    "replacement_doc_id": "reference-file-2",
                },
                dry_run=False,
            )
        finally:
            write_rebuild.perform_source_write_and_rebuild = original_rebuild
            docs_import_preview.validate_markdown_preview = original_validation

        source_path = root / apply_payload["path"]
        source_exists = source_path.exists()
        source_text = source_path.read_text(encoding="utf-8")

    assert preview_payload["preview_only"] is True
    assert preview_payload["replacement_doc_id_required"] is True
    assert "replacement_title_required" not in preview_payload
    assert preview_payload["collision"]["doc_id"] == "reference-file"
    assert apply_payload["ok"] is True
    assert apply_payload["operation"] == "create"
    assert apply_payload["doc_id"].startswith("d-")
    assert apply_payload["import_preview"]["source_doc_id"] == "reference-file-2"
    assert source_exists
    assert "title: Reference File" in source_text
