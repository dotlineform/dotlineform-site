#!/usr/bin/env python3
"""Python Docs Viewer builder payload tests."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from build_docs_test_support import prepare_repo, read_json, run_builder, write_source_docs

def test_python_docs_builder_writes_docs_payloads_and_references() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        result = run_builder(root)

        index_tree = read_json(root / "docs-viewer/generated/docs/studio/index-tree.json")
        recently_added = read_json(root / "docs-viewer/generated/docs/studio/recently-added.json")
        child = read_json(root / "docs-viewer/generated/docs/studio/by-id/child.json")
        references_index = read_json(root / "docs-viewer/generated/docs/studio/references/index.json")
        target_payload = read_json(root / "docs-viewer/generated/docs/studio/references/by-target/work/00638.json")
        by_doc = read_json(root / "docs-viewer/generated/docs/studio/references/by-doc/child.json")

    docs = result["index_payload"]["docs"]
    assert [doc["doc_id"] for doc in docs] == ["parent", "child"]
    assert docs[1]["summary"] == "Child summary"
    assert docs[1]["date"] == "2026-06-02"
    assert docs[1]["date_display"] == "June 2026"
    assert docs[1]["ui_status"] == "done"
    assert docs[1]["content_url"] == "/docs-viewer/generated/docs/studio/by-id/child.json"
    assert isinstance(docs[1]["content_text_length"], int)

    assert index_tree["schema"] == "docs_index_tree_v1"
    assert [doc["doc_id"] for doc in index_tree["docs"]] == ["parent"]
    assert [doc["doc_id"] for doc in index_tree["docs"][0]["children"]] == ["child"]
    tree_child = index_tree["docs"][0]["children"][0]
    assert tree_child == {
        "doc_id": "child",
        "title": "Child",
        "content_url": "/docs-viewer/generated/docs/studio/by-id/child.json",
        "ui_status": "done",
    }
    assert "parent_id" not in tree_child
    assert "summary" not in tree_child
    assert "added_date" not in tree_child
    assert "last_updated" not in tree_child
    assert "source_path" not in tree_child
    assert "viewer_url" not in tree_child
    assert "content_text_length" not in tree_child

    assert recently_added["schema"] == "docs_recently_added_v1"
    assert recently_added["limit"] == 10
    assert recently_added["docs"][0]["doc_id"] == "child"
    assert recently_added["docs"][0]["added_date"] == "2026-06-01"
    assert recently_added["docs"][0]["parent_title"] == "Parent"

    content_html = child["content_html"]
    assert 'href="/docs/?scope=studio&amp;doc=parent"' in content_html
    assert 'src="https://media.example.test/docs/studio/diagram.png"' in content_html
    assert (
        '<img src="https://media.example.test/docs/studio/measured-diagram.png" '
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
    assert references_index["targets"][0]["bucket_url"] == "/docs-viewer/generated/docs/studio/references/by-target/work/00638.json"
    assert target_payload["header"]["schema"] == "docs_semantic_references_by_target_v1"
    assert target_payload["target_kind"] == "work"
    assert target_payload["references"][0]["source_doc_id"] == "child"
    assert by_doc["references"][0]["label"] == "three signs"
    assert result["diagnostics"]["docs_emitted"] == 2
    assert result["diagnostics"]["index_tree_changed"] == 1
    assert result["diagnostics"]["recently_added_changed"] == 1

def test_python_docs_builder_preserves_existing_payloads_for_targeted_builds() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        run_builder(root)
        parent_before = read_json(root / "docs-viewer/generated/docs/studio/by-id/parent.json")
        write_source_docs(root, child_body_suffix="Updated targeted body.")
        result = run_builder(root, only_doc_ids=["child"])
        parent_after = read_json(root / "docs-viewer/generated/docs/studio/by-id/parent.json")
        child_after = read_json(root / "docs-viewer/generated/docs/studio/by-id/child.json")

    assert parent_after == parent_before
    assert "Updated targeted body." in child_after["content_html"]
    assert result["diagnostics"]["build_mode"] == "targeted"
    assert result["diagnostics"]["only_doc_ids"] == ["child"]
    assert "parent" not in result["write_plan"]["changed_item_ids"]

def test_python_docs_builder_registry_backed_references_do_not_validate_target_existence() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        prepare_repo(root)
        write_source_docs(root, child_body_suffix="Missing target [[ref:work:99999|still links]].")
        result = run_builder(root)
        child = read_json(root / "docs-viewer/generated/docs/studio/by-id/child.json")
        missing_target = read_json(root / "docs-viewer/generated/docs/studio/references/by-target/work/99999.json")

    assert result["diagnostics"]["warning_count"] == 0
    assert 'href="/works/?work=99999"' in child["content_html"]
    assert missing_target["target_kind"] == "work"
    assert missing_target["target_id"] == "99999"
    assert missing_target["target_status"] == "rendered"
    assert missing_target["references"][0]["label"] == "still links"
