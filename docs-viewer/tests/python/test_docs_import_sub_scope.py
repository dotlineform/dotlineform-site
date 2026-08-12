#!/usr/bin/env python3
"""Ordinary staged-source Import into one exact configured sub-scope."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

import docs_import_preview
import docs_import_source_service
import docs_management_import_service as import_service
import docs_source_model as source_model
import docs_write_rebuild
from repo_factory import (
    docs_scope_record,
    docs_sub_scope_record,
    write_docs_scope_config,
    write_site_tools_config,
    write_staged_import_file,
    write_staged_package_file,
)
from docs_import_test_support import write_test_image


REPORT_DOC_ID = "d-20260730-000000-000001"


def prepare_repo(repo_root: Path) -> None:
    write_site_tools_config(repo_root)
    write_docs_scope_config(
        repo_root,
        [
            docs_scope_record(
                "analysis",
                sub_scopes=[
                    docs_sub_scope_record(
                        "analysis",
                        "tags",
                        title="Tags",
                        ui_statuses=["draft", "done"],
                        analysis_tag_groups=["theme"],
                    )
                ],
            ),
        ],
    )
    for path in (
        repo_root / "docs-viewer/scopes/analysis/source/documents",
        (
            repo_root
            / "docs-viewer/scopes/analysis/source/sub-scopes/tags/documents"
        ),
    ):
        path.mkdir(parents=True, exist_ok=True)
    (
        repo_root
        / f"docs-viewer/scopes/analysis/source/documents/{REPORT_DOC_ID}.md"
    ).write_text(
        (
            "---\n"
            f"doc_id: {REPORT_DOC_ID}\n"
            "title: Tags\n"
            "---\n"
            "# Tags\n\n"
            ":::report\n"
            "id: docs_subscope\n"
            "access: public\n"
            "sub_scope: tags\n"
            ":::\n"
        ),
        encoding="utf-8",
    )


def stub_markdown_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        docs_import_preview,
        "validate_markdown_preview",
        lambda markdown, *, title="": {
            "ok": True,
            "html_chars": len(markdown),
            "renderer": "stub",
        },
    )


def stub_confined_rebuild(
    monkeypatch: pytest.MonkeyPatch,
) -> list[dict[str, object]]:
    calls: list[dict[str, object]] = []

    def fail_parent_rebuild(*_args, **_kwargs):
        raise AssertionError("parent scope rebuild must not run")

    def rebuild_child(
        repo_root,
        scope,
        sub_scope,
        changed_paths,
        write_operation,
        **kwargs,
    ):
        write_operation()
        calls.append(
            {
                "repo_root": repo_root,
                "scope": scope,
                "sub_scope": sub_scope,
                "changed_paths": list(changed_paths),
                "suppression_reason": kwargs.get("suppression_reason"),
            }
        )
        return {
            "ok": True,
            "docs": {
                "mode": "sub_scope",
                "sub_scope": sub_scope,
                "doc_ids": [],
            },
            "search": {"mode": "none", "doc_ids": []},
        }

    monkeypatch.setattr(
        docs_write_rebuild,
        "perform_source_write_and_rebuild",
        fail_parent_rebuild,
    )
    monkeypatch.setattr(
        docs_write_rebuild,
        "perform_sub_scope_source_write_and_rebuild",
        rebuild_child,
    )
    return calls


def test_markdown_import_creates_only_in_exact_child_with_fresh_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prepare_repo(tmp_path)
    stub_markdown_validation(monkeypatch)
    rebuild_calls = stub_confined_rebuild(monkeypatch)
    write_staged_import_file(
        tmp_path,
        "ordinary.md",
        """---
title: Imported Tag Note
doc_id: existing-tag-doc
summary: This must not become canonical metadata.
group: theme
---

