#!/usr/bin/env python3
"""Docs HTML source import tests."""

from __future__ import annotations

from pathlib import Path

import docs_import_preview
import docs_import_source_service as import_source_service
import docs_write_rebuild as write_rebuild

from docs_import_test_support import handle_import_source, make_repo, stub_rebuild, write_library_doc, write_staged_html

def test_html_import_create_uses_staged_filename_for_doc_id_and_path() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
        write_staged_html(
            root,
            "compact-name.html",
            """
            <html>
              <head><title>An Overly Descriptive Document Title</title></head>
              <body><h1>An Overly Descriptive Document Title</h1><p>Imported body.</p></body>
            </html>
            """,
        )
        original_rebuild = stub_rebuild()
        original_validation = docs_import_preview.validate_markdown_preview
        docs_import_preview.validate_markdown_preview = lambda markdown, *, title="": {
            "ok": True,
            "html_chars": len(markdown),
            "renderer": "stub",
        }
        try:
            payload = handle_import_source(
                root,
                {"scope": "library", "staged_filename": "compact-name.html"},
                dry_run=False,
            )
        finally:
            write_rebuild.perform_source_write_and_rebuild = original_rebuild
            docs_import_preview.validate_markdown_preview = original_validation

        source_path = root / "docs-viewer/source/library/compact-name.md"
        source_exists = source_path.exists()
        source_text = source_path.read_text(encoding="utf-8")

    assert payload["ok"] is True
    assert payload["operation"] == "create"
    assert payload["doc_id"] == "compact-name"
    assert payload["path"] == "docs-viewer/source/library/compact-name.md"
    assert payload["title"] == "An Overly Descriptive Document Title"
    assert payload["import_preview"]["proposed_doc_id_source"] == "filename"
    assert source_exists
    assert "doc_id: compact-name" in source_text
    assert "title: An Overly Descriptive Document Title" in source_text

def test_html_import_copies_role_marked_interactive_assets() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
        write_staged_html(
            root,
            "worksheet.html",
            """
            <html>
              <head><title>Worksheet</title></head>
              <body><h1>Worksheet</h1><p>Readable body.</p></body>
            </html>
            """,
        )
        write_staged_html(
            root,
            "Worksheet Widget.html",
            """
            <!doctype html>
            <html>
              <head><meta name="dlf:docs-import-role" content="interactive-html"></head>
              <body><button>Run</button><script>window.ready = true;</script></body>
            </html>
            """,
        )
        write_staged_html(
            root,
            "second-widget.html",
            """
            <!doctype html>
            <html>
              <head><meta name="dlf:docs-import-role" content="interactive-html"></head>
              <body>Second widget</body>
            </html>
            """,
        )
        original_rebuild = stub_rebuild()
        original_validation = docs_import_preview.validate_markdown_preview
        docs_import_preview.validate_markdown_preview = lambda markdown, *, title="": {
            "ok": True,
            "html_chars": len(markdown),
            "renderer": "stub",
        }
        try:
            payload = handle_import_source(
                root,
                {"scope": "library", "staged_filename": "worksheet.html"},
                dry_run=False,
            )
        finally:
            write_rebuild.perform_source_write_and_rebuild = original_rebuild
            docs_import_preview.validate_markdown_preview = original_validation

        source_text = (root / "docs-viewer/source/library/worksheet.md").read_text(encoding="utf-8")
        asset_path = root / "site/assets/docs/interactive/library/worksheet-widget.html"
        asset_text = asset_path.read_text(encoding="utf-8")
        second_asset_path = root / "site/assets/docs/interactive/library/second-widget.html"
        second_asset_text = second_asset_path.read_text(encoding="utf-8")

    assert payload["ok"] is True
    assert "[[interactive-html:worksheet-widget.html]]" not in source_text
    assert payload["import_preview"]["interactive_html_plans"][0]["token"] == "[[interactive-html:second-widget.html]]"
    assert payload["import_preview"]["interactive_html_plans"][1]["token"] == "[[interactive-html:worksheet-widget.html]]"
    assert [item["target_path"] for item in payload["interactive_html_written"]] == [
        "site/assets/docs/interactive/library/second-widget.html",
        "site/assets/docs/interactive/library/worksheet-widget.html",
    ]
    assert payload["interactive_html_written"][1]["display_name"] == "worksheet-widget"
    assert payload["interactive_html_written"][1]["result_type"] == "script file"
    assert "window.ready = true" in asset_text
    assert "Second widget" in second_asset_text
    assert "Copied 2 interactive HTML script files." in payload["summary_text"]

