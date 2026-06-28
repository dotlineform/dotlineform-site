#!/usr/bin/env python3
"""Docs Data Sharing returned-package review helpers."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
import re
from typing import Any, Dict

from docs_returned_import_common import scope_title
from docs_returned_import_parser import parse_staged_import
import docs_source_model as source_model


FILENAME_RE = re.compile(r"[^a-z0-9-]+")


def normalize_text(value: Any) -> str:
    return str(value or "").strip()


def filename_slug(value: Any, fallback: str) -> str:
    slug = FILENAME_RE.sub("-", normalize_text(value).lower()).strip("-")
    return slug or fallback


def local_filename_timestamp(value: dt.datetime | None = None) -> str:
    timestamp = value or dt.datetime.now().astimezone()
    return timestamp.astimezone().strftime("%Y%m%d-%H%M%S")


def source_filename_timestamp(report: Dict[str, Any]) -> str:
    generated_at = normalize_text(report.get("generated_at"))
    try:
        timestamp = dt.datetime.strptime(generated_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
    except ValueError as exc:
        raise ValueError(f"package metadata generated_at must be UTC YYYY-MM-DDTHH:MM:SSZ: {generated_at}") from exc
    return local_filename_timestamp(timestamp)


def yaml_scalar(value: Any) -> str:
    return json.dumps("" if value is None else str(value), ensure_ascii=False)


def markdown_table_cell(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().replace("|", "\\|")


def record_summary(record: Dict[str, Any]) -> str:
    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    return str(metadata.get("summary") or "")


def selected_record_indices(value: Any) -> list[int]:
    if not isinstance(value, list):
        raise ValueError("record_indices must be a list")
    selected: list[int] = []
    seen: set[int] = set()
    for item in value:
        if isinstance(item, bool):
            raise ValueError("record_indices must contain integers")
        try:
            index = int(item)
        except (TypeError, ValueError) as exc:
            raise ValueError("record_indices must contain integers") from exc
        if index < 0:
            raise ValueError("record_indices must contain zero or positive integers")
        if index not in seen:
            selected.append(index)
            seen.add(index)
    if not selected:
        raise ValueError("record_indices must include at least one selected record")
    return selected


def record_issue_map(report: Dict[str, Any]) -> dict[int, list[Dict[str, Any]]]:
    issues_by_record: dict[int, list[Dict[str, Any]]] = {}
    for issue in report.get("issues", []):
        if not isinstance(issue, dict) or not isinstance(issue.get("record_index"), int):
            continue
        issues_by_record.setdefault(int(issue["record_index"]), []).append(issue)
    return issues_by_record


def duplicate_doc_ids(records: list[Dict[str, Any]]) -> set[str]:
    counts: dict[str, int] = {}
    for record in records:
        doc_id = normalize_text(record.get("doc_id"))
        if doc_id:
            counts[doc_id] = counts.get(doc_id, 0) + 1
    return {doc_id for doc_id, count in counts.items() if count > 1}


def document_record_depth(record: Dict[str, Any], by_doc_id: dict[str, Dict[str, Any]], active_doc_ids: set[str] | None = None) -> int:
    doc_id = normalize_text(record.get("doc_id"))
    parent_id = normalize_text(record.get("parent_id"))
    if not doc_id or not parent_id or parent_id == doc_id:
        return 0
    active = set(active_doc_ids or set())
    if doc_id in active:
        return 0
    parent = by_doc_id.get(parent_id)
    if parent is None:
        return 0
    active.add(doc_id)
    return document_record_depth(parent, by_doc_id, active) + 1


def review_row_meta(scope: str, record: Dict[str, Any], duplicates: set[str]) -> str:
    doc_id = normalize_text(record.get("doc_id"))
    current_library = record.get("current_library") if isinstance(record.get("current_library"), dict) else {}
    parts = [doc_id or "missing doc_id"]
    if doc_id in duplicates:
        parts.append("duplicate doc_id")
    if current_library.get("exists") is False:
        parts.append(f"not in current {scope_title(scope)}")
    return " · ".join(parts)


def build_review_rows(report: Dict[str, Any], scope: str) -> list[Dict[str, Any]]:
    records = [record for record in report.get("records", []) if isinstance(record, dict)]
    issues_by_record = record_issue_map(report)
    duplicates = duplicate_doc_ids(records)
    rows: list[Dict[str, Any]] = []
    by_doc_id = {
        normalize_text(record.get("doc_id")): record
        for record in records
        if normalize_text(record.get("doc_id"))
    }
    for record in records:
        record_index = int(record.get("record_index")) if isinstance(record.get("record_index"), int) else len(rows)
        doc_id = normalize_text(record.get("doc_id"))
        rows.append(
            {
                "id": f"{doc_id or 'missing-doc-id'}-record-{record_index + 1}",
                "type": "document",
                "title": normalize_text(record.get("title")) or "missing title",
                "meta": review_row_meta(scope, record, duplicates),
                "record_index": record_index,
                "selectable": True,
                "record_groups": {"documents": [doc_id]} if doc_id else {},
                "issues": issues_by_record.get(record_index, []),
                "depth": document_record_depth(record, by_doc_id),
            }
        )
    return rows


def parse_returned_document_records(
    repo_root: Path,
    *,
    scope: str,
    staged_filename: str,
    staging_root: Path,
) -> Dict[str, Any]:
    normalized_scope = source_model.normalize_scope(scope)
    if not staged_filename:
        raise ValueError("staged_filename is required")

    report = parse_staged_import(
        repo_root=repo_root,
        scope=normalized_scope,
        staged_file=staged_filename,
        staging_root=staging_root,
    )
    report["review_rows"] = build_review_rows(report, normalized_scope)
    return report


def selected_records(report: Dict[str, Any], record_indices: list[int]) -> list[Dict[str, Any]]:
    records_by_index = {
        int(record.get("record_index")): record
        for record in report.get("records", [])
        if isinstance(record, dict) and isinstance(record.get("record_index"), int)
    }
    selected: list[Dict[str, Any]] = []
    for record_index in record_indices:
        record = records_by_index.get(record_index)
        if record is None:
            raise ValueError(f"selected record is not present in staged file: {record_index}")
        selected.append(record)
    return selected


def review_markdown(
    *,
    source_file: str,
    profile_id: str,
    scope: str,
    records: list[Dict[str, Any]],
) -> str:
    lines = [
        "---",
        f"source_file: {yaml_scalar(source_file)}",
        f"profile_id: {yaml_scalar(profile_id)}",
        f"scope: {yaml_scalar(scope)}",
        "---",
        "",
        "| doc_id | title | summary | parent_id |",
        "| --- | --- | --- | --- |",
    ]
    for record in records:
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_table_cell(record.get("doc_id")),
                    markdown_table_cell(record.get("title")),
                    markdown_table_cell(record_summary(record)),
                    markdown_table_cell(record.get("parent_id")),
                ]
            )
            + " |"
        )
    return "\n".join(lines).rstrip() + "\n"


def resolve_review_output_path(
    repo_root: Path,
    *,
    preview_root: Path,
    timestamp: str,
    data_domain: str,
    profile_id: str,
) -> Path:
    filename = (
        f"{filename_slug(timestamp, 'review')}-"
        f"{filename_slug(data_domain, 'data')}-"
        f"{filename_slug(profile_id, 'profile')}.md"
    )
    root = (repo_root / preview_root).resolve()
    path = (root / filename).resolve()
    if path != root and root not in path.parents:
        raise ValueError("review output path must stay under preview root")
    return path


def review_returned_document_package(
    repo_root: Path,
    *,
    scope: str,
    staged_filename: str,
    dry_run: bool,
    staging_root: Path,
    preview_root: Path,
    data_domain: str,
    record_indices: Any,
) -> Dict[str, Any]:
    normalized_scope = source_model.normalize_scope(scope)
    selected_indices = selected_record_indices(record_indices)
    report = parse_returned_document_records(
        repo_root=repo_root,
        scope=normalized_scope,
        staged_filename=staged_filename,
        staging_root=staging_root,
    )
    report["selected_record_indices"] = selected_indices
    if not report.get("ok"):
        report["selected_records"] = []
        report["review_file"] = ""
        report["review_written"] = False
        return report

    records = selected_records(report, selected_indices)
    profile_id = normalize_text(report.get("source_profile_id"))
    source_scope = normalize_text(report.get("source_scope")) or normalized_scope
    timestamp = source_filename_timestamp(report)
    output_path = resolve_review_output_path(
        repo_root,
        preview_root=preview_root,
        timestamp=timestamp,
        data_domain=data_domain,
        profile_id=profile_id,
    )
    content = review_markdown(
        source_file=normalize_text(report.get("input_file")),
        profile_id=profile_id,
        scope=source_scope,
        records=records,
    )
    if not dry_run and report.get("ok"):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
    report["selected_records"] = [
        {"record_index": index, "doc_id": normalize_text(record.get("doc_id"))}
        for index, record in zip(selected_indices, records)
    ]
    report["review_file"] = output_path.resolve().relative_to(repo_root.resolve()).as_posix()
    report["review_written"] = bool(not dry_run and report.get("ok"))
    return report
