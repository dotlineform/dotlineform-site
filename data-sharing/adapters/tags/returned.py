#!/usr/bin/env python3
"""Returned package parsing for Analytics tags Data Sharing."""

from __future__ import annotations

from dataclasses import dataclass
import datetime as dt
from pathlib import Path
from typing import Any, Dict, Optional

from data_sharing_adapters import AdapterResolution
from tag_services import tag_assignment_service

from .context import (
    SUPPORTED_EXTENSIONS,
    TagsDataSharingDependencies,
    load_current_aliases,
    load_current_assignments,
    load_current_registry,
    load_series_index,
    normalize_text,
    read_json_file,
    read_jsonl_file,
    relative_path,
    require_tags_adapter,
    resolve_staged_path,
    resolve_staging_root,
    utc_now,
)


@dataclass(frozen=True)
class ReturnedPackage:
    family: str
    mode: str
    import_payload: Dict[str, Any]
    source_payload: Any
    filename: str
    input_format: str


def normalize_mode(value: Any) -> str:
    mode = str(value or "merge").strip().lower()
    if mode not in {"add", "merge", "replace"}:
        raise ValueError("mode must be one of: add, merge, replace")
    return mode


def load_returned_package(repo_root: Path, adapter: AdapterResolution, staged_filename: str) -> ReturnedPackage:
    path = resolve_staged_path(repo_root, adapter, staged_filename)
    if not path.exists():
        raise FileNotFoundError(f"staged file not found: {path.name}")
    input_format = path.suffix.lower().lstrip(".")
    source_payload = read_jsonl_file(path) if input_format == "jsonl" else read_json_file(path)

    if isinstance(source_payload, dict):
        mode = normalize_mode(source_payload.get("mode") or source_payload.get("import_mode"))
        if isinstance(source_payload.get("import_registry"), dict):
            return ReturnedPackage("registry", mode, dict(source_payload["import_registry"]), source_payload, path.name, input_format)
        if isinstance(source_payload.get("import_aliases"), dict):
            return ReturnedPackage("aliases", mode, dict(source_payload["import_aliases"]), source_payload, path.name, input_format)
        if isinstance(source_payload.get("import_assignments"), dict):
            return ReturnedPackage("assignments", "", dict(source_payload["import_assignments"]), source_payload, path.name, input_format)
        if isinstance(source_payload.get("tags"), list):
            return ReturnedPackage("registry", mode, {"tags": source_payload["tags"]}, source_payload, path.name, input_format)
        if isinstance(source_payload.get("aliases"), dict):
            return ReturnedPackage("aliases", mode, {"aliases": source_payload["aliases"]}, source_payload, path.name, input_format)
        if isinstance(source_payload.get("series"), dict):
            return ReturnedPackage("assignments", "", {"series": source_payload["series"]}, source_payload, path.name, input_format)

    if isinstance(source_payload, list):
        records = [item for item in source_payload if isinstance(item, dict)]
        if records and all("tag_id" in item for item in records):
            return ReturnedPackage("registry", "merge", {"tags": records}, source_payload, path.name, input_format)

    raise ValueError("returned package must include import_registry, import_aliases, import_assignments, tags, aliases, or series")


def list_returned_packages(
    repo_root: Path,
    data_domain: Any,
    adapter: Optional[AdapterResolution] = None,
    dependencies: Optional[TagsDataSharingDependencies] = None,
) -> Dict[str, Any]:
    del data_domain
    adapter = require_tags_adapter(adapter)
    staging_root = resolve_staging_root(repo_root, adapter)
    files: list[Dict[str, Any]] = []
    if staging_root.exists():
        for path in sorted(staging_root.iterdir()):
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
    if dependencies is not None:
        dependencies.log_event(repo_root, "tags-data-sharing-list-returned", {"count": len(files)})
    return {
        "ok": True,
        "data_domain": adapter.data_domain,
        "adapter_id": adapter.adapter_id,
        "staging_root": relative_path(repo_root, staging_root),
        "files": files,
    }


