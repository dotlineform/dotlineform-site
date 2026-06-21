#!/usr/bin/env python3
"""Aliases family behavior for Analytics tags Data Sharing."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Dict

from data_sharing_adapters import AdapterResolution
from tag_services import tag_alias_mutations, tag_registry_mutations, tag_source_model, tag_write_transactions

from ..context import (
    adapter_source_path,
    attach_apply_activity,
    changed_from_stats,
    load_current_aliases,
    package_metadata,
    selected_record_indices,
    selection_required,
    source_files,
)
from ..returned import ReturnedPackage


def alias_keys_from_payload(aliases_payload: dict[str, Any]) -> list[str]:
    aliases = aliases_payload.get("aliases") if isinstance(aliases_payload.get("aliases"), dict) else {}
    return sorted(str(key).strip() for key in aliases.keys() if str(key).strip())


def build_package(repo_root: Path, adapter: AdapterResolution, config_id: str, generated_at_utc: str) -> tuple[Dict[str, Any], Dict[str, int], Dict[str, list[str]]]:
    aliases = load_current_aliases(repo_root, adapter)
    aliases_obj = aliases.get("aliases") if isinstance(aliases.get("aliases"), dict) else {}
    tag_ids = sorted(
        {
            str(tag_id).strip()
            for entry in aliases_obj.values()
            if isinstance(entry, dict)
            for tag_id in (entry.get("tags") if isinstance(entry.get("tags"), list) else [])
            if str(tag_id).strip()
        }
    )
    counts = {"aliases": len(aliases_obj), "tags": len(tag_ids)}
    payload = {
        "package_metadata": package_metadata(
            adapter=adapter,
            config_id=config_id,
            family="aliases",
            generated_at_utc=generated_at_utc,
            source_paths=source_files(repo_root, adapter, "aliases"),
            counts=counts,
        ),
        "aliases": copy.deepcopy(aliases_obj),
    }
    return payload, counts, {"aliases": alias_keys_from_payload(aliases), "tags": tag_ids}


def rows(package: ReturnedPackage) -> tuple[list[Dict[str, Any]], list[tuple[str, Dict[str, Any]]]]:
    order, aliases = tag_source_model.sanitize_import_aliases(package.import_payload)
    review_rows: list[Dict[str, Any]] = []
    records: list[tuple[str, Dict[str, Any]]] = []
    for index, alias_key in enumerate(order):
        entry = aliases[alias_key]
        tags = [str(item) for item in entry.get("tags", [])]
        records.append((alias_key, entry))
        review_rows.append(
            {
                "id": f"alias:{alias_key}",
                "type": "alias",
                "title": alias_key,
                "meta": f"{len(tags)} target tag(s)",
                "record_index": index,
                "selectable": True,
                "record_groups": {"aliases": [alias_key], "tags": tags},
                "issues": [],
            }
        )
    return review_rows, records


def selected_payload(records: list[tuple[str, Dict[str, Any]]], selected: list[int], mode: str) -> tuple[Dict[str, Any], list[Dict[str, Any]], list[Dict[str, Any]]]:
    by_index = {index: record for index, record in enumerate(records)}
    skipped: list[Dict[str, Any]] = []
    selected_aliases: Dict[str, Dict[str, Any]] = {}
    selected_rows: list[Dict[str, Any]] = []
    for index in selected:
        record = by_index.get(index)
        if record is None:
            skipped.append({"record_index": index, "reason": "missing_record", "message": "selected record is not present in staged file"})
            continue
        alias_key, entry = record
        selected_aliases[alias_key] = entry
        selected_rows.append({"record_index": index, "alias": alias_key})
    if mode == "replace" and len(selected_aliases) != len(records):
        raise ValueError("aliases replace mode requires selecting every returned alias row")
    return {"aliases": selected_aliases}, skipped, selected_rows


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
    existing = load_current_aliases(repo_root, adapter)
    review_rows, records = rows(package)
    subset, skipped, selected_rows = selected_payload(records, selected, package.mode)
    updated_payload, stats = tag_alias_mutations.apply_aliases_import(copy.deepcopy(existing), subset, package.mode, now_utc)
    changed = changed_from_stats(stats, ["added", "overwritten", "removed"])
    target_path = adapter_source_path(repo_root, adapter, "tag_aliases")
    if confirmed and changed and not dry_run:
        tag_write_transactions.atomic_write_many({target_path: updated_payload})
    summary_text = tag_registry_mutations.build_import_summary_text(stats, noun="aliases")
    selected_alias_keys = [row["alias"] for row in selected_rows]
    selected_tags = sorted(
        {
            tag_id
            for row in review_rows
            if row.get("record_index") in selected
            for tag_id in row.get("record_groups", {}).get("tags", [])
        }
    )
    payload: Dict[str, Any] = {
        "ok": True,
        "data_domain": adapter.data_domain,
        "adapter_id": adapter.adapter_id,
        "staged_filename": package.filename,
        "operation": "aliases_apply",
        "tag_family": "aliases",
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
        "summary_text": f"{'Updated' if confirmed and not dry_run else 'Validated'} tag alias changes: {summary_text}{' without writing' if not confirmed or dry_run else ''}.",
    }
    if payload["written"]:
        attach_apply_activity(
            repo_root,
            body,
            payload,
            record_groups={"aliases": selected_alias_keys, "tags": selected_tags, "files": [package.filename]},
            detail_items=[payload["summary_text"], f"Mode: {package.mode}; final aliases: {stats.get('final_total')}."],
            status="completed",
        )
    return payload
