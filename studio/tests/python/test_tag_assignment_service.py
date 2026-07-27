#!/usr/bin/env python3
"""Verify direct tag assignment save planners."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
STUDIO_SERVICES_DIR = REPO_ROOT / "studio" / "services"
for path in (STUDIO_SERVICES_DIR,):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from tags import tag_assignment_service as assignments  # noqa: E402


NOW = "2026-05-09T12:00:00Z"


def tag(tag_id: str, weight: float = 0.6) -> dict[str, Any]:
    return {"tag_id": tag_id, "w_manual": weight}


def assert_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


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
    assert_equal(would_write["deleted"], True, "work dry-run delete flag")


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


def main() -> None:
    test_series_assignment_save_plan()
    test_work_assignment_save_strips_inherited_tags()
    test_work_assignment_delete_plan()
    test_empty_explicit_work_row_plan()
    print("Tag assignment service tests OK")


if __name__ == "__main__":
    main()
