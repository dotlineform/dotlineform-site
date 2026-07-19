#!/usr/bin/env python3
"""Focused DOCX source adapter tests."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import mammoth
import pytest

import docs_import_docx
import docs_import_media
import docs_import_preview
import docs_write_rebuild as write_rebuild
from docs_import_docx_test_support import embedded_image_docx_bytes, semantic_docx_bytes
from docs_import_test_support import (
    handle_import_source,
    make_repo,
    stub_rebuild,
    write_library_doc,
    write_staged_bytes,
)
from docs_media_storage import DocsMediaPublishResult
from services.paths import configured_workspace_paths


def _preview(root: Path, filename: str) -> dict[str, object]:
    paths = configured_workspace_paths(root)
    source_path = docs_import_preview.resolve_staged_import_source(paths.import_staging, filename)
    return docs_import_preview.generate_import_preview(
        root,
        staging_root=paths.import_staging,
        workspace_root=paths.root,
        source_path=source_path,
        scope="library",
        include_prompt_meta=False,
    )


def test_docx_preview_uses_one_semantic_style_map_and_existing_html_converter() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged_bytes(root, "semantic-word.docx", semantic_docx_bytes())
        preview = _preview(root, "semantic-word.docx")

    markdown = str(preview["markdown_preview"])
    warnings = list(preview["warnings"])
    assert preview["source_format"] == "docx"
    assert preview["title"] == "A Word Title"
    assert preview["title_source"] == "docx-title"
    assert preview["source_path"] == "$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-staging/semantic-word.docx"
    assert markdown.startswith("# A Word Title\n\nA useful subtitle\n\n## First Section")
    assert "Body with **bold** and *italic* plus [a link](https://example.com/path)." in markdown
    assert "- First item\n- Second item" in markdown
    assert "| Name | Value |\n| --- | --- |\n| Alpha | 1 |" in markdown
    assert "###### Deep Section" in markdown
    assert "###### Clamped Section" in markdown
    assert "Unknown style body." in markdown
    assert any("Unrecognised paragraph style: Mystery Style" in warning for warning in warnings)
    assert any("Word Heading 6 was kept at Markdown heading level 6" in warning for warning in warnings)
    assert all("Unrecognised paragraph style: Title" not in warning for warning in warnings)
    assert all("Unrecognised paragraph style: Subtitle" not in warning for warning in warnings)
    assert "_inline_media_source_markdown" not in preview
    assert "_inline_svg_source_markup" not in preview


def test_docx_without_title_uses_filename_without_promoting_first_heading() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged_bytes(
            root,
            "no-title-notes.docx",
            semantic_docx_bytes(
                include_title=False,
                include_heading_6=False,
                include_unknown_style=False,
            ),
        )
        preview = _preview(root, "no-title-notes.docx")

    markdown = str(preview["markdown_preview"])
    assert preview["title"] == "No Title Notes"
    assert preview["title_source"] == "filename"
    assert markdown.startswith("## First Section")
    assert not markdown.startswith("# First Section")


def test_docx_adapter_passes_generated_html_unchanged_to_html_preview(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged_bytes(root, "unchanged.docx", semantic_docx_bytes())
        paths = configured_workspace_paths(root)
        source_path = docs_import_preview.resolve_staged_import_source(paths.import_staging, "unchanged.docx")
        expected_html = docs_import_docx.convert_docx_to_html(source_path).html
        captured: dict[str, str] = {}
        original = docs_import_preview.generate_html_content_import_preview

        def capture_html(**kwargs):
            captured["source_html"] = kwargs["source_html"]
            return original(**kwargs)

        monkeypatch.setattr(docs_import_preview, "generate_html_content_import_preview", capture_html)
        _preview(root, "unchanged.docx")

    assert captured["source_html"] == expected_html


def test_docx_adapter_locks_mammoth_options(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    source_path = tmp_path / "locked-policy.docx"
    source_path.write_bytes(b"fixture")
    captured: dict[str, object] = {}

    def fake_convert_to_html(source_file, **kwargs):
        captured["source_bytes"] = source_file.read()
        captured.update(kwargs)
        return SimpleNamespace(
            value='<h1 class="dlf-docx-title">Locked Policy</h1>',
            messages=[],
        )

    monkeypatch.setattr(mammoth, "convert_to_html", fake_convert_to_html)
    conversion = docs_import_docx.convert_docx_to_html(source_path)

    assert conversion.html == '<h1 class="dlf-docx-title">Locked Policy</h1>'
    assert conversion.title == "Locked Policy"
    assert captured["source_bytes"] == b"fixture"
    assert captured["style_map"] == docs_import_docx.DOCX_STYLE_MAP
    assert captured["include_default_style_map"] is True
    assert captured["include_embedded_style_map"] is False
    assert captured["external_file_access"] is False
    assert callable(captured["convert_image"])
    assert set(docs_import_docx.DOCX_IMAGE_CONTENT_TYPES.values()) == {
        "image/gif",
        "image/jpeg",
        "image/png",
        "image/webp",
    }


def test_docx_uses_existing_ordinary_source_service_preview() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged_bytes(root, "service-preview.docx", semantic_docx_bytes())

        payload = handle_import_source(
            root,
            {
                "scope": "library",
                "staged_filename": "service-preview.docx",
                "preview_only": True,
            },
            dry_run=False,
        )

    assert payload["ok"] is True
    assert payload["preview_only"] is True
    assert payload["import_preview"]["source_format"] == "docx"
    assert payload["import_preview"]["title"] == "A Word Title"
    assert payload["summary_text"] == "Prepared import preview for service-preview.docx."


def test_docx_preview_plans_supported_images_without_returning_conversion_bodies() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged_bytes(root, "word-images.docx", embedded_image_docx_bytes())

        payload = handle_import_source(
            root,
            {
                "scope": "library",
                "staged_filename": "word-images.docx",
                "preview_only": True,
            },
            dry_run=False,
        )

    preview = payload["import_preview"]
    serialized = json.dumps(payload)
    assert payload["ok"] is True
    assert payload["preview_only"] is True
    assert preview["source_format"] == "docx"
    assert len(preview["media_plans"]) == 1
    assert preview["media_plans"][0]["mime_type"] == "image/png"
    assert preview["media_plans"][0]["size_bytes"] == len(b"word-png-bytes")
    assert "Word image 01" in preview["markdown_preview"]
    assert "Unsupported diagram" in preview["markdown_preview"]
    assert "Unreadable diagram" in preview["markdown_preview"]
    assert any("unsupported media type image/tiff and was omitted" in warning for warning in preview["warnings"])
    assert any("could not be read and was omitted" in warning for warning in preview["warnings"])
    assert "data:image/" not in serialized
    assert "_inline_media_source_markdown" not in serialized
    assert "_inline_svg_source_markup" not in serialized


def test_docx_import_materializes_supported_image_before_source_write() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
        write_staged_bytes(root, "word-images.docx", embedded_image_docx_bytes())
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
                {"scope": "library", "staged_filename": "word-images.docx"},
                dry_run=False,
            )
        finally:
            write_rebuild.perform_source_write_and_rebuild = original_rebuild
            docs_import_preview.validate_markdown_preview = original_validation

        source_text = (root / payload["path"]).read_text(encoding="utf-8")
        media_filename = f"{payload['doc_id']}-image-01.png"
        media_path = root / "site/assets/data/docs/scopes/library/media/img" / media_filename
        media_bytes = media_path.read_bytes()
        response_text = json.dumps(payload)

    assert payload["ok"] is True
    assert payload["operation"] == "create"
    assert payload["rebuild"]["docs"]["doc_ids"] == [payload["doc_id"]]
    assert media_bytes == b"word-png-bytes"
    assert payload["inline_media_written"][0]["artifact_identity"] == media_filename
    assert f"[[media:docs/library/img/{media_filename}]]" in source_text
    assert "data:image/" not in source_text
    assert "data:image/" not in response_text
    assert "_inline_media_source_markdown" not in response_text


def test_docx_collision_requires_confirmation_and_overwrites_through_shared_path() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(
            root,
            "word-images.md",
            {"doc_id": "word-images", "title": "Existing Word", "parent_id": ""},
            body="# Existing Word\n\nOld body.\n",
        )
        write_staged_bytes(root, "word-images.docx", embedded_image_docx_bytes())
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
                {"scope": "library", "staged_filename": "word-images.docx"},
                dry_run=False,
            )
            apply_payload = handle_import_source(
                root,
                {
                    "scope": "library",
                    "staged_filename": "word-images.docx",
                    "overwrite_doc_id": "word-images",
                    "confirm_overwrite": True,
                },
                dry_run=False,
            )
        finally:
            write_rebuild.perform_source_write_and_rebuild = original_rebuild
            docs_import_preview.validate_markdown_preview = original_validation

        source_text = (root / "docs-viewer/source/library/documents/word-images.md").read_text(encoding="utf-8")

    assert preview_payload["preview_only"] is True
    assert preview_payload["requires_doc_overwrite_confirmation"] is True
    assert apply_payload["operation"] == "overwrite"
    assert apply_payload["doc_id"] == "word-images"
    assert "# Word Image Import" in source_text
    assert "Old body." not in source_text
    assert "[[media:docs/library/img/word-images-image-01.png]]" in source_text


def test_docx_media_publication_failure_does_not_write_document_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
        write_staged_bytes(root, "blocked-word.docx", embedded_image_docx_bytes())
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
                    filename="blocked.png",
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
                    {"scope": "library", "staged_filename": "blocked-word.docx"},
                    dry_run=False,
                )
        finally:
            write_rebuild.perform_source_write_and_rebuild = original_rebuild
            docs_import_preview.validate_markdown_preview = original_validation

        after = sorted(documents_root.glob("*.md"))

    assert after == before


def test_docx_preview_rejects_malformed_and_unsafe_sources() -> None:
    with make_repo() as temp:
        root = Path(temp)
        paths = configured_workspace_paths(root)
        write_staged_bytes(root, "malformed.docx", b"not-a-docx-package")
        outside = root / "outside.docx"
        outside.write_bytes(semantic_docx_bytes())
        (paths.import_staging / "linked.docx").symlink_to(outside)
        nested = paths.import_staging / "nested/source.docx"
        nested.parent.mkdir()
        nested.write_bytes(semantic_docx_bytes())
        documents_root = root / "docs-viewer/source/library/documents"
        before = sorted(documents_root.glob("*.md"))

        with pytest.raises(ValueError, match=r"malformed\.docx: BadZipFile"):
            handle_import_source(
                root,
                {"scope": "library", "staged_filename": "malformed.docx"},
                dry_run=False,
            )
        with pytest.raises(ValueError, match="must not be symlinks"):
            docs_import_preview.resolve_staged_import_source(paths.import_staging, "linked.docx")
        with pytest.raises(ValueError, match="direct children"):
            docs_import_preview.resolve_staged_import_source(paths.import_staging, "nested/source.docx")
        after = sorted(documents_root.glob("*.md"))

    assert after == before
