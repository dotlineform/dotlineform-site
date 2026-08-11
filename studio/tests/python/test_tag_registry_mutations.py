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
    group: str = "subject",
    primary_document: dict[str, str] | None = None,
) -> dict[str, Any]:
    result = {
        "tag_id": tag_id,
        "group": group,
        "updated_at_utc": "2026-05-01T00:00:00Z",
    }
    if primary_document is not None:
        result["primary_document"] = dict(primary_document)
    return result


def registry_payload(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "tag_registry_version": "tag_registry_v6",
        "updated_at_utc": "2026-05-01T00:00:00Z",
        "policy": {"allowed_groups": ["subject", "theme"]},
        "tags": rows,
    }


def assignment_tag(tag_id: str, weight: float = 0.6) -> dict[str, Any]:
    return {"tag_id": tag_id, "w_manual": weight}


def target(doc_id: str) -> dict[str, str]:
    return {
        "scope": "analysis",
        "sub_scope": "tags",
        "doc_id": doc_id,
    }


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
        row("trees"),
        row("growth", group="theme"),
    ]
    payload = registry_payload(existing_rows)
    updated, stats = registry.create_registry_tag(
        payload,
        group=" Theme ",
        tag_id="Renewal",
        now_utc=NOW,
    )

    assert_equal(payload["tags"], existing_rows, "planner preserves input rows")
    assert_equal(updated["tags"][:2], existing_rows, "create preserves unrelated rows")
    assert_equal(
        updated["tags"][2],
        {
            "tag_id": "renewal",
            "group": "theme",
            "updated_at_utc": NOW,
        },
        "created row",
    )
    assert_equal(updated["updated_at_utc"], NOW, "registry timestamp")
    assert_equal(stats["tag_id"], "renewal", "created tag id")
    assert_equal(stats["primary_document"], None, "created primary document")
    assert_equal(stats["added"], 1, "created row count")
    assert_equal(stats["final_total"], 3, "final row count")


def test_create_registry_tag_preserves_existing_primary() -> None:
    existing_primary = target("d-20260729-120000-000003")
    existing_rows = [
        row("trees", primary_document=existing_primary),
    ]
    payload = registry_payload(existing_rows)

    updated, stats = registry.create_registry_tag(
        payload,
        group="theme",
        tag_id="renewal",
        now_utc=NOW,
    )

    assert_equal(updated["tags"][0], existing_rows[0], "existing row preserved")
    assert_equal(
        "primary_document" in updated["tags"][1],
        False,
        "new tag has no primary",
    )
    assert_equal(stats["primary_document"], None, "created primary document")


def test_create_registry_tag_guards() -> None:
    payload = registry_payload([row("trees")])
    assert_raises_contains(
        lambda: registry.create_registry_tag(
            payload,
            group="domain",
            tag_id="studio",
            now_utc=NOW,
        ),
        "group must be one of",
        "invalid group",
    )
    assert_raises_contains(
        lambda: registry.create_registry_tag(
            payload,
            group="subject",
            tag_id="Bad Slug",
            now_utc=NOW,
        ),
        "tag_id must be slug-safe",
        "malformed tag id",
    )
    assert_raises_contains(
        lambda: registry.create_registry_tag(
            payload,
            group="subject",
            tag_id="trees",
            now_utc=NOW,
        ),
        "tag_id already exists",
        "duplicate tag id",
    )


def test_canonical_primary_edit_and_delete_plans() -> None:
    first_primary = target("d-20260727-225608-000001")
    second_primary = target("d-20260729-120000-000002")
    payload = registry_payload([
        row("trees", primary_document=first_primary),
        row("growth", group="theme"),
    ])
    edited, edit_meta = registry.mutate_registry_tag(
        payload,
        action="edit",
        old_tag_id="trees",
        now_utc=NOW,
        new_primary_document=second_primary,
    )
    assert_equal(edited["tags"][0]["tag_id"], "trees", "edit preserves canonical id by default")
    assert_equal(
        edited["tags"][0]["primary_document"],
        second_primary,
        "edit replaces the primary document",
    )
    assert_equal(
        edit_meta["primary_document_changed"],
        True,
        "primary document edit tracked",
    )

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
    assert_equal(
        regrouped["tags"][0]["primary_document"],
        second_primary,
        "group edit preserves primary document",
    )
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
    payload = registry_payload([
        row("trees", primary_document=target("d-20260729-120000-000002")),
        row("canopy"),
    ])
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
    assert_raises_contains(
        lambda: registry.mutate_registry_tag(
            payload,
            "edit",
            "trees",
            NOW,
            new_primary_document=None,
        ),
        "exact document target object",
        "primary cannot be cleared",
    )
    assert_raises_contains(
        lambda: registry.mutate_registry_tag(
            payload,
            "edit",
            "trees",
            NOW,
            new_primary_document={
                "scope": "studio",
                "sub_scope": "tags",
                "doc_id": "d-20260729-120000-000002",
            },
        ),
        "Analysis Tags collection",
        "wrong primary collection",
    )


def test_omitted_primary_preserves_unrelated_rows_and_stale_primary() -> None:
    stale = target("d-20260729-120000-000001")
    unrelated = row(
        "growth",
        group="theme",
        primary_document=target("d-20260729-120000-000003"),
    )
    payload = registry_payload([
        row("trees", primary_document=stale),
        unrelated,
    ])

    updated, stats = registry.mutate_registry_tag(
        payload,
        "edit",
        "trees",
        NOW,
        new_group="theme",
    )

    assert_equal(
        updated["tags"][0]["primary_document"],
        stale,
        "omitted primary preserves stored identity",
    )
    assert_equal(updated["tags"][1], unrelated, "unrelated row remains unchanged")
    assert_equal(stats["primary_document_changed"], False, "primary unchanged")


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
    test_create_registry_tag_preserves_existing_primary()
    test_create_registry_tag_guards()
    test_canonical_primary_edit_and_delete_plans()
    test_canonical_mutation_guards()
    test_omitted_primary_preserves_unrelated_rows_and_stale_primary()
    test_rewrite_assignments_for_canonical_rename()
    test_rewrite_assignments_for_canonical_delete_removes_empty_work_rows()
    print("Tag registry mutation tests OK")


if __name__ == "__main__":
    main()
