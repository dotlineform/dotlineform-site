#!/usr/bin/env python3
"""Verify catalogue transaction backup and atomic-write helpers."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import catalogue_transactions as transactions  # noqa: E402


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_transaction_backups_preserve_repo_and_external_layout() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "repo"
        backup_root = root / "var/studio/catalogue/backups/catalogue-delete-work-test"
        repo_target = root / "assets/data/works_index.json"
        external_target = Path(tmp) / "external-source.md"
        write_text(repo_target, "repo")
        write_text(external_target, "external")

        backups = transactions.backup_transaction_paths([repo_target, external_target, repo_target], backup_root, root)

        assert sorted(str(path.relative_to(backup_root)) for path in backups.values()) == [
            "external/external-source.md",
            "repo/assets/data/works_index.json",
        ]
        assert (backup_root / "repo/assets/data/works_index.json").read_text(encoding="utf-8") == "repo"
        assert (backup_root / "external/external-source.md").read_text(encoding="utf-8") == "external"


def test_restore_transaction_paths_restores_backups_and_removes_created_files() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        existing = root / "source.json"
        created = root / "created.json"
        backup = root / "backup/source.json"
        write_text(existing, "before")
        write_text(backup, "before")
        write_text(existing, "after")
        write_text(created, "created")

        transactions.restore_transaction_paths([existing, created], {existing.resolve(): backup})

        assert existing.read_text(encoding="utf-8") == "before"
        assert not created.exists()


def test_atomic_write_many_rolls_back_replaced_files_on_failure() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        backups_dir = root / "backups"
        first = root / "first.json"
        second = root / "second.json"
        write_text(first, json.dumps({"before": 1}) + "\n")
        write_text(second, json.dumps({"before": 2}) + "\n")
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
                transactions.atomic_write_many({first: {"after": 1}, second: {"after": 2}}, backups_dir)
            except OSError as exc:
                assert "simulated replace failure" in str(exc)
            else:
                raise AssertionError("expected simulated replace failure")
        finally:
            transactions.os.replace = original_replace

        assert json.loads(first.read_text(encoding="utf-8")) == {"before": 1}
        assert json.loads(second.read_text(encoding="utf-8")) == {"before": 2}
        assert not list(root.glob("*.tmp"))


if __name__ == "__main__":
    test_transaction_backups_preserve_repo_and_external_layout()
    test_restore_transaction_paths_restores_backups_and_removes_created_files()
    test_atomic_write_many_rolls_back_replaced_files_on_failure()
    print("catalogue transaction tests passed")