def review_returned_package(
    repo_root: Path,
    body: Dict[str, Any],
    dry_run: bool,
    adapter: Optional[AdapterResolution] = None,
    dependencies: Optional[TagsDataSharingDependencies] = None,
) -> Dict[str, Any]:
    operation = str(body.get("operation") or "review").strip()
    if operation != "review":
        raise ValueError("operation must be review")
    adapter = require_tags_adapter(adapter)
    staged_filename = normalize_text(body.get("staged_filename") or body.get("file"))
    package = load_returned_package(repo_root, adapter, staged_filename)
    now_utc = utc_now()
    issues: list[Dict[str, Any]] = []

    if package.family == "registry":
        from .families import registry

        existing = load_current_registry(repo_root, adapter)
        rows, records = registry.rows(existing, package)
        preview_counts = {"records": len(records), "parsed_records": len(records), "malformed_records": 0, "warnings": 0, "errors": 0}
        summary = f"Validated {len(records)} tag registry row(s) in {package.mode} mode without writing."
    elif package.family == "aliases":
        from .families import aliases

        rows, records = aliases.rows(package)
        preview_counts = {"records": len(records), "parsed_records": len(records), "malformed_records": 0, "warnings": 0, "errors": 0}
        summary = f"Validated {len(records)} tag alias row(s) in {package.mode} mode without writing."
    else:
        from .families import assignments

        existing = load_current_assignments(repo_root, adapter)
        series_index = load_series_index(repo_root, adapter)
        rows, _session, preview = assignments.rows(existing, package, series_index)
        warnings = int(preview.get("conflict_count") or 0)
        errors = int(preview.get("invalid_count") or 0) + int(preview.get("missing_count") or 0)
        preview_counts = {
            "records": int(preview.get("staged_series_count") or 0),
            "parsed_records": int(preview.get("staged_series_count") or 0),
            "malformed_records": 0,
            "warnings": warnings,
            "errors": errors,
            "applicable": int(preview.get("applicable_count") or 0),
            "conflicts": int(preview.get("conflict_count") or 0),
            "invalid": int(preview.get("invalid_count") or 0),
            "missing": int(preview.get("missing_count") or 0),
        }
        summary = tag_assignment_service.build_assignment_import_preview_summary(preview)
        for row in rows:
            issues.extend(row.get("issues", []))

    payload: Dict[str, Any] = {
        "ok": True,
        "data_domain": adapter.data_domain,
        "adapter_id": adapter.adapter_id,
        "staged_filename": package.filename,
        "input_format": package.input_format,
        "detected_import_type": f"tags_{package.family}",
        "tag_family": package.family,
        "mode": package.mode,
        "dry_run": dry_run,
        "updated_at_utc": now_utc,
        "counts": preview_counts,
        "issues": issues,
        "review_rows": rows,
        "summary_text": summary,
    }
    if dependencies is not None:
        dependencies.log_event(
            repo_root,
            "tags-data-sharing-review",
            {
                "family": package.family,
                "mode": package.mode,
                "staged_filename": package.filename,
                "records": preview_counts.get("records", 0),
                "warnings": preview_counts.get("warnings", 0),
                "errors": preview_counts.get("errors", 0),
            },
        )
    return payload


def apply_returned_changes(
    repo_root: Path,
    body: Dict[str, Any],
    dry_run: bool,
    adapter: Optional[AdapterResolution] = None,
    dependencies: Optional[TagsDataSharingDependencies] = None,
) -> Dict[str, Any]:
    operation = str(body.get("operation") or "").strip()
    if operation != "apply":
        raise ValueError("operation must be apply")
    adapter = require_tags_adapter(adapter)
    apply_action = normalize_text(body.get("apply_action"))
    if apply_action not in {"registry_apply", "aliases_apply", "assignments_apply"}:
        raise ValueError("apply_action must be registry_apply, aliases_apply, or assignments_apply")
    staged_filename = normalize_text(body.get("staged_filename") or body.get("file"))
    package = load_returned_package(repo_root, adapter, staged_filename)
    expected_family = {
        "registry_apply": "registry",
        "aliases_apply": "aliases",
        "assignments_apply": "assignments",
    }[apply_action]
    if package.family != expected_family:
        raise ValueError(f"apply_action {apply_action} cannot apply tags {package.family} package")
    now_utc = utc_now()
    if apply_action == "registry_apply":
        from .families import registry

        payload = registry.apply(repo_root, adapter, package, body, dry_run, now_utc)
    elif apply_action == "aliases_apply":
        from .families import aliases

        payload = aliases.apply(repo_root, adapter, package, body, dry_run, now_utc)
    else:
        from .families import assignments

        payload = assignments.apply(repo_root, adapter, package, body, dry_run, now_utc)
    if dependencies is not None:
        dependencies.log_event(
            repo_root,
            "tags-data-sharing-apply",
            {
                "family": package.family,
                "apply_action": apply_action,
                "staged_filename": package.filename,
                "dry_run": dry_run,
                "confirmed": bool(body.get("confirm")),
                "written": bool(payload.get("written")),
                "counts": payload.get("counts", {}),
            },
        )
    return payload
