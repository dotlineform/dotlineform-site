#!/usr/bin/env python3
"""Python Docs Viewer builder payload tests."""

from __future__ import annotations

import tempfile
from pathlib import Path

from build_docs_test_support import (
    CHILD_DOC_ID,
    PARENT_DOC_ID,
    prepare_repo,
    read_json,
    run_builder,
    write_source_docs,
    write_text,
)

def test_python_docs_builder_writes_docs_payloads_and_semantic_token_usage() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        result = run_builder(root)

        index_tree = read_json(root / "docs-viewer/scopes/studio/published/documents/index-tree.json")
        recent = read_json(root / "docs-viewer/scopes/studio/published/documents/recent.json")
        child = read_json(root / f"docs-viewer/scopes/studio/published/documents/by-id/{CHILD_DOC_ID}.json")
        semantic_tokens_dir = (
            root / "docs-viewer/scopes/studio/published/documents/semantic-tokens"
        )
        usage_index = read_json(semantic_tokens_dir / "index.json")
        by_document_exists = (semantic_tokens_dir / "by-document").exists()
        by_target_exists = (semantic_tokens_dir / "by-target").exists()

    docs = result["index_payload"]["docs"]
    assert [doc["doc_id"] for doc in docs] == [PARENT_DOC_ID, CHILD_DOC_ID]
    assert docs[1]["summary"] == "Child summary"
    assert docs[1]["date"] == "2026-06-02"
    assert docs[1]["date_display"] == "June 2026"
    assert docs[1]["ui_status"] == "done"
    assert docs[1]["content_url"] == f"/docs-viewer/scopes/studio/published/documents/by-id/{CHILD_DOC_ID}.json"
    assert isinstance(docs[1]["content_text_length"], int)

    assert index_tree["schema"] == "docs_index_tree_v1"
    assert [doc["doc_id"] for doc in index_tree["docs"]] == [PARENT_DOC_ID]
    assert [doc["doc_id"] for doc in index_tree["docs"][0]["children"]] == [CHILD_DOC_ID]
    tree_child = index_tree["docs"][0]["children"][0]
    assert tree_child == {
        "doc_id": CHILD_DOC_ID,
        "title": "Child",
        "content_url": f"/docs-viewer/scopes/studio/published/documents/by-id/{CHILD_DOC_ID}.json",
        "ui_status": "done",
    }
    assert "parent_id" not in tree_child
    assert "summary" not in tree_child
    assert "added_date" not in tree_child
    assert "last_updated" not in tree_child
    assert "source_path" not in tree_child
    assert "viewer_url" not in tree_child
    assert "content_text_length" not in tree_child

    assert recent["schema"] == "docs_recent_v1"
    assert recent["basis"] == "edited"
    assert recent["limit"] == 10
    assert recent["docs"][0]["doc_id"] == CHILD_DOC_ID
    assert recent["docs"][0]["timestamp"] == "2026-06-02 10:00:00"
    assert recent["docs"][0]["parent_title"] == "Parent"

    content_html = child["content_html"]
    assert f'href="/docs/?scope=studio&amp;doc={PARENT_DOC_ID}"' in content_html
    assert 'src="/docs/media/studio/img/diagram.png"' in content_html
    assert (
        '<img src="/docs/media/studio/img/measured-diagram.png" '
        'alt="Measured diagram" width="800" height="600"'
    ) in content_html
    assert (
        '<img src="/docs/media/studio/svg/persistent-diagram.svg" '
        'alt="Persistent SVG diagram" data-docs-viewer-diagram-kind="persistent-svg"'
    ) in content_html
    assert content_html.count('data-docs-viewer-diagram-kind="persistent-svg"') == 1
    assert 'title="Alt text"' in content_html
    assert 'href="/works/?work=00638"' in content_html
    assert 'data-semantic-token-family="catalogue"' in content_html
    assert "[[catalogue:work:63899|commented missing work]]" in content_html
    assert "[[catalogue:work:63898|commented missing work multiline]]" in content_html
    assert "[[catalogue:work:00638|inline code]]" in content_html
    assert "[[catalogue:work:00638|fenced code]]" in content_html
    assert child["date"] == "2026-06-02"
    assert child["date_display"] == "June 2026"

    assert usage_index["schema_version"] == "docs_semantic_token_usage_index_v1"
    assert len(usage_index["occurrences"]) == 1
    assert usage_index["occurrences"][0]["source_doc_id"] == CHILD_DOC_ID
    assert usage_index["occurrences"][0]["title"] == "three signs"
    assert not by_document_exists
    assert not by_target_exists
    assert result["diagnostics"]["docs_emitted"] == 2
    assert result["diagnostics"]["index_tree_changed"] == 1
    assert result["diagnostics"]["recent_changed"] == 1

