#!/usr/bin/env python3
"""Exact Projects-directory contracts for Docs Import source selection."""

from __future__ import annotations

import os
from pathlib import Path
import shutil

import pytest

import docs_import_preview
import docs_import_source_service
import docs_management_import_service
import docs_management_read_service
import docs_management_routes
import docs_write_rebuild
from docs_import_candidate_projection import TRUSTED_SOURCE_STAGING_CODE
from docs_import_test_support import (
    make_repo,
    managed_media_path,
    stub_rebuild,
    write_example_doc,
    write_returned_jsonl,
    write_scope_config,
    write_test_image,
)
from docs_document_packages.workspace import configured_workspace_paths


SOURCE_DIRECTORY = "projects/import-source"


def projects_base() -> Path:
    return Path(os.environ["DOTLINEFORM_PROJECTS_BASE_DIR"])


def source_root() -> Path:
    root = projects_base() / SOURCE_DIRECTORY
    root.mkdir(parents=True, exist_ok=True)
    return root


def request_import(repo_root: Path, staged_filename: str, **body: object) -> dict[str, object]:
    return docs_management_import_service.handle_import_source(
        repo_root,
        {
            "scope": "example",
            "source_directory": SOURCE_DIRECTORY,
            "staged_filename": staged_filename,
            **body,
        },
        dry_run=False,
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


def test_directory_and_candidate_gets_require_and_return_exact_markers() -> None:
    with make_repo() as temp:
        repo_root = Path(temp)
        selected = source_root()
        (selected / "references").mkdir()
        (selected / "notes.md").write_text("# Notes\n", encoding="utf-8")
        (selected / "standalone.png").write_bytes(b"ignored")
        read = docs_management_read_service.docs_management_get_payload

        with pytest.raises(ValueError, match="source_directory is required"):
            read(repo_root, docs_management_routes.IMPORT_SOURCE_DIRECTORIES_PATH, {})
        root_payload = read(
            repo_root,
            docs_management_routes.IMPORT_SOURCE_DIRECTORIES_PATH,
            {"source_directory": ["."]},
        )
        with pytest.raises(ValueError, match="selectable directory"):
            read(
                repo_root,
                docs_management_routes.IMPORT_SOURCE_FILES_PATH,
                {"source_directory": ["."]},
            )
        directory_payload = read(
            repo_root,
            docs_management_routes.IMPORT_SOURCE_DIRECTORIES_PATH,
            {"source_directory": [SOURCE_DIRECTORY]},
        )
        candidate_payload = read(
            repo_root,
            docs_management_routes.IMPORT_SOURCE_FILES_PATH,
            {"source_directory": [SOURCE_DIRECTORY]},
        )

    assert directory_payload["current_directory"] == SOURCE_DIRECTORY
    assert directory_payload["current_selectable"] is True
    assert directory_payload["parent_directory"] == "projects"
    assert directory_payload["directories"] == [{
        "label": "references",
        "source_directory": f"{SOURCE_DIRECTORY}/references",
    }]
    assert root_payload["current_selectable"] is False
    assert candidate_payload["source_directory"] == SOURCE_DIRECTORY
    assert candidate_payload["staging_root"] == SOURCE_DIRECTORY
    assert [record["filename"] for record in candidate_payload["files"]] == ["notes.md"]
    assert [record["filename"] for record in candidate_payload["candidates"]] == ["notes.md"]
    assert candidate_payload["candidates"][0]["path"] == f"{SOURCE_DIRECTORY}/notes.md"
    assert "markdown_preview" not in candidate_payload["candidates"][0]
    assert str(projects_base()) not in repr(candidate_payload)


def test_post_binds_preview_and_apply_to_exact_source_pair(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_repo() as temp:
        repo_root = Path(temp)
        write_scope_config(repo_root)
        write_example_doc(
            repo_root,
            "example.md",
            {"doc_id": "example", "title": "Example", "parent_id": ""},
        )
        selected = source_root()
        source = selected / "notes.md"
        source.write_text("# Alternate Notes\n\nBody.\n", encoding="utf-8")
        source_bytes = source.read_bytes()
        nested = selected / "nested"
        nested.mkdir()
        (nested / "nested.md").write_text("# Nested\n", encoding="utf-8")
        stub_markdown_validation(monkeypatch)

        preview = request_import(repo_root, "notes.md", preview_only=True)
        original_rebuild = stub_rebuild()
        try:
            applied = request_import(repo_root, "notes.md")
        finally:
            docs_write_rebuild.perform_source_write_and_rebuild = original_rebuild
        imported_source = (repo_root / applied["path"]).read_text(encoding="utf-8")
        source_unchanged = source.read_bytes() == source_bytes

        source.rename(selected / "moved.md")
        with pytest.raises(FileNotFoundError, match="does not exist"):
            request_import(repo_root, "notes.md")
        with pytest.raises(ValueError, match="selected source directory"):
            request_import(repo_root, "../outside.md")
        with pytest.raises(ValueError, match="direct children"):
            request_import(repo_root, "nested/nested.md")
        with pytest.raises(ValueError, match="source_directory is required"):
            docs_management_import_service.handle_import_source(
                repo_root, {"scope": "example", "staged_filename": "moved.md"}, dry_run=False,
            )

    assert preview["source_directory"] == SOURCE_DIRECTORY
    assert preview["import_preview"]["source_path"] == f"{SOURCE_DIRECTORY}/notes.md"
    assert applied["operation"] == "create"
    assert applied["source_directory"] == SOURCE_DIRECTORY
    assert applied["import_preview"]["source_path"] == f"{SOURCE_DIRECTORY}/notes.md"
    assert "# Alternate Notes" in imported_source
    assert source_unchanged is True
    assert str(projects_base()) not in repr(preview)
    assert str(projects_base()) not in repr(applied)


def test_non_staging_markdown_package_keeps_its_media_root(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_repo() as temp:
        repo_root = Path(temp)
        write_scope_config(repo_root)
        write_example_doc(
            repo_root,
            "example.md",
            {"doc_id": "example", "title": "Example", "parent_id": ""},
        )
        package = source_root() / "package-note"
        package.mkdir()
        (package / "Note.md").write_text(
            "---\ntitle: Alternate Package\n---\n\nPackage body.\n\n"
            "![Package image](image.png)\n",
            encoding="utf-8",
        )
        package_markdown = package / "Note.md"
        package_image = package / "image.png"
        write_test_image(package_image, (24, 18))
        source_bytes = (package_markdown.read_bytes(), package_image.read_bytes())
        stub_markdown_validation(monkeypatch)
        original_rebuild = stub_rebuild()
        try:
            payload = request_import(repo_root, "package-note")
        finally:
            docs_write_rebuild.perform_source_write_and_rebuild = original_rebuild

        source_text = (repo_root / payload["path"]).read_text(encoding="utf-8")
        media_result = payload["inline_media_written"][0]
        media_path = managed_media_path(
            "example",
            "img",
            media_result["artifact_identity"],
        )
        media_exists = media_path.is_file()
        source_unchanged = source_bytes == (
            package_markdown.read_bytes(),
            package_image.read_bytes(),
        )

    assert payload["source_directory"] == SOURCE_DIRECTORY
    assert payload["import_preview"]["source_path"] == f"{SOURCE_DIRECTORY}/package-note"
    assert payload["import_preview"]["source_markdown"] == f"{SOURCE_DIRECTORY}/package-note/Note.md"
    assert payload["import_preview"]["source_format"] == "markdown_package"
    assert media_exists is True
    assert source_unchanged is True
    assert f"[[media:{media_result['media_path']}]]" in source_text
    assert str(projects_base()) not in repr(payload)


def test_trusted_package_outside_staging_is_blocked_before_ordinary_import() -> None:
    with make_repo() as temp:
        repo_root = Path(temp)
        write_scope_config(repo_root)
        write_returned_jsonl(
            repo_root,
            "returned-documents.jsonl",
            [
                {
                    "doc_id": "returned-doc",
                    "title": "Returned Doc",
                    "content": "Returned body.",
                }
            ],
        )
        selected = source_root()
        staged = (
            configured_workspace_paths(repo_root).import_staging
            / "returned-documents.jsonl"
        )
        shutil.move(staged, selected / staged.name)

        listing = docs_import_source_service.handle_import_source_files(
            repo_root,
            source_directory=SOURCE_DIRECTORY,
        )
        candidate = listing["candidates"][0]
        with pytest.raises(
            ValueError,
            match="must be selected from data-sharing/import-staging",
        ):
            request_import(repo_root, staged.name)

    assert candidate["candidate_kind"] == "returned_package"
    assert candidate["validation_state"] == "blocked"
    assert candidate["import_enabled"] is False
    assert candidate["diagnostics"][0]["code"] == TRUSTED_SOURCE_STAGING_CODE
    assert candidate["diagnostics"][0]["message"] == (
        "Trusted document packages and edited review sources must be selected "
        "from data-sharing/import-staging."
    )
    assert candidate["path"] == f"{SOURCE_DIRECTORY}/{staged.name}"
    assert str(projects_base()) not in repr(listing)
