#!/usr/bin/env python3
"""Verify tag write-server backup and atomic JSON write helpers."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import tag_write_transactions as transactions  # noqa: E402


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_equal(actual, expected, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def test_single_file_write_creates_timestamped_backup() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        target = root / "tag_registry.json"
        backups_dir = root / "backups"
        write_json(target, {"tags": [{"tag_id": "subject:trees"}]})

        backup_path = transactions.atomic_write(target, {"tags": [{"tag_id": "subject:canopy"}]}, backups_dir)

        if backup_path is None:
            raise AssertionError("existing file write should return a backup path")
        assert_equal(read_json(target), {"tags": [{"tag_id": "subject:canopy"}]}, "updated target")
        assert_equal(read_json(backup_path), {"tags": [{"tag_id": "subject:trees"}]}, "backup payload")
        if not backup_path.name.startswith("tag_registry.json.bak-"):
            raise AssertionError(f"unexpected backup name: {backup_path.name}")


def test_single_file_write_without_existing_file_skips_backup() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        target = root / "tag_assignments.json"
        backups_dir = root / "backups"

        backup_path = transactions.atomic_write(target, {"series": {}}, backups_dir)

        assert_equal(backup_path, None, "new file backup path")
        assert_equal(read_json(target), {"series": {}}, "created target")
        assert_equal(list(backups_dir.iterdir()), [], "backup files")


def test_multi_file_write_creates_backups_with_shared_stamp() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        first = root / "tag_registry.json"
        second = root / "tag_aliases.json"
        backups_dir = root / "backups"
        write_json(first, {"before": 1})
        write_json(second, {"before": 2})

        backup_paths = transactions.atomic_write_many({first: {"after": 1}, second: {"after": 2}}, backups_dir)

        assert_equal(read_json(first), {"after": 1}, "first target")
        assert_equal(read_json(second), {"after": 2}, "second target")
        assert_equal(len(backup_paths), 2, "backup count")
        assert_equal(read_json(backups_dir / backup_paths[0].name), {"before": 1}, "first backup")
        assert_equal(read_json(backups_dir / backup_paths[1].name), {"before": 2}, "second backup")
        stamps = {path.name.split(".bak-", 1)[1] for path in backup_paths}
        assert_equal(len(stamps), 1, "shared backup stamp")


def test_multi_file_write_rolls_back_replaced_and_created_files_on_failure() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        existing = root / "tag_registry.json"
        created = root / "tag_aliases.json"
        backups_dir = root / "backups"
        write_json(existing, {"before": 1})
        original_replace = transactions.os.replace
        calls = 0

        def fail_second_replace(src: str | Path, dst: str | Path) -> None:
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("simulated replace failure")
            original_replace(src, dst)

        transactions.os.replace = fail_second_replace
        try:
            try:
                transactions.atomic_write_many({existing: {"after": 1}, created: {"after": 2}}, backups_dir)
            except OSError as exc:
                if "simulated replace failure" not in str(exc):
                    raise AssertionError(f"unexpected failure: {exc}") from exc
            else:
                raise AssertionError("expected simulated replace failure")
        finally:
            transactions.os.replace = original_replace

        assert_equal(read_json(existing), {"before": 1}, "restored existing target")
        if created.exists():
            raise AssertionError("created target should be removed during rollback")
        assert_equal(list(root.glob("*.tmp")), [], "temp cleanup")


def main() -> None:
    test_single_file_write_creates_timestamped_backup()
    test_single_file_write_without_existing_file_skips_backup()
    test_multi_file_write_creates_backups_with_shared_stamp()
    test_multi_file_write_rolls_back_replaced_and_created_files_on_failure()
    print("Tag write transaction tests OK")


if __name__ == "__main__":
    main()
