#!/usr/bin/env python3
"""Focused checks for Docs Management source body editing."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from repo_factory import (
    docs_scope_record,
    docs_sub_scope_record,
    write_docs_scope_config,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
if str(DOCS_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(DOCS_SERVICES_DIR))

import docs_management_source_service as source_service  # noqa: E402


def write_source(
    repo_root: Path,
    filename: str,
    text: str,
    scope: str = "studio",
    sub_scope: str = "",
) -> Path:
    source_root = repo_root / "docs-viewer" / "scopes" / scope / "source"
    if sub_scope:
        source_root = source_root / "sub-scopes" / sub_scope
    path = source_root / "documents" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def make_repo() -> tempfile.TemporaryDirectory[str]:
    temp_dir = tempfile.TemporaryDirectory()
    repo_root = Path(temp_dir.name)
    (repo_root / "site-tools/config").mkdir(parents=True, exist_ok=True)
    (repo_root / "site-tools/config/site-tools.json").write_text(
        "{\"schema_version\":\"site_tools_config_v1\"}\n",
        encoding="utf-8",
    )
    write_docs_scope_config(
        repo_root,
        [
            docs_scope_record(
                "studio",
                sub_scopes=[docs_sub_scope_record("studio", "tags")],
            )
        ],
    )
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
    write_source(
        repo_root,
        "detail.md",
        "---\n"
        "doc_id: detail\n"
        "title: Detail\n"
        "viewable: true\n"
        "---\n"
        "# Detail\n\nSub-scope body.\n",
        sub_scope="tags",
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
    assert set(payload) == {
        "ok",
        "scope",
        "doc_id",
        "source_body",
        "source_revision",
        "path",
    }


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


def test_rebuild_source_body_accepts_exact_crlf_revision() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        source_path = (
            repo_root
            / "docs-viewer/scopes/studio/source/documents/target.md"
        )
        source_path.write_bytes(
            source_path.read_bytes().replace(b"\n", b"\r\n")
        )
        read_payload = source_service.read_source_body(
            repo_root,
            {"scope": ["studio"], "doc_id": ["target"]},
        )

        payload = source_service.rebuild_source_body(
            repo_root,
            {
                "scope": "studio",
                "doc_id": "target",
                "source_revision": read_payload["source_revision"],
                "source_body": read_payload["source_body"],
            },
            dry_run=True,
        )

    assert payload["ok"] is True
    assert payload["source_changed"] is False


def test_read_source_body_returns_exact_sub_scope_target() -> None:
    with make_repo() as temp_path:
        payload = source_service.read_source_body(
            Path(temp_path),
            {
                "scope": ["studio"],
                "sub_scope": ["tags"],
                "doc_id": ["detail"],
            },
        )

    assert payload["scope"] == "studio"
    assert payload["sub_scope"] == "tags"
    assert payload["doc_id"] == "detail"
    assert payload["source_body"] == "# Detail\n\nSub-scope body.\n"
    assert set(payload) == {
        "ok",
        "scope",
        "sub_scope",
        "doc_id",
        "source_body",
        "source_revision",
        "path",
    }


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


def test_read_source_body_rejects_retired_doc_alias() -> None:
    with make_repo() as temp_path:
        with pytest.raises(ValueError, match="doc_id is required"):
            source_service.read_source_body(
                Path(temp_path),
                {"scope": ["studio"], "doc": ["target"]},
            )


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
    monkeypatch.setattr(source_service.source_model, "current_doc_timestamp", lambda: "2026-07-16 12:34:56")

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
        "added_date: \"2026-07-16 12:34:56\"\n"
        "last_updated: \"2026-07-16 12:34:56\"\n"
        "---\n"
        "# New\n\nBody\n"
    )


def test_rebuild_source_body_noops_without_timestamp_or_rebuild(monkeypatch) -> None:
    calls: list[object] = []
    monkeypatch.setattr(
        source_service.write_rebuild,
        "perform_source_write_and_rebuild",
        lambda *_args, **_kwargs: calls.append(object()),
    )

    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        source_path = repo_root / "docs-viewer/scopes/studio/source/documents/target.md"
        before = source_path.read_text(encoding="utf-8")
        read_payload = source_service.read_source_body(repo_root, {"scope": ["studio"], "doc_id": ["target"]})
        payload = source_service.rebuild_source_body(
            repo_root,
            {
                "scope": "studio",
                "doc_id": "target",
                "source_revision": read_payload["source_revision"],
                "source_body": read_payload["source_body"],
            },
            dry_run=False,
        )
        after = source_path.read_text(encoding="utf-8")

    assert calls == []
    assert before == after
    assert payload["source_changed"] is False
    assert payload["rebuild"] is None


def test_rebuild_sub_scope_source_uses_configured_build_and_preserves_target(
    monkeypatch,
) -> None:
    calls: list[dict[str, object]] = []

    def fake_rebuild(
        repo_root,
        scope,
        sub_scope,
        changed_paths,
        write_operation,
        **kwargs,
    ):
        calls.append(
            {
                "scope": scope,
                "sub_scope": sub_scope,
                "changed_paths": [path.name for path in changed_paths],
                "suppression_reason": kwargs.get("suppression_reason"),
            }
        )
        write_operation()
        return {
            "ok": True,
            "docs": {"mode": "sub_scope", "sub_scope": sub_scope},
            "search": {"mode": "full", "doc_ids": []},
        }

    monkeypatch.setattr(
        source_service.write_rebuild,
        "perform_sub_scope_source_write_and_rebuild",
        fake_rebuild,
    )
    monkeypatch.setattr(
        source_service.source_model,
        "current_doc_timestamp",
        lambda: "2026-07-27 20:15:00",
    )

    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        source_path = (
            repo_root
            / "docs-viewer/scopes/studio/source/sub-scopes/tags/documents/detail.md"
        )
        read_payload = source_service.read_source_body(
            repo_root,
            {
                "scope": ["studio"],
                "sub_scope": ["tags"],
                "doc_id": ["detail"],
            },
        )
        payload = source_service.rebuild_source_body(
            repo_root,
            {
                "scope": "studio",
                "sub_scope": "tags",
                "doc_id": "detail",
                "source_revision": read_payload["source_revision"],
                "source_body": "# Detail\n\nChanged body.\n",
            },
            dry_run=False,
        )
        written = source_path.read_text(encoding="utf-8")

    assert calls == [
        {
            "scope": "studio",
            "sub_scope": "tags",
            "changed_paths": ["detail.md"],
            "suppression_reason": "docs-source-editor",
        }
    ]
    assert payload["scope"] == "studio"
    assert payload["sub_scope"] == "tags"
    assert payload["doc_id"] == "detail"
    assert payload["rebuild"]["docs"]["mode"] == "sub_scope"
    assert 'last_updated: "2026-07-27 20:15:00"' in written
    assert written.endswith("# Detail\n\nChanged body.\n")


def test_open_source_doc_resolves_parent_and_sub_scope_targets() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        parent = source_service.open_source_doc(
            repo_root,
            {
                "scope": "studio",
                "doc_id": "target",
                "editor": "vscode",
            },
            dry_run=True,
        )
        detail = source_service.open_source_doc(
            repo_root,
            {
                "scope": "studio",
                "sub_scope": "tags",
                "doc_id": "detail",
                "editor": "vscode",
            },
            dry_run=True,
        )

    assert set(parent) == {
        "ok",
        "scope",
        "doc_id",
        "editor",
        "preferred_app",
        "path",
        "summary_text",
        "dry_run",
    }
    assert detail["sub_scope"] == "tags"
    assert detail["doc_id"] == "detail"
    assert "source/sub-scopes/tags/documents/detail.md" in str(detail["path"])


def test_open_source_path_uses_visual_studio_code_without_confirmation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    calls: list[dict[str, object]] = []

    def fake_run(command, **options):
        calls.append({"command": command, **options})
        return SimpleNamespace(returncode=0, stderr="", stdout="")

    source_path = tmp_path / "selected.md"
    source_path.write_text("# Selected\n", encoding="utf-8")
    monkeypatch.setattr(source_service.subprocess, "run", fake_run)

    preferred_app = source_service.open_source_path(
        tmp_path,
        source_path,
        editor="vscode",
        dry_run=False,
    )

    assert preferred_app is None
    assert calls == [
        {
            "command": ["open", "-a", "Visual Studio Code", str(source_path)],
            "cwd": str(tmp_path),
            "capture_output": True,
            "text": True,
            "check": False,
        }
    ]


def main() -> None:
    test_read_source_body_returns_body_and_revision()
    test_rebuild_source_body_rejects_stale_revision()
    test_read_source_body_rejects_invalid_existing_front_matter()
    print("Run this file with pytest for monkeypatch-backed rebuild checks.")


if __name__ == "__main__":
    main()
