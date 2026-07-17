#!/usr/bin/env python3
"""Python Docs Viewer builder payload tests."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from build_docs_test_support import (
    CHILD_DOC_ID,
    PARENT_DOC_ID,
    prepare_repo,
    read_json,
    run_builder,
    write_source_docs,
)

def test_python_docs_builder_writes_docs_payloads_and_references() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        result = run_builder(root)

        index_tree = read_json(root / "docs-viewer/published/docs/studio/index-tree.json")
        recent = read_json(root / "docs-viewer/published/docs/studio/recent.json")
        child = read_json(root / f"docs-viewer/published/docs/studio/by-id/{CHILD_DOC_ID}.json")
        references_index = read_json(root / "docs-viewer/published/docs/studio/references/index.json")
        target_payload = read_json(root / "docs-viewer/published/docs/studio/references/by-target/work/00638.json")
        by_doc = read_json(root / f"docs-viewer/published/docs/studio/references/by-doc/{CHILD_DOC_ID}.json")

    docs = result["index_payload"]["docs"]
    assert [doc["doc_id"] for doc in docs] == [PARENT_DOC_ID, CHILD_DOC_ID]
    assert docs[1]["summary"] == "Child summary"
    assert docs[1]["date"] == "2026-06-02"
    assert docs[1]["date_display"] == "June 2026"
    assert docs[1]["ui_status"] == "done"
    assert docs[1]["content_url"] == f"/docs-viewer/published/docs/studio/by-id/{CHILD_DOC_ID}.json"
    assert isinstance(docs[1]["content_text_length"], int)

    assert index_tree["schema"] == "docs_index_tree_v1"
    assert [doc["doc_id"] for doc in index_tree["docs"]] == [PARENT_DOC_ID]
    assert [doc["doc_id"] for doc in index_tree["docs"][0]["children"]] == [CHILD_DOC_ID]
    tree_child = index_tree["docs"][0]["children"][0]
    assert tree_child == {
        "doc_id": CHILD_DOC_ID,
        "title": "Child",
        "content_url": f"/docs-viewer/published/docs/studio/by-id/{CHILD_DOC_ID}.json",
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
    assert 'title="Alt text"' in content_html
    assert 'href="/works/?work=00638"' in content_html
    assert "[[ref:work:638999|commented missing work]]" in content_html
    assert "[[ref:work:638998|commented missing work multiline]]" in content_html
    assert "[[ref:series:26]]" in content_html
    assert "[[ref:moment:dark-sky]]" in content_html
    assert child["viewer_report"] == "semantic_references"
    assert child["viewer_report_subscope"] == "tags"
    assert child["date"] == "2026-06-02"
    assert child["date_display"] == "June 2026"

    assert references_index["header"]["schema"] == "docs_semantic_references_index_v1"
    assert references_index["header"]["count"] == 1
    assert "638999" not in json.dumps(references_index)
    assert "638998" not in json.dumps(references_index)
    assert references_index["targets"][0]["target_key"] == "work:00638"
    assert references_index["targets"][0]["bucket_url"] == "/docs-viewer/published/docs/studio/references/by-target/work/00638.json"
    assert target_payload["header"]["schema"] == "docs_semantic_references_by_target_v1"
    assert target_payload["target_kind"] == "work"
    assert target_payload["references"][0]["source_doc_id"] == CHILD_DOC_ID
    assert by_doc["references"][0]["label"] == "three signs"
    assert result["diagnostics"]["docs_emitted"] == 2
    assert result["diagnostics"]["index_tree_changed"] == 1
    assert result["diagnostics"]["recent_changed"] == 1

def test_python_docs_builder_preserves_existing_payloads_for_targeted_builds() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        run_builder(root)
        parent_before = read_json(root / f"docs-viewer/published/docs/studio/by-id/{PARENT_DOC_ID}.json")
        write_source_docs(root, child_body_suffix="Updated targeted body.")
        result = run_builder(root, only_doc_ids=[CHILD_DOC_ID])
        parent_after = read_json(root / f"docs-viewer/published/docs/studio/by-id/{PARENT_DOC_ID}.json")
        child_after = read_json(root / f"docs-viewer/published/docs/studio/by-id/{CHILD_DOC_ID}.json")

    assert parent_after == parent_before
    assert "Updated targeted body." in child_after["content_html"]
    assert result["diagnostics"]["build_mode"] == "targeted"
    assert result["diagnostics"]["only_doc_ids"] == [CHILD_DOC_ID]
    assert PARENT_DOC_ID not in result["write_plan"]["changed_item_ids"]

def test_python_docs_builder_registry_backed_references_do_not_validate_target_existence() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        write_source_docs(root, child_body_suffix="Missing target [[ref:work:99999|still links]].")
        result = run_builder(root)
        child = read_json(root / f"docs-viewer/published/docs/studio/by-id/{CHILD_DOC_ID}.json")
        missing_target = read_json(root / "docs-viewer/published/docs/studio/references/by-target/work/99999.json")

    assert result["diagnostics"]["warning_count"] == 0
    assert 'href="/works/?work=99999"' in child["content_html"]
    assert missing_target["target_kind"] == "work"
    assert missing_target["target_id"] == "99999"
    assert missing_target["target_status"] == "rendered"
    assert missing_target["references"][0]["label"] == "still links"
