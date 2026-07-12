#!/usr/bin/env python3
"""Safe review-package associations for the managed Docs Import listing."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import re
from typing import Any

from docs_import_data_sharing_package import COLLECTION_SOURCE_FORMAT
from docs_returned_import_files import (
    export_id_from_json_payload,
    export_id_from_jsonl_header,
    parse_json_file,
)


REVIEW_PACKAGE_SCHEMA_VERSION = "docs_review_validated_package_v1"
SAFE_PACKAGE_ID_PATTERN = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9._-]*\Z")


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _safe_staged_filename(value: Any) -> str:
    filename = _clean_text(value)
    if not filename or Path(filename).name != filename:
        return ""
    return filename


def _manifest_for_package(package_path: Path) -> dict[str, Any] | None:
    if package_path.is_symlink() or not package_path.is_dir():
        return None
    package_id = package_path.name
    if not SAFE_PACKAGE_ID_PATTERN.fullmatch(package_id):
        return None
    manifest_path = package_path / "manifest.json"
    if manifest_path.is_symlink() or not manifest_path.is_file():
        return None
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(manifest, dict):
        return None
    if manifest.get("schema_version") != REVIEW_PACKAGE_SCHEMA_VERSION:
        return None
    if _clean_text(manifest.get("package_id")) != package_id:
        return None
    if _clean_text(manifest.get("status")).lower() != "validated":
        return None
    return manifest


def _staged_export_id(path: Path) -> str:
    try:
        if path.suffix.lower() == ".jsonl":
            export_id, issues = export_id_from_jsonl_header(path)
            return "" if issues else export_id
        if path.suffix.lower() == ".json":
            payload, parse_issues = parse_json_file(path)
            if parse_issues:
                return ""
            export_id, issues = export_id_from_json_payload(payload)
            return "" if issues else export_id
    except OSError:
        return ""
    return ""


def attach_review_package_associations(
    files: list[dict[str, Any]],
    *,
    import_preview_root: Path,
    import_staging_root: Path,
) -> list[dict[str, Any]]:
    """Attach package ids only to matching server-listed immutable staged records."""

    projected = copy.deepcopy(files)
    by_filename = {
        _clean_text(record.get("filename")): record
        for record in projected
        if _clean_text(record.get("source_format")) == COLLECTION_SOURCE_FORMAT
    }
    if not by_filename or not import_preview_root.is_dir() or import_preview_root.is_symlink():
        return projected

    export_ids: dict[str, str] = {}
    for package_path in sorted(import_preview_root.iterdir(), key=lambda path: path.name.lower()):
        manifest = _manifest_for_package(package_path)
        if manifest is None:
            continue
        filename = _safe_staged_filename(manifest.get("staged_filename"))
        record = by_filename.get(filename)
        if record is None:
            continue
        source_export_id = _clean_text(manifest.get("source_export_id"))
        if not source_export_id:
            continue
        if filename not in export_ids:
            staged_path = import_staging_root / filename
            export_ids[filename] = _staged_export_id(staged_path)
        if export_ids[filename] != source_export_id:
            continue
        record.setdefault("review_package_ids", []).append(package_path.name)
    return projected


__all__ = ["attach_review_package_associations"]
