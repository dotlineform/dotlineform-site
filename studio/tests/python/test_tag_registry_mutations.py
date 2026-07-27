#!/usr/bin/env python3
"""Verify focused tag registry creation and canonical mutation planners."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[3]
STUDIO_SERVICES_DIR = REPO_ROOT / "studio" / "services"
for path in (STUDIO_SERVICES_DIR,):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from tags import tag_registry_mutations as registry  # noqa: E402


NOW = "2026-05-09T12:00:00Z"


def row(
    tag_id: str,
    description: str = "",
    group: str = "subject",
) -> dict[str, str]:
    return {
        "tag_id": tag_id,
        "group": group,
        "label": tag_id,
        "description": description,
    }


def assignment_tag(tag_id: str, weight: float = 0.6) -> dict[str, Any]:
    return {"tag_id": tag_id, "w_manual": weight}


def assert_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def assert_raises_contains(fn: Callable[[], Any], expected: str, label: str) -> None:
    try:
        fn()
    except ValueError as exc:
        if expected not in str(exc):
            raise AssertionError(f"{label}: expected error containing {expected!r}, got {str(exc)!r}") from exc
        return
    raise AssertionError(f"{label}: expected ValueError")


def test_create_registry_tag_adds_one_normalized_row() -> None:
    existing_rows = [
        row("trees", "Trees"),
        row("growth", "Growth", group="theme"),
    ]
    payload = {
        "tag_registry_version": "tag_registry_v2",
        "updated_at_utc": "2026-05-01T00:00:00Z",
        "policy": {"allowed_groups": ["subject", "theme"]},
        "tags": existing_rows,
    }

    updated, stats = registry.create_registry_tag(
        payload,
        group=" Theme ",
        tag_id="Renewal",
        description="  Renewal cycle  ",
        now_utc=NOW,
    )

    assert_equal(payload["tags"], existing_rows, "planner preserves input rows")
    assert_equal(updated["tags"][:2], existing_rows, "create preserves unrelated rows")
    assert_equal(
        updated["tags"][2],
        {
            "tag_id": "renewal",
            "group": "theme",
            "label": "renewal",
            "description": "Renewal cycle",
            "updated_at_utc": NOW,
        },
        "created row",
    )
    assert_equal(updated["updated_at_utc"], NOW, "registry timestamp")
    assert_equal(stats["tag_id"], "renewal", "created tag id")
    assert_equal(stats["added"], 1, "created row count")
    assert_equal(stats["final_total"], 3, "final row count")


def test_create_registry_tag_guards() -> None:
    payload = {
        "policy": {"allowed_groups": ["subject", "theme"]},
        "tags": [row("trees")],
    }
    assert_raises_contains(
        lambda: registry.create_registry_tag(payload, group="domain", tag_id="studio", description="", now_utc=NOW),
        "group must be one of",
        "invalid group",
    )
    assert_raises_contains(
        lambda: registry.create_registry_tag(payload, group="subject", tag_id="Bad Slug", description="", now_utc=NOW),
        "tag_id must be slug-safe",
        "malformed tag id",
    )
    assert_raises_contains(
        lambda: registry.create_registry_tag(payload, group="subject", tag_id="trees", description="", now_utc=NOW),
        "tag_id already exists",
        "duplicate tag id",
    )
    assert_raises_contains(
        lambda: registry.create_registry_tag(payload, group="subject", tag_id="canopy", description={"bad": True}, now_utc=NOW),
        "description must be a string",
        "malformed description",
    )


def test_canonical_edit_and_delete_plans() -> None:
    payload = {
        "policy": {"allowed_groups": ["subject", "theme"]},
        "tags": [row("trees", "old"), row("growth", "keep", group="theme")],
    }
    edited, edit_meta = registry.mutate_registry_tag(
        payload,
        action="edit",
        old_tag_id="trees",
        now_utc=NOW,
        new_description="new",
    )
    assert_equal(edited["tags"][0]["description"], "new", "edit updates description")
    assert_equal(edited["tags"][0]["tag_id"], "trees", "edit preserves canonical id by default")
    assert_equal(edit_meta["description_changed"], True, "edit meta tracks description change")

    renamed, rename_meta = registry.mutate_registry_tag(
        edited,
        action="edit",
        old_tag_id="trees",
        now_utc=NOW,
        new_tag_id="canopy",
        allow_canonical_rename=True,
    )
    assert_equal(renamed["tags"][0]["tag_id"], "canopy", "rename updates canonical id")
    assert_equal(rename_meta["canonical_changed"], True, "rename meta tracks canonical change")

    regrouped, regroup_meta = registry.mutate_registry_tag(
        renamed,
        action="edit",
        old_tag_id="canopy",
        now_utc=NOW,
        new_group="theme",
    )
    assert_equal(regrouped["tags"][0]["group"], "theme", "group edit is independent")
    assert_equal(regroup_meta["group_changed"], True, "group edit tracked")

    deleted, delete_meta = registry.mutate_registry_tag(
        regrouped,
        action="delete",
        old_tag_id="canopy",
        now_utc=NOW,
    )
    assert_equal([item["tag_id"] for item in deleted["tags"]], ["growth"], "delete removes target tag")
    assert_equal(delete_meta["new_tag_id"], None, "delete meta has no new tag id")


def test_canonical_mutation_guards() -> None:
    payload = {
        "policy": {"allowed_groups": ["subject", "theme"]},
        "tags": [row("trees"), row("canopy")],
    }
    assert_raises_contains(
        lambda: registry.mutate_registry_tag(payload, "edit", "trees", NOW, new_tag_id="forest"),
        "canonical rename is disabled",
        "rename disabled",
    )
    assert_raises_contains(
        lambda: registry.mutate_registry_tag(payload, "edit", "trees", NOW, new_tag_id="canopy", allow_canonical_rename=True),
        "target tag_id already exists",
        "duplicate rename target",
    )
    assert_raises_contains(
        lambda: registry.mutate_registry_tag(payload, "delete", "missing", NOW),
        "tag not found",
        "missing canonical tag",
    )


def test_rewrite_assignments_for_canonical_rename() -> None:
    payload = {
        "series": {
            "009": {
                "tags": [assignment_tag("trees"), assignment_tag("growth")],
                "works": {
                    "00001": {"tags": [assignment_tag("trees", 0.9)]},
                    "00002": {"tags": [assignment_tag("growth")]},
                },
            }
        }
    }

    updated, stats = registry.rewrite_assignments_for_tag(payload, "trees", "canopy", NOW)

    assert_equal(updated["series"]["009"]["tags"][0], assignment_tag("canopy"), "series tag rewritten")
    assert_equal(updated["series"]["009"]["works"]["00001"]["tags"][0], assignment_tag("canopy", 0.9), "work tag rewritten")
    assert_equal(updated["series"]["009"]["works"]["00002"]["tags"][0], assignment_tag("growth"), "untouched work preserved")
    assert_equal(updated["updated_at_utc"], NOW, "root timestamp updated")
    assert_equal(stats["series_rows_touched"], 1, "series rows touched")
    assert_equal(stats["series_tag_refs_rewritten"], 1, "series refs rewritten")
    assert_equal(stats["work_rows_touched"], 1, "work rows touched")
    assert_equal(stats["work_tag_refs_rewritten"], 1, "work refs rewritten")


def test_rewrite_assignments_for_canonical_delete_removes_empty_work_rows() -> None:
    payload = {
        "series": {
            "009": {
                "tags": [assignment_tag("trees"), assignment_tag("growth")],
                "works": {
                    "00001": {"tags": [assignment_tag("trees")]},
                    "00002": {"tags": [assignment_tag("trees"), assignment_tag("growth")]},
                },
            }
        }
    }

    updated, stats = registry.rewrite_assignments_for_tag(payload, "trees", None, NOW)

    assert_equal(updated["series"]["009"]["tags"], [assignment_tag("growth")], "series tag removed")
    if "00001" in updated["series"]["009"].get("works", {}):
        raise AssertionError("empty work row should be removed")
    assert_equal(updated["series"]["009"]["works"]["00002"]["tags"], [assignment_tag("growth")], "non-empty work row preserved")
    assert_equal(stats["series_tag_refs_rewritten"], 1, "series delete refs rewritten")
    assert_equal(stats["work_tag_refs_rewritten"], 2, "work delete refs rewritten")


def main() -> None:
    test_create_registry_tag_adds_one_normalized_row()
    test_create_registry_tag_guards()
    test_canonical_edit_and_delete_plans()
    test_canonical_mutation_guards()
    test_rewrite_assignments_for_canonical_rename()
    test_rewrite_assignments_for_canonical_delete_removes_empty_work_rows()
    print("Tag registry mutation tests OK")


if __name__ == "__main__":
    main()
