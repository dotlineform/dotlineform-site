#!/usr/bin/env python3
"""Verify generated catalogue recent-publications builders."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from catalogue import catalogue_generation_recent as recent  # noqa: E402


def normalized_entries(entries: list[dict[str, object]]) -> list[dict[str, object]]:
    return [entry for entry in (recent.normalize_recent_entry(raw) for raw in entries) if entry is not None]


def sample_series_payload() -> dict[str, dict[str, object]]:
    return {
        "009": {
            "series_id": "009",
            "title": "Alpha",
            "primary_work_id": "00001",
            "works": ["00001", "00002", "00003"],
        },
        "010": {
            "series_id": "010",
            "title": "Beta",
            "primary_work_id": "00004",
            "works": ["00004"],
        },
    }


def sample_works_payload() -> dict[str, dict[str, object]]:
    return {
        "00001": {"work_id": "00001", "title": "First"},
        "00002": {"work_id": "00002", "title": "Second"},
        "00003": {"work_id": "00003", "title": "Third"},
        "00004": {"work_id": "00004", "title": "Fourth"},
    }


def sample_work_meta() -> dict[str, dict[str, object]]:
    return {
        "00001": {"series_ids": ["009"]},
        "00002": {"series_ids": ["009"]},
        "00003": {"series_ids": ["009"]},
        "00004": {"series_ids": ["010"]},
        "00005": {"series_ids": ["011"]},
    }


def build_entries(
    *,
    existing_entries: list[dict[str, object]] | None = None,
    series_publish_transitions: list[dict[str, object]] | None = None,
    work_publish_transitions: list[dict[str, object]] | None = None,
    work_status_by_id: dict[str, str] | None = None,
    series_status_by_id: dict[str, str] | None = None,
) -> list[dict[str, object]]:
    return recent.build_recent_publication_entries(
        existing_entries=normalized_entries(existing_entries or []),
        series_publish_transitions=series_publish_transitions or [],
        work_publish_transitions=work_publish_transitions or [],
        series_payload=sample_series_payload(),
        works_payload=sample_works_payload(),
        work_meta_by_id=sample_work_meta(),
        work_status_by_id=work_status_by_id or {
            "00001": "published",
            "00002": "published",
            "00003": "published",
            "00004": "published",
            "00005": "draft",
        },
        series_status_by_id=series_status_by_id or {
            "009": "published",
            "010": "published",
            "011": "draft",
        },
        series_sort_by_series_id={
            "009": {
                "00001": "003-00001",
                "00002": "001-00002",
                "00003": "002-00003",
            },
            "010": {"00004": "001-00004"},
        },
        series_title_by_id={"009": "Alpha", "010": "Beta"},
        recorded_at_utc="2026-05-09T12:00:00Z",
    )


def test_retains_only_current_published_targets() -> None:
    entries = build_entries(
        existing_entries=[
            {"kind": "series", "target_id": "010", "title": "Beta", "published_date": "2026-05-01"},
            {"kind": "series", "target_id": "011", "title": "Draft", "published_date": "2026-05-02"},
            {"kind": "work", "target_id": "00001", "title": "First", "published_date": "2026-05-03"},
            {"kind": "work", "target_id": "00005", "title": "Draft Work", "published_date": "2026-05-04"},
            {"kind": "work", "target_id": "99999", "title": "Missing", "published_date": "2026-05-05"},
        ]
    )

    assert {entry["id"] for entry in entries} == {"series:010", "work:00001"}


def test_series_publish_transition_adds_series_entry() -> None:
    entries = build_entries(
        series_publish_transitions=[
            {
                "series_id": "010",
                "title": "Beta",
                "work_count": 1,
                "primary_work_id": "00004",
                "published_date": "2026-05-09",
            }
        ]
    )

    assert entries == [
        {
            "id": "series:010",
            "kind": "series",
            "target_id": "010",
            "title": "Beta",
            "caption": "1 work",
            "published_date": "2026-05-09",
            "thumb_id": "00004",
            "recorded_at_utc": "2026-05-09T12:00:00Z",
            "session_order": 1,
        }
    ]


def test_groups_newly_published_works_by_primary_series_sort() -> None:
    entries = build_entries(
        work_publish_transitions=[
            {
                "work_id": "00003",
                "title": "Third",
                "primary_series_id": "009",
                "series_title": "Alpha",
                "published_date": "2026-05-09",
            },
            {
                "work_id": "00002",
                "title": "Second",
                "primary_series_id": "009",
                "series_title": "Alpha",
                "published_date": "2026-05-09",
            },
        ]
    )

    assert entries == [
        {
            "id": "work:00002",
            "kind": "work",
            "target_id": "00002",
            "title": "Second",
            "caption": "2 new works in Alpha",
            "published_date": "2026-05-09",
            "thumb_id": "00002",
            "recorded_at_utc": "2026-05-09T12:00:00Z",
            "session_order": 1,
        }
    ]


def test_latest_series_absorbs_existing_and_new_work_entries() -> None:
    entries = build_entries(
        existing_entries=[
            {
                "kind": "series",
                "target_id": "009",
                "title": "Alpha",
                "caption": "3 works",
                "published_date": "2026-05-01",
                "thumb_id": "00001",
                "recorded_at_utc": "2026-05-01T08:00:00Z",
                "session_order": 1,
            },
            {
                "kind": "work",
                "target_id": "00001",
                "title": "First",
                "caption": "Alpha",
                "published_date": "2026-05-03",
                "thumb_id": "00001",
                "recorded_at_utc": "2026-05-03T09:00:00Z",
                "session_order": 2,
            },
        ],
        work_publish_transitions=[
            {
                "work_id": "00002",
                "title": "Second",
                "primary_series_id": "009",
                "series_title": "Alpha",
                "published_date": "2026-05-09",
            }
        ],
    )

    assert entries == [
        {
            "id": "series:009",
            "kind": "series",
            "target_id": "009",
            "title": "Alpha",
            "caption": "3 works",
            "published_date": "2026-05-09",
            "thumb_id": "00001",
            "recorded_at_utc": "2026-05-09T12:00:00Z",
            "session_order": 1,
        }
    ]


def test_series_publish_suppresses_grouped_work_entry_for_same_series() -> None:
    entries = build_entries(
        series_publish_transitions=[
            {
                "series_id": "009",
                "title": "Alpha",
                "work_count": 3,
                "primary_work_id": "00001",
                "published_date": "2026-05-09",
            }
        ],
        work_publish_transitions=[
            {
                "work_id": "00002",
                "title": "Second",
                "primary_series_id": "009",
                "series_title": "Alpha",
                "published_date": "2026-05-09",
            }
        ],
    )

    assert [entry["id"] for entry in entries] == ["series:009"]


def test_payload_cap_and_ordering_are_deterministic() -> None:
    entries = normalized_entries([
        {"kind": "work", "target_id": "00001", "title": "B", "published_date": "2026-05-02", "recorded_at_utc": "2026-05-02T09:00:00Z", "session_order": 2},
        {"kind": "series", "target_id": "009", "title": "A", "published_date": "2026-05-02", "recorded_at_utc": "2026-05-02T09:00:00Z", "session_order": 1},
        {"kind": "work", "target_id": "00002", "title": "C", "published_date": "2026-05-03", "recorded_at_utc": "2026-05-03T09:00:00Z", "session_order": 1},
    ])
    payload = recent.build_recent_index_payload(
        entries=entries,
        generated_at_utc="2026-05-09T12:30:00Z",
        limit=2,
    )

    assert payload["header"]["schema"] == "recent_index_v1"
    assert payload["header"]["generated_at_utc"] == "2026-05-09T12:30:00Z"
    assert payload["header"]["count"] == 2
    assert [entry["id"] for entry in payload["entries"]] == ["work:00002", "series:009"]


def main() -> None:
    test_retains_only_current_published_targets()
    test_series_publish_transition_adds_series_entry()
    test_groups_newly_published_works_by_primary_series_sort()
    test_latest_series_absorbs_existing_and_new_work_entries()
    test_series_publish_suppresses_grouped_work_entry_for_same_series()
    test_payload_cap_and_ordering_are_deterministic()
    print("Catalogue generation recent tests OK")


if __name__ == "__main__":
    main()
