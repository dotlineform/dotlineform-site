#!/usr/bin/env python3
"""Verify flat tag identity projection and reconciliation."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[3]
STUDIO_SERVICES_DIR = REPO_ROOT / "studio" / "services"
if str(STUDIO_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(STUDIO_SERVICES_DIR))

from tags import tag_flat_identity_migration as migration  # noqa: E402


NOW = "2026-07-27T16:30:00Z"


def assert_raises_contains(fn: Callable[[], Any], expected: str) -> None:
    try:
        fn()
    except ValueError as exc:
        if expected not in str(exc):
            raise AssertionError(
                f"expected error containing {expected!r}, got {str(exc)!r}"
            ) from exc
        return
    raise AssertionError("expected ValueError")


def legacy_sources() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    registry = {
        "tag_registry_version": "tag_registry_v1",
        "updated_at_utc": "old",
        "policy": {"allowed_groups": ["subject", "theme"]},
        "tags": [
            {
                "tag_id": "subject:trees",
                "group": "subject",
                "label": "trees",
                "description": "Trees",
                "updated_at_utc": "old",
            },
            {
                "tag_id": "theme:growth",
                "group": "theme",
                "label": "growth",
                "description": "Growth",
                "updated_at_utc": "old",
            },
        ],
    }
    aliases = {
        "tag_aliases_version": "tag_aliases_v1",
        "updated_at_utc": "old",
        "aliases": {
            "foliage": {
                "description": "Leaf forms",
                "tags": ["subject:trees", "theme:growth"],
            }
        },
    }
    assignments = {
        "tag_assignments_version": "tag_assignments_v1",
        "updated_at_utc": "old",
        "series": {
            "009": {
                "tags": [
                    {
                        "tag_id": "subject:trees",
                        "w_manual": 0.9,
                        "alias": "foliage",
                    }
                ],
                "works": {
                    "00001": {
                        "tags": [{"tag_id": "theme:growth", "w_manual": 0.3}]
                    }
                },
            }
        },
    }
    return registry, aliases, assignments


def test_project_flat_identity_sources_preserves_group_and_assignments() -> None:
    registry, aliases, assignments = legacy_sources()
    projected_registry, projected_aliases, projected_assignments, stats = (
        migration.project_flat_identity_sources(
            registry,
            aliases,
            assignments,
            now_utc=NOW,
        )
    )

    assert projected_registry["tag_registry_version"] == "tag_registry_v4"
    assert [row["tag_id"] for row in projected_registry["tags"]] == [
        "trees",
        "growth",
    ]
    assert [row["group"] for row in projected_registry["tags"]] == [
        "subject",
        "theme",
    ]
    assert all("label" not in row for row in projected_registry["tags"])
    assert projected_aliases["tag_aliases_version"] == "tag_aliases_v2"
    assert projected_aliases["aliases"]["foliage"]["tags"] == ["trees", "growth"]
    assert projected_assignments["tag_assignments_version"] == "tag_assignments_v2"
    assert projected_assignments["series"]["009"]["tags"] == [
        {"tag_id": "trees", "w_manual": 0.9, "alias": "foliage"}
    ]
    assert projected_assignments["series"]["009"]["works"]["00001"]["tags"] == [
        {"tag_id": "growth", "w_manual": 0.3}
    ]
    assert stats["id_map"] == {
        "subject:trees": "trees",
        "theme:growth": "growth",
    }
    assert stats["input_tag_count"] == stats["output_tag_count"] == 2
    assert stats["tag_merge_count"] == 0
    assert stats["input_alias_target_count"] == stats["output_alias_target_count"] == 2
    assert stats["assignment_weight_count_preserved"] == 2
    assert stats["assignment_alias_context_count_preserved"] == 1
    assert stats["unresolved_alias_target_count"] == 0
    assert stats["unresolved_assignment_reference_count"] == 0
    assert migration.validate_flat_identity_sources(
        projected_registry,
        projected_aliases,
        projected_assignments,
    ) == {
        "tag_count": 2,
        "alias_count": 1,
        "alias_target_count": 2,
        "assignment_reference_count": 2,
    }


def test_project_flat_identity_sources_rejects_flat_collision() -> None:
    registry, aliases, assignments = legacy_sources()
    registry["tags"].append(
        {
            "tag_id": "theme:trees",
            "group": "theme",
            "label": "trees",
            "description": "Theme trees",
        }
    )

    assert_raises_contains(
        lambda: migration.project_flat_identity_sources(
            registry,
            aliases,
            assignments,
            now_utc=NOW,
        ),
        "duplicate flat tag_id",
    )
