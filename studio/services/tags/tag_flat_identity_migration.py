"""Project and validate the one-time flat tag identity cutover."""

from __future__ import annotations

import copy
import re
from typing import Any, Dict

from tags import tag_source_model as tag_source


LEGACY_TAG_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*:[a-z0-9][a-z0-9-]*$")


def _legacy_tag_id(raw_tag_id: Any, field_name: str) -> str:
    tag_id = str(raw_tag_id or "").strip().lower()
    if not LEGACY_TAG_ID_RE.fullmatch(tag_id):
        raise ValueError(f"{field_name} must match the legacy <group>:<slug> shape")
    return tag_id


def _project_assignment_tags(
    raw_tags: Any,
    field_name: str,
    id_map: Dict[str, str],
) -> list[Dict[str, Any]]:
    if not isinstance(raw_tags, list):
        raise ValueError(f"{field_name} must be an array")

    projected: list[Dict[str, Any]] = []
    seen: set[str] = set()
    for idx, raw_tag in enumerate(raw_tags):
        if not isinstance(raw_tag, dict):
            raise ValueError(f"{field_name}[{idx}] must be an object")
        old_tag_id = _legacy_tag_id(raw_tag.get("tag_id"), f"{field_name}[{idx}].tag_id")
        new_tag_id = id_map.get(old_tag_id)
        if new_tag_id is None:
            raise ValueError(f"{field_name}[{idx}].tag_id is not present in registry: {old_tag_id}")
        if new_tag_id in seen:
            raise ValueError(f"{field_name}[{idx}] creates duplicate flat tag_id '{new_tag_id}'")
        seen.add(new_tag_id)
        weight = tag_source.sanitize_manual_weight(
            raw_tag.get("w_manual"),
            f"{field_name}[{idx}].w_manual",
            strict=True,
        )
        alias = ""
        if raw_tag.get("alias") is not None:
            alias = tag_source.sanitize_assignment_alias(
                raw_tag.get("alias"),
                f"{field_name}[{idx}].alias",
            )
        projected.append(tag_source.build_assignment_tag(new_tag_id, weight, alias))
    return projected


