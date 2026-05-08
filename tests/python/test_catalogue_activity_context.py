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


def normalize(raw_context, record_id: str = "00001") -> dict[str, str]:
    return server.normalize_activity_context(
        raw_context,
        page_id=server.ACTIVITY_CONTEXT_PAGE_CATALOGUE_WORK,
        action_id=server.ACTIVITY_CONTEXT_ACTION_SAVE_WORK,
        route=server.ACTIVITY_CONTEXT_ROUTE_CATALOGUE_WORK,
        control_id=server.ACTIVITY_CONTEXT_CONTROL_CATALOGUE_WORK_SAVE,
        record_id_field="work_id",
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


def main() -> None:
    test_missing_context_is_optional()
    test_save_work_context_is_normalized()
    test_server_assigns_missing_correlation_id()
    test_context_must_match_expected_action_and_record()
    print("Catalogue activity context tests OK")


if __name__ == "__main__":
    main()
