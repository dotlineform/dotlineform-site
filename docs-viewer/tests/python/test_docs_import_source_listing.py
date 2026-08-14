#!/usr/bin/env python3
"""Docs source import listing and preview tests."""

from __future__ import annotations

import json
from pathlib import Path
import shutil

import pytest

import docs_import_media
import docs_import_preview
import docs_import_review_source_folder
import docs_import_source_service as import_source_service
import docs_management_import_service
import docs_source_model
from docs_import_common import FILE_MEDIA_STAGED_SUFFIXES
from docs_import_docx_test_support import semantic_docx_bytes
from docs_document_packages.workspace import configured_workspace_paths
from repo_factory import docs_sub_scope_record

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
LIBRARY_TAGS_REPORT_DOC_ID = "d-20260730-190000-000001"


def list_import_sources(
    root: Path,
    source_directory: str = "data-sharing/import-staging",
) -> dict[str, object]:
    return import_source_service.handle_import_source_files(
        root,
        source_directory=source_directory,
    )


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
            analysis_tag_groups=["theme"],
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
    parent_root = root / "docs-viewer/scopes/library/source/documents"
    parent_root.mkdir(parents=True, exist_ok=True)
    (parent_root / f"{LIBRARY_TAGS_REPORT_DOC_ID}.md").write_text(
        docs_source_model.format_source(
            {
                "doc_id": LIBRARY_TAGS_REPORT_DOC_ID,
                "title": "Tags",
            },
            (
                "# Tags\n\n"
                ":::report\n"
                "id: docs_subscope\n"
                "access: public\n"
                "sub_scope: tags\n"
                ":::\n"
            ),
        ),
        encoding="utf-8",
    )
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
                "publishable": False,
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

        files = list_import_sources(root)["files"]

    by_filename = {item["filename"]: item for item in files}
    assert by_filename["source.html"]["source_format"] == "html"
    assert by_filename["source.md"]["source_format"] == "markdown"
    assert by_filename["source.txt"]["source_format"] == "text"
    assert by_filename["source.docx"]["source_format"] == "docx"
    assert ".docx" in FILE_MEDIA_STAGED_SUFFIXES
    assert by_filename["package-note"]["source_format"] == "markdown_package"
    assert by_filename["package-note"]["package_markdown_count"] == 1
    assert by_filename["source.md"]["path"] == "data-sharing/import-staging/source.md"
    assert {"source.svg", "source.png", "source.pdf"}.isdisjoint(by_filename)


def test_source_import_lists_valid_edited_review_folder_with_display_identity() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_review_source_fixture(root)

        files = list_import_sources(root)["files"]

    by_filename = {item["filename"]: item for item in files}
    reviewed = by_filename["edited-review-copy"]
    assert reviewed["source_format"] == (
        docs_import_review_source_folder.EDITED_REVIEW_SOURCE_FORMAT
    )
    assert reviewed["display_name"] == f"{REVIEW_FOLDER_ID} (reviewed)"
    assert reviewed["filename"] == "edited-review-copy"
    assert reviewed["review_folder_id"] == REVIEW_FOLDER_ID
    assert reviewed["document_count"] == 2


def test_edited_review_source_outside_staging_remains_blocked() -> None:
    with make_repo() as temp:
        root = Path(temp)
        staged = write_review_source_fixture(root)
        paths = configured_workspace_paths(root)
        selected = paths.root.parent / "projects/review-source"
        selected.mkdir(parents=True)
        moved = selected / staged.name
        shutil.move(staged, moved)

        listing = list_import_sources(root, "projects/review-source")
        candidate = listing["candidates"][0]
        with pytest.raises(
            ValueError,
            match="must be selected from data-sharing/import-staging",
        ):
            docs_management_import_service.handle_import_source(
                root,
                {
                    "scope": "library",
                    "source_directory": "projects/review-source",
                    "staged_filename": moved.name,
                },
                dry_run=False,
            )

    assert candidate["candidate_kind"] == "edited_review_source"
    assert candidate["validation_state"] == "blocked"
    assert candidate["disabled_reason"] == (
        "trusted_source_requires_import_staging"
    )
    assert candidate["path"] == "projects/review-source/edited-review-copy"


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

        payload = list_import_sources(root)

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

        payload = list_import_sources(root)

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
        files = list_import_sources(root)["files"]

    assert staged_folder not in {
        item["filename"]
        for item in files
    }


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

        files = list_import_sources(root)["files"]

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

        payload = list_import_sources(root)
        with pytest.raises(ValueError, match="selected source directory"):
            docs_import_preview.resolve_staged_import_source(paths.import_staging, "../outside.md")
        with pytest.raises(ValueError, match="must not be symlinks"):
            docs_import_preview.resolve_staged_import_source(paths.import_staging, "linked.md")

    assert payload["available"] is True
    assert payload["staging_root"] == "data-sharing/import-staging"
    assert payload["source_directory"] == "data-sharing/import-staging"
    assert [item["filename"] for item in payload["files"]] == ["external.md"]


def test_source_import_listing_reports_unavailable_workspace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_repo() as temp:
        root = Path(temp)
        monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(tmp_path / "missing-projects"))

        with pytest.raises(
            ValueError,
            match="DOTLINEFORM_PROJECTS_BASE_DIR must identify an existing directory",
        ):
            list_import_sources(root)


def test_source_import_listing_reports_missing_configured_staging_root() -> None:
    with make_repo() as temp:
        root = Path(temp)
        paths = configured_workspace_paths(root)
        paths.import_staging.rmdir()

        with pytest.raises(FileNotFoundError, match="source_directory does not exist"):
            list_import_sources(root)

def test_media_path_comes_from_scope_config() -> None:
    assert docs_import_media.media_path_for("analysis", "img", "diagram.png") == "docs/analysis/img/diagram.png"
    assert docs_import_media.media_token("analysis", "img", "diagram.png") == "[[media:docs/analysis/img/diagram.png]]"
    assert docs_import_media.media_path_for("analysis", "svg", "diagram.svg") == "docs/analysis/svg/diagram.svg"
    assert docs_import_media.media_token("analysis", "svg", "diagram.svg") == "[[media:docs/analysis/svg/diagram.svg]]"
