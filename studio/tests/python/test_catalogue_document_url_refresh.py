#!/usr/bin/env python3
"""Verify exact generated Catalogue document URL follow-through."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from catalogue import catalogue_transactions as transactions
from catalogue.catalogue_document_url_refresh import (
    apply_catalogue_document_url_refresh_plan,
    build_catalogue_document_url_refresh_plan,
)
from catalogue.catalogue_generation_common import (
    compact_json_object,
    compute_payload_version,
)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def work_payload(work_id: str, urls: list[str]) -> dict[str, object]:
    return {
        "header": {
            "schema": "work_record_v4",
            "version": f"before-{work_id}",
            "generated_at_utc": "2026-08-01T00:00:00Z",
            "work_id": work_id,
            "count": 0,
        },
        "work": {
            "work_id": work_id,
            "title": f"Work {work_id}",
            "doc_url": urls,
        },
        "sections": [],
    }


def series_payload(series_id: str, urls: list[str]) -> dict[str, object]:
    return {
        "header": {
            "schema": "series_record_v2",
            "version": f"before-{series_id}",
            "generated_at_utc": "2026-08-01T00:00:00Z",
            "series_id": series_id,
            "count": 2,
        },
        "series": {
            "series_id": series_id,
            "title": f"Series {series_id}",
            "doc_url": urls,
        },
    }


def test_refresh_reassigns_removes_and_adds_only_exact_affected_payloads(tmp_path: Path) -> None:
    old_url = "/library/?doc=d-old"
    new_url = "/analysis/?doc=d-new"
    work_one = tmp_path / "site/assets/works/index/00001.json"
    work_two = tmp_path / "site/assets/works/index/00002.json"
    unaffected = tmp_path / "site/assets/works/index/00003.json"
    series = tmp_path / "site/assets/series/index/009.json"
    write_json(work_one, work_payload("00001", [old_url]))
    write_json(work_two, work_payload("00002", []))
    write_json(unaffected, work_payload("00003", []))
    write_json(series, series_payload("009", []))
    unaffected_before = unaffected.read_bytes()

    plan = build_catalogue_document_url_refresh_plan(
        tmp_path,
        {
            "work": {"00002": [new_url]},
            "series": {"009": [old_url]},
        },
        generated_at_utc="2026-08-07T12:00:00Z",
    )
    result = apply_catalogue_document_url_refresh_plan(plan)

    assert result.affected_targets == (
        ("series", "009"),
        ("work", "00001"),
        ("work", "00002"),
    )
    assert set(result.written_paths) == {series, work_one, work_two}
    assert read_json(work_one)["work"]["doc_url"] == []  # type: ignore[index]
    assert read_json(work_two)["work"]["doc_url"] == [new_url]  # type: ignore[index]
    series_after = read_json(series)
    assert series_after["series"]["doc_url"] == [old_url]  # type: ignore[index]
    assert series_after["header"]["version"] == compute_payload_version(  # type: ignore[index]
        compact_json_object(
            {
                "series": series_after["series"],
                "content_html": None,
                "work_count": 2,
            }
        )
    )
    assert unaffected.read_bytes() == unaffected_before


def test_refresh_plan_is_empty_when_generated_payloads_match_projection(tmp_path: Path) -> None:
    url = "/library/?doc=d-current"
    path = tmp_path / "site/assets/works/index/00001.json"
    write_json(path, work_payload("00001", [url]))
    before = path.read_bytes()

    plan = build_catalogue_document_url_refresh_plan(
        tmp_path,
        {"work": {"00001": [url]}, "series": {}},
    )
    result = apply_catalogue_document_url_refresh_plan(plan)

    assert plan.affected_targets == ()
    assert result.written_paths == ()
    assert path.read_bytes() == before


def test_refresh_plan_rejects_missing_exact_generated_target_without_writes(tmp_path: Path) -> None:
    existing = tmp_path / "site/assets/works/index/00001.json"
    write_json(existing, work_payload("00001", []))
    before = existing.read_bytes()

    with pytest.raises(ValueError, match="generated Catalogue payload is missing"):
        build_catalogue_document_url_refresh_plan(
            tmp_path,
            {"work": {"99999": ["/library/?doc=d-missing"]}, "series": {}},
        )

    assert existing.read_bytes() == before


def test_refresh_atomic_failure_restores_all_previous_payloads(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = tmp_path / "site/assets/works/index/00001.json"
    second = tmp_path / "site/assets/series/index/009.json"
    write_json(first, work_payload("00001", ["/library/?doc=d-old"]))
    write_json(second, series_payload("009", []))
    first_before = first.read_bytes()
    second_before = second.read_bytes()
    plan = build_catalogue_document_url_refresh_plan(
        tmp_path,
        {
            "work": {},
            "series": {"009": ["/library/?doc=d-old"]},
        },
    )
    original_replace = transactions.os.replace
    calls = 0

    def fail_second_replace(source: str | Path, target: str | Path) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("simulated Catalogue follow-through failure")
        original_replace(source, target)

    monkeypatch.setattr(transactions.os, "replace", fail_second_replace)

    with pytest.raises(OSError, match="simulated Catalogue follow-through failure"):
        apply_catalogue_document_url_refresh_plan(plan)

    assert first.read_bytes() == first_before
    assert second.read_bytes() == second_before
