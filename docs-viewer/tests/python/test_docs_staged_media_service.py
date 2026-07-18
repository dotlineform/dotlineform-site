#!/usr/bin/env python3
"""Source-editor staged media publication contracts."""

from __future__ import annotations

from pathlib import Path
from http import HTTPStatus

import pytest

import docs_staged_media_service as staged_media
import docs_management_read_service
import docs_management_routes as routes
import docs_management_service
from docs_import_test_support import make_repo, write_staged_bytes, write_staged_text
from docs_media_storage import DocsMediaPublishResult
from repo_factory import docs_scope_record, write_docs_scope_config


def test_staged_media_listing_separates_images_and_files() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged_bytes(root, "photo.png", b"png")
        write_staged_text(root, "diagram.svg", "<svg xmlns='http://www.w3.org/2000/svg'/>")
        write_staged_bytes(root, "notes.pdf", b"pdf")
        write_staged_text(root, "document.md", "# Document\n")

        images = staged_media.list_staged_media_files(root, "image")["files"]
        files = staged_media.list_staged_media_files(root, "file")["files"]

    assert [item["filename"] for item in images] == ["diagram.svg", "photo.png"]
    assert [item["media_format"] for item in images] == ["svg", "raster"]
    assert [item["filename"] for item in files] == ["notes.pdf"]


def test_staged_media_accepts_safe_spaces_and_unicode_in_media_identity() -> None:
    filename = "Energy Wells ↔ Memory Attractor Basins.svg"
    with make_repo() as temp:
        root = Path(temp)
        write_staged_text(root, filename, "<svg xmlns='http://www.w3.org/2000/svg'><title>Energy wells</title></svg>")

        listing = staged_media.list_staged_media_files(root, "image")
        payload = staged_media.apply_staged_media(root, {
            "scope": "library",
            "media_kind": "image",
            "staged_filename": filename,
            "label": "Energy wells",
        })
        published = root / "site/assets/data/docs/scopes/library/media/img/energy-wells-memory-attractor-basins.svg"

        assert published.exists()

    assert [item["filename"] for item in listing["files"]] == [filename]
    assert payload["staged_filename"] == filename
    assert payload["published_filename"] == "energy-wells-memory-attractor-basins.svg"
    assert payload["media_identity"].endswith("/energy-wells-memory-attractor-basins.svg")


def test_management_routes_expose_staged_media_listing_and_write_free_preview() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged_bytes(root, "photo.png", b"png")

        listing = docs_management_read_service.docs_management_get_payload(
            root,
            routes.STAGED_MEDIA_FILES_PATH,
            {"media_kind": ["image"]},
        )
        status, preview = docs_management_service.docs_management_post_response(
            root,
            routes.STAGED_MEDIA_PREVIEW_PATH,
            {
                "scope": "library",
                "media_kind": "image",
                "staged_filename": "photo.png",
                "label": "Photo",
            },
        )
        published = root / "site/assets/data/docs/scopes/library/media/img/photo.png"

        assert not published.exists()

    assert status == HTTPStatus.OK
    assert [item["filename"] for item in listing["files"]] == ["photo.png"]
    assert preview["collision"] == "new"


def test_add_image_publishes_then_returns_markdown_without_creating_a_doc() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged_bytes(root, "photo.png", b"png bytes")
        documents_root = root / "docs-viewer/source/library/documents"
        before = sorted(documents_root.glob("*.md"))

        preview = staged_media.preview_staged_media(root, {
            "scope": "library",
            "media_kind": "image",
            "staged_filename": "photo.png",
            "label": "A quiet field",
        })
        payload = staged_media.apply_staged_media(root, {
            "scope": "library",
            "media_kind": "image",
            "staged_filename": "photo.png",
            "label": "A quiet field",
        })
        after = sorted(documents_root.glob("*.md"))
        published = root / "site/assets/data/docs/scopes/library/media/img/photo.png"
        published_bytes = published.read_bytes()

    assert preview["collision"] == "new"
    assert payload["publish"]["status"] == "uploaded"
    assert published_bytes == b"png bytes"
    assert payload["markdown"] == "![A quiet field]([[media:docs/library/img/photo.png]])"
    assert before == after


def test_add_file_publishes_to_file_media_role() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged_bytes(root, "notes.pdf", b"%PDF")

        payload = staged_media.apply_staged_media(root, {
            "scope": "library",
            "media_kind": "file",
            "staged_filename": "notes.pdf",
            "label": "Research notes",
        })
        published = root / "site/assets/data/docs/scopes/library/media/files/notes.pdf"

        assert published.read_bytes() == b"%PDF"

    assert payload["markdown"] == "[Research notes]([[media:docs/library/files/notes.pdf]])"


