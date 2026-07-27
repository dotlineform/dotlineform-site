#!/usr/bin/env python3
"""Verify the canonical tag registry label-retirement projection."""

from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[3]
STUDIO_SERVICES_DIR = REPO_ROOT / "studio" / "services"
if str(STUDIO_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(STUDIO_SERVICES_DIR))

from tags import tag_registry_label_retirement as retirement  # noqa: E402


NOW = "2026-07-27T17:30:00Z"


def assert_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def assert_raises_contains(
    fn: Callable[[], Any],
    expected: str,
    label: str,
) -> None:
    try:
        fn()
    except ValueError as exc:
        if expected not in str(exc):
            raise AssertionError(
                f"{label}: expected error containing {expected!r}, got {str(exc)!r}"
            ) from exc
        return
    raise AssertionError(f"{label}: expected ValueError")


def registry_payload() -> dict[str, Any]:
    return {
        "tag_registry_version": "tag_registry_v2",
        "updated_at_utc": "2026-07-27T16:00:00Z",
        "policy": {"allowed_groups": ["subject", "theme"]},
        "tags": [
            {
                "tag_id": "trees",
                "group": "subject",
                "label": "trees",
                "description": "Tree forms",
                "updated_at_utc": "2026-07-27T15:00:00Z",
            },
            {
                "tag_id": "growth",
                "group": "theme",
                "label": "growth",
                "description": "",
                "updated_at_utc": "2026-07-27T15:01:00Z",
            },
        ],
    }


def aliases_payload() -> dict[str, Any]:
    return {
        "tag_aliases_version": "tag_aliases_v2",
        "aliases": {
            "foliage": {"description": "", "tags": ["trees", "growth"]}
        },
    }


def assignments_payload() -> dict[str, Any]:
    return {
        "tag_assignments_version": "tag_assignments_v2",
        "series": {
            "001": {
                "tags": [
                    {"tag_id": "trees", "w_manual": 0.9},
                    {"tag_id": "growth", "w_manual": 0.3},
                ]
            }
        },
    }


def test_projection_removes_only_labels_and_updates_source_metadata() -> None:
    registry = registry_payload()
    original = copy.deepcopy(registry)
    aliases = aliases_payload()
    assignments = assignments_payload()

    projected, stats = retirement.project_registry_label_retirement(
        registry,
        aliases,
        assignments,
        now_utc=NOW,
    )

    assert_equal(registry, original, "input registry unchanged")
    assert_equal(projected["tag_registry_version"], "tag_registry_v3", "version")
    assert_equal(projected["updated_at_utc"], NOW, "source timestamp")
    assert_equal(
        projected["tags"],
        [
            {
                "tag_id": "trees",
                "group": "subject",
                "description": "Tree forms",
                "updated_at_utc": "2026-07-27T15:00:00Z",
            },
            {
                "tag_id": "growth",
                "group": "theme",
                "description": "",
                "updated_at_utc": "2026-07-27T15:01:00Z",
            },
        ],
        "projected rows",
    )
    assert_equal(stats["labels_removed"], 2, "labels removed")
    assert_equal(stats["tag_count"], 2, "valid tag count")
    assert_equal(stats["alias_target_count"], 2, "alias targets")
    assert_equal(stats["assignment_reference_count"], 2, "assignment references")


def test_projection_rejects_non_redundant_or_missing_labels() -> None:
    mismatched = registry_payload()
    mismatched["tags"][0]["label"] = "forest"
    assert_raises_contains(
        lambda: retirement.project_registry_label_retirement(
            mismatched,
            aliases_payload(),
            assignments_payload(),
            now_utc=NOW,
        ),
        "must match tag_id",
        "mismatched label",
    )

    missing = registry_payload()
    missing["tags"][0].pop("label")
    assert_raises_contains(
        lambda: retirement.project_registry_label_retirement(
            missing,
            aliases_payload(),
            assignments_payload(),
            now_utc=NOW,
        ),
        "must match tag_id",
        "missing label",
    )


def test_current_validation_rejects_labels() -> None:
    projected, _ = retirement.project_registry_label_retirement(
        registry_payload(),
        aliases_payload(),
        assignments_payload(),
        now_utc=NOW,
    )
    retirement.validate_registry_label_retirement(
        projected,
        aliases_payload(),
        assignments_payload(),
    )
    projected["tags"][0]["label"] = "trees"
    assert_raises_contains(
        lambda: retirement.validate_registry_label_retirement(
            projected,
            aliases_payload(),
            assignments_payload(),
        ),
        "must not include label",
        "retired label rejected",
    )
