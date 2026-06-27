#!/usr/bin/env python3
"""Focused checks for the Docs Viewer import parser and preview renderer."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_IMPORT_PATH = REPO_ROOT / "docs-viewer" / "services" / "docs_import.py"
DOCS_SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
if str(DOCS_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(DOCS_SERVICES_DIR))


def load_docs_import_module():
    spec = importlib.util.spec_from_file_location("docs_import", DOCS_IMPORT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load docs_import.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


docs_import = load_docs_import_module()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_repo() -> tempfile.TemporaryDirectory:
    temp_dir = tempfile.TemporaryDirectory()
    root = Path(temp_dir.name)
    (root / "site-tools/config").mkdir(parents=True, exist_ok=True); (root / "site-tools/config/site-tools.json").write_text("{\"schema_version\":\"site_tools_config_v1\"}\n", encoding="utf-8")
    (root / "var/analytics/data-sharing/library/import-staging").mkdir(parents=True, exist_ok=True)
    write_scope_config(root)
    write_current_source_docs(
        root,
        [
            {"doc_id": "library", "title": "Library", "parent_id": "", "viewable": True},
            {"doc_id": "alpha", "title": "Alpha", "parent_id": "library", "viewable": True},
            {"doc_id": "beta", "title": "Beta", "parent_id": "library", "viewable": True},
            {
                "doc_id": "missing-title",
                "title": "Missing Title",
                "parent_id": "library",
                "viewable": True,
            },
        ],
    )
    return temp_dir


def write_current_source_docs(root: Path, docs: list[dict], *, scope: str = "library") -> None:
    source_root = root / "docs-viewer/source" / scope
    source_root.mkdir(parents=True, exist_ok=True)
    for existing in source_root.glob("*.md"):
        existing.unlink()
    for doc in docs:
        doc_id = str(doc.get("doc_id") or "").strip()
        if not doc_id:
            continue
        lines = [
            "---",
            f"doc_id: {doc_id}",
            f"title: {doc.get('title') or doc_id}",
            "added_date: 2026-05-03",
            "last_updated: 2026-05-03",
        ]
        if doc.get("parent_id"):
            lines.append(f"parent_id: {doc.get('parent_id')}")
        if doc.get("viewable") is False:
            lines.append("viewable: false")
        lines.extend(["---", "", f"# {doc.get('title') or doc_id}", "", "Body text."])
        (source_root / f"{doc_id}.md").write_text("\n".join(lines), encoding="utf-8")


def scope_config(scope: str) -> dict:
    public = scope == "library"
    return {
        "scope_id": scope,
        "scope_type": "public" if public else "local",
        "source": f"docs-viewer/source/{scope}",
        "media_path_prefix": f"docs/{scope}",
        "output": f"docs-viewer/generated/docs/{scope}",
        "search_output": f"docs-viewer/generated/search/{scope}/index.json",
        "publish_output": f"site/assets/data/docs/scopes/{scope}" if public else f"docs-viewer/generated/docs/{scope}",
        "publish_search_output": f"site/assets/data/search/{scope}/index.json" if public else f"docs-viewer/generated/search/{scope}/index.json",
        "viewer_base_url": "/library/" if public else "/docs/",
        "include_scope_param": not public,
        "default_doc_id": scope,
        "allow_unresolved_parent_ids": public,
    }


def write_scope_config(root: Path, scopes: list[str] | None = None) -> None:
    scope_ids = scopes or ["library"]
    path = root / "docs-viewer/config/scopes/docs_scopes.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "docs_scopes_v1",
                "scopes": [scope_config(scope) for scope in scope_ids],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def write_staged(root: Path, filename: str, text: str, *, scope: str = "library") -> None:
    path = root / "var/analytics/data-sharing" / scope / "import-staging" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def parse(root: Path, filename: str, *, scope: str = "library"):
    return docs_import.parse_staged_import(repo_root=root, scope=scope, staged_file=filename)


def render(root: Path, report: dict, *, write: bool = True, generated_at: str = "2026-05-03T20:40:00Z"):
    return docs_import.render_markdown_previews(
        repo_root=root,
        scope="library",
        report=report,
        write=write,
        generated_at=generated_at,
    )


def test_jsonl_summary_export_rows_are_detected_and_normalized() -> None:
    with make_repo() as temp:
        root = Path(temp)
        rows = [
            {
                "doc_id": "alpha",
                "title": "Alpha",
                "parent_id": "library",
                "current_summary": "Existing summary.",
                "review_note": "Keep this unknown field.",
            },
            {
                "doc_id": "beta",
                "title": "Beta",
                "parent_id": "library",
                "current_summary": "",
            },
        ]
        write_staged(root, "summaries.jsonl", "".join(json.dumps(row) + "\n" for row in rows))
        write_staged(
            root,
            "summaries.meta.json",
            json.dumps(
                {
                    "export_id": "document-summaries",
                    "scope": "library",
                    "generated_at": "2026-05-03T20:00:00Z",
                }
            ),
        )
        report = parse(root, "summaries.jsonl")

    assert report["ok"] is True
    assert report["input_format"] == "jsonl"
    assert report["source_metadata_file"].endswith("summaries.meta.json")
    assert report["detected_import_type"] == "document_summaries"
    assert report["source_export_id"] == "document-summaries"
    assert report["source_scope"] == "library"
    assert report["generated_at"] == "2026-05-03T20:00:00Z"
    assert report["counts"] == {"records": 2, "parsed_records": 2, "malformed_records": 0, "warnings": 0, "errors": 0}
    assert report["records"][0]["metadata"]["current_summary"] == "Existing summary."
    assert report["records"][0]["unknown_metadata"] == {"review_note": "Keep this unknown field."}


def test_staged_import_listing_skips_package_sidecars() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged(root, "summaries.jsonl", '{"doc_id": "alpha", "title": "Alpha"}\n')
        write_staged(root, "summaries.meta.json", '{"export_id": "document-summaries"}\n')
        write_staged(root, "summaries.context.json", '{"task": "suggest_document_summaries"}\n')
        files = docs_import.list_staged_import_files(root, "library")

    assert [item["filename"] for item in files] == ["summaries.jsonl"]


def test_configured_studio_scope_json_envelope_can_be_previewed() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_scope_config(root, ["library", "studio"])
        write_current_source_docs(
            root,
            [
                {"doc_id": "admin", "title": "Admin", "parent_id": "", "viewable": True},
                {"doc_id": "admin-checks", "title": "Checks", "parent_id": "admin", "viewable": True},
            ],
            scope="studio",
        )
        write_text(
            root / "var/analytics/data-sharing/import-staging/20260627-162139-documents-document-summaries.json",
            json.dumps(
                {
                    "schema_version": "data_sharing_returned_package_v1",
                    "export_id": "ds_20260627T152139Z",
                    "records": [
                        {
                            "doc_id": "admin-checks",
                            "title": "Checks",
                            "parent_id": "admin",
                            "current_summary": "",
                        }
                    ],
                }
            ),
        )
        report = docs_import.parse_staged_import(
            repo_root=root,
            scope="studio",
            staged_file="20260627-162139-documents-document-summaries.json",
            staging_root=Path("var/analytics/data-sharing/import-staging"),
        )
        rendered = docs_import.render_markdown_previews(
            repo_root=root,
            scope="studio",
            report=report,
            write=True,
            generated_at="2026-06-27T16:21:39Z",
            preview_root=Path("var/analytics/data-sharing/import-preview"),
        )
        files = docs_import.list_staged_import_files(
            root,
            "studio",
            staging_root=Path("var/analytics/data-sharing/import-staging"),
        )

    assert report["ok"] is True
    assert report["scope"] == "studio"
    assert report["current_library"]["source_root"] == "docs-viewer/source/studio"
    assert report["records"][0]["current_library"]["exists"] is True
    preview_paths = [item["path"] for item in rendered["preview_files"]]
    assert (
        "var/analytics/data-sharing/import-preview/"
        "20260627-162139-admin-checks.md"
    ) in preview_paths
    assert [item["filename"] for item in files] == ["20260627-162139-documents-document-summaries.json"]


def test_json_envelope_relationship_export_preserves_tree_metadata() -> None:
    with make_repo() as temp:
        root = Path(temp)
        payload = {
            "review_batch": "tree-a",
            "records": [
                {
                    "doc_id": "library",
                    "title": "Library",
                    "parent_id": "",
                    "child_ids": ["alpha"],
                    "child_titles": ["Alpha"],
                },
                {
                    "doc_id": "alpha",
                    "title": "Alpha",
                    "parent_id": "library",
                    "ancestor_ids": ["library"],
                    "ancestor_titles": ["Library"],
                },
            ],
        }
        write_staged(root, "relationships.json", json.dumps(payload))
        write_staged(
            root,
            "relationships.meta.json",
            json.dumps(
                {
                    "export_id": "parent-child-relationships",
                    "scope": "library",
                    "generated_at": "2026-05-03T20:10:00Z",
                }
            ),
        )
        report = parse(root, "relationships.json")

    assert report["ok"] is True
    assert report["detected_import_type"] == "parent_child_relationships"
    assert report["source_metadata_file"].endswith("relationships.meta.json")
    assert report["source_export_id"] == "parent-child-relationships"
    assert report["unknown_file_metadata"] == {"review_batch": "tree-a"}
    assert report["records"][0]["relationships"]["child_ids"] == ["alpha"]
    assert report["records"][1]["relationships"]["ancestor_ids"] == ["library"]


def test_json_records_envelope_is_parsed_without_legacy_documents_key() -> None:
    with make_repo() as temp:
        root = Path(temp)
        payload = {
            "schema_version": "data_sharing_returned_package_v1",
            "export_id": "ds_20260627T120000Z",
            "records": [
                {
                    "doc_id": "alpha",
                    "title": "Alpha",
                    "parent_id": "library",
                    "current_summary": "Updated summary.",
                }
            ],
        }
        write_staged(root, "records-envelope.json", json.dumps(payload))
        report = parse(root, "records-envelope.json")

    assert report["ok"] is True
    assert report["detected_import_type"] == "document_summaries"
    assert report["source_export_id"] == "ds_20260627T120000Z"
    assert report["source_metadata"]["schema_version"] == "data_sharing_returned_package_v1"
    assert report["unknown_file_metadata"] == {}
    assert report["counts"] == {"records": 1, "parsed_records": 1, "malformed_records": 0, "warnings": 0, "errors": 0}
    assert report["records"][0]["metadata"]["current_summary"] == "Updated summary."


def test_jsonl_full_content_is_detected_from_source_text_without_metadata() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged(
            root,
            "content.jsonl",
            json.dumps(
                {
                    "doc_id": "alpha",
                    "title": "Alpha",
                    "parent_id": "library",
                    "source_text": "Plain text body.\n\nSecond paragraph.",
                }
            )
            + "\n",
        )
        report = parse(root, "content.jsonl")

    assert report["ok"] is True
    assert report["detected_import_type"] == "full_document_content"
    assert report["source_export_id"] == ""
    assert report["records"][0]["metadata"]["source_text"] == "Plain text body.\n\nSecond paragraph."


def test_jsonl_data_sharing_header_row_is_skipped() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged(
            root,
            "content-with-header.jsonl",
            "\n".join(
                [
                    json.dumps(
                        {
                            "record_type": "data_sharing_header",
                            "schema_version": "data_sharing_returned_package_v1",
                            "export_id": "ds_20260627T120000Z",
                        }
                    ),
                    json.dumps(
                        {
                            "doc_id": "alpha",
                            "title": "Alpha",
                            "parent_id": "library",
                            "source_text": "Plain text body.",
                        }
                    ),
                ]
            )
            + "\n",
        )
        report = parse(root, "content-with-header.jsonl")

    assert report["ok"] is True
    assert report["counts"] == {"records": 1, "parsed_records": 1, "malformed_records": 0, "warnings": 0, "errors": 0}
    assert report["records"][0]["doc_id"] == "alpha"
    assert report["records"][0]["line"] == 2


def test_minimal_hand_authored_json_array_reports_malformed_records_but_keeps_parsing() -> None:
    with make_repo() as temp:
        root = Path(temp)
        payload = [
            {"doc_id": "alpha", "title": "Alpha", "extra": {"review": True}},
            {"doc_id": "", "title": "Missing Id"},
            {"doc_id": "missing-title"},
            {"doc_id": "alpha", "title": "Duplicate Alpha"},
        ]
        write_staged(root, "minimal.json", json.dumps(payload))
        report = parse(root, "minimal.json")

    assert report["ok"] is True
    assert report["detected_import_type"] == "minimal_document_records"
    assert report["counts"] == {"records": 4, "parsed_records": 4, "malformed_records": 2, "warnings": 3, "errors": 0}
    assert report["records"][0]["unknown_metadata"] == {"extra": {"review": True}}
    assert [item["code"] for item in report["issues"]] == ["missing_doc_id", "missing_title", "duplicate_doc_id"]


def test_current_library_lookup_adds_record_level_warnings() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_current_source_docs(
            root,
            [
                {"doc_id": "library", "title": "Library", "parent_id": "", "viewable": True},
                {
                    "doc_id": "non-viewable-parent",
                    "title": "Non-viewable Parent",
                    "parent_id": "library",
                    "viewable": False,
                },
                {
                    "doc_id": "source-child",
                    "title": "Source Child",
                    "parent_id": "library",
                    "viewable": True,
                },
            ],
        )
        payload = [
            {"doc_id": "unknown-doc", "title": "Unknown Doc", "parent_id": "missing-parent"},
            {"doc_id": "non-viewable-parent", "title": "Non-viewable Parent", "parent_id": "library"},
            {"doc_id": "source-child", "title": "Source Child", "parent_id": "non-viewable-parent"},
        ]
        write_staged(root, "lookup.json", json.dumps(payload))
        report = parse(root, "lookup.json")

    assert report["ok"] is True
    assert report["current_library"] == {
        "source_loaded": True,
        "source_root": "docs-viewer/source/library",
        "doc_count": 3,
        "renderable_count": 3,
    }
    assert report["counts"] == {"records": 3, "parsed_records": 3, "malformed_records": 0, "warnings": 2, "errors": 0}
    assert [item["code"] for item in report["issues"]] == [
        "unknown_doc_id",
        "missing_parent_id",
    ]
    assert report["records"][0]["current_library"]["exists"] is False
    assert report["records"][2]["current_library"]["source_renderable"] is True


def test_current_lookup_uses_source_metadata() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged(root, "lookup.json", json.dumps([{"doc_id": "alpha", "title": "Alpha", "parent_id": "library"}]))
        report = parse(root, "lookup.json")

    assert report["ok"] is True
    assert report["current_library"]["source_loaded"] is True
    assert report["current_library"]["doc_count"] == 4
    assert report["records"][0]["current_library"]["exists"] is True
    assert report["records"][0]["current_library"]["source_renderable"] is True
    assert report["issues"] == []


def test_missing_source_metadata_adds_current_context_warning() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_text(
            root / "docs-viewer/config/scopes/docs_scopes.json",
            json.dumps(
                {
                    "schema_version": "docs_scopes_v1",
                    "scopes": [
                        {
                            "scope_id": "library",
                            "scope_type": "public",
                            "source": "docs-viewer/source/missing-library",
                            "media_path_prefix": "docs/library",
                            "output": "docs-viewer/generated/docs/library",
                            "search_output": "docs-viewer/generated/search/library/index.json",
                            "publish_output": "site/assets/data/docs/scopes/library",
                            "publish_search_output": "site/assets/data/search/library/index.json",
                            "viewer_base_url": "/library/",
                            "include_scope_param": False,
                            "default_doc_id": "library",
                            "allow_unresolved_parent_ids": True,
                        }
                    ],
                }
            )
            + "\n",
        )
        write_staged(root, "lookup.json", json.dumps([{"doc_id": "alpha", "title": "Alpha"}]))
        report = parse(root, "lookup.json")

    assert report["ok"] is True
    assert report["current_library"]["source_loaded"] is False
    assert report["counts"]["warnings"] == 1
    assert report["issues"][0]["code"] == "current_source_unreadable"
    assert "missing source root for scope library" in report["issues"][0]["message"]


def test_summary_preview_writes_one_file_per_document_with_fallback_names() -> None:
    with make_repo() as temp:
        root = Path(temp)
        payload = [
            {
                "doc_id": "alpha",
                "title": "Alpha",
                "parent_id": "library",
                "summary": "New alpha summary.",
                "review_note": "Keep this staged-only note.",
            },
            {"doc_id": "alpha", "title": "Alpha Duplicate", "parent_id": "library", "summary": "Duplicate summary."},
            {"doc_id": "", "title": "Missing Id", "parent_id": "library", "summary": "Missing id summary."},
        ]
        write_staged(root, "summaries.json", json.dumps(payload))
        report = render(root, parse(root, "summaries.json"))
        first_preview = (root / "var/analytics/data-sharing/library/import-preview/20260503-204000-alpha.md").read_text(encoding="utf-8")
        missing_preview = (root / "var/analytics/data-sharing/library/import-preview/20260503-204000-record-3.md").read_text(encoding="utf-8")

    assert report["preview_written"] is True
    assert [item["path"] for item in report["preview_files"]] == [
        "var/analytics/data-sharing/library/import-preview/20260503-204000-alpha.md",
        "var/analytics/data-sharing/library/import-preview/20260503-204000-alpha-record-2.md",
        "var/analytics/data-sharing/library/import-preview/20260503-204000-record-3.md",
    ]
    assert "matched_config_fields" in first_preview
    assert "staged_only_fields" in first_preview
    assert 'doc_id: "alpha"' in first_preview
    assert 'import_type: "document_summaries"' in first_preview
    assert 'review_note: "Keep this staged-only note."' in first_preview
    assert "## Proposed Summary\n\nNew alpha summary." in first_preview
    assert 'doc_id: ""' in missing_preview
    assert "`missing_doc_id`: record is missing doc_id" in missing_preview


def test_full_content_preview_preserves_headings_and_source_text() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged(
            root,
            "content-20260102-030405.jsonl",
            json.dumps(
                {
                    "doc_id": "alpha",
                    "title": "Alpha",
                    "parent_id": "library",
                    "headings": ["One", "Two"],
                    "source_text": "# One\n\n- A point\n\n> A quote",
                }
            )
            + "\n",
        )
        report = render(root, parse(root, "content-20260102-030405.jsonl"))
        preview = (root / "var/analytics/data-sharing/library/import-preview/20260102-030405-alpha.md").read_text(encoding="utf-8")

    assert report["preview_files"] == [
        {
            "path": "var/analytics/data-sharing/library/import-preview/20260102-030405-alpha.md",
            "record_index": 0,
            "doc_id": "alpha",
            "kind": "document",
        }
    ]
    assert "## Imported Headings\n\n- One\n- Two" in preview
    assert "## Imported Source Text\n\n# One\n\n- A point\n\n> A quote" in preview


def test_preview_renderer_can_dry_run_without_writing_files() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged(root, "summaries.json", json.dumps([{"doc_id": "alpha", "title": "Alpha"}]))
        report = render(root, parse(root, "summaries.json"), write=False)
        preview_exists = (root / "var/analytics/data-sharing/library/import-preview/20260503-204000-alpha.md").exists()

    assert report["preview_written"] is False
    assert report["preview_files"][0]["path"] == "var/analytics/data-sharing/library/import-preview/20260503-204000-alpha.md"
    assert preview_exists is False


def test_preview_path_rejects_unsafe_filename() -> None:
    with make_repo() as temp:
        root = Path(temp)
        try:
            docs_import.resolve_preview_path(root, "library", "../escape.md")
        except ValueError as exc:
            message = str(exc)
        else:
            raise AssertionError("unsafe preview path should fail")

    assert "unsafe preview filename" in message


def test_invalid_jsonl_is_a_file_level_blocker() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged(root, "broken.jsonl", '{"doc_id": "alpha"}\n{bad json}\n')
        report = parse(root, "broken.jsonl")

    assert report["ok"] is False
    assert report["counts"]["errors"] == 1
    assert report["counts"]["records"] == 0
    assert report["records"] == []
    assert report["issues"][0]["code"] == "invalid_jsonl"


def test_parser_rejects_paths_outside_staging_root() -> None:
    with make_repo() as temp:
        root = Path(temp)
        outside = root / "outside.json"
        outside.write_text("[]\n", encoding="utf-8")
        report = docs_import.parse_staged_import(repo_root=root, scope="library", staged_file=str(outside))

    assert report["ok"] is False
    assert report["counts"]["errors"] == 1
    assert report["issues"][0]["code"] == "unsafe_staged_path"


def main() -> None:
    tests = [
        test_jsonl_summary_export_rows_are_detected_and_normalized,
        test_staged_import_listing_skips_package_sidecars,
        test_configured_studio_scope_json_envelope_can_be_previewed,
        test_json_envelope_relationship_export_preserves_tree_metadata,
        test_json_records_envelope_is_parsed_without_legacy_documents_key,
        test_jsonl_full_content_is_detected_from_source_text_without_metadata,
        test_minimal_hand_authored_json_array_reports_malformed_records_but_keeps_parsing,
        test_current_library_lookup_adds_record_level_warnings,
        test_current_lookup_uses_source_metadata,
        test_missing_source_metadata_adds_current_context_warning,
        test_summary_preview_writes_one_file_per_document_with_fallback_names,
        test_full_content_preview_preserves_headings_and_source_text,
        test_preview_renderer_can_dry_run_without_writing_files,
        test_preview_path_rejects_unsafe_filename,
        test_invalid_jsonl_is_a_file_level_blocker,
        test_parser_rejects_paths_outside_staging_root,
    ]
    for test in tests:
        test()


if __name__ == "__main__":
    main()
