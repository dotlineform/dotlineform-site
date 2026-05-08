#!/usr/bin/env python3
"""Verify Studio activity context normalization for catalogue writes."""

from __future__ import annotations

import json
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


def normalize_for_profile(raw_context, profile: server.ActivityActionProfile, record_id: str) -> dict[str, str]:
    return server.normalize_activity_context_for_profile(raw_context, profile, record_id=record_id)


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
        (server.ACTIVITY_PROFILE_SAVE_WORK_DETAIL, "00001-001"),
        (server.ACTIVITY_PROFILE_SAVE_SERIES, "009"),
        (server.ACTIVITY_PROFILE_SAVE_MOMENT, "studio-test"),
    ]
    for profile, record_id in scenarios:
        context = normalize_for_profile(
            {
                "page_id": profile.page_id,
                "action_id": profile.action_id,
                "route": profile.route,
                "control_id": profile.control_id,
                "control_selector": profile.control_selector,
                profile.record_id_field: record_id,
                "correlation_id": f"{profile.action_id}:abc",
            },
            profile,
            record_id,
        )
        assert_equal(context["page_id"], profile.page_id, f"{profile.action_id} page_id")
        assert_equal(context["action_id"], profile.action_id, f"{profile.action_id} action_id")
        assert_equal(context["route"], profile.route, f"{profile.action_id} route")
        assert_equal(context["control_id"], profile.control_id, f"{profile.action_id} control_id")
        assert_equal(context[profile.record_id_field], record_id, f"{profile.action_id} record id")


def test_batch_b_contexts_are_normalized() -> None:
    scenarios = [
        (server.ACTIVITY_PROFILE_CREATE_WORK, "09999"),
        (server.ACTIVITY_PROFILE_CREATE_WORK_DETAIL, "00001-099"),
        (server.ACTIVITY_PROFILE_CREATE_SERIES, "099"),
        (server.activity_profile_for_publication("work", "publish"), "00001"),
        (server.activity_profile_for_publication("work_detail", "unpublish"), "00001-001"),
        (server.activity_profile_for_publication("series", "publish"), "009"),
        (server.activity_profile_for_publication("moment", "unpublish"), "studio-test"),
        (server.activity_profile_for_delete("work"), "00001"),
        (server.activity_profile_for_delete("work_detail"), "00001-001"),
        (server.activity_profile_for_delete("series"), "009"),
        (server.activity_profile_for_delete("moment"), "studio-test"),
    ]
    for profile, record_id in scenarios:
        context = normalize_for_profile(
            {
                "page_id": profile.page_id,
                "action_id": profile.action_id,
                "route": profile.route,
                "control_id": profile.control_id,
                "control_selector": profile.control_selector,
                profile.record_id_field: record_id,
                "correlation_id": f"{profile.action_id}:{record_id}",
            },
            profile,
            record_id,
        )
        assert_equal(context["page_id"], profile.page_id, f"{profile.action_id} page_id")
        assert_equal(context["action_id"], profile.action_id, f"{profile.action_id} action_id")
        assert_equal(context["route"], profile.route, f"{profile.action_id} route")
        assert_equal(context["control_id"], profile.control_id, f"{profile.action_id} control_id")
        assert_equal(context[profile.record_id_field], record_id, f"{profile.action_id} record id")


def test_batch_c_catalogue_service_contexts_are_normalized() -> None:
    scenarios = [
        (server.ACTIVITY_PROFILE_IMPORT_WORKBOOK_RECORDS, "works"),
        (server.ACTIVITY_PROFILE_IMPORT_WORKBOOK_RECORDS, "work_details"),
        (server.ACTIVITY_PROFILE_IMPORT_MOMENT, "studio-test"),
        (server.ACTIVITY_PROFILE_RUN_PROJECT_STATE_REPORT, "project-state"),
    ]
    for profile, record_id in scenarios:
        context = normalize_for_profile(
            {
                "page_id": profile.page_id,
                "action_id": profile.action_id,
                "route": profile.route,
                "control_id": profile.control_id,
                "control_selector": profile.control_selector,
                profile.record_id_field: record_id,
                "correlation_id": f"{profile.action_id}:{record_id}",
            },
            profile,
            record_id,
        )
        assert_equal(context["page_id"], profile.page_id, f"{profile.action_id} page_id")
        assert_equal(context["action_id"], profile.action_id, f"{profile.action_id} action_id")
        assert_equal(context["route"], profile.route, f"{profile.action_id} route")
        assert_equal(context["control_id"], profile.control_id, f"{profile.action_id} control_id")
        assert_equal(context[profile.record_id_field], record_id, f"{profile.action_id} record id")


