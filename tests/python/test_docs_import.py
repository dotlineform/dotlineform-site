#!/usr/bin/env python3
"""Focused checks for the read-only Docs Viewer import parser."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_IMPORT_PATH = REPO_ROOT / "scripts" / "docs" / "docs_import.py"


def load_docs_import_module():
    spec = importlib.util.spec_from_file_location("docs_import", DOCS_IMPORT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load docs_import.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


docs_import = load_docs_import_module()


def make_repo() -> tempfile.TemporaryDirectory:
    temp_dir = tempfile.TemporaryDirectory()
    root = Path(temp_dir.name)
    (root / "_config.yml").write_text("title: Test\n", encoding="utf-8")
    (root / "var/docs/import-staging/library").mkdir(parents=True, exist_ok=True)
    write_current_index(
        root,
        [
            {"doc_id": "library", "title": "Library", "parent_id": "", "published": True, "viewable": True},
            {"doc_id": "alpha", "title": "Alpha", "parent_id": "library", "published": True, "viewable": True},
            {"doc_id": "beta", "title": "Beta", "parent_id": "library", "published": True, "viewable": True},
            {
                "doc_id": "missing-title",
                "title": "Missing Title",
                "parent_id": "library",
                "published": True,
                "viewable": True,
            },
        ],
    )
    return temp_dir


def write_current_index(root: Path, docs: list[dict], *, payload_ids: list[str] | None = None) -> None:
    index_path = root / "assets/data/docs/scopes/library/index.json"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps({"docs": docs}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    payload_root = root / "assets/data/docs/scopes/library/by-id"
    payload_root.mkdir(parents=True, exist_ok=True)
    for existing in payload_root.glob("*.json"):
        existing.unlink()
    ids = payload_ids if payload_ids is not None else [doc["doc_id"] for doc in docs if doc.get("doc_id")]
    for doc_id in ids:
        (payload_root / f"{doc_id}.json").write_text(
            json.dumps({"doc_id": doc_id, "title": doc_id}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


def write_staged(root: Path, filename: str, text: str) -> None:
    path = root / "var/docs/import-staging/library" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def parse(root: Path, filename: str):
    return docs_import.parse_staged_import(repo_root=root, scope="library", staged_file=filename)


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
                {"doc_id": "library", "title": "Library", "parent_id": "", "published": True, "viewable": True},
                {
                    "doc_id": "unpublished-parent",
                    "title": "Unpublished Parent",
                    "parent_id": "library",
                    "published": False,
                    "viewable": False,
                },
                {
                    "doc_id": "no-payload",
                    "title": "No Payload",
                    "parent_id": "library",
                    "published": True,
                    "viewable": True,
                },
            ],
            payload_ids=["library", "unpublished-parent"],
        )
        payload = [
            {"doc_id": "unknown-doc", "title": "Unknown Doc", "parent_id": "missing-parent"},
            {"doc_id": "unpublished-parent", "title": "Unpublished Parent", "parent_id": "library"},
            {"doc_id": "no-payload", "title": "No Payload", "parent_id": "unpublished-parent"},
        ]
        write_staged(root, "lookup.json", json.dumps(payload))
        report = parse(root, "lookup.json")

    assert report["ok"] is True
    assert report["current_library"] == {
        "index_loaded": True,
        "index_path": "assets/data/docs/scopes/library/index.json",
        "doc_count": 3,
        "payload_count": 2,
    }
    assert report["counts"] == {"records": 3, "parsed_records": 3, "malformed_records": 0, "warnings": 5, "errors": 0}
    assert [item["code"] for item in report["issues"]] == [
        "unknown_doc_id",
        "missing_parent_id",
        "current_doc_unpublished",
        "current_payload_missing",
        "parent_unpublished",
    ]
    assert report["records"][0]["current_library"]["exists"] is False
    assert report["records"][1]["current_library"]["published"] is False
    assert report["records"][2]["current_library"]["payload_exists"] is False


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
        test_invalid_jsonl_is_a_file_level_blocker,
        test_parser_rejects_paths_outside_staging_root,
    ]
    for test in tests:
        test()


if __name__ == "__main__":
    main()
