#!/usr/bin/env python3
"""Focused checks for Docs Viewer export validation and reporting."""

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
                "exclude_archived": True,
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
                "include": ["export_id", "config_id", "scope", "generated_at", "counts"],
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
            "doc_id": "_archive",
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


def test_export_run_times_use_utc_metadata_and_local_filename_time() -> None:
    generated_at, filename_dt = docs_export.export_run_times(
        dt.datetime(2026, 5, 3, 15, 15, 7, tzinfo=dt.timezone.utc),
        filename_timezone=dt.timezone(dt.timedelta(hours=1)),
    )
    assert generated_at == "2026-05-03T15:15:07Z"
    assert filename_dt.strftime("%Y%m%d-%H%M%S") == "20260503-161507"


def main() -> None:
    tests = [
        test_missing_summary_filter_reports_expected_skips,
        test_unknown_selected_doc_blocks_export,
        test_config_validation_blocks_duplicate_output_paths,
        test_unknown_config_returns_structured_validation_report,
        test_jsonl_config_requires_jsonl_output_extension,
        test_export_run_times_use_utc_metadata_and_local_filename_time,
    ]
    for test in tests:
        test()


if __name__ == "__main__":
    main()
