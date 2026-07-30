#!/usr/bin/env python3
"""Focused ordinary Docs Import destination-adoption contracts."""

from __future__ import annotations

from pathlib import Path

import pytest

import docs_import_preview
from repo_factory import (
    docs_scope_record,
    docs_sub_scope_record,
    write_docs_scope_config,
    write_site_tools_config,
    write_staged_import_file,
)

import docs_management_import_service as import_service


def prepare_repo(repo_root: Path) -> None:
    write_site_tools_config(repo_root)
    write_docs_scope_config(
        repo_root,
        [
            docs_scope_record("studio"),
            docs_scope_record(
                "analysis",
                sub_scopes=[
                    docs_sub_scope_record(
                        "analysis",
                        "tags",
                        title="Tags",
                    )
                ],
            ),
        ],
    )
    for path in (
        repo_root / "docs-viewer/scopes/studio/source/documents",
        repo_root / "docs-viewer/scopes/analysis/source/documents",
        (
            repo_root
            / "docs-viewer/scopes/analysis/source/sub-scopes/tags/documents"
        ),
    ):
        path.mkdir(parents=True, exist_ok=True)


def test_import_target_adopts_parent_and_configured_child(
    tmp_path: Path,
) -> None:
    prepare_repo(tmp_path)

    parent = import_service.resolve_ordinary_import_target(
        tmp_path,
        {"scope": " STUDIO "},
    )
    child = import_service.resolve_ordinary_import_target(
        tmp_path,
        {"scope": "analysis", "sub_scope": "TAGS"},
    )

    assert parent.request_target() == {"scope": "studio"}
    assert child.request_target() == {
        "scope": "analysis",
        "sub_scope": "tags",
    }


def test_import_handler_preview_freezes_child_destination(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prepare_repo(tmp_path)
    write_staged_import_file(
        tmp_path,
        "ordinary.md",
        "# Ordinary\n\nPreview body.\n",
    )
    monkeypatch.setattr(
        docs_import_preview,
        "validate_markdown_preview",
        lambda markdown, *, title="": {
            "ok": True,
            "html_chars": len(markdown),
            "renderer": "stub",
        },
    )

    payload = import_service.handle_import_source(
        tmp_path,
        {
            "scope": "analysis",
            "sub_scope": "tags",
            "staged_filename": "ordinary.md",
            "preview_only": True,
        },
        dry_run=False,
    )

    assert payload["preview_only"] is True
    assert payload["scope"] == "analysis"
    assert payload["sub_scope"] == "tags"
    assert payload["import_preview"]["target"] == {
        "scope": "analysis",
        "sub_scope": "tags",
    }
    assert not list(
        (tmp_path / "docs-viewer/scopes/analysis/source/documents").glob("*.md")
    )
    assert not list(
        (
            tmp_path
            / "docs-viewer/scopes/analysis/source/sub-scopes/tags/documents"
        ).glob("*.md")
    )


@pytest.mark.parametrize(
    ("target", "message"),
    [
        ({"scope": ""}, "scope is required"),
        ({"scope": "missing"}, "unknown Docs Viewer scope"),
        (
            {"scope": "analysis", "sub_scope": ""},
            "sub_scope is required",
        ),
        (
            {"scope": "analysis", "sub_scope": "missing"},
            "unknown sub_scope",
        ),
        (
            {"scope": "analysis", "sub_scope": "tags/nested"},
            "one configured child",
        ),
        (
            {"scope": "studio", "sub_scope": "tags"},
            "unknown sub_scope",
        ),
        (
            {
                "scope": "analysis",
                "sub_scope": "tags",
                "selected_parent": "tags-report",
            },
            "must contain exactly scope",
        ),
    ],
)
def test_import_target_rejects_invalid_and_fallback_requests(
    tmp_path: Path,
    target: dict[str, str],
    message: str,
) -> None:
    prepare_repo(tmp_path)

    with pytest.raises(ValueError, match=message):
        import_service.resolve_ordinary_import_target(tmp_path, target)
