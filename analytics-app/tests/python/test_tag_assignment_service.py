#!/usr/bin/env python3
"""Verify tag assignment save and import planners."""

from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = REPO_ROOT / "scripts"
ANALYTICS_PACKAGE_DIR = REPO_ROOT / "analytics-app" / "app" / "server" / "analytics_app"
for path in (SCRIPTS_DIR, ANALYTICS_PACKAGE_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from tag_services import tag_assignment_service as assignments  # noqa: E402


NOW = "2026-05-09T12:00:00Z"


def tag(tag_id: str, weight: float = 0.6) -> dict[str, Any]:
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


def import_session(rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "version": "tag_assignments_export_v1",
        "series": rows,
    }


def test_series_assignment_save_plan() -> None:
    payload: dict[str, Any] = {"series": {}}
    updated, response, would_write = assignments.plan_assignment_save(
        payload,
        "series-a",
        None,
        None,
        [tag("subject:trees", 0.9)],
        NOW,
    )

    assert_equal(updated["series"]["series-a"]["tags"], [tag("subject:trees", 0.9)], "series tags persisted")
    assert_equal(updated["series"]["series-a"]["updated_at_utc"], NOW, "series updated timestamp")
    assert_equal(response["tag_count"], 1, "series response tag count")
    assert_equal(response["work_id"], None, "series response work id")
    assert_equal("deleted" in response, False, "series response omits deleted")
    assert_equal(would_write["tags"], [tag("subject:trees", 0.9)], "series dry-run write payload")


def test_work_assignment_save_strips_inherited_tags() -> None:
    payload = {
        "series": {
            "series-a": {
                "tags": [tag("subject:trees")],
            }
        }
    }
    updated, response, would_write = assignments.plan_assignment_save(
        payload,
        "series-a",
        "00001",
        False,
        [tag("subject:trees"), tag("theme:growth", 0.3)],
        NOW,
    )

    assert_equal(updated["series"]["series-a"]["works"]["00001"]["tags"], [tag("theme:growth", 0.3)], "work override strips inherited")
    assert_equal(response["tag_count"], 1, "work response counts persisted override tags")
    assert_equal(response["deleted"], False, "work row retained")
    assert_equal(would_write["deleted"], False, "work dry-run delete flag")


def test_work_assignment_delete_plan() -> None:
    payload = {
        "series": {
            "series-a": {
                "tags": [tag("subject:trees")],
                "works": {"00001": {"tags": [tag("theme:growth")], "updated_at_utc": "old"}},
            }
        }
    }
    updated, response, would_write = assignments.plan_assignment_save(
        payload,
        "series-a",
        "00001",
        False,
        [tag("subject:trees")],
        NOW,
    )

    assert_equal("works" in updated["series"]["series-a"], False, "empty work map removed")
    assert_equal(response["tag_count"], 0, "deleted work response tag count")
    assert_equal(response["deleted"], True, "work delete response flag")
    assert_equal(would_write["deleted"], True, "work delete dry-run flag")


def test_empty_explicit_work_row_plan() -> None:
    payload = {"series": {"series-a": {"tags": [tag("subject:trees")]}}}
    updated, response, _would_write = assignments.plan_assignment_save(
        payload,
        "series-a",
        "00001",
        True,
        [tag("subject:trees")],
        NOW,
    )

    assert_equal(updated["series"]["series-a"]["works"]["00001"]["tags"], [], "empty explicit work row retained")
    assert_equal(response["tag_count"], 0, "empty explicit row response tag count")
    assert_equal(response["deleted"], False, "empty explicit row not deleted")


def test_assignment_import_preview_conflicts_invalid_and_missing_without_mutation() -> None:
    existing = {
        "series": {
            "series-a": {"tags": [tag("subject:current")], "updated_at_utc": "current-a"},
            "series-c": {"tags": []},
        }
    }
    original = copy.deepcopy(existing)
    session = import_session(
        {
            "series-a": {
                "base_series_updated_at_utc": "base-a",
                "base_row_snapshot": {"tags": []},
                "staged_row": {"tags": [tag("theme:growth")]},
            },
            "series-b": {
                "base_row_snapshot": {"tags": []},
                "staged_row": {"tags": [tag("theme:growth")]},
            },
            "series-c": {
                "base_row_snapshot": {"tags": []},
                "staged_row": {"tags": [], "works": {"99999": {"tags": [tag("theme:growth")]}}},
            },
        }
    )
    series_index = {"series": {"series-a": {"works": []}, "series-c": {"works": ["00002"]}}}

    preview = assignments.preview_assignment_import(existing, session, series_index)
    by_series = {row["series_id"]: row for row in preview["series"]}

    assert_equal(by_series["series-a"]["status"], "conflict", "conflict status")
    assert_equal(by_series["series-a"]["resolution_required"], True, "conflict requires resolution")
    assert_equal(by_series["series-b"]["status"], "missing", "missing status")
    assert_equal(by_series["series-c"]["status"], "invalid", "invalid status")
    assert_equal(by_series["series-c"]["invalid_work_ids"], ["99999"], "invalid work ids")
    assert_equal(preview["conflict_count"], 1, "conflict count")
    assert_equal(preview["missing_count"], 1, "missing count")
    assert_equal(preview["invalid_count"], 1, "invalid count")
    assert_equal(existing, original, "preview does not mutate existing payload")


def test_assignment_import_apply_overwrite_skip_and_missing_invalid_skips() -> None:
    existing = {
        "series": {
            "series-a": {"tags": [tag("subject:current")]},
            "series-b": {"tags": [tag("subject:base")]},
        }
    }
    session = import_session(
        {
            "series-a": {
                "base_row_snapshot": {"tags": []},
                "staged_row": {"tags": [tag("theme:overwrite")]},
            },
            "series-b": {
                "base_row_snapshot": {"tags": [tag("subject:base")]},
                "staged_row": {"tags": [tag("theme:apply")], "works": {"00002": {"tags": [tag("domain:studio", 0.3)]}}},
            },
            "series-c": {
                "base_row_snapshot": {"tags": []},
                "staged_row": {"tags": [tag("theme:missing")]},
            },
            "series-d": {
                "base_row_snapshot": {"tags": []},
                "staged_row": {"tags": [], "works": {"99999": {"tags": [tag("theme:invalid")]}}},
            },
            "series-e": {
                "base_row_snapshot": {"tags": []},
                "staged_row": {"tags": [tag("theme:skip")]},
            },
        }
    )
    series_index = {
        "series": {
            "series-a": {"works": []},
            "series-b": {"works": ["00002"]},
            "series-d": {"works": ["00004"]},
            "series-e": {"works": []},
        }
    }
    existing["series"]["series-e"] = {"tags": [tag("subject:current")]}
    original = copy.deepcopy(existing)

    preview = assignments.preview_assignment_import(existing, session, series_index)
    updated, stats = assignments.apply_assignment_import(existing, session, preview, {"series-a": "overwrite", "series-e": "skip"}, NOW)

    assert_equal(updated["series"]["series-a"]["tags"], [tag("theme:overwrite")], "overwritten series tags")
    assert_equal(updated["series"]["series-b"]["tags"], [tag("theme:apply")], "applied series tags")
    assert_equal(updated["series"]["series-b"]["works"]["00002"]["tags"], [tag("domain:studio", 0.3)], "applied work tags")
    assert_equal("series-c" in updated["series"], False, "missing series skipped")
    assert_equal("series-d" in updated["series"], False, "invalid series skipped")
    assert_equal(updated["series"]["series-e"]["tags"], [tag("subject:current")], "conflict skip preserves current row")
    assert_equal(stats["applied_series"], 2, "applied count")
    assert_equal(stats["overwritten_series"], 1, "overwrite count")
    assert_equal(stats["skipped_series"], 3, "skipped conflict, missing, and invalid count")
    assert_equal(existing, original, "apply does not mutate existing payload")


def test_assignment_import_apply_requires_conflict_resolution() -> None:
    existing = {"series": {"series-a": {"tags": [tag("subject:current")]}}}
    session = import_session(
        {
            "series-a": {
                "base_row_snapshot": {"tags": []},
                "staged_row": {"tags": [tag("theme:growth")]},
            }
        }
    )
    preview = assignments.preview_assignment_import(existing, session, {"series": {"series-a": {"works": []}}})

    assert_raises_contains(
        lambda: assignments.apply_assignment_import(existing, session, preview, {}, NOW),
        "resolution required for conflicted series",
        "missing conflict resolution",
    )


def test_assignment_import_response_payloads() -> None:
    preview_payload = {
        "series": [],
        "applicable_count": 1,
        "conflict_count": 2,
        "invalid_count": 3,
        "missing_count": 4,
        "staged_series_count": 10,
    }
    response = assignments.build_assignment_import_preview_response(preview_payload, "import.json", NOW)
    assert_equal(
        response["summary_text"],
        "assignment import preview; staged 10; apply 1; conflict 2; invalid 3; missing 4",
        "preview summary text",
    )
    apply_response = assignments.build_assignment_import_apply_response(
        response,
        {
            "applied_series": 5,
            "skipped_series": 6,
            "overwritten_series": 7,
            "conflict_count": 2,
            "invalid_count": 3,
            "missing_count": 4,
            "staged_series_count": 10,
        },
    )
    assert_equal(
        apply_response["summary_text"],
        "assignment import apply; staged 10; applied 5; skipped 6; overwritten 7; conflicts 2; invalid 3; missing 4",
        "apply summary text",
    )
    assert_equal(apply_response["import_filename"], "import.json", "apply response preserves filename")


def main() -> None:
    test_series_assignment_save_plan()
    test_work_assignment_save_strips_inherited_tags()
    test_work_assignment_delete_plan()
    test_empty_explicit_work_row_plan()
    test_assignment_import_preview_conflicts_invalid_and_missing_without_mutation()
    test_assignment_import_apply_overwrite_skip_and_missing_invalid_skips()
    test_assignment_import_apply_requires_conflict_resolution()
    test_assignment_import_response_payloads()
    print("Tag assignment service tests OK")


if __name__ == "__main__":
    main()
