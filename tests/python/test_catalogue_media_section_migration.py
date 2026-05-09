#!/usr/bin/env python3
"""Focused checks for the catalogue media section migration planner."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from catalogue.catalogue_source import DETAIL_FIELDS, WORK_FIELDS, normalize_source_record  # noqa: E402
from catalogue.migrate_catalogue_media_sections import build_migration_plan, stable_json, write_migration  # noqa: E402


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def minimal_source(source_dir: Path) -> None:
    write_json(
        source_dir / "works.json",
        {
            "header": {"schema": "catalogue_source_works_v1", "count": 2},
            "works": {
                "00001": {
                    "work_id": "00001",
                    "project_folder": "one",
                    "project_subfolder": "source",
                    "project_filename": "one.jpg",
                },
                "00002": {
                    "work_id": "00002",
                    "project_folder": "two",
                    "project_filename": "two.jpg",
                },
            },
        },
    )
    write_json(
        source_dir / "work_details.json",
        {
            "header": {"schema": "catalogue_source_work_details_v1", "count": 4},
            "work_details": {
                "00001-001": {
                    "detail_uid": "00001-001",
                    "work_id": "00001",
                    "detail_id": "001",
                    "project_subfolder": "details",
                    "project_filename": "one.jpg",
                },
                "00001-002": {
                    "detail_uid": "00001-002",
                    "work_id": "00001",
                    "detail_id": "002",
                    "project_subfolder": "details",
                    "project_filename": "two.jpg",
                },
                "00001-003": {
                    "detail_uid": "00001-003",
                    "work_id": "00001",
                    "detail_id": "003",
                    "project_subfolder": "pages",
                    "project_filename": "three.jpg",
                },
                "00002-001": {
                    "detail_uid": "00002-001",
                    "work_id": "00002",
                    "detail_id": "001",
                    "project_subfolder": "source",
                    "project_filename": "four.jpg",
                },
            },
        },
    )


def assert_planner_assigns_stable_section_ids() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        source_dir = Path(tmp) / "catalogue"
        minimal_source(source_dir)
        plan = build_migration_plan(source_dir)
        assert not plan.errors, plan.errors
        assert plan.changed
        assert plan.stats.changed_records == 4
        assert plan.stats.generated_sections == 3
        assert plan.stats.persisted_work_project_subfolder == 1
        records = plan.migrated_payload["work_details"]
        assert records["00001-001"]["section_id"] == "00001-1"
        assert records["00001-002"]["section_id"] == "00001-1"
        assert records["00001-003"]["section_id"] == "00001-2"
        assert records["00002-001"]["section_id"] == "00002-1"
        assert records["00001-001"]["section_title"] == "details"
        assert records["00001-001"]["details_subfolder"] == "details"
        assert "project_subfolder" not in records["00001-001"]


def assert_write_mode_creates_backup_and_is_idempotent() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo_root = Path(tmp)
        source_dir = repo_root / "assets/studio/data/catalogue"
        backup_dir = repo_root / "var/studio/catalogue/backups"
        minimal_source(source_dir)
        plan = build_migration_plan(source_dir)
        backup_path = write_migration(plan, backup_dir, repo_root)
        assert backup_path is not None
        assert backup_path.exists()
        written_payload = json.loads((source_dir / "work_details.json").read_text(encoding="utf-8"))
        assert stable_json(written_payload) == stable_json(plan.migrated_payload)
        second_plan = build_migration_plan(source_dir)
        assert not second_plan.errors, second_plan.errors
        assert not second_plan.changed


def assert_optional_subfolders_are_omitted_when_empty() -> None:
    work_record = normalize_source_record(
        {
            "work_id": "00001",
            "project_folder": "one",
            "project_subfolder": "",
            "project_filename": "one.jpg",
        },
        WORK_FIELDS,
    )
    detail_record = normalize_source_record(
        {
            "detail_uid": "00001-001",
            "work_id": "00001",
            "detail_id": "001",
            "details_subfolder": "",
            "section_id": "00001-1",
            "section_title": "details",
            "sort_order": "",
            "project_filename": "one.jpg",
        },
        DETAIL_FIELDS,
    )
    assert "project_subfolder" not in work_record
    assert "details_subfolder" not in detail_record
    assert "sort_order" not in detail_record


def main() -> int:
    assert_planner_assigns_stable_section_ids()
    assert_write_mode_creates_backup_and_is_idempotent()
    assert_optional_subfolders_are_omitted_when_empty()
    print("catalogue media section migration checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
