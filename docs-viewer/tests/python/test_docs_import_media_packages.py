#!/usr/bin/env python3
"""Docs import media and markdown package tests."""

from __future__ import annotations

from pathlib import Path

import docs_import_media
import docs_import_preview
import docs_import_source_service as import_source_service
import docs_write_rebuild as write_rebuild

from docs_import_test_support import (
    handle_import_source,
    make_repo,
    stub_rebuild,
    write_library_doc,
    write_staged_bytes,
    write_staged_html,
    write_staged_markdown,
    write_staged_package_file,
    write_test_image,
)

def test_html_import_extracts_inline_png_to_staged_media_plan() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
        write_staged_html(
            root,
            "inline-diagram.html",
            """
            <html>
              <head><title>Inline Diagram</title></head>
              <body>
                <h1>Inline Diagram</h1>
                <p><img alt="Layered diagram" src="data:image/png;base64,aW5saW5lLXBuZw=="></p>
              </body>
            </html>
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
                {"scope": "library", "staged_filename": "inline-diagram.html"},
                dry_run=False,
            )
        finally:
            write_rebuild.perform_source_write_and_rebuild = original_rebuild
            docs_import_preview.validate_markdown_preview = original_validation

        source_text = (root / payload["path"]).read_text(encoding="utf-8")
        media_path = root / "site/assets/data/docs/scopes/library/media/img/inline-diagram-image-01.png"
        media_bytes = media_path.read_bytes()

    assert payload["ok"] is True
    assert payload["import_preview"]["media_plans"][0]["source_path"] == "inline-diagram-image-01.png"
    assert payload["import_preview"]["media_plans"][0]["media_path"] == "docs/library/img/inline-diagram-image-01.png"
    assert payload["inline_media_written"][0]["location_provider"] == "repository"
    assert payload["inline_media_written"][0]["artifact_identity"] == "inline-diagram-image-01.png"
    assert payload["inline_media_written"][0]["publish_status"] == "uploaded"
    assert media_bytes == b"inline-png"
    assert "data:image/png;base64" not in source_text
    assert "![Layered diagram]([[media:docs/library/img/inline-diagram-image-01.png]])" in source_text

def test_markdown_import_extracts_inline_png_with_incremented_filename() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
        write_staged_bytes(root, "inline-note-image-01.png", b"existing")
        write_staged_markdown(
            root,
            "inline-note.md",
            "# Inline Note\n\n![Inline](data:image/png;base64,bWFya2Rvd24tcG5n)\n",
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
                {"scope": "library", "staged_filename": "inline-note.md"},
                dry_run=False,
            )
        finally:
            write_rebuild.perform_source_write_and_rebuild = original_rebuild
            docs_import_preview.validate_markdown_preview = original_validation

        source_text = (root / payload["path"]).read_text(encoding="utf-8")
        media_path = root / "site/assets/data/docs/scopes/library/media/img/inline-note-image-02.png"
        media_bytes = media_path.read_bytes()

    assert payload["ok"] is True
    assert payload["import_preview"]["source_format"] == "markdown"
    assert payload["import_preview"]["media_plans"][0]["source_path"] == "inline-note-image-02.png"
    assert media_bytes == b"markdown-png"
    assert "data:image/png;base64" not in source_text
    assert "[[media:docs/library/img/inline-note-image-02.png]]" in source_text

def test_inline_media_write_skips_invalid_data_urls_before_valid_images() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
        write_staged_markdown(
            root,
            "mixed-inline.md",
            "# Mixed Inline\n\n![Broken](data:image/png;base64,abc)\n\n![Valid](data:image/png;base64,dmFsaWQtcG5n)\n",
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
                {"scope": "library", "staged_filename": "mixed-inline.md"},
                dry_run=False,
            )
        finally:
            write_rebuild.perform_source_write_and_rebuild = original_rebuild
            docs_import_preview.validate_markdown_preview = original_validation

        source_text = (root / payload["path"]).read_text(encoding="utf-8")
        media_path = root / "site/assets/data/docs/scopes/library/media/img/mixed-inline-image-01.png"
        media_bytes = media_path.read_bytes()

    assert payload["ok"] is True
    assert len(payload["import_preview"]["media_plans"]) == 1
    assert media_bytes == b"valid-png"
    assert "![Broken](data:image/png;base64,abc)" in source_text
    assert "[[media:docs/library/img/mixed-inline-image-01.png]]" in source_text

def test_markdown_package_import_rewrites_media_and_materializes_outputs() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
        image_path = write_staged_package_file(root, "my-note", "images/opaque-name.png", b"")
        write_test_image(image_path, (1000, 500))
        write_staged_package_file(root, "my-note", "attachments/report.pdf", b"%PDF-1.4 fake\n")
        write_staged_package_file(
            root,
            "my-note",
            "My Note.md",
            """# My Note

Some text.

![Opaque](images/opaque-name.png)
<span style="font-size: 11.285714;">
    3 symbols
</span>

[Research PDF](attachments/report.pdf)
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
                {"scope": "library", "staged_filename": "my-note"},
                dry_run=False,
            )
        finally:
            write_rebuild.perform_source_write_and_rebuild = original_rebuild
            docs_import_preview.validate_markdown_preview = original_validation

        source_text = (root / payload["path"]).read_text(encoding="utf-8")
        webp_path = root / "site/assets/data/docs/scopes/library/media/img/my-note-image-01.webp"
        attachment_path = root / "site/assets/data/docs/scopes/library/media/files/my-note-attachment-01.pdf"
        from PIL import Image

        with Image.open(webp_path) as converted:
            output_size = converted.size
        attachment_bytes = attachment_path.read_bytes()

    assert payload["ok"] is True
    assert payload["import_preview"]["source_format"] == "markdown_package"
    assert payload["import_preview"]["media_plans"][0]["source_path"] == "my-note-image-01.webp"
    assert payload["import_preview"]["media_plans"][0]["kind"] == "image"
    assert payload["import_preview"]["media_plans"][0]["title"] == "my note image 01"
    assert payload["import_preview"]["media_plans"][1]["source_path"] == "my-note-attachment-01.pdf"
    assert payload["import_preview"]["media_plans"][1]["kind"] == "attachment"
    assert payload["inline_media_written"][0]["kind"] == "image"
    assert payload["inline_media_written"][0]["conversion"]["output_width"] == 800
    assert output_size == (800, 400)
    assert attachment_bytes == b"%PDF-1.4 fake\n"
    assert '![my note image 01]([[media:docs/library/img/my-note-image-01.webp]] "my note image 01")' in source_text
    assert "[Research PDF]([[media:docs/library/files/my-note-attachment-01.pdf]])" in source_text
    assert "font-size: var(--font-caption)" in source_text

