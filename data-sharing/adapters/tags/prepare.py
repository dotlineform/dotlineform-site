#!/usr/bin/env python3
"""Prepare dispatch for Analytics tags Data Sharing."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from data_sharing_adapters import AdapterResolution

from .context import (
    TagsDataSharingDependencies,
    attach_prepare_activity,
    normalize_text,
    prepare_profiles,
    relative_path,
    require_tags_adapter,
    resolve_outbound_package_path,
    selected_record_ids,
    utc_now,
    write_json_file,
)
from .families import aliases, assignments, bundle, registry


def selectable_records(
    repo_root: Path,
    data_domain: Any,
    selectors: Optional[Dict[str, Any]] = None,
    adapter: Optional[AdapterResolution] = None,
    dependencies: Optional[TagsDataSharingDependencies] = None,
) -> Dict[str, Any]:
    del data_domain, dependencies
    adapter = require_tags_adapter(adapter)
    selector_payload = selectors if isinstance(selectors, dict) else {}
    config_id = normalize_text(selector_payload.get("config_id"))
    profile = prepare_profiles(adapter).get(config_id)
    family = normalize_text(profile.get("family")) if profile else ""
    selection = profile.get("selection") if isinstance(profile, dict) and isinstance(profile.get("selection"), dict) else {}
    if family == "registry" and normalize_text(selection.get("mode")) == "explicit_record_ids":
        return registry.selectable_records(repo_root, adapter)
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


def count_record_total(family: str, counts: dict[str, int]) -> int:
    if family == "registry":
        return int(counts.get("tags") or 0)
    if family == "aliases":
        return int(counts.get("aliases") or 0)
    if family == "assignments":
        return int(counts.get("series") or 0)
    return int(counts.get("tags") or 0) + int(counts.get("aliases") or 0) + int(counts.get("series") or 0)


def build_family_package(
    repo_root: Path,
    adapter: AdapterResolution,
    family: str,
    config_id: str,
    generated_at_utc: str,
    selected_ids: Optional[list[str]] = None,
) -> tuple[Dict[str, Any], Dict[str, int], Dict[str, list[str]]]:
    if family == "registry":
        return registry.build_package(repo_root, adapter, config_id, generated_at_utc, selected_tag_ids=selected_ids)
    if family == "aliases":
        return aliases.build_package(repo_root, adapter, config_id, generated_at_utc)
    if family == "assignments":
        return assignments.build_package(repo_root, adapter, config_id, generated_at_utc)
    if family == "bundle":
        return bundle.build_package(repo_root, adapter, config_id, generated_at_utc)
    raise ValueError(f"Unsupported tags sharing profile family: {family}")


def prepare_package(
    repo_root: Path,
    body: Dict[str, Any],
    dry_run: bool,
    adapter: Optional[AdapterResolution] = None,
    dependencies: Optional[TagsDataSharingDependencies] = None,
) -> Dict[str, Any]:
    adapter = require_tags_adapter(adapter)
    config_id = normalize_text(body.get("config_id"))
    profiles = prepare_profiles(adapter)
    profile = profiles.get(config_id)
    if profile is None:
        raise ValueError(f"Unknown tags sharing profile: {config_id}")
    family = normalize_text(profile.get("family"))
    target_format = normalize_text(body.get("target_format") or "json").lower()
    if not target_format:
        target_format = "json"
    output_path = resolve_outbound_package_path(repo_root, adapter, config_id, target_format)
    now_utc = utc_now()
    selection = body.get("selection") if isinstance(body.get("selection"), dict) else {}
    explicit_selected_ids: Optional[list[str]] = None
    if isinstance(selection, dict) and isinstance(selection.get("record_ids"), list) and not bool(selection.get("select_all")):
        explicit_selected_ids = selected_record_ids(selection.get("record_ids"))

    package_payload, family_counts, groups = build_family_package(repo_root, adapter, family, config_id, now_utc, explicit_selected_ids)

    record_total = count_record_total(family, family_counts)
    relative_output = relative_path(repo_root, output_path)
    counts = {
        "selected": record_total,
        "exported": record_total,
        "skipped": 0,
        "failed": 0,
        "truncated": 0,
        **family_counts,
    }
    if not dry_run:
        write_json_file(output_path, package_payload)
    payload: Dict[str, Any] = {
        "ok": True,
        "data_domain": adapter.data_domain,
        "adapter_id": adapter.adapter_id,
        "config_id": config_id,
        "tag_family": family,
        "target_format": target_format,
        "output_file": relative_output,
        "output_files": [relative_output],
        "counts": counts,
        "count_unit": "record",
        "warnings": [],
        "errors": [],
        "issue_counts": {"errors": 0, "warnings": 0},
        "dry_run": dry_run,
        "updated_at_utc": now_utc,
        "output_written": not dry_run,
        "summary_text": (
            f"{'Validated' if dry_run else 'Prepared'} {profile['label']} package "
            f"with {record_total} record(s){' without writing' if dry_run else ''}."
        ),
    }
    if not dry_run:
        attach_prepare_activity(
            repo_root,
            body,
            payload,
            record_groups={**groups, "files": [relative_output]},
            detail_items=[
                str(payload["summary_text"]),
                f"Data family: {family}.",
                f"Output file: {relative_output}.",
            ],
            status="completed",
        )
    if dependencies is not None:
        dependencies.log_event(
            repo_root,
            "tags-data-sharing-prepare",
            {
                "family": family,
                "config_id": config_id,
                "dry_run": dry_run,
                "output_written": bool(payload.get("output_written")),
                "output_file": relative_output,
                "counts": counts,
            },
        )
    return payload
