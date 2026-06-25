#!/usr/bin/env python3
"""Docs scope config validation tests."""

from __future__ import annotations

import json
from pathlib import Path

from docs_management_test_support import docs_scope_config, make_repo, write_docs_scope_config, write_json

def test_docs_scope_config_requires_search_output() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_json(
            repo_root / "docs-viewer/config/scopes/docs_scopes.json",
            {
                "schema_version": "docs_scopes_v1",
                "scopes": [
                    {
                        "scope_id": "studio",
                        "source": "docs-viewer/source/studio",
                        "media_path_prefix": "docs/studio",
                        "output": "docs-viewer/generated/docs/studio",
                        "viewer_base_url": "/docs/",
                        "include_scope_param": True,
                        "default_doc_id": "child",
                    }
                ],
            },
        )
        try:
            docs_scope_config.load_docs_scope_configs(repo_root)
        except ValueError as exc:
            assert "scopes[0].search_output" in str(exc)
        else:
            raise AssertionError("Expected docs scope config to require search_output")

def test_docs_scope_config_rejects_local_assets_outputs() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_json(
            repo_root / "docs-viewer/config/scopes/docs_scopes.json",
            {
                "schema_version": "docs_scopes_v1",
                "scopes": [
                    {
                        "scope_id": "studio",
                        "source": "docs-viewer/source/studio",
                        "media_path_prefix": "docs/studio",
                        "output": "site/assets/data/docs/scopes/studio",
                        "search_output": "site/assets/data/search/studio/index.json",
                        "viewer_base_url": "/docs/",
                        "include_scope_param": True,
                        "default_doc_id": "child",
                    }
                ],
            },
        )
        try:
            docs_scope_config.load_docs_scope_configs(repo_root)
        except ValueError as exc:
            assert "local scope 'studio'" in str(exc)
            assert "site/assets/data/docs/scopes" in str(exc)
        else:
            raise AssertionError("Expected local scope config to reject public generated asset roots")

def test_docs_scope_config_requires_public_readonly_publish_outputs() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_json(
            repo_root / "docs-viewer/config/scopes/docs_scopes.json",
            {
                "schema_version": "docs_scopes_v1",
                "scopes": [
                    {
                        "scope_id": "research",
                        "source": "docs-viewer/source/research",
                        "media_path_prefix": "docs/research",
                        "output": "docs-viewer/generated/docs/research",
                        "search_output": "docs-viewer/generated/search/research/index.json",
                        "publish_output": "site/assets/data/docs/scopes/research",
                        "publish_search_output": "site/assets/data/search/research/index.json",
                        "viewer_base_url": "/research/",
                        "include_scope_param": False,
                        "default_doc_id": "research",
                    }
                ],
            },
        )
        configs = docs_scope_config.load_docs_scope_configs(repo_root)

    assert configs["research"].output.as_posix() == "docs-viewer/generated/docs/research"
    assert configs["research"].search_output.as_posix() == "docs-viewer/generated/search/research/index.json"
    assert configs["research"].publish_output.as_posix() == "site/assets/data/docs/scopes/research"
    assert configs["research"].publish_search_output.as_posix() == "site/assets/data/search/research/index.json"

def test_docs_scope_config_accepts_nested_sub_scopes() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_json(
            repo_root / "docs-viewer/config/scopes/docs_scopes.json",
            {
                "schema_version": "docs_scopes_v1",
                "scopes": [
                    {
                        "scope_id": "research",
                        "scope_type": "public",
                        "source": "docs-viewer/source/research",
                        "media_path_prefix": "docs/research",
                        "output": "docs-viewer/generated/docs/research",
                        "search_output": "docs-viewer/generated/search/research/index.json",
                        "publish_output": "site/assets/data/docs/scopes/research",
                        "publish_search_output": "site/assets/data/search/research/index.json",
                        "viewer_base_url": "/research/",
                        "include_scope_param": False,
                        "default_doc_id": "research",
                        "sub_scopes": [
                            {
                                "sub_scope": "tags",
                                "source": "docs-viewer/source/research/tags",
                                "output": "docs-viewer/generated/docs/research/tags",
                                "publish_output": "site/assets/data/docs/scopes/research/tags",
                            }
                        ],
                    }
                ],
            },
        )
        config = docs_scope_config.load_docs_scope_configs(repo_root)["research"]

    assert config.sub_scopes[0].sub_scope == "tags"
    assert config.sub_scopes[0].source.as_posix() == "docs-viewer/source/research/tags"
    assert config.sub_scopes[0].output.as_posix() == "docs-viewer/generated/docs/research/tags"
    assert config.sub_scopes[0].publish_output.as_posix() == "site/assets/data/docs/scopes/research/tags"

def test_docs_scope_config_rejects_duplicate_sub_scopes() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_docs_scope_config(repo_root)
        config_path = repo_root / "docs-viewer/config/scopes/docs_scopes.json"
        payload = json.loads(config_path.read_text(encoding="utf-8"))
        payload["scopes"][0]["sub_scopes"] = [
            {
                "sub_scope": "tags",
                "source": "docs-viewer/source/studio/tags",
                "output": "docs-viewer/generated/docs/studio/tags",
            },
            {
                "sub_scope": "tags",
                "source": "docs-viewer/source/studio/more-tags",
                "output": "docs-viewer/generated/docs/studio/more-tags",
            },
        ]
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
        payload["scopes"][0]["sub_scopes"] = [
            {
                "sub_scope": "tags",
                "source": "docs-viewer/source/tags",
                "output": "docs-viewer/generated/docs/studio/tags",
            }
        ]
        write_json(config_path, payload)
        try:
            docs_scope_config.load_docs_scope_configs(repo_root)
        except ValueError as exc:
            assert "sub-scope studio/tags" in str(exc)
            assert "must be under scopes[0].source" in str(exc)
        else:
            raise AssertionError("Expected sub_scope source paths outside the parent source to be rejected")

def test_docs_scope_config_rejects_public_sub_scope_publish_paths_outside_parent() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_json(
            repo_root / "docs-viewer/config/scopes/docs_scopes.json",
            {
                "schema_version": "docs_scopes_v1",
                "scopes": [
                    {
                        "scope_id": "research",
                        "scope_type": "public",
                        "source": "docs-viewer/source/research",
                        "media_path_prefix": "docs/research",
                        "output": "docs-viewer/generated/docs/research",
                        "search_output": "docs-viewer/generated/search/research/index.json",
                        "publish_output": "site/assets/data/docs/scopes/research",
                        "publish_search_output": "site/assets/data/search/research/index.json",
                        "viewer_base_url": "/research/",
                        "include_scope_param": False,
                        "default_doc_id": "research",
                        "sub_scopes": [
                            {
                                "sub_scope": "tags",
                                "source": "docs-viewer/source/research/tags",
                                "output": "docs-viewer/generated/docs/research/tags",
                                "publish_output": "site/assets/data/docs/tags",
                            }
                        ],
                    }
                ],
            },
        )
        try:
            docs_scope_config.load_docs_scope_configs(repo_root)
        except ValueError as exc:
            assert "sub-scope research/tags" in str(exc)
            assert "must be under scopes[0].publish_output" in str(exc)
        else:
            raise AssertionError("Expected public sub_scope publish paths outside the parent publish root to be rejected")
