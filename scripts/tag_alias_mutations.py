#!/usr/bin/env python3
"""Plan tag alias imports, edits, deletes, and target rewrites."""

from __future__ import annotations

from typing import Any, Dict, Optional

import tag_source_model as tag_source


def apply_aliases_import(
    existing_payload: Dict[str, Any],
    import_aliases_payload: Any,
    mode: str,
    now_utc: str,
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    if mode not in {"replace", "merge", "add"}:
        raise ValueError("mode must be one of: replace, merge, add")

    import_order, import_by_key = tag_source.sanitize_import_aliases(import_aliases_payload)
    raw_existing_aliases = existing_payload.get("aliases")
    existing_aliases = raw_existing_aliases if isinstance(raw_existing_aliases, dict) else {}

    existing_order: list[str] = []
    existing_by_key: Dict[str, Dict[str, Any]] = {}
    for idx, (raw_key, raw_value) in enumerate(existing_aliases.items()):
        alias_key = tag_source.sanitize_alias_key(raw_key, idx)
        alias_value = tag_source.sanitize_alias_entry(raw_value, alias_key, "tag_aliases.aliases")
        if alias_key not in existing_by_key:
            existing_order.append(alias_key)
        existing_by_key[alias_key] = alias_value

    overwritten = 0
    added = 0
    unchanged = 0
    removed = 0
    final_aliases: Dict[str, Dict[str, Any]] = {}

    if mode == "replace":
        existing_keys = set(existing_by_key.keys())
        import_keys = set(import_by_key.keys())
        overwritten = len(existing_keys & import_keys)
        added = len(import_keys - existing_keys)
        removed = len(existing_keys - import_keys)
        for key in import_order:
            final_aliases[key] = import_by_key[key]
    elif mode == "merge":
        remaining_import = dict(import_by_key)
        for key in existing_order:
            if key in remaining_import:
                overwritten += 1
                final_aliases[key] = remaining_import.pop(key)
            else:
                unchanged += 1
                final_aliases[key] = existing_by_key[key]
        for key in import_order:
            if key not in remaining_import:
                continue
            added += 1
            final_aliases[key] = remaining_import.pop(key)
    else:  # mode == "add"
        for key in existing_order:
            final_aliases[key] = existing_by_key[key]
        existing_keys = set(existing_by_key.keys())
        for key in import_order:
            if key in existing_keys:
                unchanged += 1
                continue
            added += 1
            final_aliases[key] = import_by_key[key]

    if "tag_aliases_version" not in existing_payload:
        existing_payload["tag_aliases_version"] = "tag_aliases_v1"
    existing_payload["aliases"] = final_aliases
    existing_payload["updated_at_utc"] = now_utc

    stats = {
        "mode": mode,
        "imported_total": len(import_order),
        "overwritten": overwritten,
        "added": added,
        "unchanged": unchanged,
        "removed": removed,
        "final_total": len(final_aliases),
    }
    return existing_payload, stats


def delete_alias_key(
    aliases_payload: Dict[str, Any],
    alias_key: str,
    now_utc: str,
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    raw_aliases = aliases_payload.get("aliases")
    aliases = raw_aliases if isinstance(raw_aliases, dict) else {}

    normalized_aliases: Dict[str, Dict[str, Any]] = {}
    found = False
    for idx, (raw_key, raw_value) in enumerate(aliases.items()):
        key = tag_source.sanitize_alias_key(raw_key, idx)
        value = tag_source.sanitize_alias_entry(raw_value, key, "tag_aliases.aliases")
        if key == alias_key:
            found = True
            continue
        normalized_aliases[key] = value

    if not found:
        raise ValueError(f"alias not found: {alias_key}")

    if "tag_aliases_version" not in aliases_payload:
        aliases_payload["tag_aliases_version"] = "tag_aliases_v1"
    aliases_payload["aliases"] = normalized_aliases
    aliases_payload["updated_at_utc"] = now_utc

    return aliases_payload, {
        "alias": alias_key,
        "final_total": len(normalized_aliases),
    }


def build_alias_entry(description: str, tags: list[str]) -> Dict[str, Any]:
    tag_source.enforce_alias_group_constraints(tags, "alias.tags")
    return {"description": description.strip(), "tags": list(tags)}


def replace_alias_entry_refs(
    alias_entry: Dict[str, Any],
    old_tag_id: str,
    replacement_tag_ids: list[str],
) -> tuple[Dict[str, Any], bool, int]:
    original_tags = tag_source.sanitize_tag_id_list(alias_entry.get("tags"), "tag_aliases.aliases[*].tags")
    description = tag_source.sanitize_alias_description(alias_entry.get("description", ""), "tag_aliases.aliases[*].description")

    out: list[str] = []
    seen: set[str] = set()
    replaced_refs = 0
    for item in original_tags:
        if item == old_tag_id:
            replaced_refs += 1
            for replacement in replacement_tag_ids:
                if replacement in seen:
                    continue
                seen.add(replacement)
                out.append(replacement)
            continue
        if item in seen:
            continue
        seen.add(item)
        out.append(item)

    if not out:
        out = list(replacement_tag_ids)
    tag_source.enforce_alias_group_constraints(out, "tag_aliases.aliases[*].tags")

    updated_entry = build_alias_entry(description, out)
    changed = (
        updated_entry.get("description") != description
        or updated_entry.get("tags") != original_tags
    )
    return updated_entry, changed, replaced_refs


def rewrite_aliases_for_targets(
    aliases_payload: Dict[str, Any],
    old_tag_id: str,
    replacement_tag_ids: list[str],
    demoted_alias_key: str,
    now_utc: str,
) -> tuple[Dict[str, Any], Dict[str, int]]:
    raw_aliases = aliases_payload.get("aliases")
    existing_aliases = raw_aliases if isinstance(raw_aliases, dict) else {}

    final_aliases: Dict[str, Dict[str, Any]] = {}
    rewritten = 0
    refs_rewritten = 0
    demoted_alias_overwritten = 0

    for idx, (raw_key, raw_value) in enumerate(existing_aliases.items()):
        alias_key = tag_source.sanitize_alias_key(raw_key, idx)
        alias_value = tag_source.sanitize_alias_entry(raw_value, alias_key, "tag_aliases.aliases")
        if alias_key == demoted_alias_key:
            demoted_alias_overwritten = 1
            continue

        updated_value, changed, replaced = replace_alias_entry_refs(alias_value, old_tag_id, replacement_tag_ids)
        if changed:
            rewritten += 1
        if replaced > 0:
            refs_rewritten += replaced
        final_aliases[alias_key] = updated_value

    final_aliases[demoted_alias_key] = build_alias_entry("", replacement_tag_ids)

    if "tag_aliases_version" not in aliases_payload:
        aliases_payload["tag_aliases_version"] = "tag_aliases_v1"
    aliases_payload["aliases"] = final_aliases
    aliases_payload["updated_at_utc"] = now_utc

    return aliases_payload, {
        "aliases_rewritten": rewritten,
        "alias_tag_refs_rewritten": refs_rewritten,
        "demoted_alias_overwritten": demoted_alias_overwritten,
        "aliases_final_total": len(final_aliases),
    }


def update_alias_entry_for_tag(
    entry: Dict[str, Any], old_tag_id: str, new_tag_id: Optional[str]
) -> tuple[Optional[Dict[str, Any]], bool]:
    tags = tag_source.sanitize_tag_id_list(entry.get("tags"), "tag_aliases.aliases[*].tags")
    description = tag_source.sanitize_alias_description(entry.get("description", ""), "tag_aliases.aliases[*].description")

    changed = False
    out: list[str] = []
    seen: set[str] = set()
    for item in tags:
        next_item = item
        if item == old_tag_id:
            if new_tag_id is None:
                changed = True
                continue
            if new_tag_id != old_tag_id:
                changed = True
                next_item = new_tag_id
        if next_item in seen:
            changed = True
            continue
        seen.add(next_item)
        out.append(next_item)

    if not out:
        return None, True if changed else False
    tag_source.enforce_alias_group_constraints(out, "tag_aliases.aliases[*].tags")
    updated = build_alias_entry(description, out)
    return updated, changed or out != tags


def is_redundant_alias(alias_key: str, entry: Dict[str, Any]) -> bool:
    tags = tag_source.sanitize_tag_id_list(entry.get("tags"), "tag_aliases.aliases[*].tags")
    if len(tags) != 1:
        return False
    target = tags[0]
    if ":" not in target:
        return False
    target_slug = target.split(":", 1)[1]
    return alias_key == target_slug


def rewrite_aliases_for_tag(
    aliases_payload: Dict[str, Any],
    old_tag_id: str,
    new_tag_id: Optional[str],
    now_utc: str,
) -> tuple[Dict[str, Any], Dict[str, int]]:
    raw_aliases = aliases_payload.get("aliases")
    existing_aliases = raw_aliases if isinstance(raw_aliases, dict) else {}

    final_aliases: Dict[str, Dict[str, Any]] = {}
    rewritten = 0
    removed_empty = 0
    removed_redundant = 0

    for idx, (raw_key, raw_value) in enumerate(existing_aliases.items()):
        alias_key = tag_source.sanitize_alias_key(raw_key, idx)
        alias_value = tag_source.sanitize_alias_entry(raw_value, alias_key, "tag_aliases.aliases")
        updated_value, changed = update_alias_entry_for_tag(alias_value, old_tag_id, new_tag_id)
        if changed:
            rewritten += 1
        if updated_value is None:
            removed_empty += 1
            continue
        if changed and is_redundant_alias(alias_key, updated_value):
            removed_redundant += 1
            continue
        final_aliases[alias_key] = updated_value

    if "tag_aliases_version" not in aliases_payload:
        aliases_payload["tag_aliases_version"] = "tag_aliases_v1"
    aliases_payload["aliases"] = final_aliases
    aliases_payload["updated_at_utc"] = now_utc

    return aliases_payload, {
        "aliases_rewritten": rewritten,
        "aliases_removed_empty": removed_empty,
        "aliases_removed_redundant": removed_redundant,
        "aliases_final_total": len(final_aliases),
    }


def extract_registry_tag_ids(registry_payload: Dict[str, Any]) -> set[str]:
    raw_tags = registry_payload.get("tags")
    tags = raw_tags if isinstance(raw_tags, list) else []
    out: set[str] = set()
    for raw in tags:
        if not isinstance(raw, dict):
            continue
        tag_id = str(raw.get("tag_id") or "").strip().lower()
        if tag_source.TAG_ID_RE.fullmatch(tag_id):
            out.add(tag_id)
    return out


def mutate_alias_entry(
    aliases_payload: Dict[str, Any],
    registry_payload: Dict[str, Any],
    alias_key: str,
    new_alias_key: str,
    description: str,
    tags: list[str],
    now_utc: str,
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    tag_source.enforce_alias_group_constraints(tags, "tags")

    registry_tag_ids = extract_registry_tag_ids(registry_payload)
    for idx, tag_id in enumerate(tags):
        if tag_id not in registry_tag_ids:
            raise ValueError(f"tags[{idx}] is not present in registry: {tag_id}")

    raw_aliases = aliases_payload.get("aliases")
    existing_aliases = raw_aliases if isinstance(raw_aliases, dict) else {}

    normalized_order: list[str] = []
    normalized_by_key: Dict[str, Dict[str, Any]] = {}
    for idx, (raw_key, raw_value) in enumerate(existing_aliases.items()):
        key = tag_source.sanitize_alias_key(raw_key, idx)
        value = tag_source.sanitize_alias_entry(raw_value, key, "tag_aliases.aliases")
        if key not in normalized_by_key:
            normalized_order.append(key)
        normalized_by_key[key] = value

    if alias_key not in normalized_by_key:
        raise ValueError(f"alias not found: {alias_key}")
    if new_alias_key != alias_key and new_alias_key in normalized_by_key:
        raise ValueError(f"alias already exists: {new_alias_key}")

    original = normalized_by_key[alias_key]
    updated_entry = build_alias_entry(description, tags)
    renamed = new_alias_key != alias_key
    tags_changed = original.get("tags") != updated_entry.get("tags")
    description_changed = original.get("description") != updated_entry.get("description")
    changed = renamed or tags_changed or description_changed

    if not changed:
        return aliases_payload, {
            "action": "edit_alias",
            "alias": alias_key,
            "new_alias": new_alias_key,
            "renamed": False,
            "tags_changed": False,
            "description_changed": False,
            "changed": False,
            "final_total": len(normalized_by_key),
        }

    final_aliases: Dict[str, Dict[str, Any]] = {}
    inserted = False
    for key in normalized_order:
        if key == alias_key:
            if not inserted:
                final_aliases[new_alias_key] = updated_entry
                inserted = True
            continue
        final_aliases[key] = normalized_by_key[key]
    if not inserted:
        final_aliases[new_alias_key] = updated_entry

    if "tag_aliases_version" not in aliases_payload:
        aliases_payload["tag_aliases_version"] = "tag_aliases_v1"
    aliases_payload["aliases"] = final_aliases
    aliases_payload["updated_at_utc"] = now_utc

    return aliases_payload, {
        "action": "edit_alias",
        "alias": alias_key,
        "new_alias": new_alias_key,
        "renamed": renamed,
        "tags_changed": tags_changed,
        "description_changed": description_changed,
        "changed": True,
        "final_total": len(final_aliases),
    }


def build_alias_mutation_summary_text(stats: Dict[str, Any]) -> str:
    alias = str(stats.get("alias") or "")
    new_alias = str(stats.get("new_alias") or alias)
    renamed = 1 if bool(stats.get("renamed")) else 0
    tags_changed = 1 if bool(stats.get("tags_changed")) else 0
    description_changed = 1 if bool(stats.get("description_changed")) else 0
    changed = 1 if bool(stats.get("changed")) else 0
    final_total = int(stats.get("final_total") or 0)
    return (
        f"mode edit_alias; {alias} -> {new_alias}; "
        f"changed {changed}; renamed {renamed}; tags_changed {tags_changed}; "
        f"description_changed {description_changed}; final {final_total}"
    )
