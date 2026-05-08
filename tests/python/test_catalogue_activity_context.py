#!/usr/bin/env python3
"""Verify Studio activity context normalization for catalogue writes."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
STUDIO_SCRIPTS_DIR = REPO_ROOT / "scripts" / "studio"
if str(STUDIO_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(STUDIO_SCRIPTS_DIR))

import catalogue_write_server as server  # noqa: E402


def assert_equal(actual, expected, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def assert_raises_value_error(callback, expected_message: str) -> None:
    try:
        callback()
    except ValueError as exc:
        if expected_message not in str(exc):
            raise AssertionError(f"expected {expected_message!r} in {exc!r}") from exc
        return
    raise AssertionError("expected ValueError")


def normalize(
    raw_context,
    *,
    page_id: str = server.ACTIVITY_CONTEXT_PAGE_CATALOGUE_WORK,
    action_id: str = server.ACTIVITY_CONTEXT_ACTION_SAVE_WORK,
    route: str = server.ACTIVITY_CONTEXT_ROUTE_CATALOGUE_WORK,
    control_id: str = server.ACTIVITY_CONTEXT_CONTROL_CATALOGUE_WORK_SAVE,
    record_id_field: str = "work_id",
    record_id: str = "00001",
) -> dict[str, str]:
    return server.normalize_activity_context(
        raw_context,
        page_id=page_id,
        action_id=action_id,
        route=route,
        control_id=control_id,
        record_id_field=record_id_field,
        record_id=record_id,
    )


def test_missing_context_is_optional() -> None:
    assert_equal(normalize(None), {}, "missing context")


def test_save_work_context_is_normalized() -> None:
    context = normalize(
        {
            "page_id": "catalogue-work",
            "action_id": "save-work",
            "route": "/studio/catalogue-work/",
            "control_id": "catalogueWorkSave",
            "control_selector": "#catalogueWorkSave",
            "work_id": "00001",
            "correlation_id": "save-work:test 123",
            "ignored": "drop me",
        }
    )
    assert_equal(context["page_id"], "catalogue-work", "page_id")
    assert_equal(context["action_id"], "save-work", "action_id")
    assert_equal(context["route"], "/studio/catalogue-work/", "route")
    assert_equal(context["control_id"], "catalogueWorkSave", "control_id")
    assert_equal(context["control_selector"], "#catalogueWorkSave", "control_selector")
    assert_equal(context["work_id"], "00001", "work_id")
    assert_equal(context["record_id_field"], "work_id", "record_id_field")
    assert_equal(context["correlation_id"], "save-work:test123", "correlation_id")
    if "ignored" in context:
        raise AssertionError("unknown activity context fields should be ignored")


def test_server_assigns_missing_correlation_id() -> None:
    context = normalize(
        {
            "page_id": "catalogue-work",
            "action_id": "save-work",
            "route": "/studio/catalogue-work/",
            "control_id": "catalogueWorkSave",
            "work_id": "00001",
        }
    )
    correlation_id = context["correlation_id"]
    if len(correlation_id) != 32 or not correlation_id.isalnum():
        raise AssertionError(f"expected generated uuid-like correlation id, got {correlation_id!r}")


def test_batch_a_save_contexts_are_normalized() -> None:
    scenarios = [
        {
            "page_id": server.ACTIVITY_CONTEXT_PAGE_CATALOGUE_WORK_DETAIL,
            "action_id": server.ACTIVITY_CONTEXT_ACTION_SAVE_WORK_DETAIL,
            "route": server.ACTIVITY_CONTEXT_ROUTE_CATALOGUE_WORK_DETAIL,
            "control_id": server.ACTIVITY_CONTEXT_CONTROL_CATALOGUE_WORK_DETAIL_SAVE,
            "record_id_field": "detail_uid",
            "record_id": "00001-001",
        },
        {
            "page_id": server.ACTIVITY_CONTEXT_PAGE_CATALOGUE_SERIES,
            "action_id": server.ACTIVITY_CONTEXT_ACTION_SAVE_SERIES,
            "route": server.ACTIVITY_CONTEXT_ROUTE_CATALOGUE_SERIES,
            "control_id": server.ACTIVITY_CONTEXT_CONTROL_CATALOGUE_SERIES_SAVE,
            "record_id_field": "series_id",
            "record_id": "009",
        },
        {
            "page_id": server.ACTIVITY_CONTEXT_PAGE_CATALOGUE_MOMENT,
            "action_id": server.ACTIVITY_CONTEXT_ACTION_SAVE_MOMENT,
            "route": server.ACTIVITY_CONTEXT_ROUTE_CATALOGUE_MOMENT,
            "control_id": server.ACTIVITY_CONTEXT_CONTROL_CATALOGUE_MOMENT_SAVE,
            "record_id_field": "moment_id",
            "record_id": "studio-test",
        },
    ]
    for scenario in scenarios:
        context = normalize(
            {
                "page_id": scenario["page_id"],
                "action_id": scenario["action_id"],
                "route": scenario["route"],
                "control_id": scenario["control_id"],
                "control_selector": f"#{scenario['control_id']}",
                scenario["record_id_field"]: scenario["record_id"],
                "correlation_id": f"{scenario['action_id']}:abc",
            },
            **scenario,
        )
        assert_equal(context["page_id"], scenario["page_id"], f"{scenario['action_id']} page_id")
        assert_equal(context["action_id"], scenario["action_id"], f"{scenario['action_id']} action_id")
        assert_equal(context["route"], scenario["route"], f"{scenario['action_id']} route")
        assert_equal(context["control_id"], scenario["control_id"], f"{scenario['action_id']} control_id")
        assert_equal(context[scenario["record_id_field"]], scenario["record_id"], f"{scenario['action_id']} record id")


def test_context_must_match_expected_action_and_record() -> None:
    assert_raises_value_error(
        lambda: normalize(
            {
                "page_id": "catalogue-work",
                "action_id": "delete-work",
                "route": "/studio/catalogue-work/",
                "control_id": "catalogueWorkSave",
                "work_id": "00001",
            }
        ),
        "activity_context.action_id",
    )
    assert_raises_value_error(
        lambda: normalize(
            {
                "page_id": "catalogue-work",
                "action_id": "save-work",
                "route": "/studio/catalogue-work/",
                "control_id": "catalogueWorkSave",
                "work_id": "99999",
            }
        ),
        "activity_context.work_id",
    )


def test_catalogue_build_activity_rows_follow_attempted_steps() -> None:
    context = normalize(
        {
            "page_id": "catalogue-series",
            "action_id": "save-series",
            "route": "/studio/catalogue-series/",
            "control_id": "catalogueSeriesSave",
            "series_id": "009",
            "correlation_id": "save-series:009",
        },
        page_id=server.ACTIVITY_CONTEXT_PAGE_CATALOGUE_SERIES,
        action_id=server.ACTIVITY_CONTEXT_ACTION_SAVE_SERIES,
        route=server.ACTIVITY_CONTEXT_ROUTE_CATALOGUE_SERIES,
        control_id=server.ACTIVITY_CONTEXT_CONTROL_CATALOGUE_SERIES_SAVE,
        record_id_field="series_id",
        record_id="009",
    )
    rows = server.catalogue_build_activity_rows(
        context,
        {
            "ok": False,
            "completed_at_utc": "2026-05-08T12:00:00Z",
            "build": {"work_ids": ["00001"], "series_ids": ["009"]},
            "steps": [
                {"label": "Generate Work Pages", "exit_code": 0},
                {"label": "Build Catalogue Search Index", "exit_code": 1},
            ],
        },
        published_step_label="Generate Work Pages",
        published_script_purpose_id="rebuild-published-series-data",
        published_detail="Updated published series/work JSON for series 009",
        search_detail="Rebuilt catalogue search for series 009",
        fallback_record_groups={"works": [], "series": ["009"], "work_details": [], "moments": []},
    )
    assert_equal([row["script_purpose_id"] for row in rows], ["rebuild-published-series-data", "update-search"], "build row purpose order")
    assert_equal([row["status"] for row in rows], ["completed", "warning"], "build row statuses")
    assert_equal(rows[0]["record_groups"]["works"], ["00001"], "build row work scope")
    assert_equal(rows[1]["record_groups"]["search"], ["catalogue"], "search scope")


def main() -> None:
    test_missing_context_is_optional()
    test_save_work_context_is_normalized()
    test_server_assigns_missing_correlation_id()
    test_batch_a_save_contexts_are_normalized()
    test_context_must_match_expected_action_and_record()
    test_catalogue_build_activity_rows_follow_attempted_steps()
    print("Catalogue activity context tests OK")


if __name__ == "__main__":
    main()
