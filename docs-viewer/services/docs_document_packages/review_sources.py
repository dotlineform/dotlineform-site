#!/usr/bin/env python3
"""Persistent Docs Review projections for returned document-content packages."""

from __future__ import annotations

import copy
import datetime as dt
import json
from pathlib import Path
import re
from typing import Any, Callable

import docs_source_model as source_model
from docs_import_content import (
    CONTENT_INTENT_EMPTY_NEW,
    CONTENT_INTENT_PRESERVE_EXISTING,
    CONTENT_INTENT_REPLACE,
)
from docs_import_preview import generate_normalized_import_content_preview
from docs_management_source_service import split_source_exact
from docs_review_materialization import match_existing_review_package, publish_review_package
from docs_document_packages.returned_common import (
    SUPPORTED_EXTENSIONS,
    issue,
    normalize_text,
    relative_path,
    resolve_staged_path,
)
from docs_document_packages.returned_files import (
    export_id_from_json_payload,
    export_id_from_jsonl_header,
    metadata_from_internal_export_meta,
    parse_json_file,
    parse_jsonl_file,
    rows_from_payload,
)
from docs_document_packages.returned_validation import validate_whole_returned_package
from docs_document_packages.workspace import configured_workspace_paths


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
                        if key != "record_type"
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
        document = row.get("document") if isinstance(row.get("document"), dict) else {}
        title = clean_text(row.get("title") or document.get("title"))
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


