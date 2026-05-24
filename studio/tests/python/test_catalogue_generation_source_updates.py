#!/usr/bin/env python3
"""Verify generated catalogue source-update planners."""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from catalogue import catalogue_generation_source_updates as updates  # noqa: E402


def test_draft_work_publication_update_includes_recent_transition() -> None:
    plan = updates.plan_work_publication_update(
        work_id="00042",
        status="draft",
        today=dt.date(2026, 5, 9),
        work_meta={"title": "Threshold", "series_ids": ["009"]},
        series_title_by_id={"009": "Sequence"},
    )

    assert plan.updates == {"status": "published", "published_date": "2026-05-09"}
    assert plan.transition == {
        "work_id": "00042",
        "title": "Threshold",
        "primary_series_id": "009",
        "series_title": "Sequence",
        "published_date": "2026-05-09",
    }


def test_published_refresh_and_force_are_actionable_without_mutation_plan() -> None:
    assert updates.is_actionable_status("published", refresh_published=True) is True

    plan = updates.plan_work_publication_update(
        work_id="00042",
        status="published",
        today=dt.date(2026, 5, 9),
        work_meta={"title": "Threshold", "series_ids": ["009"]},
        series_title_by_id={"009": "Sequence"},
    )

    assert plan.updates == {}
    assert plan.transition is None


def test_detail_publication_update_sets_status_and_date() -> None:
    plan = updates.plan_detail_publication_update(
        detail_uid="00042-001",
        status="draft",
        today=dt.date(2026, 5, 9),
    )

    assert plan.updates == {"status": "published", "published_date": "2026-05-09"}


def test_dimension_update_suppresses_unchanged_values() -> None:
    plan = updates.plan_dimension_update(
        record_kind=updates.WORK_RECORD,
        record_id="00042",
        current_width_px="1200",
        current_height_px=800,
        source_width_px=1200,
        source_height_px=800,
    )

    assert plan.width_px == 1200
    assert plan.height_px == 800
    assert plan.updates == {}


def test_dimension_update_reports_changed_values_without_mutating_source_record() -> None:
    source_record = {"width_px": 100, "height_px": 200}

    plan = updates.plan_dimension_update(
        record_kind=updates.WORK_RECORD,
        record_id="00042",
        current_width_px=source_record["width_px"],
        current_height_px=source_record["height_px"],
        source_width_px=300,
        source_height_px=200,
    )

    assert plan.updates == {"width_px": 300}
    assert source_record == {"width_px": 100, "height_px": 200}


def test_work_source_path_warning_is_structured_when_project_folder_is_missing() -> None:
    plan = updates.plan_work_image_source_path(
        work_id="00042",
        project_filename="main.jpg",
        project_folder=None,
        project_subfolder=None,
        projects_root=Path("/projects"),
        has_project_folder_column=True,
    )

    assert plan.source_path is None
    assert plan.warning is not None
    assert plan.warning.code == updates.MISSING_PROJECT_FOLDER
    assert plan.warning.record_kind == updates.WORK_RECORD
    assert plan.warning.record_id == "00042"
    assert plan.warning.filename == "main.jpg"


def test_detail_source_path_resolution_uses_parent_work_folder() -> None:
    plan = updates.plan_detail_image_source_path(
        detail_uid="00042-001",
        project_filename="detail.jpg",
        work_project_folder="2026/work",
        details_subfolder="details",
        projects_root=Path("/projects"),
        has_project_folder_column=True,
    )

    assert plan.source_path == Path("/projects/2026/work/details/detail.jpg")
    assert plan.warning is None


def main() -> None:
    test_draft_work_publication_update_includes_recent_transition()
    test_published_refresh_and_force_are_actionable_without_mutation_plan()
    test_detail_publication_update_sets_status_and_date()
    test_dimension_update_suppresses_unchanged_values()
    test_dimension_update_reports_changed_values_without_mutating_source_record()
    test_work_source_path_warning_is_structured_when_project_folder_is_missing()
    test_detail_source_path_resolution_uses_parent_work_folder()
    print("Catalogue generation source update tests OK")


if __name__ == "__main__":
    main()
