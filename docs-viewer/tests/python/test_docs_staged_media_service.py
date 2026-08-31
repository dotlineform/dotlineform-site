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
from docs_scope_config import load_docs_scope_configs, resolve_location_path
from repo_factory import docs_scope_record, write_docs_scope_config


@pytest.fixture(autouse=True)
def isolated_media_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    projects = tmp_path / "projects"
    (projects / "docs-viewer").mkdir(parents=True)
    monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(projects))


def managed_media_path(repo_root: Path, scope: str, *parts: str) -> Path:
    config = load_docs_scope_configs(repo_root, scope_ids=(scope,))[scope]
    if parts[0] == "build-source":
        location = config.media.build_sources[parts[1]].location
        identity = Path(*parts[2:])
    else:
        location = config.media.types[parts[0]].source_location
        identity = Path(*parts[1:])
    return resolve_location_path(repo_root, location) / identity


def test_staged_media_listing_separates_images_and_files() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged_bytes(root, "photo.png", b"png")
        write_staged_text(root, "diagram.svg", "<svg xmlns='http://www.w3.org/2000/svg'/>")
        write_staged_text(root, "architecture.mmd", "flowchart LR\nA --> B\n")
        write_staged_bytes(root, "notes.pdf", b"pdf")
        write_staged_text(root, "document.md", "# Document\n")

        images = staged_media.list_staged_media_files(root, "example", "image")["files"]
        files = staged_media.list_staged_media_files(root, "example", "file")["files"]

    assert [item["filename"] for item in images] == ["architecture.mmd", "diagram.svg", "photo.png"]
    assert [item["media_format"] for item in images] == ["mermaid", "svg", "raster"]
    assert [item["filename"] for item in files] == ["notes.pdf"]


def test_staged_media_accepts_safe_spaces_and_unicode_in_media_identity() -> None:
    filename = "Energy Wells ↔ Memory Attractor Basins.svg"
    with make_repo() as temp:
        root = Path(temp)
        write_staged_text(root, filename, "<svg xmlns='http://www.w3.org/2000/svg'><title>Energy wells</title></svg>")

        listing = staged_media.list_staged_media_files(root, "example", "image")
        payload = staged_media.apply_staged_media(root, {
            "scope": "example",
            "media_kind": "image",
            "staged_filename": filename,
            "label": "Energy wells",
        })
        published = managed_media_path(root, "example", "svg", "energy-wells-memory-attractor-basins.svg")

        assert published.exists()

    assert [item["filename"] for item in listing["files"]] == [filename]
    assert payload["staged_filename"] == filename
    assert payload["published_filename"] == "energy-wells-memory-attractor-basins.svg"
    assert payload["media_identity"] == "docs/example/svg/energy-wells-memory-attractor-basins.svg"


def test_management_routes_expose_staged_media_listing_and_write_free_preview() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged_bytes(root, "photo.png", b"png")

        listing = docs_management_read_service.docs_management_get_payload(
            root,
            routes.STAGED_MEDIA_FILES_PATH,
            {"scope": ["example"], "media_kind": ["image"]},
        )
        status, preview = docs_management_service.docs_management_post_response(
            root,
            routes.STAGED_MEDIA_PREVIEW_PATH,
            {
                "scope": "example",
                "media_kind": "image",
                "staged_filename": "photo.png",
                "label": "Photo",
            },
        )
        published = managed_media_path(root, "example", "img", "photo.png")

        assert not published.exists()

    assert status == HTTPStatus.OK
    assert [item["filename"] for item in listing["files"]] == ["photo.png"]
    assert preview["collision"] == "new"