def project_flat_identity_sources(
    registry_payload: Dict[str, Any],
    aliases_payload: Dict[str, Any],
    assignments_payload: Dict[str, Any],
    *,
    now_utc: str,
) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    expected_versions = {
        "registry": "tag_registry_v1",
        "aliases": "tag_aliases_v1",
        "assignments": "tag_assignments_v1",
    }
    actual_versions = {
        "registry": registry_payload.get("tag_registry_version"),
        "aliases": aliases_payload.get("tag_aliases_version"),
        "assignments": assignments_payload.get("tag_assignments_version"),
    }
    if actual_versions != expected_versions:
        raise ValueError(
            f"flat identity migration requires legacy source versions: {actual_versions}"
        )

    raw_tags = registry_payload.get("tags")
    if not isinstance(raw_tags, list):
        raise ValueError("tag_registry.tags must be an array")
    allowed_groups = tag_source.extract_allowed_groups(registry_payload)
    id_map: Dict[str, str] = {}
    projected_tags: list[Dict[str, Any]] = []
    preserved_group_count = 0
    preserved_description_count = 0
    for idx, raw_tag in enumerate(raw_tags):
        if not isinstance(raw_tag, dict):
            raise ValueError(f"tag_registry.tags[{idx}] must be an object")
        old_tag_id = _legacy_tag_id(
            raw_tag.get("tag_id"),
            f"tag_registry.tags[{idx}].tag_id",
        )
        old_group, old_slug = old_tag_id.split(":", 1)
        group = tag_source.sanitize_group(
            raw_tag.get("group"),
            allowed_groups,
            f"tag_registry.tags[{idx}].group",
        )
        if group != old_group:
            raise ValueError(
                f"tag_registry.tags[{idx}] group '{group}' does not match '{old_tag_id}'"
            )
        if "groups" in raw_tag or isinstance(raw_tag.get("group"), list):
            raise ValueError(f"tag_registry.tags[{idx}] must have one scalar group")
        label = str(raw_tag.get("label") or "").strip().lower()
        if label != old_slug:
            raise ValueError(
                f"tag_registry.tags[{idx}] label '{label}' does not match '{old_tag_id}'"
            )
        if old_tag_id in id_map:
            raise ValueError(f"duplicate legacy tag_id: {old_tag_id}")
        if old_slug in id_map.values():
            raise ValueError(f"duplicate flat tag_id: {old_slug}")
        id_map[old_tag_id] = old_slug

        projected_row = dict(raw_tag)
        projected_row["tag_id"] = old_slug
        projected_row["group"] = group
        projected_row.pop("label", None)
        projected_row["updated_at_utc"] = now_utc
        projected_row.pop("groups", None)
        projected_tags.append(projected_row)
        preserved_group_count += 1
        if projected_row.get("description") == raw_tag.get("description"):
            preserved_description_count += 1

    projected_registry = copy.deepcopy(registry_payload)
    projected_registry["tag_registry_version"] = tag_source.TAG_REGISTRY_VERSION
    projected_registry["updated_at_utc"] = now_utc
    projected_registry["tags"] = projected_tags

    raw_aliases = aliases_payload.get("aliases")
    if not isinstance(raw_aliases, dict):
        raise ValueError("tag_aliases.aliases must be an object")
    projected_aliases_by_key: Dict[str, Dict[str, Any]] = {}
    input_alias_target_count = 0
    alias_target_count = 0
    aliases_removed_redundant = 0
    for idx, (raw_key, raw_value) in enumerate(raw_aliases.items()):
        alias_key = tag_source.sanitize_alias_key(raw_key, idx)
        if not isinstance(raw_value, dict):
            raise ValueError(f"tag_aliases.aliases['{alias_key}'] must be an object")
        raw_targets = raw_value.get("tags")
        if not isinstance(raw_targets, list) or not raw_targets:
            raise ValueError(
                f"tag_aliases.aliases['{alias_key}'].tags must be a non-empty array"
            )
        input_alias_target_count += len(raw_targets)
        projected_targets: list[str] = []
        seen_targets: set[str] = set()
        for target_idx, raw_target in enumerate(raw_targets):
            old_target = _legacy_tag_id(
                raw_target,
                f"tag_aliases.aliases['{alias_key}'].tags[{target_idx}]",
            )
            new_target = id_map.get(old_target)
            if new_target is None:
                raise ValueError(
                    f"tag_aliases.aliases['{alias_key}'].tags[{target_idx}] "
                    f"is not present in registry: {old_target}"
                )
            if new_target in seen_targets:
                raise ValueError(
                    f"tag_aliases.aliases['{alias_key}'] creates duplicate target "
                    f"'{new_target}'"
                )
            seen_targets.add(new_target)
            projected_targets.append(new_target)
            alias_target_count += 1
        description = tag_source.sanitize_alias_description(
            raw_value.get("description", ""),
            f"tag_aliases.aliases['{alias_key}'].description",
        )
        if len(projected_targets) == 1 and projected_targets[0] == alias_key:
            if description:
                raise ValueError(
                    f"redundant flat alias '{alias_key}' has a non-empty description"
                )
            aliases_removed_redundant += 1
            alias_target_count -= 1
            continue
        tag_source.enforce_alias_group_constraints(
            projected_targets,
            projected_registry,
            f"tag_aliases.aliases['{alias_key}'].tags",
        )
        projected_aliases_by_key[alias_key] = {
            "description": description,
            "tags": projected_targets,
        }

    projected_aliases = copy.deepcopy(aliases_payload)
    projected_aliases["tag_aliases_version"] = tag_source.TAG_ALIASES_VERSION
    projected_aliases["updated_at_utc"] = now_utc
    projected_aliases["aliases"] = projected_aliases_by_key

    projected_assignments = copy.deepcopy(assignments_payload)
    raw_series = projected_assignments.get("series")
    if not isinstance(raw_series, dict):
        raise ValueError("tag_assignments.series must be an object")
    series_reference_count = 0
    work_reference_count = 0
    assignment_alias_context_count = 0
    for series_id, series_row in raw_series.items():
        if not isinstance(series_row, dict):
            raise ValueError(f"tag_assignments.series['{series_id}'] must be an object")
        series_tags = _project_assignment_tags(
            series_row.get("tags"),
            f"tag_assignments.series['{series_id}'].tags",
            id_map,
        )
        if series_tags:
            series_row["tags"] = series_tags
            series_row["updated_at_utc"] = now_utc
        series_reference_count += len(series_tags)
        assignment_alias_context_count += sum(
            1 for tag in series_tags if tag.get("alias")
        )

        raw_works = series_row.get("works")
        if raw_works is None:
            continue
        if not isinstance(raw_works, dict):
            raise ValueError(
                f"tag_assignments.series['{series_id}'].works must be an object"
            )
        for work_id, work_row in raw_works.items():
            if not isinstance(work_row, dict):
                raise ValueError(
                    f"tag_assignments.series['{series_id}'].works['{work_id}'] "
                    "must be an object"
                )
            work_tags = _project_assignment_tags(
                work_row.get("tags"),
                f"tag_assignments.series['{series_id}'].works['{work_id}'].tags",
                id_map,
            )
            if work_tags:
                work_row["tags"] = work_tags
                work_row["updated_at_utc"] = now_utc
                series_row["updated_at_utc"] = now_utc
            work_reference_count += len(work_tags)
            assignment_alias_context_count += sum(
                1 for tag in work_tags if tag.get("alias")
            )

    projected_assignments["tag_assignments_version"] = (
        tag_source.TAG_ASSIGNMENTS_VERSION
    )
    projected_assignments["updated_at_utc"] = now_utc

    validate_flat_identity_sources(
        projected_registry,
        projected_aliases,
        projected_assignments,
    )
    return projected_registry, projected_aliases, projected_assignments, {
        "input_tag_count": len(raw_tags),
        "output_tag_count": len(projected_tags),
        "tag_count": len(projected_tags),
        "tag_merge_count": len(raw_tags) - len(projected_tags),
        "duplicate_flat_id_count": 0,
        "unresolved_alias_target_count": 0,
        "unresolved_assignment_reference_count": 0,
        "preserved_group_count": preserved_group_count,
        "preserved_description_count": preserved_description_count,
        "input_alias_count": len(raw_aliases),
        "output_alias_count": len(projected_aliases_by_key),
        "alias_count": len(projected_aliases_by_key),
        "input_alias_target_count": input_alias_target_count,
        "output_alias_target_count": alias_target_count,
        "alias_target_count": alias_target_count,
        "aliases_removed_redundant": aliases_removed_redundant,
        "series_reference_count": series_reference_count,
        "work_reference_count": work_reference_count,
        "assignment_reference_count": (
            series_reference_count + work_reference_count
        ),
        "assignment_weight_count_preserved": (
            series_reference_count + work_reference_count
        ),
        "assignment_alias_context_count_preserved": (
            assignment_alias_context_count
        ),
        "id_map": id_map,
    }


