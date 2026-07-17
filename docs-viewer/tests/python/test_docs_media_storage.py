#!/usr/bin/env python3
"""Focused scope, publication, and source-write checks for Docs media storage."""

from __future__ import annotations

import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

import docs_import_media
from docs_import_content import CONTENT_FORMAT_MARKDOWN, CONTENT_INTENT_REPLACE, ImportContent
from docs_import_document import IMPORT_DOCUMENT_CREATE, ImportDocumentMediaContext, apply_import_document, plan_import_document
from docs_media_storage import (
    DocsMediaPublishResult,
    docs_media_file,
    docs_publish_report,
    ensure_configured_scope_owned_media_directories,
    local_media_path_from_route,
    plan_and_publish_docs_media,
    run_docs_staged_media_publish,
    safe_content_type,
)
from docs_scope_config import DocsImportMediaConfig, DocsScopeConfig, load_docs_scope_configs
from docs_scope_manifest import (
    LOCAL_COMMITTED_MODE,
    LOCAL_EXTERNAL_MODE,
    PUBLIC_MODE,
    planned_scope_config_record,
)
from studio.services.media.publish_media_to_r2 import RemoteObject


class FakeR2Client:
    def __init__(self, remote: dict[str, RemoteObject] | None = None) -> None:
        self.remote = remote or {}
        self.puts: list[tuple[str, str]] = []

    def head_object(self, key: str) -> RemoteObject | None:
        return self.remote.get(key)

    def put_object(self, key: str, path: Path, content_type: str) -> None:
        del content_type
        self.puts.append((key, path.name))


def scope_config(
    scope: str,
    *,
    scope_type: str,
    storage_mode: str,
    source: Path | None = None,
    repo_assets_path_prefix: str = "site/assets/docs/example",
    repo_assets_public_path_prefix: str = "/assets/docs/example",
) -> DocsScopeConfig:
    return DocsScopeConfig(
        scope_id=scope,
        scope_type=scope_type,
        source=source or Path(f"docs-viewer/source/{scope}"),
        media_path_prefix=Path(f"docs/{scope}"),
        output=Path(f"docs-viewer/generated/docs/{scope}"),
        search_output=Path(f"docs-viewer/generated/search/{scope}/index.json"),
        publish_output=Path(f"site/assets/data/docs/scopes/{scope}"),
        publish_search_output=Path(f"site/assets/data/search/{scope}/index.json"),
        viewer_base_url=f"/{scope}/" if scope_type == "public" else "/docs/",
        include_scope_param=scope_type != "public",
        default_doc_id=scope,
        non_loadable_doc_ids=(),
        manage_only_tree_root_ids=(),
        allow_unresolved_parent_ids=False,
        import_media_storage=DocsImportMediaConfig(
            storage_mode=storage_mode,
            media_path_prefix=Path(f"docs/{scope}"),
            repo_assets_path_prefix=Path(repo_assets_path_prefix),
            repo_assets_public_path_prefix=repo_assets_public_path_prefix,
        ),
        sub_scopes=(),
    )


def write_scope_config(repo_root: Path, record: dict[str, object]) -> None:
    path = repo_root / "docs-viewer/config/scopes/docs_scopes.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"schema_version": "docs_scopes_v1", "scopes": [record]}) + "\n",
        encoding="utf-8",
    )


def public_scope_record(*, storage_mode: str = "r2_upload") -> dict[str, object]:
    return {
        "scope_id": "library",
        "scope_type": "public",
        "source": "docs-viewer/source/library",
        "media_path_prefix": "docs/library",
        "output": "docs-viewer/generated/docs/library",
        "search_output": "docs-viewer/generated/search/library/index.json",
        "publish_output": "site/assets/data/docs/scopes/library",
        "publish_search_output": "site/assets/data/search/library/index.json",
        "viewer_base_url": "/library/",
        "include_scope_param": False,
        "default_doc_id": "library",
        "import_media_storage": {"storage_mode": storage_mode},
    }


def external_scope_record(scope: str = "private") -> dict[str, object]:
    return {
        "scope_id": scope,
        "scope_type": "local_external",
        "external_data_root": "$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer",
        "source": f"$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/source/{scope}",
        "media_path_prefix": f"docs/{scope}",
        "output": f"$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/generated/docs/{scope}",
        "search_output": f"$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/generated/search/{scope}/index.json",
        "viewer_base_url": "/docs/",
        "include_scope_param": True,
        "default_doc_id": scope,
    }


