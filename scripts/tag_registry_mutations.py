#!/usr/bin/env python3
"""Plan tag registry imports and canonical tag mutations."""

from __future__ import annotations

from typing import Any, Dict, Optional

import tag_source_model as tag_source


MUTATE_ACTIONS = {"edit", "delete"}


def apply_registry_import(
    existing_payload: Dict[str, Any],
    import_registry: Any,
    mode: str,
    now_utc: str,
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    if mode not in {"replace", "merge", "add"}:
        raise ValueError("mode must be one of: replace, merge, add")

    allowed_groups = tag_source.extract_allowed_groups(existing_payload)
    imported_tags = tag_source.sanitize_import_registry(import_registry, allowed_groups)

    raw_existing_tags = existing_payload.get("tags")
    existing_tags = raw_existing_tags if isinstance(raw_existing_tags, list) else []

    existing_by_id: dict[str, Dict[str, Any]] = {}
    for raw in existing_tags:
        if not isinstance(raw, dict):
            continue
        tag_id = str(raw.get("tag_id") or "").strip().lower()
        if not tag_id:
            continue
        existing_by_id[tag_id] = raw

    import_order = [tag["tag_id"] for tag in imported_tags]
    import_by_id = {tag["tag_id"]: tag for tag in imported_tags}

    overwritten = 0
    added = 0
    unchanged = 0
    removed = 0

    if mode == "replace":
        existing_ids = set(existing_by_id.keys())
        imported_ids = set(import_by_id.keys())
        overwritten = len(existing_ids & imported_ids)
        added = len(imported_ids - existing_ids)
        removed = len(existing_ids - imported_ids)
        final_tags: list[Any] = []
        for tag_id in import_order:
            tag = dict(import_by_id[tag_id])
            tag["updated_at_utc"] = now_utc
            final_tags.append(tag)
    elif mode == "merge":
        final_tags = []
        remaining_import = dict(import_by_id)
        for existing_tag in existing_tags:
            if not isinstance(existing_tag, dict):
                unchanged += 1
                final_tags.append(existing_tag)
                continue

            existing_tag_id = str(existing_tag.get("tag_id") or "").strip().lower()
            if existing_tag_id and existing_tag_id in remaining_import:
                overwritten += 1
                incoming = dict(remaining_import.pop(existing_tag_id))
                incoming["updated_at_utc"] = now_utc
                final_tags.append(incoming)
            else:
                unchanged += 1
                final_tags.append(existing_tag)

        for tag_id in import_order:
            if tag_id not in remaining_import:
                continue
            added += 1
            incoming = dict(remaining_import.pop(tag_id))
            incoming["updated_at_utc"] = now_utc
            final_tags.append(incoming)
    else:  # mode == "add"
        final_tags = list(existing_tags)
        existing_ids = set(existing_by_id.keys())
        for tag_id in import_order:
            if tag_id in existing_ids:
                unchanged += 1
                continue
            incoming = dict(import_by_id[tag_id])
            incoming["updated_at_utc"] = now_utc
            final_tags.append(incoming)
            added += 1

    if "tag_registry_version" not in existing_payload:
        existing_payload["tag_registry_version"] = "tag_registry_v1"
    if not isinstance(existing_payload.get("policy"), dict):
        existing_payload["policy"] = {"allowed_groups": allowed_groups}

    existing_payload["tags"] = final_tags
    existing_payload["updated_at_utc"] = now_utc

    stats = {
        "mode": mode,
        "imported_total": len(imported_tags),
        "overwritten": overwritten,
        "added": added,
        "unchanged": unchanged,
        "removed": removed,
        "final_total": len(final_tags),
    }
    return existing_payload, stats


def mutate_registry_tag(
    registry_payload: Dict[str, Any],
    action: str,
    old_tag_id: str,
    now_utc: str,
    new_slug: Optional[str] = None,
    new_description: Optional[str] = None,
    allow_canonical_rename: bool = False,
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    if action not in MUTATE_ACTIONS:
        raise ValueError(f"action must be one of: {sorted(MUTATE_ACTIONS)}")

    raw_tags = registry_payload.get("tags")
    tags = raw_tags if isinstance(raw_tags, list) else []
    target_idx = -1
    target_row: Dict[str, Any] | None = None
    existing_ids: set[str] = set()

    for idx, raw in enumerate(tags):
        if not isinstance(raw, dict):
            continue
        tag_id = str(raw.get("tag_id") or "").strip().lower()
        if not tag_id:
            continue
        existing_ids.add(tag_id)
        if tag_id == old_tag_id:
            target_idx = idx
            target_row = raw

    if target_idx < 0 or target_row is None:
        raise ValueError(f"tag not found in registry: {old_tag_id}")

    group = str(target_row.get("group") or "").strip().lower()
    if not group or ":" not in old_tag_id:
        raise ValueError(f"invalid target registry row for: {old_tag_id}")
    old_group = old_tag_id.split(":", 1)[0]
    if group != old_group:
        raise ValueError(f"registry group mismatch for tag: {old_tag_id}")

    if action == "delete":
        final_tags = [row for idx, row in enumerate(tags) if idx != target_idx]
        registry_payload["tags"] = final_tags
        registry_payload["updated_at_utc"] = now_utc
        if "tag_registry_version" not in registry_payload:
            registry_payload["tag_registry_version"] = "tag_registry_v1"
        return registry_payload, {
            "action": "delete",
            "old_tag_id": old_tag_id,
            "new_tag_id": None,
            "group": group,
            "label": str(target_row.get("label") or "").strip(),
        }

    old_slug = old_tag_id.split(":", 1)[1]
    slug = old_slug if new_slug is None else tag_source.sanitize_slug(new_slug, "new_slug")
    label = slug
    new_tag_id = f"{group}:{slug}"
    canonical_changed = new_tag_id != old_tag_id
    if canonical_changed and not allow_canonical_rename:
        raise ValueError("canonical rename is disabled for this request")
    if canonical_changed and new_tag_id in existing_ids:
        raise ValueError(f"target tag_id already exists: {new_tag_id}")
    old_description = str(target_row.get("description") or "").strip()
    description = old_description if new_description is None else tag_source.sanitize_alias_description(new_description, "description")
    description_changed = description != old_description

    updated_row = dict(target_row)
    updated_row["label"] = label
    updated_row["tag_id"] = new_tag_id
    updated_row["description"] = description
    updated_row["updated_at_utc"] = now_utc
    final_tags = list(tags)
    final_tags[target_idx] = updated_row

    registry_payload["tags"] = final_tags
    registry_payload["updated_at_utc"] = now_utc
    if "tag_registry_version" not in registry_payload:
        registry_payload["tag_registry_version"] = "tag_registry_v1"

    return registry_payload, {
        "action": "edit",
        "old_tag_id": old_tag_id,
        "new_tag_id": new_tag_id,
        "group": group,
        "label": label,
        "canonical_changed": canonical_changed,
        "description_changed": description_changed,
    }


def build_import_summary_text(stats: Dict[str, Any], noun: str = "tags") -> str:
    mode = str(stats.get("mode") or "unknown")
    imported_total = int(stats.get("imported_total") or 0)
    added = int(stats.get("added") or 0)
    overwritten = int(stats.get("overwritten") or 0)
    unchanged = int(stats.get("unchanged") or 0)
    removed = int(stats.get("removed") or 0)
    final_total = int(stats.get("final_total") or 0)
    return (
        f"mode {mode}; Imported {imported_total} {noun}; "
        f"added {added}; overwritten {overwritten}; "
        f"unchanged {unchanged}; removed {removed}; final {final_total}"
    )


def build_mutation_summary_text(stats: Dict[str, Any]) -> str:
    action = str(stats.get("action") or "unknown")
    old_tag_id = str(stats.get("old_tag_id") or "")
    new_tag_id = str(stats.get("new_tag_id") or "")
    series_rows = int(stats.get("series_rows_touched") or 0)
    series_refs = int(stats.get("series_tag_refs_rewritten") or 0)
    work_rows = int(stats.get("work_rows_touched") or 0)
    work_refs = int(stats.get("work_tag_refs_rewritten") or 0)
    alias_rw = int(stats.get("aliases_rewritten") or 0)
    alias_empty = int(stats.get("aliases_removed_empty") or 0)
    alias_redundant = int(stats.get("aliases_removed_redundant") or 0)
    description_changed = 1 if bool(stats.get("description_changed")) else 0

    id_part = f"{old_tag_id} -> {new_tag_id}" if new_tag_id else old_tag_id
    return (
        f"mode {action}; tag {id_part}; "
        f"description_changed {description_changed}; "
        f"series rows {series_rows}; series refs {series_refs}; "
        f"work rows {work_rows}; work refs {work_refs}; "
        f"aliases rewritten {alias_rw}; aliases removed-empty {alias_empty}; "
        f"aliases removed-redundant {alias_redundant}"
    )
