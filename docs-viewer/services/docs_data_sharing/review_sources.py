#!/usr/bin/env python3
"""Temporary review source folders for returned document-content packages."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
import re
from typing import Any

import docs_source_model as source_model
from docs_management_source_service import split_source_exact
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


SCHEMA_VERSION = "docs_review_validated_package_v1"
FOLDER_ID_SOURCE = "export_metadata"
SAFE_FOLDER_ID_RE = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9._-]*\Z")
SAFE_DOC_ID_RE = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9._-]*\Z")
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
        elif not SAFE_DOC_ID_RE.fullmatch(doc_id):
            row_issues.append(
                issue(
                    "error",
                    "invalid_doc_id",
                    f"record doc_id must be a safe single path segment: {doc_id}",
                    record_index=index,
                    line=line,
                    doc_id=doc_id,
                )
            )
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


def project_package_local_hierarchy(
    valid_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Root compact-profile documents whose canonical parent is outside the returned selection."""
    package_doc_ids = {clean_text(row.get("doc_id")) for row in valid_rows}
    projected_rows: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    for row in valid_rows:
        projected = dict(row)
        parent_id = clean_text(projected.get("parent_id"))
        if parent_id and parent_id not in package_doc_ids:
            projected.pop("parent_id", None)
            warning = issue(
                "warning",
                "parent_outside_materialized_package",
                f"materialized review document was rooted because parent_id is outside the package: {parent_id}",
                record_index=int(row["_record_index"]),
                doc_id=clean_text(row.get("doc_id")),
            )
            warning["parent_id"] = parent_id
            warnings.append(warning)
        projected_rows.append(projected)
    return projected_rows, warnings


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


