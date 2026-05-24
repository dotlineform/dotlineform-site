#!/usr/bin/env python3
"""Verify tag-specific Studio activity helpers."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = REPO_ROOT / "scripts"
for path in (SCRIPTS_DIR,):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from analytics import tag_activity as activity  # noqa: E402
from analytics import tag_routes as routes  # noqa: E402


def assert_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def assert_true(value: Any, label: str) -> None:
    if not value:
        raise AssertionError(f"{label}: expected truthy value")


def assert_false(value: Any, label: str) -> None:
    if value:
        raise AssertionError(f"{label}: expected falsey value")


def tag_context(tag_id: str = "subject:trees") -> Dict[str, str]:
    return {
        "correlation_id": "tag-activity-test",
        "page_id": "tag-registry",
        "action_id": "edit-tag",
        "route": "/studio/analytics/tag-registry/",
        "control_id": "save-edit",
        "control_selector": "[data-role=\"save-edit\"]",
        "tag_id": tag_id,
    }


def alias_context(alias: str = "foliage") -> Dict[str, str]:
    return {
        "correlation_id": "tag-activity-test",
        "page_id": "tag-aliases",
        "action_id": "edit-tag-alias",
        "route": "/studio/analytics/tag-aliases/",
        "control_id": "save-edit-alias",
        "control_selector": "[data-role=\"save-edit-alias\"]",
        "alias": alias,
    }


def test_activity_write_endpoints_are_route_owned() -> None:
    assert_equal(set(activity.ACTIVITY_WRITE_ENDPOINTS) - set(routes.POST_PATHS), set(), "activity endpoints")
    preview_endpoints = [endpoint for endpoint in activity.ACTIVITY_WRITE_ENDPOINTS if endpoint.endswith("-preview")]
    assert_equal(preview_endpoints, [], "activity write endpoints should exclude preview routes")


def test_activity_status_decisions() -> None:
    assert_equal(activity.tag_activity_status({"invalid_count": 1, "conflict_count": 2}), "failed", "invalid status")
    assert_equal(activity.tag_activity_status({"missing_count": 1}), "failed", "missing status")
    assert_equal(activity.tag_activity_status({"conflict_count": 1}), "warning", "conflict status")
    assert_equal(activity.tag_activity_status({"added": 1}), "completed", "completed status")


def test_activity_changed_suppresses_no_ops() -> None:
    assert_false(activity.tag_activity_changed({"added": 0, "overwritten": 0}), "unchanged stats")
    assert_true(activity.tag_activity_changed({"added": 1}), "added stats")
    assert_true(activity.tag_activity_changed({"changed": True}), "changed flag")
    assert_true(activity.tag_activity_changed({"canonical_changed": True}), "canonical changed")
    assert_true(activity.tag_activity_changed({"description_changed": True}), "description changed")


def test_activity_append_is_write_only() -> None:
    calls: list[Dict[str, Any]] = []
    response = {"updated_at_utc": "2026-05-09T12:00:00Z"}
    activity.attach_tag_activity(
        repo_root=REPO_ROOT,
        endpoint=routes.MUTATE_TAG_APPLY_PATH,
        dry_run=True,
        append_activity=calls.append,
        body={"activity_context": tag_context()},
        response_payload=response,
        record_id="subject:trees",
    )
    assert_equal(calls, [], "dry-run append calls")
    assert_false("activity_log" in response, "dry-run activity log")

    activity.attach_tag_activity(
        repo_root=REPO_ROOT,
        endpoint=routes.MUTATE_TAG_APPLY_PATH,
        dry_run=False,
        append_activity=calls.append,
        body={},
        response_payload=response,
        record_id="subject:trees",
    )
    assert_equal(calls, [], "missing context append calls")


def test_tag_record_group_is_resolved_from_context() -> None:
    calls: list[Dict[str, Any]] = []
    response = {"updated_at_utc": "2026-05-09T12:00:00Z", "summary_text": "edited tag"}
    activity.attach_tag_activity(
        repo_root=REPO_ROOT,
        endpoint=routes.MUTATE_TAG_APPLY_PATH,
        dry_run=False,
        append_activity=calls.append,
        body={"activity_context": tag_context()},
        response_payload=response,
        record_id="subject:trees",
        status="completed",
    )
    assert_equal(len(calls), 1, "tag append calls")
    assert_equal(calls[0]["record_groups"]["tags"], ["subject:trees"], "tag record group")
    assert_equal(calls[0]["source_refs"], [{"kind": "log", "path": "var/studio/logs/studio_analytics_api.log"}], "source refs")
    assert_equal(response["activity_log"], {"written_count": 1}, "activity log")


def test_alias_record_group_is_resolved_from_context() -> None:
    calls: list[Dict[str, Any]] = []
    response = {"updated_at_utc": "2026-05-09T12:00:00Z", "summary_text": "edited alias"}
    activity.attach_tag_activity(
        repo_root=REPO_ROOT,
        endpoint=routes.MUTATE_ALIAS_APPLY_PATH,
        dry_run=False,
        append_activity=calls.append,
        body={"activity_context": alias_context()},
        response_payload=response,
        record_id="foliage",
        status="completed",
    )
    assert_equal(len(calls), 1, "alias append calls")
    assert_equal(calls[0]["record_groups"]["aliases"], ["foliage"], "alias record group")
    assert_equal(response["activity_context"]["alias"], "foliage", "alias activity context")


def test_activity_append_failure_is_non_fatal() -> None:
    def fail_append(_entry: Dict[str, Any]) -> None:
        raise RuntimeError("append failed")

    response = {"updated_at_utc": "2026-05-09T12:00:00Z", "summary_text": "edited tag"}
    activity.attach_tag_activity(
        repo_root=REPO_ROOT,
        endpoint=routes.MUTATE_TAG_APPLY_PATH,
        dry_run=False,
        append_activity=fail_append,
        body={"activity_context": tag_context()},
        response_payload=response,
        record_id="subject:trees",
    )
    assert_equal(response["activity_log"]["written_count"], 0, "failed append count")
    assert_true("append failed" in response["activity_log"].get("error", ""), "failed append error")


def main() -> None:
    test_activity_write_endpoints_are_route_owned()
    test_activity_status_decisions()
    test_activity_changed_suppresses_no_ops()
    test_activity_append_is_write_only()
    test_tag_record_group_is_resolved_from_context()
    test_alias_record_group_is_resolved_from_context()
    test_activity_append_failure_is_non_fatal()
    print("Tag activity tests OK")


if __name__ == "__main__":
    main()
