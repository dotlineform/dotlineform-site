#!/usr/bin/env python3
"""Docs scope config validation tests."""

from __future__ import annotations

import json
from pathlib import Path

from docs_management_test_support import docs_scope_config, make_repo, write_docs_scope_config, write_json
from repo_factory import docs_scope_record


def write_scope_record(repo_root: Path, record: dict[str, object]) -> None:
    write_json(
        repo_root / "docs-viewer/config/scopes/docs_scopes.json",
        {"schema_version": "docs_scopes_v2", "scopes": [record]},
    )


def sub_scope_record(
    scope_id: str,
    sub_scope: str,
    *,
    source_path: str | None = None,
    public_docs_path: str | None = None,
) -> dict[str, object]:
    return {
        "sub_scope": sub_scope,
        "title": sub_scope.title(),
        "source": {
            "location": {
                "provider": "repository",
                "path": source_path or f"docs-viewer/source/{scope_id}/sub-scopes/{sub_scope}",
            },
            "documents_path": "documents",
            "build_media": {},
            "sub_scopes_path": "sub-scopes",
        },
        "published": {
            "documents": {
                "location": {
                    "provider": "repository",
                    "path": f"docs-viewer/published/docs/{scope_id}/sub-scopes/{sub_scope}",
                }
            },
            "search": {
                "location": {
                    "provider": "repository",
                    "path": f"docs-viewer/published/search/{scope_id}/sub-scopes/{sub_scope}/index.json",
                }
            },
            "media": {},
        },
        "public_projection": {
            "documents": {
                "location": {
                    "provider": "repository",
                    "path": public_docs_path or f"site/assets/data/docs/scopes/{scope_id}/{sub_scope}",
                }
            },
            "search": None,
        },
    }


def test_docs_scope_config_requires_published_search_role() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        record = docs_scope_record("studio", default_doc_id="child")
        published = record["published"]
        assert isinstance(published, dict)
        published.pop("search")
        write_scope_record(repo_root, record)
        try:
            docs_scope_config.load_docs_scope_configs(repo_root)
        except ValueError as exc:
            assert "scopes[0].published.search" in str(exc)
        else:
            raise AssertionError("Expected docs scope config to require a published search role")


def test_docs_scope_config_requires_named_document_and_sub_scope_children() -> None:
    for field in ("documents_path", "sub_scopes_path"):
        with make_repo() as temp_path:
            repo_root = Path(temp_path)
            record = docs_scope_record("studio", default_doc_id="child")
            record["source"][field] = "."  # type: ignore[index]
            write_scope_record(repo_root, record)
            try:
                docs_scope_config.load_docs_scope_configs(repo_root)
            except ValueError as exc:
                expected = "documents" if field == "documents_path" else "sub-scopes"
                assert f"{field} must be {expected}" in str(exc)
            else:
                raise AssertionError(f"Expected docs scope config to reject source {field}=.")


def test_docs_scope_config_rejects_local_published_payloads_in_public_assets() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        record = docs_scope_record("studio", default_doc_id="child")
        record["published"]["documents"]["location"]["path"] = "site/assets/data/docs/scopes/studio"  # type: ignore[index]
        write_scope_record(repo_root, record)
        try:
            docs_scope_config.load_docs_scope_configs(repo_root)
        except ValueError as exc:
            assert "scopes[0].published.documents" in str(exc)
            assert "docs-viewer/published/docs" in str(exc)
        else:
            raise AssertionError("Expected local scope config to reject public asset payload roots")


def test_docs_scope_config_accepts_separate_public_projection() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_scope_record(
            repo_root,
            docs_scope_record(
                "research",
                scope_type="public",
                viewer_base_url="/research/",
                include_scope_param=False,
                default_doc_id="research",
            ),
        )
        config = docs_scope_config.load_docs_scope_configs(repo_root)["research"]

    assert docs_scope_config.published_documents_path(config).as_posix() == "docs-viewer/published/docs/research"
    assert docs_scope_config.published_search_path(config).as_posix() == "docs-viewer/published/search/research/index.json"
    assert docs_scope_config.public_documents_path(config).as_posix() == "site/assets/data/docs/scopes/research"
    assert docs_scope_config.public_search_path(config).as_posix() == "site/assets/data/search/research/index.json"


def test_docs_scope_config_accepts_nested_sub_scopes() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        record = docs_scope_record(
            "research",
            scope_type="public",
            viewer_base_url="/research/",
            include_scope_param=False,
            default_doc_id="research",
            sub_scopes=[sub_scope_record("research", "tags")],
        )
        write_scope_record(repo_root, record)
        config = docs_scope_config.load_docs_scope_configs(repo_root)["research"]

    sub_scope = config.sub_scopes[0]
    assert sub_scope.sub_scope == "tags"
    assert docs_scope_config.document_source_path(sub_scope).as_posix() == (
        "docs-viewer/source/research/sub-scopes/tags/documents"
    )
    assert docs_scope_config.published_documents_path(sub_scope).as_posix() == (
        "docs-viewer/published/docs/research/sub-scopes/tags"
    )
    assert docs_scope_config.public_documents_path(sub_scope).as_posix() == "site/assets/data/docs/scopes/research/tags"


def test_docs_scope_config_rejects_duplicate_sub_scopes() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_docs_scope_config(repo_root)
        config_path = repo_root / "docs-viewer/config/scopes/docs_scopes.json"
        payload = json.loads(config_path.read_text(encoding="utf-8"))
        payload["scopes"][0]["sub_scopes"] = [
            sub_scope_record("studio", "tags"),
            sub_scope_record("studio", "tags", source_path="docs-viewer/source/studio/sub-scopes/more-tags"),
        ]
        for item in payload["scopes"][0]["sub_scopes"]:
            item["public_projection"] = None
        write_json(config_path, payload)
        try:
            docs_scope_config.load_docs_scope_configs(repo_root)
        except ValueError as exc:
            assert "duplicated in scope 'studio'" in str(exc)
        else:
            raise AssertionError("Expected duplicate sub_scope ids to be rejected")


def test_docs_scope_config_rejects_sub_scope_paths_outside_parent() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_docs_scope_config(repo_root)
        config_path = repo_root / "docs-viewer/config/scopes/docs_scopes.json"
        payload = json.loads(config_path.read_text(encoding="utf-8"))
        item = sub_scope_record("studio", "tags", source_path="docs-viewer/source/tags")
        item["public_projection"] = None
        payload["scopes"][0]["sub_scopes"] = [item]
        write_json(config_path, payload)
        try:
            docs_scope_config.load_docs_scope_configs(repo_root)
        except ValueError as exc:
            assert "sub-scope studio/tags" in str(exc)
            assert "source must be docs-viewer/source/studio/sub-scopes/tags" in str(exc)
        else:
            raise AssertionError("Expected sub_scope source paths outside the parent source to be rejected")


def test_docs_scope_config_rejects_public_sub_scope_projection_outside_parent() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        record = docs_scope_record(
            "research",
            scope_type="public",
            viewer_base_url="/research/",
            include_scope_param=False,
            default_doc_id="research",
            sub_scopes=[
                sub_scope_record(
                    "research",
                    "tags",
                    public_docs_path="site/assets/data/docs/scopes/elsewhere/tags",
                )
            ],
        )
        write_scope_record(repo_root, record)
        try:
            docs_scope_config.load_docs_scope_configs(repo_root)
        except ValueError as exc:
            assert "sub-scope research/tags" in str(exc)
            assert "public documents must be site/assets/data/docs/scopes/research/tags" in str(exc)
        else:
            raise AssertionError("Expected public sub_scope projection outside the parent root to be rejected")
