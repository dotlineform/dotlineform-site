"""Tag source artifact paths, loading defaults, and validation helpers."""

from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path
from typing import Any, Dict, Optional

from tags import tag_source_paths


SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
WORK_ID_RE = re.compile(r"^\d{5}$")
ALIAS_KEY_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
TAG_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
IMMUTABLE_DOC_ID = r"d-\d{8}-\d{6}-[a-f0-9]{6}"
CANONICAL_DOC_URL_PATTERNS = (
    re.compile(rf"^/analysis/\?doc={IMMUTABLE_DOC_ID}(?:&subdoc={IMMUTABLE_DOC_ID})?$"),
    re.compile(
        rf"^/docs/\?scope=(?:analysis|studio)&doc={IMMUTABLE_DOC_ID}"
        rf"(?:&subdoc={IMMUTABLE_DOC_ID})?$"
    ),
)
TAG_REGISTRY_REQUIRED_ROW_KEYS = frozenset(("tag_id", "group", "updated_at_utc"))
TAG_REGISTRY_OPTIONAL_ROW_KEYS = frozenset(("primary_document",))
TAG_REGISTRY_ROW_KEYS = TAG_REGISTRY_REQUIRED_ROW_KEYS | TAG_REGISTRY_OPTIONAL_ROW_KEYS
PRIMARY_DOCUMENT_KEYS = frozenset(("scope", "sub_scope", "doc_id"))

MAX_TAGS = 50
MAX_ALIAS_TARGETS = 50
MAX_ALIAS_TAGS_PER_ALIAS = 4
DEFAULT_ALLOWED_GROUPS = ["subject", "domain", "form", "theme"]
MANUAL_WEIGHT_VALUES = [0.3, 0.6, 0.9]
DEFAULT_TAG_WEIGHT = 0.6
TAG_REGISTRY_VERSION = "tag_registry_v6"
TAG_ALIASES_VERSION = "tag_aliases_v2"
TAG_ASSIGNMENTS_VERSION = "tag_assignments_v2"

TAG_SOURCE_ROOT_REL_PATH = tag_source_paths.TAG_SOURCE_ROOT_REL_PATH
ASSIGNMENTS_REL_PATH = tag_source_paths.TAG_ASSIGNMENTS_REL_PATH
REGISTRY_REL_PATH = tag_source_paths.TAG_REGISTRY_REL_PATH
ALIASES_REL_PATH = tag_source_paths.TAG_ALIASES_REL_PATH
GROUPS_REL_PATH = tag_source_paths.TAG_GROUPS_REL_PATH


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


def sanitize_alias(raw_alias: Any, field_name: str = "alias") -> str:
    alias = str(raw_alias or "").strip().lower()
    if not alias:
        raise ValueError(f"{field_name} must not be empty")
    if not ALIAS_KEY_RE.fullmatch(alias):
        raise ValueError(f"{field_name} must be slug-safe")
    return alias


def sanitize_alias_key(raw_key: Any, idx: int) -> str:
    return sanitize_alias(raw_key, f"tag_aliases.aliases key at index {idx}")


def extract_registry_tag_groups(
    registry_payload: Dict[str, Any],
    field_name: str = "tag_registry.tags",
) -> Dict[str, str]:
    raw_tags = registry_payload.get("tags")
    if not isinstance(raw_tags, list):
        raise ValueError(f"{field_name} must be an array")

    allowed_groups = extract_allowed_groups(registry_payload)
    groups_by_tag_id: Dict[str, str] = {}
    for idx, raw_tag in enumerate(raw_tags):
        if not isinstance(raw_tag, dict):
            raise ValueError(f"{field_name}[{idx}] must be an object")
        tag_id = sanitize_tag_id(raw_tag.get("tag_id"), f"{field_name}[{idx}].tag_id")
        group = sanitize_group(raw_tag.get("group"), allowed_groups, f"{field_name}[{idx}].group")
        if tag_id in groups_by_tag_id:
            raise ValueError(f"{field_name}[{idx}] duplicates tag_id '{tag_id}'")
        groups_by_tag_id[tag_id] = group
    return groups_by_tag_id


def enforce_alias_group_constraints(
    tags: list[str],
    registry_payload: Dict[str, Any],
    field_name: str,
) -> None:
    if not tags:
        raise ValueError(f"{field_name} must include at least one tag id")
    if len(tags) > MAX_ALIAS_TAGS_PER_ALIAS:
        raise ValueError(f"{field_name} may include at most {MAX_ALIAS_TAGS_PER_ALIAS} tag ids")

    groups_by_tag_id = extract_registry_tag_groups(registry_payload)
    seen_groups: set[str] = set()
    for idx, tag_id in enumerate(tags):
        group = groups_by_tag_id.get(tag_id)
        if group is None:
            raise ValueError(f"{field_name}[{idx}] is not present in registry: {tag_id}")
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
        description = sanitize_alias_description(raw_value.get("description", ""), f"{field_prefix}['{alias_key}'].description")
        return {"description": description, "tags": tags}

    tags = sanitize_tag_id_list(raw_value, f"{field_prefix}['{alias_key}']")
    return {"description": "", "tags": tags}


