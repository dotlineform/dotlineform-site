#!/usr/bin/env python3
"""Focused checks for Docs Management source body editing."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
if str(DOCS_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(DOCS_SERVICES_DIR))

import docs_management_source_service as source_service  # noqa: E402


def write_source(repo_root: Path, filename: str, text: str, scope: str = "studio") -> Path:
    path = repo_root / "docs-viewer" / "source" / scope / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def make_repo() -> tempfile.TemporaryDirectory[str]:
    temp_dir = tempfile.TemporaryDirectory()
    repo_root = Path(temp_dir.name)
    (repo_root / "site-tools/config").mkdir(parents=True, exist_ok=True); (repo_root / "site-tools/config/site-tools.json").write_text("{\"schema_version\":\"site_tools_config_v1\"}\n", encoding="utf-8")
    write_source(
        repo_root,
        "target.md",
        "---\n"
        "doc_id: target\n"
        "title: Target\n"
        "viewable: true\n"
        "---\n"
        "# Target\n\nOriginal body.\n",
    )
    return temp_dir


def test_read_source_body_returns_body_and_revision() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        payload = source_service.read_source_body(repo_root, {"scope": ["studio"], "doc_id": ["target"]})

    assert payload["ok"] is True
    assert payload["doc_id"] == "target"
    assert payload["source_body"] == "# Target\n\nOriginal body.\n"
    assert str(payload["source_revision"]).startswith("sha256:")


def test_rebuild_source_body_rejects_stale_revision() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        try:
            source_service.rebuild_source_body(
                repo_root,
                {
                    "scope": "studio",
                    "doc_id": "target",
                    "source_revision": "sha256:stale",
                    "source_body": "# Changed\n",
                },
                dry_run=False,
            )
        except ValueError as error:
            assert "stale" in str(error)
        else:
            raise AssertionError("expected stale source revision to be rejected")


def test_read_source_body_rejects_invalid_existing_front_matter() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_source(repo_root, "target.md", "---\ndoc_id: target\ntitle: Target\n# Missing delimiter\n")
        try:
            source_service.read_source_body(repo_root, {"scope": ["studio"], "doc_id": ["target"]})
        except ValueError as error:
            assert "front matter" in str(error)
        else:
            raise AssertionError("expected invalid front matter to be rejected")


def test_rebuild_source_body_preserves_front_matter_exactly_and_targets_selected_doc(monkeypatch) -> None:
    calls: list[dict[str, object]] = []

    def fake_rebuild(repo_root, scope, changed_paths, write_operation, **kwargs):
        calls.append(
            {
                "scope": scope,
                "changed_paths": [path.name for path in changed_paths],
                "docs_doc_ids": kwargs.get("docs_doc_ids"),
                "search_doc_ids": kwargs.get("search_doc_ids"),
                "suppression_reason": kwargs.get("suppression_reason"),
            }
        )
        write_operation()
        return {
            "ok": True,
            "docs": {"mode": "targeted", "doc_ids": kwargs.get("docs_doc_ids")},
            "search": {"mode": "targeted", "doc_ids": kwargs.get("search_doc_ids")},
        }

    monkeypatch.setattr(source_service.write_rebuild, "perform_source_write_and_rebuild", fake_rebuild)

    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        source_path = write_source(
            repo_root,
            "target.md",
            "---\n"
            "title: Target\n"
            "# keep comment\n"
            "doc_id: target\n"
            "viewable: true\n"
            "---\n"
            "# Old\n",
        )
        read_payload = source_service.read_source_body(repo_root, {"scope": ["studio"], "doc_id": ["target"]})
        payload = source_service.rebuild_source_body(
            repo_root,
            {
                "scope": "studio",
                "doc_id": "target",
                "source_revision": read_payload["source_revision"],
                "source_body": "# New\n\nBody\n",
            },
            dry_run=False,
        )
        written = source_path.read_text(encoding="utf-8")

    assert payload["ok"] is True
    assert calls == [
        {
            "scope": "studio",
            "changed_paths": ["target.md"],
            "docs_doc_ids": ["target"],
            "search_doc_ids": ["target"],
            "suppression_reason": "docs-source-editor",
        }
    ]
    assert written == (
        "---\n"
        "title: Target\n"
        "# keep comment\n"
        "doc_id: target\n"
        "viewable: true\n"
        "---\n"
        "# New\n\nBody\n"
    )


def main() -> None:
    test_read_source_body_returns_body_and_revision()
    test_rebuild_source_body_rejects_stale_revision()
    test_read_source_body_rejects_invalid_existing_front_matter()
    print("Run this file with pytest for monkeypatch-backed rebuild checks.")


if __name__ == "__main__":
    main()
