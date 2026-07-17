#!/usr/bin/env python3
"""Focused checks for Docs Viewer public publish gate."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from repo_factory import docs_scope_record, docs_sub_scope_record


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
            "schema_version": "docs_scopes_v2",
            "scopes": [
                docs_scope_record("studio", default_doc_id="studio"),
                docs_scope_record(
                    "library",
                    scope_type="public",
                    viewer_base_url="/library/",
                    include_scope_param=False,
                    default_doc_id="library",
                ),
            ],
        },
    )


def prepare_publish_repo(root: Path) -> None:
    write_scope_config(root)
    write_json(
        root / "docs-viewer/published/docs/library/index-tree.json",
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
        root / "docs-viewer/published/docs/library/recent.json",
        {
            "schema": "docs_recent_v1",
            "basis": "edited",
            "docs": [
                {"doc_id": "hidden", "title": "Hidden", "content_url": "/assets/data/docs/scopes/library/by-id/hidden.json", "timestamp": "2026-06-02 10:00:00"},
                {"doc_id": "library", "title": "Library", "content_url": "/assets/data/docs/scopes/library/by-id/library.json", "timestamp": "2026-06-01 10:00:00"},
            ],
        },
    )
    write_json(
        root / "docs-viewer/published/docs/library/.publish/recent.json",
        {
            "schema": "docs_recent_v1",
            "basis": "edited",
            "docs": [
                {"doc_id": "library", "title": "Library", "content_url": "/assets/data/docs/scopes/library/by-id/library.json", "timestamp": "2026-06-01 10:00:00"},
            ],
        },
    )
    write_json(root / "docs-viewer/published/docs/library/by-id/library.json", {"title": "Library"})
    write_json(root / "docs-viewer/published/docs/library/by-id/hidden.json", {"title": "Hidden"})
    write_json(root / "docs-viewer/published/docs/library/by-id/hidden-child.json", {"title": "Hidden Child"})
    write_json(root / "docs-viewer/published/docs/library/by-id/manage-root.json", {"title": "Manage Root"})
    write_json(
        root / "docs-viewer/published/docs/library/references/index.json",
        {
            "header": {"schema": "docs_semantic_references_index_v1", "scope": "library", "count": 1, "target_count": 1},
            "targets": [],
        },
    )
    write_json(
        root / "docs-viewer/published/docs/library/references/by-doc/hidden.json",
        {
            "header": {"schema": "docs_semantic_references_by_doc_v1", "scope": "library", "doc_id": "hidden", "count": 1},
            "references": [{"source_doc_id": "hidden", "target_kind": "work", "target_id": "00638"}],
        },
    )
    write_json(
        root / "docs-viewer/published/docs/library/references/by-target/work/00638.json",
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
    write_json(root / "docs-viewer/published/search/library/index.json", {"entries": [{"id": "library"}]})
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
        recent = json.loads((repo_root / "site/assets/data/docs/scopes/library/recent.json").read_text(encoding="utf-8"))
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


def test_publish_confirm_and_apply_include_configured_sub_scope_payloads() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        prepare_publish_repo(repo_root)
        config_path = repo_root / "docs-viewer/config/scopes/docs_scopes.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["scopes"][1]["sub_scopes"] = [
            docs_sub_scope_record("library", "tags", title="Tags", scope_type="public")
        ]
        write_json(config_path, config)
        write_json(repo_root / "docs-viewer/published/docs/library/tags/manifest.json", {"doc_ids": "scale"})
        write_json(repo_root / "docs-viewer/published/docs/library/tags/by-id/scale.json", {"doc_id": "scale", "title": "Scale"})
        write_json(repo_root / "site/assets/data/docs/scopes/library/tags/manifest.json", {"doc_ids": "old"})
        write_json(repo_root / "site/assets/data/docs/scopes/library/tags/by-id/old.json", {"doc_id": "old"})

        preview = docs_publish_gate.publish_confirm(repo_root, {"scope": "library"})
        applied = docs_publish_gate.publish_apply(repo_root, {"scope": "library", "confirm": True})

        assert preview["operation"] == "confirm"
        assert preview["sub_scopes"] == [
            {
                "sub_scope": "tags",
                "changed": [
                    "site/assets/data/docs/scopes/library/tags/by-id/scale.json",
                    "site/assets/data/docs/scopes/library/tags/manifest.json",
                ],
                "removed": ["site/assets/data/docs/scopes/library/tags/by-id/old.json"],
                "changed_count": 2,
                "removed_count": 1,
            }
        ]
        assert "site/assets/data/docs/scopes/library/tags/by-id/old.json" not in preview["docs"]["removed"]
        assert applied["operation"] == "apply"
        public_manifest = json.loads((repo_root / "site/assets/data/docs/scopes/library/tags/manifest.json").read_text(encoding="utf-8"))
        public_scale = json.loads((repo_root / "site/assets/data/docs/scopes/library/tags/by-id/scale.json").read_text(encoding="utf-8"))

        assert public_manifest == {"doc_ids": "scale"}
        assert public_scale["title"] == "Scale"
        assert not (repo_root / "site/assets/data/docs/scopes/library/tags/by-id/old.json").exists()


def test_publish_rejects_configured_sub_scope_without_manifest() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        prepare_publish_repo(repo_root)
        config_path = repo_root / "docs-viewer/config/scopes/docs_scopes.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["scopes"][1]["sub_scopes"] = [
            docs_sub_scope_record("library", "tags", title="Tags", scope_type="public")
        ]
        write_json(config_path, config)
        (repo_root / "docs-viewer/published/docs/library/tags").mkdir(parents=True)

        try:
            docs_publish_gate.publish_confirm(repo_root, {"scope": "library"})
        except FileNotFoundError as exc:
            assert "sub-scope tags manifest not found" in str(exc)
        else:
            raise AssertionError("publish should reject configured sub-scope output without manifest")


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
