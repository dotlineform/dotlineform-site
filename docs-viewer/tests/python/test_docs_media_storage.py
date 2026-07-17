#!/usr/bin/env python3
"""Focused role, publication, and source-write checks for Docs media storage."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

import docs_import_media
from docs_artifact_locations import (
    EXTERNAL_LOCAL_PROVIDER,
    R2_PROVIDER,
    REPOSITORY_PROVIDER,
    ArtifactLocation,
)
from docs_import_content import CONTENT_FORMAT_MARKDOWN, CONTENT_INTENT_REPLACE, ImportContent
from docs_import_document import IMPORT_DOCUMENT_CREATE, ImportDocumentMediaContext, apply_import_document, plan_import_document
from docs_media_storage import (
    DocsMediaPublishResult,
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
    DocsPublicProjectionConfig,
    DocsPublishedArtifactConfig,
    DocsPublishedConfig,
    DocsPublishedMediaConfig,
    DocsScopeConfig,
    DocsSourceConfig,
    load_docs_scope_configs,
)
from docs_scope_manifest import (
    LOCAL_COMMITTED_MODE,
    LOCAL_EXTERNAL_MODE,
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
    media_provider: str,
    source: Path | None = None,
    media_location_root: Path | None = None,
) -> DocsScopeConfig:
    external = scope_type == "local_external"
    local_provider = EXTERNAL_LOCAL_PROVIDER if external else REPOSITORY_PROVIDER
    source_path = source or Path(f"docs-viewer/source/{scope}")
    workspace = source_path.parent.parent if external else Path("docs-viewer")
    published_docs = (
        workspace / "published" / "docs" / scope
        if external
        else Path(f"docs-viewer/published/docs/{scope}")
    )
    published_search = (
        workspace / "published" / "search" / scope / "index.json"
        if external
        else Path(f"docs-viewer/published/search/{scope}/index.json")
    )
    media_root = media_location_root or (
        Path(f"docs/{scope}") if media_provider == R2_PROVIDER else source_path / "media"
    )
    served_root = (
        f"https://media.example.test/docs/{scope}"
        if media_provider == R2_PROVIDER
        else f"/docs/media/{scope}"
    )
    media = {
        media_type: DocsPublishedMediaConfig(
            media_type=media_type,
            reference_prefix=Path(f"docs/{scope}/{media_type}"),
            location=ArtifactLocation(provider=media_provider, path=media_root / media_type),
            served_path_prefix=f"{served_root}/{media_type}",
            build_inputs=(),
        )
        for media_type in ("img", "files")
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
        )
    return DocsScopeConfig(
        scope_id=scope,
        scope_type=scope_type,
        source=DocsSourceConfig(
            location=ArtifactLocation(provider=local_provider, path=source_path),
            documents_path=Path("."),
            build_media={},
            sub_scopes_path=Path("."),
        ),
        published=DocsPublishedConfig(
            documents=DocsPublishedArtifactConfig(
                location=ArtifactLocation(provider=local_provider, path=published_docs)
            ),
            search=DocsPublishedArtifactConfig(
                location=ArtifactLocation(provider=local_provider, path=published_search)
            ),
            media=media,
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
        json.dumps({"schema_version": "docs_scopes_v2", "scopes": [record]}) + "\n",
        encoding="utf-8",
    )


def public_scope_record(*, media_provider: str = R2_PROVIDER) -> dict[str, object]:
    return docs_scope_record(
        "library",
        scope_type="public",
        viewer_base_url="/library/",
        include_scope_param=False,
        default_doc_id="library",
        media_provider=media_provider,
    )


def external_scope_record(scope: str = "private") -> dict[str, object]:
    return docs_scope_record(
        scope,
        scope_type="local_external",
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


def test_docs_upload_preflights_complete_set_and_keeps_remote_details_private(tmp_path: Path) -> None:
    config = scope_config("library", scope_type="public", media_provider=R2_PROVIDER)
    first = tmp_path / "first.png"
    second = tmp_path / "second.png"
    first.write_bytes(b"first")
    second.write_bytes(b"second")
    files = [docs_media_file(config, media_class="img", local_path=path, source_root=tmp_path) for path in (first, second)]
    client = FakeR2Client({"docs/library/img/first.png": b"different"})

    results = publish_with_config(tmp_path, config, files, client=client, write=True, force=False)
    report = docs_publish_report(scope="library", results=results, write=True, force=False)

    assert [result.status for result in results] == ["blocked_changed", "not_attempted"]
    assert client.puts == []
    assert report["counts"] == {"blocked_changed": 1, "not_attempted": 1}
    serialized = json.dumps(report)
    assert "docs/library" not in serialized
    assert "md5" not in serialized
    assert "etag" not in serialized.lower()


def test_docs_upload_writes_missing_objects_after_complete_preflight(tmp_path: Path) -> None:
    config = scope_config("library", scope_type="public", media_provider=R2_PROVIDER)
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
    assert client.puts == [
        ("docs/library/img/diagram.png", "artifact.png"),
        ("docs/library/files/notes.pdf", "artifact.pdf"),
    ]


def test_exact_scope_staged_file_runner_uses_safe_docs_report(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
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
        scope="library",
        media_class="img",
        staged_filename="diagram.png",
        write=False,
        force=False,
        client=FakeR2Client(),
    )

    assert report["docs_scope"] == "library"
    assert report["counts"] == {"would_upload": 1}
    assert report["objects"][0]["filename"] == "diagram.png"  # type: ignore[index]


def test_scope_config_enforces_external_media_containment_and_allows_local_r2(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    projects_base = tmp_path / "projects"
    (projects_base / "docs-viewer").mkdir(parents=True)
    monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(projects_base))
    external = external_scope_record()
    write_scope_config(tmp_path, external)
    loaded = load_docs_scope_configs(tmp_path)["private"]
    assert {item.location.provider for item in loaded.published.media.values()} == {EXTERNAL_LOCAL_PROVIDER}

    external["published"]["media"]["img"]["location"] = {  # type: ignore[index]
        "provider": REPOSITORY_PROVIDER,
        "path": "site/assets/docs/private/img",
    }
    write_scope_config(tmp_path, external)
    with pytest.raises(ValueError, match="must use provider 'external_local'"):
        load_docs_scope_configs(tmp_path)

    local_r2 = docs_scope_record(
        "private",
        scope_type="local",
        default_doc_id="private",
        media_provider=R2_PROVIDER,
    )
    write_scope_config(tmp_path, local_r2)
    assert load_docs_scope_configs(tmp_path)["private"].published.media["img"].location.provider == R2_PROVIDER


def test_new_scope_defaults_follow_scope_owned_media_policy(tmp_path: Path) -> None:
    public = planned_scope_config_record("research", Path("docs-viewer/source/research"), "/research/", "research", PUBLIC_MODE)
    local = planned_scope_config_record("notes", Path("docs-viewer/source/notes"), "", "notes", LOCAL_COMMITTED_MODE)
    external = planned_scope_config_record(
        "private",
        Path("unused"),
        "",
        "private",
        LOCAL_EXTERNAL_MODE,
        external_data_root=Path("/tmp/external-docs"),
    )

    assert public["published"]["media"]["img"]["location"]["provider"] == R2_PROVIDER  # type: ignore[index]
    assert local["published"]["media"]["img"]["location"] == {  # type: ignore[index]
        "provider": REPOSITORY_PROVIDER,
        "path": "docs-viewer/source/notes/media/img",
    }
    assert external["published"]["media"]["img"]["location"] == {  # type: ignore[index]
        "provider": EXTERNAL_LOCAL_PROVIDER,
        "path": "$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/source/private/media/img",
    }


def test_local_media_route_confines_repo_and_external_scope_assets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_config = scope_config("studio", scope_type="local", media_provider=REPOSITORY_PROVIDER)
    repo_file = tmp_path / "docs-viewer/source/studio/media/img/diagram.png"
    repo_file.parent.mkdir(parents=True)
    repo_file.write_bytes(b"diagram")
    monkeypatch.setattr("docs_media_storage.load_docs_scope_configs", lambda _repo_root: {"studio": repo_config})

    resolved, media_class = local_media_path_from_route(tmp_path, "/docs/media/studio/img/diagram.png")
    assert resolved == repo_file.resolve()
    assert media_class == "img"
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
    with pytest.raises(ValueError, match="Interactive HTML"):
        safe_content_type(html)

    external_root = tmp_path / "external/docs-viewer"
    external_source = external_root / "source/private"
    external_config = scope_config(
        "private",
        scope_type="local_external",
        media_provider=EXTERNAL_LOCAL_PROVIDER,
        source=external_source,
    )
    external_file = external_source / "media/files/notes.pdf"
    external_file.parent.mkdir(parents=True)
    external_file.write_bytes(b"pdf")
    monkeypatch.setattr("docs_media_storage.load_docs_scope_configs", lambda _repo_root: {"private": external_config})

    resolved, media_class = local_media_path_from_route(tmp_path, "/docs/media/private/files/notes.pdf")
    assert resolved == external_file.resolve()
    assert media_class == "files"


def test_configured_local_media_directories_are_materialized(tmp_path: Path) -> None:
    repo_source = tmp_path / "docs-viewer/source/studio"
    repo_source.mkdir(parents=True)
    external_source = tmp_path / "external/docs-viewer/source/notes"
    external_source.mkdir(parents=True)
    configs = {
        "studio": scope_config("studio", scope_type="local", media_provider=REPOSITORY_PROVIDER),
        "notes": scope_config(
            "notes",
            scope_type="local_external",
            media_provider=EXTERNAL_LOCAL_PROVIDER,
            source=external_source,
        ),
        "library": scope_config("library", scope_type="public", media_provider=R2_PROVIDER),
    }

    materialized = ensure_configured_scope_owned_media_directories(tmp_path, configs)
    ensure_configured_scope_owned_media_directories(tmp_path, configs)

    assert set(materialized) == {"notes", "studio"}
    assert all((repo_source / "media" / media_class).is_dir() for media_class in ("files", "img"))
    assert all((repo_source / "media" / media_class / ".gitkeep").is_file() for media_class in ("files", "img"))
    assert all((external_source / "media" / media_class).is_dir() for media_class in ("files", "img"))
    assert not any((external_source / "media" / media_class / ".gitkeep").exists() for media_class in ("files", "img"))
    assert not (tmp_path / "docs-viewer/source/library/media").exists()


def test_external_import_materializes_below_scope_source_media_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    projects_base = tmp_path / "projects"
    external_root = projects_base / "docs-viewer"
    external_root.mkdir(parents=True)
    monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(projects_base))
    write_scope_config(tmp_path, external_scope_record("dlf"))
    workspace_root = projects_base / "data-sharing"
    staging_root = workspace_root / "import-staging"
    staging_root.mkdir(parents=True)
    staged_image = staging_root / "diagram.png"
    staged_image.write_bytes(b"diagram")
    preview = docs_import_media.build_image_summary(staged_image, "dlf", repo_root=tmp_path)
    preview["scope"] = "dlf"

    written = docs_import_media.materialize_inline_raster_media(
        tmp_path,
        staging_root=staging_root,
        workspace_root=workspace_root,
        source_path=staged_image,
        import_preview=preview,
        include_prompt_meta=False,
    )

    target = external_root / "source/dlf/media/img/diagram.png"
    assert target.read_bytes() == b"diagram"
    assert written[0]["media_path"] == "docs/dlf/img/diagram.png"
    assert written[0]["media_link"] == "[[media:docs/dlf/img/diagram.png]]"
    assert str(external_root) not in json.dumps(written)


def test_r2_import_failure_does_not_commit_source_link(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    write_scope_config(tmp_path, public_scope_record())
    source_root = tmp_path / "docs-viewer/source/library"
    source_root.mkdir(parents=True)
    staging_root = tmp_path / "import-staging"
    staging_root.mkdir()
    staged_image = staging_root / "diagram.png"
    staged_image.write_bytes(b"diagram")
    preview = docs_import_media.build_image_summary(staged_image, "library", repo_root=tmp_path)
    preview["scope"] = "library"
    record = ImportContent(
        source_kind="staged-source",
        source_identity="diagram.png",
        record_identity="diagram.png",
        doc_id="diagram",
        title="Diagram",
        content_intent=CONTENT_INTENT_REPLACE,
        content_format=CONTENT_FORMAT_MARKDOWN,
        content=str(preview["markdown_preview"]),
    )
    plan = plan_import_document(
        tmp_path,
        "library",
        record,
        operation=IMPORT_DOCUMENT_CREATE,
        docs=[],
        import_preview=preview,
    )
    context = ImportDocumentMediaContext(staging_root=staging_root, workspace_root=tmp_path, source_path=staged_image)
    monkeypatch.setattr(
        docs_import_media,
        "publish_docs_media_files",
        lambda *_args, **_kwargs: [
            DocsMediaPublishResult(
                scope="library",
                media_class="img",
                filename="diagram.png",
                size=7,
                status="blocked_changed",
                reason="remote object differs",
            )
        ],
    )

    with pytest.raises(RuntimeError, match="publication did not complete"):
        apply_import_document(tmp_path, plan, media_context=context)

    assert not plan.target_path.exists()
