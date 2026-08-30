#!/usr/bin/env python3
"""Focused role, publication, and source-write checks for Docs media storage."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from docs_artifact_locations import (
    EXTERNAL_LOCAL_PROVIDER,
    R2_PROVIDER,
    REPOSITORY_PROVIDER,
    ArtifactLocation,
)
from docs_media_storage import (
    docs_media_file,
    docs_publish_report,
    ensure_configured_scope_owned_media_directories,
    local_media_path_from_route,
    media_adapters_for_scope,
    plan_and_publish_docs_media,
    run_docs_staged_media_publish,
    safe_content_type,
)
from docs_scope_config import (
    DocsManagedMediaConfig,
    DocsMediaConfig,
    DocsGeneratedConfig,
    DocsPublicProjectionConfig,
    DocsPublicMediaConfig,
    DocsPublishedArtifactConfig,
    DocsPublishedConfig,
    DocsScopeConfig,
    DocsSourceConfig,
    load_docs_scope_configs,
)
from docs_scope_manifest import (
    LOCAL_MANAGE_MODE,
    PUBLIC_MODE,
    planned_scope_config_record,
)
from repo_factory import docs_scope_record


class FakeR2Client:
    def __init__(self, remote: dict[str, bytes] | None = None) -> None:
        self.remote = remote or {}
        self.puts: list[tuple[str, str]] = []

    def list_objects(self, prefix: str):
        return [
            SimpleNamespace(key=key, size=len(value), etag=hashlib.md5(value).hexdigest())
            for key, value in self.remote.items()
            if key.startswith(prefix)
        ]

    def get_object(self, key: str) -> bytes:
        return self.remote[key]

    def head_object(self, key: str):
        value = self.remote.get(key)
        return None if value is None else SimpleNamespace(
            size=len(value),
            etag=hashlib.md5(value).hexdigest(),
        )

    def put_object(self, key: str, path: Path, content_type: str) -> None:
        del content_type
        self.remote[key] = path.read_bytes()
        self.puts.append((key, path.name))

    def delete_object(self, key: str) -> None:
        del self.remote[key]


def scope_config(
    scope: str,
    *,
    scope_type: str,
    scope_root_provider: str = REPOSITORY_PROVIDER,
    media_provider: str,
    source: Path | None = None,
    media_location_root: Path | None = None,
) -> DocsScopeConfig:
    local_provider = scope_root_provider
    scope_root = source.parent if source is not None else Path(f"docs-viewer/scopes/{scope}")
    source_path = scope_root / "source"
    generated_docs = scope_root / "generated/documents"
    generated_search = scope_root / "generated/search/index.json"
    published_docs = scope_root / "published/documents"
    published_search = scope_root / "published/search/index.json"
    source_media_root = scope_root / "source/media"
    generated_media_root = scope_root / "generated/media"
    published_media_root = scope_root / "published/media"
    public_media_root = media_location_root or (
        Path(f"docs/{scope}")
        if media_provider == R2_PROVIDER
        else Path(f"site/assets/data/docs/scopes/{scope}/media")
    )
    served_root = (
        f"https://media.example.test/docs/{scope}"
        if media_provider == R2_PROVIDER
        else f"/docs/media/{scope}"
    )
    media = {
        media_type: DocsManagedMediaConfig(
            media_type=media_type,
            reference_prefix=Path(f"docs/{scope}/{media_type}"),
            source_location=ArtifactLocation(provider=local_provider, path=source_media_root / media_type),
            generated_location=ArtifactLocation(provider=local_provider, path=generated_media_root / media_type),
            published_location=ArtifactLocation(provider=local_provider, path=published_media_root / media_type),
            served_path_prefix=f"/docs/media/{scope}/{media_type}",
            build_inputs=(),
        )
        for media_type in ("img", "svg", "files")
    }
    public_projection = None
    if scope_type == "public":
        public_projection = DocsPublicProjectionConfig(
            documents=DocsPublishedArtifactConfig(
                location=ArtifactLocation(
                    provider=REPOSITORY_PROVIDER,
                    path=Path(f"site/assets/data/docs/scopes/{scope}"),
                )
            ),
            search=DocsPublishedArtifactConfig(
                location=ArtifactLocation(
                    provider=REPOSITORY_PROVIDER,
                    path=Path(f"site/assets/data/search/{scope}/index.json"),
                )
            ),
            media={
                media_type: DocsPublicMediaConfig(
                    media_type=media_type,
                    reference_prefix=Path(f"docs/{scope}/{media_type}"),
                    location=ArtifactLocation(provider=media_provider, path=public_media_root / media_type),
                    served_path_prefix=f"{served_root}/{media_type}",
                )
                for media_type, item in media.items()
            },
        )
    return DocsScopeConfig(
        scope_id=scope,
        scope_type=scope_type,
        scope_root=ArtifactLocation(provider=local_provider, path=scope_root),
        source=DocsSourceConfig(
            location=ArtifactLocation(provider=local_provider, path=source_path),
            documents_path=Path("."),
            sub_scopes_path=Path("."),
        ),
        media=DocsMediaConfig(
            source_location=ArtifactLocation(provider=local_provider, path=source_media_root),
            generated_location=ArtifactLocation(provider=local_provider, path=generated_media_root),
            published_location=ArtifactLocation(provider=local_provider, path=published_media_root),
            types=media,
            build_sources={},
        ),
        generated=DocsGeneratedConfig(
            documents=DocsPublishedArtifactConfig(
                location=ArtifactLocation(provider=local_provider, path=generated_docs)
            ),
            search=DocsPublishedArtifactConfig(
                location=ArtifactLocation(provider=local_provider, path=generated_search)
            ),
        ),
        published=DocsPublishedConfig(
            documents=DocsPublishedArtifactConfig(
                location=ArtifactLocation(provider=local_provider, path=published_docs)
            ),
            search=DocsPublishedArtifactConfig(
                location=ArtifactLocation(provider=local_provider, path=published_search)
            ),
        ),
        public_projection=public_projection,
        viewer_base_url=f"/{scope}/" if scope_type == "public" else "/docs/",
        include_scope_param=scope_type != "public",
        default_doc_id=scope,
        non_loadable_doc_ids=(),
        manage_only_tree_root_ids=(),
        allow_unresolved_parent_ids=False,
        sub_scopes=(),
    )


def write_scope_config(repo_root: Path, record: dict[str, object]) -> None:
    path = repo_root / "docs-viewer/config/scopes/docs_scopes.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "docs_scopes_v5",
                "scopes": [record],
            }
        ) + "\n",
        encoding="utf-8",
    )


def public_scope_record(*, media_provider: str = R2_PROVIDER) -> dict[str, object]:
    return docs_scope_record(
        "example",
        scope_type="public",
        viewer_base_url="/example/",
        include_scope_param=False,
        default_doc_id="example",
        media_provider=media_provider,
    )


def external_scope_record(scope: str = "private") -> dict[str, object]:
    return docs_scope_record(
        scope,
        scope_type="local_external",
        scope_root_provider="external_local",
        default_doc_id=scope,
    )


def publish_with_config(
    repo_root: Path,
    config: DocsScopeConfig,
    files,
    *,
    client: FakeR2Client,
    write: bool,
    force: bool,
):
    adapters = media_adapters_for_scope(
        repo_root,
        config,
        {item.media_class for item in files},
        remote_client=client,
    )
    return plan_and_publish_docs_media(files, adapters=adapters, write=write, force=force)


def test_docs_source_import_preflights_complete_set_and_keeps_storage_details_private(tmp_path: Path) -> None:
    config = scope_config("example", scope_type="public", media_provider=R2_PROVIDER)
    first = tmp_path / "first.png"
    second = tmp_path / "second.png"
    first.write_bytes(b"first")
    second.write_bytes(b"second")
    files = [docs_media_file(config, media_class="img", local_path=path, source_root=tmp_path) for path in (first, second)]
    existing = tmp_path / "docs-viewer/scopes/example/source/media/img/first.png"
    existing.parent.mkdir(parents=True)
    existing.write_bytes(b"different")
    client = FakeR2Client()

    results = publish_with_config(tmp_path, config, files, client=client, write=True, force=False)
    report = docs_publish_report(scope="example", results=results, write=True, force=False)

    assert [result.status for result in results] == ["blocked_changed", "not_attempted"]
    assert client.puts == []
    assert report["counts"] == {"blocked_changed": 1, "not_attempted": 1}
    serialized = json.dumps(report)
    assert "docs/example" not in serialized
    assert "md5" not in serialized
    assert "etag" not in serialized.lower()


def test_docs_source_import_writes_missing_objects_after_complete_preflight(tmp_path: Path) -> None:
    config = scope_config("example", scope_type="public", media_provider=R2_PROVIDER)
    image = tmp_path / "diagram.png"
    attachment = tmp_path / "notes.pdf"
    image.write_bytes(b"image")
    attachment.write_bytes(b"pdf")
    files = [
        docs_media_file(config, media_class="img", local_path=image, source_root=tmp_path),
        docs_media_file(config, media_class="files", local_path=attachment, source_root=tmp_path),
    ]
    client = FakeR2Client()

    results = publish_with_config(tmp_path, config, files, client=client, write=True, force=False)

    assert [result.status for result in results] == ["uploaded", "uploaded"]
    assert client.puts == []
    assert (tmp_path / "docs-viewer/scopes/example/source/media/img/diagram.png").read_bytes() == b"image"
    assert (tmp_path / "docs-viewer/scopes/example/source/media/files/notes.pdf").read_bytes() == b"pdf"


def test_exact_scope_staged_file_runner_uses_safe_docs_report(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    projects_base = tmp_path / "projects"
    (projects_base / "docs-viewer").mkdir(parents=True)
    monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(projects_base))
    write_scope_config(tmp_path, public_scope_record())
    staging_root = tmp_path / "import-staging"
    staging_root.mkdir()
    (staging_root / "diagram.png").write_bytes(b"diagram")
    monkeypatch.setattr(
        "docs_media_storage.configured_workspace_paths",
        lambda _repo_root: SimpleNamespace(import_staging=staging_root),
    )

    report = run_docs_staged_media_publish(
        tmp_path,
        scope="example",
        media_class="img",
        staged_filename="diagram.png",
        write=False,
        force=False,
        client=FakeR2Client(),
    )

    assert report["docs_scope"] == "example"
    assert report["counts"] == {"would_upload": 1}
    assert report["objects"][0]["filename"] == "diagram.png"  # type: ignore[index]


def test_scope_config_derives_media_lifecycle_from_external_scope_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    projects_base = tmp_path / "projects"
    (projects_base / "docs-viewer").mkdir(parents=True)
    monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(projects_base))
    external = external_scope_record()
    write_scope_config(tmp_path, external)
    loaded = load_docs_scope_configs(tmp_path)["private"]
    assert {item.source_location.provider for item in loaded.media.types.values()} == {EXTERNAL_LOCAL_PROVIDER}
    assert loaded.media.source_location.path == (
        projects_base / "docs-viewer/scopes/private/source/media"
    )

    external["media"]["types"]["img"]["location"] = {  # type: ignore[index]
        "provider": EXTERNAL_LOCAL_PROVIDER,
        "path": "$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/scopes/elsewhere/source/media/img",
    }
    write_scope_config(tmp_path, external)
    with pytest.raises(ValueError, match="unknown fields: location"):
        load_docs_scope_configs(tmp_path)

    path = tmp_path / "docs-viewer/config/scopes/docs_scopes.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["media_workspace"] = {"location": {"provider": "external_local", "path": "elsewhere"}}
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="media_workspace is retired"):
        load_docs_scope_configs(tmp_path)


def test_new_scope_defaults_follow_scope_owned_media_policy(tmp_path: Path) -> None:
    public = planned_scope_config_record("research", Path("docs-viewer/scopes/research"), "/research/", "research", PUBLIC_MODE)
    local = planned_scope_config_record("notes", Path("unused"), "", "notes", LOCAL_MANAGE_MODE)

    assert public["media"]["types"]["img"] == {"build_inputs": []}  # type: ignore[index]
    assert public["public_projection"]["media"]["img"]["location"]["provider"] == R2_PROVIDER  # type: ignore[index]
    assert public["public_projection"]["media"]["svg"]["location"] == {  # type: ignore[index]
        "provider": REPOSITORY_PROVIDER,
        "path": "site/assets/data/docs/scopes/research/media/svg",
    }
    assert local["media"] == public["media"]
    assert local["public_projection"] is None


def test_local_media_route_confines_repo_and_external_scope_assets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_config = scope_config("studio", scope_type="local", media_provider=REPOSITORY_PROVIDER)
    repo_file = tmp_path / "docs-viewer/scopes/studio/generated/media/img/diagram.png"
    repo_file.parent.mkdir(parents=True)
    repo_file.write_bytes(b"diagram")
    monkeypatch.setattr("docs_media_storage.load_docs_scope_configs", lambda _repo_root: {"studio": repo_config})

    resolved, media_class = local_media_path_from_route(tmp_path, "/docs/media/studio/img/diagram.png")
    assert resolved == repo_file.resolve()
    assert media_class == "img"
    repo_svg = tmp_path / "docs-viewer/scopes/studio/generated/media/svg/diagram.svg"
    repo_svg.parent.mkdir(parents=True)
    repo_svg.write_text("<svg xmlns='http://www.w3.org/2000/svg'></svg>\n", encoding="utf-8")
    resolved, media_class = local_media_path_from_route(tmp_path, "/docs/media/studio/svg/diagram.svg")
    assert resolved == repo_svg.resolve()
    assert media_class == "svg"
    assert safe_content_type(repo_svg) == "image/svg+xml"
    with pytest.raises(ValueError, match="Invalid Docs media route"):
        local_media_path_from_route(tmp_path, "/docs/media/studio/img/nested/diagram.png")
    if hasattr(os, "symlink"):
        outside = tmp_path / "outside.png"
        outside.write_bytes(b"outside")
        os.symlink(outside, repo_file.parent / "escaped.png")
        with pytest.raises(ValueError, match="escapes its configured location"):
            local_media_path_from_route(tmp_path, "/docs/media/studio/img/escaped.png")
    html = tmp_path / "widget.html"
    html.write_text("<script>alert(1)</script>", encoding="utf-8")
    assert safe_content_type(html) == "text/html"

    external_root = tmp_path / "external/docs-viewer"
    external_source = external_root / "scopes/private/source"
    external_config = scope_config(
        "private",
        scope_type="local_external",
        scope_root_provider=EXTERNAL_LOCAL_PROVIDER,
        media_provider=EXTERNAL_LOCAL_PROVIDER,
        source=external_source,
    )
    external_file = external_root / "scopes/private/generated/media/files/notes.pdf"
    external_file.parent.mkdir(parents=True)
    external_file.write_bytes(b"pdf")
    monkeypatch.setattr("docs_media_storage.load_docs_scope_configs", lambda _repo_root: {"private": external_config})

    resolved, media_class = local_media_path_from_route(tmp_path, "/docs/media/private/files/notes.pdf")
    assert resolved == external_file.resolve()
    assert media_class == "files"


def test_configured_local_media_directories_skip_missing_external_scope(tmp_path: Path) -> None:
    repo_scope = tmp_path / "docs-viewer/scopes/studio"
    external_source = tmp_path / "external/docs-viewer/scopes/notes/source"
    external_scope = tmp_path / "external/docs-viewer/scopes/notes"
    missing_external_root = tmp_path / "external/docs-viewer/scopes/missing"
    external_source.mkdir(parents=True)
    configs = {
        "studio": scope_config("studio", scope_type="local", media_provider=REPOSITORY_PROVIDER),
        "notes": scope_config(
            "notes",
            scope_type="local_external",
            scope_root_provider=EXTERNAL_LOCAL_PROVIDER,
            media_provider=EXTERNAL_LOCAL_PROVIDER,
            source=external_source,
        ),
        "missing": scope_config(
            "missing",
            scope_type="local_external",
            scope_root_provider=EXTERNAL_LOCAL_PROVIDER,
            media_provider=EXTERNAL_LOCAL_PROVIDER,
            source=missing_external_root / "source",
        ),
        "example": scope_config("example", scope_type="public", media_provider=R2_PROVIDER),
    }

    materialized = ensure_configured_scope_owned_media_directories(tmp_path, configs)
    ensure_configured_scope_owned_media_directories(tmp_path, configs)

    assert set(materialized) == {"example", "notes", "studio"}
    for scope_root in (
        repo_scope,
        external_scope,
        tmp_path / "docs-viewer/scopes/example",
    ):
        assert all(
            (scope_root / "source/media" / media_class).is_dir()
            for media_class in ("files", "html", "img", "svg")
        )
        assert (scope_root / "source/media/build-source/mermaid").is_dir()
        for lifecycle in ("generated", "published"):
            assert all(
                (scope_root / lifecycle / "media" / media_class).is_dir()
                for media_class in ("files", "img", "svg")
            )
        for lifecycle in ("source", "generated", "published"):
            assert not any(
                (scope_root / lifecycle / "media" / media_class / ".gitkeep").exists()
                for media_class in ("files", "html", "img", "svg")
            )
    assert not missing_external_root.exists()
    assert not (tmp_path / "docs-viewer/scopes/example/source/documents/media").exists()
