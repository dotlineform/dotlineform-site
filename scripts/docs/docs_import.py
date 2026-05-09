#!/usr/bin/env python3
"""Parse staged Docs Viewer import data and optionally write Markdown previews.

Run:
  ./scripts/docs/docs_import.py --scope library --file library-document-summaries.jsonl
  ./scripts/docs/docs_import.py --scope library --file library-document-summaries.jsonl --write-previews
  ./scripts/docs/docs_import.py --scope catalogue --file works.jsonl --write-previews
"""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Any


WORKFLOW_ROOT = Path("var/studio/export-import")
STAGING_DIR_NAME = "import-staging"
PREVIEW_DIR_NAME = "import-preview"
DOCS_SCOPES_ROOT = Path("assets/data/docs/scopes")
SUPPORTED_SCOPES = {"analytics", "catalogue", "library"}
SUPPORTED_EXTENSIONS = {".json", ".jsonl"}
TEXT_WHITESPACE_RE = re.compile(r"\s+")
FILENAME_RE = re.compile(r"[^a-z0-9-]+")
STAGED_TIMESTAMP_RE = re.compile(r"^(?P<base>.+?)[-_](?P<timestamp>\d{8}-\d{6})$")

EXPORT_ID_TO_IMPORT_TYPE = {
    "library-parent-child-relationships": "parent_child_relationships",
    "library-document-summaries": "document_summaries",
    "library-full-document-content": "full_document_content",
}
IMPORT_TYPE_CONFIG_FIELDS = {
    "parent_child_relationships": [
        "doc_id",
        "title",
        "parent_id",
        "parent_title",
        "ancestor_ids",
        "ancestor_titles",
        "child_ids",
        "child_titles",
        "summary",
        "headings",
        "last_updated",
        "hidden",
        "viewable",
    ],
    "document_summaries": [
        "doc_id",
        "title",
        "parent_id",
        "headings",
        "current_summary",
        "last_updated",
        "hidden",
        "viewable",
    ],
    "full_document_content": [
        "doc_id",
        "title",
        "parent_id",
        "summary",
        "headings",
        "source_text",
        "last_updated",
        "hidden",
        "viewable",
    ],
    "minimal_document_records": [
        "doc_id",
        "title",
        "parent_id",
    ],
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
    "hidden",
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


def scope_title(scope: str) -> str:
    normalized = normalize_text(scope).lower()
    labels = {
        "analytics": "Analytics",
        "catalogue": "Catalogue",
        "library": "Library",
    }
    return labels.get(normalized, normalized.title() if normalized else "Docs")


def doc_payload_path(repo_root: Path, scope: str, doc: dict[str, Any]) -> Path:
    content_url = normalize_text(doc.get("content_url"))
    expected_prefix = f"/{DOCS_SCOPES_ROOT.as_posix()}/{scope}/by-id/"
    if content_url.startswith(expected_prefix) and content_url.endswith(".json"):
        relative_path = content_url.removeprefix("/")
        path = repo_root / relative_path
        if ".." not in Path(relative_path).parts:
            return path
    doc_id = normalize_text(doc.get("doc_id"))
    return repo_root / DOCS_SCOPES_ROOT / scope / "by-id" / f"{doc_id}.json"


def preview_generated_at(generated_at_dt: dt.datetime | None = None) -> str:
    value = generated_at_dt or dt.datetime.now(dt.timezone.utc)
    if value.tzinfo is None:
        value = value.replace(tzinfo=dt.timezone.utc)
    return value.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def preview_filename_timestamp(generated_at: str) -> str:
    match = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})Z", normalize_text(generated_at))
    if match:
        year, month, day, hour, minute, second = match.groups()
        return f"{year}{month}{day}-{hour}{minute}{second}"
    return slugify_filename(generated_at, "preview")


def local_filename_timestamp(value: dt.datetime | None = None) -> str:
    timestamp = value or dt.datetime.now().astimezone()
    if timestamp.tzinfo is None:
        timestamp = timestamp.astimezone()
    return timestamp.strftime("%Y%m%d-%H%M%S")


def staged_timestamp_suffix(report: dict[str, Any], fallback_timestamp: str) -> str:
    stem = Path(normalize_text(report.get("input_file"))).stem
    match = STAGED_TIMESTAMP_RE.fullmatch(stem)
    if match:
        return match.group("timestamp")
    return fallback_timestamp


