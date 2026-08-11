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
    doc_url: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "tag_id": tag_id,
        "group": group,
        "doc_url": list(doc_url or []),
        "updated_at_utc": "2026-05-01T00:00:00Z",
    }


def registry_payload(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "tag_registry_version": "tag_registry_v5",
        "updated_at_utc": "2026-05-01T00:00:00Z",
        "policy": {"allowed_groups": ["subject", "theme"]},
        "tags": rows,
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
        row("trees"),
        row("growth", group="theme"),
    ]
    payload = registry_payload(existing_rows)
    document_url = (
        "/analysis/?doc=d-20260624-213316-478639"
        "&subdoc=d-20260729-120000-000003"
    )

    updated, stats = registry.create_registry_tag(
        payload,
        group=" Theme ",
        tag_id="Renewal",
        doc_url=[document_url],
        now_utc=NOW,
    )

    assert_equal(payload["tags"], existing_rows, "planner preserves input rows")
    assert_equal(updated["tags"][:2], existing_rows, "create preserves unrelated rows")
    assert_equal(
        updated["tags"][2],
        {
            "tag_id": "renewal",
            "group": "theme",
            "doc_url": [document_url],
            "updated_at_utc": NOW,
        },
        "created row",
    )
    assert_equal(updated["updated_at_utc"], NOW, "registry timestamp")
    assert_equal(stats["tag_id"], "renewal", "created tag id")
    assert_equal(stats["doc_url"], [document_url], "created document URL")
    assert_equal(stats["added"], 1, "created row count")
    assert_equal(stats["final_total"], 3, "final row count")


def test_create_registry_tag_preserves_shared_existing_document_link() -> None:
    shared_doc_url = (
        "/analysis/?doc=d-20260624-213316-478639"
        "&subdoc=d-20260729-120000-000003"
    )
    existing_rows = [
        row("trees", doc_url=[shared_doc_url]),
    ]
    payload = registry_payload(existing_rows)

    updated, stats = registry.create_registry_tag(
        payload,
        group="theme",
        tag_id="renewal",
        doc_url=[shared_doc_url],
        now_utc=NOW,
    )

    assert_equal(updated["tags"][0], existing_rows[0], "existing row preserved")
    assert_equal(updated["tags"][1]["doc_url"], [shared_doc_url], "shared link accepted")
    assert_equal(stats["doc_url"], [shared_doc_url], "created document URL")


def test_create_registry_tag_guards() -> None:
    payload = registry_payload([row("trees")])
    document_url = "/analysis/?doc=d-20260729-120000-000001"
    assert_raises_contains(
        lambda: registry.create_registry_tag(
            payload,
            group="domain",
            tag_id="studio",
            doc_url=[document_url],
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
            doc_url=[document_url],
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
            doc_url=[document_url],
            now_utc=NOW,
        ),
        "tag_id already exists",
        "duplicate tag id",
    )
    assert_raises_contains(
        lambda: registry.create_registry_tag(
            payload,
            group="subject",
            tag_id="canopy",
            doc_url="not-an-array",
            now_utc=NOW,
        ),
        "doc_url must be an array",
        "malformed document URL array",
    )
    assert_raises_contains(
        lambda: registry.create_registry_tag(
            payload,
            group="subject",
            tag_id="canopy",
            doc_url=["https://example.test/docs/"],
            now_utc=NOW,
        ),
        "supported canonical Docs Viewer URL",
        "unsupported document URL",
    )


def test_canonical_edit_and_delete_plans() -> None:
    document_url = (
        "/analysis/?doc=d-20260624-213316-478639"
        "&subdoc=d-20260727-225608-000001"
    )
    second_document_url = "/analysis/?doc=d-20260729-120000-000002"
    payload = registry_payload([
        row("trees", doc_url=[document_url]),
        row("growth", group="theme"),
    ])
    edited, edit_meta = registry.mutate_registry_tag(
        payload,
        action="edit",
        old_tag_id="trees",
        now_utc=NOW,
        new_doc_url=[document_url, second_document_url],
    )
    assert_equal(edited["tags"][0]["tag_id"], "trees", "edit preserves canonical id by default")
    assert_equal(
        edited["tags"][0]["doc_url"],
        [document_url, second_document_url],
        "edit stores the complete ordered URL draft",
    )
    assert_equal(edit_meta["doc_url_changed"], True, "document URL edit tracked")
    assert_equal(edit_meta["document_urls_added"], 1, "document URL addition tracked")
    assert_equal(edit_meta["document_urls_removed"], 0, "document URL removal tracked")

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
        regrouped["tags"][0]["doc_url"],
        [document_url, second_document_url],
        "group edit preserves linked document URLs",
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
    document_url = "/analysis/?doc=d-20260729-120000-000002"
    payload = registry_payload([
        row("trees", doc_url=[document_url]),
        row("canopy", doc_url=[document_url]),
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
            new_doc_url=[document_url, document_url],
        ),
        "duplicates URL",
        "duplicate document URL",
    )
    assert_raises_contains(
        lambda: registry.mutate_registry_tag(
            payload,
            "edit",
            "trees",
            NOW,
            new_doc_url=["https://example.test/document"],
        ),
        "supported canonical Docs Viewer URL",
        "external document URL",
    )


def test_canonical_document_edit_preserves_unrelated_rows_and_accepts_unlinked() -> None:
    first = "/analysis/?doc=d-20260729-120000-000001"
    second = "/analysis/?doc=d-20260729-120000-000002"
    shared = "/analysis/?doc=d-20260729-120000-000003"
    unrelated = row("growth", group="theme", doc_url=[shared])
    payload = registry_payload([
        row("trees", doc_url=[first, second]),
        unrelated,
    ])

    updated, stats = registry.mutate_registry_tag(
        payload,
        "edit",
        "trees",
        NOW,
        new_doc_url=[],
    )

    assert_equal(updated["tags"][0]["doc_url"], [], "complete draft removes both URLs")
    assert_equal(updated["tags"][1], unrelated, "unrelated row remains unchanged")
    assert_equal(stats["document_urls_removed"], 2, "removed URL count")
    assert_equal(stats["document_urls_added"], 0, "added URL count")


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
    test_create_registry_tag_preserves_shared_existing_document_link()
    test_create_registry_tag_guards()
    test_canonical_edit_and_delete_plans()
    test_canonical_mutation_guards()
    test_rewrite_assignments_for_canonical_rename()
    test_rewrite_assignments_for_canonical_delete_removes_empty_work_rows()
    print("Tag registry mutation tests OK")


if __name__ == "__main__":
    main()