def test_add_image_uses_external_scope_owned_media_root(monkeypatch: pytest.MonkeyPatch) -> None:
    with make_repo() as temp:
        root = Path(temp)
        projects_root = root / "projects"
        (projects_root / "docs-viewer").mkdir(parents=True)
        staging_root = projects_root / "data-sharing/import-staging"
        staging_root.mkdir(parents=True)
        monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(projects_root))
        write_docs_scope_config(
            root,
            [docs_scope_record("notes", scope_type="local_external", default_doc_id="notes")],
        )
        (staging_root / "diagram.png").write_bytes(b"diagram")

        payload = staged_media.apply_staged_media(root, {
            "scope": "notes",
            "media_kind": "image",
            "staged_filename": "diagram.png",
            "label": "Diagram",
        })
        target = projects_root / "docs-viewer/source/notes/media/img/diagram.png"
        target_bytes = target.read_bytes()

    assert target_bytes == b"diagram"
    assert payload["media_identity"] == "docs/notes/img/diagram.png"
    assert str(projects_root) not in str(payload)


def test_add_svg_uses_shared_sanitizer_and_requires_confirmed_replacement() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged_text(
            root,
            "diagram.svg",
            """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10" onclick="alert(1)">
              <title>Energy wells</title>
              <style>.safe { fill: url(#gradient); }</style>
              <defs><linearGradient id="gradient"/></defs>
              <rect class="safe" width="10" height="10"/>
              <image href="https://example.com/tracker.png"/>
              <script>alert(1)</script>
            </svg>""",
        )
        request = {
            "scope": "library",
            "media_kind": "image",
            "staged_filename": "diagram.svg",
            "label": "Energy wells",
        }
        first = staged_media.apply_staged_media(root, request)
        published = root / "site/assets/data/docs/scopes/library/media/img/diagram.svg"
        sanitized = published.read_text(encoding="utf-8")

        write_staged_text(root, "diagram.svg", "<svg xmlns='http://www.w3.org/2000/svg'><circle r='4'/></svg>")
        replacement = staged_media.preview_staged_media(root, request)
        with pytest.raises(ValueError, match="confirm replacement"):
            staged_media.apply_staged_media(root, request)
        replaced = staged_media.apply_staged_media(root, {**request, "confirm_replace": True})
        replaced_bytes = published.read_bytes()

    assert first["svg"]["title"] == "Energy wells"
    assert "<script" not in sanitized
    assert "onclick" not in sanitized
    assert "https://example.com" not in sanitized
    assert "url(#gradient)" in sanitized
    assert replacement["collision"] == "replace"
    assert replacement["requires_replace_confirmation"] is True
    assert replaced["publish"]["status"] == "overwritten"
    assert b"<circle" in replaced_bytes


def test_add_media_publication_failure_returns_no_insertable_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged_bytes(root, "photo.png", b"changed")
        monkeypatch.setattr(
            staged_media,
            "publish_docs_media_files",
            lambda *_args, **_kwargs: [
                DocsMediaPublishResult(
                    scope="library",
                    media_class="img",
                    filename="photo.png",
                    size=7,
                    status="blocked_changed",
                    reason="publication blocked",
                )
            ],
        )

        with pytest.raises(RuntimeError, match="publication did not complete"):
            staged_media.apply_staged_media(root, {
                "scope": "library",
                "media_kind": "image",
                "staged_filename": "photo.png",
                "label": "Photo",
            })


@pytest.mark.parametrize(
    "svg_source",
    [
        "<svg><path></svg>",
        "<!DOCTYPE svg [<!ENTITY payload SYSTEM 'file:///etc/passwd'>]><svg>&payload;</svg>",
        "<html><body>Not SVG</body></html>",
        "<svg xmlns='https://example.com/not-svg'></svg>",
    ],
)
def test_add_svg_rejects_malformed_or_non_self_contained_xml(svg_source: str) -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged_text(root, "diagram.svg", svg_source)

        with pytest.raises(ValueError):
            staged_media.preview_staged_media(root, {
                "scope": "library",
                "media_kind": "image",
                "staged_filename": "diagram.svg",
                "label": "Diagram",
            })


@pytest.mark.parametrize("filename", ["../escape.png", "image.exe"])
def test_staged_media_rejects_unsafe_or_unsupported_identity(filename: str) -> None:
    with make_repo() as temp:
        root = Path(temp)
        with pytest.raises((ValueError, FileNotFoundError)):
            staged_media.preview_staged_media(root, {
                "scope": "studio",
                "media_kind": "image",
                "staged_filename": filename,
                "label": "Image",
            })
