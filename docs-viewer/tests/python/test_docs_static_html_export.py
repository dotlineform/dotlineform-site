#!/usr/bin/env python3
"""Focused checks for Docs Viewer static HTML export."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from repo_factory import docs_scope_record


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
if str(DOCS_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(DOCS_SERVICES_DIR))

import docs_management_routes as routes  # noqa: E402
import docs_management_service  # noqa: E402
import docs_static_html_export as exporter  # noqa: E402
import docs_static_html_export_media as media_export  # noqa: E402


FIXED_EXPORT_DATE = date(2026, 7, 31)


def snapshot_apply_body(preview: dict[str, object], *, replace_existing: bool = False) -> dict[str, object]:
    return {
        "scope": preview["scope"],
        "doc_ids": preview["doc_ids"],
        "export_date": preview["export_date"],
        "plan_revision": preview["plan_revision"],
        "target_revision": preview["target_revision"],
        "confirm": True,
        "replace_existing": replace_existing,
    }


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_scope_config(root: Path) -> None:
    write_json(
        root / "docs-viewer/config/scopes/docs_scopes.json",
        {
            "schema_version": "docs_scopes_v3",
            "scopes": [
                docs_scope_record(
                    "studio",
                    default_doc_id="parent",
                    media_types=("img", "svg", "files", "html"),
                ),
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


def write_generated_scope(
    generated_root: Path,
    rows: list[dict[str, object]],
    payloads: list[dict[str, object]],
) -> None:
    write_json(
        generated_root / "index-tree.json",
        {
            "schema": "docs_index_tree_v1",
            "docs": rows,
        },
    )
    for payload in payloads:
        doc_id = str(payload["doc_id"])
        write_json(generated_root / f"by-id/{doc_id}.json", payload)


def prepare_repo(root: Path, projects_root: Path) -> None:
    os.environ["DOTLINEFORM_PROJECTS_BASE_DIR"] = str(projects_root)
    (projects_root / "docs-viewer").mkdir(parents=True, exist_ok=True)
    write_scope_config(root)
    write_generated_scope(
        root / "docs-viewer/scopes/studio/published/documents",
        [
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
            },
            {
                "doc_id": "sibling",
                "title": "Sibling",
                "content_url": "/docs-viewer/scopes/studio/published/documents/by-id/sibling.json",
            },
        ],
        [
            {
                "doc_id": "parent",
                "title": "Parent & Root",
                "report": {
                    "id": "reports_list",
                    "access": "local",
                    "scope": None,
                    "preset": None,
                    "sub_scope": None,
                },
                "content_html": (
                    '<p><a href="/docs/?scope=studio&amp;doc=child">Child</a> '
                    '<a href="https://example.com/">External</a></p>'
                    '<section class="docsViewerReport" data-docs-viewer-report-host '
                    'aria-label="Document report"></section>'
                ),
            },
            {
                "doc_id": "child",
                "title": "Child",
                "content_html": '<p><a href="/docs/?scope=studio&doc=parent#top">Parent</a></p>',
            },
            {
                "doc_id": "sibling",
                "title": "Sibling",
                "content_html": "<p>Sibling body</p>",
            },
        ],
    )
    write_generated_scope(
        root / "docs-viewer/scopes/library/published/documents",
        [{"doc_id": "library", "title": "Library"}],
        [{"doc_id": "library", "title": "Library", "content_html": "<p>Library body</p>"}],
    )
    write_json(
        root / "docs-viewer/scopes/library/published/documents/by-id/library.json",
        {"title": "Library", "content_html": "<p>Library body</p>"},
    )
    write_generated_scope(
        projects_root / "docs-viewer/scopes/external/published/documents",
        [{"doc_id": "external", "title": "External"}],
        [{"doc_id": "external", "title": "External", "content_html": "<p>External body</p>"}],
    )


def test_tree_doc_id_collection_preserves_order() -> None:
    tree = [{"doc_id": "parent", "children": [{"doc_id": "child"}]}, {"doc_id": "sibling"}]
    assert exporter.collect_doc_ids_from_tree(tree) == ["parent", "child", "sibling"]


def test_snapshot_preview_plans_exact_single_partial_and_complete_sets_without_writes() -> None:
    with tempfile.TemporaryDirectory() as repo_path, tempfile.TemporaryDirectory() as projects_path:
        repo_root = Path(repo_path)
        projects_root = Path(projects_path)
        prepare_repo(repo_root, projects_root)

        single = exporter.plan_static_html_snapshot(
            repo_root,
            {"scope": "studio", "doc_ids": ["parent"]},
            export_date=FIXED_EXPORT_DATE,
        )
        assert single.doc_ids == ("parent",)
        assert single.selection_kind == "single"
        assert single.folder_name == "studio selection - 2026-07-31"
        assert single.default_doc_id == "parent"
        assert single.index_tree["docs"] == [
            {
                "doc_id": "parent",
                "title": "Parent & Root",
                "content_url": "/docs-viewer/scopes/studio/published/documents/by-id/parent.json",
            }
        ]

        partial = exporter.plan_static_html_snapshot(
            repo_root,
            {"scope": "studio", "doc_ids": ["sibling", "child"]},
            export_date=FIXED_EXPORT_DATE,
        )
        assert partial.doc_ids == ("child", "sibling")
        assert partial.selection_kind == "partial"
        assert partial.folder_name == "studio selection - 2026-07-31"
        assert partial.default_doc_id == "child"
        assert [row["doc_id"] for row in partial.index_tree["docs"]] == ["child", "sibling"]
        assert all("children" not in row for row in partial.index_tree["docs"])

        partial_reordered = exporter.plan_static_html_snapshot(
            repo_root,
            {"scope": "studio", "doc_ids": ["child", "sibling"]},
            export_date=FIXED_EXPORT_DATE,
        )
        assert partial_reordered.plan_revision == partial.plan_revision

        complete = exporter.plan_static_html_snapshot(
            repo_root,
            {"scope": "studio", "doc_ids": ["sibling", "child", "parent"]},
            export_date=FIXED_EXPORT_DATE,
        )
        assert complete.doc_ids == ("parent", "child", "sibling")
        assert complete.selection_kind == "complete"
        assert complete.folder_name == "studio - 2026-07-31"
        assert complete.default_doc_id == "parent"
        assert complete.index_tree["docs"][0]["children"][0]["doc_id"] == "child"
        assert not (projects_root / "docs-export").exists()


def test_snapshot_preview_rejects_invalid_or_inferred_selection_fields() -> None:
    with tempfile.TemporaryDirectory() as repo_path, tempfile.TemporaryDirectory() as projects_path:
        repo_root = Path(repo_path)
        prepare_repo(repo_root, Path(projects_path))
        invalid_requests = [
            ({"scope": "studio"}, "non-empty array"),
            ({"scope": "studio", "doc_ids": []}, "non-empty array"),
            ({"scope": "studio", "doc_ids": ["parent", "parent"]}, "duplicate doc_id"),
            ({"scope": "studio", "doc_ids": ["library"]}, "active generated scope"),
            ({"scope": "studio", "doc_ids": ["../escape"]}, "safe HTML filename"),
            ({"scope": "studio", "doc_ids": ["parent"], "action": "export"}, "action is not supported"),
            ({"scope": "studio", "doc_ids": ["parent"], "mode": "complete"}, "mode is not supported"),
            (
                {"scope": "studio", "doc_ids": ["parent"], "include_descendants": True},
                "include_descendants is not supported",
            ),
            ({"scope": "studio", "sub_scope": "tags", "doc_ids": ["parent"]}, "sub_scope is not supported"),
        ]
        for body, expected_message in invalid_requests:
            try:
                exporter.plan_static_html_snapshot(repo_root, body, export_date=FIXED_EXPORT_DATE)
            except ValueError as exc:
                assert expected_message in str(exc)
            else:
                raise AssertionError(f"invalid snapshot request should fail: {body!r}")


def test_snapshot_plans_and_renders_repo_public_and_external_local_generated_payloads() -> None:
    with tempfile.TemporaryDirectory() as repo_path, tempfile.TemporaryDirectory() as projects_path:
        repo_root = Path(repo_path)
        prepare_repo(repo_root, Path(projects_path))

        for scope, doc_id, folder_name in (
            ("studio", "parent", "studio selection - 2026-07-31"),
            ("library", "library", "library - 2026-07-31"),
            ("external", "external", "external - 2026-07-31"),
        ):
            plan = exporter.plan_static_html_snapshot(
                repo_root,
                {"scope": scope, "doc_ids": [doc_id]},
                export_date=FIXED_EXPORT_DATE,
            )
            assert plan.scope == scope
            assert plan.doc_ids == (doc_id,)
            assert plan.folder_name == folder_name
            files = exporter.compute_snapshot_files(plan, generated_at="2026-07-31T12:00:00+01:00")
            assert Path("docs") / f"{doc_id}.html" in files
            if doc_id == "parent":
                assert b"data-docs-viewer-report-host" in files[
                    Path("docs") / "parent.html"
                ]


def test_snapshot_capability_accepts_readable_repo_public_and_external_generated_payloads() -> None:
    with tempfile.TemporaryDirectory() as repo_path, tempfile.TemporaryDirectory() as projects_path:
        repo_root = Path(repo_path)
        prepare_repo(repo_root, Path(projects_path))
        configs = exporter.load_docs_scope_configs(repo_root)
        workspace = exporter.static_html_export_capability()

        assert workspace == {"preview": True, "apply": True, "error": ""}
        for scope, document_count in (("studio", 3), ("library", 1), ("external", 1)):
            capability = exporter.scope_static_html_export_capability(
                repo_root,
                scope,
                configs[scope],
                workspace_available=True,
            )
            assert capability == {
                "preview": True,
                "apply": True,
                "document_count": document_count,
                "default_doc_id": configs[scope].default_doc_id,
                "error": "",
            }


def test_snapshot_folder_labels_are_portable_and_bounded() -> None:
    assert exporter.normalize_snapshot_folder_label("CON") == "CON snapshot"
    assert exporter.normalize_snapshot_folder_label("A/B\\C:*?") == "A-B-C---"
    assert exporter.normalize_snapshot_folder_label(" . ") == "snapshot"
    assert len(exporter.normalize_snapshot_folder_label("é" * 300).encode("utf-8")) <= 180


def test_snapshot_preview_reports_absent_recognized_unrecognized_and_non_directory_targets() -> None:
    with tempfile.TemporaryDirectory() as repo_path, tempfile.TemporaryDirectory() as projects_path:
        repo_root = Path(repo_path)
        projects_root = Path(projects_path)
        prepare_repo(repo_root, projects_root)

        absent = exporter.preview_static_html_export(
            repo_root,
            {"scope": "studio", "doc_ids": ["parent"]},
            export_date=FIXED_EXPORT_DATE,
        )
        assert absent["target_state"] == "absent"
        assert absent["replacement_required"] is False
        assert absent["replace_allowed"] is True
        assert "destination" not in absent

        recognized_root = projects_root / "docs-export/studio selection - 2026-07-31"
        write_json(
            recognized_root / exporter.SNAPSHOT_PROVENANCE_FILENAME,
            {
                "schema_version": exporter.SNAPSHOT_SCHEMA_VERSION,
                "scope": "studio",
                "doc_ids": ["parent"],
                "selection_kind": "single",
                "document_count": 1,
                "media_count": 0,
                "media_bytes": 0,
                "media": [],
                "external_dependency_count": 0,
                "external_dependencies": [],
                "generated_at": "2026-07-31T12:00:00+01:00",
            },
        )
        recognized = exporter.preview_static_html_export(
            repo_root,
            {"scope": "studio", "doc_ids": ["parent"]},
            export_date=FIXED_EXPORT_DATE,
        )
        assert recognized["target_state"] == "recognized"
        assert recognized["replacement_required"] is True
        assert recognized["existing_snapshot"]["scope"] == "studio"
        assert recognized["existing_snapshot"]["selection_kind"] == "single"
        assert recognized["existing_snapshot"]["document_count"] == 1
        assert recognized["existing_snapshot"]["media_count"] == 0
        assert recognized["existing_snapshot"]["media_bytes"] == 0
        assert recognized["existing_snapshot"]["external_dependency_count"] == 0
        assert recognized["existing_snapshot"]["generated_at"] == "2026-07-31T12:00:00+01:00"
        assert len(recognized["existing_snapshot"]["selection_revision"]) == 64
        first_target_revision = recognized["target_revision"]
        extra_path = recognized_root / "extra.txt"
        extra_path.write_text("changed", encoding="utf-8")
        changed = exporter.preview_static_html_export(
            repo_root,
            {"scope": "studio", "doc_ids": ["parent"]},
            export_date=FIXED_EXPORT_DATE,
        )
        assert changed["target_revision"] != first_target_revision
        changed_stat = extra_path.stat()
        extra_path.write_text("altered", encoding="utf-8")
        os.utime(extra_path, ns=(changed_stat.st_atime_ns, changed_stat.st_mtime_ns))
        content_changed = exporter.preview_static_html_export(
            repo_root,
            {"scope": "studio", "doc_ids": ["parent"]},
            export_date=FIXED_EXPORT_DATE,
        )
        assert content_changed["target_revision"] != changed["target_revision"]

        unrecognized_root = projects_root / "docs-export/studio selection - 2026-07-30"
        write_json(
            unrecognized_root / exporter.SNAPSHOT_PROVENANCE_FILENAME,
            {
                "schema_version": exporter.SNAPSHOT_SCHEMA_VERSION,
                "scope": "studio",
                "doc_ids": ["child", "sibling"],
                "selection_kind": "partial",
                "document_count": 1,
                "generated_at": "2026-07-31T12:00:00+01:00",
            },
        )
        unrecognized = exporter.preview_static_html_export(
            repo_root,
            {"scope": "studio", "doc_ids": ["child", "sibling"]},
            export_date=date(2026, 7, 30),
        )
        assert unrecognized["target_state"] == "unrecognized"
        assert unrecognized["existing_snapshot"] is None
        assert unrecognized["replacement_required"] is True

        non_directory_root = projects_root / "docs-export/studio - 2026-07-31"
        non_directory_root.write_text("collision", encoding="utf-8")
        non_directory = exporter.preview_static_html_export(
            repo_root,
            {"scope": "studio", "doc_ids": ["parent", "child", "sibling"]},
            export_date=FIXED_EXPORT_DATE,
        )
        assert non_directory["target_state"] == "non_directory"
        assert non_directory["replace_allowed"] is False

        symlink_root = projects_root / "docs-export/studio selection - 2026-07-29"
        symlink_root.symlink_to(recognized_root, target_is_directory=True)
        symlink = exporter.preview_static_html_export(
            repo_root,
            {"scope": "studio", "doc_ids": ["child"]},
            export_date=date(2026, 7, 29),
        )
        assert symlink["target_state"] == "non_directory"
        assert symlink["replace_allowed"] is False

        version_one_root = projects_root / "docs-export/studio selection - 2026-07-28"
        write_json(
            version_one_root / exporter.SNAPSHOT_PROVENANCE_FILENAME,
            {
                "schema_version": "docs_static_html_snapshot_v1",
                "scope": "studio",
                "doc_ids": ["parent"],
                "selection_kind": "single",
                "document_count": 1,
                "generated_at": "2026-07-31T12:00:00+01:00",
            },
        )
        version_one = exporter.preview_static_html_export(
            repo_root,
            {"scope": "studio", "doc_ids": ["parent"]},
            export_date=date(2026, 7, 28),
        )
        assert version_one["target_state"] == "unrecognized"
        assert version_one["replacement_required"] is True


def test_snapshot_link_rewriting_only_localizes_included_documents() -> None:
    html = (
        '<a href="/docs/?scope=studio&amp;doc=child">Child</a>'
        '<a href="/docs/?scope=studio&amp;doc=sibling">Sibling</a>'
    )
    rewritten = exporter.rewrite_internal_docs_viewer_links(
        html,
        scope="studio",
        link_prefix="",
        included_doc_ids={"child"},
    )
    assert 'href="child.html"' in rewritten
    assert 'href="/docs/?scope=studio&amp;doc=sibling"' in rewritten


def test_snapshot_preview_missing_payload_error_omits_filesystem_path() -> None:
    with tempfile.TemporaryDirectory() as repo_path, tempfile.TemporaryDirectory() as projects_path:
        repo_root = Path(repo_path)
        prepare_repo(repo_root, Path(projects_path))
        (repo_root / "docs-viewer/scopes/studio/published/documents/by-id/sibling.json").unlink()

        try:
            exporter.preview_static_html_export(
                repo_root,
                {"scope": "studio", "doc_ids": ["sibling"]},
                export_date=FIXED_EXPORT_DATE,
            )
        except FileNotFoundError as exc:
            assert str(exc) == "selected document payload not found for scope studio"
            assert repo_path not in str(exc)
        else:
            raise AssertionError("missing selected payload should fail")


def test_load_doc_payload_normalizes_filename_identity_and_rejects_unsafe_doc_id() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        write_json(root / "by-id/valid-doc.json", {"doc_id": "valid-doc", "title": "Valid"})
        write_json(root / "by-id/public-doc.json", {"title": "Public"})

        assert exporter.load_doc_payload(root / "by-id", "valid-doc")["title"] == "Valid"
        assert exporter.load_doc_payload(root / "by-id", "public-doc") == {
            "doc_id": "public-doc",
            "title": "Public",
        }
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
    assert "1 document exported" in exporter.render_index_html(
        {"docs": [{"doc_id": "parent", "title": "Parent"}]},
        scope="studio",
        default_doc_id="parent",
        document_count=1,
    )


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


def test_snapshot_apply_creates_exact_partial_artifact_with_provenance() -> None:
    with tempfile.TemporaryDirectory() as repo_path, tempfile.TemporaryDirectory() as projects_path:
        repo_root = Path(repo_path)
        projects_root = Path(projects_path)
        prepare_repo(repo_root, projects_root)
        preview = exporter.preview_static_html_export(
            repo_root,
            {"scope": "studio", "doc_ids": ["sibling", "child"]},
            export_date=FIXED_EXPORT_DATE,
        )

        payload = exporter.apply_static_html_snapshot(repo_root, snapshot_apply_body(preview))

        destination = projects_root / "docs-export/studio selection - 2026-07-31"
        assert payload["ok"] is True
        assert payload["schema_version"] == exporter.SNAPSHOT_APPLY_SCHEMA_VERSION
        assert payload["doc_ids"] == ["child", "sibling"]
        assert payload["document_count"] == 2
        assert payload["file_count"] == 5
        assert payload["replaced"] is False
        assert payload["destination_label"] == "/docs-export/studio selection - 2026-07-31/"
        assert "destination" not in payload
        assert (destination / "index.html").exists()
        assert (destination / "styles.css").exists()
        assert not (destination / "docs/parent.html").exists()
        child_html = (destination / "docs/child.html").read_text(encoding="utf-8")
        assert 'href="/docs/?scope=studio&doc=parent#top"' in child_html
        provenance = json.loads((destination / exporter.SNAPSHOT_PROVENANCE_FILENAME).read_text(encoding="utf-8"))
        assert provenance == {
            "schema_version": exporter.SNAPSHOT_SCHEMA_VERSION,
            "scope": "studio",
            "doc_ids": ["child", "sibling"],
            "selection_kind": "partial",
            "document_count": 2,
            "media_count": 0,
            "media_bytes": 0,
            "media": [],
            "external_dependency_count": 0,
            "external_dependencies": [],
            "default_doc_id": "child",
            "export_date": "2026-07-31",
            "generated_at": payload["generated_at"],
            "plan_revision": preview["plan_revision"],
        }


def test_snapshot_packages_only_selected_owned_media_and_records_external_dependencies() -> None:
    with tempfile.TemporaryDirectory() as repo_path, tempfile.TemporaryDirectory() as projects_path:
        repo_root = Path(repo_path)
        projects_root = Path(projects_path)
        prepare_repo(repo_root, projects_root)
        media_root = repo_root / "docs-viewer/scopes/studio/published/media"
        media_objects = {
            "img/photo one.png": b"photo",
            "svg/diagram.svg": b"<svg/>",
            "files/manual.pdf": b"manual",
            "html/widget.html": b"<p>widget</p>",
            "img/unchecked.png": b"unchecked",
        }
        for relative_path, content in media_objects.items():
            path = media_root / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        parent_payload_path = repo_root / "docs-viewer/scopes/studio/published/documents/by-id/parent.json"
        parent_payload = json.loads(parent_payload_path.read_text(encoding="utf-8"))
        parent_payload["content_html"] = (
            '<p><img src="/docs/media/studio/img/photo%20one.png?cache=1#view">'
            '<img src="/docs/media/studio/svg/diagram.svg">'
            '<a href="/docs/media/studio/files/manual.pdf">Manual</a>'
            '<iframe src="/docs/media/studio/html/widget.html"></iframe>'
            '<img src="images/external.png?cache=2"></p>'
        )
        write_json(parent_payload_path, parent_payload)
        sibling_payload_path = repo_root / "docs-viewer/scopes/studio/published/documents/by-id/sibling.json"
        sibling_payload = json.loads(sibling_payload_path.read_text(encoding="utf-8"))
        sibling_payload["content_html"] = '<img src="/docs/media/studio/img/unchecked.png">'
        write_json(sibling_payload_path, sibling_payload)

        preview = exporter.preview_static_html_export(
            repo_root,
            {"scope": "studio", "doc_ids": ["parent"]},
            export_date=FIXED_EXPORT_DATE,
        )

        assert preview["schema_version"] == "docs_static_html_snapshot_preview_v2"
        assert preview["media_count"] == 4
        assert preview["media_bytes"] == 30
        assert preview["external_dependency_count"] == 1
        with patch("urllib.request.urlopen", side_effect=AssertionError("served URL fetch attempted")):
            payload = exporter.apply_static_html_snapshot(repo_root, snapshot_apply_body(preview))
        destination = projects_root / "docs-export/studio selection - 2026-07-31"
        assert payload["media_count"] == 4
        assert payload["media_bytes"] == 30
        assert payload["external_dependency_count"] == 1
        assert payload["file_count"] == 8
        assert (destination / "media/img/photo one.png").read_bytes() == b"photo"
        assert (destination / "media/svg/diagram.svg").read_bytes() == b"<svg/>"
        assert (destination / "media/files/manual.pdf").read_bytes() == b"manual"
        assert (destination / "media/html/widget.html").read_bytes() == b"<p>widget</p>"
        assert not (destination / "media/img/unchecked.png").exists()
        document_html = (destination / "docs/parent.html").read_text(encoding="utf-8")
        assert 'src="../media/img/photo%20one.png#view"' in document_html
        assert 'src="../media/svg/diagram.svg"' in document_html
        assert 'href="../media/files/manual.pdf"' in document_html
        assert 'src="../media/html/widget.html"' in document_html
        assert 'src="images/external.png?cache=2"' in document_html
        provenance = json.loads((destination / exporter.SNAPSHOT_PROVENANCE_FILENAME).read_text(encoding="utf-8"))
        assert {
            (item["media_type"], item["identity"]): (
                item["provider"],
                item["packaged_path"],
                item["size"],
                item["sha256"],
                item["doc_ids"],
            )
            for item in provenance["media"]
        } == {
            ("files", "manual.pdf"): (
                "repository",
                "media/files/manual.pdf",
                6,
                hashlib.sha256(b"manual").hexdigest(),
                ["parent"],
            ),
            ("html", "widget.html"): (
                "repository",
                "media/html/widget.html",
                13,
                hashlib.sha256(b"<p>widget</p>").hexdigest(),
                ["parent"],
            ),
            ("img", "photo one.png"): (
                "repository",
                "media/img/photo one.png",
                5,
                hashlib.sha256(b"photo").hexdigest(),
                ["parent"],
            ),
            ("svg", "diagram.svg"): (
                "repository",
                "media/svg/diagram.svg",
                6,
                hashlib.sha256(b"<svg/>").hexdigest(),
                ["parent"],
            ),
        }
        assert provenance["external_dependencies"] == [
            {
                "reference": "images/external.png",
                "element": "img",
                "attribute": "src",
                "doc_ids": ["parent"],
            }
        ]


def test_snapshot_plan_revision_detects_body_and_media_byte_changes() -> None:
    with tempfile.TemporaryDirectory() as repo_path, tempfile.TemporaryDirectory() as projects_path:
        repo_root = Path(repo_path)
        prepare_repo(repo_root, Path(projects_path))
        payload_path = repo_root / "docs-viewer/scopes/studio/published/documents/by-id/parent.json"
        first = exporter.preview_static_html_export(
            repo_root,
            {"scope": "studio", "doc_ids": ["parent"]},
            export_date=FIXED_EXPORT_DATE,
        )
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
        payload["content_html"] = "<p>Changed body without a title change.</p>"
        write_json(payload_path, payload)
        body_changed = exporter.preview_static_html_export(
            repo_root,
            {"scope": "studio", "doc_ids": ["parent"]},
            export_date=FIXED_EXPORT_DATE,
        )
        assert body_changed["plan_revision"] != first["plan_revision"]

        media_path = repo_root / "docs-viewer/scopes/studio/published/media/img/photo.png"
        media_path.parent.mkdir(parents=True)
        media_path.write_bytes(b"first")
        payload["content_html"] = '<img src="/docs/media/studio/img/photo.png">'
        write_json(payload_path, payload)
        media_first = exporter.preview_static_html_export(
            repo_root,
            {"scope": "studio", "doc_ids": ["parent"]},
            export_date=FIXED_EXPORT_DATE,
        )
        media_path.write_bytes(b"second")
        media_changed = exporter.preview_static_html_export(
            repo_root,
            {"scope": "studio", "doc_ids": ["parent"]},
            export_date=FIXED_EXPORT_DATE,
        )
        assert media_changed["plan_revision"] != media_first["plan_revision"]
        with pytest.raises(exporter.StaticHtmlSnapshotApplyConflict, match="plan changed"):
            exporter.apply_static_html_snapshot(repo_root, snapshot_apply_body(media_first))


def test_output_path_validation_requires_projects_export_root() -> None:
    with tempfile.TemporaryDirectory() as projects_path:
        os.environ["DOTLINEFORM_PROJECTS_BASE_DIR"] = projects_path
        try:
            exporter.validate_destination_path(Path(projects_path).resolve() / "other/studio")
        except ValueError as exc:
            assert "docs-export" in str(exc)
        else:
            raise AssertionError("destination outside docs-export must be rejected")


def test_snapshot_apply_reads_public_and_external_local_generated_scopes() -> None:
    with tempfile.TemporaryDirectory() as repo_path, tempfile.TemporaryDirectory() as projects_path:
        repo_root = Path(repo_path)
        projects_root = Path(projects_path)
        prepare_repo(repo_root, projects_root)
        external_payload_path = projects_root / "docs-viewer/scopes/external/published/documents/by-id/external.json"
        external_payload = json.loads(external_payload_path.read_text(encoding="utf-8"))
        external_payload["content_html"] = '<img src="/docs/media/external/svg/diagram.svg">'
        write_json(external_payload_path, external_payload)
        external_svg = projects_root / "docs-viewer/scopes/external/published/media/svg/diagram.svg"
        external_svg.parent.mkdir(parents=True)
        external_svg.write_bytes(b"<svg>external</svg>")

        for scope in ("library", "external"):
            preview = exporter.preview_static_html_export(
                repo_root,
                {"scope": scope, "doc_ids": [scope]},
                export_date=FIXED_EXPORT_DATE,
            )
            payload = exporter.apply_static_html_snapshot(repo_root, snapshot_apply_body(preview))

            assert payload["scope"] == scope
            assert payload["selection_kind"] == "complete"
            assert (projects_root / f"docs-export/{scope} - 2026-07-31/docs/{scope}.html").is_file()
            if scope == "external":
                destination = projects_root / "docs-export/external - 2026-07-31"
                assert (destination / "media/svg/diagram.svg").read_bytes() == b"<svg>external</svg>"
                assert 'src="../media/svg/diagram.svg"' in (
                    destination / "docs/external.html"
                ).read_text(encoding="utf-8")


def test_snapshot_apply_packages_r2_fixture_without_fetching_served_url() -> None:
    with tempfile.TemporaryDirectory() as repo_path, tempfile.TemporaryDirectory() as projects_path:
        repo_root = Path(repo_path)
        projects_root = Path(projects_path)
        prepare_repo(repo_root, projects_root)
        library_payload_path = repo_root / "docs-viewer/scopes/library/published/documents/by-id/library.json"
        library_payload = json.loads(library_payload_path.read_text(encoding="utf-8"))
        library_payload["content_html"] = (
            '<img src="https://media.example.test/docs/library/img/photo.webp?cache=1">'
        )
        write_json(library_payload_path, library_payload)

        class ReadOnlyR2Fixture:
            def get_object(self, key: str) -> bytes:
                if key != "docs/library/img/photo.webp":
                    raise FileNotFoundError(key)
                return b"r2-photo"

        with (
            patch.object(
                media_export,
                "authenticated_remote_client_for_locations",
                return_value=ReadOnlyR2Fixture(),
            ),
            patch("urllib.request.urlopen", side_effect=AssertionError("served URL fetch attempted")),
        ):
            preview = exporter.preview_static_html_export(
                repo_root,
                {"scope": "library", "doc_ids": ["library"]},
                export_date=FIXED_EXPORT_DATE,
            )
            payload = exporter.apply_static_html_snapshot(repo_root, snapshot_apply_body(preview))

        destination = projects_root / "docs-export/library - 2026-07-31"
        assert payload["media_count"] == 1
        assert (destination / "media/img/photo.webp").read_bytes() == b"r2-photo"
        assert 'src="../media/img/photo.webp"' in (
            destination / "docs/library.html"
        ).read_text(encoding="utf-8")


def test_snapshot_apply_replaces_only_explicitly_confirmed_existing_target() -> None:
    with tempfile.TemporaryDirectory() as repo_path, tempfile.TemporaryDirectory() as projects_path:
        repo_root = Path(repo_path)
        projects_root = Path(projects_path)
        prepare_repo(repo_root, projects_root)
        first_preview = exporter.preview_static_html_export(
            repo_root,
            {"scope": "studio", "doc_ids": ["parent"]},
            export_date=FIXED_EXPORT_DATE,
        )
        exporter.apply_static_html_snapshot(repo_root, snapshot_apply_body(first_preview))
        destination = projects_root / "docs-export/studio selection - 2026-07-31"
        stale_path = destination / "stale.txt"
        stale_path.write_text("stale", encoding="utf-8")
        replacement_preview = exporter.preview_static_html_export(
            repo_root,
            {"scope": "studio", "doc_ids": ["parent"]},
            export_date=FIXED_EXPORT_DATE,
        )

        try:
            exporter.apply_static_html_snapshot(repo_root, snapshot_apply_body(replacement_preview))
        except ValueError as exc:
            assert "replace_existing must be true" in str(exc)
        else:
            raise AssertionError("replacement without explicit confirmation should fail")
        assert stale_path.read_text(encoding="utf-8") == "stale"

        payload = exporter.apply_static_html_snapshot(
            repo_root,
            snapshot_apply_body(replacement_preview, replace_existing=True),
        )

        assert payload["replaced"] is True
        assert not stale_path.exists()
        assert (destination / "docs/parent.html").is_file()
        assert not list(destination.parent.glob(".*.backup"))
        assert not list(destination.parent.glob(".*.staging"))


def test_snapshot_apply_can_replace_an_explicitly_confirmed_unrecognized_directory() -> None:
    with tempfile.TemporaryDirectory() as repo_path, tempfile.TemporaryDirectory() as projects_path:
        repo_root = Path(repo_path)
        projects_root = Path(projects_path)
        prepare_repo(repo_root, projects_root)
        destination = projects_root / "docs-export/studio selection - 2026-07-31"
        destination.mkdir(parents=True)
        (destination / "unrelated.txt").write_text("existing", encoding="utf-8")
        preview = exporter.preview_static_html_export(
            repo_root,
            {"scope": "studio", "doc_ids": ["parent"]},
            export_date=FIXED_EXPORT_DATE,
        )
        assert preview["target_state"] == "unrecognized"

        payload = exporter.apply_static_html_snapshot(
            repo_root,
            snapshot_apply_body(preview, replace_existing=True),
        )

        assert payload["replaced"] is True
        assert not (destination / "unrelated.txt").exists()
        assert (destination / exporter.SNAPSHOT_PROVENANCE_FILENAME).is_file()


def test_snapshot_apply_rejects_missing_confirmation_and_non_directory_target() -> None:
    with tempfile.TemporaryDirectory() as repo_path, tempfile.TemporaryDirectory() as projects_path:
        repo_root = Path(repo_path)
        projects_root = Path(projects_path)
        prepare_repo(repo_root, projects_root)
        destination = projects_root / "docs-export/studio selection - 2026-07-31"
        destination.parent.mkdir(parents=True)
        destination.write_text("preserve collision", encoding="utf-8")
        preview = exporter.preview_static_html_export(
            repo_root,
            {"scope": "studio", "doc_ids": ["parent"]},
            export_date=FIXED_EXPORT_DATE,
        )
        assert preview["target_state"] == "non_directory"
        unconfirmed = snapshot_apply_body(preview, replace_existing=True)
        unconfirmed["confirm"] = False

        try:
            exporter.apply_static_html_snapshot(repo_root, unconfirmed)
        except ValueError as exc:
            assert "confirm must be true" in str(exc)
        else:
            raise AssertionError("unconfirmed apply should fail")

        try:
            exporter.apply_static_html_snapshot(
                repo_root,
                snapshot_apply_body(preview, replace_existing=True),
            )
        except exporter.StaticHtmlSnapshotApplyConflict as exc:
            assert "not a replaceable directory" in str(exc)
        else:
            raise AssertionError("non-directory target should fail")
        assert destination.read_text(encoding="utf-8") == "preserve collision"


def test_snapshot_apply_rejects_stale_plan_and_target_while_preserving_existing_artifacts() -> None:
    with tempfile.TemporaryDirectory() as repo_path, tempfile.TemporaryDirectory() as projects_path:
        repo_root = Path(repo_path)
        projects_root = Path(projects_path)
        prepare_repo(repo_root, projects_root)
        stale_plan_preview = exporter.preview_static_html_export(
            repo_root,
            {"scope": "studio", "doc_ids": ["parent"]},
            export_date=FIXED_EXPORT_DATE,
        )
        exporter.apply_static_html_snapshot(repo_root, snapshot_apply_body(stale_plan_preview))
        stale_plan_preview = exporter.preview_static_html_export(
            repo_root,
            {"scope": "studio", "doc_ids": ["parent"]},
            export_date=FIXED_EXPORT_DATE,
        )
        parent_payload_path = repo_root / "docs-viewer/scopes/studio/published/documents/by-id/parent.json"
        parent_payload = json.loads(parent_payload_path.read_text(encoding="utf-8"))
        parent_payload["title"] = "Changed title"
        write_json(parent_payload_path, parent_payload)

        try:
            exporter.apply_static_html_snapshot(
                repo_root,
                snapshot_apply_body(stale_plan_preview, replace_existing=True),
            )
        except exporter.StaticHtmlSnapshotApplyConflict as exc:
            assert "plan changed" in str(exc)
            assert exc.payload["requires_preview"] is True
        else:
            raise AssertionError("stale plan should fail")
        original_destination = projects_root / "docs-export/studio selection - 2026-07-31"
        assert (original_destination / exporter.SNAPSHOT_PROVENANCE_FILENAME).is_file()

        current_preview = exporter.preview_static_html_export(
            repo_root,
            {"scope": "studio", "doc_ids": ["parent"]},
            export_date=FIXED_EXPORT_DATE,
        )
        exporter.apply_static_html_snapshot(
            repo_root,
            snapshot_apply_body(current_preview, replace_existing=True),
        )
        replacement_preview = exporter.preview_static_html_export(
            repo_root,
            {"scope": "studio", "doc_ids": ["parent"]},
            export_date=FIXED_EXPORT_DATE,
        )
        destination = projects_root / "docs-export/studio selection - 2026-07-31"
        changed_path = destination / "changed-after-preview.txt"
        changed_path.write_text("preserve me", encoding="utf-8")

        try:
            exporter.apply_static_html_snapshot(
                repo_root,
                snapshot_apply_body(replacement_preview, replace_existing=True),
            )
        except exporter.StaticHtmlSnapshotApplyConflict as exc:
            assert "destination changed" in str(exc)
        else:
            raise AssertionError("stale target should fail")
        assert changed_path.read_text(encoding="utf-8") == "preserve me"


def test_snapshot_render_staging_and_validation_failures_preserve_existing_target() -> None:
    with tempfile.TemporaryDirectory() as repo_path, tempfile.TemporaryDirectory() as projects_path:
        repo_root = Path(repo_path)
        projects_root = Path(projects_path)
        prepare_repo(repo_root, projects_root)
        first_preview = exporter.preview_static_html_export(
            repo_root,
            {"scope": "studio", "doc_ids": ["parent"]},
            export_date=FIXED_EXPORT_DATE,
        )
        exporter.apply_static_html_snapshot(repo_root, snapshot_apply_body(first_preview))
        destination = projects_root / "docs-export/studio selection - 2026-07-31"
        marker = destination / "preserved.txt"
        marker.write_text("original", encoding="utf-8")
        replacement_preview = exporter.preview_static_html_export(
            repo_root,
            {"scope": "studio", "doc_ids": ["parent"]},
            export_date=FIXED_EXPORT_DATE,
        )
        real_writer = exporter.write_snapshot_staging_files

        with patch.object(exporter, "compute_snapshot_files", side_effect=RuntimeError("simulated render failure")):
            try:
                exporter.apply_static_html_snapshot(
                    repo_root,
                    snapshot_apply_body(replacement_preview, replace_existing=True),
                )
            except RuntimeError as exc:
                assert str(exc) == "simulated render failure"
            else:
                raise AssertionError("simulated render failure should escape")
        assert marker.read_text(encoding="utf-8") == "original"

        def fail_after_write(staging_root: Path, files: dict[Path, bytes]) -> None:
            real_writer(staging_root, files)
            raise RuntimeError("simulated staging failure")

        with patch.object(exporter, "write_snapshot_staging_files", side_effect=fail_after_write):
            try:
                exporter.apply_static_html_snapshot(
                    repo_root,
                    snapshot_apply_body(replacement_preview, replace_existing=True),
                )
            except RuntimeError as exc:
                assert str(exc) == "simulated staging failure"
            else:
                raise AssertionError("simulated staging failure should escape")
        assert marker.read_text(encoding="utf-8") == "original"

        def corrupt_after_write(staging_root: Path, files: dict[Path, bytes]) -> None:
            real_writer(staging_root, files)
            (staging_root / "index.html").write_text("corrupt", encoding="utf-8")

        with patch.object(exporter, "write_snapshot_staging_files", side_effect=corrupt_after_write):
            try:
                exporter.apply_static_html_snapshot(
                    repo_root,
                    snapshot_apply_body(replacement_preview, replace_existing=True),
                )
            except ValueError as exc:
                assert "content validation failed" in str(exc)
            else:
                raise AssertionError("simulated validation failure should escape")

        assert marker.read_text(encoding="utf-8") == "original"
        assert not list(destination.parent.glob(".*.staging"))


def test_snapshot_final_switch_failure_restores_existing_target() -> None:
    with tempfile.TemporaryDirectory() as repo_path, tempfile.TemporaryDirectory() as projects_path:
        repo_root = Path(repo_path)
        projects_root = Path(projects_path)
        prepare_repo(repo_root, projects_root)
        first_preview = exporter.preview_static_html_export(
            repo_root,
            {"scope": "studio", "doc_ids": ["parent"]},
            export_date=FIXED_EXPORT_DATE,
        )
        exporter.apply_static_html_snapshot(repo_root, snapshot_apply_body(first_preview))
        destination = projects_root / "docs-export/studio selection - 2026-07-31"
        marker = destination / "preserved.txt"
        marker.write_text("original", encoding="utf-8")
        replacement_preview = exporter.preview_static_html_export(
            repo_root,
            {"scope": "studio", "doc_ids": ["parent"]},
            export_date=FIXED_EXPORT_DATE,
        )
        path_type = type(destination)
        real_rename = path_type.rename

        def fail_staging_install(source: Path, target: Path) -> Path:
            if source.name.endswith(".staging"):
                raise OSError("simulated final switch failure")
            return real_rename(source, target)

        with patch.object(path_type, "rename", new=fail_staging_install):
            try:
                exporter.apply_static_html_snapshot(
                    repo_root,
                    snapshot_apply_body(replacement_preview, replace_existing=True),
                )
            except OSError as exc:
                assert str(exc) == "simulated final switch failure"
            else:
                raise AssertionError("simulated final switch failure should escape")

        assert marker.read_text(encoding="utf-8") == "original"
        assert not list(destination.parent.glob(".*.backup"))
        assert not list(destination.parent.glob(".*.staging"))


def test_management_apply_route_returns_snapshot_response_and_stale_conflict() -> None:
    with tempfile.TemporaryDirectory() as repo_path, tempfile.TemporaryDirectory() as projects_path:
        repo_root = Path(repo_path)
        projects_root = Path(projects_path)
        prepare_repo(repo_root, projects_root)
        _preview_status, preview = docs_management_service.docs_management_post_response(
            repo_root,
            routes.STATIC_HTML_EXPORT_PREVIEW_PATH,
            {"scope": "studio", "doc_ids": ["parent"]},
        )

        status, payload = docs_management_service.docs_management_post_response(
            repo_root,
            routes.STATIC_HTML_EXPORT_APPLY_PATH,
            snapshot_apply_body(preview),
        )

        assert status.value == 200
        assert payload["ok"] is True
        assert payload["operation"] == "apply"
        assert payload["destination_label"].startswith("/docs-export/studio selection - ")
        assert payload["summary_text"].startswith("Exported 1 document to ")
        assert "destination" not in payload

        _replacement_status, replacement_preview = docs_management_service.docs_management_post_response(
            repo_root,
            routes.STATIC_HTML_EXPORT_PREVIEW_PATH,
            {"scope": "studio", "doc_ids": ["parent"]},
        )
        destination = projects_root / replacement_preview["destination_label"].strip("/")
        (destination / "changed.txt").write_text("changed", encoding="utf-8")
        conflict_status, conflict = docs_management_service.docs_management_post_response(
            repo_root,
            routes.STATIC_HTML_EXPORT_APPLY_PATH,
            snapshot_apply_body(replacement_preview, replace_existing=True),
        )

        assert conflict_status.value == 409
        assert conflict["ok"] is False
        assert conflict["requires_preview"] is True
        assert "destination" not in conflict


def test_management_preview_route_returns_write_free_browser_safe_plan() -> None:
    with tempfile.TemporaryDirectory() as repo_path, tempfile.TemporaryDirectory() as projects_path:
        repo_root = Path(repo_path)
        projects_root = Path(projects_path)
        prepare_repo(repo_root, projects_root)

        status, payload = docs_management_service.docs_management_post_response(
            repo_root,
            routes.STATIC_HTML_EXPORT_PREVIEW_PATH,
            {"scope": "studio", "doc_ids": ["sibling", "child"]},
        )

        assert status.value == 200
        assert payload["ok"] is True
        assert payload["schema_version"] == exporter.SNAPSHOT_PREVIEW_SCHEMA_VERSION
        assert payload["operation"] == "preview"
        assert payload["dry_run"] is True
        assert payload["doc_ids"] == ["child", "sibling"]
        assert payload["media_count"] == 0
        assert payload["media_bytes"] == 0
        assert payload["external_dependency_count"] == 0
        assert payload["selection_kind"] == "partial"
        assert payload["destination_label"].startswith("/docs-export/studio selection - ")
        assert "destination" not in payload
        assert not (projects_root / "docs-export").exists()


def test_legacy_latest_folder_and_delete_service_are_retired() -> None:
    assert not hasattr(exporter, "build_static_html_export")
    assert not hasattr(exporter, "delete_static_html_export")
    assert not hasattr(routes, "STATIC_HTML_EXPORT_DELETE_PATH")
    assert "/docs/export/static-html/delete" not in routes.POST_PATHS
