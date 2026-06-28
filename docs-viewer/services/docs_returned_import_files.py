#!/usr/bin/env python3
"""Staged returned-package file and metadata parsing."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from docs_returned_import_common import (
    EXPORT_ID_RE,
    EXPORT_METADATA_FIELDS,
    KNOWN_RECORD_FIELDS,
    WORKFLOW_ROOT,
    issue,
    normalize_text,
)

def parse_json_file(path: Path) -> tuple[Any, list[dict[str, Any]]]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except json.JSONDecodeError as exc:
        return None, [issue("error", "invalid_json", f"invalid JSON: {exc.msg}", line=exc.lineno)]


def internal_metadata_path(repo_root: Path, export_id: str) -> Path | None:
    normalized = normalize_text(export_id)
    if not EXPORT_ID_RE.fullmatch(normalized):
        return None
    return repo_root / WORKFLOW_ROOT / "meta" / f"{normalized}.meta.json"


def export_id_from_jsonl_header(path: Path) -> tuple[str, list[dict[str, Any]]]:
    try:
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                return "", [issue("error", "invalid_jsonl", f"invalid JSONL on line {line_number}: {exc.msg}", line=line_number)]
            if not isinstance(row, dict) or row.get("record_type") != "data_sharing_header":
                return "", [
                    issue(
                        "error",
                        "missing_export_id",
                        "first JSONL row must be a data_sharing_header with export_id",
                        line=line_number,
                    )
                ]
            export_id = normalize_text(row.get("export_id"))
            if not export_id:
                return "", [issue("error", "missing_export_id", "JSONL header is missing export_id", line=line_number)]
            if not EXPORT_ID_RE.fullmatch(export_id):
                return "", [issue("error", "invalid_export_id", f"invalid export_id: {export_id}", line=line_number)]
            return export_id, []
    except OSError as exc:
        return "", [issue("error", "unreadable_file", f"unreadable file: {exc}")]
    return "", [issue("error", "missing_export_id", "JSONL file is empty")]


def metadata_from_internal_export_meta(repo_root: Path, export_id: str) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], Path | None]:
    metadata_path = internal_metadata_path(repo_root, export_id)
    if metadata_path is None:
        return {}, {}, [issue("error", "invalid_export_id", f"invalid export_id: {export_id}")], None
    if not metadata_path.exists():
        return {}, {}, [issue("error", "missing_export_metadata", f"metadata file not found for export_id: {export_id}")], metadata_path
    payload, issues = parse_json_file(metadata_path)
    if any(item["level"] == "error" for item in issues):
        return {}, {}, issues, metadata_path
    if not isinstance(payload, dict):
        return {}, {}, [issue("error", "invalid_metadata_file", "internal export metadata file is not a JSON object")], metadata_path
    metadata, unknown = file_metadata_from_envelope(payload)
    metadata_export_id = normalize_text(metadata.get("export_id"))
    if metadata_export_id != export_id:
        return {}, {}, [
            issue(
                "error",
                "metadata_export_id_mismatch",
                f"metadata export_id {metadata_export_id or '<missing>'} does not match {export_id}",
            )
        ], metadata_path
    return metadata, unknown, [], metadata_path


def parse_jsonl_file(path: Path) -> tuple[list[Any], list[dict[str, Any]]]:
    records: list[Any] = []
    issues: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return [], [issue("error", "unreadable_file", f"unreadable file: {exc}")]
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            issues.append(issue("error", "invalid_jsonl", f"invalid JSONL on line {line_number}: {exc.msg}", line=line_number))
            continue
        if isinstance(row, dict):
            if row.get("record_type") == "data_sharing_header":
                continue
            row = dict(row)
            row["_source_line"] = line_number
        records.append(row)
    if any(item["level"] == "error" for item in issues):
        return [], issues
    return records, issues


def is_document_like_record(value: dict[str, Any]) -> bool:
    return any(key in value for key in KNOWN_RECORD_FIELDS)


def file_metadata_from_envelope(payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    metadata = {key: copy.deepcopy(value) for key, value in payload.items() if key in EXPORT_METADATA_FIELDS}
    unknown = {
        key: copy.deepcopy(value)
        for key, value in payload.items()
        if key not in EXPORT_METADATA_FIELDS and key != "records"
    }
    return metadata, unknown


def rows_from_payload(payload: Any) -> tuple[list[Any], dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    issues: list[dict[str, Any]] = []
    if isinstance(payload, list):
        return payload, {}, {}, issues
    if isinstance(payload, dict):
        if isinstance(payload.get("records"), list):
            metadata, unknown = file_metadata_from_envelope(payload)
            return payload["records"], metadata, unknown, issues
        if is_document_like_record(payload):
            return [payload], {}, {}, issues
        issues.append(
            issue(
                "warning",
                "unsupported_import_shape",
                "JSON object does not contain a records array or document-like fields",
            )
        )
        return [], {}, copy.deepcopy(payload), issues
    issues.append(issue("warning", "unsupported_import_shape", "JSON payload is not an object or array"))
    return [], {}, {}, issues


def export_id_from_json_payload(payload: Any) -> tuple[str, list[dict[str, Any]]]:
    if not isinstance(payload, dict):
        return "", [issue("error", "missing_export_id", "JSON staged file must be an object with export_id")]
    export_id = normalize_text(payload.get("export_id"))
    if not export_id:
        return "", [issue("error", "missing_export_id", "JSON staged file is missing export_id")]
    if not EXPORT_ID_RE.fullmatch(export_id):
        return "", [issue("error", "invalid_export_id", f"invalid export_id: {export_id}")]
    return export_id, []
