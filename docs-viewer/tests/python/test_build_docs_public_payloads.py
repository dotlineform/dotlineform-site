#!/usr/bin/env python3
"""Python Docs Viewer public payload builder tests."""

from __future__ import annotations

import tempfile
from pathlib import Path

import build_docs
from docs_scope_config import load_docs_scope_configs

from build_docs_test_support import (
    CHILD_DOC_ID,
    HIDDEN_CHILD_DOC_ID,
    HIDDEN_DOC_ID,
    MANAGE_CHILD_DOC_ID,
    MANAGE_ROOT_DOC_ID,
    PARENT_DOC_ID,
    read_json,
    write_public_scope_config,
    write_public_source_docs,
    write_site_tools_config,
    write_text,
)


REPORT_DOC_ID = "d-20260624-000000-000008"

def test_python_docs_builder_public_generated_payloads_include_manage_rows() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        write_site_tools_config(root, media_base="")
        write_public_scope_config(root)
        write_public_source_docs(root)
        config = load_docs_scope_configs(root)["library"]
        result = build_docs.DocsDataBuilder(repo_root=root, config=config).run(write=True)
        index_tree = read_json(root / "docs-viewer/generated/docs/library/index-tree.json")
        recently_added = read_json(root / "docs-viewer/generated/docs/library/recently-added.json")
        child_payload = read_json(root / f"docs-viewer/generated/docs/library/by-id/{CHILD_DOC_ID}.json")
        hidden_payload = read_json(root / f"docs-viewer/generated/docs/library/by-id/{HIDDEN_DOC_ID}.json")
        browser_config = build_docs.browser_scope_config_payload(root, [config])

    assert result["diagnostics"]["docs_emitted"] == 6
    public_tree_forbidden_keys = {
        "summary",
        "date",
        "date_display",
        "added_date",
        "last_updated",
        "source_path",
        "viewer_url",
        "content_text_length",
        "viewer_report",
        "viewer_report_scope",
        "viewer_report_access",
        "viewer_report_preset",
        "viewer_report_subscope",
    }
    public_recent_forbidden_keys = {
        "summary",
        "date",
        "date_display",
        "last_updated",
        "source_path",
        "viewer_url",
        "content_text_length",
        "viewer_report",
        "viewer_report_scope",
        "viewer_report_access",
        "viewer_report_preset",
        "viewer_report_subscope",
        "viewable",
        "ui_status",
    }
    public_by_id_forbidden_keys = {
        "doc_id",
        "added_date",
        "parent_id",
        "source_path",
        "viewer_url",
        "ui_status",
        "viewable",
        "content_text_length",
        "viewer_report",
        "viewer_report_scope",
        "viewer_report_access",
        "viewer_report_preset",
        "viewer_report_subscope",
    }

    assert index_tree["schema"] == "docs_index_tree_v1"
    assert [doc["doc_id"] for doc in index_tree["docs"]] == [MANAGE_ROOT_DOC_ID, PARENT_DOC_ID]
    assert [doc["doc_id"] for doc in index_tree["docs"][0]["children"]] == [MANAGE_CHILD_DOC_ID]
    assert [doc["doc_id"] for doc in index_tree["docs"][1]["children"]] == [CHILD_DOC_ID, HIDDEN_DOC_ID]
    assert [doc["doc_id"] for doc in index_tree["docs"][1]["children"][1]["children"]] == [HIDDEN_CHILD_DOC_ID]
    flattened_tree_docs = [
        index_tree["docs"][0],
        *index_tree["docs"][0]["children"],
        index_tree["docs"][1],
        *index_tree["docs"][1]["children"],
        *index_tree["docs"][1]["children"][1]["children"],
    ]
    assert all("parent_id" not in doc for doc in flattened_tree_docs)
    assert index_tree["docs"][1]["children"][1]["viewable"] is False
    assert all(public_tree_forbidden_keys.isdisjoint(doc) for doc in flattened_tree_docs)
    assert recently_added["schema"] == "docs_recently_added_v1"
    assert recently_added["limit"] == 2
    assert [doc["doc_id"] for doc in recently_added["docs"]] == [MANAGE_CHILD_DOC_ID, HIDDEN_CHILD_DOC_ID]
    assert recently_added["docs"][0]["parent_title"] == "Manage Root"
    assert all(public_recent_forbidden_keys.isdisjoint(doc) for doc in recently_added["docs"])
    assert set(child_payload) == {"content_html", "date", "date_display", "last_updated", "summary", "title"}
    assert child_payload["title"] == "Child"
    assert child_payload["date"] == "2026-06-02"
    assert child_payload["date_display"] == "June 2026"
    assert child_payload["summary"] == "Child summary"
    assert child_payload["last_updated"] == "2026-06-03"
    assert "content_html" in child_payload
    assert public_by_id_forbidden_keys.isdisjoint(child_payload)
    assert hidden_payload["title"] == "Hidden"
    assert browser_config["scopes"][0]["index_tree_url"] == "/assets/data/docs/scopes/library/index-tree.json"
    assert browser_config["scopes"][0]["recently_added_url"] == "/assets/data/docs/scopes/library/recently-added.json"
    assert index_tree["docs"][1]["content_url"] == f"/assets/data/docs/scopes/library/by-id/{PARENT_DOC_ID}.json"

def test_python_docs_builder_public_payloads_include_promoted_report_metadata() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        write_site_tools_config(root, media_base="")
        write_public_scope_config(root)
        write_public_source_docs(root)
        write_text(
            root / f"docs-viewer/source/library/{REPORT_DOC_ID}.md",
            f"""---
doc_id: {REPORT_DOC_ID}
title: Report
added_date: 2026-06-24
last_updated: 2026-06-24
parent_id: {PARENT_DOC_ID}
viewer_report: docs_subscope
viewer_report_access: public
viewer_report_subscope: tags
---
# Report
""",
        )
        config = load_docs_scope_configs(root)["library"]

        build_docs.DocsDataBuilder(repo_root=root, config=config).run(write=True)
        report_payload = read_json(root / f"docs-viewer/generated/docs/library/by-id/{REPORT_DOC_ID}.json")
        index_tree = read_json(root / "docs-viewer/generated/docs/library/index-tree.json")

    assert report_payload["viewer_report"] == "docs_subscope"
    assert report_payload["viewer_report_access"] == "public"
    assert report_payload["viewer_report_subscope"] == "tags"
    report_row = index_tree["docs"][1]["children"][2]
    assert report_row["doc_id"] == REPORT_DOC_ID
    assert "viewer_report" not in report_row
    assert "viewer_report_access" not in report_row
    assert "viewer_report_subscope" not in report_row
