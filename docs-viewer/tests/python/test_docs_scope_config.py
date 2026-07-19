#!/usr/bin/env python3
"""Docs scope config validation tests."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from docs_management_test_support import docs_scope_config, make_repo, write_docs_scope_config, write_json
from repo_factory import docs_scope_record, docs_sub_scope_record


def write_scope_record(repo_root: Path, record: dict[str, object]) -> None:
    write_json(
        repo_root / "docs-viewer/config/scopes/docs_scopes.json",
        {"schema_version": "docs_scopes_v3", "scopes": [record]},
    )


def sub_scope_record(
    scope_id: str,
    sub_scope: str,
    *,
    source_path: str | None = None,
    public_docs_path: str | None = None,
) -> dict[str, object]:
    record = docs_sub_scope_record(
        scope_id,
        sub_scope,
        title=sub_scope.title(),
        scope_type="public",
        public_docs_path=public_docs_path,
    )
    if source_path is not None:
        record["source"] = {
            "location": {"provider": "repository", "path": source_path},
        }
    return record


def test_docs_scope_config_rejects_repeated_published_search_role() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        record = docs_scope_record("studio", default_doc_id="child")
        published = record["published"]
        assert isinstance(published, dict)
        published["search"] = {
            "location": {
                "provider": "repository",
                "path": "docs-viewer/scopes/studio/published/search/index.json",
            }
        }
        write_scope_record(repo_root, record)
        try:
            docs_scope_config.load_docs_scope_configs(repo_root)
        except ValueError as exc:
            assert "must not repeat scope-root paths: search" in str(exc)
        else:
            raise AssertionError("Expected docs scope config to reject a repeated published search role")


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
                assert f"must not repeat scope-root paths: {field}" in str(exc)
            else:
                raise AssertionError(f"Expected docs scope config to reject source {field}=.")


def test_docs_scope_config_rejects_local_published_payloads_in_public_assets() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        record = docs_scope_record("studio", default_doc_id="child")
        record["scope_root"]["path"] = "site/assets/data/docs/scopes/studio"  # type: ignore[index]
        write_scope_record(repo_root, record)
        try:
            docs_scope_config.load_docs_scope_configs(repo_root)
        except ValueError as exc:
            assert "scopes[0].scope_root.path must be docs-viewer/scopes/studio" in str(exc)
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

    assert docs_scope_config.published_documents_path(config).as_posix() == "docs-viewer/scopes/research/published/documents"
    assert docs_scope_config.published_search_path(config).as_posix() == "docs-viewer/scopes/research/published/search/index.json"
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
        "docs-viewer/scopes/research/source/sub-scopes/tags/documents"
    )
    assert docs_scope_config.published_documents_path(sub_scope).as_posix() == (
        "docs-viewer/scopes/research/published/documents/sub-scopes/tags"
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
            sub_scope_record("studio", "tags"),
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


def test_docs_scope_config_rejects_repeated_sub_scope_paths() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_docs_scope_config(repo_root)
        config_path = repo_root / "docs-viewer/config/scopes/docs_scopes.json"
        payload = json.loads(config_path.read_text(encoding="utf-8"))
        item = sub_scope_record("studio", "tags", source_path="docs-viewer/scopes/tags/source")
        item["public_projection"] = None
        payload["scopes"][0]["sub_scopes"] = [item]
        write_json(config_path, payload)
        try:
            docs_scope_config.load_docs_scope_configs(repo_root)
        except ValueError as exc:
            assert "sub-scope studio/tags" in str(exc)
            assert "derives source and published paths from its parent scope_root" in str(exc)
        else:
            raise AssertionError("Expected repeated sub_scope source paths to be rejected")


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


def test_docs_scope_config_accepts_explicit_mermaid_to_svg_build_contract() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        record = docs_scope_record("studio", default_doc_id="child")
        record["source"]["build_media"] = {  # type: ignore[index]
            "mermaid": {
                "path": "media/mermaid",
                "producer": "mermaid",
                "publishes_to": "svg",
            }
        }
        record["published"]["media"]["svg"]["build_inputs"] = ["mermaid"]  # type: ignore[index]
        write_scope_record(repo_root, record)

        config = docs_scope_config.load_docs_scope_configs(repo_root)["studio"]

    assert config.source.build_media["mermaid"].path == Path("media/mermaid")
    assert config.published.media["svg"].build_inputs == ("mermaid",)


def test_docs_scope_config_rejects_unhandled_media_types() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        record = docs_scope_record("studio", default_doc_id="child")
        record["published"]["media"]["video"] = {  # type: ignore[index]
            "reference_prefix": "docs/studio/video",
            "location": {
                "provider": "repository",
                "path": "docs-viewer/scopes/studio/published/documents/media/video",
            },
            "served_path_prefix": "/docs/media/studio/video",
            "build_inputs": [],
        }
        write_scope_record(repo_root, record)

        try:
            docs_scope_config.load_docs_scope_configs(repo_root)
        except ValueError as exc:
            assert "unsupported published media type" in str(exc)
        else:
            raise AssertionError("Expected unhandled published media type to require an explicit contract")


def test_docs_scope_policy_rejects_competing_producers_for_one_published_type() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        record = docs_scope_record("studio", default_doc_id="child")
        write_scope_record(repo_root, record)
        config = docs_scope_config.load_docs_scope_configs(repo_root)["studio"]

    builds = {
        "mermaid": docs_scope_config.DocsBuildMediaConfig(
            path=Path("media/mermaid"),
            producer="first",
            publishes_to="img",
        ),
        "other": docs_scope_config.DocsBuildMediaConfig(
            path=Path("media/other"),
            producer="second",
            publishes_to="img",
        ),
    }
    media = dict(config.published.media)
    media["img"] = replace(media["img"], build_inputs=("mermaid", "other"))
    competing = replace(
        config,
        source=replace(config.source, build_media=builds),
        published=replace(config.published, media=media),
    )

    try:
        docs_scope_config.validate_scope_policy(competing, field="scopes[0]")
    except ValueError as exc:
        assert "compete for published media 'img'" in str(exc)
    else:
        raise AssertionError("Expected competing media producers to be rejected")
