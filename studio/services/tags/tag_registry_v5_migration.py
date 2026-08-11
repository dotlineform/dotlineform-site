"""Project and validate the tag Registry document-link cutover."""

from __future__ import annotations

import copy
from typing import Any, Callable, Dict

from tags import tag_flat_identity_migration
from tags import tag_source_model as tag_source


LEGACY_REGISTRY_VERSION = "tag_registry_v4"
TARGET_REGISTRY_VERSION = "tag_registry_v5"
TARGET_ROW_KEYS = frozenset(("tag_id", "group", "doc_url", "updated_at_utc"))
DocumentUrlFactory = Callable[[str], str]


def project_tag_registry_v5(
    registry_payload: Dict[str, Any],
    aliases_payload: Dict[str, Any],
    assignments_payload: Dict[str, Any],
    *,
    now_utc: str,
    document_url_for_id: DocumentUrlFactory,
) -> tuple[Dict[str, Any], Dict[str, int]]:
    if registry_payload.get("tag_registry_version") != LEGACY_REGISTRY_VERSION:
        raise ValueError(
            f"tag Registry v5 migration requires {LEGACY_REGISTRY_VERSION}"
        )
    raw_tags = registry_payload.get("tags")
    if not isinstance(raw_tags, list):
        raise ValueError("tag_registry.tags must be an array")

    projected_tags: list[Dict[str, Any]] = []
    populated_count = 0
    empty_count = 0
    for idx, raw_tag in enumerate(raw_tags):
        field = f"tag_registry.tags[{idx}]"
        if not isinstance(raw_tag, dict):
            raise ValueError(f"{field} must be an object")
        if not isinstance(raw_tag.get("description"), str):
            raise ValueError(f"{field}.description must be a string")
        doc_id = str(raw_tag.get("doc_id") or "").strip()
        projected_row = copy.deepcopy(raw_tag)
        projected_row.pop("description", None)
        projected_row.pop("doc_id", None)
        if doc_id:
            projected_row["doc_url"] = [document_url_for_id(doc_id)]
            populated_count += 1
        else:
            projected_row["doc_url"] = []
            empty_count += 1
        projected_tags.append(projected_row)

    projected_registry = copy.deepcopy(registry_payload)
    projected_registry["tag_registry_version"] = TARGET_REGISTRY_VERSION
    projected_registry["updated_at_utc"] = now_utc
    projected_registry["tags"] = projected_tags
    reconciliation = validate_tag_registry_v5(
        projected_registry,
        aliases_payload,
        assignments_payload,
    )
    return projected_registry, {
        "input_tag_count": len(raw_tags),
        "output_tag_count": len(projected_tags),
        "description_fields_removed": len(projected_tags),
        "doc_id_fields_removed": len(projected_tags),
        "populated_doc_url_count": populated_count,
        "empty_doc_url_count": empty_count,
        "preserved_order": [
            str(row.get("tag_id") or "") for row in raw_tags
        ] == [
            str(row.get("tag_id") or "") for row in projected_tags
        ],
        **reconciliation,
    }


def validate_tag_registry_v5(
    registry_payload: Dict[str, Any],
    aliases_payload: Dict[str, Any],
    assignments_payload: Dict[str, Any],
) -> Dict[str, int]:
    if registry_payload.get("tag_registry_version") != TARGET_REGISTRY_VERSION:
        raise ValueError(f"tag registry must use {TARGET_REGISTRY_VERSION}")
    raw_tags = registry_payload.get("tags")
    if not isinstance(raw_tags, list):
        raise ValueError("tag_registry.tags must be an array")
    allowed_groups = tag_source.extract_allowed_groups(registry_payload)
    seen_tag_ids: set[str] = set()
    document_url_count = 0
    for index, raw_tag in enumerate(raw_tags):
        field = f"tag_registry.tags[{index}]"
        if not isinstance(raw_tag, dict) or set(raw_tag) != TARGET_ROW_KEYS:
            raise ValueError(f"{field} must use the exact Registry v5 row schema")
        tag_id = tag_source.sanitize_tag_id(raw_tag.get("tag_id"), f"{field}.tag_id")
        if tag_id in seen_tag_ids:
            raise ValueError(f"{field} duplicates tag_id '{tag_id}'")
        seen_tag_ids.add(tag_id)
        tag_source.sanitize_group(raw_tag.get("group"), allowed_groups, f"{field}.group")
        document_url_count += len(
            tag_source.sanitize_tag_document_urls(
                raw_tag.get("doc_url"),
                f"{field}.doc_url",
            )
        )
        if not isinstance(raw_tag.get("updated_at_utc"), str):
            raise ValueError(f"{field}.updated_at_utc must be a string")
    registry_stats = {
        "tag_count": len(raw_tags),
        "document_url_count": document_url_count,
    }
    reconciliation = tag_flat_identity_migration.validate_flat_identity_sources(
        registry_payload,
        aliases_payload,
        assignments_payload,
        expected_registry_version=TARGET_REGISTRY_VERSION,
    )
    return {**registry_stats, **reconciliation}


__all__ = [
    "LEGACY_REGISTRY_VERSION",
    "TARGET_REGISTRY_VERSION",
    "project_tag_registry_v5",
    "validate_tag_registry_v5",
]
