#!/usr/bin/env python3
"""Analytics tags adapter for Data Sharing workflows."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from data_sharing_adapters import AdapterResolution
from services.dispatch import DataSharingAdapterHandlers
from tag_services import tag_assignment_service

from .context import (
    SUPPORTED_EXTENSIONS,
    SUPPORTED_PREPARE_FORMATS,
    TAG_PREPARE_PROFILES,
    TagsDataSharingDependencies,
    adapter_source_path,
    changed_from_stats,
    issue,
    load_current_aliases,
    load_current_assignments,
    load_current_registry,
    load_series_index,
    load_source_json,
    load_works_index,
    normalize_text,
    prepare_profiles,
    read_json_file,
    read_jsonl_file,
    relative_path,
    require_tags_adapter,
    resolve_outbound_package_path,
    resolve_outbound_root,
    resolve_staged_path,
    resolve_staging_root,
    selected_record_indices,
    selection_required,
    source_files,
    utc_now,
    write_json_file,
)
from .families import aliases, assignments, bundle, registry
from .prepare import count_record_total, prepare_package
from .returned import ReturnedPackage, load_returned_package, normalize_mode


# Compatibility aliases for existing tests and direct imports.
build_registry_package = registry.build_package
build_aliases_package = aliases.build_package
build_assignments_package = assignments.build_package
build_bundle_package = bundle.build_package
registry_rows = registry.rows
alias_rows = aliases.rows
assignment_rows = assignments.rows
assignment_record_groups = assignments.record_groups
normalize_assignments_import_payload = assignments.normalize_import_payload
selected_registry_payload = registry.selected_payload
selected_aliases_payload = aliases.selected_payload
selected_assignment_session = assignments.selected_session
selected_assignment_groups = assignments.selected_groups
tag_ids_from_registry = registry.tag_ids_from_registry
alias_keys_from_payload = aliases.alias_keys_from_payload
series_ids_from_assignments = assignments.series_ids_from_assignments
work_ids_from_assignments = assignments.work_ids_from_assignments
count_assignment_works = assignments.count_assignment_works
merge_counts = bundle.merge_counts
merge_groups = bundle.merge_groups
apply_registry = registry.apply
apply_aliases = aliases.apply
apply_assignments = assignments.apply


def selectable_records(
    repo_root: Path,
    data_domain: Any,
    selectors: Optional[Dict[str, Any]] = None,
    adapter: Optional[AdapterResolution] = None,
    dependencies: Optional[TagsDataSharingDependencies] = None,
) -> Dict[str, Any]:
    del repo_root, data_domain, selectors, dependencies
    adapter = require_tags_adapter(adapter)
    return {
        "ok": True,
        "data_domain": adapter.data_domain,
        "adapter_id": adapter.adapter_id,
        "selection_model": str(adapter.capability.get("selection_model") or adapter.domain.get("selection_model") or "").strip(),
        "records": [],
        "docs": [],
        "source": {
            "kind": "adapter",
            "module": "analytics.tags",
            "source": "profile_only",
            "data_domain": adapter.data_domain,
        },
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
        existing = load_current_registry(repo_root, adapter)
        rows, records = registry.rows(existing, package)
        preview_counts = {"records": len(records), "parsed_records": len(records), "malformed_records": 0, "warnings": 0, "errors": 0}
        summary = f"Validated {len(records)} tag registry row(s) in {package.mode} mode without writing."
    elif package.family == "aliases":
        rows, records = aliases.rows(package)
        preview_counts = {"records": len(records), "parsed_records": len(records), "malformed_records": 0, "warnings": 0, "errors": 0}
        summary = f"Validated {len(records)} tag alias row(s) in {package.mode} mode without writing."
    else:
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
        payload = registry.apply(repo_root, adapter, package, body, dry_run, now_utc)
    elif apply_action == "aliases_apply":
        payload = aliases.apply(repo_root, adapter, package, body, dry_run, now_utc)
    else:
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


def list_returned_packages(
    repo_root: Path,
    data_domain: Any,
    adapter: Optional[AdapterResolution] = None,
    dependencies: Optional[TagsDataSharingDependencies] = None,
) -> Dict[str, Any]:
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


def handlers_for(
    dependencies_factory: Callable[[], TagsDataSharingDependencies],
) -> DataSharingAdapterHandlers:
    def selectable_records_handler(repo_root: Path, data_domain: Any, selectors: Any, adapter: AdapterResolution) -> Dict[str, Any]:
        return selectable_records(repo_root, data_domain, selectors, adapter, dependencies_factory())

    def list_handler(repo_root: Path, data_domain: Any, adapter: AdapterResolution) -> Dict[str, Any]:
        return list_returned_packages(repo_root, data_domain, adapter, dependencies_factory())

    def review_handler(repo_root: Path, body: Dict[str, Any], dry_run: bool, adapter: AdapterResolution) -> Dict[str, Any]:
        return review_returned_package(repo_root, body, dry_run, adapter, dependencies_factory())

    def apply_handler(repo_root: Path, body: Dict[str, Any], dry_run: bool, adapter: AdapterResolution) -> Dict[str, Any]:
        return apply_returned_changes(repo_root, body, dry_run, adapter, dependencies_factory())

    def prepare_handler(repo_root: Path, body: Dict[str, Any], dry_run: bool, adapter: AdapterResolution) -> Dict[str, Any]:
        return prepare_package(repo_root, body, dry_run, adapter, dependencies_factory())

    return DataSharingAdapterHandlers(
        module="analytics.tags",
        selectable_records=selectable_records_handler,
        prepare=prepare_handler,
        list_returned=list_handler,
        review=review_handler,
        apply=apply_handler,
    )
