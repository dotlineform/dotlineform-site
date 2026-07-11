#!/usr/bin/env python3
"""Temporary review source folders for returned document-content packages."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
import re
import shutil
from typing import Any

import docs_source_model as source_model
from docs_returned_import_common import (
    SUPPORTED_EXTENSIONS,
    issue,
    normalize_text,
    relative_path,
    resolve_staged_path,
)
from docs_returned_import_files import (
    export_id_from_json_payload,
    export_id_from_jsonl_header,
    metadata_from_internal_export_meta,
    parse_json_file,
    parse_jsonl_file,
    rows_from_payload,
)


SCHEMA_VERSION = "data_sharing_import_review_source_v1"
FOLDER_ID_SOURCE = "export_metadata"
SAFE_FOLDER_ID_RE = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9._-]*\Z")
SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._-]+")
FRONT_MATTER_FIELDS = ("title", "parent_id", "summary", "viewable")
CONTENT_FIELD = "content"
CONTENT_FORMAT_FIELD = "content_format"


def clean_text(value: Any) -> str:
    return str(value or "").strip()


def current_review_date() -> str:
    return dt.datetime.now().astimezone().strftime("%Y-%m-%d")


def folder_timestamp(generated_at: Any) -> str:
    text = clean_text(generated_at)
    try:
        timestamp = dt.datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
    except ValueError as exc:
        raise ValueError(f"metadata generated_at must be UTC YYYY-MM-DDTHH:MM:SSZ: {text or '<missing>'}") from exc
    return timestamp.astimezone().strftime("%Y%m%d-%H%M%S")


def validate_folder_id(folder_id: Any) -> str:
    value = clean_text(folder_id)
    if not value:
        raise ValueError("folder_id is required")
    if value in {".", ".."} or ".." in value:
        raise ValueError("folder_id must not contain ..")
    if "/" in value or "\\" in value or Path(value).is_absolute():
        raise ValueError("folder_id must be a safe folder name, not a path")
    if not SAFE_FOLDER_ID_RE.fullmatch(value):
        raise ValueError("folder_id contains unsupported characters")
    return value


def derive_folder_id(metadata: dict[str, Any]) -> str:
    timestamp = folder_timestamp(metadata.get("generated_at"))
    data_domain = clean_text(metadata.get("data_domain"))
    profile_id = clean_text(metadata.get("profile_id"))
    if not data_domain:
        raise ValueError("metadata data_domain is required")
    if not profile_id:
        raise ValueError("metadata profile_id is required")
    return validate_folder_id(f"{timestamp}-{data_domain}-{profile_id}")


def resolve_review_folder(repo_root: Path, preview_root: Path, folder_id: str) -> Path:
    del repo_root
    normalized_folder_id = validate_folder_id(folder_id)
    root = preview_root.resolve()
    path = root / normalized_folder_id
    if path.is_symlink():
        raise ValueError("review source folders must not be symlinks")
    resolved = path.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError("folder_id resolves outside the import-preview root") from exc
    return resolved


def markdown_filename(doc_id: str, used: set[str]) -> str:
    stem = SAFE_FILENAME_RE.sub("-", doc_id.strip()).strip(".-_") or "document"
    filename = f"{stem}.md"
    if filename not in used:
        used.add(filename)
        return filename
    suffix = 2
    while True:
        candidate = f"{stem}-{suffix}.md"
        if candidate not in used:
            used.add(candidate)
            return candidate
        suffix += 1


def read_staged_rows(
    repo_root: Path,
    *,
    scope: str,
    staged_filename: str,
    staging_root: Path,
) -> tuple[Path | None, str, list[Any], dict[str, Any], list[dict[str, Any]]]:
    issues: list[dict[str, Any]] = []
    try:
        path = resolve_staged_path(repo_root, scope, staged_filename, staging_root)
    except ValueError as exc:
        return None, "", [], {}, [issue("error", "unsafe_staged_path", str(exc))]

    extension = path.suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        return path, "", [], {}, [issue("error", "unsupported_extension", f"unsupported extension: {extension or '<none>'}")]
    if not path.exists():
        return path, "", [], {}, [issue("error", "unreadable_file", "staged file does not exist")]

    if extension == ".jsonl":
        header_metadata: dict[str, Any] = {}
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                header = json.loads(line)
                if isinstance(header, dict) and header.get("record_type") == "data_sharing_header":
                    header_metadata = {
                        key: value
                        for key, value in header.items()
                        if key not in {"record_type", "schema_version"}
                    }
                break
        except (OSError, json.JSONDecodeError):
            header_metadata = {}
        export_id, export_issues = export_id_from_jsonl_header(path)
        rows, parse_issues = parse_jsonl_file(path)
        issues.extend(export_issues)
        issues.extend(parse_issues)
        return path, export_id, rows, header_metadata, issues

    payload, parse_issues = parse_json_file(path)
    issues.extend(parse_issues)
    if any(item["level"] == "error" for item in issues):
        return path, "", [], {}, issues
    export_id, export_issues = export_id_from_json_payload(payload)
    rows, file_metadata, unknown_file_metadata, shape_issues = rows_from_payload(payload)
    issues.extend(export_issues)
    issues.extend(shape_issues)
    if unknown_file_metadata:
        file_metadata["unknown_file_metadata"] = unknown_file_metadata
    return path, export_id, rows, file_metadata, issues


def content_format_from_package(
    metadata: dict[str, Any],
    package_metadata: dict[str, Any],
    raw_rows: list[Any],
) -> str:
    for source in (metadata, package_metadata):
        value = clean_text(source.get(CONTENT_FORMAT_FIELD)) if isinstance(source, dict) else ""
        if value:
            return value
    for row in raw_rows:
        if isinstance(row, dict):
            value = clean_text(row.get(CONTENT_FORMAT_FIELD))
            if value:
                return value
    return ""


def validate_returned_rows(raw_rows: list[Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    valid: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    seen_doc_ids: dict[str, int] = {}
    for index, row in enumerate(raw_rows):
        line = row.get("_source_line") if isinstance(row, dict) and isinstance(row.get("_source_line"), int) else None
        if not isinstance(row, dict):
            skipped.append(issue("error", "non_object_record", "record is not a JSON object", record_index=index, line=line))
            continue
        doc_id = clean_text(row.get("doc_id"))
        title = clean_text(row.get("title"))
        row_issues: list[dict[str, Any]] = []
        if not doc_id:
            row_issues.append(issue("error", "missing_doc_id", "record is missing doc_id", record_index=index, line=line))
        if not title:
            row_issues.append(issue("error", "missing_title", "record is missing title", record_index=index, line=line, doc_id=doc_id))
        if CONTENT_FIELD not in row or row.get(CONTENT_FIELD) is None:
            row_issues.append(issue("error", "missing_content", "record is missing content", record_index=index, line=line, doc_id=doc_id))
        elif not isinstance(row.get(CONTENT_FIELD), str):
            row_issues.append(issue("error", "invalid_content", "record content must be a string", record_index=index, line=line, doc_id=doc_id))
        elif row.get(CONTENT_FIELD) == "":
            row_issues.append(issue("error", "missing_content", "record content is empty", record_index=index, line=line, doc_id=doc_id))
        if doc_id:
            first_index = seen_doc_ids.get(doc_id)
            if first_index is not None:
                row_issues.append(
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
        if row_issues:
            skipped.extend(row_issues)
            continue
        clean_row = dict(row)
        clean_row["_record_index"] = index
        valid.append(clean_row)
    return valid, skipped


def review_front_matter(
    row: dict[str, Any],
    *,
    metadata: dict[str, Any],
    folder_id: str,
    date_value: str,
) -> dict[str, Any]:
    front_matter: dict[str, Any] = {
        "doc_id": clean_text(row.get("doc_id")),
        "title": clean_text(row.get("title")) or clean_text(row.get("doc_id")),
        "added_date": date_value,
        "last_updated": date_value,
        "review_folder_id": folder_id,
        "review_source_export_id": clean_text(metadata.get("export_id")),
        "review_source_scope": clean_text(metadata.get("scope")),
        "review_profile_id": clean_text(metadata.get("profile_id")),
    }
    for field in FRONT_MATTER_FIELDS:
        if field in row and field not in front_matter:
            front_matter[field] = row[field]
    return front_matter


def source_markdown(row: dict[str, Any], front_matter: dict[str, Any]) -> str:
    preferred_order = [
        "doc_id",
        "title",
        "added_date",
        "last_updated",
        "summary",
        "parent_id",
        "viewable",
    ]
    ordered_keys = [key for key in preferred_order if key in front_matter]
    ordered_keys.extend(sorted(key for key in front_matter.keys() if key not in ordered_keys))
    lines = ["---"]
    for key in ordered_keys:
        lines.append(f"{key}: {source_model.format_front_matter_value(front_matter[key])}")
    lines.append("---")
    return "\n".join(lines) + "\n" + row[CONTENT_FIELD]


def count_issues(items: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "errors": len([item for item in items if item.get("level") == "error"]),
        "warnings": len([item for item in items if item.get("level") == "warning"]),
    }


def skipped_record_count(items: list[dict[str, Any]]) -> int:
    indices = {item.get("record_index") for item in items if isinstance(item.get("record_index"), int)}
    return len(indices)


def create_review_source_folder(
    repo_root: Path,
    *,
    scope: str,
    staged_filename: str,
    dry_run: bool,
    staging_root: Path,
    metadata_root: Path,
    preview_root: Path,
) -> dict[str, Any]:
    path, export_id, raw_rows, package_metadata, parse_issues = read_staged_rows(
        repo_root,
        scope=scope,
        staged_filename=staged_filename,
        staging_root=staging_root,
    )
    issues = list(parse_issues)
    metadata: dict[str, Any] = {}
    metadata_path: Path | None = None
    if export_id and not any(item.get("level") == "error" for item in issues):
        metadata, unknown, metadata_issues, metadata_path = metadata_from_internal_export_meta(
            repo_root,
            export_id,
            metadata_root,
        )
        del unknown
        issues.extend(metadata_issues)

    folder_id = ""
    folder_path: Path | None = None
    if metadata and not any(item.get("level") == "error" for item in issues):
        try:
            folder_id = derive_folder_id(metadata)
            folder_path = resolve_review_folder(repo_root, preview_root, folder_id)
        except ValueError as exc:
            issues.append(issue("error", "invalid_folder_id", str(exc)))

    valid_rows, skipped_records = validate_returned_rows(raw_rows)
    issues.extend(skipped_records)
    issue_counts = count_issues(issues)
    ok = issue_counts["errors"] == 0
    content_format = content_format_from_package(metadata, package_metadata, raw_rows)
    source_scope = clean_text(metadata.get("scope")) if metadata else ""
    generated_at = clean_text(metadata.get("generated_at")) if metadata else ""
    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "folder_id": folder_id,
        "folder_id_source": FOLDER_ID_SOURCE if folder_id else "",
        "data_domain": clean_text(metadata.get("data_domain")) if metadata else "",
        "source_scope": source_scope,
        "profile_id": clean_text(metadata.get("profile_id")) if metadata else "",
        "source_export_id": export_id,
        "staged_filename": clean_text(staged_filename),
        "staged_file": relative_path(repo_root, path) if path is not None else clean_text(staged_filename),
        "content_format": content_format,
        "content_mapping": {
            "content_field": CONTENT_FIELD,
            "content_format_field": CONTENT_FORMAT_FIELD,
            "front_matter_fields": list(FRONT_MATTER_FIELDS),
        },
        "generated_at": generated_at,
        "created_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "counts": {
            "records": len(raw_rows),
            "valid_records": len(valid_rows),
            "skipped_records": skipped_record_count(skipped_records),
            **issue_counts,
        },
        "issues": issues,
        "skipped_records": skipped_records,
        "delete_safe": True,
    }
    if metadata_path is not None:
        manifest["source_metadata_file"] = relative_path(repo_root, metadata_path)
    if folder_path is not None:
        manifest["folder_path"] = relative_path(repo_root, folder_path)
        manifest["source_path"] = relative_path(repo_root, folder_path / "source")

    source_files: list[dict[str, Any]] = []
    if ok and folder_path is not None:
        used_filenames: set[str] = set()
        date_value = current_review_date()
        for row in valid_rows:
            filename = markdown_filename(clean_text(row.get("doc_id")), used_filenames)
            output_path = folder_path / "source" / filename
            source_files.append(
                {
                    "record_index": int(row["_record_index"]),
                    "doc_id": clean_text(row.get("doc_id")),
                    "path": relative_path(repo_root, output_path),
                }
            )
        manifest["source_files"] = source_files
        if not dry_run:
            if folder_path.exists():
                if not folder_path.is_dir() or folder_path.is_symlink():
                    raise ValueError(f"review source folder is not a directory: {relative_path(repo_root, folder_path)}")
                shutil.rmtree(folder_path)
            (folder_path / "source").mkdir(parents=True, exist_ok=True)
            for row, file_record in zip(valid_rows, source_files):
                output_path = folder_path / "source" / Path(str(file_record["path"])).name
                front_matter = review_front_matter(row, metadata=metadata, folder_id=folder_id, date_value=date_value)
                output_path.write_text(source_markdown(row, front_matter), encoding="utf-8")
            (folder_path / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        manifest["source_files"] = []

    return {
        "ok": ok,
        "schema_version": SCHEMA_VERSION,
        "review_action": "source_folder",
        "source_export_id": export_id,
        "source_scope": source_scope,
        "source_profile_id": clean_text(metadata.get("profile_id")) if metadata else "",
        "content_format": content_format,
        "folder_id": folder_id,
        "folder_path": manifest.get("folder_path", ""),
        "source_path": manifest.get("source_path", ""),
        "manifest_path": relative_path(repo_root, folder_path / "manifest.json") if folder_path is not None else "",
        "staged_filename": clean_text(staged_filename),
        "counts": manifest["counts"],
        "issues": issues,
        "skipped_records": skipped_records,
        "source_files": source_files,
        "manifest": manifest,
        "review_source_folder_written": bool(ok and not dry_run),
        "summary_text": (
            f"{'Validated' if dry_run else 'Created'} import review source folder {folder_id} "
            f"with {len(source_files)} documents."
            if ok
            else "Import review source folder was not created."
        ),
    }
