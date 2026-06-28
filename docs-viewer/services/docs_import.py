#!/usr/bin/env python3
"""Parse staged Docs Viewer import data.

Run:
  ./docs-viewer/services/docs_import.py --scope library --file document-content.jsonl
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any

from docs_scope_config import load_docs_scope_configs
from docs_data_sharing import source_metadata


WORKFLOW_ROOT = Path("var/analytics/data-sharing")
STAGING_DIR_NAME = "import-staging"
SUPPORTED_EXTENSIONS = {".json", ".jsonl"}
TEXT_WHITESPACE_RE = re.compile(r"\s+")
EXPORT_ID_RE = re.compile(r"^ds_\d{8}T\d{6}Z$")

PROFILE_ID_TO_IMPORT_TYPE = {
    "document-content": "document_changes",
}
EXPORT_METADATA_FIELDS = {
    "schema_version",
    "export_id",
    "profile_id",
    "config_id",
    "config_checksum",
    "app",
    "adapter_id",
    "data_domain",
    "scope",
    "target_format",
    "record_shape",
    "generated_at",
    "supports_return_import",
    "selected_doc_ids",
    "source_last_updated",
    "counts",
}
KNOWN_RECORD_FIELDS = {
    "doc_id",
    "title",
    "parent_id",
    "parent_title",
    "ancestors",
    "children",
    "summary",
    "current_summary",
    "headings",
    "source_text",
    "last_updated",
    "viewable",
}


def detect_repo_root(explicit_root: str | None = None) -> Path:
    if explicit_root:
        repo_root = Path(explicit_root).expanduser().resolve()
        if not (repo_root / "site-tools" / "config" / "site-tools.json").exists():
            raise ValueError(f"--repo-root does not look like repo root: {repo_root}")
        return repo_root

    current = Path.cwd().resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "site-tools" / "config" / "site-tools.json").exists():
            return candidate

    script_dir = Path(__file__).resolve().parent
    for candidate in [script_dir, *script_dir.parents]:
        if (candidate / "site-tools" / "config" / "site-tools.json").exists():
            return candidate

    raise ValueError("Could not detect repo root")


def normalize_text(value: Any) -> str:
    return TEXT_WHITESPACE_RE.sub(" ", str(value or "")).strip()


def scope_title(scope: str) -> str:
    normalized = normalize_text(scope).lower()
    labels = {
        "analytics": "Analytics",
        "catalogue": "Catalogue",
        "library": "Library",
    }
    return labels.get(normalized, normalized.title() if normalized else "Docs")


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


def normalize_id_title_pairs(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    normalized: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        doc_id = normalize_text(item.get("id"))
        title = normalize_text(item.get("title"))
        if doc_id or title:
            normalized.append({"id": doc_id, "title": title})
    return normalized


def relative_path(repo_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def default_staging_root(scope: str) -> Path:
    return WORKFLOW_ROOT / normalize_text(scope).lower() / STAGING_DIR_NAME


def supported_scopes(repo_root: Path) -> set[str]:
    return set(load_docs_scope_configs(repo_root).keys())


def validate_scope(repo_root: Path, scope: str) -> str:
    normalized_scope = normalize_text(scope).lower()
    scopes = supported_scopes(repo_root)
    if normalized_scope not in scopes:
        raise ValueError(f"scope must be one of: {', '.join(sorted(scopes))}")
    return normalized_scope


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
        "source_profile_id": "",
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
        "source_metadata_file": "",
        "unknown_file_metadata": {},
    }


def resolve_staged_path(repo_root: Path, scope: str, staged_file: str, staging_root: Path | str | None = None) -> Path:
    normalized_scope = validate_scope(repo_root, scope)
    base_root = Path(staging_root) if staging_root else default_staging_root(normalized_scope)
    raw_path = Path(staged_file)
    path = raw_path if raw_path.is_absolute() else repo_root / base_root / raw_path
    resolved = path.resolve()
    allowed_root = (repo_root / base_root).resolve()
    if resolved != allowed_root and allowed_root not in resolved.parents:
        raise ValueError(f"staged file must stay under {base_root}")
    return resolved


def list_staged_import_files(repo_root: Path, scope: str, staging_root: Path | str | None = None) -> list[dict[str, Any]]:
    normalized_scope = validate_scope(repo_root, scope)
    base_root = Path(staging_root) if staging_root else default_staging_root(normalized_scope)
    resolved_staging_root = (repo_root / base_root).resolve()
    if not resolved_staging_root.exists():
        return []
    files: list[dict[str, Any]] = []
    for path in sorted(resolved_staging_root.iterdir()):
        if path.name.endswith(".meta.json") or path.name.endswith(".context.json"):
            continue
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        stat = path.stat()
        files.append(
            {
                "filename": path.name,
                "path": relative_path(repo_root, path),
                "format": path.suffix.lower().lstrip("."),
                "size_bytes": stat.st_size,
                "modified_utc": dt.datetime.fromtimestamp(stat.st_mtime, tz=dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
        )
    return files


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


def read_json_object(path: Path, label: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object for {label}: {path}")
    return payload


def load_current_docs_context(repo_root: Path, scope: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    issues: list[dict[str, Any]] = []
    context: dict[str, Any] = {
        "source_loaded": False,
        "source_root": "",
        "doc_count": 0,
        "renderable_count": 0,
        "docs_by_id": {},
        "renderable_ids": [],
    }
    try:
        source_context = source_metadata.load_data_sharing_docs_source_context(repo_root, scope)
    except (FileNotFoundError, json.JSONDecodeError, ValueError, RuntimeError, OSError) as exc:
        issues.append(issue("warning", "current_source_unreadable", f"current {scope} docs source metadata could not be read: {exc}"))
        return context, issues

    docs_by_id: dict[str, dict[str, Any]] = {}
    renderable_ids: list[str] = []
    for item in source_context.records:
        doc_id = item.doc_id
        docs_by_id[doc_id] = item
        renderable_ids.append(doc_id)
    context.update(
        {
            "source_loaded": True,
            "source_root": source_context.scope_config.source.as_posix(),
            "doc_count": len(docs_by_id),
            "renderable_count": len(set(renderable_ids)),
            "docs_by_id": docs_by_id,
            "renderable_ids": sorted(set(renderable_ids)),
        }
    )
    return context, issues


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
    for key in ["viewable"]:
        if key in row:
            normalized["metadata"][key] = row.get(key)
    if "headings" in row:
        normalized["metadata"]["headings"] = normalize_string_list(row.get("headings"))
    if "source_text" in row:
        normalized["metadata"]["source_text"] = str(row.get("source_text") or "")

    for key in ["ancestors", "children"]:
        if key in row:
            normalized["relationships"][key] = normalize_id_title_pairs(row.get(key))

    unknown = {
        key: copy.deepcopy(value)
        for key, value in row.items()
        if key not in KNOWN_RECORD_FIELDS and key != "_source_line"
    }
    normalized["unknown_metadata"] = unknown
    return normalized, issues


def detect_import_type(source_metadata: dict[str, Any]) -> str:
    if source_metadata.get("supports_return_import") is False:
        return "export_only"
    profile_id = normalize_text(source_metadata.get("profile_id"))
    if profile_id in PROFILE_ID_TO_IMPORT_TYPE:
        return PROFILE_ID_TO_IMPORT_TYPE[profile_id]
    return "unknown"


def supported_return_import_profile_ids() -> set[str]:
    return set(PROFILE_ID_TO_IMPORT_TYPE)


def current_report_context(current: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_loaded": bool(current.get("source_loaded")),
        "source_root": normalize_text(current.get("source_root")),
        "doc_count": int(current.get("doc_count") or 0),
        "renderable_count": int(current.get("renderable_count") or 0),
    }


def add_current_library_report(
    records: list[dict[str, Any]],
    *,
    current: dict[str, Any],
    scope: str = "library",
) -> list[dict[str, Any]]:
    if not current.get("source_loaded"):
        return []

    issues: list[dict[str, Any]] = []
    docs_by_id = current.get("docs_by_id") if isinstance(current.get("docs_by_id"), dict) else {}
    renderable_ids = set(current.get("renderable_ids") if isinstance(current.get("renderable_ids"), list) else [])

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
        metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}

        current_state: dict[str, Any] = {
            "exists": bool(current_doc),
            "viewable": None,
            "source_exists": bool(current_doc),
            "source_renderable": False,
            "current_summary": "",
            "staged_current_summary_matches": None,
            "parent_exists": None,
            "parent_source_exists": None,
            "parent_source_renderable": None,
        }
        if current_doc:
            current_state["viewable"] = current_doc.viewable
            current_state["source_renderable"] = doc_id in renderable_ids
            current_state["current_summary"] = current_doc.summary
            if "current_summary" in metadata:
                current_state["staged_current_summary_matches"] = str(metadata.get("current_summary") or "") == current_doc.summary
        record["current_library"] = current_state

        if not doc_id:
            continue
        if not current_doc:
            issues.append(
                issue(
                    "warning",
                    "unknown_doc_id",
                    f"record doc_id is not in the current {scope_title(scope)} source metadata: {doc_id}",
                    record_index=record_index,
                    line=line,
                    doc_id=doc_id,
                )
            )
        if current_doc and doc_id not in renderable_ids:
            issues.append(
                issue(
                    "warning",
                    "current_source_unrenderable",
                    f"record exists in the current {scope_title(scope)} source metadata but could not be rendered: {doc_id}",
                    record_index=record_index,
                    line=line,
                    doc_id=doc_id,
                )
            )

        if parent_id:
            parent_doc = docs_by_id.get(parent_id)
            current_state["parent_exists"] = bool(parent_doc)
            current_state["parent_source_exists"] = bool(parent_doc)
            current_state["parent_source_renderable"] = parent_id in renderable_ids
            if parent_id not in docs_by_id and parent_id not in staged_ids:
                issues.append(
                    issue(
                        "warning",
                        "missing_parent_id",
                        f"parent_id is not in the current {scope_title(scope)} source metadata or staged records: {parent_id}",
                        record_index=record_index,
                        line=line,
                        doc_id=doc_id,
                    )
                )
            elif parent_doc and parent_id not in renderable_ids:
                issues.append(
                    issue(
                        "warning",
                        "parent_source_unrenderable",
                        f"parent_id points to a current {scope_title(scope)} source metadata record that could not be rendered: {parent_id}",
                        record_index=record_index,
                        line=line,
                        doc_id=doc_id,
                    )
                )
    return issues


def parse_staged_import(
    *,
    repo_root: Path,
    scope: str,
    staged_file: str,
    staging_root: Path | str | None = None,
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
                issue("warning", "non_object_record", "record is not a JSON object", record_index=index, line=line)
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

    source_metadata = copy.deepcopy(file_metadata)
    current_context, current_issues = load_current_docs_context(repo_root, normalized_scope)
    report["issues"].extend(current_issues)
    source_export_id = normalize_text(source_metadata.get("export_id"))
    source_profile_id = normalize_text(source_metadata.get("profile_id"))
    report["source_export_id"] = source_export_id
    report["source_profile_id"] = source_profile_id
    report["source_scope"] = normalize_text(source_metadata.get("scope"))
    report["generated_at"] = normalize_text(source_metadata.get("generated_at"))
    report["source_metadata"] = source_metadata
    report["unknown_file_metadata"] = unknown_file_metadata
    report["records"] = records
    report["detected_import_type"] = detect_import_type(source_metadata)
    report["current_library"] = current_report_context(current_context)
    report["issues"].extend(add_current_library_report(records, current=current_context, scope=normalized_scope))

    supports_return_import = source_metadata.get("supports_return_import") is not False
    if raw_rows and not supports_return_import:
        report["issues"].append(
            issue(
                "error",
                "export_only_profile",
                f"profile does not support returned-package import: {source_profile_id or '<missing>'}",
            )
        )
    elif raw_rows and not source_profile_id:
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Parse staged Docs Viewer import data.")
    parser.add_argument("--scope", default="library", help="Docs Viewer scope to import")
    parser.add_argument("--file", required=True, help="Staged JSON or JSONL filename under var/analytics/data-sharing/<scope>/import-staging/")
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
