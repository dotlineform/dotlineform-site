#!/usr/bin/env python3
"""Focused checks for Docs Viewer public publish gate."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
if str(DOCS_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(DOCS_SERVICES_DIR))

import docs_publish_gate  # noqa: E402


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_scope_config(root: Path) -> None:
    write_json(
        root / "docs-viewer/config/scopes/docs_scopes.json",
        {
            "schema_version": "docs_scopes_v1",
            "scopes": [
                {
                    "scope_id": "studio",
                    "scope_type": "local",
                    "source": "docs-viewer/source/studio",
                    "media_path_prefix": "docs/studio",
                    "output": "docs-viewer/generated/docs/studio",
                    "search_output": "docs-viewer/generated/search/studio/index.json",
                    "viewer_base_url": "/docs/",
                    "include_scope_param": True,
                    "default_doc_id": "studio",
                },
                {
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
                },
            ],
        },
    )


def prepare_publish_repo(root: Path) -> None:
    write_scope_config(root)
    write_json(
        root / "docs-viewer/generated/docs/library/index-tree.json",
        {
            "schema": "docs_index_tree_v1",
            "viewer_options": {"manage_only_tree_root_ids": ["manage-root"]},
            "docs": [
                {
                    "doc_id": "library",
                    "title": "Library",
                    "content_url": "/assets/data/docs/scopes/library/by-id/library.json",
                    "children": [
                        {
                            "doc_id": "hidden",
                            "title": "Hidden",
                            "content_url": "/assets/data/docs/scopes/library/by-id/hidden.json",
                            "viewable": False,
                            "children": [
                                {
                                    "doc_id": "hidden-child",
                                    "title": "Hidden Child",
                                    "content_url": "/assets/data/docs/scopes/library/by-id/hidden-child.json",
                                }
                            ],
                        }
                    ],
                },
                {
                    "doc_id": "manage-root",
                    "title": "Manage Root",
                    "content_url": "/assets/data/docs/scopes/library/by-id/manage-root.json",
                },
            ],
        },
    )
    write_json(
        root / "docs-viewer/generated/docs/library/recently-added.json",
        {
            "schema": "docs_recently_added_v1",
            "docs": [
                {"doc_id": "hidden", "title": "Hidden", "content_url": "/assets/data/docs/scopes/library/by-id/hidden.json", "added_date": "2026-06-02"},
                {"doc_id": "library", "title": "Library", "content_url": "/assets/data/docs/scopes/library/by-id/library.json", "added_date": "2026-06-01"},
            ],
        },
    )
    write_json(root / "docs-viewer/generated/docs/library/by-id/library.json", {"title": "Library"})
    write_json(root / "docs-viewer/generated/docs/library/by-id/hidden.json", {"title": "Hidden"})
    write_json(root / "docs-viewer/generated/docs/library/by-id/hidden-child.json", {"title": "Hidden Child"})
    write_json(root / "docs-viewer/generated/docs/library/by-id/manage-root.json", {"title": "Manage Root"})
    write_json(
        root / "docs-viewer/generated/docs/library/references/index.json",
        {
            "header": {"schema": "docs_semantic_references_index_v1", "scope": "library", "count": 1, "target_count": 1},
            "targets": [],
        },
    )
    write_json(
        root / "docs-viewer/generated/docs/library/references/by-doc/hidden.json",
        {
            "header": {"schema": "docs_semantic_references_by_doc_v1", "scope": "library", "doc_id": "hidden", "count": 1},
            "references": [{"source_doc_id": "hidden", "target_kind": "work", "target_id": "00638"}],
        },
    )
    write_json(
        root / "docs-viewer/generated/docs/library/references/by-target/work/00638.json",
        {
            "header": {"schema": "docs_semantic_references_by_target_v1", "scope": "library", "count": 1},
            "target_key": "work:00638",
            "target_kind": "work",
            "target_id": "00638",
            "target_href": "/works/?work=00638",
            "target_title": "3 symbols",
            "target_status": "published",
            "count": 1,
            "references": [{"source_doc_id": "hidden", "source_title": "Hidden"}],
        },
    )
    write_json(root / "docs-viewer/generated/search/library/index.json", {"entries": [{"id": "library"}]})
    write_json(root / "site/assets/data/docs/scopes/library/index-tree.json", {"docs": []})
    write_json(root / "site/assets/data/docs/scopes/library/by-id/stale.json", {"title": "Stale"})
    write_json(root / "site/assets/data/docs/scopes/library/by-id/hidden.json", {"title": "Old Hidden"})
    write_json(root / "site/assets/data/search/library/index.json", {"entries": []})


def test_publish_confirm_reports_changes_and_apply_syncs_stale_files() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        prepare_publish_repo(repo_root)

        preview = docs_publish_gate.publish_confirm(repo_root, {"scope": "library"})
        applied = docs_publish_gate.publish_apply(repo_root, {"scope": "library", "confirm": True})

        assert preview["operation"] == "confirm"
        assert preview["changed_count"] >= 3
        assert "site/assets/data/docs/scopes/library/by-id/stale.json" in preview["docs"]["removed"]
        assert "site/assets/data/docs/scopes/library/by-id/hidden.json" in preview["docs"]["removed"]
        assert applied["operation"] == "apply"
        public_tree = json.loads((repo_root / "site/assets/data/docs/scopes/library/index-tree.json").read_text(encoding="utf-8"))
        recent = json.loads((repo_root / "site/assets/data/docs/scopes/library/recently-added.json").read_text(encoding="utf-8"))
        references = json.loads((repo_root / "site/assets/data/docs/scopes/library/references/index.json").read_text(encoding="utf-8"))

        assert public_tree["docs"][0]["doc_id"] == "library"
        assert "children" not in public_tree["docs"][0]
        assert recent["docs"][0]["doc_id"] == "library"
        assert references["header"]["count"] == 0
        assert (repo_root / "site/assets/data/docs/scopes/library/by-id/library.json").exists()
        assert not (repo_root / "site/assets/data/docs/scopes/library/by-id/hidden.json").exists()
        assert not (repo_root / "site/assets/data/docs/scopes/library/by-id/hidden-child.json").exists()
        assert not (repo_root / "site/assets/data/docs/scopes/library/by-id/manage-root.json").exists()
        assert not (repo_root / "site/assets/data/docs/scopes/library/references/by-doc/hidden.json").exists()
        assert not (repo_root / "site/assets/data/docs/scopes/library/references/by-target/work/00638.json").exists()
        assert not (repo_root / "site/assets/data/docs/scopes/library/by-id/stale.json").exists()
        assert json.loads((repo_root / "site/assets/data/search/library/index.json").read_text(encoding="utf-8"))["entries"][0]["id"] == "library"


def test_publish_apply_requires_confirmation() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        prepare_publish_repo(repo_root)

        try:
            docs_publish_gate.publish_apply(repo_root, {"scope": "library"})
        except ValueError as exc:
            assert "confirm must be true" in str(exc)
        else:
            raise AssertionError("publish apply should require explicit confirmation")


def test_publish_rejects_non_public_scope() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        write_scope_config(repo_root)

        try:
            docs_publish_gate.publish_confirm(repo_root, {"scope": "studio"})
        except ValueError as exc:
            assert "not a public read-only scope" in str(exc)
        else:
            raise AssertionError("publish should reject non-public scopes")
