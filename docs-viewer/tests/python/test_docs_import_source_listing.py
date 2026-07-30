#!/usr/bin/env python3
"""Docs source import listing and preview tests."""

from __future__ import annotations

import json
from pathlib import Path
import shutil

import pytest

import docs_import_collection_apply
import docs_import_media
import docs_import_preview
import docs_import_review_source_folder
import docs_import_source_service as import_source_service
import docs_management_import_service
import docs_review_packages
import docs_source_model
import docs_write_rebuild
from docs_builder.pipeline import DocsDataBuilder
from docs_builder.sub_scope import SubScopeDocsBuilder, selected_sub_scope
from docs_import_common import FILE_MEDIA_STAGED_SUFFIXES
from docs_import_docx_test_support import semantic_docx_bytes
from docs_management_document_target import resolve_managed_document_collection
from docs_document_packages.workspace import configured_workspace_paths
from docs_scope_config import load_docs_scope_configs
from repo_factory import docs_scope_record, docs_sub_scope_record

from docs_import_test_support import (
    make_repo,
    write_returned_jsonl,
    write_staged,
    write_staged_bytes,
    write_staged_html,
    write_staged_markdown,
    write_staged_package_file,
    write_staged_text,
)


REVIEW_FOLDER_ID = "20260730-105512-document-content"
REVIEW_EXPORT_ID = "ds_20260730T095512Z"
SUB_REVIEW_FOLDER_ID = "20260730-190000-document-content"
SUB_REVIEW_EXPORT_ID = "ds_20260730T180000Z"
ANALYSIS_REVIEW_FOLDER_ID = "20260730-200000-document-content"
ANALYSIS_REVIEW_EXPORT_ID = "ds_20260730T190000Z"


def review_source_text(
    doc_id: str,
    title: str,
    *,
    folder_id: str = REVIEW_FOLDER_ID,
    export_id: str = REVIEW_EXPORT_ID,
    scope: str = "library",
    sub_scope: str = "",
) -> str:
    sub_scope_line = (
        f"review_source_sub_scope: {sub_scope}\n"
        if sub_scope
        else ""
    )
    return (
        "---\n"
        f"doc_id: {doc_id}\n"
        f"title: {title}\n"
        "added_date: 2026-07-30\n"
        "last_updated: 2026-07-30\n"
        f"review_folder_id: {folder_id}\n"
        f"review_source_export_id: {export_id}\n"
        f"review_source_scope: {scope}\n"
        f"{sub_scope_line}"
        "review_profile_id: document-content\n"
        "---\n"
        f"# {title}\n"
    )


def write_review_source_fixture(
    root: Path,
    *,
    staged_folder: str = "edited-review-copy",
    supports_return_import: bool = True,
    folder_id: str = REVIEW_FOLDER_ID,
    export_id: str = REVIEW_EXPORT_ID,
    scope: str = "library",
    sub_scope: str = "",
    records: list[tuple[str, str]] | None = None,
    source_last_updated: dict[str, str] | None = None,
) -> Path:
    paths = configured_workspace_paths(root)
    source_records = records or [
        ("alpha", "Alpha"),
        ("beta", "Beta"),
    ]
    retained_source = paths.import_preview / folder_id / "source"
    staged_source = paths.import_staging / staged_folder
    retained_source.mkdir(parents=True, exist_ok=True)
    staged_source.mkdir(parents=True, exist_ok=True)
    for doc_id, title in source_records:
        source_text = review_source_text(
            doc_id,
            title,
            folder_id=folder_id,
            export_id=export_id,
            scope=scope,
            sub_scope=sub_scope,
        )
        (retained_source / f"{doc_id}.md").write_text(
            source_text,
            encoding="utf-8",
        )
        (staged_source / f"{doc_id}.md").write_text(
            source_text,
            encoding="utf-8",
        )
    manifest = {
        "schema_version": "docs_review_validated_package_v1",
        "package_id": folder_id,
        "status": "validated",
        "source_scope": scope,
        "source_sub_scope": sub_scope,
        "profile_id": "document-content",
        "supports_docs_review": True,
        "supports_return_import": supports_return_import,
        "selected_doc_ids": [doc_id for doc_id, _title in source_records],
        "default_doc_id": source_records[0][0],
        "source_export_id": export_id,
        "source_files": [
            {
                "doc_id": doc_id,
                "path": f"source/{doc_id}.md",
            }
            for doc_id, _title in source_records
        ],
    }
    (retained_source.parent / "manifest.json").write_text(
        json.dumps(manifest) + "\n",
        encoding="utf-8",
    )
    generated_at = (
        f"{export_id[3:7]}-{export_id[7:9]}-{export_id[9:11]}"
        f"T{export_id[12:14]}:{export_id[14:16]}:{export_id[16:18]}Z"
    )
    metadata = {
        "schema_version": "data_sharing_export_meta_v1",
        "export_id": export_id,
        "app": "docs-viewer",
        "adapter_id": "documents",
        "data_domain": "documents",
        "profile_id": "document-content",
        "config_id": "document-content",
        "scope": scope,
        **({"sub_scope": sub_scope} if sub_scope else {}),
        "target_format": "jsonl",
        "record_shape": "document_rows",
        "supports_docs_review": True,
        "supports_return_import": supports_return_import,
        "generated_at": generated_at,
        "selected_doc_ids": [
            doc_id
            for doc_id, _title in source_records
        ],
        "source_last_updated": source_last_updated or {
            doc_id: "2026-07-29 12:00:00"
            for doc_id, _title in source_records
        },
    }
    paths.meta.mkdir(parents=True, exist_ok=True)
    (paths.meta / f"{export_id}.meta.json").write_text(
        json.dumps(metadata) + "\n",
        encoding="utf-8",
    )
    return staged_source


def import_dependencies() -> import_source_service.ImportSourceDependencies:
    return import_source_service.ImportSourceDependencies(
        log_event=lambda *_args, **_kwargs: None,
        perform_source_write_and_rebuild=lambda *_args, **_kwargs: {},
        perform_scope_source_write_and_rebuild_atomic=(
            lambda *_args, **_kwargs: {}
        ),
        perform_sub_scope_source_write_and_rebuild=(
            lambda *_args, **_kwargs: {}
        ),
    )


def write_review_scope_targets(root: Path) -> dict[str, Path]:
    targets = {
        "alpha": root / "docs-viewer/scopes/library/source/documents/alpha.md",
        "beta": root / "docs-viewer/scopes/library/source/documents/beta.md",
    }
    targets["alpha"].write_text(
        docs_source_model.format_source(
            {
            "doc_id": "alpha",
            "title": "Alpha",
            "added_date": "2026-07-01 10:00:00",
            "last_updated": "2026-07-29 12:00:00",
            "parent_id": "library",
            "summary": "Original Alpha summary.",
            "group": "protected-alpha",
            "ui_status": "draft",
            },
            "# Alpha\n",
        ),
        encoding="utf-8",
    )
    targets["beta"].write_text(
        docs_source_model.format_source(
            {
            "doc_id": "beta",
            "title": "Beta",
            "added_date": "2026-07-02 10:00:00",
            "last_updated": "2026-07-29 12:00:00",
            "parent_id": "library",
            "group": "protected-beta",
            "ui_status": "done",
            },
            "# Beta\n",
        ),
        encoding="utf-8",
    )
    return targets