Body without an H1.
""",
    )

    payload = import_service.handle_import_source(
        tmp_path,
        {
            "scope": "analysis",
            "sub_scope": "tags",
            "source_directory": "data-sharing/import-staging",
            "staged_filename": "ordinary.md",
        },
        dry_run=False,
    )

    target_path = tmp_path / payload["path"]
    front_matter, body = source_model.parse_source(target_path)
    child_root = (
        tmp_path
        / "docs-viewer/scopes/analysis/source/sub-scopes/tags/documents"
    )

    assert payload["ok"] is True
    assert payload["operation"] == "create"
    assert payload["scope"] == "analysis"
    assert payload["sub_scope"] == "tags"
    assert payload["source_directory"] == "data-sharing/import-staging"
    assert payload["target"] == {
        "scope": "analysis",
        "sub_scope": "tags",
        "doc_id": payload["doc_id"],
    }
    assert payload["viewer_url"] == (
        f"/docs/?scope=analysis&doc={REPORT_DOC_ID}&subdoc={payload['doc_id']}"
    )
    assert payload["record"] == {
        "doc_id": payload["doc_id"],
        "title": "Imported Tag Note",
    }
    assert source_model.is_immutable_doc_id(payload["doc_id"])
    assert payload["doc_id"] != "existing-tag-doc"
    assert target_path.parent == child_root
    assert [
        path.name
        for path in (
            tmp_path / "docs-viewer/scopes/analysis/source/documents"
        ).glob("*.md")
    ] == [f"{REPORT_DOC_ID}.md"]
    assert front_matter["doc_id"] == payload["doc_id"]
    assert front_matter["title"] == "Imported Tag Note"
    assert "publishable" not in front_matter
    assert "parent_id" not in front_matter
    assert "summary" not in front_matter
    assert "group" not in front_matter
    assert body == "Body without an H1.\n"
    assert payload["import_preview"]["target"] == {
        "scope": "analysis",
        "sub_scope": "tags",
    }
    assert payload["import_preview"]["ordinary_front_matter"] == {
        "stripped": True,
        "fields": ["title", "doc_id", "summary", "group"],
        "ignored_fields": ["doc_id", "summary", "group"],
        "title_used": True,
    }
    assert len(rebuild_calls) == 1
    assert rebuild_calls[0]["scope"] == "analysis"
    assert rebuild_calls[0]["sub_scope"] == "tags"
    assert rebuild_calls[0]["changed_paths"] == [target_path]
    assert rebuild_calls[0]["suppression_reason"] == "docs-import-source-create"
    assert payload["rebuild"]["search"] == {"mode": "none", "doc_ids": []}


def test_markdown_package_reuses_parent_media_and_child_source_owners(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prepare_repo(tmp_path)
    stub_markdown_validation(monkeypatch)
    rebuild_calls = stub_confined_rebuild(monkeypatch)
    markdown_path = write_staged_package_file(
        tmp_path,
        "tag-package",
        "note.md",
        """---
title: Package Tag Note
doc_id: package-overwrite-id
---

Package body.

![Reference](image.png)
""",
    )
    image_path = write_staged_package_file(
        tmp_path,
        "tag-package",
        "image.png",
        b"",
    )
    write_test_image(image_path, (24, 18))

    payload = import_service.handle_import_source(
        tmp_path,
        {
            "scope": "analysis",
            "sub_scope": "tags",
            "source_directory": "data-sharing/import-staging",
            "staged_filename": "tag-package",
        },
        dry_run=False,
    )

    target_path = tmp_path / payload["path"]
    source_text = target_path.read_text(encoding="utf-8")
    media_result = payload["inline_media_written"][0]
    media_path = (
        Path(os.environ["DOTLINEFORM_PROJECTS_BASE_DIR"])
        / "docs-viewer/media/analysis/img"
        / media_result["artifact_identity"]
    )

    assert markdown_path.is_file()
    assert payload["import_preview"]["source_format"] == "markdown_package"
    assert payload["title"] == "Package Tag Note"
    assert payload["viewer_url"] == (
        f"/docs/?scope=analysis&doc={REPORT_DOC_ID}&subdoc={payload['doc_id']}"
    )
    assert "---" not in payload["import_preview"]["markdown_preview"]
    assert "package-overwrite-id" not in source_text
    assert target_path.parent.name == "documents"
    assert target_path.parent.parent.name == "tags"
    assert media_result["media_path"].startswith("docs/analysis/img/")
    assert media_result["publish_status"] == "uploaded"
    assert media_path.is_file()
    assert media_path.suffix == ".webp"
    assert f"[[media:{media_result['media_path']}]]" in source_text
    assert len(rebuild_calls) == 1


def test_child_destination_rejects_registered_collection_before_markdown(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prepare_repo(tmp_path)
    write_staged_import_file(
        tmp_path,
        "claimed.md",
        "---\ntitle: Must remain untouched\n---\nBody.\n",
    )
    monkeypatch.setattr(
        docs_import_source_service,
        "document_package_source_format",
        lambda *_args, **_kwargs: (
            docs_import_source_service.COLLECTION_SOURCE_FORMAT
        ),
    )
    monkeypatch.setattr(
        docs_import_source_service,
        "generate_import_preview",
        lambda *_args, **_kwargs: (
            pytest.fail("registered collection must not reach generic Markdown")
        ),
    )

    with pytest.raises(
        ValueError,
        match="Returned document packages are not supported",
    ):
        import_service.handle_import_source(
            tmp_path,
            {
                "scope": "analysis",
                "sub_scope": "tags",
                "source_directory": "data-sharing/import-staging",
                "staged_filename": "claimed.md",
            },
            dry_run=False,
        )


def test_child_collection_metadata_is_validated_before_preview(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prepare_repo(tmp_path)
    write_staged_import_file(
        tmp_path,
        "ordinary.md",
        "# Ordinary\n\nBody.\n",
    )
    invalid_child = (
        tmp_path
        / "docs-viewer/scopes/analysis/source/sub-scopes/tags/documents/invalid.md"
    )
    invalid_child.write_text(
        """---
doc_id: invalid
title: Invalid
group: unsupported
---
# Invalid
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        docs_import_source_service,
        "generate_import_preview",
        lambda *_args, **_kwargs: pytest.fail(
            "invalid child collection must block before preview",
        ),
    )

    with pytest.raises(ValueError, match="Unknown group 'unsupported'"):
        import_service.handle_import_source(
            tmp_path,
            {
                "scope": "analysis",
                "sub_scope": "tags",
                "source_directory": "data-sharing/import-staging",
                "staged_filename": "ordinary.md",
                "preview_only": True,
            },
            dry_run=False,
        )
