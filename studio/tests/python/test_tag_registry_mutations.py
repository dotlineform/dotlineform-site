#!/usr/bin/env python3
"""Verify tag registry import and canonical tag mutation planners."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from analytics import tag_registry_mutations as registry  # noqa: E402


NOW = "2026-05-09T12:00:00Z"


def row(tag_id: str, description: str = "", status: str = "active") -> dict[str, str]:
    group, slug = tag_id.split(":", 1)
    return {
        "tag_id": tag_id,
        "group": group,
        "label": slug,
        "status": status,
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


def test_registry_import_modes() -> None:
    existing = {
        "policy": {"allowed_groups": ["subject", "theme", "domain"]},
        "tags": [row("subject:trees", "old"), row("theme:growth", "keep")],
    }
    incoming = {"tags": [row("subject:trees", "new"), row("domain:studio", "added")]}

    replaced, replace_stats = registry.apply_registry_import(
        {"policy": existing["policy"], "tags": list(existing["tags"])},
        incoming,
        "replace",
        NOW,
    )
    assert_equal([item["tag_id"] for item in replaced["tags"]], ["subject:trees", "domain:studio"], "replace tag order")
    assert_equal(replace_stats["removed"], 1, "replace removed count")
    assert_equal(replace_stats["overwritten"], 1, "replace overwritten count")

    merged, merge_stats = registry.apply_registry_import(
        {"policy": existing["policy"], "tags": list(existing["tags"])},
        incoming,
        "merge",
        NOW,
    )
    assert_equal([item["tag_id"] for item in merged["tags"]], ["subject:trees", "theme:growth", "domain:studio"], "merge tag order")
    assert_equal(merged["tags"][0]["description"], "new", "merge overwrites existing row")
    assert_equal(merge_stats["unchanged"], 1, "merge unchanged count")

    added, add_stats = registry.apply_registry_import(
        {"policy": existing["policy"], "tags": list(existing["tags"])},
        incoming,
        "add",
        NOW,
    )
    assert_equal(added["tags"][0]["description"], "old", "add preserves existing row")
    assert_equal([item["tag_id"] for item in added["tags"]], ["subject:trees", "theme:growth", "domain:studio"], "add tag order")
    assert_equal(add_stats["unchanged"], 1, "add unchanged count")


def test_registry_import_duplicate_handling() -> None:
    payload = {"policy": {"allowed_groups": ["subject"]}, "tags": []}
    imported, stats = registry.apply_registry_import(
        payload,
        {"tags": [row("subject:trees", "first"), row("subject:trees", "second")]},
        "add",
        NOW,
    )

    assert_equal(len(imported["tags"]), 1, "duplicate import compacts to one row")
    assert_equal(imported["tags"][0]["description"], "second", "last duplicate wins")
    assert_equal(stats["imported_total"], 1, "stats count normalized imports")


def test_canonical_edit_and_delete_plans() -> None:
    payload = {"tags": [row("subject:trees", "old"), row("theme:growth", "keep")]}
    edited, edit_meta = registry.mutate_registry_tag(
        payload,
        action="edit",
        old_tag_id="subject:trees",
        now_utc=NOW,
        new_description="new",
    )
    assert_equal(edited["tags"][0]["description"], "new", "edit updates description")
    assert_equal(edited["tags"][0]["tag_id"], "subject:trees", "edit preserves canonical id by default")
    assert_equal(edit_meta["description_changed"], True, "edit meta tracks description change")

    renamed, rename_meta = registry.mutate_registry_tag(
        edited,
        action="edit",
        old_tag_id="subject:trees",
        now_utc=NOW,
        new_slug="canopy",
        allow_canonical_rename=True,
    )
    assert_equal(renamed["tags"][0]["tag_id"], "subject:canopy", "rename updates canonical id")
    assert_equal(rename_meta["canonical_changed"], True, "rename meta tracks canonical change")

    deleted, delete_meta = registry.mutate_registry_tag(
        renamed,
        action="delete",
        old_tag_id="subject:canopy",
        now_utc=NOW,
    )
    assert_equal([item["tag_id"] for item in deleted["tags"]], ["theme:growth"], "delete removes target tag")
    assert_equal(delete_meta["new_tag_id"], None, "delete meta has no new tag id")


def test_canonical_mutation_guards() -> None:
    payload = {"tags": [row("subject:trees"), row("subject:canopy")]}
    assert_raises_contains(
        lambda: registry.mutate_registry_tag(payload, "edit", "subject:trees", NOW, new_slug="forest"),
        "canonical rename is disabled",
        "rename disabled",
    )
    assert_raises_contains(
        lambda: registry.mutate_registry_tag(payload, "edit", "subject:trees", NOW, new_slug="canopy", allow_canonical_rename=True),
        "target tag_id already exists",
        "duplicate rename target",
    )
    assert_raises_contains(
        lambda: registry.mutate_registry_tag(payload, "delete", "subject:missing", NOW),
        "tag not found",
        "missing canonical tag",
    )


def test_registry_summary_text() -> None:
    text = registry.build_import_summary_text(
        {"mode": "merge", "imported_total": 2, "added": 1, "overwritten": 1, "unchanged": 3, "removed": 0, "final_total": 5}
    )
    assert_equal(
        text,
        "mode merge; Imported 2 tags; added 1; overwritten 1; unchanged 3; removed 0; final 5",
        "import summary text",
    )


def test_rewrite_assignments_for_canonical_rename() -> None:
    payload = {
        "series": {
            "009": {
                "tags": [assignment_tag("subject:trees"), assignment_tag("theme:growth")],
                "works": {
                    "00001": {"tags": [assignment_tag("subject:trees", 0.9)]},
                    "00002": {"tags": [assignment_tag("theme:growth")]},
                },
            }
        }
    }

    updated, stats = registry.rewrite_assignments_for_tag(payload, "subject:trees", "subject:canopy", NOW)

    assert_equal(updated["series"]["009"]["tags"][0], assignment_tag("subject:canopy"), "series tag rewritten")
    assert_equal(updated["series"]["009"]["works"]["00001"]["tags"][0], assignment_tag("subject:canopy", 0.9), "work tag rewritten")
    assert_equal(updated["series"]["009"]["works"]["00002"]["tags"][0], assignment_tag("theme:growth"), "untouched work preserved")
    assert_equal(updated["updated_at_utc"], NOW, "root timestamp updated")
    assert_equal(stats["series_rows_touched"], 1, "series rows touched")
    assert_equal(stats["series_tag_refs_rewritten"], 1, "series refs rewritten")
    assert_equal(stats["work_rows_touched"], 1, "work rows touched")
    assert_equal(stats["work_tag_refs_rewritten"], 1, "work refs rewritten")


def test_rewrite_assignments_for_canonical_delete_removes_empty_work_rows() -> None:
    payload = {
        "series": {
            "009": {
                "tags": [assignment_tag("subject:trees"), assignment_tag("theme:growth")],
                "works": {
                    "00001": {"tags": [assignment_tag("subject:trees")]},
                    "00002": {"tags": [assignment_tag("subject:trees"), assignment_tag("theme:growth")]},
                },
            }
        }
    }

    updated, stats = registry.rewrite_assignments_for_tag(payload, "subject:trees", None, NOW)

    assert_equal(updated["series"]["009"]["tags"], [assignment_tag("theme:growth")], "series tag removed")
    if "00001" in updated["series"]["009"].get("works", {}):
        raise AssertionError("empty work row should be removed")
    assert_equal(updated["series"]["009"]["works"]["00002"]["tags"], [assignment_tag("theme:growth")], "non-empty work row preserved")
    assert_equal(stats["series_tag_refs_rewritten"], 1, "series delete refs rewritten")
    assert_equal(stats["work_tag_refs_rewritten"], 2, "work delete refs rewritten")


def main() -> None:
    test_registry_import_modes()
    test_registry_import_duplicate_handling()
    test_canonical_edit_and_delete_plans()
    test_canonical_mutation_guards()
    test_registry_summary_text()
    test_rewrite_assignments_for_canonical_rename()
    test_rewrite_assignments_for_canonical_delete_removes_empty_work_rows()
    print("Tag registry mutation tests OK")


if __name__ == "__main__":
    main()