def configure_review_sub_scope_targets(root: Path) -> dict[str, Path]:
    config_path = root / "docs-viewer/config/scopes/docs_scopes.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["scopes"][0]["sub_scopes"] = [
        docs_sub_scope_record(
            "library",
            "tags",
            title="Tags",
            supports_return_import=True,
            scope_type="public",
            public_docs_path="site/assets/data/docs/scopes/library/tags",
            ui_statuses=["draft", "done"],
            document_groups=["theme"],
        ),
        docs_sub_scope_record(
            "library",
            "notes",
            title="Notes",
            supports_return_import=True,
            scope_type="public",
            public_docs_path="site/assets/data/docs/scopes/library/notes",
            ui_statuses=["draft", "done"],
        ),
    ]
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    tags_root = (
        root
        / "docs-viewer/scopes/library/source/sub-scopes/tags/documents"
    )
    notes_root = (
        root
        / "docs-viewer/scopes/library/source/sub-scopes/notes/documents"
    )
    tags_root.mkdir(parents=True, exist_ok=True)
    notes_root.mkdir(parents=True, exist_ok=True)
    paths = {
        "tag-a": tags_root / "tag-a.md",
        "tag-b": tags_root / "tag-b.md",
        "tag-other": tags_root / "tag-other.md",
        "notes-tag-a": notes_root / "tag-a.md",
        "parent-tag-a": (
            root
            / "docs-viewer/scopes/library/source/documents/parent-tag-a.md"
        ),
    }
    records = {
        "tag-a": (
            {
                "doc_id": "tag-a",
                "title": "Tag A",
                "added_date": "2026-07-01 10:00:00",
                "last_updated": "2026-07-29 10:00:00",
                "summary": "Original Tag A summary.",
                "ui_status": "draft",
                "group": "theme",
                "viewable": False,
            },
            "# Tag A\n",
        ),
        "tag-b": (
            {
                "doc_id": "tag-b",
                "title": "Tag B",
                "added_date": "2026-07-02 10:00:00",
                "last_updated": "2026-07-29 11:00:00",
                "ui_status": "done",
                "group": "theme",
            },
            "# Tag B\n",
        ),
        "tag-other": (
            {
                "doc_id": "tag-other",
                "title": "Other Tag",
                "added_date": "2026-07-03 10:00:00",
                "last_updated": "2026-07-29 12:00:00",
                "ui_status": "draft",
                "group": "theme",
            },
            "# Other Tag\n",
        ),
        "notes-tag-a": (
            {
                "doc_id": "tag-a",
                "title": "Notes Tag A",
                "added_date": "2026-07-04 10:00:00",
                "last_updated": "2026-07-29 13:00:00",
                "ui_status": "draft",
            },
            "# Notes Tag A\n",
        ),
        "parent-tag-a": (
            {
                "doc_id": "tag-a",
                "title": "Parent Tag A",
                "added_date": "2026-07-05 10:00:00",
                "last_updated": "2026-07-29 14:00:00",
                "parent_id": "library",
            },
            "# Parent Tag A\n",
        ),
    }
    for key, path in paths.items():
        front_matter, body = records[key]
        path.write_text(
            docs_source_model.format_source(front_matter, body),
            encoding="utf-8",
        )
    return paths


def configure_analysis_tags_round_trip_targets(root: Path) -> dict[str, Path]:
    config_path = root / "docs-viewer/config/scopes/docs_scopes.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["scopes"].append(
        docs_scope_record(
            "analysis",
            default_doc_id="analysis-root",
            media_provider="repository",
            sub_scopes=[
                docs_sub_scope_record(
                    "analysis",
                    "tags",
                    title="Tags",
                    supports_return_import=True,
                    document_groups=["theme"],
                )
            ],
        )
    )
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    parent_root = root / "docs-viewer/scopes/analysis/source/documents"
    tags_root = (
        root
        / "docs-viewer/scopes/analysis/source/sub-scopes/tags/documents"
    )
    parent_root.mkdir(parents=True, exist_ok=True)
    tags_root.mkdir(parents=True, exist_ok=True)
    (parent_root / "analysis-root.md").write_text(
        docs_source_model.format_source(
            {
                "doc_id": "analysis-root",
                "title": "Analysis",
                "added_date": "2026-07-01 09:00:00",
                "last_updated": "2026-07-29 09:00:00",
            },
            "# Analysis\n",
        ),
        encoding="utf-8",
    )
    (parent_root / "tags-report.md").write_text(
        docs_source_model.format_source(
            {
                "doc_id": "tags-report",
                "title": "Tags",
                "added_date": "2026-07-01 09:30:00",
                "last_updated": "2026-07-29 09:30:00",
                "parent_id": "analysis-root",
                "viewer_report": "docs_subscope",
                "viewer_report_subscope": "tags",
            },
            "# Tags\n",
        ),
        encoding="utf-8",
    )
    targets = {
        "tag-a": tags_root / "tag-a.md",
        "tag-b": tags_root / "tag-b.md",
        "tag-other": tags_root / "tag-other.md",
    }
    records = {
        "tag-a": (
            {
                "doc_id": "tag-a",
                "title": "Tag A",
                "added_date": "2026-07-01 10:00:00",
                "last_updated": "2026-07-29 10:00:00",
                "summary": "Original Tag A summary.",
                "ui_status": "draft",
                "group": "theme",
                "viewable": False,
            },
            "# Tag A\n",
        ),
        "tag-b": (
            {
                "doc_id": "tag-b",
                "title": "Tag B",
                "added_date": "2026-07-02 10:00:00",
                "last_updated": "2026-07-29 11:00:00",
                "ui_status": "done",
                "group": "theme",
            },
            "# Tag B\n",
        ),
        "tag-other": (
            {
                "doc_id": "tag-other",
                "title": "Other Tag",
                "added_date": "2026-07-03 10:00:00",
                "last_updated": "2026-07-29 12:00:00",
                "ui_status": "draft",
                "group": "theme",
            },
            "# Other Tag\n",
        ),
    }
    for doc_id, path in targets.items():
        front_matter, body = records[doc_id]
        path.write_text(
            docs_source_model.format_source(front_matter, body),
            encoding="utf-8",
        )
    return targets


def write_review_sub_scope_fixture(root: Path) -> Path:
    return write_review_source_fixture(
        root,
        staged_folder="edited-tags-review",
        folder_id=SUB_REVIEW_FOLDER_ID,
        export_id=SUB_REVIEW_EXPORT_ID,
        scope="library",
        sub_scope="tags",
        records=[("tag-a", "Tag A"), ("tag-b", "Tag B")],
        source_last_updated={
            "tag-a": "2026-07-29 10:00:00",
            "tag-b": "2026-07-29 11:00:00",
        },
    )


def edit_review_alpha(
    staged_folder: Path,
    *,
    parent_id: str = "library",
) -> None:
    path = staged_folder / "alpha.md"
    inserted_parent = f"parent_id: {parent_id}\n" if parent_id else ""
    path.write_text(
        path.read_text(encoding="utf-8")
        .replace("title: Alpha", "title: Edited Alpha")
        .replace(
            "---\n# Alpha",
            "summary: Edited Alpha summary.\n"
            f"{inserted_parent}"
            "viewable: false\n"
            "---\n"
            "# Edited Alpha\n\nEdited reviewed body.",
        ),
        encoding="utf-8",
    )