def validate_flat_identity_sources(
    registry_payload: Dict[str, Any],
    aliases_payload: Dict[str, Any],
    assignments_payload: Dict[str, Any],
) -> Dict[str, int]:
    versions = {
        "registry": registry_payload.get("tag_registry_version"),
        "aliases": aliases_payload.get("tag_aliases_version"),
        "assignments": assignments_payload.get("tag_assignments_version"),
    }
    expected_versions = {
        "registry": tag_source.TAG_REGISTRY_VERSION,
        "aliases": tag_source.TAG_ALIASES_VERSION,
        "assignments": tag_source.TAG_ASSIGNMENTS_VERSION,
    }
    if versions != expected_versions:
        raise ValueError(f"flat identity source versions are incomplete: {versions}")

    groups_by_tag_id = tag_source.extract_registry_tag_groups(registry_payload)
    raw_tags = registry_payload.get("tags", [])
    for idx, raw_tag in enumerate(raw_tags):
        tag_source.sanitize_tag_id(
            raw_tag.get("tag_id"),
            f"tag_registry.tags[{idx}].tag_id",
        )
        if "label" in raw_tag:
            raise ValueError(f"tag_registry.tags[{idx}] must not include label")
        if "groups" in raw_tag or isinstance(raw_tag.get("group"), list):
            raise ValueError(f"tag_registry.tags[{idx}] must have one scalar group")

    raw_aliases = aliases_payload.get("aliases")
    if not isinstance(raw_aliases, dict):
        raise ValueError("tag_aliases.aliases must be an object")
    alias_target_count = 0
    for idx, (raw_key, raw_value) in enumerate(raw_aliases.items()):
        alias_key = tag_source.sanitize_alias_key(raw_key, idx)
        alias_value = tag_source.sanitize_alias_entry(
            raw_value,
            alias_key,
            "tag_aliases.aliases",
        )
        tag_source.enforce_alias_group_constraints(
            alias_value["tags"],
            registry_payload,
            f"tag_aliases.aliases['{alias_key}'].tags",
        )
        alias_target_count += len(alias_value["tags"])

    raw_series = assignments_payload.get("series")
    if not isinstance(raw_series, dict):
        raise ValueError("tag_assignments.series must be an object")
    assignment_reference_count = 0
    for series_id, series_row in raw_series.items():
        if not isinstance(series_row, dict):
            raise ValueError(f"tag_assignments.series['{series_id}'] must be an object")
        tag_lists = [series_row.get("tags")]
        raw_works = series_row.get("works")
        if raw_works is not None:
            if not isinstance(raw_works, dict):
                raise ValueError(
                    f"tag_assignments.series['{series_id}'].works must be an object"
                )
            for work_id, work_row in raw_works.items():
                if not isinstance(work_row, dict):
                    raise ValueError(
                        f"tag_assignments.series['{series_id}'].works"
                        f"['{work_id}'] must be an object"
                    )
                tag_lists.append(work_row.get("tags"))
        for list_idx, raw_tags in enumerate(tag_lists):
            tags = tag_source.sanitize_assignment_tags(
                raw_tags,
                f"tag_assignments.series['{series_id}'].tag_lists[{list_idx}]",
                strict=True,
            )
            for tag in tags:
                if tag["tag_id"] not in groups_by_tag_id:
                    raise ValueError(
                        f"assignment target is not present in registry: {tag['tag_id']}"
                    )
            assignment_reference_count += len(tags)

    return {
        "tag_count": len(groups_by_tag_id),
        "alias_count": len(raw_aliases),
        "alias_target_count": alias_target_count,
        "assignment_reference_count": assignment_reference_count,
    }
