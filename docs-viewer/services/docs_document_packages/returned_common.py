#!/usr/bin/env python3
"""Shared helpers for returned document-package imports."""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path
from typing import Any

from docs_document_packages.provenance import require_package_stage
from docs_document_packages.workspace import configured_workspace_paths, marker_path


SUPPORTED_EXTENSIONS = {".json", ".jsonl"}
TEXT_WHITESPACE_RE = re.compile(r"\s+")
EXPORT_ID_RE = re.compile(r"^ds_\d{8}T\d{6}Z$")
RETIRED_DOCUMENT_PACKAGE_FILENAME_RE = re.compile(
    r"^\d{8}-\d{6}-documents-[A-Za-z0-9][A-Za-z0-9._-]*\.(?:json|jsonl)$",
)

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
    "stage",
    "collection",
    "target_format",
    "record_shape",
    "generated_at",
    "supports_docs_review",
    "supports_return_import",
    "content_format",
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
    "content",
    "last_updated",
}
DOCS_REVIEW_CAPABILITY = "supports_docs_review"
RETURN_IMPORT_CAPABILITY = "supports_return_import"


def retired_document_package_filename(value: Any) -> bool:
    return RETIRED_DOCUMENT_PACKAGE_FILENAME_RE.fullmatch(
        Path(str(value or "")).name,
    ) is not None


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
    del repo_root
    try:
        return marker_path(path)
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


def empty_report(repo_root: Path, stage: str, staged_file: str) -> dict[str, Any]:
    return {
        "ok": False,
        "stage": stage,
        "input_file": staged_file,
        "input_format": "",
        "detected_import_type": "unknown",
        "source_export_id": "",
        "source_profile_id": "",
        "source_stage": "",
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


def resolve_staged_path(repo_root: Path, stage: str, staged_file: str, staging_root: Path | str | None = None) -> Path:
    require_package_stage(stage)
    base_root = Path(staging_root) if staging_root else configured_workspace_paths(repo_root).import_staging
    raw_path = Path(staged_file)
    path = raw_path if raw_path.is_absolute() else base_root / raw_path
    resolved = path.resolve()
    allowed_root = base_root.resolve()
    if resolved != allowed_root and allowed_root not in resolved.parents:
        raise ValueError(f"staged file must stay under {base_root}")
    return resolved


def list_staged_import_files(repo_root: Path, stage: str, staging_root: Path | str | None = None) -> list[dict[str, Any]]:
    require_package_stage(stage)
    base_root = Path(staging_root) if staging_root else configured_workspace_paths(repo_root).import_staging
    resolved_staging_root = base_root.resolve()
    if not resolved_staging_root.exists():
        return []
    files: list[dict[str, Any]] = []
    for path in sorted(resolved_staging_root.iterdir()):
        if path.name.endswith(".meta.json"):
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
