#!/usr/bin/env python3
"""Preview or apply the catalogue media/detail section source migration."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

_BOOTSTRAP_START = Path(__file__).resolve()
for _candidate in (_BOOTSTRAP_START.parent, *_BOOTSTRAP_START.parents):
    if (_candidate / "_config.yml").exists():
        if str(_candidate) not in sys.path:
            sys.path.insert(0, str(_candidate))
        break

from scripts.studio_python_paths import ensure_studio_python_paths

REPO_ROOT = ensure_studio_python_paths(__file__)
SCRIPTS_DIR = REPO_ROOT / "scripts"

try:
    from catalogue.catalogue_source import (
        DEFAULT_SOURCE_DIR,
        SOURCE_FILES,
        build_detail_section_id,
        detail_section_id_number,
        is_empty,
        load_json_file,
        normalize_text,
        slug_id,
    )
except ModuleNotFoundError:  # pragma: no cover - package import fallback
    from catalogue.catalogue_source import (
        DEFAULT_SOURCE_DIR,
        SOURCE_FILES,
        build_detail_section_id,
        detail_section_id_number,
        is_empty,
        load_json_file,
        normalize_text,
        slug_id,
    )

try:
    from display_paths import format_display_path
except ModuleNotFoundError:  # pragma: no cover - package import fallback
    from scripts.display_paths import format_display_path


DEFAULT_BACKUP_DIR = Path("var/studio/catalogue/backups")


@dataclass(frozen=True)
class SectionAssignment:
    work_id: str
    legacy_project_subfolder: str
    section_id: str
    detail_count: int = 0


@dataclass
class MigrationStats:
    total_records: int = 0
    changed_records: int = 0
    legacy_records: int = 0
    migrated_records: int = 0
    generated_sections: int = 0
    persisted_project_subfolder: int = 0
    persisted_details_subfolder: int = 0
    omitted_empty_project_subfolder: int = 0
    omitted_empty_details_subfolder: int = 0
    removed_project_subfolder: int = 0
    added_section_id: int = 0
    added_section_title: int = 0
    added_details_subfolder: int = 0
    duplicate_section_title_conflicts: int = 0
    work_records: int = 0
    persisted_work_project_subfolder: int = 0
    omitted_empty_work_project_subfolder: int = 0


@dataclass
class MigrationPlan:
    source_path: Path
    original_payload: dict[str, Any]
    migrated_payload: dict[str, Any]
    assignments: list[SectionAssignment]
    stats: MigrationStats
    errors: list[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return self.original_payload != self.migrated_payload


def stable_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def detail_sort_key(item: tuple[str, Mapping[str, Any]]) -> tuple[str, str, str]:
    key, record = item
    work_id = normalize_text(record.get("work_id"))
    detail_id = normalize_text(record.get("detail_id"))
    return (work_id, detail_id, key)


def next_section_id(work_id: str, existing_count: int) -> str:
    return build_detail_section_id(work_id, existing_count + 1)


def copied_record_with_new_fields(
    record: Mapping[str, Any],
    *,
    section_id: str,
    section_title: str,
    details_subfolder: str | None,
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    inserted = False
    for field_name, value in record.items():
        if field_name == "project_subfolder":
            out["section_id"] = section_id
            out["section_title"] = section_title
            if details_subfolder:
                out["details_subfolder"] = details_subfolder
            inserted = True
            continue
        if field_name in {"section_id", "section_title", "details_subfolder"}:
            continue
        out[field_name] = value
    if not inserted:
        out["section_id"] = section_id
        out["section_title"] = section_title
        if details_subfolder:
            out["details_subfolder"] = details_subfolder
    return out


def build_migration_plan(source_dir: Path) -> MigrationPlan:
    source_path = source_dir / SOURCE_FILES["work_details"]
    works_path = source_dir / SOURCE_FILES["works"]
    payload = load_json_file(source_path)
    works_payload = load_json_file(works_path)
    raw_records = payload.get("work_details")
    if not isinstance(raw_records, dict):
        return MigrationPlan(source_path, payload, payload, [], MigrationStats(), [f"{source_path}: missing work_details object"])
    raw_work_records = works_payload.get("works")

    errors: list[str] = []
    stats = MigrationStats(total_records=len(raw_records))
    if isinstance(raw_work_records, Mapping):
        stats.work_records = len(raw_work_records)
        for raw_work_record in raw_work_records.values():
            if not isinstance(raw_work_record, Mapping):
                continue
            if normalize_text(raw_work_record.get("project_subfolder")):
                stats.persisted_work_project_subfolder += 1
            elif "project_subfolder" in raw_work_record:
                stats.omitted_empty_work_project_subfolder += 1
    assignments_by_work: dict[str, dict[str, str]] = {}
    detail_counts_by_section: dict[tuple[str, str], int] = {}
    existing_section_count_by_work: dict[str, int] = {}
    for _key, raw_record in sorted(raw_records.items(), key=detail_sort_key):
        if not isinstance(raw_record, Mapping) or "project_subfolder" in raw_record:
            continue
        work_id = normalize_text(raw_record.get("work_id"))
        section_number = detail_section_id_number(work_id, raw_record.get("section_id"))
        if section_number is not None:
            existing_section_count_by_work[work_id] = max(
                existing_section_count_by_work.get(work_id, 0),
                section_number,
            )

    for key, raw_record in sorted(raw_records.items(), key=detail_sort_key):
        if not isinstance(raw_record, Mapping):
            errors.append(f"work_details {key}: record must be an object")
            continue
        try:
            work_id = slug_id(raw_record.get("work_id"))
        except ValueError as exc:
            errors.append(f"work_details {key}: invalid work_id ({exc})")
            continue

        if "project_subfolder" not in raw_record:
            stats.migrated_records += 1
            continue

        legacy_value = normalize_text(raw_record.get("project_subfolder"))
        if not legacy_value:
            errors.append(f"work_details {key}: legacy project_subfolder is empty; cannot derive required section_title")
            continue

        stats.legacy_records += 1
        work_assignments = assignments_by_work.setdefault(work_id, {})
        if legacy_value not in work_assignments:
            existing_count = existing_section_count_by_work.get(work_id, 0)
            work_assignments[legacy_value] = next_section_id(work_id, existing_count + len(work_assignments))
        detail_counts_by_section[(work_id, legacy_value)] = detail_counts_by_section.get((work_id, legacy_value), 0) + 1

        existing_details_subfolder = normalize_text(raw_record.get("details_subfolder"))
        if existing_details_subfolder and existing_details_subfolder != legacy_value:
            errors.append(
                f"work_details {key}: details_subfolder {existing_details_subfolder!r} conflicts with "
                f"legacy project_subfolder {legacy_value!r}"
            )
        existing_section_title = normalize_text(raw_record.get("section_title"))
        if existing_section_title and existing_section_title != legacy_value:
            errors.append(
                f"work_details {key}: section_title {existing_section_title!r} conflicts with "
                f"legacy project_subfolder {legacy_value!r}"
            )

    assignments: list[SectionAssignment] = []
    for work_id in sorted(assignments_by_work):
        for legacy_value, section_id in assignments_by_work[work_id].items():
            assignments.append(
                SectionAssignment(
                    work_id=work_id,
                    legacy_project_subfolder=legacy_value,
                    section_id=section_id,
                    detail_count=detail_counts_by_section.get((work_id, legacy_value), 0),
                )
            )
    stats.generated_sections = len(assignments)

    if errors:
        return MigrationPlan(source_path, payload, payload, assignments, stats, sorted(dict.fromkeys(errors)))

    migrated_records: dict[str, Any] = {}
    for key, raw_record in raw_records.items():
        if not isinstance(raw_record, Mapping):
            migrated_records[key] = raw_record
            continue
        if "project_subfolder" not in raw_record:
            migrated_records[key] = dict(raw_record)
            continue
        work_id = slug_id(raw_record.get("work_id"))
        legacy_value = normalize_text(raw_record.get("project_subfolder"))
        section_id = assignments_by_work[work_id][legacy_value]
        migrated_record = copied_record_with_new_fields(
            raw_record,
            section_id=section_id,
            section_title=legacy_value,
            details_subfolder=legacy_value if not is_empty(legacy_value) else None,
        )
        migrated_records[key] = migrated_record

        if migrated_record != dict(raw_record):
            stats.changed_records += 1
        stats.removed_project_subfolder += 1
        stats.added_section_id += 1
        stats.added_section_title += 1
        if legacy_value:
            stats.added_details_subfolder += 1
            stats.persisted_details_subfolder += 1
        else:
            stats.omitted_empty_details_subfolder += 1

    for raw_record in raw_records.values():
        if not isinstance(raw_record, Mapping):
            continue
        if normalize_text(raw_record.get("project_subfolder")):
            stats.persisted_project_subfolder += 1
        elif "project_subfolder" in raw_record:
            stats.omitted_empty_project_subfolder += 1

    migrated_payload = {
        "header": {
            **dict(payload.get("header") if isinstance(payload.get("header"), Mapping) else {}),
            "count": len(migrated_records),
        },
        "work_details": {key: migrated_records[key] for key in sorted(migrated_records)},
    }
    return MigrationPlan(source_path, payload, migrated_payload, assignments, stats, [])


def backup_path_for(source_path: Path, backup_dir: Path, repo_root: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    bundle_dir = backup_dir / f"catalogue-media-section-migration-{stamp}"
    rel_source_path = source_path.resolve().relative_to(repo_root.resolve())
    return bundle_dir / rel_source_path


def write_migration(plan: MigrationPlan, backup_dir: Path, repo_root: Path) -> Path | None:
    if not plan.changed:
        return None
    backup_path = backup_path_for(plan.source_path, backup_dir, repo_root)
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(plan.source_path, backup_path)
    temp_path = plan.source_path.with_suffix(plan.source_path.suffix + ".tmp")
    temp_path.write_text(stable_json(plan.migrated_payload), encoding="utf-8")
    temp_path.replace(plan.source_path)
    return backup_path


def print_plan(plan: MigrationPlan, *, write: bool, repo_root: Path, max_assignments: int) -> None:
    mode = "WRITE" if write else "DRY-RUN"
    stats = plan.stats
    print(f"Catalogue media section migration: {mode}")
    print(f"Source: {format_display_path(plan.source_path, repo_root=repo_root)}")
    print(f"Records: {stats.total_records}")
    print(f"Legacy records: {stats.legacy_records}")
    print(f"Already migrated records: {stats.migrated_records}")
    print(f"Changed records: {stats.changed_records}")
    print(f"Generated sections: {stats.generated_sections}")
    print(f"Duplicate section-title conflicts: {stats.duplicate_section_title_conflicts}")
    print("Field changes:")
    print(f"- remove project_subfolder: {stats.removed_project_subfolder}")
    print(f"- add section_id: {stats.added_section_id}")
    print(f"- add section_title: {stats.added_section_title}")
    print(f"- add details_subfolder: {stats.added_details_subfolder}")
    print("Persisted source metadata:")
    print(f"- work project_subfolder values already persisted: {stats.persisted_work_project_subfolder}")
    print(f"- empty work project_subfolder values omitted: {stats.omitted_empty_work_project_subfolder}")
    print(f"- legacy detail project_subfolder values read: {stats.persisted_project_subfolder}")
    print(f"- details_subfolder values to persist: {stats.persisted_details_subfolder}")
    print(f"- empty legacy detail project_subfolder values omitted: {stats.omitted_empty_project_subfolder}")
    print(f"- empty details_subfolder values omitted: {stats.omitted_empty_details_subfolder}")
    if plan.assignments:
        shown = plan.assignments[:max_assignments]
        print(f"Generated section ids (showing {len(shown)} of {len(plan.assignments)}):")
        for assignment in shown:
            print(
                f"- work {assignment.work_id}: {assignment.section_id} <- "
                f"{assignment.legacy_project_subfolder!r} ({assignment.detail_count} details)"
            )
        if len(plan.assignments) > len(shown):
            print(f"- ... {len(plan.assignments) - len(shown)} more")
    if plan.errors:
        print("Errors:")
        for error in plan.errors:
            print(f"- {error}")
    elif plan.changed:
        print("Result: changes pending." if not write else "Result: changes written.")
    else:
        print("Result: no changes.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Preview or apply the work-detail media section source migration.",
    )
    parser.add_argument("--source-dir", default=str(DEFAULT_SOURCE_DIR), help="Catalogue source JSON directory")
    parser.add_argument(
        "--backup-dir",
        default=str(DEFAULT_BACKUP_DIR),
        help="Backup root used only with --write",
    )
    parser.add_argument("--write", action="store_true", help="Write migrated source JSON. Default is dry-run.")
    parser.add_argument(
        "--max-assignments",
        type=int,
        default=40,
        help="Maximum generated section-id assignments to print",
    )
    args = parser.parse_args()

    repo_root = REPO_ROOT
    source_dir = Path(args.source_dir).expanduser()
    backup_dir = Path(args.backup_dir).expanduser()
    if not source_dir.is_absolute():
        source_dir = repo_root / source_dir
    if not backup_dir.is_absolute():
        backup_dir = repo_root / backup_dir

    plan = build_migration_plan(source_dir)
    print_plan(plan, write=args.write, repo_root=repo_root, max_assignments=max(args.max_assignments, 0))
    if plan.errors:
        return 1
    if args.write:
        backup_path = write_migration(plan, backup_dir, repo_root)
        if backup_path is not None:
            print(f"Backup: {format_display_path(backup_path, repo_root=repo_root)}")
            print(f"Wrote: {format_display_path(plan.source_path, repo_root=repo_root)}")
    else:
        print("Dry-run only. Pass --write to update source JSON.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