def test_add_image_publishes_then_returns_markdown_without_creating_a_doc() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged_bytes(root, "photo.png", b"png bytes")
        documents_root = root / "docs-viewer/scopes/example/source/documents"
        before = sorted(documents_root.glob("*.md"))

        preview = staged_media.preview_staged_media(root, {
            "scope": "example",
            "media_kind": "image",
            "staged_filename": "photo.png",
            "label": "A quiet field",
        })
        payload = staged_media.apply_staged_media(root, {
            "scope": "example",
            "media_kind": "image",
            "staged_filename": "photo.png",
            "label": "A quiet field",
        })
        after = sorted(documents_root.glob("*.md"))
        published = managed_media_path(root, "example", "img", "photo.png")
        published_bytes = published.read_bytes()

    assert preview["collision"] == "new"
    assert preview["add_caption"] is False
    assert payload["publish"]["status"] == "uploaded"
    assert payload["add_caption"] is False
    assert published_bytes == b"png bytes"
    assert payload["markdown"] == "![A quiet field]([[media:docs/example/img/photo.png]])"
    assert before == after


def test_add_image_caption_uses_explicit_full_figure_contract() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged_bytes(root, "photo.png", b"png bytes")
        request = {
            "scope": "example",
            "media_kind": "image",
            "staged_filename": "photo.png",
            "label": "A [quiet] field & <stream>",
            "add_caption": True,
            "caption": "A [quiet] field & <stream>",
            "placement": "full",
            "fill_width": True,
        }

        preview = staged_media.preview_staged_media(root, request)
        payload = staged_media.apply_staged_media(root, request)

    expected = (
        '<figure class="docsViewerFigure docsViewerFigure--full-column">\n'
        '  <img src="[[media:docs/example/img/photo.png]]" '
        'alt="A [quiet] field &amp; &lt;stream&gt;">\n'
        "  <figcaption>\n"
        '    <span class="docsViewerFigure__caption">'
        "A [quiet] field &amp; &lt;stream&gt;</span>\n"
        "  </figcaption>\n"
        "</figure>"
    )
    assert preview["add_caption"] is True
    assert preview["markdown"] == expected
    assert payload["add_caption"] is True
    assert payload["markdown"] == expected


def test_add_image_preview_and_apply_share_explicit_figure_fragment() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged_bytes(root, "photo.png", b"png bytes")
        request = {
            "scope": "example",
            "media_kind": "image",
            "staged_filename": "photo.png",
            "label": "Alternative text",
            "add_caption": True,
            "caption": "Visible caption",
            "summary": "Supporting copy\nSecond line",
            "placement": "left",
            "fill_width": False,
        }

        preview = staged_media.preview_staged_media(root, request)
        payload = staged_media.apply_staged_media(root, request)

    expected = (
        '<figure class="docsViewerFigure docsViewerFigure--image-left '
        'docsViewerFigure--natural-width">\n'
        '  <img src="[[media:docs/example/img/photo.png]]" alt="Alternative text">\n'
        "  <figcaption>\n"
        '    <span class="docsViewerFigure__caption">Visible caption</span>\n'
        '    <span class="docsViewerFigure__summary">Supporting copy\nSecond line</span>\n'
        "  </figcaption>\n"
        "</figure>"
    )
    assert preview["markdown"] == expected
    assert payload["markdown"] == expected


def test_add_image_rejects_explicit_empty_caption_and_invalid_placement() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged_bytes(root, "photo.png", b"png bytes")
        request = {
            "scope": "example",
            "media_kind": "image",
            "staged_filename": "photo.png",
            "label": "Alternative text",
            "add_caption": True,
            "caption": "",
            "placement": "full",
            "fill_width": True,
        }

        with pytest.raises(ValueError, match="caption is required"):
            staged_media.preview_staged_media(root, request)
        with pytest.raises(ValueError, match="placement must be one of"):
            staged_media.preview_staged_media(
                root,
                {**request, "caption": "Caption", "placement": "center"},
            )


def test_add_image_caption_requires_explicit_caption_and_placement() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged_bytes(root, "photo.png", b"png bytes")
        request = {
            "scope": "example",
            "media_kind": "image",
            "staged_filename": "photo.png",
            "label": "Alternative text",
            "add_caption": True,
        }

        with pytest.raises(ValueError, match="caption is required"):
            staged_media.preview_staged_media(root, request)
        with pytest.raises(ValueError, match="placement is required"):
            staged_media.preview_staged_media(
                root,
                {**request, "caption": "Visible caption"},
            )
        with pytest.raises(ValueError, match="fill_width must be a boolean"):
            staged_media.preview_staged_media(
                root,
                {**request, "caption": "Visible caption", "placement": "full"},
            )


