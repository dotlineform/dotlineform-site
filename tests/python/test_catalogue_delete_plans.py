#!/usr/bin/env python3
"""Verify catalogue delete preview planners."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import catalogue_delete_plans  # noqa: E402
from catalogue_source import payload_for_map  # noqa: E402
from moment_sources import moment_metadata_payload  # noqa: E402


def assert_equal(actual, expected, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(f"{label}: expected truthy value, got {value!r}")


def write_json(path: Path, payload: dict) -> None:
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
    write_json(
        source_dir / "work_details.json",
        payload_for_map(
            "work_details",
            {
                "00001-001": {
                    "detail_uid": "00001-001",
                    "work_id": "00001",
                    "detail_id": "001",
                    "section_id": "00001-1",
                    "section_title": "Details",
                    "project_filename": "alpha-detail.jpg",
                    "title": "Alpha detail",
                    "status": "published",
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
    write_json(
        source_dir / "moments.json",
        moment_metadata_payload(
            {
                "keys": {
                    "moment_id": "keys",
                    "title": "Keys",
                    "status": "published",
                    "published_date": "2026-01-01",
                    "date": "2026-01-01",
                    "date_display": "January 2026",
                    "image_alt": "Keys",
                }
            }
        ),
    )


def test_work_delete_preview_reports_dependents_and_primary_blocker() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source_dir = root / "assets/studio/data/catalogue"
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


def test_detail_series_and_moment_delete_preview_shapes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source_dir = root / "assets/studio/data/catalogue"
        write_source_fixture(source_dir)

        detail = catalogue_delete_plans.build_delete_preview(source_dir, "work_detail", "00001-001", repo_root=root)
        series = catalogue_delete_plans.build_delete_preview(source_dir, "series", "009", repo_root=root)
        moment = catalogue_delete_plans.build_delete_preview(source_dir, "moment", "keys", repo_root=root)

    assert_equal(detail["affected"], {"works": ["00001"], "series": [], "work_details": ["00001-001"]}, "detail affected")
    assert_equal(detail["summary"], "Delete work detail 00001-001 and remove 0 generated/media file(s).", "detail summary")
    assert_equal(series["affected"], {"works": ["00001"], "series": ["009"], "work_details": []}, "series affected")
    assert_equal(series["summary"], "Delete series 009, remove it from 1 member work record(s), and remove 0 generated/media file(s).", "series summary")
    assert_equal(moment["affected"]["moments"], ["keys"], "moment affected")
    assert_equal(
        moment["summary"],
        "Delete moment keys, remove 0 generated/media file(s), update the moments index, and rebuild catalogue search.",
        "moment summary",
    )


def test_draft_series_primary_reference_is_cleared_for_work_delete_validation() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source_dir = root / "assets/studio/data/catalogue"
        write_source_fixture(source_dir)

        preview = catalogue_delete_plans.build_delete_preview(source_dir, "work", "00002", repo_root=root)

    assert_equal(preview["blockers"], [], "draft primary blockers")
    assert_equal(preview["affected"]["series"], ["010"], "draft primary affected series")


def test_delete_apply_plan_builds_source_payloads_and_activity_affected() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source_dir = root / "assets/studio/data/catalogue"
        write_source_fixture(source_dir)

        preview = catalogue_delete_plans.build_delete_preview(source_dir, "work", "00002", repo_root=root)
        plan = catalogue_delete_plans.build_delete_apply_plan(source_dir, root, "work", "00002", preview)

    assert_equal(plan.backup_label, "catalogue-delete-work", "backup label")
    assert_equal(sorted(path.name for path in plan.payloads), ["series.json", "work_details.json", "works.json"], "payload files")
    assert_equal(plan.payloads[(source_dir / "works.json").resolve()]["works"].get("00002"), None, "deleted work payload")
    assert_equal(plan.payloads[(source_dir / "series.json").resolve()]["series"]["010"].get("primary_work_id"), None, "draft primary cleared")
    assert_equal(plan.activity_affected["series"], ["010"], "activity affected series")


def main() -> None:
    test_work_delete_preview_reports_dependents_and_primary_blocker()
    test_detail_series_and_moment_delete_preview_shapes()
    test_draft_series_primary_reference_is_cleared_for_work_delete_validation()
    test_delete_apply_plan_builds_source_payloads_and_activity_affected()
    print("Catalogue delete plan tests OK")


if __name__ == "__main__":
    main()
