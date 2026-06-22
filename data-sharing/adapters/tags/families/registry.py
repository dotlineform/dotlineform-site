#!/usr/bin/env python3
"""Registry family behavior for Analytics tags Data Sharing."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Dict, Optional

from data_sharing_adapters import AdapterResolution
from tag_services import tag_registry_mutations, tag_source_model, tag_write_transactions

from ..context import (
    adapter_source_path,
    attach_apply_activity,
    changed_from_stats,
    load_current_registry,
    package_metadata,
    normalize_text,
    selected_record_indices,
    selection_required,
    source_files,
)
from ..returned import ReturnedPackage


def tag_ids_from_registry(registry_payload: dict[str, Any]) -> list[str]:
    tags = registry_payload.get("tags") if isinstance(registry_payload.get("tags"), list) else []
    return sorted({str(item.get("tag_id") or "").strip() for item in tags if isinstance(item, dict) and str(item.get("tag_id") or "").strip()})


def tag_record_name(tag: Dict[str, Any], tag_id: str) -> str:
    return normalize_text(tag.get("label")) or tag_id


def tag_sort_key(tag: Dict[str, Any]) -> tuple[str, str]:
    tag_id = normalize_text(tag.get("tag_id"))
    return (tag_record_name(tag, tag_id).casefold(), tag_id.casefold())


def selectable_records(repo_root: Path, adapter: AdapterResolution) -> Dict[str, Any]:
    registry = load_current_registry(repo_root, adapter)
    source_tags = registry.get("tags") if isinstance(registry.get("tags"), list) else []
    records: list[Dict[str, Any]] = []
    for tag in source_tags:
        if not isinstance(tag, dict):
            continue
        tag_id = normalize_text(tag.get("tag_id"))
        if not tag_id:
            continue
        records.append(
            {
                "id": tag_id,
                "name": tag_record_name(tag, tag_id),
                "tag_id": tag_id,
                "group": normalize_text(tag.get("group")),
                "selectable": True,
            }
        )
    records.sort(key=lambda record: (normalize_text(record.get("name")).casefold(), normalize_text(record.get("id")).casefold()))
    return {
        "ok": True,
        "data_domain": adapter.data_domain,
        "adapter_id": adapter.adapter_id,
        "selection_model": str(adapter.capability.get("selection_model") or adapter.domain.get("selection_model") or "").strip(),
        "records": records,
        "docs": records,
        "source": {
            "kind": "adapter",
            "module": "analytics.tags",
            "source": "tag_registry",
            "data_domain": adapter.data_domain,
        },
    }


def selected_tags(source_tags: list[Any], selected_tag_ids: Optional[list[str]]) -> list[Dict[str, Any]]:
    tags = [tag for tag in source_tags if isinstance(tag, dict)]
    if selected_tag_ids is None:
        return sorted(tags, key=tag_sort_key)
    by_id = {normalize_text(tag.get("tag_id")): tag for tag in tags if normalize_text(tag.get("tag_id"))}
    unknown = [tag_id for tag_id in selected_tag_ids if tag_id not in by_id]
    if unknown:
        raise ValueError(f"record_ids contains unknown tag id: {unknown[0]}")
    selected = set(selected_tag_ids)
    return sorted([tag for tag in tags if normalize_text(tag.get("tag_id")) in selected], key=tag_sort_key)


def build_package(
    repo_root: Path,
    adapter: AdapterResolution,
    config_id: str,
    generated_at_utc: str,
    selected_tag_ids: Optional[list[str]] = None,
) -> tuple[Dict[str, Any], Dict[str, int], Dict[str, list[str]]]:
    registry = load_current_registry(repo_root, adapter)
    source_tags = registry.get("tags") if isinstance(registry.get("tags"), list) else []
    tags = selected_tags(source_tags, selected_tag_ids)
    counts = {"tags": len(tags)}
    payload = {
        "package_metadata": package_metadata(
            adapter=adapter,
            config_id=config_id,
            family="registry",
            generated_at_utc=generated_at_utc,
            source_paths=source_files(repo_root, adapter, "registry"),
            counts=counts,
        ),
        "policy": copy.deepcopy(registry.get("policy") if isinstance(registry.get("policy"), dict) else {}),
        "tags": copy.deepcopy(tags),
    }
    return payload, counts, {"tags": tag_ids_from_registry({"tags": tags})}


def rows(existing_payload: Dict[str, Any], package: ReturnedPackage) -> tuple[list[Dict[str, Any]], list[Dict[str, Any]]]:
    allowed_groups = tag_source_model.extract_allowed_groups(existing_payload)
    tags = tag_source_model.sanitize_import_registry(package.import_payload, allowed_groups)
    current_ids = {
        str(item.get("tag_id") or "").strip().lower()
        for item in existing_payload.get("tags", [])
        if isinstance(item, dict) and str(item.get("tag_id") or "").strip()
    }
    review_rows: list[Dict[str, Any]] = []
    for index, tag in enumerate(tags):
        tag_id = tag["tag_id"]
        exists = tag_id in current_ids
        if package.mode == "add" and exists:
            meta = "already exists; add mode will skip"
        elif exists:
            meta = "replace existing tag"
        else:
            meta = "add new tag"
        review_rows.append(
            {
                "id": f"registry:{tag_id}",
                "type": "tag",
                "title": tag_id,
                "meta": meta,
                "record_index": index,
                "selectable": not (package.mode == "add" and exists),
                "record_groups": {"tags": [tag_id]},
                "issues": [],
            }
        )
    return review_rows, tags


def selected_payload(records: list[Dict[str, Any]], selected: list[int], mode: str) -> tuple[Dict[str, Any], list[Dict[str, Any]], list[Dict[str, Any]]]:
    by_index = {index: record for index, record in enumerate(records)}
    skipped: list[Dict[str, Any]] = []
    selected_records: list[Dict[str, Any]] = []
    for index in selected:
        record = by_index.get(index)
        if record is None:
            skipped.append({"record_index": index, "reason": "missing_record", "message": "selected record is not present in staged file"})
            continue
        selected_records.append(record)
    if mode == "replace" and len(selected_records) != len(records):
        raise ValueError("registry replace mode requires selecting every returned tag row")
    return {"tags": selected_records}, skipped, [{"record_index": index, "tag_id": record["tag_id"]} for index, record in enumerate(records) if index in selected]


def apply(
    repo_root: Path,
    adapter: AdapterResolution,
    package: ReturnedPackage,
    body: Dict[str, Any],
    dry_run: bool,
    now_utc: str,
) -> Dict[str, Any]:
    selected = selected_record_indices(body.get("record_indices", []))
    selection_required(selected)
    confirmed = bool(body.get("confirm"))
    existing = load_current_registry(repo_root, adapter)
    review_rows, records = rows(existing, package)
    subset, skipped, selected_rows = selected_payload(records, selected, package.mode)
    updated_payload, stats = tag_registry_mutations.apply_registry_import(copy.deepcopy(existing), subset, package.mode, now_utc)
    changed = changed_from_stats(stats, ["added", "overwritten", "removed"])
    target_path = adapter_source_path(repo_root, adapter, "tag_registry")
    if confirmed and changed and not dry_run:
        tag_write_transactions.atomic_write_many({target_path: updated_payload})
    summary_text = tag_registry_mutations.build_import_summary_text(stats)
    payload: Dict[str, Any] = {
        "ok": True,
        "data_domain": adapter.data_domain,
        "adapter_id": adapter.adapter_id,
        "staged_filename": package.filename,
        "operation": "registry_apply",
        "tag_family": "registry",
        "mode": package.mode,
        "confirmed": confirmed,
        "dry_run": dry_run,
        "updated_at_utc": now_utc,
        "selected_records": selected_rows,
        "skipped": skipped,
        "errors": [],
        "warnings": [],
        "counts": {"selected": len(selected), "changed": int(changed), "skipped": len(skipped), "errors": 0, "warnings": 0, **stats},
        "written": bool(confirmed and changed and not dry_run),
        "requires_confirmation": bool(changed and not confirmed),
        "review_rows": review_rows,
        "summary_text": f"{'Updated' if confirmed and not dry_run else 'Validated'} tag registry changes: {summary_text}{' without writing' if not confirmed or dry_run else ''}.",
    }
    if payload["written"]:
        attach_apply_activity(
            repo_root,
            body,
            payload,
            record_groups={"tags": [row["tag_id"] for row in selected_rows], "files": [package.filename]},
            detail_items=[payload["summary_text"], f"Mode: {package.mode}; final tags: {stats.get('final_total')}."],
            status="completed",
        )
    return payload