def test_python_docs_builder_preserves_existing_payloads_for_targeted_builds() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        run_builder(root)
        parent_before = read_json(root / f"docs-viewer/scopes/studio/published/documents/by-id/{PARENT_DOC_ID}.json")
        write_source_docs(root, child_body_suffix="Updated targeted body.")
        result = run_builder(root, only_doc_ids=[CHILD_DOC_ID])
        parent_after = read_json(root / f"docs-viewer/scopes/studio/published/documents/by-id/{PARENT_DOC_ID}.json")
        child_after = read_json(root / f"docs-viewer/scopes/studio/published/documents/by-id/{CHILD_DOC_ID}.json")

    assert parent_after == parent_before
    assert "Updated targeted body." in child_after["content_html"]
    assert result["diagnostics"]["build_mode"] == "targeted"
    assert result["diagnostics"]["only_doc_ids"] == [CHILD_DOC_ID]
    assert PARENT_DOC_ID not in result["write_plan"]["changed_item_ids"]

def test_python_docs_builder_targeted_build_preserves_usage_from_scope_index() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        run_builder(root)
        child_before = read_json(
            root / f"docs-viewer/scopes/studio/published/documents/by-id/{CHILD_DOC_ID}.json"
        )
        write_source_docs(root, parent_body_suffix="Updated targeted parent.")
        result = run_builder(root, only_doc_ids=[PARENT_DOC_ID])
        child_after = read_json(
            root / f"docs-viewer/scopes/studio/published/documents/by-id/{CHILD_DOC_ID}.json"
        )
        usage_index = read_json(
            root / "docs-viewer/scopes/studio/published/documents/semantic-tokens/index.json"
        )

    assert child_after == child_before
    assert result["diagnostics"]["build_mode"] == "targeted"
    assert result["diagnostics"]["only_doc_ids"] == [PARENT_DOC_ID]
    assert [row["source_doc_id"] for row in usage_index["occurrences"]] == [CHILD_DOC_ID]


def test_python_docs_builder_targeted_build_removes_selected_doc_usage_from_scope_index() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        run_builder(root)
        child_source = (
            root / f"docs-viewer/scopes/studio/source/documents/{CHILD_DOC_ID}.md"
        )
        write_text(
            child_source,
            child_source.read_text(encoding="utf-8").replace(
                "[[catalogue:work:00638|three signs]]",
                "three signs",
            ),
        )
        result = run_builder(root, only_doc_ids=[CHILD_DOC_ID])
        usage_index = read_json(
            root / "docs-viewer/scopes/studio/published/documents/semantic-tokens/index.json"
        )

    assert result["diagnostics"]["build_mode"] == "targeted"
    assert result["diagnostics"]["only_doc_ids"] == [CHILD_DOC_ID]
    assert result["diagnostics"]["semantic_token_index_changed"] == 1
    assert usage_index["occurrences"] == []


def test_python_docs_builder_leaves_unresolved_catalogue_tokens_literal() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        write_source_docs(
            root,
            child_body_suffix="Missing target [[catalogue:work:99999|still literal]].",
        )
        result = run_builder(root)
        child = read_json(root / f"docs-viewer/scopes/studio/published/documents/by-id/{CHILD_DOC_ID}.json")
        usage_index = read_json(
            root / "docs-viewer/scopes/studio/published/documents/semantic-tokens/index.json"
        )

    assert result["diagnostics"]["warning_count"] == 0
    assert "[[catalogue:work:99999|still literal]]" in child["content_html"]
    assert all(
        occurrence["target_id"] != "99999"
        for occurrence in usage_index["occurrences"]
    )


def test_python_docs_builder_projects_only_valid_local_folder_links() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        write_source_docs(
            root,
            child_body_suffix="""
[Folder](dlf-local:projects/3%20symbols)
[](dlf-local:archives/future)
[Unsafe](dlf-local:projects/%2E%2E)
![Image](dlf-local:projects/image.png)
`[Inline](dlf-local:projects/inline)`

    [Indented](dlf-local:projects/indented)

<pre>[Pre](dlf-local:projects/pre)</pre>
""",
        )
        run_builder(root)
        child = read_json(root / f"docs-viewer/scopes/studio/published/documents/by-id/{CHILD_DOC_ID}.json")

    content_html = child["content_html"]
    assert '<a href="#" data-docs-viewer-local-target="projects/3%20symbols">Folder</a>' in content_html
    assert '<a href="#" data-docs-viewer-local-target="archives/future">[local file or folder]</a>' in content_html
    assert content_html.count("data-docs-viewer-local-target") == 2
    assert "Unsafe" in content_html and "Image" in content_html
    assert "dlf-local:projects/inline" in content_html
    assert "dlf-local:projects/indented" in content_html
    assert "dlf-local:projects/pre" in content_html
