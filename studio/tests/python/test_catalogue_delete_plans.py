#!/usr/bin/env python3
"""Verify catalogue delete preview planners."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from catalogue import catalogue_delete_plans  # noqa: E402
from catalogue.catalogue_source import load_json_file, payload_for_map, work_details_payload_for_maps, write_work_detail_payloads  # noqa: E402


def assert_equal(actual, expected, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(f"{label}: expected truthy value, got {value!r}")


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_work_details_source(source_dir: Path, payload: dict) -> None:
    write_work_detail_payloads(
        source_dir,
        payload.get("work_detail_sections") or {},
        payload.get("work_details") or {},
    )


def read_work_details_source(source_dir: Path) -> dict:
    return load_json_file(source_dir / "work_details")


def write_source_fixture(source_dir: Path) -> None:
    write_json(
        source_dir / "works.json",
        payload_for_map(
            "works",
            {
                "00001": {
                    "work_id": "00001",
                    "status": "published",
                    "published_date": "2026-01-01",
                    "series_ids": ["009"],
                    "project_folder": "2026/alpha",
                    "project_filename": "alpha.jpg",
                    "title": "Alpha",
                    "year": "2026",
                    "year_display": "2026",
                },
                "00002": {
                    "work_id": "00002",
                    "status": "draft",
                    "series_ids": ["010"],
                    "project_folder": "2026/beta",
                    "project_filename": "beta.jpg",
                    "title": "Beta",
                    "year": "2026",
                    "year_display": "2026",
                },
            },
        ),
    )
    write_work_details_source(
        source_dir,
        work_details_payload_for_maps(
            {
                "00001-1": {
                    "section_id": "00001-1",
                    "work_id": "00001",
                    "section_title": "Details",
                    "details_subfolder": "details",
                }
            },
            {
                "00001-001": {
                    "detail_uid": "00001-001",
                    "work_id": "00001",
                    "detail_id": "001",
                    "section_id": "00001-1",
                    "project_filename": "alpha-detail.jpg",
                    "title": "Alpha detail",
                }
            },
        ),
    )
    write_json(
        source_dir / "series.json",
        payload_for_map(
            "series",
            {
                "009": {
                    "series_id": "009",
                    "title": "Published series",
                    "status": "published",
                    "year": "2026",
                    "year_display": "2026",
                    "primary_work_id": "00001",
                },
                "010": {
                    "series_id": "010",
                    "title": "Draft series",
                    "status": "draft",
                    "year": "2026",
                    "year_display": "2026",
                    "primary_work_id": "00002",
                },
            },
        ),
    )


def test_work_delete_preview_reports_dependents_and_primary_blocker() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source_dir = root / "studio/data/canonical/catalogue"
        write_source_fixture(source_dir)

        preview = catalogue_delete_plans.build_delete_preview(source_dir, "work", "00001", repo_root=root)

    assert_equal(preview["kind"], "work", "work preview kind")
    assert_equal(preview["affected"]["works"], ["00001"], "work affected works")
    assert_equal(preview["affected"]["work_details"], ["00001-001"], "work affected details")
    assert_equal(preview["affected"]["series"], ["009"], "work affected series")
    assert_equal(
        preview["blockers"],
        ["Work is primary_work_id for series: 009. Reassign those series before deleting the work."],
        "work delete blockers",
    )
    assert_true(preview["blocked"], "work delete blocked")


def test_detail_and_series_delete_preview_shapes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source_dir = root / "studio/data/canonical/catalogue"
        write_source_fixture(source_dir)

        detail = catalogue_delete_plans.build_delete_preview(source_dir, "work_detail", "00001-001", repo_root=root)
        section = catalogue_delete_plans.build_delete_preview(source_dir, "work_detail_section", "00001-1", repo_root=root)
        series = catalogue_delete_plans.build_delete_preview(source_dir, "series", "009", repo_root=root)

    assert_equal(detail["affected"], {"works": ["00001"], "series": [], "work_details": ["00001-001"]}, "detail affected")
    assert_equal(detail["summary"], "Delete work detail 00001-001 and remove 0 generated/media file(s).", "detail summary")
    assert_equal(section["affected"], {"works": ["00001"], "series": [], "work_details": ["00001-001"]}, "section affected")
    assert_equal(section["summary"], "Delete detail section 00001-1, 1 detail record(s), and remove 0 generated/media file(s).", "section summary")
    assert_equal(series["affected"], {"works": ["00001"], "series": ["009"], "work_details": []}, "series affected")
    assert_equal(series["summary"], "Delete series 009, remove it from 1 member work record(s), and remove 0 generated/media file(s).", "series summary")


def test_draft_series_primary_reference_is_cleared_for_work_delete_validation() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source_dir = root / "studio/data/canonical/catalogue"
        write_source_fixture(source_dir)

        preview = catalogue_delete_plans.build_delete_preview(source_dir, "work", "00002", repo_root=root)

    assert_equal(preview["blockers"], [], "draft primary blockers")
    assert_equal(preview["affected"]["series"], ["010"], "draft primary affected series")


def test_delete_apply_plan_builds_source_payloads_and_activity_affected() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source_dir = root / "studio/data/canonical/catalogue"
        write_source_fixture(source_dir)

        preview = catalogue_delete_plans.build_delete_preview(source_dir, "work", "00002", repo_root=root)
        plan = catalogue_delete_plans.build_delete_apply_plan(source_dir, root, "work", "00002", preview)

    assert_equal(sorted(path.name for path in plan.payloads), ["series.json", "work_details", "works.json"], "payload files")
    assert_equal(plan.payloads[(source_dir / "works.json").resolve()]["works"].get("00002"), None, "deleted work payload")
    assert_equal(plan.payloads[(source_dir / "series.json").resolve()]["series"]["010"].get("primary_work_id"), None, "draft primary cleared")
    assert_equal(plan.activity_affected["series"], ["010"], "activity affected series")


def test_section_delete_apply_plan_removes_section_and_details() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source_dir = root / "studio/data/canonical/catalogue"
        write_source_fixture(source_dir)
        payload = read_work_details_source(source_dir)
        payload["work_detail_sections"]["00001-2"] = {
            "section_id": "00001-2",
            "work_id": "00001",
            "section_title": "Versions",
            "details_subfolder": "versions",
        }
        payload["work_details"]["00001-002"] = {
            "detail_uid": "00001-002",
            "work_id": "00001",
            "detail_id": "002",
            "section_id": "00001-2",
            "project_filename": "alpha-version.jpg",
            "title": "Alpha version",
        }
        write_work_details_source(source_dir, payload)

        preview = catalogue_delete_plans.build_delete_preview(source_dir, "work_detail_section", "00001-1", repo_root=root)
        plan = catalogue_delete_plans.build_delete_apply_plan(source_dir, root, "work_detail_section", "00001-1", preview)

    details_payload = plan.payloads[(source_dir / "work_details").resolve()]
    assert_equal(sorted(details_payload["work_detail_sections"]), ["00001-2"], "remaining sections")
    assert_equal(sorted(details_payload["work_details"]), ["00001-002"], "remaining details")
    assert_equal(plan.activity_affected["work_details"], ["00001-001"], "section activity affected details")


def main() -> None:
    test_work_delete_preview_reports_dependents_and_primary_blocker()
    test_detail_and_series_delete_preview_shapes()
    test_draft_series_primary_reference_is_cleared_for_work_delete_validation()
    test_delete_apply_plan_builds_source_payloads_and_activity_affected()
    test_section_delete_apply_plan_removes_section_and_details()
    print("Catalogue delete plan tests OK")


if __name__ == "__main__":
    main()
