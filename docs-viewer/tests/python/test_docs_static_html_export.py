#!/usr/bin/env python3
"""Focused checks for Docs Viewer static HTML export."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

from repo_factory import docs_scope_record


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
if str(DOCS_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(DOCS_SERVICES_DIR))

import docs_management_routes as routes  # noqa: E402
import docs_management_service  # noqa: E402
import docs_static_html_export as exporter  # noqa: E402


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_scope_config(root: Path) -> None:
    write_json(
        root / "docs-viewer/config/scopes/docs_scopes.json",
        {
            "schema_version": "docs_scopes_v3",
            "scopes": [
                docs_scope_record("studio", default_doc_id="parent"),
                docs_scope_record(
                    "library",
                    scope_type="public",
                    viewer_base_url="/library/",
                    include_scope_param=False,
                    default_doc_id="library",
                ),
                docs_scope_record("external", scope_type="local_external", default_doc_id="external"),
            ],
        },
    )


def prepare_repo(root: Path, projects_root: Path) -> None:
    os.environ["DOTLINEFORM_PROJECTS_BASE_DIR"] = str(projects_root)
    (projects_root / "docs-viewer").mkdir(parents=True, exist_ok=True)
    write_scope_config(root)
    write_json(
        root / "docs-viewer/scopes/studio/published/documents/index-tree.json",
        {
            "schema": "docs_index_tree_v1",
            "docs": [
                {
                    "doc_id": "parent",
                    "title": "Parent & Root",
                    "content_url": "/docs-viewer/scopes/studio/published/documents/by-id/parent.json",
                    "children": [
                        {
                            "doc_id": "child",
                            "title": "Child",
                            "content_url": "/docs-viewer/scopes/studio/published/documents/by-id/child.json",
                        }
                    ],
                }
            ],
        },
    )
    write_json(
        root / "docs-viewer/scopes/studio/published/documents/by-id/parent.json",
        {
            "doc_id": "parent",
            "title": "Parent & Root",
            "content_html": '<p><a href="/docs/?scope=studio&amp;doc=child">Child</a> <a href="https://example.com/">External</a></p>',
        },
    )
    write_json(
        root / "docs-viewer/scopes/studio/published/documents/by-id/child.json",
        {
            "doc_id": "child",
            "title": "Child",
            "content_html": '<p><a href="/docs/?scope=studio&doc=parent#top">Parent</a></p>',
        },
    )


def test_tree_doc_id_collection_preserves_order() -> None:
    tree = [{"doc_id": "parent", "children": [{"doc_id": "child"}]}, {"doc_id": "sibling"}]
    assert exporter.collect_doc_ids_from_tree(tree) == ["parent", "child", "sibling"]


def test_load_doc_payload_and_reject_unsafe_doc_id() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        write_json(root / "by-id/valid-doc.json", {"doc_id": "valid-doc", "title": "Valid"})

        assert exporter.load_doc_payload(root / "by-id", "valid-doc")["title"] == "Valid"
        try:
            exporter.load_doc_payload(root / "by-id", "../escape")
        except ValueError as exc:
            assert "safe HTML filename" in str(exc)
        else:
            raise AssertionError("unsafe doc ids must be rejected")


def test_render_doc_page_and_rewrite_internal_links() -> None:
    html = exporter.render_doc_html(
        {
            "doc_id": "parent",
            "title": "Parent & Root",
            "content_html": '<h1>Source Heading</h1><p><a href="/docs/?scope=studio&amp;doc=child">Child</a></p>',
        },
        scope="studio",
    )

    assert "<title>Parent &amp; Root</title>" in html
    assert "<h1>Parent &amp; Root</h1>" not in html
    assert html.count("<h1>") == 1
    assert "<h1>Source Heading</h1>" in html
    assert 'href="child.html"' in html
    assert 'href="../styles.css"' in html


def test_render_doc_page_preserves_inline_mermaid_code_without_runtime() -> None:
    mermaid_block = "\n".join(
        [
            '<pre><code class="language-mermaid">flowchart LR',
            "  Source --&gt; StaticExport",
            "</code></pre>",
        ]
    )
    html = exporter.render_doc_html(
        {
            "doc_id": "inline-mermaid",
            "title": "Inline Mermaid",
            "content_html": f"<h1>Inline Mermaid</h1>\n{mermaid_block}",
        },
        scope="studio",
    )

    assert mermaid_block in html
    assert "<svg" not in html
    assert 'data-docs-viewer-diagram-kind="inline-mermaid"' not in html
    assert "mermaid.min.js" not in html
    assert "docs-viewer-inline-mermaid.js" not in html
    assert "<script" not in html


def test_index_page_renders_tree_links() -> None:
    html = exporter.render_index_html(
        {"docs": [{"doc_id": "parent", "title": "Parent", "children": [{"doc_id": "child", "title": "Child"}]}]},
        scope="studio",
        default_doc_id="parent",
        document_count=2,
    )

    assert 'href="docs/parent.html"' in html
    assert 'href="docs/child.html"' in html
    assert "2 documents exported" in html


def test_rewrite_internal_docs_viewer_links_leaves_other_links() -> None:
    html = (
        '<a href="/docs/?scope=studio&amp;doc=child#section">Child</a>'
        '<a href="/docs/?scope=library&amp;doc=library">Library</a>'
        '<a href="https://example.com/">External</a>'
    )

    rewritten = exporter.rewrite_internal_docs_viewer_links(html, scope="studio", link_prefix="")

    assert 'href="child.html#section"' in rewritten
    assert 'href="/docs/?scope=library&amp;doc=library"' in rewritten
    assert 'href="https://example.com/"' in rewritten


def test_apply_export_replaces_destination_and_writes_static_files() -> None:
    with tempfile.TemporaryDirectory() as repo_path, tempfile.TemporaryDirectory() as projects_path:
        repo_root = Path(repo_path)
        projects_root = Path(projects_path)
        prepare_repo(repo_root, projects_root)
        stale_path = projects_root / "docs-export/studio/stale.txt"
        stale_path.parent.mkdir(parents=True)
        stale_path.write_text("stale", encoding="utf-8")

        payload = exporter.build_static_html_export(repo_root, {"scope": "studio", "action": "export"})

        destination = projects_root / "docs-export/studio"
        assert payload["ok"] is True
        assert payload["document_count"] == 2
        assert not stale_path.exists()
        assert (destination / "index.html").exists()
        assert (destination / "styles.css").exists()
        assert 'href="child.html"' in (destination / "docs/parent.html").read_text(encoding="utf-8")
        assert 'href="parent.html#top"' in (destination / "docs/child.html").read_text(encoding="utf-8")


def test_empty_conflict_dir_cleanup_is_narrow() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        destination = Path(temp_path) / "docs-export/studio"
        (destination / "docs 2").mkdir(parents=True)
        (destination / "docs 3").mkdir()
        (destination / "docs 4").mkdir()
        (destination / "docs 4/keep.txt").write_text("keep", encoding="utf-8")
        (destination / "media 2").mkdir()

        removed = exporter.remove_empty_conflict_dirs(destination, {"docs"})

        assert removed == ["docs 2", "docs 3"]
        assert not (destination / "docs 2").exists()
        assert not (destination / "docs 3").exists()
        assert (destination / "docs 4").exists()
        assert (destination / "media 2").exists()


def test_output_path_validation_requires_projects_export_root() -> None:
    with tempfile.TemporaryDirectory() as projects_path:
        os.environ["DOTLINEFORM_PROJECTS_BASE_DIR"] = projects_path
        try:
            exporter.validate_destination_path(Path(projects_path).resolve() / "other/studio")
        except ValueError as exc:
            assert "docs-export" in str(exc)
        else:
            raise AssertionError("destination outside docs-export must be rejected")


def test_export_rejects_public_and_local_external_scopes() -> None:
    with tempfile.TemporaryDirectory() as repo_path, tempfile.TemporaryDirectory() as projects_path:
        repo_root = Path(repo_path)
        projects_root = Path(projects_path)
        prepare_repo(repo_root, projects_root)

        for scope in ("library", "external"):
            try:
                exporter.build_static_html_export(repo_root, {"scope": scope, "action": "export"})
            except ValueError as exc:
                assert "repo-backed local scope" in str(exc)
            else:
                raise AssertionError(f"{scope} should be rejected")


def test_management_apply_route_returns_export_response() -> None:
    with tempfile.TemporaryDirectory() as repo_path, tempfile.TemporaryDirectory() as projects_path:
        repo_root = Path(repo_path)
        projects_root = Path(projects_path)
        prepare_repo(repo_root, projects_root)

        status, payload = docs_management_service.docs_management_post_response(
            repo_root,
            routes.STATIC_HTML_EXPORT_APPLY_PATH,
            {"scope": "studio", "action": "export"},
        )

        assert status.value == 200
        assert payload["ok"] is True
        assert payload["operation"] == "apply"
        assert payload["destination_label"] == "/docs-export/studio/"


def test_delete_export_does_not_require_generated_payloads() -> None:
    with tempfile.TemporaryDirectory() as repo_path, tempfile.TemporaryDirectory() as projects_path:
        repo_root = Path(repo_path)
        projects_root = Path(projects_path)
        os.environ["DOTLINEFORM_PROJECTS_BASE_DIR"] = str(projects_root)
        (projects_root / "docs-viewer").mkdir(parents=True)
        write_scope_config(repo_root)
        destination = projects_root / "docs-export/studio"
        destination.mkdir(parents=True)
        (destination / "index.html").write_text("<!doctype html>", encoding="utf-8")

        payload = exporter.delete_static_html_export(repo_root, {"scope": "studio"})

        assert payload["ok"] is True
        assert payload["deleted"] is True
        assert not destination.exists()
