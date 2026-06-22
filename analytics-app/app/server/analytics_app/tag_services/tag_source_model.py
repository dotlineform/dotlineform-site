"""Tag source artifact paths, loading defaults, and validation helpers."""

from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path
from typing import Any, Dict, Optional

from tag_services import tag_source_paths


SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
WORK_ID_RE = re.compile(r"^\d{5}$")
ALIAS_KEY_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
TAG_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*:[a-z0-9][a-z0-9-]*$")

MAX_TAGS = 50
MAX_IMPORT_TAGS = 10000
MAX_IMPORT_ALIASES = 10000
MAX_ALIAS_TARGETS = 50
MAX_ALIAS_TAGS_PER_ALIAS = 4
DEFAULT_ALLOWED_GROUPS = ["subject", "domain", "form", "theme"]
MANUAL_WEIGHT_VALUES = [0.3, 0.6, 0.9]
DEFAULT_TAG_WEIGHT = 0.6

TAG_SOURCE_ROOT_REL_PATH = tag_source_paths.TAG_SOURCE_ROOT_REL_PATH
ASSIGNMENTS_REL_PATH = tag_source_paths.TAG_ASSIGNMENTS_REL_PATH
REGISTRY_REL_PATH = tag_source_paths.TAG_REGISTRY_REL_PATH
ALIASES_REL_PATH = tag_source_paths.TAG_ALIASES_REL_PATH
GROUPS_REL_PATH = tag_source_paths.TAG_GROUPS_REL_PATH
SERIES_INDEX_REL_PATH = tag_source_paths.SERIES_INDEX_REL_PATH


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sanitize_manual_weight(raw_weight: Any, field_name: str, strict: bool = True) -> float:
    if raw_weight is None:
        if strict:
            raise ValueError(f"{field_name} is required")
        return DEFAULT_TAG_WEIGHT
    try:
        value = float(raw_weight)
    except Exception as exc:  # noqa: BLE001
        if strict:
            raise ValueError(f"{field_name} must be numeric") from exc
        return DEFAULT_TAG_WEIGHT

    for allowed in MANUAL_WEIGHT_VALUES:
        if abs(value - allowed) < 1e-9:
            return allowed

    if strict:
        raise ValueError(f"{field_name} must be one of: {MANUAL_WEIGHT_VALUES}")

    closest = MANUAL_WEIGHT_VALUES[0]
    diff = abs(value - closest)
    for allowed in MANUAL_WEIGHT_VALUES[1:]:
        current = abs(value - allowed)
        if current < diff:
            closest = allowed
            diff = current
    return closest


def build_assignment_tag(tag_id: str, w_manual: float, alias: str = "") -> Dict[str, Any]:
    row = {
        "tag_id": tag_id,
        "w_manual": sanitize_manual_weight(w_manual, "w_manual", strict=False),
    }
    if alias:
        row["alias"] = alias
    return row


def sanitize_assignment_alias(raw_alias: Any, field_name: str) -> str:
    alias = str(raw_alias or "").strip().lower()
    if not alias:
        raise ValueError(f"{field_name} must not be empty")
    if not ALIAS_KEY_RE.fullmatch(alias):
        raise ValueError(f"{field_name} must be slug-safe")
    return alias


def normalize_assignment_tag(raw_tag: Any, field_name: str, strict: bool = False) -> Optional[Dict[str, Any]]:
    if isinstance(raw_tag, str):
        if strict:
            raise ValueError(f"{field_name} must be an object with tag_id, w_manual")
        try:
            tag_id = sanitize_tag_id(raw_tag, field_name)
        except ValueError:
            return None
        return build_assignment_tag(tag_id, DEFAULT_TAG_WEIGHT)

    if not isinstance(raw_tag, dict):
        if strict:
            raise ValueError(f"{field_name} must be an object with tag_id, w_manual")
        return None

    try:
        tag_id = sanitize_tag_id(raw_tag.get("tag_id"), f"{field_name}.tag_id")
    except ValueError:
        if strict:
            raise
        return None
    w_manual = sanitize_manual_weight(raw_tag.get("w_manual"), f"{field_name}.w_manual", strict=strict)
    alias = ""
    if "alias" in raw_tag and raw_tag.get("alias") is not None:
        alias = sanitize_assignment_alias(raw_tag.get("alias"), f"{field_name}.alias")
    return build_assignment_tag(tag_id, w_manual, alias)


