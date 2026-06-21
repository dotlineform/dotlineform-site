#!/usr/bin/env python3
"""Bundle family behavior for Analytics tags Data Sharing."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping

from data_sharing_adapters import AdapterResolution

from ..context import normalize_text, package_metadata, source_files
from . import aliases, assignments, registry


def merge_counts(*items: Mapping[str, int]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for item in items:
        for key, value in item.items():
            out[key] = out.get(key, 0) + int(value or 0)
    return out


def merge_groups(*items: Mapping[str, list[str]]) -> Dict[str, list[str]]:
    merged: Dict[str, set[str]] = {}
    for groups in items:
        for key, values in groups.items():
            merged.setdefault(key, set()).update(normalize_text(value) for value in values if normalize_text(value))
    return {key: sorted(values) for key, values in merged.items() if values}


def build_package(repo_root: Path, adapter: AdapterResolution, config_id: str, generated_at_utc: str) -> tuple[Dict[str, Any], Dict[str, int], Dict[str, list[str]]]:
    registry_payload, registry_counts, registry_groups = registry.build_package(repo_root, adapter, config_id, generated_at_utc)
    aliases_payload, aliases_counts, aliases_groups = aliases.build_package(repo_root, adapter, config_id, generated_at_utc)
    assignments_payload, assignments_counts, assignments_groups = assignments.build_package(repo_root, adapter, config_id, generated_at_utc)
    counts = merge_counts(registry_counts, aliases_counts, assignments_counts)
    payload = {
        "package_metadata": package_metadata(
            adapter=adapter,
            config_id=config_id,
            family="bundle",
            generated_at_utc=generated_at_utc,
            source_paths=source_files(repo_root, adapter, "bundle"),
            counts=counts,
        ),
        "families": {
            "registry": {key: value for key, value in registry_payload.items() if key != "package_metadata"},
            "aliases": {key: value for key, value in aliases_payload.items() if key != "package_metadata"},
            "assignments": {key: value for key, value in assignments_payload.items() if key != "package_metadata"},
        },
    }
    return payload, counts, merge_groups(registry_groups, aliases_groups, assignments_groups)