def validate_materialized_sources(source_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Validate the exact Markdown projection before it becomes discoverable by Docs Review."""
    if not source_records:
        return [issue("error", "missing_materialized_sources", "review package must contain at least one source document")]
    issues: list[dict[str, Any]] = []
    parsed: dict[str, dict[str, Any]] = {}
    for record in source_records:
        filename = clean_text(record.get("filename"))
        expected_doc_id = clean_text(record.get("doc_id"))
        try:
            _front_matter_source, front_matter, _source_body = split_source_exact(str(record.get("source_text") or ""))
        except ValueError as exc:
            issues.append(
                issue(
                    "error",
                    "invalid_materialized_source",
                    f"materialized review source could not be parsed: {filename}: {exc}",
                    doc_id=expected_doc_id,
                )
            )
            continue
        doc_id = clean_text(front_matter.get("doc_id"))
        title = clean_text(front_matter.get("title"))
        parent_id = clean_text(front_matter.get("parent_id"))
        if not doc_id or not SAFE_DOC_ID_RE.fullmatch(doc_id):
            issues.append(
                issue(
                    "error",
                    "invalid_materialized_doc_id",
                    f"materialized review source has an invalid doc_id: {filename}",
                    doc_id=doc_id or expected_doc_id,
                )
            )
            continue
        if doc_id != expected_doc_id or filename != f"{doc_id}.md":
            issues.append(
                issue(
                    "error",
                    "materialized_source_identity_mismatch",
                    f"materialized review filename and doc_id must match: {filename}",
                    doc_id=doc_id,
                )
            )
            continue
        if not title:
            issues.append(
                issue(
                    "error",
                    "missing_materialized_title",
                    f"materialized review source is missing title: {filename}",
                    doc_id=doc_id,
                )
            )
            continue
        if doc_id in parsed:
            issues.append(issue("error", "duplicate_materialized_doc_id", f"duplicate materialized doc_id: {doc_id}", doc_id=doc_id))
            continue
        parsed[doc_id] = {"parent_id": parent_id}

    if issues:
        return issues

    for doc_id, record in parsed.items():
        parent_id = record["parent_id"]
        if parent_id and parent_id not in parsed:
            issues.append(
                issue(
                    "error",
                    "unknown_materialized_parent_id",
                    f"materialized review parent_id does not identify a package document: {parent_id}",
                    doc_id=doc_id,
                )
            )

    for doc_id in parsed:
        current = doc_id
        visited: set[str] = set()
        while current:
            if current in visited:
                issues.append(
                    issue(
                        "error",
                        "materialized_hierarchy_cycle",
                        f"materialized review hierarchy contains a cycle involving: {doc_id}",
                        doc_id=doc_id,
                    )
                )
                break
            visited.add(current)
            current = clean_text(parsed.get(current, {}).get("parent_id"))
    return issues


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
    materialized_rows, hierarchy_warnings = project_package_local_hierarchy(valid_rows)
    issues.extend(hierarchy_warnings)
    content_format = content_format_from_package(metadata, package_metadata, raw_rows)
    source_scope = clean_text(metadata.get("scope")) if metadata else ""
    generated_at = clean_text(metadata.get("generated_at")) if metadata else ""
    source_files: list[dict[str, Any]] = []
    materialized_sources: list[dict[str, Any]] = []
    if not any(item.get("level") == "error" for item in issues) and folder_path is not None:
        used_filenames: set[str] = set()
        date_value = current_review_date()
        for row in materialized_rows:
            doc_id = clean_text(row.get("doc_id"))
            filename = markdown_filename(doc_id, used_filenames)
            output_path = folder_path / "source" / filename
            source_text = source_markdown(
                row,
                review_front_matter(row, metadata=metadata, folder_id=folder_id, date_value=date_value),
            )
            source_files.append(
                {
                    "record_index": int(row["_record_index"]),
                    "doc_id": doc_id,
                    "path": relative_path(repo_root, output_path),
                }
            )
            materialized_sources.append(
                {
                    "doc_id": doc_id,
                    "filename": filename,
                    "source_text": source_text,
                }
            )
        issues.extend(validate_materialized_sources(materialized_sources))

    if folder_path is not None and folder_path.exists():
        issues.append(
            issue(
                "error",
                "review_package_exists",
                f"timestamped Docs Review package already exists: {folder_id}",
            )
        )

    issue_counts = count_issues(issues)
    ok = issue_counts["errors"] == 0
    counts = {
        "records": len(raw_rows),
        "valid_records": len(valid_rows),
        "skipped_records": skipped_record_count(skipped_records),
        **issue_counts,
    }
    default_doc_id = next(
        (
            clean_text(row.get("doc_id"))
            for row in materialized_rows
            if not clean_text(row.get("parent_id"))
        ),
        clean_text(materialized_rows[0].get("doc_id")) if materialized_rows else "",
    )
    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "package_id": folder_id,
        "status": "validated" if ok else "",
        "data_domain": clean_text(metadata.get("data_domain")) if metadata else "",
        "source_scope": source_scope,
        "default_doc_id": default_doc_id,
        "profile_id": clean_text(metadata.get("profile_id")) if metadata else "",
        "source_projection": "rendered_derived_text_only",
        "source_export_id": export_id,
        "package_id_source": FOLDER_ID_SOURCE if folder_id else "",
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
        "validation": {
            "counts": counts,
            "issues": issues,
            "skipped_records": skipped_records,
        },
        "delete_safe": True,
        "source_files": [
            {
                "record_index": record["record_index"],
                "doc_id": record["doc_id"],
                "path": f"source/{Path(str(record['path'])).name}",
            }
            for record in source_files
        ],
    }
    if metadata_path is not None:
        manifest["source_metadata_file"] = relative_path(repo_root, metadata_path)

    if ok and folder_path is not None:
        if not dry_run:
            (folder_path / "source").mkdir(parents=True, exist_ok=False)
            for source_record in materialized_sources:
                (folder_path / "source" / source_record["filename"]).write_text(
                    source_record["source_text"],
                    encoding="utf-8",
                )
            (folder_path / "manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

    package_path = relative_path(repo_root, folder_path) if folder_path is not None else ""
    source_path = relative_path(repo_root, folder_path / "source") if folder_path is not None else ""
    if ok:
        action = "Validated" if dry_run else "Published"
        summary_text = (
            f"{action} Docs Review package {folder_id} with {len(source_files)} "
            "rendered-derived text documents."
        )
    else:
        summary_text = "Docs Review package was not published because validation failed."

    return {
        "ok": ok,
        "schema_version": SCHEMA_VERSION,
        "review_action": "source_folder",
        "source_export_id": export_id,
        "source_scope": source_scope,
        "source_profile_id": clean_text(metadata.get("profile_id")) if metadata else "",
        "content_format": content_format,
        "folder_id": folder_id,
        "folder_path": package_path,
        "source_path": source_path,
        "manifest_path": relative_path(repo_root, folder_path / "manifest.json") if folder_path is not None else "",
        "staged_filename": clean_text(staged_filename),
        "counts": counts,
        "issues": issues,
        "skipped_records": skipped_records,
        "source_files": source_files,
        "manifest": manifest,
        "review_source_folder_written": bool(ok and not dry_run),
        "summary_text": summary_text,
    }
