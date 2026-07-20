#!/usr/bin/env python3
"""Generic Docs Import content contract tests."""

from __future__ import annotations

from pathlib import Path

import pytest

import docs_import_preview
from docs_import_content import (
    CONTENT_INTENT_EMPTY_NEW,
    CONTENT_INTENT_PRESERVE_EXISTING,
    CONTENT_INTENT_REPLACE,
    ImportContent,
)
from docs_import_test_support import make_repo, write_staged_html, write_staged_markdown, write_staged_text
from docs_document_packages.workspace import configured_workspace_paths


def make_content(**changes: object) -> ImportContent:
    fields: dict[str, object] = {
        "source_kind": "ordinary_markdown",
        "source_identity": "note.md",
        "record_identity": "note.md",
        "doc_id": "note",
        "title": "Note",
        "content_intent": CONTENT_INTENT_REPLACE,
        "content_format": "markdown",
        "content": "# Note\n",
    }
    fields.update(changes)
    return ImportContent(**fields)  # type: ignore[arg-type]


def test_generic_import_content_does_not_require_adapter_provenance() -> None:
    content = make_content()

    assert content.provenance == {}
    assert content.as_dict()["content"] == "# Note\n"


def test_content_intents_distinguish_replace_preserve_and_empty_new() -> None:
    replacement = make_content(content_intent=CONTENT_INTENT_REPLACE, content="")
    preserved = make_content(content_intent=CONTENT_INTENT_PRESERVE_EXISTING, content=None)
    empty_new = make_content(content_intent=CONTENT_INTENT_EMPTY_NEW, content=None)

    assert replacement.content == ""
    assert preserved.content is None
    assert empty_new.content is None


def test_content_intent_rejects_ambiguous_content_presence() -> None:
    with pytest.raises(ValueError, match="requires string content"):
        make_content(content_intent=CONTENT_INTENT_REPLACE, content=None)
    with pytest.raises(ValueError, match="must not carry replacement content"):
        make_content(content_intent=CONTENT_INTENT_PRESERVE_EXISTING, content="# Wrong")
    with pytest.raises(ValueError, match="content_format"):
        make_content(content_format="rich_text")


@pytest.mark.parametrize(
    ("filename", "content_format", "content"),
    [
        ("note.md", "markdown", "# Note\n\nMarkdown body.\n"),
        ("note.html", "html", "<html><body><h1>Note</h1><p>HTML body.</p></body></html>"),
        ("note.txt", "plain_text", "Note\n\nPlain body.\n"),
    ],
)
def test_file_wrappers_use_the_same_content_entrypoints(
    filename: str,
    content_format: str,
    content: str,
) -> None:
    with make_repo() as temp:
        root = Path(temp)
        writers = {
            "markdown": write_staged_markdown,
            "html": write_staged_html,
            "plain_text": write_staged_text,
        }
        writers[content_format](root, filename, content)
        paths = configured_workspace_paths(root)
        source_path = docs_import_preview.resolve_staged_import_source(paths.import_staging, filename)

        file_preview = docs_import_preview.generate_import_preview(
            root,
            staging_root=paths.import_staging,
            workspace_root=paths.root,
            source_path=source_path,
            scope="library",
            include_prompt_meta=False,
        )
        content_preview = docs_import_preview.generate_content_import_preview(
            content=content,
            content_format=content_format,
            source_identity="note",
            scope="library",
            staging_root=paths.import_staging,
            workspace_root=paths.root,
        )

    for key in ("title", "proposed_doc_id", "markdown_preview", "source_stats", "markdown_validation"):
        assert content_preview[key] == file_preview[key]


def test_content_entrypoint_honors_record_identity_over_body_heading() -> None:
    with make_repo() as temp:
        root = Path(temp)
        paths = configured_workspace_paths(root)
        preview = docs_import_preview.generate_content_import_preview(
            content="# Body Heading\n\nBody.\n",
            content_format="markdown",
            source_identity="wrapper-row-1",
            scope="library",
            staging_root=paths.import_staging,
            workspace_root=paths.root,
            title="Trusted Record Title",
            doc_id="trusted-record",
        )

    assert preview["title"] == "Trusted Record Title"
    assert preview["title_source"] == "record"
    assert preview["proposed_doc_id"] == "trusted-record"
    assert preview["proposed_doc_id_source"] == "record"


def test_normalized_import_content_dispatches_to_the_content_preview_boundary() -> None:
    with make_repo() as temp:
        root = Path(temp)
        paths = configured_workspace_paths(root)
        record = make_content(
            record_identity="wrapper:0:trusted-record",
            doc_id="trusted-record",
            title="Trusted Record",
            content_format="plain_text",
            content="Plain body https://example.com/path.",
        )

        preview = docs_import_preview.generate_normalized_import_content_preview(
            record,
            scope="library",
            staging_root=paths.import_staging,
            workspace_root=paths.root,
        )

    assert preview["title"] == "Trusted Record"
    assert preview["proposed_doc_id"] == "trusted-record"
    assert "<https://example.com/path>" in preview["markdown_preview"]

    with pytest.raises(ValueError, match="only replace"):
        docs_import_preview.generate_normalized_import_content_preview(
            make_content(content_intent=CONTENT_INTENT_PRESERVE_EXISTING, content=None),
            scope="library",
            staging_root=paths.import_staging,
            workspace_root=paths.root,
        )