def edit_review_tag_a(staged_folder: Path, *, parent_id: str = "") -> None:
    path = staged_folder / "tag-a.md"
    inserted_parent = f"parent_id: {parent_id}\n" if parent_id else ""
    path.write_text(
        path.read_text(encoding="utf-8")
        .replace("title: Tag A", "title: Edited Tag A")
        .replace(
            "---\n# Tag A",
            "summary: Edited Tag A summary.\n"
            f"{inserted_parent}"
            "viewable: true\n"
            "---\n"
            "# Edited Tag A\n\nEdited tag body.",
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


def reviewed_scope_preview(root: Path, staged_filename: str) -> dict[str, object]:
    return docs_management_import_service.handle_import_source(
        root,
        {
            "scope": "library",
            "staged_filename": staged_filename,
            "preview_only": True,
        },
        dry_run=False,
    )


def reviewed_scope_apply(
    root: Path,
    staged_filename: str,
    preview: dict[str, object],
) -> dict[str, object]:
    package = preview["package"]
    assert isinstance(package, dict)
    return docs_management_import_service.handle_import_source(
        root,
        {
            "scope": "library",
            "staged_filename": staged_filename,
            "preview_only": False,
            "confirm": True,
            "export_id": package["export_id"],
            "source_sha256": package["source_sha256"],
            "trusted_metadata_sha256": package["trusted_metadata_sha256"],
            "planned_identities": preview["planned_identities"],
            "planned_actions": preview["planned_actions"],
        },
        dry_run=False,
    )


def reviewed_sub_scope_preview(
    root: Path,
    staged_filename: str,
    *,
    sub_scope: str = "tags",
) -> dict[str, object]:
    return docs_management_import_service.handle_import_source(
        root,
        {
            "scope": "library",
            "sub_scope": sub_scope,
            "staged_filename": staged_filename,
            "preview_only": True,
        },
        dry_run=False,
    )


def reviewed_sub_scope_apply(
    root: Path,
    staged_filename: str,
    preview: dict[str, object],
) -> dict[str, object]:
    package = preview["package"]
    assert isinstance(package, dict)
    return docs_management_import_service.handle_import_source(
        root,
        {
            "scope": "library",
            "sub_scope": "tags",
            "staged_filename": staged_filename,
            "preview_only": False,
            "confirm": True,
            "export_id": package["export_id"],
            "source_sha256": package["source_sha256"],
            "trusted_metadata_sha256": package["trusted_metadata_sha256"],
            "planned_identities": preview["planned_identities"],
            "planned_actions": preview["planned_actions"],
        },
        dry_run=False,
    )


def test_source_import_files_list_registered_document_formats() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged_html(root, "source.html", "<html><body><h1>Source</h1></body></html>")
        write_staged_markdown(root, "source.md", "# Source\n")
        write_staged_text(root, "source.txt", "Source\n")
        write_staged_bytes(root, "source.docx", semantic_docx_bytes())
        write_staged_text(root, "source.svg", "<svg viewBox='0 0 10 10'></svg>\n")
        write_staged_bytes(root, "source.png", b"fake image")
        write_staged_bytes(root, "source.pdf", b"fake pdf")
        write_staged_package_file(root, "package-note", "Note.md", "# Package Note\n")

        files = import_source_service.handle_import_source_files(root)["files"]

    by_filename = {item["filename"]: item for item in files}
    assert by_filename["source.html"]["source_format"] == "html"
    assert by_filename["source.md"]["source_format"] == "markdown"
    assert by_filename["source.txt"]["source_format"] == "text"
    assert by_filename["source.docx"]["source_format"] == "docx"
    assert ".docx" in FILE_MEDIA_STAGED_SUFFIXES
    assert by_filename["package-note"]["source_format"] == "markdown_package"
    assert by_filename["package-note"]["package_markdown_count"] == 1
    assert by_filename["source.md"]["path"] == "$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-staging/source.md"
    assert {"source.svg", "source.png", "source.pdf"}.isdisjoint(by_filename)


def test_source_import_lists_valid_edited_review_folder_with_display_identity() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_review_source_fixture(root)

        files = import_source_service.handle_import_source_files(root)["files"]

    by_filename = {item["filename"]: item for item in files}
    reviewed = by_filename["edited-review-copy"]
    assert reviewed["source_format"] == (
        docs_import_review_source_folder.EDITED_REVIEW_SOURCE_FORMAT
    )
    assert reviewed["display_name"] == f"{REVIEW_FOLDER_ID} (reviewed)"
    assert reviewed["filename"] == "edited-review-copy"
    assert reviewed["review_folder_id"] == REVIEW_FOLDER_ID
    assert reviewed["document_count"] == 2


def test_app_level_candidate_projection_is_global_body_free_and_recognizer_first() -> None:
    with make_repo() as temp:
        root = Path(temp)
        configure_review_sub_scope_targets(root)
        write_staged_markdown(root, "ordinary.md", "# Ordinary\n")
        write_staged_package_file(
            root,
            "multiple-markdown",
            "one.md",
            "# One\n",
        )
        write_staged_package_file(
            root,
            "multiple-markdown",
            "two.md",
            "# Two\n",
        )
        write_staged_bytes(root, "standalone.png", b"not imported")
        write_returned_jsonl(
            root,
            "returned-documents.jsonl",
            [
                {
                    "doc_id": "returned-doc",
                    "title": "Returned Doc",
                    "content": "Returned body must not enter the listing.",
                },
            ],
            export_id="ds_20260730T171500Z",
        )
        edited = write_review_sub_scope_fixture(root)
        paths = configured_workspace_paths(root)
        standalone_review = paths.import_staging / "tag-a-reviewed.md"
        standalone_review.write_text(
            (edited / "tag-a.md").read_text(encoding="utf-8"),
            encoding="utf-8",
        )

        payload = import_source_service.handle_import_source_files(root)

    candidates = {
        item["filename"]: item
        for item in payload["candidates"]
    }
    assert set(candidates) == {
        "edited-tags-review",
        "multiple-markdown",
        "ordinary.md",
        "returned-documents.jsonl",
        "tag-a-reviewed.md",
    }
    assert "standalone.png" not in candidates
    ordinary = candidates["ordinary.md"]
    assert ordinary["candidate_kind"] == "ordinary_document"
    assert ordinary["validation_state"] == "ready"
    assert ordinary["target_mode"] == "ordinary_context"
    assert ordinary["target"] is None
    assert ordinary["supports_docs_review"] is False
    assert ordinary["supports_return_import"] is False
    assert ordinary["docs_review_enabled"] is False
    assert ordinary["import_enabled"] is True
    assert ordinary["diagnostics"] == []
    returned = candidates["returned-documents.jsonl"]
    assert returned["candidate_kind"] == "returned_package"
    assert returned["target_mode"] == "manifest_collection"
    assert returned["target"] == {"scope": "library"}
    assert returned["target_label"] == "Library"
    assert returned["docs_review_enabled"] is True
    assert returned["import_enabled"] is True
    assert returned["document_count"] == 1
    assert {"records", "source_metadata", "content"}.isdisjoint(returned)

    reviewed = candidates["edited-tags-review"]
    assert reviewed["candidate_kind"] == "edited_review_source"
    assert reviewed["target"] == {
        "scope": "library",
        "sub_scope": "tags",
    }
    assert reviewed["target_label"] == "Library / Tags"
    assert reviewed["docs_review_enabled"] is False
    assert reviewed["import_enabled"] is True
    assert "records" not in reviewed

    incomplete = candidates["tag-a-reviewed.md"]
    assert incomplete["candidate_kind"] == "edited_review_source"
    assert incomplete["validation_state"] == "blocked"
    assert incomplete["disabled_reason"] == "incomplete_edited_review_source"
    assert incomplete["source_format"] == "edited_review_sources"
    multi_markdown = candidates["multiple-markdown"]
    assert multi_markdown["candidate_kind"] == "ordinary_document"
    assert multi_markdown["validation_state"] == "blocked"
    assert multi_markdown["disabled_reason"] == (
        "invalid_ordinary_markdown_folder"
    )


def test_app_level_candidate_projection_keeps_safe_blocked_package_diagnostics() -> None:
    with make_repo() as temp:
        root = Path(temp)
        paths = configured_workspace_paths(root)
        write_staged(
            root,
            "missing-metadata.jsonl",
            [
                {
                    "record_type": "data_sharing_header",
                    "export_id": "ds_20260730T171501Z",
                },
                {
                    "doc_id": "alpha",
                    "title": "Alpha",
                },
            ],
        )
        write_staged(
            root,
            "unrelated.json",
            {"kind": "not-a-documents-package"},
        )
        write_returned_jsonl(
            root,
            "20260730-181500-documents-document-content.jsonl",
            [
                {
                    "doc_id": "returned-doc",
                    "title": "Returned Doc",
                    "content": "Body.",
                },
            ],
            export_id="ds_20260730T171500Z",
        )
        old_folder_id = "20260730-105512-documents-document-content"
        write_review_source_fixture(
            root,
            staged_folder="retired-review-name",
            folder_id=old_folder_id,
        )

        payload = import_source_service.handle_import_source_files(root)

    candidates = {
        item["filename"]: item
        for item in payload["candidates"]
    }
    assert "unrelated.json" not in candidates
    retired_package = candidates[
        "20260730-181500-documents-document-content.jsonl"
    ]
    assert retired_package["validation_state"] == "blocked"
    assert retired_package["docs_review_enabled"] is False
    assert retired_package["import_enabled"] is False
    assert retired_package["disabled_reason"] == "retired_package_filename"
    missing = candidates["missing-metadata.jsonl"]
    assert missing["candidate_kind"] == "returned_package"
    assert missing["validation_state"] == "blocked"
    assert missing["disabled_reason"] == "untrusted_package_metadata"
    assert missing["diagnostics"] == [
        {
            "code": "untrusted_package_metadata",
            "message": (
                "Trusted export metadata is unavailable for this claimed package."
            ),
        }
    ]
    retired = candidates["retired-review-name"]
    assert retired["candidate_kind"] == "edited_review_source"
    assert retired["validation_state"] == "blocked"
    assert retired["disabled_reason"] == "invalid_edited_review_source"
    assert "retired review_folder_id" in retired["diagnostics"][0]["message"]
    assert str(paths.root) not in retired["diagnostics"][0]["message"]


@pytest.mark.parametrize(
    ("case", "error"),
    (
        ("incomplete", "selected_doc_ids does not match"),
        ("mixed", "added_date must be a non-blank string"),
        ("non-importable", "supports_return_import must be true"),
        ("nested", "only direct Markdown files"),
        ("unsupported", "unsupported entries"),
        ("duplicate-field", "duplicate front matter fields"),
        ("mixed-provenance", "one consistent review_source_export_id"),
        ("missing-source-version", "source_last_updated membership"),
        ("symlink", "must not contain symlinks"),
    ),
)
def test_source_import_blocks_invalid_edited_review_folders(
    case: str,
    error: str,
) -> None:
    with make_repo() as temp:
        root = Path(temp)
        staged_folder = f"{case}-review"
        staged = write_review_source_fixture(
            root,
            staged_folder=staged_folder,
            supports_return_import=case != "non-importable",
        )
        paths = configured_workspace_paths(root)
        if case == "incomplete":
            (staged / "beta.md").unlink()
        elif case == "mixed":
            (staged / "ordinary.md").write_text(
                "---\ndoc_id: ordinary\ntitle: Ordinary\n---\nBody\n",
                encoding="utf-8",
            )
        elif case == "nested":
            nested = staged / "nested"
            nested.mkdir()
            (staged / "beta.md").rename(nested / "beta.md")
        elif case == "unsupported":
            (staged / "notes.txt").write_text("not a source\n", encoding="utf-8")
        elif case == "duplicate-field":
            alpha = staged / "alpha.md"
            alpha.write_text(
                alpha.read_text(encoding="utf-8").replace(
                    "---\n# Alpha",
                    f"review_folder_id: {REVIEW_FOLDER_ID}\n---\n# Alpha",
                ),
                encoding="utf-8",
            )
        elif case == "mixed-provenance":
            alpha = staged / "alpha.md"
            alpha.write_text(
                alpha.read_text(encoding="utf-8").replace(
                    REVIEW_EXPORT_ID,
                    "ds_20260730T095513Z",
                ),
                encoding="utf-8",
            )
        elif case == "missing-source-version":
            metadata_path = paths.meta / f"{REVIEW_EXPORT_ID}.meta.json"
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            metadata["source_last_updated"].pop("beta")
            metadata_path.write_text(
                json.dumps(metadata) + "\n",
                encoding="utf-8",
            )
        elif case == "symlink":
            (staged / "linked.md").symlink_to(
                paths.import_preview / REVIEW_FOLDER_ID / "source/alpha.md",
            )

        with pytest.raises(ValueError, match=error):
            docs_import_review_source_folder.recognize_edited_review_source_folder(
                root,
                candidate=staged,
                staging_root=paths.import_staging,
                metadata_root=paths.meta,
            )
        files = import_source_service.handle_import_source_files(root)["files"]

    assert staged_folder not in {
        item["filename"]
        for item in files
    }


def test_source_import_rejects_review_file_and_plans_folder_before_generic_markdown() -> None:
    with make_repo() as temp:
        root = Path(temp)
        staged_folder = write_review_source_fixture(root)
        paths = configured_workspace_paths(root)
        standalone = paths.import_staging / "alpha-reviewed.md"
        standalone.write_text(
            (staged_folder / "alpha.md").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        destination = resolve_managed_document_collection(
            root,
            scope="library",
        )

        with pytest.raises(
            ValueError,
            match="Stage and select the complete edited review source folder",
        ):
            import_source_service.handle_import_source(
                root,
                {
                    "scope": "library",
                    "staged_filename": "alpha-reviewed.md",
                },
                True,
                import_dependencies(),
                staging_root=paths.import_staging,
                workspace_root=paths.root,
                metadata_root=paths.meta,
                destination=destination,
            )
        preview = import_source_service.handle_import_source(
            root,
            {
                "scope": "library",
                "staged_filename": staged_folder.name,
                "preview_only": True,
            },
            True,
            import_dependencies(),
            staging_root=paths.import_staging,
            workspace_root=paths.root,
            metadata_root=paths.meta,
            destination=destination,
        )

    assert preview["collection"] is True
    assert preview["source_format"] == "edited_review_sources"
    assert preview["target"] == {"scope": "library"}
    assert preview["ready_for_confirmation"] is False
    assert {
        blocker["code"]
        for blocker in preview["blockers"]
    } >= {"stale_prepared_sources", "overwrite_target_missing"}


def test_edited_review_scope_preview_is_write_free_exact_and_overwrite_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stub_markdown_validation(monkeypatch)
    with make_repo() as temp:
        root = Path(temp)
        targets = write_review_scope_targets(root)
        staged_folder = write_review_source_fixture(root)
        edit_review_alpha(staged_folder)
        originals = {
            doc_id: path.read_bytes()
            for doc_id, path in targets.items()
        }

        preview = reviewed_scope_preview(root, staged_folder.name)

        assert {
            doc_id: path.read_bytes()
            for doc_id, path in targets.items()
        } == originals

    assert preview["ready_for_confirmation"] is True
    assert preview["source_format"] == "edited_review_sources"
    assert preview["target"] == {"scope": "library"}
    assert preview["staged_filename"] == "edited-review-copy"
    assert preview["planned_identities"] == []
    assert [record["action"] for record in preview["records"]] == [
        "overwrite",
        "overwrite",
    ]
    assert preview["counts"]["creates"] == 0
    assert preview["counts"]["collisions"] == 2
    assert preview["warnings"] == [
        {
            "level": "warning",
            "code": "derived_markdown_fidelity",
            "message": (
                "Edited review sources are derived Markdown. Rich content, "
                "tokens, comments, raw embeds, source formatting, and package "
                "assets may not survive this import."
            ),
        }
    ]
    package = preview["package"]
    assert package["review_folder_id"] == REVIEW_FOLDER_ID
    assert package["export_id"] == REVIEW_EXPORT_ID
    assert package["document_count"] == 2
    assert package["source_last_updated"] == {
        "alpha": "2026-07-29 12:00:00",
        "beta": "2026-07-29 12:00:00",
    }
    assert "added_date" not in package
    assert "last_updated" not in package


def test_edited_review_scope_apply_preserves_authority_and_refreshes_scope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stub_markdown_validation(monkeypatch)
    boundary_calls: list[dict[str, object]] = []

    def atomic_scope_boundary(
        repo_root,
        scope,
        changed_paths,
        write_operation,
        **kwargs,
    ):
        snapshots = kwargs["source_snapshots"]
        assert set(path.resolve() for path in changed_paths) == set(snapshots)
        write_operation()
        boundary_calls.append(
            {
                "scope": scope,
                "changed_paths": [path.name for path in changed_paths],
                "docs_doc_ids": list(kwargs.get("docs_doc_ids") or []),
                "search_doc_ids": list(kwargs.get("search_doc_ids") or []),
                "reason": kwargs.get("suppression_reason"),
            }
        )
        return {
            "ok": True,
            "docs": {
                "mode": "targeted",
                "doc_ids": list(kwargs.get("docs_doc_ids") or []),
            },
            "search": {
                "mode": "targeted",
                "doc_ids": list(kwargs.get("search_doc_ids") or []),
            },
        }

    monkeypatch.setattr(
        docs_write_rebuild,
        "perform_scope_source_write_and_rebuild_atomic",
        atomic_scope_boundary,
    )
    with make_repo() as temp:
        root = Path(temp)
        targets = write_review_scope_targets(root)
        staged_folder = write_review_source_fixture(root)
        edit_review_alpha(staged_folder)

        preview = reviewed_scope_preview(root, staged_folder.name)
        payload = reviewed_scope_apply(root, staged_folder.name, preview)
        alpha_front_matter, alpha_body = docs_source_model.parse_source(
            targets["alpha"],
        )
        beta_front_matter, beta_body = docs_source_model.parse_source(
            targets["beta"],
        )

    assert payload["outcome"] == "completed"
    assert payload["target"] == {"scope": "library"}
    assert payload["counts"] == {
        "created": 0,
        "overwritten": 2,
        "failed": 0,
        "not_attempted": 0,
    }
    assert payload["rollback"]["status"] == "not-needed"
    assert boundary_calls == [
        {
            "scope": "library",
            "changed_paths": ["alpha.md", "beta.md"],
            "docs_doc_ids": ["alpha", "beta"],
            "search_doc_ids": ["alpha", "beta"],
            "reason": "docs-import-reviewed-scope-collection-apply",
        }
    ]
    assert alpha_front_matter["doc_id"] == "alpha"
    assert alpha_front_matter["added_date"] == "2026-07-01 10:00:00"
    assert alpha_front_matter["group"] == "protected-alpha"
    assert alpha_front_matter["ui_status"] == "draft"
    assert alpha_front_matter["title"] == "Edited Alpha"
    assert alpha_front_matter["summary"] == "Edited Alpha summary."
    assert alpha_front_matter["parent_id"] == "library"
    assert alpha_front_matter["viewable"] is False
    assert alpha_front_matter["last_updated"] not in {
        "2026-07-29 12:00:00",
        "2026-07-30",
    }
    assert "Edited reviewed body." in alpha_body
    assert beta_front_matter["doc_id"] == "beta"
    assert beta_front_matter["added_date"] == "2026-07-02 10:00:00"
    assert beta_front_matter["group"] == "protected-beta"
    assert beta_front_matter["ui_status"] == "done"
    assert beta_front_matter["last_updated"] == "2026-07-29 12:00:00"
    assert beta_body.strip() == "# Beta"


def test_edited_review_scope_revalidates_versions_and_folder_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stub_markdown_validation(monkeypatch)
    with make_repo() as temp:
        root = Path(temp)
        targets = write_review_scope_targets(root)
        staged_folder = write_review_source_fixture(root)
        preview = reviewed_scope_preview(root, staged_folder.name)
        targets["alpha"].write_text(
            targets["alpha"].read_text(encoding="utf-8").replace(
                "last_updated: \"2026-07-29 12:00:00\"",
                "last_updated: \"2026-07-30 21:00:00\"",
            ),
            encoding="utf-8",
        )

        stale = reviewed_scope_apply(root, staged_folder.name, preview)

        write_review_scope_targets(root)
        refreshed_preview = reviewed_scope_preview(root, staged_folder.name)
        (staged_folder / "alpha.md").write_text(
            (staged_folder / "alpha.md").read_text(encoding="utf-8")
            + "\nEdited after preview.\n",
            encoding="utf-8",
        )
        changed_folder = reviewed_scope_apply(
            root,
            staged_folder.name,
            refreshed_preview,
        )

    assert stale["preview_only"] is True
    assert stale["reconfirmation_required"] is True
    assert stale["ready_for_confirmation"] is False
    assert "stale_prepared_sources" in {
        blocker["code"]
        for blocker in stale["blockers"]
    }
    assert changed_folder["preview_only"] is True
    assert changed_folder["reconfirmation_required"] is True
    assert changed_folder["revalidation_issues"][0]["code"] == (
        "package_identity_changed"
    )


def test_edited_review_scope_rechecks_snapshot_inside_write_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stub_markdown_validation(monkeypatch)
    original_boundary = (
        docs_write_rebuild.perform_scope_source_write_and_rebuild_atomic
    )
    raced = False

    def race_boundary(
        repo_root,
        scope,
        changed_paths,
        write_operation,
        **kwargs,
    ):
        nonlocal raced
        snapshots = kwargs["source_snapshots"]
        if not raced:
            raced = True
            first_path = next(iter(snapshots))
            first_path.write_text(
                first_path.read_text(encoding="utf-8")
                + "\nExternal concurrent edit.\n",
                encoding="utf-8",
            )
        return original_boundary(
            repo_root,
            scope,
            changed_paths,
            write_operation,
            **kwargs,
        )

    monkeypatch.setattr(
        docs_write_rebuild,
        "perform_scope_source_write_and_rebuild_atomic",
        race_boundary,
    )
    with make_repo() as temp:
        root = Path(temp)
        targets = write_review_scope_targets(root)
        staged_folder = write_review_source_fixture(root)
        edit_review_alpha(staged_folder)
        preview = reviewed_scope_preview(root, staged_folder.name)

        refreshed = reviewed_scope_apply(root, staged_folder.name, preview)
        source_after = targets["alpha"].read_text(encoding="utf-8")

    assert raced is True
    assert refreshed["preview_only"] is True
    assert refreshed["reconfirmation_required"] is True
    assert refreshed["revalidation_issues"][0]["code"] == "target_state_changed"
    assert "External concurrent edit." in source_after
    assert "Edited reviewed body." not in source_after


@pytest.mark.parametrize("failure_mode", ["source-write", "rebuild"])
def test_edited_review_scope_failure_restores_every_source_and_projection(
    monkeypatch: pytest.MonkeyPatch,
    failure_mode: str,
) -> None:
    stub_markdown_validation(monkeypatch)
    original_apply = docs_import_collection_apply.apply_import_document_source
    source_write_count = 0
    rebuild_count = 0

    def apply_source(document_plan):
        nonlocal source_write_count
        source_write_count += 1
        if failure_mode == "source-write" and source_write_count == 2:
            raise RuntimeError("simulated second source-write failure")
        original_apply(document_plan)

    def rebuild_scope(
        repo_root,
        scope,
        *,
        include_search,
        search_doc_ids,
        docs_doc_ids,
        skip_media_builds,
    ):
        nonlocal rebuild_count
        rebuild_count += 1
        if failure_mode == "rebuild" and rebuild_count == 1:
            raise RuntimeError("simulated scope rebuild failure")
        return {
            "ok": True,
            "docs": {
                "mode": "targeted",
                "doc_ids": list(docs_doc_ids or []),
            },
            "search": {
                "mode": "targeted",
                "doc_ids": list(search_doc_ids or []),
            },
        }

    monkeypatch.setattr(
        docs_import_collection_apply,
        "apply_import_document_source",
        apply_source,
    )
    monkeypatch.setattr(
        docs_write_rebuild,
        "rebuild_scope_outputs",
        rebuild_scope,
    )
    with make_repo() as temp:
        root = Path(temp)
        targets = write_review_scope_targets(root)
        staged_folder = write_review_source_fixture(root)
        edit_review_alpha(staged_folder)
        originals = {
            doc_id: path.read_bytes()
            for doc_id, path in targets.items()
        }
        preview = reviewed_scope_preview(root, staged_folder.name)

        payload = reviewed_scope_apply(root, staged_folder.name, preview)
        restored = {
            doc_id: path.read_bytes()
            for doc_id, path in targets.items()
        }

    assert restored == originals
    assert payload["outcome"] == "generation-failed"
    assert payload["counts"] == {
        "created": 0,
        "overwritten": 0,
        "failed": 2,
        "not_attempted": 0,
    }
    assert payload["rollback"]["status"] == "completed"
    assert payload["rollback"]["sources_restored"] is True
    assert rebuild_count == (1 if failure_mode == "source-write" else 2)


def test_edited_review_sub_scope_preview_apply_and_discovery_are_exact(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stub_markdown_validation(monkeypatch)
    boundary_calls: list[dict[str, object]] = []

    def child_boundary(
        repo_root,
        scope,
        sub_scope,
        changed_paths,
        write_operation,
        **kwargs,
    ):
        write_operation()
        boundary_calls.append(
            {
                "scope": scope,
                "sub_scope": sub_scope,
                "changed_paths": [path.name for path in changed_paths],
                "reason": kwargs.get("suppression_reason"),
                "snapshots": sorted(
                    path.name
                    for path in kwargs.get("source_snapshots") or {}
                ),
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
        "perform_sub_scope_source_write_and_rebuild",
        child_boundary,
    )
    with make_repo() as temp:
        root = Path(temp)
        targets = configure_review_sub_scope_targets(root)
        staged_folder = write_review_sub_scope_fixture(root)
        edit_review_tag_a(staged_folder)
        untouched = {
            key: path.read_bytes()
            for key, path in targets.items()
            if key not in {"tag-a", "tag-b"}
        }
        public_projection = (
            root / "site/assets/data/docs/scopes/library/tags"
        )

        listing = import_source_service.handle_import_source_files(root)
        assert public_projection.exists() is False
        preview = reviewed_sub_scope_preview(root, staged_folder.name)
        assert public_projection.exists() is False
        payload = reviewed_sub_scope_apply(root, staged_folder.name, preview)
        tag_a_front_matter, tag_a_body = docs_source_model.parse_source(
            targets["tag-a"],
        )
        tag_b_front_matter, tag_b_body = docs_source_model.parse_source(
            targets["tag-b"],
        )
        untouched_after = {
            key: path.read_bytes()
            for key, path in targets.items()
            if key not in {"tag-a", "tag-b"}
        }

    reviewed_listing = next(
        record
        for record in listing["files"]
        if record["filename"] == staged_folder.name
    )
    assert reviewed_listing["display_name"] == (
        f"{SUB_REVIEW_FOLDER_ID} (reviewed)"
    )
    assert reviewed_listing["scope"] == "library"
    assert reviewed_listing["sub_scope"] == "tags"
    assert reviewed_listing["supports_return_import"] is True
    assert preview["ready_for_confirmation"] is True
    assert preview["target"] == {"scope": "library", "sub_scope": "tags"}
    assert preview["planned_identities"] == []
    assert [record["action"] for record in preview["records"]] == [
        "overwrite",
        "overwrite",
    ]
    assert payload["outcome"] == "completed"
    assert payload["target"] == {"scope": "library", "sub_scope": "tags"}
    assert payload["rollback"]["status"] == "not-needed"
    assert boundary_calls == [
        {
            "scope": "library",
            "sub_scope": "tags",
            "changed_paths": ["tag-a.md", "tag-b.md"],
            "reason": "docs-import-sub-scope-collection-apply",
            "snapshots": ["tag-a.md", "tag-b.md"],
        }
    ]
    assert tag_a_front_matter["doc_id"] == "tag-a"
    assert tag_a_front_matter["added_date"] == "2026-07-01 10:00:00"
    assert tag_a_front_matter["group"] == "theme"
    assert tag_a_front_matter["ui_status"] == "draft"
    assert tag_a_front_matter["viewable"] is False
    assert tag_a_front_matter["title"] == "Edited Tag A"
    assert tag_a_front_matter["summary"] == "Edited Tag A summary."
    assert "parent_id" not in tag_a_front_matter
    assert tag_a_front_matter["last_updated"] != "2026-07-29 10:00:00"
    assert "Edited tag body." in tag_a_body
    assert tag_b_front_matter["last_updated"] == "2026-07-29 11:00:00"
    assert tag_b_body.strip() == "# Tag B"
    assert untouched_after == untouched


def test_edited_review_sub_scope_rejects_parent_fallback_and_non_flat_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stub_markdown_validation(monkeypatch)
    with make_repo() as temp:
        root = Path(temp)
        targets = configure_review_sub_scope_targets(root)
        staged_folder = write_review_sub_scope_fixture(root)
        originals = {
            key: path.read_bytes()
            for key, path in targets.items()
        }

        with pytest.raises(
            ValueError,
            match="belongs to collection 'library/tags', not 'library/notes'",
        ):
            reviewed_sub_scope_preview(
                root,
                staged_folder.name,
                sub_scope="notes",
            )
        with pytest.raises(
            ValueError,
            match="belongs to collection 'library/tags', not 'library'",
        ):
            reviewed_scope_preview(root, staged_folder.name)

        edit_review_tag_a(staged_folder, parent_id="tag-b")
        source_hierarchy = reviewed_sub_scope_preview(
            root,
            staged_folder.name,
        )

        staged_folder = write_review_sub_scope_fixture(root)
        targets["tag-b"].write_text(
            targets["tag-b"].read_text(encoding="utf-8").replace(
                "---\n# Tag B",
                "parent_id: tag-a\n---\n# Tag B",
            ),
            encoding="utf-8",
        )
        non_flat_target = reviewed_sub_scope_preview(
            root,
            staged_folder.name,
        )
        after = {
            key: path.read_bytes()
            for key, path in targets.items()
        }

    assert "sub_scope_hierarchy_not_allowed" in {
        blocker["code"]
        for blocker in source_hierarchy["blockers"]
    }
    assert "non_flat_sub_scope_target" in {
        blocker["code"]
        for blocker in non_flat_target["blockers"]
    }
    assert {
        key: value
        for key, value in after.items()
        if key != "tag-b"
    } == {
        key: value
        for key, value in originals.items()
        if key != "tag-b"
    }


def test_edited_review_sub_scope_rebuild_failure_restores_only_exact_collection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stub_markdown_validation(monkeypatch)
    rebuild_count = 0

    def rebuild_sub_scope(repo_root, scope, sub_scope):
        nonlocal rebuild_count
        rebuild_count += 1
        if rebuild_count == 1:
            raise RuntimeError("simulated confined rebuild failure")
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
        "rebuild_sub_scope_outputs",
        rebuild_sub_scope,
    )
    with make_repo() as temp:
        root = Path(temp)
        targets = configure_review_sub_scope_targets(root)
        staged_folder = write_review_sub_scope_fixture(root)
        edit_review_tag_a(staged_folder)
        originals = {
            key: path.read_bytes()
            for key, path in targets.items()
        }
        preview = reviewed_sub_scope_preview(root, staged_folder.name)

        payload = reviewed_sub_scope_apply(
            root,
            staged_folder.name,
            preview,
        )
        after = {
            key: path.read_bytes()
            for key, path in targets.items()
        }

    assert after == originals
    assert rebuild_count == 2
    assert payload["outcome"] == "generation-failed"
    assert payload["target"] == {"scope": "library", "sub_scope": "tags"}
    assert payload["counts"] == {
        "created": 0,
        "overwritten": 0,
        "failed": 2,
        "not_attempted": 0,
    }
    assert payload["rollback"]["status"] == "completed"
    assert payload["rollback"]["sources_restored"] is True


def test_edited_review_scope_and_analysis_tags_round_trip_render_end_to_end(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stub_markdown_validation(monkeypatch)

    class FixtureDocsDataBuilder(DocsDataBuilder):
        def validate_canonical_doc_ids(self, docs):
            del docs

    class FixtureSubScopeDocsBuilder(SubScopeDocsBuilder):
        def validate_canonical_doc_ids(self, docs):
            del docs

        def parent_report_doc_id(self):
            return ""

    def build_scope_after_write(
        repo_root,
        scope,
        changed_paths,
        write_operation,
        **kwargs,
    ):
        del changed_paths, kwargs
        write_operation()
        config = load_docs_scope_configs(repo_root)[scope]
        FixtureDocsDataBuilder(
            repo_root=repo_root,
            config=config,
        ).run(write=True)
        return {
            "ok": True,
            "docs": {"mode": "full", "doc_ids": []},
            "search": {"mode": "none", "doc_ids": []},
        }

    def build_child_after_write(
        repo_root,
        scope,
        sub_scope,
        changed_paths,
        write_operation,
        **kwargs,
    ):
        del changed_paths, kwargs
        write_operation()
        config = load_docs_scope_configs(repo_root)[scope]
        FixtureSubScopeDocsBuilder(
            repo_root=repo_root,
            config=config,
            sub_scope=selected_sub_scope(config, sub_scope),
        ).run(write=True)
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
        "perform_scope_source_write_and_rebuild_atomic",
        build_scope_after_write,
    )
    monkeypatch.setattr(
        docs_write_rebuild,
        "perform_sub_scope_source_write_and_rebuild",
        build_child_after_write,
    )
    with make_repo() as temp:
        root = Path(temp)
        scope_targets = write_review_scope_targets(root)
        child_targets = configure_analysis_tags_round_trip_targets(root)
        paths = configured_workspace_paths(root)
        write_staged_markdown(root, "ordinary.md", "# Ordinary staged source\n")
        write_returned_jsonl(
            root,
            "returned-documents.jsonl",
            [
                {
                    "doc_id": "returned-doc",
                    "title": "Returned document",
                    "content": "Returned package body.",
                }
            ],
            export_id="ds_20260730T191500Z",
        )
        ordinary_source = paths.import_staging / "ordinary.md"
        returned_source = paths.import_staging / "returned-documents.jsonl"
        staged_sentinels = {
            ordinary_source: ordinary_source.read_bytes(),
            returned_source: returned_source.read_bytes(),
        }

        scope_staged = write_review_source_fixture(
            root,
            staged_folder="scope-reviewed-round-trip",
        )
        scope_retained = paths.import_preview / REVIEW_FOLDER_ID / "source"
        edit_review_alpha(scope_retained, parent_id="")
        scope_review_source = scope_retained / "alpha.md"
        scope_review_bytes = scope_review_source.read_bytes()
        scope_canonical_before_build = {
            doc_id: path.read_bytes()
            for doc_id, path in scope_targets.items()
        }
        scope_build = docs_review_packages.build_package(
            root,
            {"package_id": REVIEW_FOLDER_ID},
        )
        assert {
            doc_id: path.read_bytes()
            for doc_id, path in scope_targets.items()
        } == scope_canonical_before_build
        scope_review_payload = docs_review_packages.read_payload(
            root,
            REVIEW_FOLDER_ID,
            "alpha",
        )["payload"]
        shutil.copytree(scope_retained, scope_staged, dirs_exist_ok=True)

        scope_listing = import_source_service.handle_import_source_files(root)
        scope_preview = reviewed_scope_preview(root, scope_staged.name)
        scope_apply = reviewed_scope_apply(
            root,
            scope_staged.name,
            scope_preview,
        )
        scope_rendered = json.loads(
            (
                root
                / "docs-viewer/scopes/library/published/documents/by-id/alpha.json"
            ).read_text(encoding="utf-8")
        )

        child_staged = write_review_source_fixture(
            root,
            staged_folder="analysis-tags-reviewed-round-trip",
            folder_id=ANALYSIS_REVIEW_FOLDER_ID,
            export_id=ANALYSIS_REVIEW_EXPORT_ID,
            scope="analysis",
            sub_scope="tags",
            records=[("tag-a", "Tag A"), ("tag-b", "Tag B")],
            source_last_updated={
                "tag-a": "2026-07-29 10:00:00",
                "tag-b": "2026-07-29 11:00:00",
            },
        )
        child_retained = (
            paths.import_preview / ANALYSIS_REVIEW_FOLDER_ID / "source"
        )
        edit_review_tag_a(child_retained)
        child_review_source = child_retained / "tag-a.md"
        child_review_bytes = child_review_source.read_bytes()
        child_canonical_before_build = {
            doc_id: path.read_bytes()
            for doc_id, path in child_targets.items()
        }
        child_build = docs_review_packages.build_package(
            root,
            {"package_id": ANALYSIS_REVIEW_FOLDER_ID},
        )
        assert {
            doc_id: path.read_bytes()
            for doc_id, path in child_targets.items()
        } == child_canonical_before_build
        child_review_payload = docs_review_packages.read_payload(
            root,
            ANALYSIS_REVIEW_FOLDER_ID,
            "tag-a",
        )["payload"]
        shutil.copytree(child_retained, child_staged, dirs_exist_ok=True)

        child_listing = import_source_service.handle_import_source_files(root)
        child_preview = docs_management_import_service.handle_import_source(
            root,
            {
                "scope": "analysis",
                "sub_scope": "tags",
                "staged_filename": child_staged.name,
                "preview_only": True,
            },
            dry_run=False,
        )
        child_package = child_preview["package"]
        assert isinstance(child_package, dict)
        child_apply = docs_management_import_service.handle_import_source(
            root,
            {
                "scope": "analysis",
                "sub_scope": "tags",
                "staged_filename": child_staged.name,
                "preview_only": False,
                "confirm": True,
                "export_id": child_package["export_id"],
                "source_sha256": child_package["source_sha256"],
                "trusted_metadata_sha256": child_package[
                    "trusted_metadata_sha256"
                ],
                "planned_identities": child_preview["planned_identities"],
                "planned_actions": child_preview["planned_actions"],
            },
            dry_run=False,
        )
        child_rendered = json.loads(
            (
                root
                / "docs-viewer/scopes/analysis/published/documents/sub-scopes"
                / "tags/by-id/tag-a.json"
            ).read_text(encoding="utf-8")
        )
        child_front_matter, _child_body = docs_source_model.parse_source(
            child_targets["tag-a"],
        )
        final_listing = import_source_service.handle_import_source_files(root)

        assert scope_build["built"] is True
        assert "Edited reviewed body." in scope_review_payload["content_html"]
        assert scope_review_source.read_bytes() == scope_review_bytes
        assert {
            doc_id: path.read_bytes()
            for doc_id, path in scope_targets.items()
        } != scope_canonical_before_build
        assert scope_apply["outcome"] == "completed"
        assert "Edited reviewed body." in scope_rendered["content_html"]
        assert [warning["code"] for warning in scope_preview["warnings"]] == [
            "derived_markdown_fidelity"
        ]
        assert next(
            record
            for record in scope_listing["files"]
            if record["filename"] == scope_staged.name
        )["display_name"] == f"{REVIEW_FOLDER_ID} (reviewed)"

        assert child_build["built"] is True
        assert "Edited tag body." in child_review_payload["content_html"]
        assert child_review_source.read_bytes() == child_review_bytes
        assert {
            doc_id: path.read_bytes()
            for doc_id, path in child_targets.items()
        } != child_canonical_before_build
        assert child_apply["outcome"] == "completed"
        assert child_apply["target"] == {
            "scope": "analysis",
            "sub_scope": "tags",
        }
        assert "Edited tag body." in child_rendered["content_html"]
        assert [warning["code"] for warning in child_preview["warnings"]] == [
            "derived_markdown_fidelity"
        ]
        assert child_front_matter["group"] == "theme"
        assert child_front_matter["ui_status"] == "draft"
        assert child_front_matter["viewable"] is False
        assert next(
            record
            for record in child_listing["files"]
            if record["filename"] == child_staged.name
        )["display_name"] == (
            f"{ANALYSIS_REVIEW_FOLDER_ID} (reviewed)"
        )
        assert {
            path: path.read_bytes()
            for path in staged_sentinels
        } == staged_sentinels
        final_formats = {
            record["filename"]: record["source_format"]
            for record in final_listing["files"]
        }
        assert final_formats["ordinary.md"] == "markdown"
        assert final_formats["returned-documents.jsonl"] == (
            "data_sharing_documents"
        )


def test_supported_documents_collection_registers_before_generic_json_fallback() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_returned_jsonl(
            root,
            "reviewed-documents.jsonl",
            [{"doc_id": "reviewed-doc", "title": "Reviewed Doc", "content": "Body."}],
            export_id="ds_20260712T150000Z",
        )
        write_staged(root, "ordinary.json", {"kind": "ordinary-attachment"})

        files = import_source_service.handle_import_source_files(root)["files"]

    by_filename = {item["filename"]: item for item in files}
    assert by_filename["reviewed-documents.jsonl"]["source_format"] == "data_sharing_documents"
    assert "ordinary.json" not in by_filename


def test_source_import_ignores_repo_local_staging_and_rejects_traversal() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged_markdown(root, "external.md", "# External\n")
        repo_local = root / "var/docs/import-staging/repo-local.md"
        repo_local.parent.mkdir(parents=True, exist_ok=True)
        repo_local.write_text("# Repo local\n", encoding="utf-8")
        paths = configured_workspace_paths(root)
        outside = root / "outside.md"
        outside.write_text("# Outside\n", encoding="utf-8")
        (paths.import_staging / "linked.md").symlink_to(outside)

        payload = import_source_service.handle_import_source_files(root)
        with pytest.raises(ValueError, match="configured import staging root"):
            docs_import_preview.resolve_staged_import_source(paths.import_staging, "../outside.md")
        with pytest.raises(ValueError, match="must not be symlinks"):
            docs_import_preview.resolve_staged_import_source(paths.import_staging, "linked.md")

    assert payload["available"] is True
    assert payload["staging_root"] == "$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-staging"
    assert [item["filename"] for item in payload["files"]] == ["external.md"]


def test_source_import_listing_reports_unavailable_workspace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_repo() as temp:
        root = Path(temp)
        monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(tmp_path / "missing-projects"))

        payload = import_source_service.handle_import_source_files(root)

    assert payload["ok"] is True
    assert payload["available"] is False
    assert payload["staging_root"] == "$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing"
    assert payload["files"] == []
    assert "does not exist" in payload["message"]


def test_source_import_listing_reports_missing_configured_staging_root() -> None:
    with make_repo() as temp:
        root = Path(temp)
        paths = configured_workspace_paths(root)
        paths.import_staging.rmdir()

        payload = import_source_service.handle_import_source_files(root)

    assert payload["available"] is False
    assert payload["files"] == []
    assert "$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-staging" in payload["message"]

def test_source_import_previews_validate_with_python_renderer() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged_html(root, "source.html", "<html><body><h1>Source</h1><p>Body.</p></body></html>")
        write_staged_markdown(root, "source.md", "# Source\n\n| A | B |\n| - | - |\n| 1 | 2 |\n")
        write_staged_text(root, "source.txt", "Source\n\nSee https://example.com/path.\n")
        write_staged_package_file(root, "package-note", "Note.md", "# Package Note\n\nBody.\n")
        paths = configured_workspace_paths(root)

        previews = [
            docs_import_preview.generate_import_preview(
                root,
                staging_root=paths.import_staging,
                workspace_root=paths.root,
                source_path=docs_import_preview.resolve_staged_import_source(paths.import_staging, staged_filename),
                scope="library",
                include_prompt_meta=False,
            )
            for staged_filename in [
                "source.html",
                "source.md",
                "source.txt",
                "package-note",
            ]
        ]

    source_formats = {preview["source_format"] for preview in previews}
    assert source_formats == {"html", "markdown", "text", "markdown_package"}
    for preview in previews:
        validation = preview["markdown_validation"]
        assert validation["ok"] is True
        assert validation["renderer"] == "studio/shared/python/markdown_renderer.py"
        assert validation["renderer_contract"]["library"] == "markdown-it-py"
        assert validation["sanitizer_boundary"]["import_html"] == "structured conversion plus sanitized SVG media extraction"

def test_media_path_comes_from_scope_config() -> None:
    assert docs_import_media.media_path_for("analysis", "img", "diagram.png") == "docs/analysis/img/diagram.png"
    assert docs_import_media.media_token("analysis", "img", "diagram.png") == "[[media:docs/analysis/img/diagram.png]]"
    assert docs_import_media.media_path_for("analysis", "svg", "diagram.svg") == "docs/analysis/svg/diagram.svg"
    assert docs_import_media.media_token("analysis", "svg", "diagram.svg") == "[[media:docs/analysis/svg/diagram.svg]]"
