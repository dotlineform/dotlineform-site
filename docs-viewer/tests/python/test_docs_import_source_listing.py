#!/usr/bin/env python3
"""Docs source import listing and preview tests."""

from __future__ import annotations

from pathlib import Path

import docs_import_media
import docs_import_preview
import docs_import_source_service as import_source_service

from docs_import_test_support import (
    make_repo,
    write_staged_bytes,
    write_staged_html,
    write_staged_markdown,
    write_staged_package_file,
    write_staged_text,
)

def test_source_import_files_list_html_and_markdown() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged_html(root, "source.html", "<html><body><h1>Source</h1></body></html>")
        write_staged_markdown(root, "source.md", "# Source\n")
        write_staged_text(root, "source.txt", "Source\n")
        write_staged_text(root, "source.svg", "<svg viewBox='0 0 10 10'></svg>\n")
        write_staged_bytes(root, "source.png", b"fake image")
        write_staged_bytes(root, "source.pdf", b"fake pdf")
        write_staged_package_file(root, "package-note", "Note.md", "# Package Note\n")

        files = import_source_service.list_staged_import_source_files(root)

    by_filename = {item["filename"]: item for item in files}
    assert by_filename["source.html"]["source_format"] == "html"
    assert by_filename["source.md"]["source_format"] == "markdown"
    assert by_filename["source.txt"]["source_format"] == "text"
    assert by_filename["source.svg"]["source_format"] == "svg"
    assert by_filename["source.png"]["source_format"] == "image"
    assert by_filename["source.pdf"]["source_format"] == "file"
    assert by_filename["package-note"]["source_format"] == "markdown_package"
    assert by_filename["package-note"]["package_markdown_count"] == 1

def test_source_import_previews_validate_with_python_renderer() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged_html(root, "source.html", "<html><body><h1>Source</h1><p>Body.</p></body></html>")
        write_staged_markdown(root, "source.md", "# Source\n\n| A | B |\n| - | - |\n| 1 | 2 |\n")
        write_staged_text(root, "source.txt", "Source\n\nSee https://example.com/path.\n")
        write_staged_text(root, "source.svg", "<svg viewBox='0 0 10 10'><title>Source</title><rect /></svg>\n")
        write_staged_bytes(root, "source.png", b"fake image")
        write_staged_bytes(root, "source.pdf", b"fake pdf")
        write_staged_package_file(root, "package-note", "Note.md", "# Package Note\n\nBody.\n")

        previews = [
            docs_import_preview.generate_import_preview(
                root,
                source_path=docs_import_preview.resolve_staged_import_source(root, staged_filename),
                scope="library",
                include_prompt_meta=False,
            )
            for staged_filename in [
                "source.html",
                "source.md",
                "source.txt",
                "source.svg",
                "source.png",
                "source.pdf",
                "package-note",
            ]
        ]

    source_formats = {preview["source_format"] for preview in previews}
    assert source_formats == {"html", "markdown", "text", "svg", "image", "file", "markdown_package"}
    for preview in previews:
        validation = preview["markdown_validation"]
        assert validation["ok"] is True
        assert validation["renderer"] == "studio/shared/python/markdown_renderer.py"
        assert validation["renderer_contract"]["library"] == "markdown-it-py"
        assert validation["sanitizer_boundary"]["import_html"] == "docs_import_html_parser structured conversion and SVG serialization"

def test_media_path_comes_from_scope_config() -> None:
    assert docs_import_media.media_path_for("analysis", "img", "diagram.png") == "docs/analysis/img/diagram.png"
    assert docs_import_media.media_token("analysis", "img", "diagram.png") == "[[media:docs/analysis/img/diagram.png]]"