def staged_stem_without_timestamp(report: dict[str, Any], fallback: str) -> str:
    stem = Path(normalize_text(report.get("input_file")) or fallback).stem
    match = STAGED_TIMESTAMP_RE.fullmatch(stem)
    if match:
        stem = match.group("base")
    return slugify_filename(stem, fallback)


def slugify_filename(value: Any, fallback: str) -> str:
    slug = FILENAME_RE.sub("-", normalize_text(value).lower()).strip("-")
    return slug or fallback


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


def default_staging_root(scope: str) -> Path:
    return WORKFLOW_ROOT / normalize_text(scope).lower() / STAGING_DIR_NAME


def default_preview_root(scope: str) -> Path:
    return WORKFLOW_ROOT / normalize_text(scope).lower() / PREVIEW_DIR_NAME


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


def resolve_staged_path(repo_root: Path, scope: str, staged_file: str, staging_root: Path | str | None = None) -> Path:
    normalized_scope = normalize_text(scope).lower()
    if normalized_scope not in SUPPORTED_SCOPES:
        raise ValueError(f"scope must be one of: {', '.join(sorted(SUPPORTED_SCOPES))}")
    base_root = Path(staging_root) if staging_root else default_staging_root(normalized_scope)
    raw_path = Path(staged_file)
    path = raw_path if raw_path.is_absolute() else repo_root / base_root / raw_path
    resolved = path.resolve()
    allowed_root = (repo_root / base_root).resolve()
    if resolved != allowed_root and allowed_root not in resolved.parents:
        raise ValueError(f"staged file must stay under {base_root}")
    return resolved


def list_staged_import_files(repo_root: Path, scope: str, staging_root: Path | str | None = None) -> list[dict[str, Any]]:
    normalized_scope = normalize_text(scope).lower()
    if normalized_scope not in SUPPORTED_SCOPES:
        raise ValueError(f"scope must be one of: {', '.join(sorted(SUPPORTED_SCOPES))}")
    base_root = Path(staging_root) if staging_root else default_staging_root(normalized_scope)
    resolved_staging_root = (repo_root / base_root).resolve()
    if not resolved_staging_root.exists():
        return []
    files: list[dict[str, Any]] = []
    for path in sorted(resolved_staging_root.iterdir()):
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


def resolve_preview_path(repo_root: Path, scope: str, filename: str, preview_root: Path | str | None = None) -> Path:
    normalized_scope = normalize_text(scope).lower()
    if normalized_scope not in SUPPORTED_SCOPES:
        raise ValueError(f"scope must be one of: {', '.join(sorted(SUPPORTED_SCOPES))}")
    relative = Path(filename)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"unsafe preview filename: {filename}")
    base_root = Path(preview_root) if preview_root else default_preview_root(normalized_scope)
    path = (repo_root / base_root / relative).resolve()
    allowed_root = (repo_root / base_root).resolve()
    if path != allowed_root and allowed_root not in path.parents:
        raise ValueError(f"preview file must stay under {base_root}")
    return path


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

    payload_ids = sorted(
        doc_id
        for doc_id, doc in docs_by_id.items()
        if doc_payload_path(repo_root, scope, doc).exists()
    )
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
    for key in ["hidden", "viewable", "published"]:
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
    scope: str = "library",
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
            "hidden": None,
            "viewable": None,
            "payload_exists": False,
            "parent_exists": None,
            "parent_payload_exists": None,
        }
        if current_doc:
            current_state["published"] = current_doc.get("published")
            current_state["hidden"] = current_doc.get("hidden")
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
                    f"record doc_id is not in the current {scope_title(scope)} index: {doc_id}",
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
                    f"record exists in the current {scope_title(scope)} index but is unpublished: {doc_id}",
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
                        f"parent_id is not in the current {scope_title(scope)} index or staged records: {parent_id}",
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


def issue_applies_to_record(item: dict[str, Any], record: dict[str, Any]) -> bool:
    record_index = record.get("record_index")
    doc_id = normalize_text(record.get("doc_id"))
    if "record_index" in item:
        return item.get("record_index") == record_index
    if item.get("doc_id"):
        return normalize_text(item.get("doc_id")) == doc_id
    return False


def issues_for_record(report: dict[str, Any], record: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item
        for item in report.get("issues", [])
        if isinstance(item, dict) and issue_applies_to_record(item, record)
    ]


