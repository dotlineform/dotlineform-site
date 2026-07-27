#!/usr/bin/env python3
"""Project and validate retirement of canonical tag registry labels."""

from __future__ import annotations

import copy
from typing import Any, Dict

from tags import tag_flat_identity_migration
from tags import tag_source_model as tag_source


LEGACY_REGISTRY_VERSION = "tag_registry_v2"


def project_registry_label_retirement(
    registry_payload: Dict[str, Any],
    aliases_payload: Dict[str, Any],
    assignments_payload: Dict[str, Any],
    *,
    now_utc: str,
) -> tuple[Dict[str, Any], Dict[str, int]]:
    if registry_payload.get("tag_registry_version") != LEGACY_REGISTRY_VERSION:
        raise ValueError(
            "tag registry label retirement requires "
            f"{LEGACY_REGISTRY_VERSION}"
        )

    raw_tags = registry_payload.get("tags")
    if not isinstance(raw_tags, list):
        raise ValueError("tag_registry.tags must be an array")

    allowed_groups = tag_source.extract_allowed_groups(registry_payload)
    projected_tags: list[Dict[str, Any]] = []
    seen_tag_ids: set[str] = set()
    for idx, raw_tag in enumerate(raw_tags):
        if not isinstance(raw_tag, dict):
            raise ValueError(f"tag_registry.tags[{idx}] must be an object")
        tag_id = tag_source.sanitize_tag_id(
            raw_tag.get("tag_id"),
            f"tag_registry.tags[{idx}].tag_id",
        )
        if tag_id in seen_tag_ids:
            raise ValueError(f"tag_registry.tags[{idx}] duplicates tag_id '{tag_id}'")
        seen_tag_ids.add(tag_id)
        tag_source.sanitize_group(
            raw_tag.get("group"),
            allowed_groups,
            f"tag_registry.tags[{idx}].group",
        )
        if "groups" in raw_tag or isinstance(raw_tag.get("group"), list):
            raise ValueError(f"tag_registry.tags[{idx}] must have one scalar group")
        label = str(raw_tag.get("label") or "").strip().lower()
        if label != tag_id:
            raise ValueError(
                f"tag_registry.tags[{idx}].label must match tag_id '{tag_id}'"
            )
        if not isinstance(raw_tag.get("description", ""), str):
            raise ValueError(
                f"tag_registry.tags[{idx}].description must be a string"
            )

        projected_row = copy.deepcopy(raw_tag)
        projected_row.pop("label", None)
        projected_tags.append(projected_row)

    projected_registry = copy.deepcopy(registry_payload)
    projected_registry["tag_registry_version"] = tag_source.TAG_REGISTRY_VERSION
    projected_registry["updated_at_utc"] = now_utc
    projected_registry["tags"] = projected_tags

    reconciliation = tag_flat_identity_migration.validate_flat_identity_sources(
        projected_registry,
        aliases_payload,
        assignments_payload,
    )
    return projected_registry, {
        "input_tag_count": len(raw_tags),
        "output_tag_count": len(projected_tags),
        "labels_removed": len(projected_tags),
        "preserved_tag_id_count": len(projected_tags),
        "preserved_group_count": len(projected_tags),
        "preserved_description_count": len(projected_tags),
        "preserved_row_timestamp_count": len(projected_tags),
        **reconciliation,
    }


def validate_registry_label_retirement(
    registry_payload: Dict[str, Any],
    aliases_payload: Dict[str, Any],
    assignments_payload: Dict[str, Any],
) -> Dict[str, int]:
    return tag_flat_identity_migration.validate_flat_identity_sources(
        registry_payload,
        aliases_payload,
        assignments_payload,
    )