def test_html_import_reports_role_marked_interactive_assets_in_preview_only() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
        write_staged_html(root, "worksheet.html", "<html><body><h1>Worksheet</h1></body></html>")
        write_staged_html(
            root,
            "Worksheet Widget.html",
            """
            <!doctype html>
            <html>
              <head><meta name="dlf:docs-import-role" content="interactive-html"></head>
              <body>Interactive</body>
            </html>
            """,
        )
        original_rebuild = stub_rebuild()
        original_validation = docs_import_preview.validate_markdown_preview
        docs_import_preview.validate_markdown_preview = lambda markdown, *, title="": {
            "ok": True,
            "html_chars": len(markdown),
            "renderer": "stub",
        }
        try:
            payload = handle_import_source(
                root,
                {"scope": "library", "staged_filename": "worksheet.html", "preview_only": True},
                dry_run=False,
            )
            files = import_source_service.handle_import_source_files(root)["files"]
        finally:
            write_rebuild.perform_source_write_and_rebuild = original_rebuild
            docs_import_preview.validate_markdown_preview = original_validation

        asset_exists = (root / "site/assets/docs/interactive/library/worksheet-widget.html").exists()

    assert payload["ok"] is True
    assert payload["preview_only"] is True
    assert payload["import_preview"]["interactive_html_plans"][0]["target_path"] == "site/assets/docs/interactive/library/worksheet-widget.html"
    assert [file["filename"] for file in files] == ["worksheet.html"]
    assert asset_exists is False

def test_html_import_confirms_existing_role_marked_interactive_asset_target() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
        write_staged_html(root, "worksheet.html", "<html><body><h1>Worksheet</h1></body></html>")
        write_staged_html(
            root,
            "worksheet-widget.html",
            """
            <!doctype html>
            <html>
              <head><meta name="dlf:docs-import-role" content="interactive-html"></head>
              <body>Interactive</body>
            </html>
            """,
        )
        existing_asset = root / "site/assets/docs/interactive/library/worksheet-widget.html"
        existing_asset.parent.mkdir(parents=True, exist_ok=True)
        existing_asset.write_text("existing\n", encoding="utf-8")
        original_rebuild = stub_rebuild()
        original_validation = docs_import_preview.validate_markdown_preview
        docs_import_preview.validate_markdown_preview = lambda markdown, *, title="": {
            "ok": True,
            "html_chars": len(markdown),
            "renderer": "stub",
        }
        try:
            preview_payload = handle_import_source(
                root,
                {"scope": "library", "staged_filename": "worksheet.html"},
                dry_run=False,
            )
            apply_payload = handle_import_source(
                root,
                {"scope": "library", "staged_filename": "worksheet.html", "confirm_overwrite": True},
                dry_run=False,
            )
        finally:
            write_rebuild.perform_source_write_and_rebuild = original_rebuild
            docs_import_preview.validate_markdown_preview = original_validation

        source_text = (root / "docs-viewer/source/library/worksheet.md").read_text(encoding="utf-8")
        asset_text = existing_asset.read_text(encoding="utf-8")

    assert preview_payload["ok"] is True
    assert preview_payload["preview_only"] is True
    assert preview_payload["requires_interactive_html_confirmation"] is True
    assert preview_payload["summary_text"] == "Interactive HTML asset overwrite required for site/assets/docs/interactive/library/worksheet-widget.html."
    assert apply_payload["ok"] is True
    assert apply_payload["interactive_html_written"][0]["overwrote"] is True
    assert "doc_id: worksheet" in source_text
    assert "Interactive" in asset_text
    assert asset_text != "existing\n"
