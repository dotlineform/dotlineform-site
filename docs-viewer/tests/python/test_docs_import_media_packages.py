#!/usr/bin/env python3
"""Docs import media and markdown package tests."""

from __future__ import annotations

from pathlib import Path

import pytest

import docs_import_media
import docs_import_preview
import docs_import_source_service as import_source_service
import docs_write_rebuild as write_rebuild
from docs_media_storage import DocsMediaPublishResult

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
        media_filename = f"{payload['doc_id']}-image-01.png"
        media_path = root / "site/assets/data/docs/scopes/library/media/img" / media_filename
        media_bytes = media_path.read_bytes()

    assert payload["ok"] is True
    assert payload["import_preview"]["media_plans"][0]["source_path"] == media_filename
    assert payload["import_preview"]["media_plans"][0]["media_path"] == f"docs/library/img/{media_filename}"
    assert payload["inline_media_written"][0]["location_provider"] == "repository"
    assert payload["inline_media_written"][0]["artifact_identity"] == media_filename
    assert payload["inline_media_written"][0]["publish_status"] == "uploaded"
    assert media_bytes == b"inline-png"
    assert "data:image/png;base64" not in source_text
    assert f"![Layered diagram]([[media:docs/library/img/{media_filename}]])" in source_text


def test_html_import_extracts_sanitized_inline_svg_before_source_write() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
        write_staged_html(
            root,
            "energy-wells.html",
            """<html><head><title>Energy Wells</title></head><body>
            <h1>Energy Wells</h1>
            <svg viewBox="0 0 20 10" onclick="alert(1)">
              <title>Potential field</title>
              <defs>
                <linearGradient id="gradient"><stop offset="100%" stop-color="#000"/></linearGradient>
                <path id="curve" d="M0 5 L20 5"/>
              </defs>
              <style><![CDATA[.curve { stroke: url(#gradient); }]]></style>
              <use href="#curve"/>
              <image href="https://example.com/tracker.png"/>
            </svg>
            </body></html>""",
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
                {"scope": "library", "staged_filename": "energy-wells.html"},
                dry_run=False,
            )
        finally:
            write_rebuild.perform_source_write_and_rebuild = original_rebuild
            docs_import_preview.validate_markdown_preview = original_validation

        source_text = (root / payload["path"]).read_text(encoding="utf-8")
        media_filename = f"{payload['doc_id']}-image-01.svg"
        media_path = root / "site/assets/data/docs/scopes/library/media/img" / media_filename
        svg_text = media_path.read_text(encoding="utf-8")

    assert payload["import_preview"]["media_plans"][0]["source"] == "inline_svg"
    assert payload["inline_media_written"][0]["artifact_identity"] == media_filename
    assert f"![Potential field]([[media:docs/library/img/{media_filename}]])" in source_text
    assert "<svg" not in source_text
    assert "onclick" not in svg_text
    assert "https://example.com" not in svg_text
    assert 'href="#curve"' in svg_text
    assert 'xmlns="http://www.w3.org/2000/svg"' in svg_text
    assert "linearGradient" in svg_text
    assert "lineargradient" not in svg_text
    assert ".curve { stroke: url(#gradient); }" in svg_text
    assert "&lt;![CDATA[" not in svg_text


def test_html_inline_svg_publication_failure_does_not_write_document_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
        write_staged_html(
            root,
            "energy-wells.html",
            "<html><body><h1>Energy Wells</h1><svg><title>Potential field</title></svg></body></html>",
        )
        documents_root = root / "docs-viewer/source/library/documents"
        before = sorted(documents_root.glob("*.md"))
        original_rebuild = stub_rebuild()
        original_validation = docs_import_preview.validate_markdown_preview
        docs_import_preview.validate_markdown_preview = lambda markdown, *, title="": {
            "ok": True,
            "html_chars": len(markdown),
            "renderer": "stub",
        }
        monkeypatch.setattr(
            docs_import_media,
            "publish_docs_media_files",
            lambda *_args, **_kwargs: [
                DocsMediaPublishResult(
                    scope="library",
                    media_class="img",
                    filename="blocked.svg",
                    size=0,
                    status="blocked_changed",
                    reason="remote object differs",
                )
            ],
        )
        try:
            with pytest.raises(RuntimeError, match="publication did not complete"):
                handle_import_source(
                    root,
                    {"scope": "library", "staged_filename": "energy-wells.html"},
                    dry_run=False,
                )
        finally:
            write_rebuild.perform_source_write_and_rebuild = original_rebuild
            docs_import_preview.validate_markdown_preview = original_validation

        after = sorted(documents_root.glob("*.md"))

    assert after == before

def test_markdown_import_extracts_inline_png_with_canonical_doc_identity() -> None:
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
        media_filename = f"{payload['doc_id']}-image-01.png"
        media_path = root / "site/assets/data/docs/scopes/library/media/img" / media_filename
        media_bytes = media_path.read_bytes()

    assert payload["ok"] is True
    assert payload["import_preview"]["source_format"] == "markdown"
    assert payload["import_preview"]["media_plans"][0]["source_path"] == media_filename
    assert media_bytes == b"markdown-png"
    assert "data:image/png;base64" not in source_text
    assert f"[[media:docs/library/img/{media_filename}]]" in source_text

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
        media_filename = f"{payload['doc_id']}-image-01.png"
        media_path = root / "site/assets/data/docs/scopes/library/media/img" / media_filename
        media_bytes = media_path.read_bytes()

    assert payload["ok"] is True
    assert len(payload["import_preview"]["media_plans"]) == 1
    assert media_bytes == b"valid-png"
    assert "![Broken](data:image/png;base64,abc)" in source_text
    assert f"[[media:docs/library/img/{media_filename}]]" in source_text

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
        image_filename = f"{payload['doc_id']}-image-01.webp"
        attachment_filename = f"{payload['doc_id']}-attachment-01.pdf"
        webp_path = root / "site/assets/data/docs/scopes/library/media/img" / image_filename
        attachment_path = root / "site/assets/data/docs/scopes/library/media/files" / attachment_filename
        from PIL import Image

        with Image.open(webp_path) as converted:
            output_size = converted.size
        attachment_bytes = attachment_path.read_bytes()

    assert payload["ok"] is True
    assert payload["import_preview"]["source_format"] == "markdown_package"
    assert payload["import_preview"]["media_plans"][0]["source_path"] == image_filename
    assert payload["import_preview"]["media_plans"][0]["kind"] == "image"
    assert payload["import_preview"]["media_plans"][0]["title"] == "my note image 01"
    assert payload["import_preview"]["media_plans"][1]["source_path"] == attachment_filename
    assert payload["import_preview"]["media_plans"][1]["kind"] == "attachment"
    assert payload["inline_media_written"][0]["kind"] == "image"
    assert payload["inline_media_written"][0]["conversion"]["output_width"] == 800
    assert output_size == (800, 400)
    assert attachment_bytes == b"%PDF-1.4 fake\n"
    assert f'![my note image 01]([[media:docs/library/img/{image_filename}]] "my note image 01")' in source_text
    assert f"[Research PDF]([[media:docs/library/files/{attachment_filename}]])" in source_text
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
