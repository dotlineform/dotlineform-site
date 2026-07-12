#!/usr/bin/env python3
"""Docs source import listing and preview tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import docs_import_media
import docs_import_preview
import docs_import_source_service as import_source_service
from services.paths import configured_workspace_paths

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

def test_source_import_files_list_html_and_markdown() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged_html(root, "source.html", "<html><body><h1>Source</h1></body></html>")
        write_staged_markdown(root, "source.md", "# Source\n")
        write_staged_text(root, "source.txt", "Source\n")
        write_staged_text(root, "source.svg", "<svg viewBox='0 0 10 10'></svg>\n")
        write_staged_bytes(root, "source.png", b"fake image")
        write_staged_bytes(root, "source.pdf", b"fake pdf")
        write_staged_package_file(root, "package-note", "Note.md", "# Package Note\n")

        files = import_source_service.handle_import_source_files(root)["files"]

    by_filename = {item["filename"]: item for item in files}
    assert by_filename["source.html"]["source_format"] == "html"
    assert by_filename["source.md"]["source_format"] == "markdown"
    assert by_filename["source.txt"]["source_format"] == "text"
    assert by_filename["source.svg"]["source_format"] == "svg"
    assert by_filename["source.png"]["source_format"] == "image"
    assert by_filename["source.pdf"]["source_format"] == "file"
    assert by_filename["package-note"]["source_format"] == "markdown_package"
    assert by_filename["package-note"]["package_markdown_count"] == 1
    assert by_filename["source.md"]["path"] == "$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-staging/source.md"


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
    assert by_filename["ordinary.json"]["source_format"] == "file"


def test_review_package_identity_attaches_only_to_its_matching_safe_staged_record() -> None:
    with make_repo() as temp:
        root = Path(temp)
        export_id = "ds_20260712T180000Z"
        filename = "reviewed-documents.jsonl"
        write_returned_jsonl(
            root,
            filename,
            [{"doc_id": "reviewed-doc", "title": "Reviewed Doc", "content": "Body."}],
            export_id=export_id,
        )
        paths = configured_workspace_paths(root)
        package = paths.import_preview / "reviewed-package"
        package.mkdir(parents=True)
        (package / "manifest.json").write_text(
            json.dumps(
                {
                    "schema_version": "docs_review_validated_package_v1",
                    "package_id": "reviewed-package",
                    "status": "validated",
                    "source_scope": "library",
                    "source_export_id": export_id,
                    "staged_filename": filename,
                }
            )
            + "\n",
            encoding="utf-8",
        )

        listed = import_source_service.handle_import_source_files(root)["files"]
        matching = next(record for record in listed if record["filename"] == filename)

        assert matching["review_package_ids"] == ["reviewed-package"]
        assert "package_path" not in matching
        assert "preview_path" not in matching

        manifest = json.loads((package / "manifest.json").read_text(encoding="utf-8"))
        manifest["source_export_id"] = "ds_20260712T180001Z"
        (package / "manifest.json").write_text(json.dumps(manifest) + "\n", encoding="utf-8")
        mismatched = import_source_service.handle_import_source_files(root)["files"]

    assert "review_package_ids" not in next(record for record in mismatched if record["filename"] == filename)


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


def test_source_import_listing_ignores_collection_result_reports() -> None:
    with make_repo() as temp:
        root = Path(temp)
        paths = configured_workspace_paths(root)
        results = paths.import_staging / "results"
        results.mkdir()
        (results / "result.md").write_text("# Import result\n", encoding="utf-8")
        write_staged_markdown(root, "ordinary.md", "# Ordinary\n")

        payload = import_source_service.handle_import_source_files(root)

    assert [item["filename"] for item in payload["files"]] == ["ordinary.md"]


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
        write_staged_text(root, "source.svg", "<svg viewBox='0 0 10 10'><title>Source</title><rect /></svg>\n")
        write_staged_bytes(root, "source.png", b"fake image")
        write_staged_bytes(root, "source.pdf", b"fake pdf")
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
                "source.svg",
                "source.png",
                "source.pdf",
                "package-note",
            ]
        ]

    source_formats = {preview["source_format"] for preview in previews}
    assert source_formats == {"html", "markdown", "text", "svg", "image", "file", "markdown_package"}
    for preview in previews:
        validation = preview["markdown_validation"]
        assert validation["ok"] is True
        assert validation["renderer"] == "studio/shared/python/markdown_renderer.py"
        assert validation["renderer_contract"]["library"] == "markdown-it-py"
        assert validation["sanitizer_boundary"]["import_html"] == "docs_html_markdown structured conversion and SVG serialization"

def test_media_path_comes_from_scope_config() -> None:
    assert docs_import_media.media_path_for("analysis", "img", "diagram.png") == "docs/analysis/img/diagram.png"
    assert docs_import_media.media_token("analysis", "img", "diagram.png") == "[[media:docs/analysis/img/diagram.png]]"
