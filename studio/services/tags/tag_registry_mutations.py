#!/usr/bin/env python3
"""Plan focused canonical tag mutations."""

from __future__ import annotations

from typing import Any, Dict, Optional

from tags import tag_source_model as tag_source


MUTATE_ACTIONS = {"edit", "delete"}
PRIMARY_DOCUMENT_UNCHANGED = object()


def create_registry_tag(
    registry_payload: Dict[str, Any],
    *,
    group: Any,
    tag_id: Any,
    now_utc: str,
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """Plan one canonical tag addition without changing existing rows."""
    allowed_groups = tag_source.extract_allowed_groups(registry_payload)
    normalized_group = tag_source.sanitize_group(group, allowed_groups)
    normalized_tag_id = tag_source.sanitize_tag_id(tag_id)

    raw_tags = registry_payload.get("tags")
    if not isinstance(raw_tags, list):
        raise ValueError("registry tags must be an array")
    for raw_tag in raw_tags:
        if not isinstance(raw_tag, dict):
            continue
        existing_tag_id = str(raw_tag.get("tag_id") or "").strip().lower()
        if existing_tag_id == normalized_tag_id:
            raise ValueError(f"tag_id already exists: {normalized_tag_id}")

    created_row = {
        "tag_id": normalized_tag_id,
        "group": normalized_group,
        "updated_at_utc": now_utc,
    }
    updated_payload = dict(registry_payload)
    updated_payload.setdefault("tag_registry_version", tag_source.TAG_REGISTRY_VERSION)
    if not isinstance(updated_payload.get("policy"), dict):
        updated_payload["policy"] = {"allowed_groups": allowed_groups}
    updated_payload["tags"] = [*raw_tags, created_row]
    updated_payload["updated_at_utc"] = now_utc

    return updated_payload, {
        "action": "create",
        "tag_id": normalized_tag_id,
        "group": normalized_group,
        "primary_document": None,
        "added": 1,
        "final_total": len(updated_payload["tags"]),
    }


def mutate_registry_tag(
    registry_payload: Dict[str, Any],
    action: str,
    old_tag_id: str,
    now_utc: str,
    new_tag_id: Optional[str] = None,
    new_group: Optional[str] = None,
    new_primary_document: Any = PRIMARY_DOCUMENT_UNCHANGED,
    allow_canonical_rename: bool = False,
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    if action not in MUTATE_ACTIONS:
        raise ValueError(f"action must be one of: {sorted(MUTATE_ACTIONS)}")

    tag_source.validate_registry_payload(registry_payload)
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

    allowed_groups = tag_source.extract_allowed_groups(registry_payload)
    group = tag_source.sanitize_group(target_row.get("group"), allowed_groups, "group")
    primary_document = (
        tag_source.sanitize_primary_document(
            target_row.get("primary_document"),
            "primary_document",
        )
        if "primary_document" in target_row
        else None
    )

    if action == "delete":
        final_tags = [row for idx, row in enumerate(tags) if idx != target_idx]
        registry_payload["tags"] = final_tags
        registry_payload["updated_at_utc"] = now_utc
        if "tag_registry_version" not in registry_payload:
            registry_payload["tag_registry_version"] = tag_source.TAG_REGISTRY_VERSION
        return registry_payload, {
            "action": "delete",
            "old_tag_id": old_tag_id,
            "new_tag_id": None,
            "group": group,
        }

    normalized_new_tag_id = (
        old_tag_id
        if new_tag_id is None
        else tag_source.sanitize_tag_id(new_tag_id, "new_tag_id")
    )
    normalized_new_group = (
        group
        if new_group is None
        else tag_source.sanitize_group(new_group, allowed_groups, "new_group")
    )
    normalized_new_primary_document = (
        primary_document
        if new_primary_document is PRIMARY_DOCUMENT_UNCHANGED
        else tag_source.sanitize_primary_document(
            new_primary_document,
            "primary_document",
        )
    )
    canonical_changed = normalized_new_tag_id != old_tag_id
    group_changed = normalized_new_group != group
    primary_document_changed = normalized_new_primary_document != primary_document
    if canonical_changed and not allow_canonical_rename:
        raise ValueError("canonical rename is disabled for this request")
    if canonical_changed and normalized_new_tag_id in existing_ids:
        raise ValueError(f"target tag_id already exists: {normalized_new_tag_id}")
    updated_row = dict(target_row)
    updated_row.pop("label", None)
    updated_row["tag_id"] = normalized_new_tag_id
    updated_row["group"] = normalized_new_group
    if normalized_new_primary_document is None:
        updated_row.pop("primary_document", None)
    else:
        updated_row["primary_document"] = normalized_new_primary_document
    updated_row["updated_at_utc"] = now_utc
    final_tags = list(tags)
    final_tags[target_idx] = updated_row

    registry_payload["tags"] = final_tags
    registry_payload["updated_at_utc"] = now_utc
    if "tag_registry_version" not in registry_payload:
        registry_payload["tag_registry_version"] = tag_source.TAG_REGISTRY_VERSION

    tag_source.validate_registry_payload(registry_payload)
    return registry_payload, {
        "action": "edit",
        "old_tag_id": old_tag_id,
        "new_tag_id": normalized_new_tag_id,
        "group": normalized_new_group,
        "primary_document": normalized_new_primary_document,
        "canonical_changed": canonical_changed,
        "group_changed": group_changed,
        "primary_document_changed": primary_document_changed,
    }


def rewrite_assignment_tag_list_for_tag(
    raw_tags: Any,
    field_name: str,
    old_tag_id: str,
    new_tag_id: Optional[str],
) -> tuple[list[Dict[str, Any]], bool, int]:
    tags = raw_tags if isinstance(raw_tags, list) else []
    changed = not isinstance(raw_tags, list)
    out: list[Dict[str, Any]] = []
    seen: set[str] = set()
    refs_rewritten = 0

    for raw_tag in tags:
        normalized_tag = tag_source.normalize_assignment_tag(raw_tag, f"{field_name}[*]", strict=False)
        if normalized_tag is None:
            changed = True
            continue

        tag_value = normalized_tag["tag_id"]
        if tag_value == old_tag_id:
            refs_rewritten += 1
            changed = True
            if new_tag_id is None:
                continue
            tag_value = new_tag_id
        if tag_value in seen:
            changed = True
            continue
        seen.add(tag_value)
        out.append(
            tag_source.build_assignment_tag(
                tag_value,
                normalized_tag["w_manual"],
                normalized_tag.get("alias", ""),
            )
        )

    return out, changed, refs_rewritten


def rewrite_assignments_for_tag(
    assignments_payload: Dict[str, Any],
    old_tag_id: str,
    new_tag_id: Optional[str],
    now_utc: str,
) -> tuple[Dict[str, Any], Dict[str, int]]:
    series_obj = assignments_payload.get("series")
    if not isinstance(series_obj, dict):
        series_obj = {}
        assignments_payload["series"] = series_obj
    if "tag_assignments_version" not in assignments_payload:
        assignments_payload["tag_assignments_version"] = tag_source.TAG_ASSIGNMENTS_VERSION

    series_rows_touched = 0
    series_refs_rewritten = 0
    work_rows_touched = 0
    work_refs_rewritten = 0

    for series_id, row in series_obj.items():
        if not isinstance(row, dict):
            continue
        series_out, series_changed, series_refs = rewrite_assignment_tag_list_for_tag(
            row.get("tags"),
            f"series[{series_id}].tags",
            old_tag_id,
            new_tag_id,
        )
        if series_changed:
            row["tags"] = series_out
            row["updated_at_utc"] = now_utc
            series_rows_touched += 1
        series_refs_rewritten += series_refs

        works_obj = row.get("works")
        if not isinstance(works_obj, dict):
            continue
        for work_id, work_row in list(works_obj.items()):
            if not isinstance(work_row, dict):
                continue
            work_out, work_changed, work_refs = rewrite_assignment_tag_list_for_tag(
                work_row.get("tags"),
                f"series[{series_id}].works[{work_id}].tags",
                old_tag_id,
                new_tag_id,
            )
            if work_changed:
                if work_out:
                    work_row["tags"] = work_out
                    work_row["updated_at_utc"] = now_utc
                else:
                    del works_obj[work_id]
                row["updated_at_utc"] = now_utc
                work_rows_touched += 1
            work_refs_rewritten += work_refs
        if not works_obj:
            row.pop("works", None)

    assignments_payload["updated_at_utc"] = now_utc
    return assignments_payload, {
        "series_rows_touched": series_rows_touched,
        "series_tag_refs_rewritten": series_refs_rewritten,
        "work_rows_touched": work_rows_touched,
        "work_tag_refs_rewritten": work_refs_rewritten,
    }


def build_create_summary_text(stats: Dict[str, Any]) -> str:
    tag_id = str(stats.get("tag_id") or "")
    final_total = int(stats.get("final_total") or 0)
    return f"created tag {tag_id}; no document association; final {final_total}"


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
    group_changed = 1 if bool(stats.get("group_changed")) else 0
    primary_document_changed = 1 if bool(stats.get("primary_document_changed")) else 0

    id_part = f"{old_tag_id} -> {new_tag_id}" if new_tag_id else old_tag_id
    return (
        f"mode {action}; tag {id_part}; "
        f"group_changed {group_changed}; "
        f"primary_document_changed {primary_document_changed}; "
        f"series rows {series_rows}; series refs {series_refs}; "
        f"work rows {work_rows}; work refs {work_refs}; "
        f"aliases rewritten {alias_rw}; aliases removed-empty {alias_empty}; "
        f"aliases removed-redundant {alias_redundant}"
    )