def sanitize_tag_id(raw_tag_id: Any, field_name: str = "tag_id") -> str:
    tag_id = str(raw_tag_id or "").strip().lower()
    if not TAG_ID_RE.fullmatch(tag_id):
        raise ValueError(f"{field_name} must be slug-safe")
    return tag_id


def sanitize_tag_document_url(raw_url: Any, field_name: str = "doc_url") -> str:
    if not isinstance(raw_url, str):
        raise ValueError(f"{field_name} must be a string")
    url = raw_url.strip()
    if not url:
        raise ValueError(f"{field_name} must not be empty")
    if not any(pattern.fullmatch(url) for pattern in CANONICAL_DOC_URL_PATTERNS):
        raise ValueError(
            f"{field_name} must be a supported canonical Docs Viewer URL"
        )
    return url


def sanitize_tag_document_urls(
    raw_urls: Any,
    field_name: str = "doc_url",
) -> list[str]:
    if not isinstance(raw_urls, list):
        raise ValueError(f"{field_name} must be an array")
    urls: list[str] = []
    seen: set[str] = set()
    for idx, raw_url in enumerate(raw_urls):
        url = sanitize_tag_document_url(raw_url, f"{field_name}[{idx}]")
        if url in seen:
            raise ValueError(f"{field_name}[{idx}] duplicates URL '{url}'")
        seen.add(url)
        urls.append(url)
    return urls


def sanitize_primary_document(
    raw_value: Any,
    field_name: str = "primary_document",
) -> Dict[str, str]:
    if not isinstance(raw_value, dict):
        raise ValueError(f"{field_name} must be an exact document target object")
    unexpected = sorted(set(raw_value) - PRIMARY_DOCUMENT_KEYS)
    missing = sorted(PRIMARY_DOCUMENT_KEYS - set(raw_value))
    if unexpected:
        raise ValueError(f"{field_name} has unsupported fields: {unexpected}")
    if missing:
        raise ValueError(f"{field_name} is missing fields: {missing}")
    scope = str(raw_value.get("scope") or "").strip()
    sub_scope = str(raw_value.get("sub_scope") or "").strip()
    doc_id = str(raw_value.get("doc_id") or "").strip()
    if scope != "analysis" or sub_scope != "tags":
        raise ValueError(f"{field_name} must target the Analysis Tags collection")
    if re.fullmatch(IMMUTABLE_DOC_ID, doc_id) is None:
        raise ValueError(f"{field_name}.doc_id must use immutable document identity")
    return {
        "scope": scope,
        "sub_scope": sub_scope,
        "doc_id": doc_id,
    }


def validate_registry_payload(payload: Dict[str, Any]) -> Dict[str, int]:
    if payload.get("tag_registry_version") != TAG_REGISTRY_VERSION:
        raise ValueError(f"tag registry must use {TAG_REGISTRY_VERSION}")
    raw_tags = payload.get("tags")
    if not isinstance(raw_tags, list):
        raise ValueError("tag_registry.tags must be an array")
    allowed_groups = extract_allowed_groups(payload)
    seen_tag_ids: set[str] = set()
    primary_count = 0
    for idx, raw_tag in enumerate(raw_tags):
        field = f"tag_registry.tags[{idx}]"
        if not isinstance(raw_tag, dict):
            raise ValueError(f"{field} must be an object")
        unexpected = sorted(set(raw_tag) - TAG_REGISTRY_ROW_KEYS)
        if unexpected:
            raise ValueError(f"{field} has unsupported fields: {unexpected}")
        missing = sorted(TAG_REGISTRY_REQUIRED_ROW_KEYS - set(raw_tag))
        if missing:
            raise ValueError(f"{field} is missing fields: {missing}")
        tag_id = sanitize_tag_id(raw_tag.get("tag_id"), f"{field}.tag_id")
        if tag_id in seen_tag_ids:
            raise ValueError(f"{field} duplicates tag_id '{tag_id}'")
        seen_tag_ids.add(tag_id)
        sanitize_group(raw_tag.get("group"), allowed_groups, f"{field}.group")
        if "primary_document" in raw_tag:
            sanitize_primary_document(
                raw_tag.get("primary_document"),
                f"{field}.primary_document",
            )
            primary_count += 1
        if not isinstance(raw_tag.get("updated_at_utc"), str):
            raise ValueError(f"{field}.updated_at_utc must be a string")
    return {"tag_count": len(raw_tags), "primary_document_count": primary_count}


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
            "tag_assignments_version": TAG_ASSIGNMENTS_VERSION,
            "updated_at_utc": utc_now(),
            "series": {},
        },
        "tag assignments",
    )


def load_registry(path: Path) -> Dict[str, Any]:
    payload = load_json_object(
        path,
        {
            "tag_registry_version": TAG_REGISTRY_VERSION,
            "updated_at_utc": utc_now(),
            "policy": {"allowed_groups": list(DEFAULT_ALLOWED_GROUPS)},
            "tags": [],
        },
        "tag registry",
    )
    validate_registry_payload(payload)
    return payload


def load_aliases(path: Path) -> Dict[str, Any]:
    return load_json_object(
        path,
        {
            "tag_aliases_version": TAG_ALIASES_VERSION,
            "updated_at_utc": utc_now(),
            "aliases": {},
        },
        "tag aliases",
    )