def source_markdown(body: str, front_matter: dict[str, Any]) -> str:
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
    return "\n".join(lines) + "\n" + body


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
    normalize_import_content: Callable[..., Any],
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
        if not any(item.get("level") == "error" for item in issues):
            issues.extend(validate_whole_returned_package(raw_rows, metadata, scope=scope))

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
    source_profile_id = clean_text(metadata.get("profile_id")) if metadata else ""
    full_source_package = source_profile_id == "document-full-source"
    generated_at = clean_text(metadata.get("generated_at")) if metadata else ""
    current_docs = source_model.load_scope_docs(repo_root, scope)
    current_docs_by_id = {doc.doc_id: doc for doc in current_docs}
    normalized_batch = None
    if metadata and materialized_rows and folder_path is not None:
        normalized_package_metadata = {**package_metadata, **metadata}
        wrapper_schema = clean_text(package_metadata.get("schema_version"))
        if wrapper_schema:
            normalized_package_metadata["schema_version"] = wrapper_schema
        else:
            normalized_package_metadata.pop("schema_version", None)
        normalized_package_metadata["export_id"] = export_id
        normalized_package_metadata["content_format"] = content_format
        try:
            normalized_batch = normalize_import_content(
                materialized_rows,
                package_metadata=normalized_package_metadata,
                current_doc_ids=set(current_docs_by_id),
                staged_filename=staged_filename,
            )
        except ValueError as exc:
            issues.append(issue("error", "invalid_import_content", str(exc)))
    normalized_records = list(normalized_batch.records) if normalized_batch is not None else []
    for record in normalized_records:
        record_index = int(record.provenance.get("record_index") or 0)
        for diagnostic in record.diagnostics:
            if diagnostic.get("level") != "warning":
                continue
            diagnostic_issue = issue(
                "warning",
                clean_text(diagnostic.get("code")) or "import_content_warning",
                clean_text(diagnostic.get("message")) or "Document package content warning.",
                record_index=record_index,
                doc_id=record.doc_id,
            )
            for key, value in diagnostic.items():
                if key not in {"level", "code", "message"}:
                    diagnostic_issue[key] = copy.deepcopy(value)
            issues.append(diagnostic_issue)
    source_files: list[dict[str, Any]] = []
    materialized_sources: list[dict[str, Any]] = []
    if not any(item.get("level") == "error" for item in issues) and folder_path is not None:
        used_filenames: set[str] = set()
        date_value = current_review_date()
        workspace_paths = configured_workspace_paths(repo_root)
        for record in normalized_records:
            doc_id = record.doc_id
            filename = markdown_filename(doc_id, used_filenames)
            output_path = folder_path / "source" / filename
            projection_row = {
                **record.front_matter,
                "doc_id": doc_id,
                "title": record.title,
            }
            if record.parent_id or "parent_id" in record.front_matter:
                projection_row["parent_id"] = record.parent_id
            if record.content_intent == CONTENT_INTENT_REPLACE:
                preview = generate_normalized_import_content_preview(
                    record,
                    repo_root=repo_root,
                    scope=scope,
                    staging_root=staging_root,
                    workspace_root=workspace_paths.root,
                )
                body = str(preview.get("markdown_preview") or "")
            elif record.content_intent == CONTENT_INTENT_PRESERVE_EXISTING:
                current_doc = current_docs_by_id.get(record.doc_id)
                if current_doc is None:
                    issues.append(
                        issue(
                            "error",
                            "missing_preserve_existing_source",
                            f"current canonical source is unavailable for preserve-existing record: {record.doc_id}",
                            record_index=int(record.provenance.get("record_index") or 0),
                            doc_id=record.doc_id,
                        )
                    )
                    continue
                _front_matter_source, _current_front_matter, body = split_source_exact(current_doc.source_text)
            elif record.content_intent == CONTENT_INTENT_EMPTY_NEW:
                body = ""
            else:
                raise RuntimeError(f"unsupported import content intent: {record.content_intent}")
            source_text = source_markdown(
                body,
                review_front_matter(
                    projection_row,
                    metadata=metadata,
                    folder_id=folder_id,
                    date_value=date_value,
                ),
            )
            source_files.append(
                {
                    "record_index": int(record.provenance.get("record_index") or 0),
                    "doc_id": doc_id,
                    "content_intent": record.content_intent,
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

    issue_counts = count_issues(issues)
    ok = issue_counts["errors"] == 0
    counts = {
        "records": len(raw_rows),
        "valid_records": len(normalized_records),
        "skipped_records": skipped_record_count(skipped_records),
        **issue_counts,
    }
    default_doc_id = next(
        (
            record.doc_id
            for record in normalized_records
            if not record.parent_id
        ),
        normalized_records[0].doc_id if normalized_records else "",
    )
    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "package_id": folder_id,
        "status": "validated" if ok else "",
        "data_domain": clean_text(metadata.get("data_domain")) if metadata else "",
        "source_scope": source_scope,
        "default_doc_id": default_doc_id,
        "profile_id": source_profile_id,
        "source_projection": "canonical_full_source" if full_source_package else "rendered_derived_text_only",
        "source_export_id": export_id,
        "package_id_source": FOLDER_ID_SOURCE if folder_id else "",
        "staged_filename": clean_text(staged_filename),
        "staged_file": relative_path(repo_root, path) if path is not None else clean_text(staged_filename),
        "content_format": content_format,
        "content_mapping": {
            "content_field": "canonical_markdown" if full_source_package else CONTENT_FIELD,
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
                "content_intent": record["content_intent"],
                "path": f"source/{Path(str(record['path'])).name}",
            }
            for record in source_files
        ],
    }
    if metadata_path is not None:
        manifest["source_metadata_file"] = relative_path(repo_root, metadata_path)

    existing_review = False
    existing_generated: dict[str, Any] = {}
    if (
        folder_path is not None
        and (folder_path.exists() or folder_path.is_symlink())
        and ok
    ):
        try:
            existing_generated = match_existing_review_package(
                package_path=folder_path,
                package_id=folder_id,
                source_records=materialized_sources,
                manifest=manifest,
            )
            existing_review = True
        except (OSError, ValueError) as exc:
            issues.append(
                issue(
                    "error",
                    "review_package_identity_mismatch",
                    f"existing Docs Review package does not match the selected returned package: {exc}",
                )
            )
            issue_counts = count_issues(issues)
            counts = {
                "records": len(raw_rows),
                "valid_records": len(normalized_records),
                "skipped_records": skipped_record_count(skipped_records),
                **issue_counts,
            }
            ok = False
            manifest["status"] = ""
            manifest["validation"] = {
                "counts": counts,
                "issues": issues,
                "skipped_records": skipped_records,
            }

    generated: dict[str, Any] = {}
    package_written = False
    if existing_review:
        generated = {
            "document_count": int(existing_generated.get("document_count") or 0),
            "asset_count": 0,
            "warnings": [],
        }
    elif ok and folder_path is not None and not dry_run:
        try:
            build = publish_review_package(
                repo_root,
                package_path=folder_path,
                package_id=folder_id,
                default_doc_id=default_doc_id,
                source_records=materialized_sources,
                manifest=manifest,
            )
            generated = {
                "document_count": int(build.get("document_count") or 0),
                "asset_count": int(build.get("asset_count") or 0),
                "warnings": list(build.get("warnings") or []),
            }
            package_written = True
        except (OSError, RuntimeError, ValueError) as exc:
            issues.append(
                issue(
                    "error",
                    "review_package_build_failed",
                    f"persistent Docs Review package build failed: {exc}",
                )
            )
            issue_counts = count_issues(issues)
            counts = {
                "records": len(raw_rows),
                "valid_records": len(normalized_records),
                "skipped_records": skipped_record_count(skipped_records),
                **issue_counts,
            }
            ok = False
            manifest["status"] = ""
            manifest["validation"] = {
                "counts": counts,
                "issues": issues,
                "skipped_records": skipped_records,
            }

    package_path = relative_path(repo_root, folder_path) if folder_path is not None else ""
    source_path = relative_path(repo_root, folder_path / "source") if folder_path is not None else ""
    if ok:
        action = "Matched existing" if existing_review else ("Validated" if dry_run else "Published")
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
        "review_source_folder_written": package_written,
        "review_generated_written": package_written,
        "review_existing": existing_review,
        "generated": generated,
        "summary_text": summary_text,
    }
