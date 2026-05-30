#!/usr/bin/env python3
"""Plan tag alias promotion and canonical tag demotion mutations."""

from __future__ import annotations

from typing import Any, Dict

from tag_services import tag_alias_mutations as tag_aliases
from tag_services import tag_source_model as tag_source


def rewrite_assignment_tag_list_for_targets(
    raw_tags: Any,
    field_name: str,
    old_tag_id: str,
    replacement_tag_ids: list[str],
) -> tuple[list[Dict[str, Any]], bool, int, int]:
    tags = raw_tags if isinstance(raw_tags, list) else []
    changed = not isinstance(raw_tags, list)
    out: list[Dict[str, Any]] = []
    seen: set[str] = set()
    refs_rewritten = 0
    targets_inserted = 0

    for raw_tag in tags:
        normalized_tag = tag_source.normalize_assignment_tag(raw_tag, f"{field_name}[*]", strict=False)
        if normalized_tag is None:
            changed = True
            continue

        tag_value = normalized_tag["tag_id"]
        if tag_value == old_tag_id:
            refs_rewritten += 1
            changed = True
            for replacement in replacement_tag_ids:
                if replacement in seen:
                    continue
                seen.add(replacement)
                out.append(tag_source.build_assignment_tag(replacement, normalized_tag["w_manual"]))
                targets_inserted += 1
            continue
        if tag_value in seen:
            changed = True
            continue
        seen.add(tag_value)
        out.append(normalized_tag)

    return out, changed, refs_rewritten, targets_inserted


def rewrite_assignments_for_targets(
    assignments_payload: Dict[str, Any],
    old_tag_id: str,
    replacement_tag_ids: list[str],
    now_utc: str,
) -> tuple[Dict[str, Any], Dict[str, int], bool]:
    series_obj = assignments_payload.get("series")
    if not isinstance(series_obj, dict):
        series_obj = {}
        assignments_payload["series"] = series_obj
    if "tag_assignments_version" not in assignments_payload:
        assignments_payload["tag_assignments_version"] = "tag_assignments_v1"

    series_rows_touched = 0
    series_refs_rewritten = 0
    series_targets_inserted = 0
    work_rows_touched = 0
    work_refs_rewritten = 0
    work_targets_inserted = 0

    for series_id, row in series_obj.items():
        if not isinstance(row, dict):
            continue
        series_out, series_changed, series_refs, series_inserted = rewrite_assignment_tag_list_for_targets(
            row.get("tags"),
            f"series[{series_id}].tags",
            old_tag_id,
            replacement_tag_ids,
        )
        if series_changed:
            row["tags"] = series_out
            row["updated_at_utc"] = now_utc
            series_rows_touched += 1
        series_refs_rewritten += series_refs
        series_targets_inserted += series_inserted

        works_obj = row.get("works")
        if not isinstance(works_obj, dict):
            continue
        for work_id, work_row in list(works_obj.items()):
            if not isinstance(work_row, dict):
                continue
            work_out, work_changed, work_refs, work_inserted = rewrite_assignment_tag_list_for_targets(
                work_row.get("tags"),
                f"series[{series_id}].works[{work_id}].tags",
                old_tag_id,
                replacement_tag_ids,
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
            work_targets_inserted += work_inserted
        if not works_obj:
            row.pop("works", None)

    assignments_changed = (series_rows_touched + work_rows_touched) > 0
    if assignments_changed:
        assignments_payload["updated_at_utc"] = now_utc

    return assignments_payload, {
        "series_rows_touched": series_rows_touched,
        "series_tag_refs_rewritten": series_refs_rewritten,
        "series_targets_inserted": series_targets_inserted,
        "work_rows_touched": work_rows_touched,
        "work_tag_refs_rewritten": work_refs_rewritten,
        "work_targets_inserted": work_targets_inserted,
    }, assignments_changed


def promote_alias_to_canonical_tag(
    registry_payload: Dict[str, Any],
    aliases_payload: Dict[str, Any],
    alias_key: str,
    group: str,
    now_utc: str,
) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], bool, bool]:
    raw_tags = registry_payload.get("tags")
    tags = raw_tags if isinstance(raw_tags, list) else []

    existing_tag_ids: set[str] = set()
    for raw in tags:
        if not isinstance(raw, dict):
            continue
        tag_id = str(raw.get("tag_id") or "").strip().lower()
        if tag_id:
            existing_tag_ids.add(tag_id)

    raw_aliases = aliases_payload.get("aliases")
    aliases = raw_aliases if isinstance(raw_aliases, dict) else {}
    final_aliases: Dict[str, Dict[str, Any]] = {}
    alias_found = False
    for idx, (raw_key, raw_value) in enumerate(aliases.items()):
        key = tag_source.sanitize_alias_key(raw_key, idx)
        value = tag_source.sanitize_alias_entry(raw_value, key, "tag_aliases.aliases")
        if key == alias_key:
            alias_found = True
            continue
        final_aliases[key] = value

    if not alias_found:
        raise ValueError(f"alias not found: {alias_key}")

    new_tag_id = f"{group}:{alias_key}"
    canonical_exists = new_tag_id in existing_tag_ids
    canonical_added = 0
    registry_changed = False
    if not canonical_exists:
        if "tag_registry_version" not in registry_payload:
            registry_payload["tag_registry_version"] = "tag_registry_v1"
        if not isinstance(registry_payload.get("policy"), dict):
            registry_payload["policy"] = {"allowed_groups": list(tag_source.DEFAULT_ALLOWED_GROUPS)}
        appended_tags = list(tags)
        appended_tags.append(
            {
                "tag_id": new_tag_id,
                "group": group,
                "label": alias_key,
                "status": "active",
                "description": "",
                "updated_at_utc": now_utc,
            }
        )
        registry_payload["tags"] = appended_tags
        registry_payload["updated_at_utc"] = now_utc
        canonical_added = 1
        registry_changed = True

    if "tag_aliases_version" not in aliases_payload:
        aliases_payload["tag_aliases_version"] = "tag_aliases_v1"
    aliases_payload["aliases"] = final_aliases
    aliases_payload["updated_at_utc"] = now_utc
    aliases_changed = True

    stats: Dict[str, Any] = {
        "action": "promote_alias",
        "alias": alias_key,
        "group": group,
        "new_tag_id": new_tag_id,
        "canonical_exists": canonical_exists,
        "canonical_added": canonical_added,
        "alias_deleted": 1,
        "registry_final_total": len(registry_payload.get("tags", [])) if isinstance(registry_payload.get("tags"), list) else 0,
        "aliases_final_total": len(final_aliases),
    }
    return registry_payload, aliases_payload, stats, registry_changed, aliases_changed


