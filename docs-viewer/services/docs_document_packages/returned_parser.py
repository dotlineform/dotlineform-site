#!/usr/bin/env python3
"""Returned document-package parser and report assembly."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from docs_document_packages.returned_common import (
    SUPPORTED_EXTENSIONS,
    empty_report,
    issue,
    normalize_text,
    relative_path,
    resolve_staged_path,
)
from docs_document_packages.returned_context import add_current_library_report, current_report_context, load_current_docs_context
from docs_document_packages.returned_files import (
    export_id_from_json_payload,
    export_id_from_jsonl_header,
    metadata_from_internal_export_meta,
    parse_json_file,
    parse_jsonl_file,
    rows_from_payload,
)
from docs_document_packages.returned_profiles import detect_import_type
from docs_document_packages.returned_records import normalize_record
from docs_document_packages.returned_validation import validate_whole_returned_package

def parse_staged_import(
    *,
    repo_root: Path,
    scope: str,
    staged_file: str,
    staging_root: Path | str | None = None,
    metadata_root: Path | None = None,
) -> dict[str, Any]:
    normalized_scope = normalize_text(scope).lower()
    report = empty_report(repo_root, normalized_scope, staged_file)
    try:
        path = resolve_staged_path(repo_root, normalized_scope, staged_file, staging_root)
    except ValueError as exc:
        report["issues"].append(issue("error", "unsafe_staged_path", str(exc)))
        report["counts"]["errors"] = 1
        return report

    report["input_file"] = relative_path(repo_root, path)
    extension = path.suffix.lower()
    report["input_format"] = extension.lstrip(".")
    if extension not in SUPPORTED_EXTENSIONS:
        report["issues"].append(issue("error", "unsupported_extension", f"unsupported extension: {extension or '<none>'}"))
        report["counts"]["errors"] = 1
        return report
    if not path.exists():
        report["issues"].append(issue("error", "unreadable_file", "staged file does not exist"))
        report["counts"]["errors"] = 1
        return report

    try:
        file_metadata: dict[str, Any] = {}
        unknown_file_metadata: dict[str, Any] = {}
        export_id_for_metadata = ""
        if extension == ".jsonl":
            export_id_for_metadata, metadata_issues = export_id_from_jsonl_header(path)
            raw_rows, parse_issues = parse_jsonl_file(path)
            parse_issues.extend(metadata_issues)
        else:
            payload, parse_issues = parse_json_file(path)
            if any(item["level"] == "error" for item in parse_issues):
                raw_rows = []
            else:
                export_id_for_metadata, metadata_issues = export_id_from_json_payload(payload)
                parse_issues.extend(metadata_issues)
                raw_rows, _payload_metadata, _payload_unknown_metadata, shape_issues = rows_from_payload(payload)
                parse_issues.extend(shape_issues)
        if export_id_for_metadata and not any(item["level"] == "error" for item in parse_issues):
            internal_metadata, internal_unknown_metadata, internal_issues, internal_metadata_path = metadata_from_internal_export_meta(
                repo_root,
                export_id_for_metadata,
                metadata_root,
            )
            if internal_metadata_path is not None:
                report["source_metadata_file"] = relative_path(repo_root, internal_metadata_path)
            if internal_metadata:
                file_metadata.update(internal_metadata)
            if internal_unknown_metadata:
                unknown_file_metadata.update(internal_unknown_metadata)
            parse_issues.extend(internal_issues)
    except OSError as exc:
        report["issues"].append(issue("error", "unreadable_file", f"unreadable file: {exc}"))
        report["counts"]["errors"] = 1
        return report

    report["issues"].extend(parse_issues)
    if any(item["level"] == "error" for item in parse_issues):
        report["counts"]["errors"] = len([item for item in report["issues"] if item["level"] == "error"])
        report["counts"]["warnings"] = len([item for item in report["issues"] if item["level"] == "warning"])
        return report

    records: list[dict[str, Any]] = []
    malformed = 0
    seen_doc_ids: dict[str, int] = {}
    for index, row in enumerate(raw_rows):
        line = row.get("_source_line") if isinstance(row, dict) and isinstance(row.get("_source_line"), int) else None
        if not isinstance(row, dict):
            report["issues"].append(
                issue("error", "non_object_record", "record is not a JSON object", record_index=index, line=line)
            )
            malformed += 1
            continue
        normalized, record_issues = normalize_record(row, index, line)
        if any(item["code"] in {"missing_doc_id", "missing_title"} for item in record_issues):
            malformed += 1
        records.append(normalized)
        report["issues"].extend(record_issues)

        doc_id = normalized.get("doc_id")
        if doc_id:
            if doc_id in seen_doc_ids:
                report["issues"].append(
                    issue(
                        "error",
                        "duplicate_doc_id",
                        f"duplicate doc_id: {doc_id}",
                        record_index=index,
                        line=line,
                        doc_id=doc_id,
                    )
                )
            else:
                seen_doc_ids[doc_id] = index

    package_metadata = copy.deepcopy(file_metadata)
    report["issues"].extend(
        validate_whole_returned_package(raw_rows, package_metadata, scope=normalized_scope)
    )
    current_context, current_issues = load_current_docs_context(repo_root, normalized_scope)
    report["issues"].extend(current_issues)
    source_export_id = normalize_text(package_metadata.get("export_id"))
    source_profile_id = normalize_text(package_metadata.get("profile_id"))
    report["source_export_id"] = source_export_id
    report["source_profile_id"] = source_profile_id
    report["source_scope"] = normalize_text(package_metadata.get("scope"))
    report["generated_at"] = normalize_text(package_metadata.get("generated_at"))
    report["source_metadata"] = package_metadata
    report["unknown_file_metadata"] = unknown_file_metadata
    report["records"] = records
    report["detected_import_type"] = detect_import_type(package_metadata)
    report["current_library"] = current_report_context(current_context)
    report["issues"].extend(add_current_library_report(records, current=current_context, scope=normalized_scope))

    supports_return_import = package_metadata.get("supports_return_import") is not False
    issue_codes = {
        normalize_text(item.get("code"))
        for item in report["issues"]
        if isinstance(item, dict)
    }
    if raw_rows and not supports_return_import:
        if "export_only_profile" not in issue_codes:
            report["issues"].append(
                issue(
                    "error",
                    "export_only_profile",
                    f"profile does not support returned-package import: {source_profile_id or '<missing>'}",
                )
            )
    elif raw_rows and not source_profile_id:
        if "missing_import_metadata" not in issue_codes:
            if source_export_id:
                report["issues"].append(
                    issue(
                        "error",
                        "missing_import_metadata",
                        f"missing import profile metadata for export_id: {source_export_id}",
                    )
                )
            else:
                report["issues"].append(
                    issue(
                        "error",
                        "missing_import_metadata",
                        "missing import profile metadata: profile_id is required",
                    )
                )
    elif raw_rows and report["detected_import_type"] == "unknown":
        report["issues"].append(
            issue(
                "error",
                "unsupported_import_profile",
                f"unsupported import profile: {source_profile_id}",
            )
        )

    error_count = len([item for item in report["issues"] if item["level"] == "error"])
    warning_count = len([item for item in report["issues"] if item["level"] == "warning"])
    report["counts"] = {
        "records": len(raw_rows),
        "parsed_records": len(records),
        "malformed_records": malformed,
        "warnings": warning_count,
        "errors": error_count,
    }
    report["ok"] = error_count == 0
    return report