def test_add_file_publishes_to_file_media_role() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged_bytes(root, "notes.pdf", b"%PDF")

        payload = staged_media.apply_staged_media(root, {
            "scope": "example",
            "media_kind": "file",
            "staged_filename": "notes.pdf",
            "label": "Research notes",
            "add_caption": True,
        })
        published = managed_media_path(root, "example", "files", "notes.pdf")

        assert published.read_bytes() == b"%PDF"

    assert payload["add_caption"] is False
    assert payload["markdown"] == "[Research notes]([[media:docs/example/files/notes.pdf]])"


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
            [
                docs_scope_record(
                    "notes",
                    scope_type="local",
                    scope_root_provider="external_local",
                    default_doc_id="notes",
                )
            ],
        )
        (staging_root / "diagram.png").write_bytes(b"diagram")

        payload = staged_media.apply_staged_media(root, {
            "scope": "notes",
            "media_kind": "image",
            "staged_filename": "diagram.png",
            "label": "Diagram",
        })
        target = projects_root / "docs-viewer/scopes/notes/source/media/img/diagram.png"
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
            "scope": "example",
            "media_kind": "image",
            "staged_filename": "diagram.svg",
            "label": "Energy wells",
        }
        first = staged_media.apply_staged_media(root, request)
        published = managed_media_path(root, "example", "svg", "diagram.svg")
        sanitized = published.read_text(encoding="utf-8")

        write_staged_text(root, "diagram.svg", "<svg xmlns='http://www.w3.org/2000/svg'><circle r='4'/></svg>")
        replacement = staged_media.preview_staged_media(root, request)
        with pytest.raises(ValueError, match="confirm replacement"):
            staged_media.apply_staged_media(root, request)
        replaced = staged_media.apply_staged_media(root, {**request, "confirm_replace": True})
        replaced_bytes = published.read_bytes()

    assert first["svg"]["title"] == "Energy wells"
    assert first["markdown"] == "![Energy wells]([[media:docs/example/svg/diagram.svg]])"
    assert "<script" not in sanitized
    assert "onclick" not in sanitized
    assert "https://example.com" not in sanitized
    assert "url(#gradient)" in sanitized
    assert replacement["collision"] == "replace"
    assert replacement["requires_replace_confirmation"] is True
    assert replaced["publish"]["status"] == "overwritten"
    assert b"<circle" in replaced_bytes


def _configure_example_mermaid(root: Path) -> None:
    record = docs_scope_record(
        "example",
        scope_type="public",
        viewer_base_url="/example/",
        include_scope_param=False,
        default_doc_id="example",
        allow_unresolved_parent_ids=True,
        media_provider="repository",
        media_location_root="site/assets/data/docs/scopes/example/media",
        media_served_root="/assets/data/docs/scopes/example/media",
        media_types=("img", "svg", "files", "html"),
    )
    record["media"]["build_sources"] = {  # type: ignore[index]
        "mermaid": {
            "producer": "mermaid",
            "publishes_to": "svg",
        }
    }
    record["media"]["types"]["svg"]["build_inputs"] = ["mermaid"]  # type: ignore[index]
    write_docs_scope_config(root, [record])


def _fake_mermaid_producer(context) -> tuple[str, ...]:
    source = context.source.read("architecture.mmd").decode("utf-8")
    if "FAIL" in source:
        raise RuntimeError("fixture renderer failed")
    width = "20" if "changed" in source else "10"
    rendered = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50">
<title>Architecture flow</title><desc>Verified fixture diagram.</desc><rect width="{width}" height="10"/>
</svg>""".encode("utf-8")
    context.generated.replace("architecture.svg", rendered, content_type="image/svg+xml")
    return ("architecture.svg",)


def test_add_mermaid_copies_canonical_source_renders_svg_and_returns_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_repo() as temp:
        root = Path(temp)
        _configure_example_mermaid(root)
        write_staged_text(
            root,
            "architecture.mmd",
            """flowchart LR
    accTitle: Architecture flow
    accDescr: Source flows to a rendered diagram.
    A --> B