def demote_tag_to_alias(
    registry_payload: Dict[str, Any],
    aliases_payload: Dict[str, Any],
    assignments_payload: Dict[str, Any],
    old_tag_id: str,
    alias_targets: list[str],
    now_utc: str,
) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any], bool]:
    raw_tags = registry_payload.get("tags")
    tags = raw_tags if isinstance(raw_tags, list) else []

    target_idx = -1
    existing_tag_ids: set[str] = set()
    for idx, raw in enumerate(tags):
        if not isinstance(raw, dict):
            continue
        tag_id = str(raw.get("tag_id") or "").strip().lower()
        if not tag_id:
            continue
        existing_tag_ids.add(tag_id)
        if tag_id == old_tag_id:
            target_idx = idx

    if target_idx < 0:
        raise ValueError(f"tag not found in registry: {old_tag_id}")

    for idx, target in enumerate(alias_targets):
        if target == old_tag_id:
            raise ValueError("alias_targets must not include the demoted tag_id")
        if target not in existing_tag_ids:
            raise ValueError(f"alias_targets[{idx}] is not present in registry: {target}")

    demoted_alias_key = old_tag_id.split(":", 1)[1]

    final_tags = [row for idx, row in enumerate(tags) if idx != target_idx]
    if "tag_registry_version" not in registry_payload:
        registry_payload["tag_registry_version"] = "tag_registry_v1"
    if not isinstance(registry_payload.get("policy"), dict):
        registry_payload["policy"] = {"allowed_groups": list(tag_source.DEFAULT_ALLOWED_GROUPS)}
    registry_payload["tags"] = final_tags
    registry_payload["updated_at_utc"] = now_utc

    aliases_updated, alias_stats = tag_aliases.rewrite_aliases_for_targets(
        aliases_payload,
        old_tag_id=old_tag_id,
        replacement_tag_ids=alias_targets,
        demoted_alias_key=demoted_alias_key,
        now_utc=now_utc,
    )

    assignments_updated, assignment_stats, assignments_changed = rewrite_assignments_for_targets(
        assignments_payload,
        old_tag_id=old_tag_id,
        replacement_tag_ids=alias_targets,
        now_utc=now_utc,
    )

    stats: Dict[str, Any] = {
        "action": "demote_tag",
        "old_tag_id": old_tag_id,
        "alias_key": demoted_alias_key,
        "alias_targets": list(alias_targets),
        "alias_targets_count": len(alias_targets),
        "registry_final_total": len(final_tags),
        **alias_stats,
        **assignment_stats,
    }
    return registry_payload, aliases_updated, assignments_updated, stats, assignments_changed


def build_promote_summary_text(stats: Dict[str, Any]) -> str:
    alias = str(stats.get("alias") or "")
    new_tag_id = str(stats.get("new_tag_id") or "")
    canonical_added = int(stats.get("canonical_added") or 0)
    alias_deleted = int(stats.get("alias_deleted") or 0)
    reg_total = int(stats.get("registry_final_total") or 0)
    aliases_total = int(stats.get("aliases_final_total") or 0)
    return (
        f"mode promote_alias; {alias} -> {new_tag_id}; "
        f"canonical_added {canonical_added}; alias_deleted {alias_deleted}; "
        f"registry final {reg_total}; aliases final {aliases_total}"
    )


def build_demote_summary_text(stats: Dict[str, Any]) -> str:
    old_tag_id = str(stats.get("old_tag_id") or "")
    alias_key = str(stats.get("alias_key") or "")
    targets_count = int(stats.get("alias_targets_count") or 0)
    series_rows = int(stats.get("series_rows_touched") or 0)
    series_refs = int(stats.get("series_tag_refs_rewritten") or 0)
    work_rows = int(stats.get("work_rows_touched") or 0)
    work_refs = int(stats.get("work_tag_refs_rewritten") or 0)
    alias_refs = int(stats.get("alias_tag_refs_rewritten") or 0)
    aliases_rw = int(stats.get("aliases_rewritten") or 0)
    return (
        f"mode demote_tag; {old_tag_id} -> alias {alias_key}; "
        f"targets {targets_count}; series rows {series_rows}; "
        f"series refs {series_refs}; work rows {work_rows}; work refs {work_refs}; "
        f"alias refs {alias_refs}; aliases rewritten {aliases_rw}"
    )
