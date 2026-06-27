#!/usr/bin/env python3
"""Focused checks for Data Sharing docs source metadata helpers."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
SHARED_PYTHON_DIR = REPO_ROOT / "studio" / "shared" / "python"
for path in (DOCS_SERVICES_DIR, SHARED_PYTHON_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from docs_data_sharing import package as data_sharing_package  # noqa: E402
from docs_data_sharing import source_metadata  # noqa: E402


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def scope_config(
    scope_id: str,
    *,
    source: str | None = None,
    output: str | None = None,
    viewer_base_url: str = "/docs/",
    include_scope_param: bool = True,
    allow_unresolved_parent_ids: bool = False,
) -> dict[str, object]:
    config = {
        "scope_id": scope_id,
        "scope_type": "local" if include_scope_param else "public",
        "source": source or f"docs-viewer/source/{scope_id}",
        "media_path_prefix": f"docs/{scope_id}",
        "output": output or f"docs-viewer/generated/docs/{scope_id}",
        "search_output": f"docs-viewer/generated/search/{scope_id}/index.json",
        "viewer_base_url": viewer_base_url,
        "include_scope_param": include_scope_param,
        "default_doc_id": scope_id,
        "allow_unresolved_parent_ids": allow_unresolved_parent_ids,
    }
    if not include_scope_param:
        config["publish_output"] = f"site/assets/data/docs/scopes/{scope_id}"
        config["publish_search_output"] = f"site/assets/data/search/{scope_id}/index.json"
    return config


def write_scope_config(root: Path, scopes: list[dict[str, object]]) -> None:
    write_json(
        root / "site-tools/config/site-tools.json",
        {
            "schema_version": "site_tools_config_v1",
            "media": {
                "base": "https://media.example.test",
            },
        },
    )
    write_json(
        root / "docs-viewer/config/scopes/docs_scopes.json",
        {
            "schema_version": "docs_scopes_v1",
            "scopes": scopes,
        },
    )


def write_doc(
    root: Path,
    scope: str,
    filename: str,
    *,
    doc_id: str,
    title: str,
    parent_id: str = "",
    summary: str = "",
    added_date: str = "2026-01-01",
    last_updated: str = "2026-01-02",
    viewable: bool = True,
    published: bool = True,
    ui_status: str = "",
    body: str = "Body text.",
) -> None:
    lines = [
        "---",
        f"doc_id: {doc_id}",
        f"title: {title}",
        f"added_date: {added_date}",
        f"last_updated: {last_updated}",
    ]
    if summary:
        lines.append(f"summary: {summary}")
    if parent_id:
        lines.append(f"parent_id: {parent_id}")
    if not viewable:
        lines.append("viewable: false")
    if not published:
        lines.append("published: false")
    if ui_status:
        lines.append(f"ui_status: {ui_status}")
    lines.extend(["---", "", body])
    write_text(root / f"docs-viewer/source/{scope}/{filename}", "\n".join(lines))


def test_source_records_include_locked_fields_and_rendered_text() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        write_scope_config(repo_root, [scope_config("studio")])
        write_doc(
            repo_root,
            "studio",
            "parent.md",
            doc_id="parent",
            title="Parent",
            summary="Parent summary.",
            body="# Parent\n\nIntro text.",
        )
        write_doc(
            repo_root,
            "studio",
            "child.md",
            doc_id="child",
            title="Child",
            parent_id="parent",
            viewable=False,
            published=False,
            ui_status="draft",
            body="# Child\n\n## Details\n\nChild **body** with [parent](parent.md).",
        )

        context = source_metadata.load_data_sharing_docs_source_context(repo_root, "studio")

    child = context.records_by_id["child"]
    assert child.scope == "studio"
    assert child.doc_id == "child"
    assert child.title == "Child"
    assert child.published is False
    assert child.viewable is False
    assert child.parent_id == "parent"
    assert child.parent_title == "Parent"
    assert child.ui_status == "draft"
    assert child.source_path == "docs-viewer/source/studio/child.md"
    assert child.viewer_url == "/docs/?scope=studio&doc=child"
    assert child.content_text_length == len("Details\n\nChild body with parent.")
    assert source_metadata.data_sharing_doc_headings(context, "child") == ["Details"]
    assert source_metadata.data_sharing_doc_content_text(context, "child") == "Details\n\nChild body with parent."
    assert 'href="parent.md"' in source_metadata.render_data_sharing_doc_html(context, "child")


def test_source_metadata_uses_scope_config_without_scope_name_branches() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        write_scope_config(
            repo_root,
            [
                scope_config("studio"),
                scope_config(
                    "research",
                    source="docs-viewer/source/research",
                    output="custom/generated/docs/research",
                    viewer_base_url="/research/",
                    include_scope_param=False,
                ),
            ],
        )
        write_doc(repo_root, "studio", "studio.md", doc_id="studio-doc", title="Studio Doc")
        write_doc(repo_root, "research", "research.md", doc_id="research-doc", title="Research Doc")

        studio_records = source_metadata.load_data_sharing_docs_source_records(repo_root, "studio")
        research_records = source_metadata.load_data_sharing_docs_source_records(repo_root, "research")

    assert [record.doc_id for record in studio_records] == ["studio-doc"]
    assert [record.doc_id for record in research_records] == ["research-doc"]
    assert research_records[0].viewer_url == "/research/?doc=research-doc"


def test_duplicate_doc_ids_and_missing_source_roots_fail_visibly() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        write_scope_config(repo_root, [scope_config("studio"), scope_config("missing")])
        write_doc(repo_root, "studio", "one.md", doc_id="same", title="One")
        write_doc(repo_root, "studio", "two.md", doc_id="same", title="Two")

        try:
            source_metadata.load_data_sharing_docs_source_context(repo_root, "studio")
        except RuntimeError as exc:
            assert "Duplicate doc_id" in str(exc)
        else:
            raise AssertionError("Expected duplicate source doc_id values to fail")

        try:
            source_metadata.load_data_sharing_docs_source_context(repo_root, "missing")
        except RuntimeError as exc:
            assert "missing source root" in str(exc)
        else:
            raise AssertionError("Expected missing source root to fail")


def test_unresolved_parent_policy_follows_scope_config() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        write_scope_config(
            repo_root,
            [
                scope_config("strict"),
                scope_config("loose", allow_unresolved_parent_ids=True),
            ],
        )
        write_doc(repo_root, "strict", "child.md", doc_id="strict-child", title="Strict Child", parent_id="missing")
        write_doc(repo_root, "loose", "child.md", doc_id="loose-child", title="Loose Child", parent_id="missing")

        try:
            source_metadata.load_data_sharing_docs_source_context(repo_root, "strict")
        except RuntimeError as exc:
            assert "Unknown parent_id" in str(exc)
        else:
            raise AssertionError("Expected strict unresolved parent to fail")

        context = source_metadata.load_data_sharing_docs_source_context(repo_root, "loose")

    record = context.records_by_id["loose-child"]
    assert record.parent_id == "missing"
    assert record.parent_title == ""


def test_helper_loads_source_metadata_context() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        write_scope_config(repo_root, [scope_config("studio")])
        write_doc(repo_root, "studio", "doc.md", doc_id="doc", title="Source Title", body="# Source Title\n\nSource body.")

        context = source_metadata.load_data_sharing_docs_source_context(repo_root, "studio")

    assert context.records_by_id["doc"].title == "Source Title"
    assert source_metadata.data_sharing_doc_content_text(context, "doc") == "Source body."


def test_selectable_document_records_use_source_metadata() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        write_scope_config(repo_root, [scope_config("studio")])
        write_doc(
            repo_root,
            "studio",
            "doc.md",
            doc_id="doc",
            title="Source Title",
            summary="Source summary.",
            published=False,
            body="# Source Title\n\nSource body.",
        )

        payload = data_sharing_package.selectable_document_records(
            repo_root,
            scope="studio",
            selection_model="documents",
        )

    assert payload["ok"] is True
    assert payload["source"]["source"] == "docs_source_metadata"
    assert payload["records"] == [
        {
            "id": "doc",
            "name": "Source Title",
            "doc_id": "doc",
            "title": "Source Title",
            "type": "document",
            "meta": "doc",
            "parent_id": "",
            "published": False,
            "viewable": True,
            "selectable": False,
            "children": [],
            "issues": [{"level": "warning", "message": "Document is not published."}],
            "content_text_length": len("Source body."),
            "summary": "Source summary.",
        }
    ]


def test_active_data_sharing_metadata_services_use_source_metadata_owner() -> None:
    service_paths = {
        "package": REPO_ROOT / "docs-viewer/services/docs_data_sharing/package.py",
        "export": REPO_ROOT / "docs-viewer/services/docs_export.py",
        "import": REPO_ROOT / "docs-viewer/services/docs_import.py",
    }
    source_text_by_service = {name: path.read_text(encoding="utf-8") for name, path in service_paths.items()}

    assert all("from docs_data_sharing import source_metadata" in text for text in source_text_by_service.values())
    assert "source_metadata.load_data_sharing_docs_source_records" in source_text_by_service["package"]
    assert "source_metadata.load_data_sharing_docs_source_context" in source_text_by_service["export"]
    assert "source_metadata.load_data_sharing_docs_source_context" in source_text_by_service["import"]


def test_unknown_doc_path_safety() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        write_scope_config(repo_root, [scope_config("nested")])
        write_doc(
            repo_root,
            "nested",
            "nested-doc.md",
            doc_id="nested-doc",
            title="Nested Doc",
        )

        context = source_metadata.load_data_sharing_docs_source_context(repo_root, "nested")

        try:
            source_metadata.render_data_sharing_doc_html(context, "../nested-doc")
        except ValueError as exc:
            assert "unknown doc_id" in str(exc)
        else:
            raise AssertionError("Expected unsafe unknown doc_id to be rejected")

    assert context.records_by_id["nested-doc"].source_path == "docs-viewer/source/nested/nested-doc.md"


def test_nested_source_markdown_is_rejected() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        write_scope_config(repo_root, [scope_config("nested")])
        write_doc(
            repo_root,
            "nested",
            "section/nested-doc.md",
            doc_id="nested-doc",
            title="Nested Doc",
        )

        try:
            source_metadata.load_data_sharing_docs_source_context(repo_root, "nested")
        except RuntimeError as exc:
            assert "Nested markdown docs are not supported" in str(exc)
            assert "section/nested-doc.md" in str(exc)
        else:
            raise AssertionError("Expected nested source Markdown to be rejected")


def main() -> None:
    tests = [
        test_source_records_include_locked_fields_and_rendered_text,
        test_source_metadata_uses_scope_config_without_scope_name_branches,
        test_duplicate_doc_ids_and_missing_source_roots_fail_visibly,
        test_unresolved_parent_policy_follows_scope_config,
        test_helper_loads_source_metadata_context,
        test_selectable_document_records_use_source_metadata,
        test_active_data_sharing_metadata_services_use_source_metadata_owner,
        test_unknown_doc_path_safety,
        test_nested_source_markdown_is_rejected,
    ]
    for test in tests:
        test()
    print("Docs Data Sharing source metadata tests OK")


if __name__ == "__main__":
    main()
