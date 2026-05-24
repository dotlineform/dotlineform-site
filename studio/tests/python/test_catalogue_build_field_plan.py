#!/usr/bin/env python3
"""Verify field-aware scoped catalogue build planning helpers."""

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

from catalogue import catalogue_build_field_plan as field_plan  # noqa: E402
from catalogue.catalogue_source import payload_for_map  # noqa: E402


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
                }
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
                    "title": "Alpha series",
                    "status": "published",
                    "primary_work_id": "00001",
                    "sort_fields": "title",
                }
            },
        ),
    )


def work_scope(source_dir: Path) -> dict[str, Any]:
    return {
        "work_ids": ["00001"],
        "series_ids": ["009"],
        "generate_only": ["work-pages", "work-json"],
        "rebuild_search": True,
        "source_dir": str(source_dir),
        "summary": "Build works [00001].",
    }


def test_parse_csv_tokens_dedupes_append_values() -> None:
    assert field_plan.parse_csv_tokens(["title, year", "downloads", "title", ""]) == ["title", "year", "downloads"]


def test_infer_record_family_for_scope() -> None:
    assert field_plan.infer_record_family_for_scope({"kind": "moment", "moment_ids": ["keys"]}) == "moment"
    assert field_plan.infer_record_family_for_scope({"work_ids": ["00001"], "detail_uid": "00001-001"}) == "work_detail"
    assert field_plan.infer_record_family_for_scope({"series_ids": ["009"], "work_ids": []}) == "series"
    assert field_plan.infer_record_family_for_scope({"work_ids": ["00001"], "series_ids": ["009"]}) == "work"
    assert field_plan.infer_record_family_for_scope({}, "work-detail") == "work_detail"
    try:
        field_plan.infer_record_family_for_scope({}, "invalid")
    except ValueError as exc:
        assert str(exc) == "--record-family must be work, work_detail, series, or moment"
    else:
        raise AssertionError("expected invalid record-family failure")


def test_empty_changed_fields_return_no_plan() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        source_dir = Path(tmp) / "studio/data/canonical/catalogue"
        write_source_fixture(source_dir)

        plan = field_plan.build_field_plan_for_scope(REPO_ROOT, source_dir, work_scope(source_dir), changed_fields=["", " "])

    assert plan == {}


def test_work_public_metadata_reduces_to_focused_work_json() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        source_dir = Path(tmp) / "studio/data/canonical/catalogue"
        write_source_fixture(source_dir)
        scope = work_scope(source_dir)

        plan = field_plan.build_field_plan_for_scope(REPO_ROOT, source_dir, scope, changed_fields=["downloads"])
        field_plan.apply_field_build_plan_to_scope(scope, plan)

    assert plan["mode"] == "field-aware"
    assert plan["rule_ids"] == ["work_local_public_metadata"]
    assert scope["generate_only"] == ["work-json"]
    assert scope["rebuild_search"] is False
    assert scope["generate_local_media"] is False
    assert "generate [work-json], search no, local media no" in scope["summary"]
    assert field_plan.field_plan_explanation_lines(plan) == [
        "source-json, studio-lookup, work-json: downloads -> These fields are focused work metadata and should not select series artifacts or broad aggregate indexes unless a future public artifact starts serializing them."
    ]


def test_work_media_source_reduces_to_local_media_only() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        source_dir = Path(tmp) / "studio/data/canonical/catalogue"
        write_source_fixture(source_dir)
        scope = work_scope(source_dir)

        plan = field_plan.build_field_plan_for_scope(REPO_ROOT, source_dir, scope, changed_fields=["project_filename"])
        field_plan.apply_field_build_plan_to_scope(scope, plan)

    assert plan["rule_ids"] == ["work_media_source"]
    assert scope["generate_only"] == []
    assert scope["rebuild_search"] is False
    assert scope["generate_local_media"] is True


def test_detail_series_and_moment_field_plans_use_inferred_families() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        source_dir = Path(tmp) / "studio/data/canonical/catalogue"
        write_source_fixture(source_dir)

        detail_plan = field_plan.build_field_plan_for_scope(
            REPO_ROOT,
            source_dir,
            {"work_ids": ["00001"], "series_ids": ["009"], "detail_uid": "00001-001"},
            changed_fields=["title"],
        )
        series_plan = field_plan.build_field_plan_for_scope(
            REPO_ROOT,
            source_dir,
            {"kind": "series", "work_ids": [], "series_ids": ["009"]},
            changed_fields=["title"],
        )
        moment_plan = field_plan.build_field_plan_for_scope(
            REPO_ROOT,
            source_dir,
            {"kind": "moment", "moment_ids": ["keys"]},
            changed_fields=["source_image_file"],
        )

    assert detail_plan["rule_ids"] == ["work_detail_public_metadata"]
    assert detail_plan["generate_only"] == ["work-json"]
    assert detail_plan["rebuild_search"] is False
    assert detail_plan["generate_local_media"] is False
    assert series_plan["rule_ids"] == ["series_display_search"]
    assert series_plan["generate_only"] == ["series-pages", "series-index-json", "recent-index-json"]
    assert series_plan["rebuild_search"] is True
    assert series_plan["generate_local_media"] is False
    assert moment_plan["rule_ids"] == ["moment_media_source"]
    assert moment_plan["generate_only"] == []
    assert moment_plan["rebuild_search"] is False
    assert moment_plan["generate_local_media"] is True


def main() -> None:
    test_parse_csv_tokens_dedupes_append_values()
    test_infer_record_family_for_scope()
    test_empty_changed_fields_return_no_plan()
    test_work_public_metadata_reduces_to_focused_work_json()
    test_work_media_source_reduces_to_local_media_only()
    test_detail_series_and_moment_field_plans_use_inferred_families()
    print("Catalogue build field-plan tests OK")


if __name__ == "__main__":
    main()
