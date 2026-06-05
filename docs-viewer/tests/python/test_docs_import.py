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
    (root / "_config.yml").write_text("title: Test\n", encoding="utf-8")
    (root / "var/analytics/data-sharing/library/import-staging").mkdir(parents=True, exist_ok=True)
    write_scope_config(root)
    write_current_index(
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


def write_current_index(root: Path, docs: list[dict], *, payload_ids: list[str] | None = None) -> None:
    del payload_ids
    source_root = root / "docs-viewer/source/library"
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


def write_scope_config(root: Path) -> None:
    path = root / "docs-viewer/config/scopes/docs_scopes.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "docs_scopes_v1",
                "scopes": [
                    {
                        "scope_id": "library",
                        "scope_type": "public",
                        "source": "docs-viewer/source/library",
                        "media_path_prefix": "docs/library",
                        "output": "assets/data/docs/scopes/library",
                        "search_output": "assets/data/search/library/index.json",
                        "viewer_base_url": "/library/",
                        "include_scope_param": False,
                        "default_doc_id": "library",
                        "allow_nested_source": False,
                        "allow_unresolved_parent_ids": True,
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def write_staged(root: Path, filename: str, text: str) -> None:
    path = root / "var/analytics/data-sharing/library/import-staging" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def parse(root: Path, filename: str):
    return docs_import.parse_staged_import(repo_root=root, scope="library", staged_file=filename)


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
                "_export": {
                    "export_id": "library-document-summaries",
                    "scope": "library",
                    "generated_at": "2026-05-03T20:00:00Z",
                },
                "doc_id": "alpha",
                "title": "Alpha",
                "parent_id": "library",
                "current_summary": "Existing summary.",
                "review_note": "Keep this unknown field.",
            },
            {
                "_export": {
                    "export_id": "library-document-summaries",
                    "scope": "library",
                    "generated_at": "2026-05-03T20:00:00Z",
                },
                "doc_id": "beta",
                "title": "Beta",
                "parent_id": "library",
                "current_summary": "",
            },
        ]
        write_staged(root, "summaries.jsonl", "".join(json.dumps(row) + "\n" for row in rows))
        report = parse(root, "summaries.jsonl")

    assert report["ok"] is True
    assert report["input_format"] == "jsonl"
    assert report["detected_import_type"] == "document_summaries"
    assert report["source_export_id"] == "library-document-summaries"
    assert report["source_scope"] == "library"
    assert report["generated_at"] == "2026-05-03T20:00:00Z"
    assert report["counts"] == {"records": 2, "parsed_records": 2, "malformed_records": 0, "warnings": 0, "errors": 0}
    assert report["records"][0]["metadata"]["current_summary"] == "Existing summary."
    assert report["records"][0]["unknown_metadata"] == {"review_note": "Keep this unknown field."}


def test_json_envelope_relationship_export_preserves_tree_metadata() -> None:
    with make_repo() as temp:
        root = Path(temp)
        payload = {
            "export_id": "library-parent-child-relationships",
            "scope": "library",
            "generated_at": "2026-05-03T20:10:00Z",
            "review_batch": "tree-a",
            "documents": [
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
        report = parse(root, "relationships.json")

    assert report["ok"] is True
    assert report["detected_import_type"] == "parent_child_relationships"
    assert report["unknown_file_metadata"] == {"review_batch": "tree-a"}
    assert report["records"][0]["relationships"]["child_ids"] == ["alpha"]
    assert report["records"][1]["relationships"]["ancestor_ids"] == ["library"]


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
        write_current_index(
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
                    "doc_id": "no-payload",
                    "title": "No Payload",
                    "parent_id": "library",
                    "viewable": True,
                },
            ],
        )
        payload = [
            {"doc_id": "unknown-doc", "title": "Unknown Doc", "parent_id": "missing-parent"},
            {"doc_id": "non-viewable-parent", "title": "Non-viewable Parent", "parent_id": "library"},
            {"doc_id": "no-payload", "title": "No Payload", "parent_id": "non-viewable-parent"},
        ]
        write_staged(root, "lookup.json", json.dumps(payload))
        report = parse(root, "lookup.json")

    assert report["ok"] is True
    assert report["current_library"] == {
        "index_loaded": True,
        "index_path": "docs-viewer/source/library",
        "source_loaded": True,
        "source_root": "docs-viewer/source/library",
        "doc_count": 3,
        "payload_count": 3,
    }
    assert report["counts"] == {"records": 3, "parsed_records": 3, "malformed_records": 0, "warnings": 2, "errors": 0}
    assert [item["code"] for item in report["issues"]] == [
        "unknown_doc_id",
        "missing_parent_id",
    ]
    assert report["records"][0]["current_library"]["exists"] is False
    assert report["records"][2]["current_library"]["source_renderable"] is True


def test_current_lookup_uses_source_metadata_when_generated_artifacts_are_broken() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_text(root / "assets/data/docs/scopes/library/index.json", "{")
        write_text(root / "assets/data/docs/scopes/library/index-tree.json", "{")
        write_text(root / "assets/data/docs/scopes/library/recently-added.json", "{")
        write_text(root / "assets/data/search/library/index.json", "{")
        write_text(root / "assets/data/docs/scopes/library/by-id/alpha.json", "{")
        write_text(root / "assets/data/docs/scopes/library/metadata-index.json", "{")
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
                            "output": "assets/data/docs/scopes/library",
                            "search_output": "assets/data/search/library/index.json",
                            "viewer_base_url": "/library/",
                            "include_scope_param": False,
                            "default_doc_id": "library",
                            "allow_nested_source": False,
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
        first_preview = (root / "var/analytics/data-sharing/library/import-preview/alpha-20260503-204000.md").read_text(encoding="utf-8")
        missing_preview = (root / "var/analytics/data-sharing/library/import-preview/record-3-20260503-204000.md").read_text(encoding="utf-8")

    assert report["preview_written"] is True
    assert [item["path"] for item in report["preview_files"]] == [
        "var/analytics/data-sharing/library/import-preview/summaries-tree-20260503-204000.md",
        "var/analytics/data-sharing/library/import-preview/alpha-20260503-204000.md",
        "var/analytics/data-sharing/library/import-preview/alpha-record-2-20260503-204000.md",
        "var/analytics/data-sharing/library/import-preview/record-3-20260503-204000.md",
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
        preview = (root / "var/analytics/data-sharing/library/import-preview/alpha-20260102-030405.md").read_text(encoding="utf-8")

    assert report["preview_files"] == [
        {
            "path": "var/analytics/data-sharing/library/import-preview/content-tree-20260102-030405.md",
            "record_count": 1,
            "kind": "relationship_tree",
        },
        {
            "path": "var/analytics/data-sharing/library/import-preview/alpha-20260102-030405.md",
            "record_index": 0,
            "doc_id": "alpha",
            "kind": "document",
        }
    ]
    assert "## Imported Headings\n\n- One\n- Two" in preview
    assert "## Imported Source Text\n\n# One\n\n- A point\n\n> A quote" in preview


def test_relationship_preview_writes_one_whole_tree_file() -> None:
    with make_repo() as temp:
        root = Path(temp)
        payload = {
            "export_id": "library-parent-child-relationships",
            "scope": "library",
            "documents": [
                {"doc_id": "library", "title": "Library", "parent_id": ""},
                {"doc_id": "alpha", "title": "Alpha", "parent_id": "library", "summary": "Alpha summary."},
                {"doc_id": "beta", "title": "Beta", "parent_id": "library", "headings": ["Beta Heading"]},
            ],
        }
        write_staged(root, "relationships.json", json.dumps(payload))
        report = render(root, parse(root, "relationships.json"))
        preview = (root / "var/analytics/data-sharing/library/import-preview/relationships-tree-20260503-204000.md").read_text(encoding="utf-8")

    assert report["preview_files"][:1] == [
        {
            "path": "var/analytics/data-sharing/library/import-preview/relationships-tree-20260503-204000.md",
            "record_count": 3,
            "kind": "relationship_tree",
        }
    ]
    assert [item["kind"] for item in report["preview_files"]] == ["relationship_tree", "document", "document", "document"]
    assert 'import_type: "parent_child_relationships"' in preview
    assert "- Library (`library`)\n  - Alpha (`alpha`)" in preview
    assert "  - summary: Alpha summary." in preview
    assert "  - Beta (`beta`)\n    - headings: Beta Heading" in preview


def test_preview_renderer_can_dry_run_without_writing_files() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged(root, "summaries.json", json.dumps([{"doc_id": "alpha", "title": "Alpha"}]))
        report = render(root, parse(root, "summaries.json"), write=False)
        preview_exists = (root / "var/analytics/data-sharing/library/import-preview/alpha-20260503-204000.md").exists()

    assert report["preview_written"] is False
    assert report["preview_files"][0]["path"] == "var/analytics/data-sharing/library/import-preview/alpha-20260503-204000.md"
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
        test_json_envelope_relationship_export_preserves_tree_metadata,
        test_jsonl_full_content_is_detected_from_source_text_without_metadata,
        test_minimal_hand_authored_json_array_reports_malformed_records_but_keeps_parsing,
        test_current_library_lookup_adds_record_level_warnings,
        test_current_lookup_uses_source_metadata_when_generated_artifacts_are_broken,
        test_missing_source_metadata_adds_current_context_warning,
        test_summary_preview_writes_one_file_per_document_with_fallback_names,
        test_full_content_preview_preserves_headings_and_source_text,
        test_relationship_preview_writes_one_whole_tree_file,
        test_preview_renderer_can_dry_run_without_writing_files,
        test_preview_path_rejects_unsafe_filename,
        test_invalid_jsonl_is_a_file_level_blocker,
        test_parser_rejects_paths_outside_staging_root,
    ]
    for test in tests:
        test()


if __name__ == "__main__":
    main()