def test_docs_upload_preflights_complete_set_and_keeps_remote_details_private(tmp_path: Path) -> None:
    config = scope_config("library", scope_type="public", storage_mode="r2_upload")
    first = tmp_path / "first.png"
    second = tmp_path / "second.png"
    first.write_bytes(b"first")
    second.write_bytes(b"second")
    files = [
        docs_media_file(config, media_class="img", local_path=path, source_root=tmp_path)
        for path in (first, second)
    ]
    client = FakeR2Client(
        {"docs/library/img/first.png": RemoteObject(size=99, etag='"different"')}
    )

    results = plan_and_publish_docs_media(files, client=client, write=True, force=False)
    report = docs_publish_report(scope="library", results=results, write=True, force=False)

    assert [result.status for result in results] == ["blocked_changed", "not_attempted"]
    assert client.puts == []
    assert report["counts"] == {"blocked_changed": 1, "not_attempted": 1}
    serialized = json.dumps(report)
    assert "docs/library" not in serialized
    assert "md5" not in serialized
    assert "etag" not in serialized.lower()


def test_docs_upload_writes_missing_objects_after_complete_preflight(tmp_path: Path) -> None:
    config = scope_config("library", scope_type="public", storage_mode="r2_upload")
    image = tmp_path / "diagram.png"
    attachment = tmp_path / "notes.pdf"
    image.write_bytes(b"image")
    attachment.write_bytes(b"pdf")
    files = [
        docs_media_file(config, media_class="img", local_path=image, source_root=tmp_path),
        docs_media_file(config, media_class="files", local_path=attachment, source_root=tmp_path),
    ]
    client = FakeR2Client()

    results = plan_and_publish_docs_media(files, client=client, write=True, force=False)

    assert [result.status for result in results] == ["uploaded", "uploaded"]
    assert client.puts == [
        ("docs/library/img/diagram.png", "diagram.png"),
        ("docs/library/files/notes.pdf", "notes.pdf"),
    ]


def test_exact_scope_staged_file_runner_uses_safe_docs_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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
    assert report["objects"] == [
        {
            "scope": "library",
            "media_class": "img",
            "filename": "diagram.png",
            "size": 7,
            "status": "would_upload",
            "reason": "dry-run",
        }
    ]


def test_scope_config_enforces_external_and_r2_storage_boundaries(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    projects_base = tmp_path / "projects"
    (projects_base / "docs-viewer").mkdir(parents=True)
    monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(projects_base))
    external = external_scope_record()
    write_scope_config(tmp_path, external)

    assert load_docs_scope_configs(tmp_path)["private"].import_media_storage.storage_mode == "external_assets"

    external["import_media_storage"] = {
        "storage_mode": "external_assets",
        "repo_assets_path_prefix": "site/assets/docs/private",
    }
    write_scope_config(tmp_path, external)
    with pytest.raises(ValueError, match="must not configure repo asset destinations"):
        load_docs_scope_configs(tmp_path)


def test_new_scope_defaults_follow_scope_owned_media_policy(tmp_path: Path) -> None:
    public = planned_scope_config_record(
        "research",
        Path("docs-viewer/source/research"),
        "/research/",
        "research",
        PUBLIC_MODE,
    )
    local = planned_scope_config_record(
        "notes",
        Path("docs-viewer/source/notes"),
        "",
        "notes",
        LOCAL_COMMITTED_MODE,
    )
    external = planned_scope_config_record(
        "private",
        Path("unused"),
        "",
        "private",
        LOCAL_EXTERNAL_MODE,
        external_data_root=Path("/tmp/external-docs"),
    )

    assert public["import_media_storage"] == {"storage_mode": "r2_upload"}
    assert local["import_media_storage"] == {
        "storage_mode": "repo_assets",
        "repo_assets_path_prefix": "docs-viewer/source/notes/media",
        "repo_assets_public_path_prefix": "/docs/media/notes",
    }
    assert external["import_media_storage"] == {"storage_mode": "external_assets"}

    local_r2 = public_scope_record()
    local_r2["scope_type"] = "local"
    local_r2["viewer_base_url"] = "/docs/"
    local_r2["include_scope_param"] = True
    local_r2.pop("publish_output")
    local_r2.pop("publish_search_output")
    write_scope_config(tmp_path, local_r2)
    with pytest.raises(ValueError, match="only valid for public read-only scopes"):
        load_docs_scope_configs(tmp_path)


