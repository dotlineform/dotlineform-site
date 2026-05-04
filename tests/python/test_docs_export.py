#!/usr/bin/env python3
"""Focused checks for Docs Viewer export validation, reporting, and v1 workflows."""

from __future__ import annotations

import copy
import datetime as dt
import importlib.util
import json
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_EXPORT_PATH = REPO_ROOT / "scripts" / "docs" / "docs_export.py"


def load_docs_export_module():
    spec = importlib.util.spec_from_file_location("docs_export", DOCS_EXPORT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load docs_export.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


docs_export = load_docs_export_module()


BASE_CONFIG = {
    "schema_version": "library_export_configs_v1",
    "configs": [
        {
            "id": "library-document-summaries",
            "label": "Document summaries",
            "description": "Exports summary metadata.",
            "enabled": True,
            "scopes": ["library"],
            "target": {
                "format": "jsonl",
                "record_shape": "document_rows",
                "include_export_metadata": True,
            },
            "output": {
                "path_pattern": "var/docs/exports/{scope}/{export_id}-{timestamp}.jsonl",
                "timestamp_format": "%Y%m%d-%H%M%S",
            },
            "selection": {
                "mode": "explicit_doc_ids",
                "include_descendants": True,
                "include_non_viewable": True,
                "exclude_archived": False,
                "exclude_unpublished": True,
                "supports_missing_summary_only": True,
                "default_missing_summary_only": True,
            },
            "limits": {
                "max_documents": None,
                "max_chars_per_document": None,
                "max_total_chars": None,
                "truncate": {
                    "enabled": False,
                    "strategy": "paragraph_boundary",
                    "marker": "[truncated]",
                },
            },
            "metadata": {
                "include": ["export_id", "config_id", "scope", "generated_at", "selected_doc_ids", "counts"],
            },
            "document_fields": [
                {"source": "doc_id", "output_path": "doc_id", "required": True},
                {"source": "title", "output_path": "title", "required": True},
                {"source": "current_summary", "output_path": "current_summary", "default": ""},
                {"source": "last_updated", "output_path": "last_updated", "required": True},
            ],
        }
    ],
}


INDEX_PAYLOAD = {
    "docs": [
        {
            "doc_id": "library",
            "title": "Library",
            "parent_id": "",
            "summary": "",
            "last_updated": "2026-05-03 10:00",
            "published": True,
            "viewable": True,
        },
        {
            "doc_id": "child-with-summary",
            "title": "Child With Summary",
            "parent_id": "library",
            "summary": "Existing summary.",
            "last_updated": "2026-05-03 10:01",
            "published": True,
            "viewable": True,
        },
        {
            "doc_id": "archive",
            "title": "Archive",
            "parent_id": "",
            "summary": "",
            "last_updated": "2026-05-03 10:02",
            "published": True,
            "viewable": False,
        },
    ],
}


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def make_repo(config: dict | None = None) -> tempfile.TemporaryDirectory:
    temp_dir = tempfile.TemporaryDirectory()
    root = Path(temp_dir.name)
    (root / "_config.yml").write_text("title: Test\n", encoding="utf-8")
    write_json(root / "assets/studio/data/library_export_configs.json", config or BASE_CONFIG)
    write_json(root / "assets/data/docs/scopes/library/index.json", INDEX_PAYLOAD)
    for doc in INDEX_PAYLOAD["docs"]:
        write_json(
            root / f"assets/data/docs/scopes/library/by-id/{doc['doc_id']}.json",
            {
                "doc_id": doc["doc_id"],
                "title": doc["title"],
                "content_html": f"<h1>{doc['title']}</h1><p>Body text.</p>",
            },
        )
    return temp_dir


def run_export(root: Path, **overrides):
    args = {
        "repo_root": root,
        "config_id": "library-document-summaries",
        "scope": "library",
        "selected_doc_ids": ["library"],
        "select_all": False,
        "missing_summary_only": None,
        "write": False,
    }
    args.update(overrides)
    return docs_export.build_export(**args)


def test_missing_summary_filter_reports_expected_skips() -> None:
    with make_repo() as temp:
        report = run_export(Path(temp))
    assert report["ok"] is True
    assert report["counts"] == {"selected": 1, "exported": 1, "skipped": 1, "failed": 0, "truncated": 0}
    assert report["skipped_summary"] == {"has_summary": 1}
    assert report["warnings"] == ["selection: 1 document(s) skipped because they already have summaries"]


def test_selected_doc_resolution_expands_descendants_in_index_order() -> None:
    with make_repo() as temp:
        report = run_export(Path(temp), missing_summary_only=False)
    assert report["ok"] is True
    assert report["selected_doc_ids"] == ["library", "child-with-summary"]
    assert report["exported_doc_ids"] == ["library", "child-with-summary"]
    assert report["skipped"] == []


def test_unknown_selected_doc_blocks_export() -> None:
    with make_repo() as temp:
        report = run_export(Path(temp), selected_doc_ids=["missing-doc"])
    assert report["ok"] is False
    assert report["counts"]["skipped"] == 1
    assert report["skipped_summary"] == {"unknown_doc_id": 1}
    assert "selection: unknown doc_id value(s): missing-doc" in report["errors"]
    assert report["output_written"] is False


def test_config_validation_blocks_duplicate_output_paths() -> None:
    config = copy.deepcopy(BASE_CONFIG)
    config["configs"][0]["document_fields"].append(
        {"source": "title", "output_path": "title", "required": True}
    )
    with make_repo(config) as temp:
        report = run_export(Path(temp))
    assert report["ok"] is False
    assert "config library-document-summaries: duplicate document output_path title" in report["errors"]


def test_unknown_config_returns_structured_validation_report() -> None:
    with make_repo() as temp:
        report = run_export(Path(temp), config_id="missing-config")
    assert report["ok"] is False
    assert report["counts"] == {"selected": 0, "exported": 0, "skipped": 0, "failed": 0, "truncated": 0}
    assert report["errors"] == ["Unknown export config id: missing-config"]
    assert report["issue_counts"] == {"errors": 1, "warnings": 0}


def test_jsonl_config_requires_jsonl_output_extension() -> None:
    config = copy.deepcopy(BASE_CONFIG)
    config["configs"][0]["output"]["path_pattern"] = "var/docs/exports/{scope}/{export_id}-{timestamp}.json"
    with make_repo(config) as temp:
        report = run_export(Path(temp))
    assert report["ok"] is False
    assert "config library-document-summaries: output.path_pattern extension must match target.format" in report["errors"]


def test_written_jsonl_output_is_deterministic_for_fixed_run_time() -> None:
    fixed_generated_at = "2026-05-03T15:15:07Z"
    fixed_filename_dt = dt.datetime(2026, 5, 3, 16, 15, 7, tzinfo=dt.timezone(dt.timedelta(hours=1)))
    original_export_run_times = docs_export.export_run_times
    docs_export.export_run_times = lambda: (fixed_generated_at, fixed_filename_dt)
    try:
        with make_repo() as temp:
            root = Path(temp)
            first_report = run_export(root, missing_summary_only=False, write=True)
            first_output = root / first_report["output_file"]
            first_text = first_output.read_text(encoding="utf-8")

            second_report = run_export(root, missing_summary_only=False, write=True)
            second_text = (root / second_report["output_file"]).read_text(encoding="utf-8")
    finally:
        docs_export.export_run_times = original_export_run_times

    assert first_report["ok"] is True
    assert first_report["output_file"] == (
        "var/docs/exports/library/library-document-summaries-20260503-161507.jsonl"
    )
    assert first_text == second_text
    rows = [json.loads(line) for line in first_text.splitlines()]
    assert [row["doc_id"] for row in rows] == ["library", "child-with-summary"]
    assert rows[0]["_export"]["generated_at"] == fixed_generated_at
    assert rows[0]["_export"]["selected_doc_ids"] == ["library", "child-with-summary"]


def test_export_run_times_use_utc_metadata_and_local_filename_time() -> None:
    generated_at, filename_dt = docs_export.export_run_times(
        dt.datetime(2026, 5, 3, 15, 15, 7, tzinfo=dt.timezone.utc),
        filename_timezone=dt.timezone(dt.timedelta(hours=1)),
    )
    assert generated_at == "2026-05-03T15:15:07Z"
    assert filename_dt.strftime("%Y%m%d-%H%M%S") == "20260503-161507"


def test_repo_library_export_configs_load_and_validate() -> None:
    payload = docs_export.load_config_file(REPO_ROOT)
    payload_errors, payload_warnings = docs_export.validate_config_payload(payload)
    assert payload_errors == []
    assert payload_warnings == []

    configs = payload["configs"]
    config_ids = [config["id"] for config in configs]
    assert config_ids == [
        "library-parent-child-relationships",
        "library-document-summaries",
        "library-full-document-content",
    ]
    for config in configs:
        errors, warnings = docs_export.validate_export_config(config)
        assert errors == []
        assert warnings == []

    summary_fields = {
        field["source"]
        for field in docs_export.find_export_config(payload, "library-document-summaries")["document_fields"]
    }
    full_fields = {
        field["source"]
        for field in docs_export.find_export_config(payload, "library-full-document-content")["document_fields"]
    }
    assert "source_text" not in summary_fields
    assert "source_text" in full_fields
    relationship_fields = {
        "parent_id",
        "parent_title",
        "ancestor_ids",
        "ancestor_titles",
        "child_ids",
        "child_titles",
    }
    assert relationship_fields <= full_fields
    assert "sort_order" not in full_fields


def test_repo_full_document_content_exports_relationship_fields() -> None:
    config = docs_export.load_config_file(REPO_ROOT)
    fixed_generated_at = "2026-05-04T12:00:00Z"
    fixed_filename_dt = dt.datetime(2026, 5, 4, 13, 0, 0, tzinfo=dt.timezone(dt.timedelta(hours=1)))
    original_export_run_times = docs_export.export_run_times
    docs_export.export_run_times = lambda: (fixed_generated_at, fixed_filename_dt)
    try:
        with make_repo(copy.deepcopy(config)) as temp:
            root = Path(temp)
            report = docs_export.build_export(
                repo_root=root,
                config_id="library-full-document-content",
                scope="library",
                selected_doc_ids=["library"],
                select_all=False,
                missing_summary_only=None,
                write=True,
            )
            output = root / report["output_file"]
            rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    finally:
        docs_export.export_run_times = original_export_run_times

    assert report["ok"] is True, report
    assert report["output_written"] is True
    assert [row["doc_id"] for row in rows] == ["library", "child-with-summary"]
    library_row = rows[0]
    child_row = rows[1]
    assert library_row["parent_id"] == ""
    assert library_row["parent_title"] == ""
    assert library_row["ancestor_ids"] == []
    assert library_row["ancestor_titles"] == []
    assert library_row["child_ids"] == ["child-with-summary"]
    assert library_row["child_titles"] == ["Child With Summary"]
    assert child_row["parent_id"] == "library"
    assert child_row["parent_title"] == "Library"
    assert child_row["ancestor_ids"] == ["library"]
    assert child_row["ancestor_titles"] == ["Library"]
    assert child_row["child_ids"] == []
    assert child_row["child_titles"] == []
    assert "sort_order" not in library_row
    assert "sort_order" not in child_row


def test_repo_parent_child_relationships_respects_selected_docs() -> None:
    report = docs_export.build_export(
        repo_root=REPO_ROOT,
        config_id="library-parent-child-relationships",
        scope="library",
        selected_doc_ids=["can-the-brain-comprehend-how-it-works"],
        select_all=False,
        missing_summary_only=None,
        write=False,
    )
    assert report["ok"] is True, report
    assert report["selected_doc_ids"] == ["can-the-brain-comprehend-how-it-works"]
    assert report["exported_doc_ids"] == ["can-the-brain-comprehend-how-it-works"]
    assert report["counts"]["exported"] == 1


def test_repo_representative_library_exports_dry_run_successfully() -> None:
    cases = [
        {
            "config_id": "library-parent-child-relationships",
            "selected_doc_ids": ["library"],
            "select_all": False,
            "missing_summary_only": None,
            "target_format": "json",
        },
        {
            "config_id": "library-document-summaries",
            "selected_doc_ids": ["library"],
            "select_all": False,
            "missing_summary_only": False,
            "target_format": "jsonl",
        },
        {
            "config_id": "library-full-document-content",
            "selected_doc_ids": ["can-the-brain-comprehend-how-it-works"],
            "select_all": False,
            "missing_summary_only": None,
            "target_format": "jsonl",
        },
    ]
    for case in cases:
        report = docs_export.build_export(
            repo_root=REPO_ROOT,
            config_id=case["config_id"],
            scope="library",
            selected_doc_ids=case["selected_doc_ids"],
            select_all=case["select_all"],
            missing_summary_only=case["missing_summary_only"],
            write=False,
        )
        assert report["ok"] is True, report
        assert report["dry_run"] is True
        assert report["target_format"] == case["target_format"]
        assert report["counts"]["exported"] > 0
        assert report["counts"]["failed"] == 0
        assert report["output_written"] is False
        assert report["output_file"].startswith(f"var/docs/exports/library/{case['config_id']}-")
        assert report["output_file"].endswith(f".{case['target_format']}")


def main() -> None:
    tests = [
        test_missing_summary_filter_reports_expected_skips,
        test_selected_doc_resolution_expands_descendants_in_index_order,
        test_unknown_selected_doc_blocks_export,
        test_config_validation_blocks_duplicate_output_paths,
        test_unknown_config_returns_structured_validation_report,
        test_jsonl_config_requires_jsonl_output_extension,
        test_written_jsonl_output_is_deterministic_for_fixed_run_time,
        test_export_run_times_use_utc_metadata_and_local_filename_time,
        test_repo_library_export_configs_load_and_validate,
        test_repo_full_document_content_exports_relationship_fields,
        test_repo_parent_child_relationships_respects_selected_docs,
        test_repo_representative_library_exports_dry_run_successfully,
    ]
    for test in tests:
        test()


if __name__ == "__main__":
    main()
