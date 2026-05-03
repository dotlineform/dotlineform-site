#!/usr/bin/env python3
"""Parse staged Docs Viewer import data without writing source or previews.

Run:
  ./scripts/docs/docs_import.py --scope library --file library-document-summaries.jsonl
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any


STAGING_ROOT = Path("var/docs/import-staging")
DOCS_SCOPES_ROOT = Path("assets/data/docs/scopes")
SUPPORTED_SCOPES = {"library"}
SUPPORTED_EXTENSIONS = {".json", ".jsonl"}
TEXT_WHITESPACE_RE = re.compile(r"\s+")

EXPORT_ID_TO_IMPORT_TYPE = {
    "library-parent-child-relationships": "parent_child_relationships",
    "library-document-summaries": "document_summaries",
    "library-full-document-content": "full_document_content",
}
EXPORT_METADATA_FIELDS = {
    "_export",
    "export_id",
    "config_id",
    "config_checksum",
    "scope",
    "generated_at",
    "selected_doc_ids",
    "source_last_updated",
    "counts",
}
KNOWN_RECORD_FIELDS = {
    "_export",
    "doc_id",
    "title",
    "parent_id",
    "parent_title",
    "ancestor_ids",
    "ancestor_titles",
    "child_ids",
    "child_titles",
    "summary",
    "current_summary",
    "headings",
    "source_text",
    "last_updated",
    "viewable",
    "published",
}


def detect_repo_root(explicit_root: str | None = None) -> Path:
    if explicit_root:
        repo_root = Path(explicit_root).expanduser().resolve()
        if not (repo_root / "_config.yml").exists():
            raise ValueError(f"--repo-root does not look like repo root: {repo_root}")
        return repo_root

    current = Path.cwd().resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "_config.yml").exists():
            return candidate

    script_dir = Path(__file__).resolve().parent
    for candidate in [script_dir, *script_dir.parents]:
        if (candidate / "_config.yml").exists():
            return candidate

    raise ValueError("Could not detect repo root")


def normalize_text(value: Any) -> str:
    return TEXT_WHITESPACE_RE.sub(" ", str(value or "")).strip()


def normalize_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    values = value if isinstance(value, list) else [value]
    normalized: list[str] = []
    for item in values:
        text = normalize_text(item)
        if text:
            normalized.append(text)
    return normalized


def relative_path(repo_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def issue(
    level: str,
    code: str,
    message: str,
    *,
    record_index: int | None = None,
    line: int | None = None,
    doc_id: str = "",
) -> dict[str, Any]:
    item: dict[str, Any] = {"level": level, "code": code, "message": message}
    if record_index is not None:
        item["record_index"] = record_index
    if line is not None:
        item["line"] = line
    if doc_id:
        item["doc_id"] = doc_id
    return item


def empty_report(repo_root: Path, scope: str, staged_file: str) -> dict[str, Any]:
    return {
        "ok": False,
        "scope": scope,
        "input_file": staged_file,
        "input_format": "",
        "detected_import_type": "unknown",
        "source_export_id": "",
        "source_scope": "",
        "generated_at": "",
        "counts": {
            "records": 0,
            "parsed_records": 0,
            "malformed_records": 0,
            "warnings": 0,
            "errors": 0,
        },
        "issues": [],
        "records": [],
        "source_metadata": {},
        "unknown_file_metadata": {},
    }


def resolve_staged_path(repo_root: Path, scope: str, staged_file: str) -> Path:
    normalized_scope = normalize_text(scope).lower()
    if normalized_scope not in SUPPORTED_SCOPES:
        raise ValueError(f"scope must be one of: {', '.join(sorted(SUPPORTED_SCOPES))}")
    raw_path = Path(staged_file)
    path = raw_path if raw_path.is_absolute() else repo_root / STAGING_ROOT / normalized_scope / raw_path
    resolved = path.resolve()
    allowed_root = (repo_root / STAGING_ROOT / normalized_scope).resolve()
    if resolved != allowed_root and allowed_root not in resolved.parents:
        raise ValueError(f"staged file must stay under {STAGING_ROOT / normalized_scope}")
    return resolved


def parse_json_file(path: Path) -> tuple[Any, list[dict[str, Any]]]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except json.JSONDecodeError as exc:
        return None, [issue("error", "invalid_json", f"invalid JSON: {exc.msg}", line=exc.lineno)]


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
            row = dict(row)
            row["_source_line"] = line_number
        records.append(row)
    if any(item["level"] == "error" for item in issues):
        return [], issues
    return records, issues


def is_document_like_record(value: dict[str, Any]) -> bool:
    return any(key in value for key in KNOWN_RECORD_FIELDS - {"_export"})


def file_metadata_from_envelope(payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    metadata = {key: copy.deepcopy(value) for key, value in payload.items() if key in EXPORT_METADATA_FIELDS}
    unknown = {
        key: copy.deepcopy(value)
        for key, value in payload.items()
        if key not in EXPORT_METADATA_FIELDS and key != "documents"
    }
    return metadata, unknown


def rows_from_payload(payload: Any) -> tuple[list[Any], dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    issues: list[dict[str, Any]] = []
    if isinstance(payload, list):
        return payload, {}, {}, issues
    if isinstance(payload, dict):
        if isinstance(payload.get("documents"), list):
            metadata, unknown = file_metadata_from_envelope(payload)
            return payload["documents"], metadata, unknown, issues
        if is_document_like_record(payload):
            return [payload], {}, {}, issues
        metadata, unknown = file_metadata_from_envelope(payload)
        issues.append(
            issue(
                "warning",
                "unsupported_import_shape",
                "JSON object does not contain a documents array or document-like fields",
            )
        )
        return [], metadata, unknown, issues
    issues.append(issue("warning", "unsupported_import_shape", "JSON payload is not an object or array"))
    return [], {}, {}, issues


def read_json_object(path: Path, label: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object for {label}: {path}")
    return payload


def load_current_docs_context(repo_root: Path, scope: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    issues: list[dict[str, Any]] = []
    index_path = repo_root / DOCS_SCOPES_ROOT / scope / "index.json"
    context: dict[str, Any] = {
        "index_loaded": False,
        "index_path": relative_path(repo_root, index_path),
        "doc_count": 0,
        "payload_count": 0,
        "docs_by_id": {},
        "payload_ids": [],
    }
    try:
        payload = read_json_object(index_path, f"{scope} docs index")
    except FileNotFoundError:
        issues.append(issue("warning", "current_index_missing", f"current {scope} docs index is missing"))
        return context, issues
    except (json.JSONDecodeError, ValueError, OSError) as exc:
        issues.append(issue("warning", "current_index_unreadable", f"current {scope} docs index could not be read: {exc}"))
        return context, issues

    docs = payload.get("docs")
    if not isinstance(docs, list):
        issues.append(issue("warning", "current_index_invalid", f"current {scope} docs index has no docs array"))
        return context, issues

    docs_by_id: dict[str, dict[str, Any]] = {}
    for item in docs:
        if not isinstance(item, dict):
            continue
        doc_id = normalize_text(item.get("doc_id"))
        if not doc_id:
            continue
        if doc_id in docs_by_id:
            issues.append(issue("warning", "current_duplicate_doc_id", f"current Library index has duplicate doc_id: {doc_id}", doc_id=doc_id))
            continue
        docs_by_id[doc_id] = item

    payload_root = repo_root / DOCS_SCOPES_ROOT / scope / "by-id"
    payload_ids = sorted(path.stem for path in payload_root.glob("*.json")) if payload_root.exists() else []
    context.update(
        {
            "index_loaded": True,
            "doc_count": len(docs_by_id),
            "payload_count": len(payload_ids),
            "docs_by_id": docs_by_id,
            "payload_ids": payload_ids,
        }
    )
    return context, issues


def row_export_metadata(row: dict[str, Any]) -> dict[str, Any]:
    metadata = row.get("_export")
    return copy.deepcopy(metadata) if isinstance(metadata, dict) else {}


def normalize_record(row: dict[str, Any], record_index: int, line: int | None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    doc_id = normalize_text(row.get("doc_id"))
    title = normalize_text(row.get("title"))
    issues: list[dict[str, Any]] = []
    if not doc_id:
        issues.append(issue("warning", "missing_doc_id", "record is missing doc_id", record_index=record_index, line=line))
    if not title:
        issues.append(issue("warning", "missing_title", "record is missing title", record_index=record_index, line=line, doc_id=doc_id))

    normalized: dict[str, Any] = {
        "record_index": record_index,
        "doc_id": doc_id,
        "title": title,
        "parent_id": normalize_text(row.get("parent_id")),
        "metadata": {},
        "relationships": {},
        "unknown_metadata": {},
    }
    if line is not None:
        normalized["line"] = line

    for key in ["parent_title", "last_updated"]:
        if key in row:
            normalized["metadata"][key] = normalize_text(row.get(key))
    for key in ["summary", "current_summary"]:
        if key in row:
            normalized["metadata"][key] = str(row.get(key) or "")
    for key in ["viewable", "published"]:
        if key in row:
            normalized["metadata"][key] = row.get(key)
    if "headings" in row:
        normalized["metadata"]["headings"] = normalize_string_list(row.get("headings"))
    if "source_text" in row:
        normalized["metadata"]["source_text"] = str(row.get("source_text") or "")

    for key in ["ancestor_ids", "ancestor_titles", "child_ids", "child_titles"]:
        if key in row:
            normalized["relationships"][key] = normalize_string_list(row.get(key))

    unknown = {
        key: copy.deepcopy(value)
        for key, value in row.items()
        if key not in KNOWN_RECORD_FIELDS and key != "_source_line"
    }
    normalized["unknown_metadata"] = unknown
    return normalized, issues


def detect_import_type(source_export_id: str, records: list[dict[str, Any]]) -> str:
    if source_export_id in EXPORT_ID_TO_IMPORT_TYPE:
        return EXPORT_ID_TO_IMPORT_TYPE[source_export_id]
    if any(record.get("relationships") for record in records):
        return "parent_child_relationships"
    if any("source_text" in record.get("metadata", {}) for record in records):
        return "full_document_content"
    if any(
        "current_summary" in record.get("metadata", {}) or "summary" in record.get("metadata", {})
        for record in records
    ):
        return "document_summaries"
    if records:
        return "minimal_document_records"
    return "unknown"


def merge_source_metadata(file_metadata: dict[str, Any], row_metadata: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    issues: list[dict[str, Any]] = []
    metadata = copy.deepcopy(file_metadata)
    for row in row_metadata:
        for key, value in row.items():
            if key not in metadata:
                metadata[key] = copy.deepcopy(value)
            elif metadata[key] != value:
                issues.append(issue("warning", "inconsistent_export_metadata", f"inconsistent export metadata field: {key}"))
    return metadata, issues


def current_report_context(current: dict[str, Any]) -> dict[str, Any]:
    return {
        "index_loaded": bool(current.get("index_loaded")),
        "index_path": normalize_text(current.get("index_path")),
        "doc_count": int(current.get("doc_count") or 0),
        "payload_count": int(current.get("payload_count") or 0),
    }


def add_current_library_report(
    records: list[dict[str, Any]],
    *,
    current: dict[str, Any],
) -> list[dict[str, Any]]:
    if not current.get("index_loaded"):
        return []

    issues: list[dict[str, Any]] = []
    docs_by_id = current.get("docs_by_id") if isinstance(current.get("docs_by_id"), dict) else {}
    payload_ids = set(current.get("payload_ids") if isinstance(current.get("payload_ids"), list) else [])

    staged_ids = {
        normalize_text(record.get("doc_id"))
        for record in records
        if normalize_text(record.get("doc_id"))
    }
    for record in records:
        record_index = record.get("record_index") if isinstance(record.get("record_index"), int) else None
        line = record.get("line") if isinstance(record.get("line"), int) else None
        doc_id = normalize_text(record.get("doc_id"))
        parent_id = normalize_text(record.get("parent_id"))
        current_doc = docs_by_id.get(doc_id)

        current_state: dict[str, Any] = {
            "exists": bool(current_doc),
            "published": None,
            "viewable": None,
            "payload_exists": False,
            "parent_exists": None,
            "parent_payload_exists": None,
        }
        if current_doc:
            current_state["published"] = current_doc.get("published")
            current_state["viewable"] = current_doc.get("viewable")
            current_state["payload_exists"] = doc_id in payload_ids
        record["current_library"] = current_state

        if not doc_id:
            continue
        if not current_doc:
            issues.append(
                issue(
                    "warning",
                    "unknown_doc_id",
                    f"record doc_id is not in the current Library index: {doc_id}",
                    record_index=record_index,
                    line=line,
                    doc_id=doc_id,
                )
            )
        elif current_doc.get("published") is False:
            issues.append(
                issue(
                    "warning",
                    "current_doc_unpublished",
                    f"record exists in the current Library index but is unpublished: {doc_id}",
                    record_index=record_index,
                    line=line,
                    doc_id=doc_id,
                )
            )
        if current_doc and doc_id not in payload_ids:
            issues.append(
                issue(
                    "warning",
                    "current_payload_missing",
                    f"record exists in the current Library index but has no generated payload: {doc_id}",
                    record_index=record_index,
                    line=line,
                    doc_id=doc_id,
                )
            )

        if parent_id:
            parent_doc = docs_by_id.get(parent_id)
            current_state["parent_exists"] = bool(parent_doc)
            current_state["parent_payload_exists"] = parent_id in payload_ids
            if parent_id not in docs_by_id and parent_id not in staged_ids:
                issues.append(
                    issue(
                        "warning",
                        "missing_parent_id",
                        f"parent_id is not in the current Library index or staged records: {parent_id}",
                        record_index=record_index,
                        line=line,
                        doc_id=doc_id,
                    )
                )
            elif parent_doc and parent_doc.get("published") is False:
                issues.append(
                    issue(
                        "warning",
                        "parent_unpublished",
                        f"parent_id points to an unpublished current Library record: {parent_id}",
                        record_index=record_index,
                        line=line,
                        doc_id=doc_id,
                    )
                )
            elif parent_doc and parent_id not in payload_ids:
                issues.append(
                    issue(
                        "warning",
                        "parent_payload_missing",
                        f"parent_id points to a current Library record with no generated payload: {parent_id}",
                        record_index=record_index,
                        line=line,
                        doc_id=doc_id,
                    )
                )
    return issues


def parse_staged_import(*, repo_root: Path, scope: str, staged_file: str) -> dict[str, Any]:
    normalized_scope = normalize_text(scope).lower()
    report = empty_report(repo_root, normalized_scope, staged_file)
    try:
        path = resolve_staged_path(repo_root, normalized_scope, staged_file)
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
        if extension == ".jsonl":
            raw_rows, parse_issues = parse_jsonl_file(path)
            file_metadata: dict[str, Any] = {}
            unknown_file_metadata: dict[str, Any] = {}
        else:
            payload, parse_issues = parse_json_file(path)
            if any(item["level"] == "error" for item in parse_issues):
                raw_rows = []
                file_metadata = {}
                unknown_file_metadata = {}
            else:
                raw_rows, file_metadata, unknown_file_metadata, shape_issues = rows_from_payload(payload)
                parse_issues.extend(shape_issues)
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
    row_metadata: list[dict[str, Any]] = []
    malformed = 0
    seen_doc_ids: dict[str, int] = {}
    for index, row in enumerate(raw_rows):
        line = row.get("_source_line") if isinstance(row, dict) and isinstance(row.get("_source_line"), int) else None
        if not isinstance(row, dict):
            report["issues"].append(
                issue("warning", "non_object_record", "record is not a JSON object", record_index=index, line=line)
            )
            malformed += 1
            continue
        row_metadata.append(row_export_metadata(row))
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
                        "warning",
                        "duplicate_doc_id",
                        f"duplicate doc_id: {doc_id}",
                        record_index=index,
                        line=line,
                        doc_id=doc_id,
                    )
                )
            else:
                seen_doc_ids[doc_id] = index

    source_metadata, metadata_issues = merge_source_metadata(file_metadata, [item for item in row_metadata if item])
    report["issues"].extend(metadata_issues)
    current_context, current_issues = load_current_docs_context(repo_root, normalized_scope)
    report["issues"].extend(current_issues)
    source_export_id = normalize_text(source_metadata.get("export_id") or source_metadata.get("config_id"))
    report["source_export_id"] = source_export_id
    report["source_scope"] = normalize_text(source_metadata.get("scope"))
    report["generated_at"] = normalize_text(source_metadata.get("generated_at"))
    report["source_metadata"] = source_metadata
    report["unknown_file_metadata"] = unknown_file_metadata
    report["records"] = records
    report["detected_import_type"] = detect_import_type(source_export_id, records)
    report["current_library"] = current_report_context(current_context)
    report["issues"].extend(add_current_library_report(records, current=current_context))

    if report["detected_import_type"] == "unknown" and raw_rows:
        report["issues"].append(issue("warning", "unsupported_import_shape", "could not detect import type"))

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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Parse staged Docs Viewer import data without writing output files.")
    parser.add_argument("--scope", default="library", help="Docs Viewer scope to import")
    parser.add_argument("--file", required=True, help="Staged JSON or JSONL filename under var/docs/import-staging/<scope>/")
    parser.add_argument("--repo-root", default="", help="Override repo root")
    parser.add_argument("--no-records", action="store_true", help="Omit normalized records from the printed report")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        repo_root = detect_repo_root(args.repo_root or None)
        report = parse_staged_import(
            repo_root=repo_root,
            scope=args.scope,
            staged_file=args.file,
        )
    except Exception as exc:
        print(f"docs_import: {exc}", file=sys.stderr)
        return 1

    if args.no_records:
        report = dict(report)
        report["records"] = []
    print(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return 0 if report.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
