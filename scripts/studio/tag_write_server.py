#!/usr/bin/env python3
"""
README
======
Run:
  python3 scripts/studio/tag_write_server.py
  python3 scripts/studio/tag_write_server.py --port 8787
  python3 scripts/studio/tag_write_server.py --repo-root /path/to/dotlineform-site
  python3 scripts/studio/tag_write_server.py --dry-run

What it does:
  - Exposes a tiny localhost API for Tag Studio.
  - Endpoint paths are owned by scripts/tag_routes.py.
  - Updates:
    - assets/studio/data/tag_assignments.json (series and work tag saves)
    - assets/studio/data/tag_registry.json (registry import replace/merge)
    - assets/studio/data/tag_aliases.json (aliases import replace/merge/add)

Security constraints:
  - Binds to 127.0.0.1 only.
  - CORS allows only:
      http://localhost:*
      http://127.0.0.1:*
  - Hard allowlist for data writes permits only:
      <repo-root>/assets/studio/data/tag_assignments.json
      <repo-root>/assets/studio/data/tag_registry.json
      <repo-root>/assets/studio/data/tag_aliases.json
      <repo-root>/var/studio/backups/*
  - Change event logs are written only to:
      <repo-root>/var/studio/logs/tag_write_server.log
  - Unified Studio activity rows are appended only through the fixed activity
    feed paths owned by scripts/studio_activity.py.
  - No external dependencies (Python stdlib only).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import sys
import tempfile
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Mapping, Optional
from urllib.parse import urlparse

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from script_logging import append_script_log
from studio_activity import append_studio_activity
from tag_activity import attach_tag_activity, tag_activity_changed, tag_activity_status
import tag_assignment_service as tag_assignments
import tag_routes as routes
import tag_source_model as tag_source


MUTATE_ACTIONS = {"edit", "delete"}
BACKUPS_REL_DIR = Path("var/studio/backups")
LOGS_REL_DIR = Path("var/studio/logs")


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def backup_stamp_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%S")


def find_repo_root(start: Path) -> Optional[Path]:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "_config.yml").exists():
            return candidate
    return None


def detect_repo_root(explicit_root: str) -> Path:
    if explicit_root:
        repo_root = Path(explicit_root).expanduser().resolve()
        if not (repo_root / "_config.yml").exists():
            raise SystemExit(f"--repo-root does not look like repo root (missing _config.yml): {repo_root}")
        return repo_root

    for start in [Path.cwd(), Path(__file__).resolve().parent]:
        found = find_repo_root(start)
        if found is not None:
            return found

    raise SystemExit("Could not auto-detect repo root. Pass --repo-root.")


def allowed_origin(origin: str) -> Optional[str]:
    if not origin:
        return None

    try:
        parsed = urlparse(origin)
    except Exception:
        return None

    if parsed.scheme != "http":
        return None
    if parsed.hostname not in {"localhost", "127.0.0.1"}:
        return None
    if parsed.path not in {"", "/"}:
        return None
    if parsed.params or parsed.query or parsed.fragment:
        return None
    if parsed.port is None:
        return f"{parsed.scheme}://{parsed.hostname}"
    return f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"


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

    existing_order: list[str] = []
    existing_by_id: dict[str, Dict[str, Any]] = {}
    for raw in existing_tags:
        if not isinstance(raw, dict):
            continue
        tag_id = str(raw.get("tag_id") or "").strip().lower()
        if not tag_id:
            continue
        if tag_id not in existing_by_id:
            existing_order.append(tag_id)
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
        out.append(tag_source.build_assignment_tag(tag_value, normalized_tag["w_manual"]))

    return out, changed, refs_rewritten


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

    aliases_updated, alias_stats = rewrite_aliases_for_targets(
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
        assignments_payload["tag_assignments_version"] = "tag_assignments_v1"

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


def atomic_write(path: Path, payload: Dict[str, Any], backups_dir: Path) -> None:
    backups_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backups_dir / f"{path.name}.bak-{backup_stamp_now()}"
    if path.exists():
        shutil.copy2(path, backup_path)

    fd, temp_name = tempfile.mkstemp(prefix=f"{path.name}.", suffix=".tmp", dir=str(path.parent))
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2, sort_keys=False)
            fh.write("\n")
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass


def atomic_write_many(payloads_by_path: Dict[Path, Dict[str, Any]], backups_dir: Path) -> None:
    backups_dir.mkdir(parents=True, exist_ok=True)
    stamp = backup_stamp_now()
    backups: Dict[Path, Path] = {}
    temp_paths: Dict[Path, Path] = {}
    replaced_paths: list[Path] = []

    try:
        for path, payload in payloads_by_path.items():
            if path.exists():
                backup_path = backups_dir / f"{path.name}.bak-{stamp}"
                shutil.copy2(path, backup_path)
                backups[path] = backup_path

            fd, temp_name = tempfile.mkstemp(prefix=f"{path.name}.", suffix=".tmp", dir=str(path.parent))
            temp_path = Path(temp_name)
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, ensure_ascii=False, indent=2, sort_keys=False)
                fh.write("\n")
            temp_paths[path] = temp_path

        for path, temp_path in temp_paths.items():
            os.replace(temp_path, path)
            replaced_paths.append(path)
    except Exception:
        for path in reversed(replaced_paths):
            backup_path = backups.get(path)
            try:
                if backup_path and backup_path.exists():
                    shutil.copy2(backup_path, path)
                elif path.exists():
                    path.unlink()
            except Exception:
                pass
        raise
    finally:
        for temp_path in temp_paths.values():
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass


class TagWriteServer(ThreadingHTTPServer):
    def __init__(
        self,
        server_address: tuple[str, int],
        handler_cls,
        repo_root: Path,
        assignments_path: Path,
        series_index_path: Path,
        registry_path: Path,
        aliases_path: Path,
        allowed_write_paths: set[Path],
        backups_dir: Path,
        dry_run: bool,
    ):
        super().__init__(server_address, handler_cls)
        self.repo_root = repo_root.resolve()
        self.assignments_path = assignments_path
        self.series_index_path = series_index_path
        self.registry_path = registry_path
        self.aliases_path = aliases_path
        self.allowed_write_paths = {path.resolve() for path in allowed_write_paths}
        self.backups_dir = backups_dir.resolve()
        self.dry_run = dry_run

    def log_event(self, event: str, details: Optional[Dict[str, Any]] = None) -> None:
        try:
            append_script_log(
                Path(__file__),
                event=event,
                details=details,
                repo_root=self.repo_root,
                log_dir_rel=LOGS_REL_DIR,
            )
        except Exception:
            # Logging must never block API requests.
            pass

    def append_activity(self, entry: Dict[str, Any]) -> None:
        append_studio_activity(self.repo_root, entry)


class Handler(BaseHTTPRequestHandler):
    server: TagWriteServer  # type: ignore[assignment]

    POST_HANDLERS: Mapping[str, str] = {
        routes.SAVE_TAGS_PATH: "_handle_save_tags",
        routes.BUILD_DOCS_PATH: "_handle_build_docs_deprecated",
        routes.IMPORT_ASSIGNMENTS_PREVIEW_PATH: "_handle_import_tag_assignments_preview",
        routes.IMPORT_ASSIGNMENTS_APPLY_PATH: "_handle_import_tag_assignments_apply",
        routes.IMPORT_REGISTRY_PATH: "_handle_import_tag_registry",
        routes.IMPORT_ALIASES_PATH: "_handle_import_tag_aliases",
        routes.DELETE_ALIAS_PATH: "_handle_delete_tag_alias",
        routes.MUTATE_ALIAS_PREVIEW_PATH: "_handle_mutate_tag_alias_preview",
        routes.MUTATE_ALIAS_APPLY_PATH: "_handle_mutate_tag_alias",
        routes.PROMOTE_ALIAS_PREVIEW_PATH: "_handle_promote_tag_alias_preview",
        routes.PROMOTE_ALIAS_APPLY_PATH: "_handle_promote_tag_alias",
        routes.DEMOTE_TAG_PREVIEW_PATH: "_handle_demote_tag_preview",
        routes.DEMOTE_TAG_APPLY_PATH: "_handle_demote_tag",
        routes.MUTATE_TAG_PREVIEW_PATH: "_handle_mutate_tag_preview",
        routes.MUTATE_TAG_APPLY_PATH: "_handle_mutate_tag",
    }

    def _request_path(self) -> str:
        return urlparse(self.path).path

    def do_OPTIONS(self) -> None:  # noqa: N802
        request_path = self._request_path()
        if request_path not in routes.OPTIONS_PATHS:
            self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "not found"})
            return
        origin = self.headers.get("Origin", "")
        allowed = allowed_origin(origin)
        if origin and not allowed:
            self._send_json(HTTPStatus.FORBIDDEN, {"ok": False, "error": "origin not allowed"})
            return
        self.send_response(HTTPStatus.NO_CONTENT)
        self._write_cors_headers(allowed)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        origin = self.headers.get("Origin", "")
        allowed = allowed_origin(origin)
        if origin and not allowed:
            self._send_json(HTTPStatus.FORBIDDEN, {"ok": False, "error": "origin not allowed"})
            return

        request_path = self._request_path()
        if request_path != routes.HEALTH_PATH:
            self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "not found"}, allowed)
            return

        self._send_json(
            HTTPStatus.OK,
            {
                "ok": True,
                "service": "tag_write_server",
                "tag_assignments_path": str(self.server.assignments_path),
                "tag_registry_path": str(self.server.registry_path),
                "tag_aliases_path": str(self.server.aliases_path),
                "time_utc": utc_now(),
            },
            allowed,
        )

    def do_POST(self) -> None:  # noqa: N802
        origin = self.headers.get("Origin", "")
        allowed = allowed_origin(origin)
        if origin and not allowed:
            self._send_json(HTTPStatus.FORBIDDEN, {"ok": False, "error": "origin not allowed"})
            return

        request_path = self._request_path()
        handler_name = self.POST_HANDLERS.get(request_path)
        if handler_name is None:
            self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "not found"}, allowed)
            return

        try:
            getattr(self, handler_name)(allowed)
        except ValueError as exc:
            self.server.log_event("request_error", {"path": request_path, "error": str(exc), "kind": "validation"})
            self._send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)}, allowed)
        except Exception as exc:  # noqa: BLE001
            self.server.log_event("request_error", {"path": request_path, "error": str(exc), "kind": "internal"})
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"ok": False, "error": f"internal error: {exc}"}, allowed)

    def _handle_build_docs_deprecated(self, allowed: Optional[str]) -> None:
        self._send_json(
            HTTPStatus.GONE,
            {
                "ok": False,
                "error": f"`{routes.BUILD_DOCS_PATH}` is deprecated. Use the Docs Management Server `POST /docs/rebuild` path for live docs rebuilds.",
            },
            allowed,
        )

    def _handle_save_tags(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        series_id = body.get("series_id")
        work_id = body.get("work_id")
        keep_work = body.get("keep_work")
        tags = body.get("tags")
        _ = body.get("client_time_utc")

        now_utc = utc_now()
        payload = tag_source.load_assignments(self.server.assignments_path)
        updated_payload, response_payload, would_write = tag_assignments.plan_assignment_save(
            payload,
            series_id,
            work_id,
            keep_work,
            tags,
            now_utc,
        )
        deleted = bool(response_payload.get("deleted"))
        normalized_series_id = str(response_payload.get("series_id") or "")
        normalized_work_id = response_payload.get("work_id")
        normalized_keep_work = response_payload.get("keep_work")

        target_path = self.server.assignments_path.resolve()
        if not self.server.dry_run:
            if target_path not in self.server.allowed_write_paths:
                raise ValueError("write target not allowlisted")
            atomic_write(target_path, updated_payload, self.server.backups_dir)
        else:
            response_payload["dry_run"] = True
            response_payload["would_write"] = would_write

        self.server.log_event(
            "save_tags",
            {
                "series_id": normalized_series_id,
                "work_id": normalized_work_id,
                "keep_work": normalized_keep_work,
                "tag_count": response_payload["tag_count"],
                "deleted": deleted,
                "dry_run": self.server.dry_run,
            },
        )
        attach_tag_activity(
            repo_root=self.server.repo_root,
            endpoint=self.path,
            dry_run=self.server.dry_run,
            append_activity=self.server.append_activity,
            body=body,
            response_payload=response_payload,
            record_id=normalized_series_id,
            record_groups={"series": [normalized_series_id], "works": [normalized_work_id] if normalized_work_id else []},
            detail_items=[
                f"Saved tag assignments for series {normalized_series_id}.",
                f"Updated work {normalized_work_id}." if normalized_work_id else "",
                f"Tag count: {response_payload['tag_count']}.",
            ],
            activity_id_suffix=f"work:{normalized_work_id}" if normalized_work_id else f"series:{normalized_series_id}",
        )
        self._send_json(HTTPStatus.OK, response_payload, allowed)

    def _handle_import_tag_registry(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        mode = str(body.get("mode") or "").strip().lower()
        import_registry = body.get("import_registry")
        import_filename = tag_source.sanitize_import_filename(body.get("import_filename"))
        _ = body.get("client_time_utc")

        now_utc = utc_now()
        existing_payload = tag_source.load_registry(self.server.registry_path)
        updated_payload, stats = apply_registry_import(existing_payload, import_registry, mode, now_utc)
        summary_text = build_import_summary_text(stats)

        response_payload: Dict[str, Any] = {
            "ok": True,
            "updated_at_utc": now_utc,
            "summary_text": summary_text,
            "import_filename": import_filename,
            **stats,
        }

        target_path = self.server.registry_path.resolve()
        if not self.server.dry_run:
            if target_path not in self.server.allowed_write_paths:
                raise ValueError("write target not allowlisted")
            atomic_write(target_path, updated_payload, self.server.backups_dir)
        else:
            response_payload["dry_run"] = True
            response_payload["would_write"] = {
                "updated_at_utc": now_utc,
                **stats,
            }

        self.server.log_event(
            "import_tag_registry",
            {
                "summary_text": summary_text,
                "import_filename": import_filename,
                "mode": mode,
                "dry_run": self.server.dry_run,
                **stats,
            },
        )
        if tag_activity_changed(stats):
            attach_tag_activity(
                repo_root=self.server.repo_root,
                endpoint=self.path,
                dry_run=self.server.dry_run,
                append_activity=self.server.append_activity,
                body=body,
                response_payload=response_payload,
                detail_items=[
                    summary_text,
                    f"Mode: {mode}; imported: {stats.get('imported_total')}; final tags: {stats.get('final_total')}.",
                ],
                status=tag_activity_status(stats),
            )
        self._send_json(HTTPStatus.OK, response_payload, allowed)

    def _handle_import_tag_assignments_preview(self, allowed: Optional[str]) -> None:
        self._handle_import_tag_assignments(allowed, preview=True)

    def _handle_import_tag_assignments_apply(self, allowed: Optional[str]) -> None:
        self._handle_import_tag_assignments(allowed, preview=False)

    def _handle_import_tag_assignments(self, allowed: Optional[str], preview: bool) -> None:
        body = self._read_json_body()
        import_assignments = tag_source.sanitize_import_assignments_session(body.get("import_assignments"))
        import_filename = tag_source.sanitize_import_filename(body.get("import_filename"))
        raw_resolutions = body.get("resolutions")
        _ = body.get("client_time_utc")

        resolutions: Dict[str, str] = {}
        if raw_resolutions is not None:
            if not isinstance(raw_resolutions, dict):
                raise ValueError("resolutions must be an object")
            for raw_series_id, raw_resolution in raw_resolutions.items():
                series_id = str(raw_series_id or "").strip().lower()
                if not series_id:
                    continue
                resolution = str(raw_resolution or "").strip().lower()
                if resolution not in {"overwrite", "skip"}:
                    raise ValueError(f"resolutions[{series_id}] must be overwrite or skip")
                resolutions[series_id] = resolution

        now_utc = utc_now()
        existing_payload = tag_source.load_assignments(self.server.assignments_path)
        series_index_payload = tag_source.load_series_index(self.server.series_index_path)
        preview_payload = tag_assignments.preview_assignment_import(existing_payload, import_assignments, series_index_payload)
        response_payload = tag_assignments.build_assignment_import_preview_response(preview_payload, import_filename, now_utc)

        if preview:
            self.server.log_event(
                "import_tag_assignments_preview",
                {
                    "staged_series_count": preview_payload["staged_series_count"],
                    "applicable_count": preview_payload["applicable_count"],
                    "conflict_count": preview_payload["conflict_count"],
                    "invalid_count": preview_payload["invalid_count"],
                    "missing_count": preview_payload["missing_count"],
                    "dry_run": self.server.dry_run,
                },
            )
            self._send_json(HTTPStatus.OK, response_payload, allowed)
            return

        updated_payload, apply_stats = tag_assignments.apply_assignment_import(
            existing_payload,
            import_assignments,
            preview_payload,
            resolutions,
            now_utc,
        )
        response_payload = tag_assignments.build_assignment_import_apply_response(response_payload, apply_stats)
        apply_summary_text = str(response_payload.get("summary_text") or "")

        target_path = self.server.assignments_path.resolve()
        if not self.server.dry_run:
            if target_path not in self.server.allowed_write_paths:
                raise ValueError("write target not allowlisted")
            atomic_write(target_path, updated_payload, self.server.backups_dir)
        else:
            response_payload["dry_run"] = True
            response_payload["would_write"] = {
                "updated_at_utc": now_utc,
                **apply_stats,
            }

        self.server.log_event(
            "import_tag_assignments",
            {
                **apply_stats,
                "dry_run": self.server.dry_run,
            },
        )
        if tag_activity_changed(apply_stats):
            attach_tag_activity(
                repo_root=self.server.repo_root,
                endpoint=self.path,
                dry_run=self.server.dry_run,
                append_activity=self.server.append_activity,
                body=body,
                response_payload=response_payload,
                detail_items=[
                    apply_summary_text,
                    f"Applied series: {apply_stats.get('applied_series')}; skipped: {apply_stats.get('skipped_series')}.",
                ],
                status=tag_activity_status(apply_stats),
            )
        self._send_json(HTTPStatus.OK, response_payload, allowed)

    def _handle_import_tag_aliases(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        mode = str(body.get("mode") or "").strip().lower()
        import_aliases = body.get("import_aliases")
        import_filename = tag_source.sanitize_import_filename(body.get("import_filename"))
        _ = body.get("client_time_utc")

        now_utc = utc_now()
        existing_payload = tag_source.load_aliases(self.server.aliases_path)
        updated_payload, stats = apply_aliases_import(existing_payload, import_aliases, mode, now_utc)
        summary_text = build_import_summary_text(stats, noun="aliases")

        response_payload: Dict[str, Any] = {
            "ok": True,
            "updated_at_utc": now_utc,
            "summary_text": summary_text,
            "import_filename": import_filename,
            **stats,
        }

        target_path = self.server.aliases_path.resolve()
        if not self.server.dry_run:
            if target_path not in self.server.allowed_write_paths:
                raise ValueError("write target not allowlisted")
            atomic_write(target_path, updated_payload, self.server.backups_dir)
        else:
            response_payload["dry_run"] = True
            response_payload["would_write"] = {
                "updated_at_utc": now_utc,
                **stats,
            }

        self.server.log_event(
            "import_tag_aliases",
            {
                "summary_text": summary_text,
                "import_filename": import_filename,
                "mode": mode,
                "dry_run": self.server.dry_run,
                **stats,
            },
        )
        if tag_activity_changed(stats):
            attach_tag_activity(
                repo_root=self.server.repo_root,
                endpoint=self.path,
                dry_run=self.server.dry_run,
                append_activity=self.server.append_activity,
                body=body,
                response_payload=response_payload,
                detail_items=[
                    summary_text,
                    f"Mode: {mode}; imported: {stats.get('imported_total')}; final aliases: {stats.get('final_total')}.",
                ],
                status=tag_activity_status(stats),
            )
        self._send_json(HTTPStatus.OK, response_payload, allowed)

    def _handle_delete_tag_alias(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        alias_raw = body.get("alias")
        alias_key = tag_source.sanitize_alias_key(alias_raw, 0)
        _ = body.get("client_time_utc")

        now_utc = utc_now()
        existing_payload = tag_source.load_aliases(self.server.aliases_path)
        updated_payload, stats = delete_alias_key(existing_payload, alias_key, now_utc)
        summary_text = f"deleted alias {alias_key}; final {int(stats.get('final_total') or 0)}"

        response_payload: Dict[str, Any] = {
            "ok": True,
            "updated_at_utc": now_utc,
            "summary_text": summary_text,
            **stats,
        }

        target_path = self.server.aliases_path.resolve()
        if not self.server.dry_run:
            if target_path not in self.server.allowed_write_paths:
                raise ValueError("write target not allowlisted")
            atomic_write(target_path, updated_payload, self.server.backups_dir)
        else:
            response_payload["dry_run"] = True
            response_payload["would_write"] = {
                "updated_at_utc": now_utc,
                **stats,
            }

        self.server.log_event(
            "delete_tag_alias",
            {
                "summary_text": summary_text,
                "dry_run": self.server.dry_run,
                **stats,
            },
        )
        attach_tag_activity(
            repo_root=self.server.repo_root,
            endpoint=self.path,
            dry_run=self.server.dry_run,
            append_activity=self.server.append_activity,
            body=body,
            response_payload=response_payload,
            detail_items=[summary_text],
            status=tag_activity_status(stats),
        )
        self._send_json(HTTPStatus.OK, response_payload, allowed)

    def _handle_mutate_tag_alias_preview(self, allowed: Optional[str]) -> None:
        self._handle_mutate_tag_alias(allowed, preview=True)

    def _handle_mutate_tag_alias(self, allowed: Optional[str], preview: bool = False) -> None:
        body = self._read_json_body()
        alias_key = tag_source.sanitize_alias_key(body.get("alias"), 0)
        new_alias_raw = body.get("new_alias", alias_key)
        new_alias_key = tag_source.sanitize_alias_key(new_alias_raw, 1)
        description = tag_source.sanitize_alias_description(body.get("description", ""), "description")
        tags = tag_source.sanitize_tag_id_list(body.get("tags"), "tags")
        tag_source.enforce_alias_group_constraints(tags, "tags")
        _ = body.get("client_time_utc")

        now_utc = utc_now()
        aliases_payload = tag_source.load_aliases(self.server.aliases_path)
        registry_payload = tag_source.load_registry(self.server.registry_path)
        aliases_updated, stats = mutate_alias_entry(
            aliases_payload=aliases_payload,
            registry_payload=registry_payload,
            alias_key=alias_key,
            new_alias_key=new_alias_key,
            description=description,
            tags=tags,
            now_utc=now_utc,
        )
        summary_text = build_alias_mutation_summary_text(stats)

        response_payload: Dict[str, Any] = {
            "ok": True,
            "updated_at_utc": now_utc,
            "summary_text": summary_text,
            "preview": preview,
            **stats,
        }

        target_path = self.server.aliases_path.resolve()
        should_write = bool(stats.get("changed"))
        if preview:
            response_payload["dry_run"] = True
            response_payload["would_write"] = {
                "updated_at_utc": now_utc,
                **stats,
            }
        elif not self.server.dry_run:
            if should_write:
                if target_path not in self.server.allowed_write_paths:
                    raise ValueError("write target not allowlisted")
                atomic_write(target_path, aliases_updated, self.server.backups_dir)
        else:
            response_payload["dry_run"] = True
            response_payload["would_write"] = {
                "updated_at_utc": now_utc,
                **stats,
            }

        if not preview:
            self.server.log_event(
                "mutate_tag_alias",
                {
                    "summary_text": summary_text,
                    "dry_run": self.server.dry_run,
                    **stats,
                },
            )
            if tag_activity_changed(stats):
                attach_tag_activity(
                    repo_root=self.server.repo_root,
                    endpoint=self.path,
                    dry_run=self.server.dry_run,
                    append_activity=self.server.append_activity,
                    body=body,
                    response_payload=response_payload,
                    detail_items=[
                        summary_text,
                        f"Alias: {stats.get('alias')}; new alias: {stats.get('new_alias')}.",
                    ],
                    status=tag_activity_status(stats),
                )
        self._send_json(HTTPStatus.OK, response_payload, allowed)

    def _handle_promote_tag_alias_preview(self, allowed: Optional[str]) -> None:
        self._handle_promote_tag_alias(allowed, preview=True)

    def _handle_promote_tag_alias(self, allowed: Optional[str], preview: bool = False) -> None:
        body = self._read_json_body()
        alias_key = tag_source.sanitize_alias_key(body.get("alias"), 0)
        _ = body.get("client_time_utc")

        now_utc = utc_now()
        registry_payload = tag_source.load_registry(self.server.registry_path)
        aliases_payload = tag_source.load_aliases(self.server.aliases_path)
        allowed_groups = tag_source.extract_allowed_groups(registry_payload)
        group = tag_source.sanitize_group(body.get("group"), allowed_groups, "group")

        registry_updated, aliases_updated, stats, registry_changed, aliases_changed = promote_alias_to_canonical_tag(
            registry_payload=registry_payload,
            aliases_payload=aliases_payload,
            alias_key=alias_key,
            group=group,
            now_utc=now_utc,
        )
        summary_text = build_promote_summary_text(stats)

        response_payload: Dict[str, Any] = {
            "ok": True,
            "updated_at_utc": now_utc,
            "summary_text": summary_text,
            "preview": preview,
            **stats,
        }

        payloads_to_write: Dict[Path, Dict[str, Any]] = {}
        registry_target = self.server.registry_path.resolve()
        aliases_target = self.server.aliases_path.resolve()
        if registry_changed:
            payloads_to_write[registry_target] = registry_updated
        if aliases_changed:
            payloads_to_write[aliases_target] = aliases_updated

        if preview:
            response_payload["dry_run"] = True
            response_payload["would_write"] = {
                "updated_at_utc": now_utc,
                **stats,
            }
        elif not self.server.dry_run:
            for target in payloads_to_write.keys():
                if target not in self.server.allowed_write_paths:
                    raise ValueError("write target not allowlisted")
            if payloads_to_write:
                atomic_write_many(payloads_to_write, self.server.backups_dir)
        else:
            response_payload["dry_run"] = True
            response_payload["would_write"] = {
                "updated_at_utc": now_utc,
                **stats,
            }

        if not preview:
            self.server.log_event(
                "promote_tag_alias",
                {
                    "summary_text": summary_text,
                    "dry_run": self.server.dry_run,
                    **stats,
                },
            )
            if tag_activity_changed(stats):
                attach_tag_activity(
                    repo_root=self.server.repo_root,
                    endpoint=self.path,
                    dry_run=self.server.dry_run,
                    append_activity=self.server.append_activity,
                    body=body,
                    response_payload=response_payload,
                    detail_items=[
                        summary_text,
                        f"Promoted alias {stats.get('alias')} to {stats.get('new_tag_id')}.",
                    ],
                    status=tag_activity_status(stats),
                )
        self._send_json(HTTPStatus.OK, response_payload, allowed)

    def _handle_demote_tag_preview(self, allowed: Optional[str]) -> None:
        self._handle_demote_tag(allowed, preview=True)

    def _handle_demote_tag(self, allowed: Optional[str], preview: bool = False) -> None:
        body = self._read_json_body()
        old_tag_id = tag_source.sanitize_tag_id(body.get("tag_id"), "tag_id")
        alias_targets = tag_source.sanitize_tag_id_list(body.get("alias_targets"), "alias_targets")
        tag_source.enforce_alias_group_constraints(alias_targets, "alias_targets")
        _ = body.get("client_time_utc")

        now_utc = utc_now()
        registry_payload = tag_source.load_registry(self.server.registry_path)
        aliases_payload = tag_source.load_aliases(self.server.aliases_path)
        assignments_payload = tag_source.load_assignments(self.server.assignments_path)

        registry_updated, aliases_updated, assignments_updated, stats, assignments_changed = demote_tag_to_alias(
            registry_payload=registry_payload,
            aliases_payload=aliases_payload,
            assignments_payload=assignments_payload,
            old_tag_id=old_tag_id,
            alias_targets=alias_targets,
            now_utc=now_utc,
        )
        summary_text = build_demote_summary_text(stats)

        response_payload: Dict[str, Any] = {
            "ok": True,
            "updated_at_utc": now_utc,
            "summary_text": summary_text,
            "preview": preview,
            **stats,
        }

        registry_target = self.server.registry_path.resolve()
        aliases_target = self.server.aliases_path.resolve()
        assignments_target = self.server.assignments_path.resolve()

        payloads_to_write: Dict[Path, Dict[str, Any]] = {
            registry_target: registry_updated,
            aliases_target: aliases_updated,
        }
        if assignments_changed:
            payloads_to_write[assignments_target] = assignments_updated

        if preview:
            response_payload["dry_run"] = True
            response_payload["would_write"] = {
                "updated_at_utc": now_utc,
                **stats,
            }
        elif not self.server.dry_run:
            for target in payloads_to_write.keys():
                if target not in self.server.allowed_write_paths:
                    raise ValueError("write target not allowlisted")
            atomic_write_many(payloads_to_write, self.server.backups_dir)
        else:
            response_payload["dry_run"] = True
            response_payload["would_write"] = {
                "updated_at_utc": now_utc,
                **stats,
            }

        if not preview:
            self.server.log_event(
                "demote_tag",
                {
                    "summary_text": summary_text,
                    "dry_run": self.server.dry_run,
                    **stats,
                },
            )
            if tag_activity_changed(stats):
                attach_tag_activity(
                    repo_root=self.server.repo_root,
                    endpoint=self.path,
                    dry_run=self.server.dry_run,
                    append_activity=self.server.append_activity,
                    body=body,
                    response_payload=response_payload,
                    detail_items=[
                        summary_text,
                        f"Demoted {stats.get('old_tag_id')} to alias {stats.get('alias_key')}.",
                    ],
                    status=tag_activity_status(stats),
                )
        self._send_json(HTTPStatus.OK, response_payload, allowed)

    def _handle_mutate_tag_preview(self, allowed: Optional[str]) -> None:
        self._handle_mutate_tag(allowed, preview=True)

    def _handle_mutate_tag(self, allowed: Optional[str], preview: bool = False) -> None:
        body = self._read_json_body()
        action = str(body.get("action") or "").strip().lower()
        old_tag_id = tag_source.sanitize_tag_id(body.get("tag_id"), "tag_id")
        raw_allow_canonical_rename = body.get("allow_canonical_rename", False)
        if not isinstance(raw_allow_canonical_rename, bool):
            raise ValueError("allow_canonical_rename must be a boolean")
        allow_canonical_rename = raw_allow_canonical_rename
        _ = body.get("client_time_utc")

        if action not in MUTATE_ACTIONS:
            raise ValueError(f"action must be one of: {sorted(MUTATE_ACTIONS)}")

        new_slug: Optional[str] = None
        new_description: Optional[str] = None
        if action == "edit":
            raw_new_slug = body.get("new_slug")
            if raw_new_slug is not None and str(raw_new_slug).strip():
                new_slug = tag_source.sanitize_slug(raw_new_slug, "new_slug")
            if "description" in body:
                new_description = tag_source.sanitize_alias_description(body.get("description"), "description")

        now_utc = utc_now()
        registry_payload = tag_source.load_registry(self.server.registry_path)
        aliases_payload = tag_source.load_aliases(self.server.aliases_path)
        assignments_payload = tag_source.load_assignments(self.server.assignments_path)

        registry_updated, mutate_meta = mutate_registry_tag(
            registry_payload,
            action=action,
            old_tag_id=old_tag_id,
            now_utc=now_utc,
            new_slug=new_slug,
            new_description=new_description,
            allow_canonical_rename=allow_canonical_rename,
        )
        new_tag_id = mutate_meta.get("new_tag_id")
        rewrite_to = str(new_tag_id) if new_tag_id else None
        should_rewrite_refs = (action == "delete") or (rewrite_to is not None and rewrite_to != old_tag_id)
        if should_rewrite_refs:
            aliases_updated, alias_stats = rewrite_aliases_for_tag(
                aliases_payload,
                old_tag_id=old_tag_id,
                new_tag_id=rewrite_to,
                now_utc=now_utc,
            )
            assignments_updated, assignment_stats = rewrite_assignments_for_tag(
                assignments_payload,
                old_tag_id=old_tag_id,
                new_tag_id=rewrite_to,
                now_utc=now_utc,
            )
        else:
            aliases_updated = aliases_payload
            assignments_updated = assignments_payload
            alias_stats = {
                "aliases_rewritten": 0,
                "aliases_removed_empty": 0,
                "aliases_removed_redundant": 0,
                "aliases_final_total": len(aliases_payload.get("aliases", {})) if isinstance(aliases_payload.get("aliases"), dict) else 0,
            }
            assignment_stats = {
                "series_rows_touched": 0,
                "series_tag_refs_rewritten": 0,
                "work_rows_touched": 0,
                "work_tag_refs_rewritten": 0,
            }

        stats: Dict[str, Any] = {
            "action": action,
            "old_tag_id": old_tag_id,
            "new_tag_id": rewrite_to,
            "canonical_changed": bool(mutate_meta.get("canonical_changed")),
            "description_changed": bool(mutate_meta.get("description_changed")),
            **alias_stats,
            **assignment_stats,
        }
        summary_text = build_mutation_summary_text(stats)

        response_payload: Dict[str, Any] = {
            "ok": True,
            "updated_at_utc": now_utc,
            "summary_text": summary_text,
            "preview": preview,
            **stats,
        }

        registry_target = self.server.registry_path.resolve()
        aliases_target = self.server.aliases_path.resolve()
        assignments_target = self.server.assignments_path.resolve()

        payloads_to_write: Dict[Path, Dict[str, Any]] = {
            registry_target: registry_updated,
        }
        if should_rewrite_refs:
            payloads_to_write[aliases_target] = aliases_updated
            payloads_to_write[assignments_target] = assignments_updated

        if preview:
            response_payload["dry_run"] = True
            response_payload["would_write"] = {
                "updated_at_utc": now_utc,
                **stats,
            }
        elif not self.server.dry_run:
            for target in payloads_to_write.keys():
                if target not in self.server.allowed_write_paths:
                    raise ValueError("write target not allowlisted")
            atomic_write_many(payloads_to_write, self.server.backups_dir)
        else:
            response_payload["dry_run"] = True
            response_payload["would_write"] = {
                "updated_at_utc": now_utc,
                **stats,
            }

        if not preview:
            self.server.log_event(
                "mutate_tag",
                {
                    "summary_text": summary_text,
                    "dry_run": self.server.dry_run,
                    **stats,
                },
            )
            if tag_activity_changed(stats):
                attach_tag_activity(
                    repo_root=self.server.repo_root,
                    endpoint=self.path,
                    dry_run=self.server.dry_run,
                    append_activity=self.server.append_activity,
                    body=body,
                    response_payload=response_payload,
                    detail_items=[
                        summary_text,
                        f"Action: {action}; tag: {old_tag_id}.",
                    ],
                    status=tag_activity_status(stats),
                )
        self._send_json(HTTPStatus.OK, response_payload, allowed)

    def _read_json_body(self) -> Dict[str, Any]:
        content_length = self.headers.get("Content-Length")
        if content_length is None:
            raise ValueError("missing Content-Length")
        try:
            length = int(content_length)
        except ValueError as exc:
            raise ValueError("invalid Content-Length") from exc
        if length < 0 or length > 1024 * 1024:
            raise ValueError("request body too large")

        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            raise ValueError(f"invalid JSON body: {exc}") from exc
        if not isinstance(data, dict):
            raise ValueError("JSON body must be an object")
        return data

    def _send_json(self, status: HTTPStatus, payload: Dict[str, Any], allowed: Optional[str] = None) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._write_cors_headers(allowed)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _write_cors_headers(self, allowed: Optional[str]) -> None:
        if allowed:
            self.send_header("Access-Control-Allow-Origin", allowed)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, fmt: str, *args) -> None:  # noqa: A003
        # Keep stdout concise but still provide basic request logs.
        print(f"[tag_write_server] {self.address_string()} - {fmt % args}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Localhost-only tag write service.")
    parser.add_argument("--port", type=int, default=8787, help="Server port (default: 8787)")
    parser.add_argument("--repo-root", default="", help="Repo root path (auto-detected if omitted)")
    parser.add_argument("--dry-run", action="store_true", help="Validate and respond without writing files")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = detect_repo_root(args.repo_root)
    assignments_path = (repo_root / tag_source.ASSIGNMENTS_REL_PATH).resolve()
    series_index_path = (repo_root / tag_source.SERIES_INDEX_REL_PATH).resolve()
    registry_path = (repo_root / tag_source.REGISTRY_REL_PATH).resolve()
    aliases_path = (repo_root / tag_source.ALIASES_REL_PATH).resolve()
    backups_dir = (repo_root / BACKUPS_REL_DIR).resolve()
    allowed_paths = {assignments_path, registry_path, aliases_path}

    server = TagWriteServer(
        ("127.0.0.1", args.port),
        Handler,
        repo_root=repo_root,
        assignments_path=assignments_path,
        series_index_path=series_index_path,
        registry_path=registry_path,
        aliases_path=aliases_path,
        allowed_write_paths=allowed_paths,
        backups_dir=backups_dir,
        dry_run=args.dry_run,
    )
    mode = "dry-run" if args.dry_run else "write"
    print(
        f"tag_write_server listening on http://127.0.0.1:{args.port} "
        f"(mode={mode}, assignments={assignments_path}, series_index={series_index_path}, registry={registry_path}, aliases={aliases_path}, backups={backups_dir})"
    )
    server.log_event(
        "server_start",
        {
            "port": args.port,
            "mode": mode,
            "assignments_path": str(assignments_path.relative_to(repo_root)),
            "series_index_path": str(series_index_path.relative_to(repo_root)),
            "registry_path": str(registry_path.relative_to(repo_root)),
            "aliases_path": str(aliases_path.relative_to(repo_root)),
            "backups_dir": str(backups_dir.relative_to(repo_root)),
        },
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        server.log_event("server_stop", {"port": args.port})
        print("tag_write_server stopped")


if __name__ == "__main__":
    main()