def sanitize_assignment_tags(raw_tags: Any, field_name: str = "tags", strict: bool = True) -> list[Dict[str, Any]]:
    if not isinstance(raw_tags, list):
        raise ValueError(f"{field_name} must be an array")
    if len(raw_tags) > MAX_TAGS:
        raise ValueError(f"{field_name} may include at most {MAX_TAGS} entries")

    out: list[Dict[str, Any]] = []
    seen: set[str] = set()
    for idx, raw in enumerate(raw_tags):
        row = normalize_assignment_tag(raw, f"{field_name}[{idx}]", strict=strict)
        if row is None:
            continue
        tag_id = row["tag_id"]
        if tag_id in seen:
            continue
        seen.add(tag_id)
        out.append(row)
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
    return {
        "tag_id": tag_id,
        "group": group,
        "label": slug,
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


def enforce_alias_group_constraints(tags: list[str], field_name: str) -> None:
    if not tags:
        raise ValueError(f"{field_name} must include at least one tag id")
    if len(tags) > MAX_ALIAS_TAGS_PER_ALIAS:
        raise ValueError(f"{field_name} may include at most {MAX_ALIAS_TAGS_PER_ALIAS} tag ids")

    seen_groups: set[str] = set()
    for idx, tag_id in enumerate(tags):
        group = tag_id.split(":", 1)[0]
        if group in seen_groups:
            raise ValueError(f"{field_name}[{idx}] duplicates group '{group}'")
        seen_groups.add(group)


def sanitize_alias_description(raw_description: Any, field_name: str) -> str:
    if raw_description is None:
        return ""
    if not isinstance(raw_description, str):
        raise ValueError(f"{field_name} must be a string")
    return raw_description.strip()


def sanitize_alias_entry(raw_value: Any, alias_key: str, field_prefix: str) -> Dict[str, Any]:
    if isinstance(raw_value, dict):
        tags = sanitize_tag_id_list(raw_value.get("tags"), f"{field_prefix}['{alias_key}'].tags")
        enforce_alias_group_constraints(tags, f"{field_prefix}['{alias_key}'].tags")
        description = sanitize_alias_description(raw_value.get("description", ""), f"{field_prefix}['{alias_key}'].description")
        return {"description": description, "tags": tags}

    tags = sanitize_tag_id_list(raw_value, f"{field_prefix}['{alias_key}']")
    enforce_alias_group_constraints(tags, f"{field_prefix}['{alias_key}']")
    return {"description": "", "tags": tags}


def sanitize_import_aliases(raw_aliases_payload: Any) -> tuple[list[str], Dict[str, Dict[str, Any]]]:
    if not isinstance(raw_aliases_payload, dict):
        raise ValueError("import_aliases must be an object")

    raw_aliases = raw_aliases_payload.get("aliases")
    if not isinstance(raw_aliases, dict):
        raise ValueError("import_aliases.aliases must be an object")
    if len(raw_aliases) > MAX_IMPORT_ALIASES:
        raise ValueError(f"import_aliases.aliases may include at most {MAX_IMPORT_ALIASES} entries")

    order: list[str] = []
    by_key: Dict[str, Dict[str, Any]] = {}
    for idx, (raw_key, raw_value) in enumerate(raw_aliases.items()):
        alias_key = sanitize_alias_key(raw_key, idx)
        alias_value = sanitize_alias_entry(raw_value, alias_key, "import_aliases.aliases")
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


def sanitize_group(raw_group: Any, allowed_groups: list[str], field_name: str = "group") -> str:
    group = str(raw_group or "").strip().lower()
    if group not in allowed_groups:
        raise ValueError(f"{field_name} must be one of: {allowed_groups}")
    return group


def sanitize_tag_id_list(raw_value: Any, field_name: str = "tag_ids") -> list[str]:
    values: list[Any]
    if isinstance(raw_value, str):
        values = [raw_value]
    elif isinstance(raw_value, list):
        values = raw_value
    else:
        raise ValueError(f"{field_name} must be a string or array of strings")

    if not values:
        raise ValueError(f"{field_name} must include at least one tag_id")
    if len(values) > MAX_ALIAS_TARGETS:
        raise ValueError(f"{field_name} may include at most {MAX_ALIAS_TARGETS} tag ids")

    out: list[str] = []
    seen: set[str] = set()
    for idx, raw in enumerate(values):
        tag_id = sanitize_tag_id(raw, f"{field_name}[{idx}]")
        if tag_id in seen:
            continue
        seen.add(tag_id)
        out.append(tag_id)

    if not out:
        raise ValueError(f"{field_name} must include at least one tag_id")
    return out


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


def load_series_index(path: Path) -> Dict[str, Any]:
    return load_json_object(
        path,
        {
            "header": {},
            "series": {},
        },
        "series index",
    )


def normalize_assignment_rows_for_compare(rows: Any) -> list[Dict[str, Any]]:
    return sanitize_assignment_tags(rows if rows is not None else [], "tags", strict=False)


def normalize_assignment_series_row_for_compare(row: Any) -> Dict[str, Any]:
    raw_row = row if isinstance(row, dict) else {}
    works_obj = raw_row.get("works") if isinstance(raw_row.get("works"), dict) else {}
    works: Dict[str, Dict[str, Any]] = {}

    for raw_work_id, raw_work_row in works_obj.items():
        work_id = str(raw_work_id or "").strip()
        if not WORK_ID_RE.fullmatch(work_id):
            continue
        if not isinstance(raw_work_row, dict):
            continue
        works[work_id] = {
            "tags": normalize_assignment_rows_for_compare(raw_work_row.get("tags", []))
        }

    normalized: Dict[str, Any] = {
        "tags": normalize_assignment_rows_for_compare(raw_row.get("tags", []))
    }
    if works:
        normalized["works"] = dict(sorted(works.items()))
    return normalized


def assignment_series_rows_equal(left: Any, right: Any) -> bool:
    a = normalize_assignment_series_row_for_compare(left)
    b = normalize_assignment_series_row_for_compare(right)
    return a == b


def sanitize_import_assignments_session(payload: Any) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("import_assignments must be a JSON object")

    raw_series = payload.get("series")
    if not isinstance(raw_series, dict):
        raise ValueError("import_assignments.series must be an object")

    out_series: Dict[str, Dict[str, Any]] = {}
    for raw_series_id, raw_entry in raw_series.items():
        series_id = str(raw_series_id or "").strip().lower()
        if not series_id or not SLUG_RE.fullmatch(series_id):
            raise ValueError(f"import_assignments.series[{raw_series_id!r}] must use a slug-safe series id")
        out_series[series_id] = sanitize_import_assignments_series_entry(raw_entry, series_id)

    return {
        "version": str(payload.get("version") or "").strip(),
        "updated_at_utc": str(payload.get("updated_at_utc") or "").strip(),
        "series": out_series,
    }


def sanitize_import_assignments_series_entry(raw_entry: Any, series_id: str) -> Dict[str, Any]:
    if not isinstance(raw_entry, dict):
        raise ValueError(f"import_assignments.series[{series_id}] must be an object")

    staged_row = sanitize_import_assignment_series_row(raw_entry.get("staged_row"), f"import_assignments.series[{series_id}].staged_row")
    base_snapshot = sanitize_import_assignment_series_row(
        raw_entry.get("base_row_snapshot"),
        f"import_assignments.series[{series_id}].base_row_snapshot",
        allow_missing=True,
    )
    base_updated = str(raw_entry.get("base_series_updated_at_utc") or "").strip()
    staged_at = str(raw_entry.get("staged_at_utc") or "").strip()
    return {
        "base_series_updated_at_utc": base_updated,
        "base_row_snapshot": base_snapshot,
        "staged_row": staged_row,
        "staged_at_utc": staged_at,
    }


def sanitize_import_assignment_series_row(raw_row: Any, field_name: str, allow_missing: bool = False) -> Dict[str, Any]:
    if raw_row is None and allow_missing:
        return {"tags": []}
    if not isinstance(raw_row, dict):
        raise ValueError(f"{field_name} must be an object")

    tags = sanitize_assignment_tags(raw_row.get("tags", []), f"{field_name}.tags", strict=True)
    works_out: Dict[str, Dict[str, Any]] = {}
    raw_works = raw_row.get("works")
    if raw_works is not None:
        if not isinstance(raw_works, dict):
            raise ValueError(f"{field_name}.works must be an object")
        for raw_work_id, raw_work_row in raw_works.items():
            work_id = str(raw_work_id or "").strip()
            if not WORK_ID_RE.fullmatch(work_id):
                raise ValueError(f"{field_name}.works keys must be 5-digit work ids")
            if not isinstance(raw_work_row, dict):
                raise ValueError(f"{field_name}.works[{work_id}] must be an object")
            works_out[work_id] = {
                "tags": sanitize_assignment_tags(raw_work_row.get("tags", []), f"{field_name}.works[{work_id}].tags", strict=True)
            }

    out: Dict[str, Any] = {"tags": tags}
    if works_out:
        out["works"] = dict(sorted(works_out.items()))
    return out


def build_series_work_membership(series_index_payload: Dict[str, Any]) -> Dict[str, set[str]]:
    raw_series = series_index_payload.get("series")
    if not isinstance(raw_series, dict):
        return {}

    membership: Dict[str, set[str]] = {}
    for raw_series_id, raw_row in raw_series.items():
        series_id = str(raw_series_id or "").strip().lower()
        if not series_id or not isinstance(raw_row, dict):
            continue
        works = raw_row.get("works")
        members: set[str] = set()
        if isinstance(works, list):
            for raw_work_id in works:
                work_id = str(raw_work_id or "").strip()
                if WORK_ID_RE.fullmatch(work_id):
                    members.add(work_id)
        membership[series_id] = members
    return membership
