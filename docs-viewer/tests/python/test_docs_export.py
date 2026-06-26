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


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_EXPORT_PATH = REPO_ROOT / "docs-viewer" / "services" / "docs_export.py"
DOCS_SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
if str(DOCS_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(DOCS_SERVICES_DIR))


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
    "schema_version": "documents_prepare_profiles_v1",
    "configs": [
        {
            "id": "document-summaries",
            "label": "Document summaries",
            "description": "Exports summary metadata.",
            "enabled": True,
            "data_domains": ["documents"],
            "target": {
                "format": "jsonl",
                "supported_formats": ["jsonl", "json"],
                "record_shape": "document_rows",
                "include_export_metadata": True,
            },
            "output": {
                "path_pattern": "var/analytics/data-sharing/exports/{data_domain}-{export_id}-{timestamp}.jsonl",
                "timestamp_format": "%Y%m%d-%H%M%S",
            },
            "selection": {
                "mode": "explicit_doc_ids",
                "include_descendants": True,
                "include_non_viewable": True,
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
            "external_context": {
                "task": "suggest_document_summaries",
                "response_guidance": "Return proposed summary changes keyed by doc_id.",
                "field_descriptions": {
                    "doc_id": "Stable document identifier. Preserve exactly in responses.",
                    "title": "Document title.",
                    "current_summary": "Existing document summary.",
                },
            },
            "document_fields": [
                {"source": "doc_id", "output_path": "doc_id", "required": True},
                {"source": "title", "output_path": "title", "required": True},
                {"source": "current_summary", "output_path": "current_summary", "default": ""},
            ],
        }
    ],
}


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_scope_config(root: Path) -> None:
    write_json(
        root / "docs-viewer/config/scopes/docs_scopes.json",
        {
            "schema_version": "docs_scopes_v1",
            "scopes": [
                {
                    "scope_id": "library",
                    "scope_type": "public",
                    "source": "docs-viewer/source/library",
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
        },
    )


def write_doc(
    root: Path,
    filename: str,
    *,
    doc_id: str,
    title: str,
    parent_id: str = "",
    summary: str = "",
    last_updated: str = "2026-05-03 10:00",
    viewable: bool = True,
    body: str = "Body text.",
) -> None:
    lines = [
        "---",
        f"doc_id: {doc_id}",
        f"title: {title}",
        "added_date: 2026-05-03",
        f"last_updated: {last_updated}",
    ]
    if parent_id:
        lines.append(f"parent_id: {parent_id}")
    if summary:
        lines.append(f"summary: {summary}")
    if not viewable:
        lines.append("viewable: false")
    lines.extend(["---", "", body])
    path = root / "docs-viewer/source/library" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def make_repo(config: dict | None = None) -> tempfile.TemporaryDirectory:
    temp_dir = tempfile.TemporaryDirectory()
    root = Path(temp_dir.name)
    (root / "site-tools/config").mkdir(parents=True, exist_ok=True); (root / "site-tools/config/site-tools.json").write_text("{\"schema_version\":\"site_tools_config_v1\"}\n", encoding="utf-8")
    write_json(root / "data-sharing/adapters/documents/config/prepare-profiles.json", config or BASE_CONFIG)
    write_scope_config(root)
    write_doc(root, "library.md", doc_id="library", title="Library", body="# Library\n\nBody text.")
    write_doc(
        root,
        "child-with-summary.md",
        doc_id="child-with-summary",
        title="Child With Summary",
        parent_id="library",
        summary="Existing summary.",
        last_updated="2026-05-03 10:01",
        body="# Child With Summary\n\nBody text.",
    )
    return temp_dir


def run_export(root: Path, **overrides):
    args = {
        "repo_root": root,
        "config_id": "document-summaries",
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
    assert report["counts"] == {"selected": 1, "exported": 1, "skipped": 0, "failed": 0, "truncated": 0}
    assert report["skipped_summary"] == {}
    assert report["warnings"] == []


def test_selected_doc_resolution_uses_explicit_ids_only() -> None:
    with make_repo() as temp:
        report = run_export(Path(temp), missing_summary_only=False)
    assert report["ok"] is True
    assert report["selected_doc_ids"] == ["library"]
    assert report["exported_doc_ids"] == ["library"]
    assert report["skipped"] == []


def test_selected_docs_are_exported_in_doc_id_order() -> None:
    with make_repo() as temp:
        report = run_export(
            Path(temp),
            selected_doc_ids=["library", "child-with-summary"],
            missing_summary_only=False,
        )
    assert report["ok"] is True
    assert report["selected_doc_ids"] == ["child-with-summary", "library"]
    assert report["exported_doc_ids"] == ["child-with-summary", "library"]


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
    assert "config document-summaries: duplicate document output_path title" in report["errors"]


def test_config_validation_requires_external_context_descriptions() -> None:
    config = copy.deepcopy(BASE_CONFIG)
    del config["configs"][0]["external_context"]["field_descriptions"]["current_summary"]
    config["configs"][0]["external_context"]["field_descriptions"]["retired_field"] = "Stale field."
    with make_repo(config) as temp:
        report = run_export(Path(temp))

    assert report["ok"] is False
    assert "config document-summaries: external_context.field_descriptions.current_summary is required" in report["errors"]
    assert "config document-summaries: external_context.field_descriptions.retired_field does not match a document output_path" in report["errors"]


def test_unknown_config_returns_structured_validation_report() -> None:
    with make_repo() as temp:
        report = run_export(Path(temp), config_id="missing-config")
    assert report["ok"] is False
    assert report["counts"] == {"selected": 0, "exported": 0, "skipped": 0, "failed": 0, "truncated": 0}
    assert report["errors"] == ["Unknown export config id: missing-config"]
    assert report["issue_counts"] == {"errors": 1, "warnings": 0}


def test_jsonl_config_requires_jsonl_output_extension() -> None:
    config = copy.deepcopy(BASE_CONFIG)
    config["configs"][0]["output"]["path_pattern"] = "var/analytics/data-sharing/exports/{data_domain}-{export_id}-{timestamp}.json"
    with make_repo(config) as temp:
        report = run_export(Path(temp))
    assert report["ok"] is False
    assert "config document-summaries: output.path_pattern extension must match target.format" in report["errors"]


def test_written_jsonl_output_is_deterministic_for_fixed_run_time() -> None:
    fixed_generated_at = "2026-05-03T15:15:07Z"
    fixed_filename_dt = dt.datetime(2026, 5, 3, 16, 15, 7, tzinfo=dt.timezone(dt.timedelta(hours=1)))
    original_export_run_times = docs_export.export_run_times
    docs_export.export_run_times = lambda: (fixed_generated_at, fixed_filename_dt)
    try:
        with make_repo() as temp:
            root = Path(temp)
            selected_doc_ids = ["library", "child-with-summary"]
            first_report = run_export(root, selected_doc_ids=selected_doc_ids, missing_summary_only=False, write=True)
            first_output = root / first_report["output_file"]
            first_metadata_output = root / first_report["metadata_file"]
            first_context_output = root / first_report["context_file"]
            first_text = first_output.read_text(encoding="utf-8")
            first_metadata_text = first_metadata_output.read_text(encoding="utf-8")
            first_context_text = first_context_output.read_text(encoding="utf-8")

            second_report = run_export(root, selected_doc_ids=selected_doc_ids, missing_summary_only=False, write=True)
            second_text = (root / second_report["output_file"]).read_text(encoding="utf-8")
            second_metadata_text = (root / second_report["metadata_file"]).read_text(encoding="utf-8")
            second_context_text = (root / second_report["context_file"]).read_text(encoding="utf-8")
    finally:
        docs_export.export_run_times = original_export_run_times

    assert first_report["ok"] is True
    assert first_report["output_file"] == (
        "var/analytics/data-sharing/exports/documents-document-summaries-20260503-161507.jsonl"
    )
    assert first_report["metadata_file"] == (
        "var/analytics/data-sharing/exports/documents-document-summaries-20260503-161507.meta.json"
    )
    assert first_report["context_file"] == (
        "var/analytics/data-sharing/exports/documents-document-summaries-20260503-161507.context.json"
    )
    assert first_text == second_text
    assert first_metadata_text == second_metadata_text
    assert first_context_text == second_context_text
    rows = [json.loads(line) for line in first_text.splitlines()]
    metadata = json.loads(first_metadata_text)
    context = json.loads(first_context_text)
    assert [row["doc_id"] for row in rows] == ["child-with-summary", "library"]
    assert "_export" not in rows[0]
    assert "last_updated" not in rows[0]
    assert metadata["generated_at"] == fixed_generated_at
    assert metadata["scope"] == "library"
    assert metadata["selected_doc_ids"] == ["child-with-summary", "library"]
    assert context["task"] == "suggest_document_summaries"
    assert context["response_guidance"] == "Return proposed summary changes keyed by doc_id."
    assert context["record_format"] == "jsonl"
    assert {field["field"] for field in context["record_schema"]} >= {"doc_id", "title", "current_summary"}
    description_by_field = {field["field"]: field["description"] for field in context["record_schema"]}
    assert description_by_field["current_summary"] == "Existing document summary."
    assert "last_updated" not in {field["field"] for field in context["record_schema"]}
    assert "generated_at" not in context
    assert "counts" not in context


def test_document_rows_json_format_override_writes_json_array() -> None:
    fixed_generated_at = "2026-05-03T15:15:07Z"
    fixed_filename_dt = dt.datetime(2026, 5, 3, 16, 15, 7, tzinfo=dt.timezone(dt.timedelta(hours=1)))
    original_export_run_times = docs_export.export_run_times
    docs_export.export_run_times = lambda: (fixed_generated_at, fixed_filename_dt)
    try:
        with make_repo() as temp:
            root = Path(temp)
            report = run_export(
                root,
                selected_doc_ids=["library", "child-with-summary"],
                missing_summary_only=False,
                write=True,
                target_format="json",
            )
            payload = json.loads((root / report["output_file"]).read_text(encoding="utf-8"))
            metadata = json.loads((root / report["metadata_file"]).read_text(encoding="utf-8"))
            context = json.loads((root / report["context_file"]).read_text(encoding="utf-8"))
    finally:
        docs_export.export_run_times = original_export_run_times

    assert report["ok"] is True, report
    assert report["target_format"] == "json"
    assert report["output_file"] == (
        "var/analytics/data-sharing/exports/documents-document-summaries-20260503-161507.json"
    )
    assert isinstance(payload, list)
    assert [row["doc_id"] for row in payload] == ["child-with-summary", "library"]
    assert "_export" not in payload[0]
    assert "last_updated" not in payload[0]
    assert metadata["generated_at"] == fixed_generated_at
    assert metadata["scope"] == "library"
    assert context["record_container"] == "JSON array of document objects"


def test_unsupported_format_override_blocks_export() -> None:
    config = copy.deepcopy(BASE_CONFIG)
    config["configs"][0]["target"]["supported_formats"] = ["jsonl"]
    with make_repo(config) as temp:
        report = run_export(Path(temp), target_format="json")

    assert report["ok"] is False
    assert "config document-summaries: target_format 'json' is not supported; supported formats: jsonl" in report["errors"]
    assert report["target_format"] == "json"
    assert report["output_file"].endswith(".json")
    assert report["output_written"] is False


def test_export_run_times_use_utc_metadata_and_local_filename_time() -> None:
    generated_at, filename_dt = docs_export.export_run_times(
        dt.datetime(2026, 5, 3, 15, 15, 7, tzinfo=dt.timezone.utc),
        filename_timezone=dt.timezone(dt.timedelta(hours=1)),
    )
    assert generated_at == "2026-05-03T15:15:07Z"
    assert filename_dt.strftime("%Y%m%d-%H%M%S") == "20260503-161507"


def test_repo_documents_prepare_profiles_load_and_validate() -> None:
    payload = docs_export.load_config_file(REPO_ROOT)
    payload_errors, payload_warnings = docs_export.validate_config_payload(payload)
    assert payload_errors == []
    assert payload_warnings == []

    configs = payload["configs"]
    config_ids = [config["id"] for config in configs]
    assert config_ids == [
        "parent-child-relationships",
        "document-summaries",
        "document-content",
    ]
    for config in configs:
        errors, warnings = docs_export.validate_export_config(config)
        assert errors == []
        assert warnings == []

    summary_fields = {
        field["source"]
        for field in docs_export.find_export_config(payload, "document-summaries")["document_fields"]
    }
    full_fields = {
        field["source"]
        for field in docs_export.find_export_config(payload, "document-content")["document_fields"]
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

    relationship_config = docs_export.find_export_config(payload, "parent-child-relationships")
    summary_config = docs_export.find_export_config(payload, "document-summaries")
    full_config = docs_export.find_export_config(payload, "document-content")
    assert docs_export.supported_target_formats(relationship_config) == ["json"]
    assert docs_export.supported_target_formats(summary_config) == ["jsonl", "json"]
    assert docs_export.supported_target_formats(full_config) == ["jsonl", "json"]


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
                config_id="document-content",
                scope="library",
                selected_doc_ids=["library", "child-with-summary"],
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
    assert report["metadata_file"].endswith(".meta.json")
    assert [row["doc_id"] for row in rows] == ["child-with-summary", "library"]
    assert "last_updated" not in rows[0]
    rows_by_doc_id = {row["doc_id"]: row for row in rows}
    library_row = rows_by_doc_id["library"]
    child_row = rows_by_doc_id["child-with-summary"]
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


def test_export_uses_source_metadata_for_document_content() -> None:
    config = docs_export.load_config_file(REPO_ROOT)
    with make_repo(copy.deepcopy(config)) as temp:
        root = Path(temp)

        report = docs_export.build_export(
            repo_root=root,
            config_id="document-content",
            scope="library",
            selected_doc_ids=["library", "child-with-summary"],
            select_all=False,
            missing_summary_only=None,
            write=True,
        )
        rows = [json.loads(line) for line in (root / report["output_file"]).read_text(encoding="utf-8").splitlines()]

    assert report["ok"] is True, report
    assert report["exported_doc_ids"] == ["child-with-summary", "library"]
    rows_by_doc_id = {row["doc_id"]: row for row in rows}
    assert rows_by_doc_id["library"]["source_text"] == "Body text."


def test_missing_source_metadata_returns_structured_export_error() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_json(
            root / "docs-viewer/config/scopes/docs_scopes.json",
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
            },
        )
        report = run_export(root)

    assert report["ok"] is False
    assert report["counts"] == {"selected": 0, "exported": 0, "skipped": 0, "failed": 0, "truncated": 0}
    assert report["output_written"] is False
    assert "source metadata: missing source root for scope library: docs-viewer/source/missing-library" in report["errors"]


def test_repo_parent_child_relationships_respects_selected_docs() -> None:
    report = docs_export.build_export(
        repo_root=REPO_ROOT,
        config_id="parent-child-relationships",
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


def test_envelope_json_export_writes_clean_payload_and_sidecars() -> None:
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
                config_id="parent-child-relationships",
                scope="library",
                selected_doc_ids=["library", "child-with-summary"],
                select_all=False,
                missing_summary_only=None,
                write=True,
            )
            payload = json.loads((root / report["output_file"]).read_text(encoding="utf-8"))
            metadata = json.loads((root / report["metadata_file"]).read_text(encoding="utf-8"))
            context = json.loads((root / report["context_file"]).read_text(encoding="utf-8"))
    finally:
        docs_export.export_run_times = original_export_run_times

    assert report["ok"] is True, report
    assert sorted(payload.keys()) == ["documents"]
    assert [row["doc_id"] for row in payload["documents"]] == ["child-with-summary", "library"]
    assert "last_updated" not in payload["documents"][0]
    assert metadata["generated_at"] == fixed_generated_at
    assert metadata["scope"] == "library"
    assert metadata["counts"]["exported"] == 2
    assert context["task"] == "review parent-child relationships"
    assert context["records_path"] == "documents"
    assert "counts" not in context


def test_repo_representative_library_exports_dry_run_successfully() -> None:
    cases = [
        {
            "config_id": "parent-child-relationships",
            "selected_doc_ids": ["library"],
            "select_all": False,
            "missing_summary_only": None,
            "target_format": "json",
        },
        {
            "config_id": "document-summaries",
            "selected_doc_ids": ["library"],
            "select_all": False,
            "missing_summary_only": False,
            "target_format": "jsonl",
        },
        {
            "config_id": "document-content",
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
        assert report["output_file"].startswith(f"var/analytics/data-sharing/exports/documents-{case['config_id']}-")
        assert report["output_file"].endswith(f".{case['target_format']}")
        assert report["metadata_file"].endswith(".meta.json")
        assert report["context_file"].endswith(".context.json")


def main() -> None:
    tests = [
        test_missing_summary_filter_reports_expected_skips,
        test_selected_doc_resolution_uses_explicit_ids_only,
        test_unknown_selected_doc_blocks_export,
        test_config_validation_blocks_duplicate_output_paths,
        test_config_validation_requires_external_context_descriptions,
        test_unknown_config_returns_structured_validation_report,
        test_jsonl_config_requires_jsonl_output_extension,
        test_written_jsonl_output_is_deterministic_for_fixed_run_time,
        test_document_rows_json_format_override_writes_json_array,
        test_unsupported_format_override_blocks_export,
        test_export_run_times_use_utc_metadata_and_local_filename_time,
        test_repo_documents_prepare_profiles_load_and_validate,
        test_repo_full_document_content_exports_relationship_fields,
        test_export_uses_source_metadata_for_document_content,
        test_missing_source_metadata_returns_structured_export_error,
        test_repo_parent_child_relationships_respects_selected_docs,
        test_envelope_json_export_writes_clean_payload_and_sidecars,
        test_repo_representative_library_exports_dry_run_successfully,
    ]
    for test in tests:
        test()


if __name__ == "__main__":
    main()
