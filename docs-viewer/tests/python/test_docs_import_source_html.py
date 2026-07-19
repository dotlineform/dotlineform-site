#!/usr/bin/env python3
"""Docs HTML source import tests."""

from __future__ import annotations

from pathlib import Path

import docs_html_markdown
import docs_import_preview
import docs_import_source_service as import_source_service
import docs_write_rebuild as write_rebuild

from docs_import_test_support import handle_import_source, make_repo, stub_rebuild, write_library_doc, write_staged_html


def test_html_to_markdown_is_available_without_import_preview_summary() -> None:
    result = docs_html_markdown.html_to_markdown(
        """
        <html>
          <head><title>Shared Converter</title></head>
          <body>
            <h1>Shared Converter</h1>
            <p>Body with <strong>bold</strong> and <a href="https://example.com">a link</a>.</p>
            <ul><li>One</li><li>Two</li></ul>
          </body>
        </html>
        """
    )

    assert result.title == "Shared Converter"
    assert result.markdown == "# Shared Converter\n\nBody with **bold** and [a link](https://example.com).\n\n- One\n- Two"
    assert result.tag_counts["html"] == 1
    assert result.comment_count == 0
    assert result.warnings == []


def test_html_to_markdown_preserves_whitespace_around_emphasis_runs() -> None:
    result = docs_html_markdown.html_to_markdown(
        """
        <html><body>
          <p><strong>Benefit Description: </strong>A supported benefit.</p>
          <p>Before <em>emphasized </em>text and <b>bold</b>.</p>
        </body></html>
        """
    )
    rendered = docs_import_preview.render_markdown_document(result.markdown, title="Emphasis")

    assert result.markdown == (
        "**Benefit Description:** A supported benefit.\n\n"
        "Before *emphasized* text and **bold**."
    )
    assert "<strong>Benefit Description:</strong> A supported benefit." in rendered.html
    assert "**Benefit Description:**" not in rendered.html


def test_html_to_markdown_keeps_historical_inline_svg_children_out_of_paragraphs() -> None:
    result = docs_html_markdown.html_to_markdown(
        """
        <html><body><svg viewBox="0 0 10 10">
          <title>Diagram</title>

          <rect width="10" height="10"></rect>
        </svg></body></html>
        """
    )
    rendered = docs_import_preview.render_markdown_document(result.markdown, title="Diagram")

    assert "<svg" in result.markdown
    assert "\n\n" not in result.markdown
    assert "<rect" in rendered.html
    assert "<p><rect" not in rendered.html


def test_html_to_markdown_preserves_table_cell_block_and_list_boundaries() -> None:
    result = docs_html_markdown.html_to_markdown(
        """
        <table>
          <tr><th>Step</th><th>Description</th></tr>
          <tr>
            <td><p>1</p></td>
            <td>
              <p>Travel somewhere nice.</p>
              <p>There are many places to go:</p>
              <ul><li>Here</li><li>There</li><li>Anywhere</li></ul>
            </td>
          </tr>
        </table>
        """
    )

    assert result.markdown == (
        "| Step | Description |\n"
        "| --- | --- |\n"
        "| 1 | Travel somewhere nice.<br>There are many places to go:<br>"
        "Here; There; Anywhere |"
    )
    assert result.warnings == []


def test_html_import_create_allocates_identity_independent_of_staged_filename() -> None:
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

        source_path = root / payload["path"]
        source_exists = source_path.exists()
        source_text = source_path.read_text(encoding="utf-8")

    assert payload["ok"] is True
    assert payload["operation"] == "create"
    assert payload["doc_id"].startswith("d-")
    assert payload["path"] == f"docs-viewer/source/library/documents/{payload['doc_id']}.md"
    assert payload["title"] == "An Overly Descriptive Document Title"
    assert payload["import_preview"]["proposed_doc_id_source"] == "allocated-local-identity"
    assert payload["import_preview"]["source_doc_id"] == "compact-name"
    assert source_exists
    assert f"doc_id: {payload['doc_id']}" in source_text
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

        source_text = (root / payload["path"]).read_text(encoding="utf-8")
        asset_path = root / "site/assets/data/docs/scopes/library/media/html/worksheet-widget.html"
        asset_text = asset_path.read_text(encoding="utf-8")
        second_asset_path = root / "site/assets/data/docs/scopes/library/media/html/second-widget.html"
        second_asset_text = second_asset_path.read_text(encoding="utf-8")

    assert payload["ok"] is True
    assert "[[html-media:docs/library/html/worksheet-widget.html]]" not in source_text
    assert payload["import_preview"]["interactive_html_plans"][0]["token"] == "[[html-media:docs/library/html/second-widget.html]]"
    assert payload["import_preview"]["interactive_html_plans"][1]["token"] == "[[html-media:docs/library/html/worksheet-widget.html]]"
    assert [item["target_path"] for item in payload["interactive_html_written"]] == [
        "docs/library/html/second-widget.html",
        "docs/library/html/worksheet-widget.html",
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

        asset_exists = (root / "site/assets/data/docs/scopes/library/media/html/worksheet-widget.html").exists()

    assert payload["ok"] is True
    assert payload["preview_only"] is True
    assert payload["import_preview"]["interactive_html_plans"][0]["target_path"] == "docs/library/html/worksheet-widget.html"
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
        existing_asset = root / "site/assets/data/docs/scopes/library/media/html/worksheet-widget.html"
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

        source_text = (root / apply_payload["path"]).read_text(encoding="utf-8")
        asset_text = existing_asset.read_text(encoding="utf-8")

    assert preview_payload["ok"] is True
    assert preview_payload["preview_only"] is True
    assert preview_payload["requires_interactive_html_confirmation"] is True
    assert preview_payload["summary_text"] == "Interactive HTML asset overwrite required for docs/library/html/worksheet-widget.html."
    assert apply_payload["ok"] is True
    assert apply_payload["interactive_html_written"][0]["overwrote"] is True
    assert f"doc_id: {apply_payload['doc_id']}" in source_text
    assert "Interactive" in asset_text
    assert asset_text != "existing\n"
