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
                    "publish_output": "assets/data/docs/scopes/library",
                    "publish_search_output": "assets/data/search/library/index.json",
                    "viewer_base_url": "/library/",
                    "include_scope_param": False,
                    "default_doc_id": "library",
                },
            ],
        },
    )


def prepare_publish_repo(root: Path) -> None:
    write_scope_config(root)
    write_json(root / "docs-viewer/generated/docs/library/index-tree.json", {"docs": [{"doc_id": "library"}]})
    write_json(root / "docs-viewer/generated/docs/library/recently-added.json", {"docs": [{"doc_id": "library"}]})
    write_json(root / "docs-viewer/generated/docs/library/by-id/library.json", {"title": "Library"})
    write_json(root / "docs-viewer/generated/search/library/index.json", {"entries": [{"id": "library"}]})
    write_json(root / "assets/data/docs/scopes/library/index-tree.json", {"docs": []})
    write_json(root / "assets/data/docs/scopes/library/by-id/stale.json", {"title": "Stale"})
    write_json(root / "assets/data/search/library/index.json", {"entries": []})


def test_publish_confirm_reports_changes_and_apply_syncs_stale_files() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        prepare_publish_repo(repo_root)

        preview = docs_publish_gate.publish_confirm(repo_root, {"scope": "library"})
        applied = docs_publish_gate.publish_apply(repo_root, {"scope": "library", "confirm": True})

        assert preview["operation"] == "confirm"
        assert preview["changed_count"] >= 3
        assert "assets/data/docs/scopes/library/by-id/stale.json" in preview["docs"]["removed"]
        assert applied["operation"] == "apply"
        assert (repo_root / "assets/data/docs/scopes/library/by-id/library.json").exists()
        assert not (repo_root / "assets/data/docs/scopes/library/by-id/stale.json").exists()
        assert json.loads((repo_root / "assets/data/search/library/index.json").read_text(encoding="utf-8"))["entries"][0]["id"] == "library"


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