""",
        )
        staged = staged_media.configured_workspace_paths(root).import_staging / "architecture.mmd"
        monkeypatch.setattr(staged_media, "produce_mermaid_svg", _fake_mermaid_producer)
        documents_root = root / "docs-viewer/scopes/example/source/documents"
        before = sorted(documents_root.glob("*.md"))

        payload = staged_media.apply_staged_media(root, {
            "scope": "example",
            "media_kind": "image",
            "staged_filename": "architecture.mmd",
            "label": "Architecture",
        })
        after = sorted(documents_root.glob("*.md"))
        canonical = managed_media_path(root, "example", "build-source", "mermaid", "architecture.mmd")
        published = resolve_location_path(
            root,
            load_docs_scope_configs(root)["example"].media.types["svg"].generated_location,
        ) / "architecture.svg"

        assert staged.is_file()
        assert canonical.read_bytes() == staged.read_bytes()
        assert b"<rect" in published.read_bytes()

    assert payload["media_format"] == "mermaid"
    assert payload["source_identity"] == "architecture.mmd"
    assert payload["media_identity"] == "docs/example/svg/architecture.svg"
    assert payload["markdown"] == "![Architecture]([[media:docs/example/svg/architecture.svg]])"
    assert before == after


def test_add_mermaid_normalizes_the_canonical_extension() -> None:
    with make_repo() as temp:
        root = Path(temp)
        _configure_example_mermaid(root)
        write_staged_text(root, "Architecture.MMD", "flowchart LR\nA --> B\n")

        _scope, _kind, _source, _label, media_class, media_filename = staged_media._staged_media_contract(
            root,
            {
                "scope": "example",
                "media_kind": "image",
                "staged_filename": "Architecture.MMD",
                "label": "Architecture",
            },
        )

    assert media_class == "mermaid"
    assert media_filename == "Architecture.mmd"


def test_add_mermaid_renders_before_configured_source_or_svg_publication(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_repo() as temp:
        root = Path(temp)
        _configure_example_mermaid(root)
        write_staged_text(root, "architecture.mmd", "FAIL\n")
        monkeypatch.setattr(staged_media, "produce_mermaid_svg", _fake_mermaid_producer)

        with pytest.raises(RuntimeError, match="fixture renderer failed"):
            staged_media.apply_staged_media(root, {
                "scope": "example",
                "media_kind": "image",
                "staged_filename": "architecture.mmd",
                "label": "Architecture",
            })

        assert not managed_media_path(root, "example", "build-source", "mermaid", "architecture.mmd").exists()
        assert not (
            resolve_location_path(
                root,
                load_docs_scope_configs(root)["example"].media.types["svg"].generated_location,
            )
            / "architecture.svg"
        ).exists()


def test_add_mermaid_requires_confirmation_when_canonical_or_rendered_bytes_change(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_repo() as temp:
        root = Path(temp)
        _configure_example_mermaid(root)
        monkeypatch.setattr(staged_media, "produce_mermaid_svg", _fake_mermaid_producer)
        request = {
            "scope": "example",
            "media_kind": "image",
            "staged_filename": "architecture.mmd",
            "label": "Architecture",
        }
        write_staged_text(root, "architecture.mmd", "initial\n")
        staged_media.apply_staged_media(root, request)
        write_staged_text(root, "architecture.mmd", "changed\n")

        preview = staged_media.preview_staged_media(root, request)
        with pytest.raises(ValueError, match="confirm replacement"):
            staged_media.apply_staged_media(root, request)
        payload = staged_media.apply_staged_media(root, {**request, "confirm_replace": True})

    assert preview["collision"] == "replace"
    assert preview["requires_replace_confirmation"] is True
    assert payload["publish"]["status"] == "overwritten"


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
                    scope="example",
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
                "scope": "example",
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
                "scope": "example",
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