def test_local_media_route_confines_repo_and_external_scope_assets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_config = scope_config(
        "studio",
        scope_type="local",
        storage_mode="repo_assets",
        repo_assets_path_prefix="docs-viewer/source/studio/media",
        repo_assets_public_path_prefix="/docs/media/studio",
    )
    repo_file = tmp_path / "docs-viewer/source/studio/media/img/diagram.png"
    repo_file.parent.mkdir(parents=True)
    repo_file.write_bytes(b"diagram")
    monkeypatch.setattr(
        "docs_media_storage.load_docs_scope_configs",
        lambda _repo_root: {"studio": repo_config},
    )

    resolved, media_class = local_media_path_from_route(tmp_path, "/docs/media/studio/img/diagram.png")

    assert resolved == repo_file.resolve()
    assert media_class == "img"
    with pytest.raises(ValueError, match="Invalid Docs media route"):
        local_media_path_from_route(tmp_path, "/docs/media/studio/img/nested/diagram.png")
    if hasattr(os, "symlink"):
        outside = tmp_path / "outside.png"
        outside.write_bytes(b"outside")
        os.symlink(outside, repo_file.parent / "escaped.png")
        with pytest.raises(FileNotFoundError, match="Docs media file not found"):
            local_media_path_from_route(tmp_path, "/docs/media/studio/img/escaped.png")
        outside_root = tmp_path.parent / f"{tmp_path.name}-outside-media"
        outside_root.mkdir()
        (outside_root / "img").mkdir()
        (outside_root / "img/diagram.png").write_bytes(b"outside")
        os.symlink(outside_root, tmp_path / "linked-media")
        escaped_root_config = scope_config(
            "studio",
            scope_type="local",
            storage_mode="repo_assets",
            repo_assets_path_prefix="linked-media",
            repo_assets_public_path_prefix="/docs/media/studio",
        )
        monkeypatch.setattr(
            "docs_media_storage.load_docs_scope_configs",
            lambda _repo_root: {"studio": escaped_root_config},
        )
        with pytest.raises(ValueError, match="must be the scope source media directory"):
            local_media_path_from_route(tmp_path, "/docs/media/studio/img/diagram.png")
    html = tmp_path / "widget.html"
    html.write_text("<script>alert(1)</script>", encoding="utf-8")
    with pytest.raises(ValueError, match="Interactive HTML"):
        safe_content_type(html)

    external_root = tmp_path / "external/docs-viewer"
    external_config = scope_config(
        "private",
        scope_type="local_external",
        storage_mode="external_assets",
        source=external_root / "source/private",
    )
    external_file = external_root / "source/private/media/files/notes.pdf"
    external_file.parent.mkdir(parents=True)
    external_file.write_bytes(b"pdf")
    monkeypatch.setattr(
        "docs_media_storage.load_docs_scope_configs",
        lambda _repo_root: {"private": external_config},
    )
    monkeypatch.setattr("docs_media_storage.resolve_external_data_root", lambda: external_root)

    resolved, media_class = local_media_path_from_route(tmp_path, "/docs/media/private/files/notes.pdf")

    assert resolved == external_file.resolve()
    assert media_class == "files"


def test_configured_local_media_directories_are_materialized(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_source = tmp_path / "docs-viewer/source/studio"
    repo_source.mkdir(parents=True)
    external_root = tmp_path / "external/docs-viewer"
    external_source = external_root / "source/notes"
    external_source.mkdir(parents=True)
    configs = {
        "studio": scope_config(
            "studio",
            scope_type="local",
            storage_mode="repo_assets",
            repo_assets_path_prefix="docs-viewer/source/studio/media",
            repo_assets_public_path_prefix="/docs/media/studio",
        ),
        "notes": scope_config(
            "notes",
            scope_type="local_external",
            storage_mode="external_assets",
            source=external_source,
        ),
        "library": scope_config(
            "library",
            scope_type="public",
            storage_mode="r2_upload",
        ),
    }
    monkeypatch.setattr("docs_media_storage.resolve_external_data_root", lambda: external_root)

    materialized = ensure_configured_scope_owned_media_directories(tmp_path, configs)
    ensure_configured_scope_owned_media_directories(tmp_path, configs)

    assert set(materialized) == {"notes", "studio"}
    assert all((repo_source / "media" / media_class).is_dir() for media_class in ("files", "img"))
    assert all(
        (repo_source / "media" / media_class / ".gitkeep").is_file()
        for media_class in ("files", "img")
    )
    assert all((external_source / "media" / media_class).is_dir() for media_class in ("files", "img"))
    assert not any(
        (external_source / "media" / media_class / ".gitkeep").exists()
        for media_class in ("files", "img")
    )
    assert not (tmp_path / "docs-viewer/source/library/media").exists()
    if hasattr(os, "symlink"):
        repo_img = repo_source / "media/img"
        (repo_img / ".gitkeep").unlink()
        repo_img.rmdir()
        outside = tmp_path / "outside-img"
        outside.mkdir()
        os.symlink(outside, repo_img)
        with pytest.raises(ValueError, match="must not be a symlink"):
            ensure_configured_scope_owned_media_directories(tmp_path, configs)


def test_external_import_materializes_below_scope_source_media_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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
    assert written[0]["media_path"] == "media/img/diagram.png"
    assert written[0]["media_link"] == "/docs/media/dlf/img/diagram.png"
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
    context = ImportDocumentMediaContext(
        staging_root=staging_root,
        workspace_root=tmp_path,
        source_path=staged_image,
    )
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
