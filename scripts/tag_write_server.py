#!/usr/bin/env python3
"""
README
======
Run:
  python3 scripts/tag_write_server.py
  python3 scripts/tag_write_server.py --port 8787
  python3 scripts/tag_write_server.py --repo-root /path/to/dotlineform-site
  python3 scripts/tag_write_server.py --dry-run

What it does:
  - Exposes a tiny localhost API for Tag Studio:
    - GET /health
    - POST /save-tags
    - POST /import-tag-registry
    - POST /import-tag-aliases
    - POST /delete-tag-alias
    - POST /mutate-tag-preview
    - POST /mutate-tag
  - Updates:
    - assets/data/tag_assignments.json (series tag saves)
    - assets/data/tag_registry.json (registry import replace/merge)
    - assets/data/tag_aliases.json (aliases import replace/merge/add)

Security constraints:
  - Binds to 127.0.0.1 only.
  - CORS allows only:
      http://localhost:*
      http://127.0.0.1:*
  - Hard allowlist for data writes permits only:
      <repo-root>/assets/data/tag_assignments.json
      <repo-root>/assets/data/tag_registry.json
      <repo-root>/assets/data/tag_aliases.json
      <repo-root>/assets/data/backups/*
  - Change event logs are written only to:
      <repo-root>/logs/tag_write_server.log
  - No external dependencies (Python stdlib only).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import tempfile
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

try:
    from script_logging import append_script_log
except ModuleNotFoundError:  # pragma: no cover - package import fallback
    from scripts.script_logging import append_script_log


SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
ALIAS_KEY_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
TAG_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*:[a-z0-9][a-z0-9-]*$")
MUTATE_ACTIONS = {"edit", "delete"}
MAX_TAGS = 50
MAX_IMPORT_TAGS = 10000
MAX_IMPORT_ALIASES = 10000
MAX_ALIAS_TARGETS = 50
TAG_STATUSES = {"active", "deprecated", "candidate"}
DEFAULT_ALLOWED_GROUPS = ["subject", "domain", "form", "theme"]

ALLOWED_ASSIGNMENTS_REL_PATH = Path("assets/data/tag_assignments.json")
ALLOWED_REGISTRY_REL_PATH = Path("assets/data/tag_registry.json")
ALLOWED_ALIASES_REL_PATH = Path("assets/data/tag_aliases.json")


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


def sanitize_tags(raw_tags: Any) -> list[str]:
    if not isinstance(raw_tags, list):
        raise ValueError("tags must be an array")
    if len(raw_tags) > MAX_TAGS:
        raise ValueError(f"tags may include at most {MAX_TAGS} entries")

    out: list[str] = []
    seen: set[str] = set()
    for idx, raw in enumerate(raw_tags):
        if not isinstance(raw, str):
            raise ValueError(f"tags[{idx}] must be a string")
        if raw == "":
            raise ValueError(f"tags[{idx}] must not be empty")
        if any((ch.isspace() or ord(ch) < 32 or ord(ch) == 127) for ch in raw):
            raise ValueError(f"tags[{idx}] contains whitespace or control characters")
        if raw in seen:
            continue
        seen.add(raw)
        out.append(raw)
    return out


def extract_allowed_groups(registry_payload: Dict[str, Any]) -> list[str]:
    policy = registry_payload.get("policy")
    if isinstance(policy, dict) and isinstance(policy.get("allowed_groups"), list):
        groups: list[str] = []
        for raw in policy.get("allowed_groups", []):
            value = str(raw or "").strip().lower()
            if not value or value in groups:
                continue
            groups.append(value)
        if groups:
            return groups
    return list(DEFAULT_ALLOWED_GROUPS)


def normalize_import_tag(raw_tag: Any, idx: int, allowed_groups: set[str]) -> Dict[str, str]:
    if not isinstance(raw_tag, dict):
        raise ValueError(f"import_registry.tags[{idx}] must be an object")

    tag_id = str(raw_tag.get("tag_id") or "").strip().lower()
    group = str(raw_tag.get("group") or "").strip().lower()
    status = str(raw_tag.get("status") or "active").strip().lower()
    description = str(raw_tag.get("description") or "").strip()

    if not TAG_ID_RE.fullmatch(tag_id):
        raise ValueError(f"import_registry.tags[{idx}].tag_id must match <group>:<slug>")
    if ":" not in tag_id:
        raise ValueError(f"import_registry.tags[{idx}].tag_id must include ':'")
    tag_group = tag_id.split(":", 1)[0]
    slug = tag_id.split(":", 1)[1]
    if group != tag_group:
        raise ValueError(f"import_registry.tags[{idx}] group must match tag_id prefix")
    if group not in allowed_groups:
        raise ValueError(f"import_registry.tags[{idx}].group is not allowed")
    if status not in TAG_STATUSES:
        raise ValueError(f"import_registry.tags[{idx}].status must be one of {sorted(TAG_STATUSES)}")

    return {
        "tag_id": tag_id,
        "group": group,
        "label": slug,
        "status": status,
        "description": description,
    }


def sanitize_import_registry(raw_registry: Any, allowed_groups: list[str]) -> list[Dict[str, str]]:
    if not isinstance(raw_registry, dict):
        raise ValueError("import_registry must be an object")

    raw_tags = raw_registry.get("tags")
    if not isinstance(raw_tags, list):
        raise ValueError("import_registry.tags must be an array")
    if len(raw_tags) > MAX_IMPORT_TAGS:
        raise ValueError(f"import_registry.tags may include at most {MAX_IMPORT_TAGS} entries")

    out_order: list[str] = []
    out_by_id: dict[str, Dict[str, str]] = {}
    allowed_set = set(allowed_groups)
    for idx, raw_tag in enumerate(raw_tags):
        normalized = normalize_import_tag(raw_tag, idx, allowed_set)
        tag_id = normalized["tag_id"]
        if tag_id not in out_by_id:
            out_order.append(tag_id)
        out_by_id[tag_id] = normalized

    return [out_by_id[tag_id] for tag_id in out_order]


def sanitize_alias_key(raw_key: Any, idx: int) -> str:
    key = str(raw_key or "").strip().lower()
    if not key:
        raise ValueError(f"import_aliases.aliases key at index {idx} must not be empty")
    if not ALIAS_KEY_RE.fullmatch(key):
        raise ValueError(f"import_aliases.aliases key at index {idx} must be slug-safe")
    return key


def sanitize_alias_value(raw_value: Any, alias_key: str) -> str | list[str]:
    if isinstance(raw_value, str):
        value = raw_value.strip().lower()
        if not TAG_ID_RE.fullmatch(value):
            raise ValueError(f"import_aliases.aliases['{alias_key}'] must be canonical <group>:<slug>")
        return value

    if not isinstance(raw_value, list):
        raise ValueError(f"import_aliases.aliases['{alias_key}'] must be a string or array of strings")
    if not raw_value:
        raise ValueError(f"import_aliases.aliases['{alias_key}'] must not be an empty array")
    if len(raw_value) > MAX_ALIAS_TARGETS:
        raise ValueError(f"import_aliases.aliases['{alias_key}'] may include at most {MAX_ALIAS_TARGETS} tag ids")

    out: list[str] = []
    seen: set[str] = set()
    for idx, raw_item in enumerate(raw_value):
        if not isinstance(raw_item, str):
            raise ValueError(f"import_aliases.aliases['{alias_key}'][{idx}] must be a string")
        value = raw_item.strip().lower()
        if not TAG_ID_RE.fullmatch(value):
            raise ValueError(f"import_aliases.aliases['{alias_key}'][{idx}] must be canonical <group>:<slug>")
        if value in seen:
            continue
        seen.add(value)
        out.append(value)

    if not out:
        raise ValueError(f"import_aliases.aliases['{alias_key}'] must include at least one tag id")
    return out


def sanitize_import_aliases(raw_aliases_payload: Any) -> tuple[list[str], Dict[str, str | list[str]]]:
    if not isinstance(raw_aliases_payload, dict):
        raise ValueError("import_aliases must be an object")

    raw_aliases = raw_aliases_payload.get("aliases")
    if not isinstance(raw_aliases, dict):
        raise ValueError("import_aliases.aliases must be an object")
    if len(raw_aliases) > MAX_IMPORT_ALIASES:
        raise ValueError(f"import_aliases.aliases may include at most {MAX_IMPORT_ALIASES} entries")

    order: list[str] = []
    by_key: Dict[str, str | list[str]] = {}
    for idx, (raw_key, raw_value) in enumerate(raw_aliases.items()):
        alias_key = sanitize_alias_key(raw_key, idx)
        alias_value = sanitize_alias_value(raw_value, alias_key)
        if alias_key not in by_key:
            order.append(alias_key)
        by_key[alias_key] = alias_value
    return order, by_key


def sanitize_import_filename(raw_filename: Any) -> str:
    if raw_filename is None:
        return ""
    if not isinstance(raw_filename, str):
        raise ValueError("import_filename must be a string")

    # Keep basename only to avoid logging local path details.
    normalized = raw_filename.replace("\\", "/").strip()
    if not normalized:
        return ""
    basename = normalized.split("/")[-1]
    if not basename:
        return ""
    if len(basename) > 255:
        raise ValueError("import_filename is too long")
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in basename):
        raise ValueError("import_filename contains control characters")
    return basename


def sanitize_tag_id(raw_tag_id: Any, field_name: str = "tag_id") -> str:
    tag_id = str(raw_tag_id or "").strip().lower()
    if not TAG_ID_RE.fullmatch(tag_id):
        raise ValueError(f"{field_name} must match <group>:<slug>")
    return tag_id


def sanitize_slug(raw_slug: Any, field_name: str = "slug") -> str:
    slug = str(raw_slug or "").strip().lower()
    if not SLUG_RE.fullmatch(slug):
        raise ValueError(f"{field_name} must be slug-safe")
    return slug


def load_json_object(path: Path, default_payload: Dict[str, Any], object_name: str) -> Dict[str, Any]:
    if not path.exists():
        return default_payload

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"failed to parse {object_name}: {exc}") from exc

    if not isinstance(payload, dict):
        raise ValueError(f"{object_name} must be a JSON object")
    return payload


def load_assignments(path: Path) -> Dict[str, Any]:
    return load_json_object(
        path,
        {
            "tag_assignments_version": "tag_assignments_v1",
            "updated_at_utc": utc_now(),
            "series": {},
        },
        "tag assignments",
    )


def load_registry(path: Path) -> Dict[str, Any]:
    return load_json_object(
        path,
        {
            "tag_registry_version": "tag_registry_v1",
            "updated_at_utc": utc_now(),
            "policy": {"allowed_groups": list(DEFAULT_ALLOWED_GROUPS)},
            "tags": [],
        },
        "tag registry",
    )


def load_aliases(path: Path) -> Dict[str, Any]:
    return load_json_object(
        path,
        {
            "tag_aliases_version": "tag_aliases_v1",
            "updated_at_utc": utc_now(),
            "aliases": {},
        },
        "tag aliases",
    )


def apply_assignment_update(payload: Dict[str, Any], series_id: str, tags: list[str], now_utc: str) -> Dict[str, Any]:
    if not isinstance(payload.get("series"), dict):
        payload["series"] = {}
    if "tag_assignments_version" not in payload:
        payload["tag_assignments_version"] = "tag_assignments_v1"

    series_obj = payload["series"]
    row = series_obj.get(series_id)
    if not isinstance(row, dict):
        row = {}
        series_obj[series_id] = row

    row["tags"] = tags
    row["updated_at_utc"] = now_utc
    payload["updated_at_utc"] = now_utc
    return payload


def apply_registry_import(
    existing_payload: Dict[str, Any],
    import_registry: Any,
    mode: str,
    now_utc: str,
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    if mode not in {"replace", "merge", "add"}:
        raise ValueError("mode must be one of: replace, merge, add")

    allowed_groups = extract_allowed_groups(existing_payload)
    imported_tags = sanitize_import_registry(import_registry, allowed_groups)

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

    import_order, import_by_key = sanitize_import_aliases(import_aliases_payload)
    raw_existing_aliases = existing_payload.get("aliases")
    existing_aliases = raw_existing_aliases if isinstance(raw_existing_aliases, dict) else {}

    existing_order: list[str] = []
    existing_by_key: Dict[str, str | list[str]] = {}
    for idx, (raw_key, raw_value) in enumerate(existing_aliases.items()):
        alias_key = sanitize_alias_key(raw_key, idx)
        alias_value = sanitize_alias_value(raw_value, alias_key)
        if alias_key not in existing_by_key:
            existing_order.append(alias_key)
        existing_by_key[alias_key] = alias_value

    overwritten = 0
    added = 0
    unchanged = 0
    removed = 0
    final_aliases: Dict[str, str | list[str]] = {}

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

    normalized_aliases: Dict[str, str | list[str]] = {}
    found = False
    for idx, (raw_key, raw_value) in enumerate(aliases.items()):
        key = sanitize_alias_key(raw_key, idx)
        value = sanitize_alias_value(raw_value, key)
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


def update_alias_value_for_tag(value: str | list[str], old_tag_id: str, new_tag_id: Optional[str]) -> tuple[Optional[str | list[str]], bool]:
    if isinstance(value, str):
        if value != old_tag_id:
            return value, False
        if new_tag_id is None:
            return None, True
        return new_tag_id, new_tag_id != value

    if not isinstance(value, list):
        return value, False

    changed = False
    out: list[str] = []
    seen: set[str] = set()
    for raw in value:
        if not isinstance(raw, str):
            continue
        item = raw
        if item == old_tag_id:
            if new_tag_id is None:
                changed = True
                continue
            if new_tag_id != old_tag_id:
                changed = True
                item = new_tag_id
        if item in seen:
            changed = True
            continue
        seen.add(item)
        out.append(item)

    if not out:
        return None, True if changed else False
    if len(out) == 1:
        return out[0], True if changed or (isinstance(value, list) and len(value) != 1) else changed
    return out, changed


def is_redundant_alias(alias_key: str, value: str | list[str]) -> bool:
    targets: list[str] = []
    if isinstance(value, str):
        targets = [value]
    elif isinstance(value, list):
        targets = [item for item in value if isinstance(item, str)]
    if len(targets) != 1:
        return False
    target = targets[0]
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

    final_aliases: Dict[str, str | list[str]] = {}
    rewritten = 0
    removed_empty = 0
    removed_redundant = 0

    for idx, (raw_key, raw_value) in enumerate(existing_aliases.items()):
        alias_key = sanitize_alias_key(raw_key, idx)
        alias_value = sanitize_alias_value(raw_value, alias_key)
        updated_value, changed = update_alias_value_for_tag(alias_value, old_tag_id, new_tag_id)
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

    rows_touched = 0
    refs_rewritten = 0

    for series_id, row in series_obj.items():
        if not isinstance(row, dict):
            continue
        tags = row.get("tags")
        if not isinstance(tags, list):
            continue
        changed = False
        out: list[str] = []
        seen: set[str] = set()
        for raw_tag in tags:
            if not isinstance(raw_tag, str):
                continue
            tag_value = raw_tag
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
            out.append(tag_value)

        if changed:
            row["tags"] = out
            row["updated_at_utc"] = now_utc
            rows_touched += 1

    assignments_payload["updated_at_utc"] = now_utc
    return assignments_payload, {
        "series_rows_touched": rows_touched,
        "series_tag_refs_rewritten": refs_rewritten,
    }


def mutate_registry_tag(
    registry_payload: Dict[str, Any],
    action: str,
    old_tag_id: str,
    now_utc: str,
    new_slug: Optional[str] = None,
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

    slug = sanitize_slug(new_slug, "new_slug")
    label = slug
    new_tag_id = f"{group}:{slug}"
    canonical_changed = new_tag_id != old_tag_id
    if canonical_changed and not allow_canonical_rename:
        raise ValueError("canonical rename is disabled for this request")
    if canonical_changed and new_tag_id in existing_ids:
        raise ValueError(f"target tag_id already exists: {new_tag_id}")

    updated_row = dict(target_row)
    updated_row["label"] = label
    updated_row["tag_id"] = new_tag_id
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
    touched = int(stats.get("series_rows_touched") or 0)
    refs = int(stats.get("series_tag_refs_rewritten") or 0)
    alias_rw = int(stats.get("aliases_rewritten") or 0)
    alias_empty = int(stats.get("aliases_removed_empty") or 0)
    alias_redundant = int(stats.get("aliases_removed_redundant") or 0)

    id_part = f"{old_tag_id} -> {new_tag_id}" if new_tag_id else old_tag_id
    return (
        f"mode {action}; tag {id_part}; "
        f"series rows {touched}; refs {refs}; "
        f"aliases rewritten {alias_rw}; aliases removed-empty {alias_empty}; "
        f"aliases removed-redundant {alias_redundant}"
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
        registry_path: Path,
        aliases_path: Path,
        allowed_write_paths: set[Path],
        backups_dir: Path,
        dry_run: bool,
    ):
        super().__init__(server_address, handler_cls)
        self.repo_root = repo_root.resolve()
        self.assignments_path = assignments_path
        self.registry_path = registry_path
        self.aliases_path = aliases_path
        self.allowed_write_paths = {path.resolve() for path in allowed_write_paths}
        self.backups_dir = backups_dir.resolve()
        self.dry_run = dry_run

    def log_event(self, event: str, details: Optional[Dict[str, Any]] = None) -> None:
        try:
            append_script_log(Path(__file__), event=event, details=details, repo_root=self.repo_root)
        except Exception:
            # Logging must never block API requests.
            pass


class Handler(BaseHTTPRequestHandler):
    server: TagWriteServer  # type: ignore[assignment]

    def do_OPTIONS(self) -> None:  # noqa: N802
        if self.path not in {"/save-tags", "/import-tag-registry", "/import-tag-aliases", "/delete-tag-alias", "/mutate-tag", "/mutate-tag-preview"}:
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

        if self.path != "/health":
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

        try:
            if self.path == "/save-tags":
                self._handle_save_tags(allowed)
                return
            if self.path == "/import-tag-registry":
                self._handle_import_tag_registry(allowed)
                return
            if self.path == "/import-tag-aliases":
                self._handle_import_tag_aliases(allowed)
                return
            if self.path == "/delete-tag-alias":
                self._handle_delete_tag_alias(allowed)
                return
            if self.path == "/mutate-tag":
                self._handle_mutate_tag(allowed, preview=False)
                return
            if self.path == "/mutate-tag-preview":
                self._handle_mutate_tag(allowed, preview=True)
                return
            self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "not found"}, allowed)
        except ValueError as exc:
            self.server.log_event("request_error", {"path": self.path, "error": str(exc), "kind": "validation"})
            self._send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)}, allowed)
        except Exception as exc:  # noqa: BLE001
            self.server.log_event("request_error", {"path": self.path, "error": str(exc), "kind": "internal"})
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"ok": False, "error": f"internal error: {exc}"}, allowed)

    def _handle_save_tags(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        series_id = body.get("series_id")
        tags = body.get("tags")
        _ = body.get("client_time_utc")

        if not isinstance(series_id, str) or not series_id or not SLUG_RE.fullmatch(series_id):
            raise ValueError("series_id must be a non-empty slug-safe string")

        sanitized_tags = sanitize_tags(tags)
        now_utc = utc_now()

        payload = load_assignments(self.server.assignments_path)
        updated_payload = apply_assignment_update(payload, series_id, sanitized_tags, now_utc)

        response_payload: Dict[str, Any] = {
            "ok": True,
            "series_id": series_id,
            "updated_at_utc": now_utc,
            "tag_count": len(sanitized_tags),
        }

        target_path = self.server.assignments_path.resolve()
        if not self.server.dry_run:
            if target_path not in self.server.allowed_write_paths:
                raise ValueError("write target not allowlisted")
            atomic_write(target_path, updated_payload, self.server.backups_dir)
        else:
            response_payload["dry_run"] = True
            response_payload["would_write"] = {
                "series_id": series_id,
                "tags": sanitized_tags,
                "updated_at_utc": now_utc,
            }

        self.server.log_event(
            "save_tags",
            {
                "series_id": series_id,
                "tag_count": len(sanitized_tags),
                "dry_run": self.server.dry_run,
            },
        )
        self._send_json(HTTPStatus.OK, response_payload, allowed)

    def _handle_import_tag_registry(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        mode = str(body.get("mode") or "").strip().lower()
        import_registry = body.get("import_registry")
        import_filename = sanitize_import_filename(body.get("import_filename"))
        _ = body.get("client_time_utc")

        now_utc = utc_now()
        existing_payload = load_registry(self.server.registry_path)
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
        self._send_json(HTTPStatus.OK, response_payload, allowed)

    def _handle_import_tag_aliases(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        mode = str(body.get("mode") or "").strip().lower()
        import_aliases = body.get("import_aliases")
        import_filename = sanitize_import_filename(body.get("import_filename"))
        _ = body.get("client_time_utc")

        now_utc = utc_now()
        existing_payload = load_aliases(self.server.aliases_path)
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
        self._send_json(HTTPStatus.OK, response_payload, allowed)

    def _handle_delete_tag_alias(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        alias_raw = body.get("alias")
        alias_key = sanitize_alias_key(alias_raw, 0)
        _ = body.get("client_time_utc")

        now_utc = utc_now()
        existing_payload = load_aliases(self.server.aliases_path)
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
        self._send_json(HTTPStatus.OK, response_payload, allowed)

    def _handle_mutate_tag(self, allowed: Optional[str], preview: bool = False) -> None:
        body = self._read_json_body()
        action = str(body.get("action") or "").strip().lower()
        old_tag_id = sanitize_tag_id(body.get("tag_id"), "tag_id")
        raw_allow_canonical_rename = body.get("allow_canonical_rename", False)
        if not isinstance(raw_allow_canonical_rename, bool):
            raise ValueError("allow_canonical_rename must be a boolean")
        allow_canonical_rename = raw_allow_canonical_rename
        _ = body.get("client_time_utc")

        if action not in MUTATE_ACTIONS:
            raise ValueError(f"action must be one of: {sorted(MUTATE_ACTIONS)}")

        new_slug: Optional[str] = None
        if action == "edit":
            new_slug = sanitize_slug(body.get("new_slug"), "new_slug")

        now_utc = utc_now()
        registry_payload = load_registry(self.server.registry_path)
        aliases_payload = load_aliases(self.server.aliases_path)
        assignments_payload = load_assignments(self.server.assignments_path)

        registry_updated, mutate_meta = mutate_registry_tag(
            registry_payload,
            action=action,
            old_tag_id=old_tag_id,
            now_utc=now_utc,
            new_slug=new_slug,
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
            }

        stats: Dict[str, Any] = {
            "action": action,
            "old_tag_id": old_tag_id,
            "new_tag_id": rewrite_to,
            "canonical_changed": bool(mutate_meta.get("canonical_changed")),
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
    assignments_path = (repo_root / ALLOWED_ASSIGNMENTS_REL_PATH).resolve()
    registry_path = (repo_root / ALLOWED_REGISTRY_REL_PATH).resolve()
    aliases_path = (repo_root / ALLOWED_ALIASES_REL_PATH).resolve()
    backups_dir = (repo_root / "assets/data/backups").resolve()
    allowed_paths = {assignments_path, registry_path, aliases_path}

    server = TagWriteServer(
        ("127.0.0.1", args.port),
        Handler,
        repo_root=repo_root,
        assignments_path=assignments_path,
        registry_path=registry_path,
        aliases_path=aliases_path,
        allowed_write_paths=allowed_paths,
        backups_dir=backups_dir,
        dry_run=args.dry_run,
    )
    mode = "dry-run" if args.dry_run else "write"
    print(
        f"tag_write_server listening on http://127.0.0.1:{args.port} "
        f"(mode={mode}, assignments={assignments_path}, registry={registry_path}, aliases={aliases_path}, backups={backups_dir})"
    )
    server.log_event(
        "server_start",
        {
            "port": args.port,
            "mode": mode,
            "assignments_path": str(assignments_path.relative_to(repo_root)),
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