def yaml_scalar(value: Any) -> str:
    return json.dumps("" if value is None else str(value), ensure_ascii=False)


def front_matter(values: dict[str, Any]) -> str:
    lines = ["---"]
    for key, value in values.items():
        lines.append(f"{key}: {yaml_scalar(value)}")
    lines.append("---")
    return "\n".join(lines)


def markdown_escape_inline(value: Any) -> str:
    return str(value or "").replace("|", "\\|").strip()


def normalize_markdown_body(value: Any) -> str:
    lines = [line.rstrip() for line in str(value or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    trimmed_start = 0
    trimmed_end = len(lines)
    while trimmed_start < trimmed_end and not lines[trimmed_start].strip():
        trimmed_start += 1
    while trimmed_end > trimmed_start and not lines[trimmed_end - 1].strip():
        trimmed_end -= 1
    return "\n".join(lines[trimmed_start:trimmed_end]).strip()


def render_issue_list(items: list[dict[str, Any]]) -> list[str]:
    if not items:
        return []
    lines = ["## Import Warnings", ""]
    for item in items:
        code = normalize_text(item.get("code")) or "warning"
        message = normalize_text(item.get("message"))
        lines.append(f"- `{code}`: {message}")
    lines.append("")
    return lines


def record_preview_filename(record: dict[str, Any], seen: dict[str, int], timestamp_suffix: str) -> str:
    record_index = int(record.get("record_index") or 0)
    doc_id = normalize_text(record.get("doc_id"))
    base = slugify_filename(doc_id, f"record-{record_index + 1}")
    count = seen.get(base, 0)
    seen[base] = count + 1
    if count:
        return f"{base}-record-{record_index + 1}-{timestamp_suffix}.md"
    return f"{base}-{timestamp_suffix}.md"


def relationship_preview_filename(report: dict[str, Any], timestamp_suffix: str) -> str:
    base = staged_stem_without_timestamp(report, "relationships")
    return f"{base}-tree-{timestamp_suffix}.md"


def render_doc_front_matter(record: dict[str, Any], report: dict[str, Any], generated_at: str) -> str:
    import_type = normalize_text(report.get("detected_import_type"))
    return render_preview_metadata_sections(
        record=record,
        import_type=import_type,
        generated_at=generated_at,
        source_file=normalize_text(report.get("input_file")),
    )


def record_field_value(record: dict[str, Any], field: str) -> Any:
    if field in {"doc_id", "title", "parent_id"}:
        return normalize_text(record.get(field))
    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    relationships = record.get("relationships") if isinstance(record.get("relationships"), dict) else {}
    if field in metadata:
        return metadata.get(field)
    if field in relationships:
        return relationships.get(field)
    return ""


def preview_scalar(value: Any, *, field: str = "") -> str:
    if field == "source_text" and normalize_text(value):
        return '"[see Imported Source Text section]"'
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    text = str(value or "")
    if "\n" in text or len(text) > 160:
        text = normalize_text(text)
        if len(text) > 160:
            text = text[:157].rstrip() + "..."
    return yaml_scalar(text)


def metadata_section(title: str, rows: list[tuple[str, Any]]) -> list[str]:
    lines = ["---", title]
    if rows:
        for key, value in rows:
            lines.append(f"{key}: {preview_scalar(value, field=key)}")
    else:
        lines.append("none")
    lines.append("---")
    return lines


def matched_config_fields(import_type: str, record: dict[str, Any]) -> list[tuple[str, Any]]:
    fields = IMPORT_TYPE_CONFIG_FIELDS.get(import_type) or IMPORT_TYPE_CONFIG_FIELDS["minimal_document_records"]
    return [(field, record_field_value(record, field)) for field in fields]


def render_preview_metadata_sections(
    *,
    record: dict[str, Any],
    import_type: str,
    generated_at: str,
    source_file: str,
) -> str:
    lines: list[str] = []
    lines.extend(metadata_section("matched_config_fields", matched_config_fields(import_type, record)))
    unknown = record.get("unknown_metadata") if isinstance(record.get("unknown_metadata"), dict) else {}
    lines.extend(metadata_section("staged_only_fields", sorted(unknown.items())))
    lines.extend(
        metadata_section(
            "preview_metadata",
            [
                ("import_type", import_type),
                ("preview_generated_at", generated_at),
                ("source_file", source_file),
            ],
        )
    )
    return "\n".join(lines)


def render_metadata_lines(record: dict[str, Any], report: dict[str, Any]) -> list[str]:
    scope = normalize_text(report.get("scope")) or ""
    lines = [
        "- doc_id: `" + (normalize_text(record.get("doc_id")) or "[missing]") + "`",
        "- parent_id: `" + (normalize_text(record.get("parent_id")) or "[root]") + "`",
    ]
    current = record.get("current_library") if isinstance(record.get("current_library"), dict) else {}
    if current:
        exists = "yes" if current.get("exists") else "no"
        payload = "yes" if current.get("payload_exists") else "no"
        lines.extend(
            [
                f"- current {scope_title(scope)} match: {exists}",
                f"- generated payload: {payload}",
            ]
        )
    return lines


def render_summary_preview(report: dict[str, Any], record: dict[str, Any], generated_at: str) -> str:
    title = normalize_text(record.get("title")) or "Untitled Import Record"
    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    summary = str(metadata.get("summary") if "summary" in metadata else metadata.get("current_summary", ""))
    lines = [
        render_doc_front_matter(record, report, generated_at),
        "",
        f"# {title}",
        "",
        "## Import Metadata",
        "",
        *render_metadata_lines(record, report),
        "",
        *render_issue_list(issues_for_record(report, record)),
        "## Proposed Summary",
        "",
        normalize_markdown_body(summary) or "[missing summary]",
        "",
    ]
    return "\n".join(lines).rstrip() + "\n"


def render_full_content_preview(report: dict[str, Any], record: dict[str, Any], generated_at: str) -> str:
    title = normalize_text(record.get("title")) or "Untitled Import Record"
    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    headings = metadata.get("headings") if isinstance(metadata.get("headings"), list) else []
    source_text = normalize_markdown_body(metadata.get("source_text", ""))
    lines = [
        render_doc_front_matter(record, report, generated_at),
        "",
        f"# {title}",
        "",
        "## Import Metadata",
        "",
        *render_metadata_lines(record, report),
        "",
        *render_issue_list(issues_for_record(report, record)),
    ]
    if headings:
        lines.extend(["## Imported Headings", ""])
        lines.extend(f"- {markdown_escape_inline(item)}" for item in headings)
        lines.append("")
    lines.extend(["## Imported Source Text", "", source_text or "[missing source_text]", ""])
    return "\n".join(lines).rstrip() + "\n"


def children_by_parent(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    children: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        parent_id = normalize_text(record.get("parent_id"))
        children.setdefault(parent_id, []).append(record)
    return children


def render_tree_item(
    record: dict[str, Any],
    *,
    children: dict[str, list[dict[str, Any]]],
    depth: int,
    visited: set[str],
    rendered: set[str],
    lines: list[str],
) -> None:
    doc_id = normalize_text(record.get("doc_id")) or f"record-{int(record.get('record_index') or 0) + 1}"
    title = normalize_text(record.get("title")) or "[missing title]"
    indent = "  " * depth
    lines.append(f"{indent}- {title} (`{doc_id}`)")
    rendered.add(doc_id)
    if doc_id in visited:
        lines.append(f"{indent}  - [cycle detected]")
        return
    visited.add(doc_id)
    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    summary = normalize_text(metadata.get("summary") or metadata.get("current_summary"))
    headings = metadata.get("headings") if isinstance(metadata.get("headings"), list) else []
    if summary:
        lines.append(f"{indent}  - summary: {markdown_escape_inline(summary)}")
    if headings:
        lines.append(f"{indent}  - headings: {', '.join(markdown_escape_inline(item) for item in headings)}")
    for child in children.get(doc_id, []):
        render_tree_item(child, children=children, depth=depth + 1, visited=visited, rendered=rendered, lines=lines)
    visited.remove(doc_id)


def render_relationship_preview(report: dict[str, Any], generated_at: str) -> str:
    records = [record for record in report.get("records", []) if isinstance(record, dict)]
    ids = {normalize_text(record.get("doc_id")) for record in records if normalize_text(record.get("doc_id"))}
    children = children_by_parent(records)
    roots = [
        record
        for record in records
        if not normalize_text(record.get("parent_id")) or normalize_text(record.get("parent_id")) not in ids
    ]
    if not roots:
        roots = records
    lines = [
        front_matter(
            {
                "title": f"{scope_title(normalize_text(report.get('scope')))} Import Relationship Tree",
                "import_type": normalize_text(report.get("detected_import_type")),
                "preview_generated_at": generated_at,
            }
        ),
        "",
        f"# {scope_title(normalize_text(report.get('scope')))} Import Relationship Tree",
        "",
        "## Import Metadata",
        "",
        f"- source file: `{normalize_text(report.get('input_file'))}`",
        f"- records: {len(records)}",
        "",
    ]
    report_issues = [
        item
        for item in report.get("issues", [])
        if isinstance(item, dict)
    ]
    lines.extend(render_issue_list(report_issues))
    lines.extend(["## Candidate Tree", ""])
    rendered_ids: set[str] = set()
    for root in roots:
        root_id = normalize_text(root.get("doc_id")) or f"record-{int(root.get('record_index') or 0) + 1}"
        if root_id in rendered_ids:
            continue
        render_tree_item(root, children=children, depth=0, visited=set(), rendered=rendered_ids, lines=lines)
    for record in records:
        doc_id = normalize_text(record.get("doc_id")) or f"record-{int(record.get('record_index') or 0) + 1}"
        if doc_id not in rendered_ids:
            render_tree_item(record, children=children, depth=0, visited=set(), rendered=rendered_ids, lines=lines)
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def has_relationship_metadata(records: list[dict[str, Any]]) -> bool:
    for record in records:
        if normalize_text(record.get("parent_id")):
            return True
        relationships = record.get("relationships") if isinstance(record.get("relationships"), dict) else {}
        if any(relationships.get(key) for key in ["ancestor_ids", "ancestor_titles", "child_ids", "child_titles"]):
            return True
    return False


def render_markdown_previews(
    *,
    repo_root: Path,
    scope: str,
    report: dict[str, Any],
    write: bool,
    generated_at: str | None = None,
    preview_root: Path | str | None = None,
) -> dict[str, Any]:
    if not report.get("ok"):
        report["preview_files"] = []
        report["preview_written"] = False
        return report
    generated = generated_at or preview_generated_at()
    fallback_timestamp = preview_filename_timestamp(generated_at) if generated_at else local_filename_timestamp()
    timestamp_suffix = staged_timestamp_suffix(report, fallback_timestamp)
    import_type = normalize_text(report.get("detected_import_type"))
    records = [record for record in report.get("records", []) if isinstance(record, dict)]
    preview_files: list[dict[str, Any]] = []

    if has_relationship_metadata(records):
        filename = relationship_preview_filename(report, timestamp_suffix)
        path = resolve_preview_path(repo_root, scope, filename, preview_root)
        content = render_relationship_preview(report, generated)
        preview_files.append({"path": relative_path(repo_root, path), "record_count": len(records), "kind": "relationship_tree"})
        if write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

    seen: dict[str, int] = {}
    for record in records:
        filename = record_preview_filename(record, seen, timestamp_suffix)
        path = resolve_preview_path(repo_root, scope, filename, preview_root)
        if import_type == "full_document_content":
            content = render_full_content_preview(report, record, generated)
        else:
            content = render_summary_preview(report, record, generated)
        preview_files.append(
            {
                "path": relative_path(repo_root, path),
                "record_index": record.get("record_index"),
                "doc_id": normalize_text(record.get("doc_id")),
                "kind": "document",
            }
        )
        if write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

    report["preview_files"] = preview_files
    report["preview_written"] = bool(write)
    return report


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
    report["issues"].extend(add_current_library_report(records, current=current_context, scope=normalized_scope))

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
    parser = argparse.ArgumentParser(description="Parse staged Docs Viewer import data and optionally write Markdown previews.")
    parser.add_argument("--scope", default="library", help="Docs Viewer scope to import")
    parser.add_argument("--file", required=True, help="Staged JSON or JSONL filename under var/studio/export-import/<scope>/import-staging/")
    parser.add_argument("--repo-root", default="", help="Override repo root")
    parser.add_argument("--write-previews", action="store_true", help="Write Markdown previews under var/studio/export-import/<scope>/import-preview/")
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
        report = render_markdown_previews(
            repo_root=repo_root,
            scope=args.scope,
            report=report,
            write=bool(args.write_previews),
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
