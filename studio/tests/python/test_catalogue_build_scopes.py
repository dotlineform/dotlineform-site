#!/usr/bin/env python3
"""Verify scoped catalogue build planning helpers."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from catalogue import catalogue_build_scopes as scopes  # noqa: E402
from catalogue.catalogue_source import payload_for_map, work_details_payload_for_maps, write_work_detail_payloads  # noqa: E402


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_source_fixture(source_dir: Path) -> None:
    write_json(
        source_dir / "works.json",
        payload_for_map(
            "works",
            {
                "00001": {
                    "work_id": "00001",
                    "status": "published",
                    "series_ids": ["009"],
                    "project_folder": "2026/alpha",
                    "project_filename": "alpha.jpg",
                    "title": "Alpha",
                },
                "00002": {
                    "work_id": "00002",
                    "status": "published",
                    "series_ids": ["010"],
                    "project_folder": "2026/beta",
                    "project_filename": "beta.jpg",
                    "title": "Beta",
                },
                "00003": {
                    "work_id": "00003",
                    "status": "draft",
                    "series_ids": ["009"],
                    "title": "Draft",
                },
            },
        ),
    )
    write_work_detail_payloads(
        source_dir,
        {
            "00001-1": {
                "section_id": "00001-1",
                "work_id": "00001",
                "details_subfolder": "details",
                "section_title": "Details",
            }
        },
        work_details_payload_for_maps(
            {},
            {
                "00001-001": {
                    "detail_uid": "00001-001",
                    "work_id": "00001",
                    "detail_id": "001",
                    "section_id": "00001-1",
                    "details_subfolder": "details",
                    "project_filename": "alpha-detail.jpg",
                    "title": "Alpha detail",
                    "status": "published",
                }
            },
        )["work_details"],
    )
    write_json(
        source_dir / "series.json",
        payload_for_map(
            "series",
            {
                "009": {
                    "series_id": "009",
                    "title": "Alpha series",
                    "status": "published",
                    "primary_work_id": "00001",
                },
                "010": {
                    "series_id": "010",
                    "title": "Beta series",
                    "status": "published",
                    "primary_work_id": "00002",
                },
                "011": {
                    "series_id": "011",
                    "title": "Draft series",
                    "status": "draft",
                    "primary_work_id": "00003",
                },
            },
        ),
    )


def readiness_item(key: str) -> dict[str, Any]:
    return {"items": [{"key": key, "status": "ready"}]}


def test_work_scope_includes_extra_series_detail_readiness_and_stable_keys() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        source_dir = Path(tmp) / "studio/data/canonical/catalogue"
        write_source_fixture(source_dir)

        scope = scopes.build_scope_for_work(
            source_dir,
            "1",
            extra_series_ids=["10", "010"],
            detail_uid="00001-001",
            work_readiness_builder=lambda records, work_id, **kwargs: readiness_item(f"work:{work_id}"),
            detail_readiness_builder=lambda records, detail_uid, **kwargs: readiness_item(f"detail:{detail_uid}"),
        )

    assert list(scope.keys()) == [
        "work_ids",
        "series_ids",
        "current_series_ids",
        "extra_series_ids",
        "generate_only",
        "rebuild_search",
        "search_scope",
        "source_mode",
        "source_dir",
        "refresh_published",
        "summary",
        "detail_uid",
        "readiness",
    ]
    assert scope["work_ids"] == ["00001"]
    assert scope["series_ids"] == ["009", "010"]
    assert scope["current_series_ids"] == ["009"]
    assert scope["extra_series_ids"] == ["010"]
    assert scope["detail_uid"] == "00001-001"
    assert [item["key"] for item in scope["readiness"]["items"]] == ["work:00001", "detail:00001-001"]
    assert scope["generate_only"] == scopes.DEFAULT_ARTIFACTS


def test_work_scope_can_carry_transient_media_source() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        source_dir = Path(tmp) / "studio/data/canonical/catalogue"
        write_source_fixture(source_dir)
        seen_filenames: list[str] = []

        def readiness_item_from_records(records, work_id, **_kwargs):
            seen_filenames.append(records.works[work_id]["project_filename"])
            return readiness_item(f"work:{work_id}")

        scope = scopes.build_scope_for_work(
            source_dir,
            "00001",
            work_media_source={
                "project_folder": "2026/beta",
                "project_subfolder": "install",
                "project_filename": "replacement.jpg",
            },
            work_readiness_builder=readiness_item_from_records,
        )
        saved_payload = json.loads((source_dir / "works.json").read_text(encoding="utf-8"))

    assert seen_filenames == ["replacement.jpg"]
    assert scope["work_media_sources"]["00001"]["project_folder"] == "2026/beta"
    assert scope["work_media_sources"]["00001"]["project_subfolder"] == "install"
    assert scope["work_media_sources"]["00001"]["project_filename"] == "replacement.jpg"
    assert saved_payload["works"]["00001"]["project_filename"] == "alpha.jpg"


def test_series_scope_includes_extra_work_ids_and_stable_keys() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        source_dir = Path(tmp) / "studio/data/canonical/catalogue"
        write_source_fixture(source_dir)

        scope = scopes.build_scope_for_series(
            source_dir,
            "9",
            extra_work_ids=["2", "00002"],
            series_readiness_builder=lambda records, series_id, **kwargs: readiness_item(f"series:{series_id}"),
        )

    assert list(scope.keys()) == [
        "kind",
        "work_ids",
        "series_ids",
        "current_work_ids",
        "extra_work_ids",
        "generate_only",
        "rebuild_search",
        "search_scope",
        "source_mode",
        "source_dir",
        "refresh_published",
        "summary",
        "readiness",
    ]
    assert scope["kind"] == "series"
    assert scope["work_ids"] == ["00001", "00002"]
    assert scope["current_work_ids"] == ["00001"]
    assert scope["extra_work_ids"] == ["00002"]
    assert scope["series_ids"] == ["009"]
    assert scope["readiness"]["items"][0]["key"] == "series:009"


def test_invalid_series_scope_reports_build_preconditions() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        source_dir = Path(tmp) / "studio/data/canonical/catalogue"
        write_source_fixture(source_dir)

        try:
            scopes.build_scope_for_series(
                source_dir,
                "011",
                series_readiness_builder=lambda records, series_id, **kwargs: readiness_item("unused"),
            )
        except ValueError as exc:
            assert str(exc) == "series 011: status must be published for runtime build"
        else:
            raise AssertionError("expected draft series failure")

        payload = json.loads((source_dir / "series.json").read_text(encoding="utf-8"))
        payload["series"]["009"]["primary_work_id"] = "00002"
        write_json(source_dir / "series.json", payload)
        try:
            scopes.build_scope_for_work(
                source_dir,
                "00001",
                work_readiness_builder=lambda records, work_id, **kwargs: readiness_item("unused"),
            )
        except ValueError as exc:
            assert "series 009: primary_work_id '00002' is not in that work's series_ids" in str(exc)
        else:
            raise AssertionError("expected invalid primary-work failure")


def main() -> None:
    test_work_scope_includes_extra_series_detail_readiness_and_stable_keys()
    test_work_scope_can_carry_transient_media_source()
    test_series_scope_includes_extra_work_ids_and_stable_keys()
    test_invalid_series_scope_reports_build_preconditions()
    print("Catalogue build scope tests OK")


if __name__ == "__main__":
    main()
