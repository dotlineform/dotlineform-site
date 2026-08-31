#!/usr/bin/env python3
"""Focused checks for static HTML snapshot media planning."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from repo_factory import docs_scope_record, write_docs_scope_config


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
if str(DOCS_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(DOCS_SERVICES_DIR))

import docs_static_html_export_media as media_export  # noqa: E402
from docs_scope_config import load_docs_scope_configs  # noqa: E402


class FakeRemoteClient:
    def __init__(self, objects: dict[str, bytes]) -> None:
        self.objects = dict(objects)

    def list_objects(self, prefix: str):
        return [
            SimpleNamespace(key=key, size=len(value), etag=f"etag-{len(value)}")
            for key, value in self.objects.items()
            if key.startswith(prefix)
        ]

    def get_object(self, key: str) -> bytes:
        try:
            return self.objects[key]
        except KeyError as exc:
            raise FileNotFoundError(key) from exc

    def head_object(self, key: str):
        value = self.objects.get(key)
        return None if value is None else SimpleNamespace(size=len(value), etag=f"etag-{len(value)}")

    def put_object(self, key: str, path: Path, content_type: str) -> None:
        del content_type
        self.objects[key] = path.read_bytes()

    def delete_object(self, key: str) -> None:
        del self.objects[key]


def configured_scope(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    record: dict[str, object],
) -> tuple[Path, object]:
    repo_root = tmp_path / "repo"
    projects_root = tmp_path / "projects"
    (projects_root / "docs-viewer").mkdir(parents=True)
    monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(projects_root))
    write_docs_scope_config(repo_root, [record])
    scope_id = str(record["scope_id"])
    return repo_root, load_docs_scope_configs(repo_root, scope_ids=(scope_id,))[scope_id]


def test_srcset_parser_preserves_descriptors_and_data_url_commas() -> None:
    candidates = media_export.parse_srcset(
        "/docs/media/example/img/photo.png 1x, /docs/media/example/img/photo@2x.png 2x"
    )
    assert candidates == (
        media_export.SrcsetCandidate("/docs/media/example/img/photo.png", "1x"),
        media_export.SrcsetCandidate("/docs/media/example/img/photo@2x.png", "2x"),
    )
    assert media_export.render_srcset(candidates) == (
        "/docs/media/example/img/photo.png 1x, /docs/media/example/img/photo@2x.png 2x"
    )
    assert media_export.parse_srcset("data:image/png;base64,AAAA 1x") == (
        media_export.SrcsetCandidate("data:image/png;base64,AAAA", "1x"),
    )


def test_owned_reference_requires_exact_prefix_authority_and_confined_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _repo_root, config = configured_scope(
        tmp_path,
        monkeypatch,
        docs_scope_record("example", media_served_root="https://media.example.test/docs/example"),
    )
    owned = media_export.owned_media_reference(
        "/docs/media/example/img/nested/photo%20one.png?cache=1#view",
        config.media.types,
    )
    assert owned == media_export.OwnedMediaReference("img", "nested/photo one.png", "view")
    assert media_export.owned_media_reference(
        "/docs/media/other/img/photo.png",
        config.media.types,
    ) is None
    assert media_export.owned_media_reference(
        "/docs/media/example/image/photo.png",
        config.media.types,
    ) is None
    with pytest.raises(ValueError, match="confined relative path"):
        media_export.owned_media_reference(
            "/docs/media/example/img/%2e%2e/escape.png",
            config.media.types,
        )


def test_repository_plan_reads_deduplicates_rewrites_and_records_dependencies(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root, config = configured_scope(
        tmp_path,
        monkeypatch,
        docs_scope_record("example", media_provider="repository"),
    )
    media_root = repo_root / "docs-viewer/scopes/example/generated/media"
    (media_root / "img").mkdir(parents=True)
    (media_root / "files").mkdir(parents=True)
    (media_root / "img/photo one.png").write_bytes(b"photo")
    (media_root / "files/manual.pdf").write_bytes(b"manual")
    payloads = {
        "doc-a": {
            "content_html": (
                '<p><img src="/docs/media/example/img/photo%20one.png?cache=1#view" alt="Photo &amp; view">'
                '<a href="/docs/media/example/files/manual.pdf?download=1">Manual</a>'
                '<img src="images/local.png?cache=2">'
                '<a href="https://example.test/page">Ordinary link</a></p>'
                '<pre><code class="language-mermaid">a &amp; b\nc</code></pre>'
            )
        },
        "doc-b": {"content_html": '<img src="/docs/media/example/img/photo%20one.png">'},
    }

    plan = media_export.plan_snapshot_media(repo_root, config, payloads)

    assert [(item.media_type, item.identity, item.doc_ids) for item in plan.items] == [
        ("files", "manual.pdf", ("doc-a",)),
        ("img", "photo one.png", ("doc-a", "doc-b")),
    ]
    assert plan.media_bytes == 11
    assert plan.items[0].packaged_path == Path("media/files/manual.pdf")
    assert plan.items[1].packaged_path == Path("media/img/photo one.png")
    rewritten = plan.rewritten_html_by_doc["doc-a"]
    assert 'src="../media/img/photo%20one.png#view"' in rewritten
    assert 'href="../media/files/manual.pdf"' in rewritten
    assert 'alt="Photo &amp; view"' in rewritten
    assert 'href="https://example.test/page"' in rewritten
    assert '<pre><code class="language-mermaid">a &amp; b\nc</code></pre>' in rewritten
    assert [item.manifest_record() for item in plan.external_dependencies] == [
        {
            "reference": "images/local.png",
            "element": "img",
            "attribute": "src",
            "doc_ids": ["doc-a"],
        }
    ]


def test_external_local_plan_uses_scope_location_without_provider_search(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root, config = configured_scope(
        tmp_path,
        monkeypatch,
        docs_scope_record(
            "external",
            scope_type="local",
            scope_root_provider="external_local",
        ),
    )
    media_path = tmp_path / "projects/docs-viewer/scopes/external/generated/media/svg/diagram.svg"
    media_path.parent.mkdir(parents=True)
    media_path.write_bytes(b"<svg/>")

    plan = media_export.plan_snapshot_media(
        repo_root,
        config,
        {"doc": {"content_html": '<img src="/docs/media/external/svg/diagram.svg">'}},
    )

    assert [(item.provider, item.identity, item.data) for item in plan.items] == [
        ("external_local", "diagram.svg", b"<svg/>"),
    ]


def test_public_scope_plan_reads_managed_media_instead_of_public_projection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root, config = configured_scope(
        tmp_path,
        monkeypatch,
        docs_scope_record(
            "public",
            scope_type="public",
            viewer_base_url="/public/",
            include_scope_param=False,
        ),
    )
    media_path = repo_root / "docs-viewer/scopes/public/generated/media/img/photo.webp"
    media_path.parent.mkdir(parents=True)
    media_path.write_bytes(b"managed-photo")

    plan = media_export.plan_snapshot_media(
        repo_root,
        config,
        {
            "doc": {
                "content_html": '<img src="/docs/media/public/img/photo.webp?v=2">'
            }
        },
    )

    assert [(item.provider, item.identity, item.data) for item in plan.items] == [
        ("repository", "photo.webp", b"managed-photo"),
    ]
    assert 'src="../media/img/photo.webp"' in plan.rewritten_html_by_doc["doc"]


def test_plan_rewrites_srcset_iframe_and_link_but_does_not_recurse(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root, config = configured_scope(
        tmp_path,
        monkeypatch,
        docs_scope_record(
            "example",
            media_provider="repository",
            media_types=("img", "html"),
        ),
    )
    media_root = repo_root / "docs-viewer/scopes/example/generated/media"
    for relative, content in (
        ("img/one.png", b"one"),
        ("img/two.png", b"two"),
        ("html/widget.html", b'<script src="remote.js"></script>'),
    ):
        path = media_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    source = (
        '<img srcset="/docs/media/example/img/one.png 1x, /docs/media/example/img/two.png 2x">'
        '<iframe src="/docs/media/example/html/widget.html"></iframe>'
        '<link href="https://cdn.example.test/theme.css" rel="stylesheet">'
    )

    plan = media_export.plan_snapshot_media(repo_root, config, {"doc": {"content_html": source}})

    rewritten = plan.rewritten_html_by_doc["doc"]
    assert 'srcset="../media/img/one.png 1x, ../media/img/two.png 2x"' in rewritten
    assert 'src="../media/html/widget.html"' in rewritten
    assert [item.identity for item in plan.items] == ["widget.html", "one.png", "two.png"]
    assert plan.items[0].data == b'<script src="remote.js"></script>'
    assert plan.external_dependencies[0].reference == "https://cdn.example.test/theme.css"


def test_missing_owned_media_fails_without_downgrading_to_external_dependency(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root, config = configured_scope(
        tmp_path,
        monkeypatch,
        docs_scope_record("example", media_provider="repository"),
    )
    with pytest.raises(ValueError, match="scope-owned media is unavailable: img/missing.png"):
        media_export.plan_snapshot_media(
            repo_root,
            config,
            {"doc": {"content_html": '<img src="/docs/media/example/img/missing.png">'}},
        )


def test_inline_and_ordinary_links_are_not_external_dependencies_and_unowned_html_is_unchanged(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root, config = configured_scope(
        tmp_path,
        monkeypatch,
        docs_scope_record("example", media_provider="repository"),
    )
    source = (
        '<pre><code class="language-mermaid">a &amp; b</code></pre>'
        '<img src="data:image/png;base64,AAAA">'
        '<a href="https://example.test/page?token=visible">Page</a>'
    )

    plan = media_export.plan_snapshot_media(repo_root, config, {"doc": {"content_html": source}})

    assert plan.items == ()
    assert plan.external_dependencies == ()
    assert plan.rewritten_html_by_doc["doc"] == source


def test_external_dependency_manifest_removes_credentials_query_and_fragment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root, config = configured_scope(
        tmp_path,
        monkeypatch,
        docs_scope_record("example", media_provider="repository"),
    )
    plan = media_export.plan_snapshot_media(
        repo_root,
        config,
        {
            "doc": {
                "content_html": (
                    '<img src="https://user:secret@cdn.example.test/photo.png?token=one#view">'
                )
            }
        },
    )

    assert plan.external_dependencies[0].reference == "https://cdn.example.test/photo.png"
