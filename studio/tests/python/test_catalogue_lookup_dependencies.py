#!/usr/bin/env python3
"""Verify catalogue lookup dependency descriptors match payload builders."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Iterable, Mapping


REPO_ROOT = Path(__file__).resolve().parents[3]
SERVICES_DIR = REPO_ROOT / "studio/services"
if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))

from catalogue.catalogue_lookup import (  # noqa: E402
    SERIES_MEMBER_WORK_FIELDS,
    SERIES_SEARCH_FIELDS,
    WORK_DETAIL_PARENT_WORK_FIELDS,
    WORK_DETAIL_SEARCH_FIELDS,
    WORK_DETAIL_WORK_SUMMARY_FIELDS,
    WORK_SEARCH_FIELDS,
    WORK_SERIES_SUMMARY_FIELDS,
    build_series_lookup_payload,
    build_series_search_payload,
    build_work_detail_lookup_payload,
    build_work_detail_search_payload,
    build_work_lookup_payload,
    build_work_search_payload,
)
from catalogue.catalogue_source import (  # noqa: E402
    DETAIL_FIELDS,
    DETAIL_SECTION_FIELDS,
    SERIES_FIELDS,
    WORK_FIELDS,
    CatalogueSourceRecords,
)


WORK_ID = "00001"
DETAIL_UID = "00001-001"
SERIES_ID = "009"


def assert_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def sentinel_record(fields: Iterable[str], family: str) -> dict[str, Any]:
    return {field: f"{family}-{field}-sentinel" for field in fields}


def dependency_fixture_records() -> CatalogueSourceRecords:
    work = sentinel_record(WORK_FIELDS, "work")
    work.update(
        {
            "work_id": WORK_ID,
            "series_ids": [SERIES_ID],
            "downloads": [{"filename": "work-download-filename-sentinel", "label": "work-download-label-sentinel"}],
            "links": [{"url": "https://example.invalid/work-link-sentinel", "label": "work-link-label-sentinel"}],
        }
    )

    detail = sentinel_record(DETAIL_FIELDS, "detail")
    detail.update(
        {
            "detail_uid": DETAIL_UID,
            "work_id": WORK_ID,
            "detail_id": "001",
            "section_id": f"{WORK_ID}-3",
        }
    )
    section = {
        "section_id": f"{WORK_ID}-3",
        "work_id": WORK_ID,
        "details_subfolder": "detail-details_subfolder-sentinel",
        "section_title": "detail-section_title-sentinel",
        "section_order": 73,
        "detail_sort": "title",
    }

    series = sentinel_record(SERIES_FIELDS, "series")
    series.update(
        {
            "series_id": SERIES_ID,
            "primary_work_id": WORK_ID,
        }
    )

    return CatalogueSourceRecords(
        works={WORK_ID: work},
        work_detail_sections={section["section_id"]: section},
        work_details={DETAIL_UID: detail},
        series={SERIES_ID: series},
    )


def payload_contains_source_value(payload: Any, source_value: Any) -> bool:
    if payload == source_value:
        return True
    if isinstance(source_value, int) and payload == str(source_value):
        return True
    if isinstance(payload, Mapping):
        return any(payload_contains_source_value(value, source_value) for value in payload.values())
    if isinstance(payload, list):
        return any(payload_contains_source_value(value, source_value) for value in payload)
    return False


def payload_source_fields(
    payload: Any,
    source_record: Mapping[str, Any],
    candidate_fields: Iterable[str],
) -> set[str]:
    return {
        field
        for field in candidate_fields
        if field in source_record and payload_contains_source_value(payload, source_record[field])
    }


def only_item(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    items = payload.get("items")
    if not isinstance(items, list) or len(items) != 1:
        raise AssertionError(f"expected exactly one payload item, got {items!r}")
    item = items[0]
    if not isinstance(item, Mapping):
        raise AssertionError(f"expected payload item to be a mapping, got {item!r}")
    return item


def test_work_search_fields_match_payload_dependencies() -> None:
    records = dependency_fixture_records()

    actual_fields = payload_source_fields(
        only_item(build_work_search_payload(records)),
        records.works[WORK_ID],
        WORK_FIELDS,
    )

    assert_equal(actual_fields, set(WORK_SEARCH_FIELDS), "work search dependencies")


def test_work_search_medium_caption_guard_matches_payload_output() -> None:
    records = dependency_fixture_records()
    actual_fields = payload_source_fields(
        only_item(build_work_search_payload(records)),
        records.works[WORK_ID],
        WORK_FIELDS,
    )

    assert_equal("medium_caption" in actual_fields, False, "medium_caption work search output")
    assert_equal("medium_caption" in WORK_SEARCH_FIELDS, False, "medium_caption work search descriptor")


def test_series_member_work_fields_match_payload_dependencies() -> None:
    records = dependency_fixture_records()
    member_works = build_series_lookup_payload(records, SERIES_ID)["member_works"]

    actual_fields = payload_source_fields(member_works, records.works[WORK_ID], WORK_FIELDS)

    assert_equal(actual_fields, set(SERIES_MEMBER_WORK_FIELDS), "series member work dependencies")


def test_work_detail_work_summary_fields_match_payload_dependencies() -> None:
    records = dependency_fixture_records()
    work_summary = build_work_detail_lookup_payload(records, DETAIL_UID)["work_summary"]

    actual_fields = payload_source_fields(work_summary, records.works[WORK_ID], WORK_FIELDS)
    actual_fields.discard("work_id")

    assert_equal(actual_fields, set(WORK_DETAIL_WORK_SUMMARY_FIELDS), "work detail work summary dependencies")


def test_work_detail_search_fields_match_payload_dependencies() -> None:
    records = dependency_fixture_records()
    payload = only_item(build_work_detail_search_payload(records))

    actual_fields = payload_source_fields(payload, records.work_details[DETAIL_UID], DETAIL_FIELDS)
    actual_fields.update(
        payload_source_fields(
            payload,
            records.work_detail_sections[f"{WORK_ID}-3"],
            DETAIL_SECTION_FIELDS,
        )
    )

    assert_equal(actual_fields, set(WORK_DETAIL_SEARCH_FIELDS), "work detail search dependencies")


def test_work_detail_parent_work_fields_match_payload_dependencies() -> None:
    records = dependency_fixture_records()
    detail_sections = build_work_lookup_payload(records, WORK_ID)["detail_sections"]

    actual_fields = payload_source_fields(detail_sections, records.work_details[DETAIL_UID], DETAIL_FIELDS)
    actual_fields.update(
        payload_source_fields(
            detail_sections,
            records.work_detail_sections[f"{WORK_ID}-3"],
            DETAIL_SECTION_FIELDS,
        )
    )
    actual_fields.discard("detail_uid")
    actual_fields.add("work_id")

    assert_equal(actual_fields, set(WORK_DETAIL_PARENT_WORK_FIELDS), "work detail parent work dependencies")


def test_series_search_fields_match_payload_dependencies() -> None:
    records = dependency_fixture_records()

    actual_fields = payload_source_fields(
        only_item(build_series_search_payload(records)),
        records.series[SERIES_ID],
        SERIES_FIELDS,
    )

    assert_equal(actual_fields, set(SERIES_SEARCH_FIELDS), "series search dependencies")


def test_work_series_summary_fields_match_payload_dependencies() -> None:
    records = dependency_fixture_records()
    series_summary = build_work_lookup_payload(records, WORK_ID)["series_summary"]

    actual_fields = payload_source_fields(series_summary, records.series[SERIES_ID], SERIES_FIELDS)
    actual_fields.discard("series_id")

    assert_equal(actual_fields, set(WORK_SERIES_SUMMARY_FIELDS), "work series summary dependencies")


def main() -> None:
    test_work_search_fields_match_payload_dependencies()
    test_work_search_medium_caption_guard_matches_payload_output()
    test_series_member_work_fields_match_payload_dependencies()
    test_work_detail_work_summary_fields_match_payload_dependencies()
    test_work_detail_search_fields_match_payload_dependencies()
    test_work_detail_parent_work_fields_match_payload_dependencies()
    test_series_search_fields_match_payload_dependencies()
    test_work_series_summary_fields_match_payload_dependencies()
    print("Catalogue lookup dependency tests OK")


if __name__ == "__main__":
    main()
