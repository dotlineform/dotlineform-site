#!/usr/bin/env python3
"""Focused checks for Studio backup retention planning."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "studio" / "studio_backup_retention.py"


def load_retention_module():
    spec = importlib.util.spec_from_file_location("studio_backup_retention", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load studio_backup_retention.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


retention = load_retention_module()


def make_repo() -> tempfile.TemporaryDirectory:
    temp_dir = tempfile.TemporaryDirectory()
    root = Path(temp_dir.name)
    (root / "_config.yml").write_text("title: Test\n", encoding="utf-8")
    return temp_dir


def write_file(path: Path, text: str = "backup") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def plan_paths(plan, repo_root: Path, bucket: str) -> list[str]:
    items = getattr(plan, bucket)
    return sorted(str(item.path.relative_to(repo_root)) for item in items)


def test_studio_backups_keep_newest_per_source_file_and_skip_unparseable() -> None:
    with make_repo() as temp:
        root = Path(temp)
        backup_root = root / "var/studio/backups"
        write_file(backup_root / "tag_registry.json.bak-20260501-100000")
        write_file(backup_root / "tag_registry.json.bak-20260502-100000")
        write_file(backup_root / "tag_registry.json.bak-20260503-100000")
        write_file(backup_root / "tag_aliases.json.bak-20260501-100000")
        write_file(backup_root / "tag_assignments.json.bak")

        plan = retention.build_retention_plan(root, studio_keep=2, catalogue_keep=30)

    assert plan_paths(plan, root, "keep") == [
        "var/studio/backups/tag_aliases.json.bak-20260501-100000",
        "var/studio/backups/tag_registry.json.bak-20260502-100000",
        "var/studio/backups/tag_registry.json.bak-20260503-100000",
    ]
    assert plan_paths(plan, root, "delete") == [
        "var/studio/backups/tag_registry.json.bak-20260501-100000",
    ]
    assert [str(path.relative_to(root)) for path in plan.skipped] == ["var/studio/backups/tag_assignments.json.bak"]


def test_catalogue_bundles_are_kept_when_any_contained_target_is_retained() -> None:
    with make_repo() as temp:
        root = Path(temp)
        backup_root = root / "var/studio/catalogue/backups"
        write_file(backup_root / "catalogue-save-20260501-100000-000001/works.json")
        write_file(backup_root / "catalogue-save-20260502-100000-000001/works.json")
        write_file(backup_root / "catalogue-save-20260503-100000-000001/work_details.json")
        transaction = backup_root / "catalogue-delete-work-20260501-110000-000001"
        write_file(transaction / "repo/assets/studio/data/catalogue/works.json")
        write_file(transaction / "repo/assets/data/search/catalogue/index.json")
        write_file(backup_root / "manual-review-bundle/works.json")

        plan = retention.build_retention_plan(root, studio_keep=20, catalogue_keep=2)

    assert plan_paths(plan, root, "keep") == [
        "var/studio/catalogue/backups/catalogue-delete-work-20260501-110000-000001",
        "var/studio/catalogue/backups/catalogue-save-20260502-100000-000001",
        "var/studio/catalogue/backups/catalogue-save-20260503-100000-000001",
    ]
    assert plan_paths(plan, root, "delete") == [
        "var/studio/catalogue/backups/catalogue-save-20260501-100000-000001",
    ]
    assert [str(path.relative_to(root)) for path in plan.skipped] == [
        "var/studio/catalogue/backups/manual-review-bundle"
    ]


def test_write_mode_deletes_only_pruned_items() -> None:
    with make_repo() as temp:
        root = Path(temp)
        backup_root = root / "var/studio/backups"
        old_backup = backup_root / "tag_registry.json.bak-20260501-100000"
        kept_backup = backup_root / "tag_registry.json.bak-20260502-100000"
        write_file(old_backup)
        write_file(kept_backup)

        exit_code = retention.main(["--repo-root", str(root), "--studio-keep", "1", "--catalogue-keep", "1", "--write", "--quiet"])

        assert exit_code == 0
        assert not old_backup.exists()
        assert kept_backup.exists()


if __name__ == "__main__":
    test_studio_backups_keep_newest_per_source_file_and_skip_unparseable()
    test_catalogue_bundles_are_kept_when_any_contained_target_is_retained()
    test_write_mode_deletes_only_pruned_items()
    print("studio backup retention checks passed")