def test_activity_profiles_match_registry() -> None:
    contract = json.loads((REPO_ROOT / "assets/studio/data/activity_contract.json").read_text(encoding="utf-8"))
    pages = contract["pages"]
    for profile in server.ACTIVITY_ACTION_PROFILES:
        page = pages.get(profile.page_id)
        if not isinstance(page, dict):
            raise AssertionError(f"profile page missing from registry: {profile.page_id}")
        action = (page.get("actions") or {}).get(profile.action_id)
        if not isinstance(action, dict):
            raise AssertionError(f"profile action missing from registry: {profile.action_id}")
        assert_equal(page.get("route"), profile.route, f"{profile.action_id} route")
        assert_equal(action.get("control_id"), profile.control_id, f"{profile.action_id} control_id")
        assert_equal(action.get("control_selector"), profile.control_selector, f"{profile.action_id} control_selector")
        assert_equal(action.get("endpoint"), profile.endpoint, f"{profile.action_id} endpoint")
        assert_equal(action.get("record_family"), profile.record_family, f"{profile.action_id} record_family")
        assert_equal(action.get("record_id_field"), profile.record_id_field, f"{profile.action_id} record_id_field")
        purpose_ids = tuple(str(row.get("id") or "").strip() for row in action.get("script_purposes") or [])
        assert_equal(purpose_ids, profile.script_purpose_ids, f"{profile.action_id} purpose ids")


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


def test_catalogue_build_studio_activity_rows_follow_attempted_steps() -> None:
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
    rows = server.catalogue_build_studio_activity_rows(
        server.ACTIVITY_PROFILE_SAVE_SERIES,
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
        published_detail="Updated published series/work JSON for series 009",
        search_detail="Rebuilt catalogue search for series 009",
        fallback_record_groups={"works": [], "series": ["009"], "work_details": [], "moments": []},
    )
    assert_equal([row["script_purpose_id"] for row in rows], ["rebuild-published-series-data", "update-search"], "build row purpose order")
    assert_equal([row["status"] for row in rows], ["completed", "warning"], "build row statuses")
    assert_equal(rows[0]["record_groups"]["works"], ["00001"], "build row work scope")
    assert_equal(rows[1]["record_groups"]["search"], ["catalogue"], "search scope")


def test_delete_activity_rows_follow_profile_order() -> None:
    profile = server.activity_profile_for_delete("work")
    context = normalize_for_profile(
        {
            "page_id": profile.page_id,
            "action_id": profile.action_id,
            "route": profile.route,
            "control_id": profile.control_id,
            "work_id": "00001",
            "correlation_id": "delete-work:00001",
        },
        profile,
        "00001",
    )
    rows = server.catalogue_delete_activity_rows(
        profile,
        context,
        {
            "deleted_files": 2,
            "updated_json_files": 3,
            "catalogue_search_rebuilt": True,
            "search_exit_code": 0,
        },
        now_utc="2026-05-08T12:00:00Z",
        record_groups={"works": ["00001"], "series": [], "work_details": [], "moments": [], "search": []},
        source_detail_items=["Deleted canonical work source record 00001"],
        cleanup_detail_items=["Cleaned generated artifacts for deleted work 00001"],
    )
    assert_equal(
        [row["script_purpose_id"] for row in rows],
        ["delete-canonical-data", "clean-generated-artifacts", "rebuild-lookups", "update-search"],
        "delete row purpose order",
    )
    assert_equal([row["status"] for row in rows], ["completed", "completed", "completed", "completed"], "delete row statuses")
    assert_equal(rows[3]["record_groups"]["search"], ["catalogue"], "delete search scope")


def test_moment_create_stays_out_of_batch_b_contract() -> None:
    contract = json.loads((REPO_ROOT / "assets/studio/data/activity_contract.json").read_text(encoding="utf-8"))
    moment_actions = contract["pages"]["catalogue-moment"]["actions"]
    if "create-moment" in moment_actions:
        raise AssertionError("moment creation belongs to import/apply coverage, not Batch B create-mode coverage")


def test_moment_profiles_do_not_emit_lookup_rows() -> None:
    profiles = [
        server.ACTIVITY_PROFILE_SAVE_MOMENT,
        server.activity_profile_for_publication("moment", "publish"),
        server.activity_profile_for_publication("moment", "unpublish"),
        server.activity_profile_for_delete("moment"),
    ]
    for profile in profiles:
        if "rebuild-lookups" in profile.script_purpose_ids:
            raise AssertionError(f"{profile.action_id} should not advertise Studio lookup refresh activity")
        assert_equal(profile.lookup_script_purpose_id, "", f"{profile.action_id} lookup purpose")


def test_moment_build_invalidation_uses_moment_artifacts() -> None:
    invalidation = server.moment_build_invalidation_for_fields(["title"])
    assert_equal(invalidation["class"], server.LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD, "moment invalidation class")
    assert_equal(invalidation["artifacts"], ["catalogue_search", "moment_record", "moments_index"], "moment invalidation artifacts")


def main() -> None:
    test_missing_context_is_optional()
    test_save_work_context_is_normalized()
    test_server_assigns_missing_correlation_id()
    test_batch_a_save_contexts_are_normalized()
    test_batch_b_contexts_are_normalized()
    test_batch_c_catalogue_service_contexts_are_normalized()
    test_activity_profiles_match_registry()
    test_context_must_match_expected_action_and_record()
    test_catalogue_build_studio_activity_rows_follow_attempted_steps()
    test_delete_activity_rows_follow_profile_order()
    test_moment_create_stays_out_of_batch_b_contract()
    test_moment_profiles_do_not_emit_lookup_rows()
    test_moment_build_invalidation_uses_moment_artifacts()
    print("Studio activity context tests OK")


if __name__ == "__main__":
    main()