def test_markdown_package_image_conversion_does_not_upscale() -> None:
    with make_repo() as temp:
        root = Path(temp)
        source = root / "small.png"
        target = root / "small.webp"
        write_test_image(source, (320, 160))
        result = docs_import_media.convert_package_image_to_webp(source, target, max_width=800)
        from PIL import Image

        with Image.open(target) as converted:
            output_size = converted.size

    assert result["resized"] is False
    assert output_size == (320, 160)

def test_markdown_package_import_reports_unresolved_and_unsupported_links() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
        write_staged_package_file(root, "broken-note", "attachments/sample-binary.exe", b"fake exe")
        write_staged_package_file(
            root,
            "broken-note",
            "Broken Note.md",
            "# Broken Note\n\n![Missing](images/missing.png)\n\n[Unsupported](attachments/sample-binary.exe)\n",
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
                {"scope": "library", "staged_filename": "broken-note", "preview_only": True},
                dry_run=False,
            )
        finally:
            write_rebuild.perform_source_write_and_rebuild = original_rebuild
            docs_import_preview.validate_markdown_preview = original_validation

    warnings = payload["import_preview"]["warnings"]
    assert payload["ok"] is True
    assert payload["preview_only"] is True
    assert any("Package image target was not found" in warning for warning in warnings)
    assert any("Unsupported package attachment type .exe" in warning for warning in warnings)
