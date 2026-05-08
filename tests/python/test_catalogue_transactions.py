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


def test_execute_source_json_write_dry_run_suppresses_write() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        target = root / "assets/studio/data/catalogue/works.json"
        backups_dir = root / "var/studio/catalogue/backups"
        write_text(target, json.dumps({"works": {"00001": {"title": "Before"}}}) + "\n")

        result = transactions.execute_source_json_write(
            {target: {"works": {"00001": {"title": "After"}}}},
            backups_dir,
            dry_run=True,
            repo_root=root,
        )

        assert result.backup_paths == []
        assert result.backups == []
        assert json.loads(target.read_text(encoding="utf-8")) == {"works": {"00001": {"title": "Before"}}}
        assert not backups_dir.exists()


def test_execute_source_json_write_reports_relative_backup_paths() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        target = root / "assets/studio/data/catalogue/works.json"
        backups_dir = root / "var/studio/catalogue/backups"
        write_text(target, json.dumps({"works": {"00001": {"title": "Before"}}}) + "\n")

        result = transactions.execute_source_json_write(
            {target: {"works": {"00001": {"title": "After"}}}},
            backups_dir,
            dry_run=False,
            repo_root=root,
        )

        assert json.loads(target.read_text(encoding="utf-8")) == {"works": {"00001": {"title": "After"}}}
        assert len(result.backup_paths) == 1
        assert len(result.backups) == 1
        backup_rel_path = result.backups[0]
        assert backup_rel_path.startswith("var/studio/catalogue/backups/catalogue-save-")
        assert backup_rel_path.endswith("/works.json")
        assert json.loads((root / backup_rel_path).read_text(encoding="utf-8")) == {"works": {"00001": {"title": "Before"}}}


def test_execute_source_json_write_rolls_back_replaced_files_on_failure() -> None:
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
                transactions.execute_source_json_write(
                    {first: {"after": 1}, second: {"after": 2}},
                    backups_dir,
                    dry_run=False,
                    repo_root=root,
                )
            except OSError as exc:
                assert "simulated replace failure" in str(exc)
            else:
                raise AssertionError("expected simulated replace failure")
        finally:
            transactions.os.replace = original_replace

        assert json.loads(first.read_text(encoding="utf-8")) == {"before": 1}
        assert json.loads(second.read_text(encoding="utf-8")) == {"before": 2}
        assert not list(root.glob("*.tmp"))


def test_execute_source_json_write_rejects_empty_payload_map() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        try:
            transactions.execute_source_json_write(
                {},
                root / "backups",
                dry_run=False,
                repo_root=root,
            )
        except ValueError as exc:
            assert "source write payloads are required" in str(exc)
        else:
            raise AssertionError("expected empty payload map to be rejected")


def test_atomic_write_text_no_backup_replaces_text_without_backup() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        target = root / "source/prose.md"

        transactions.atomic_write_text_no_backup(target, "new prose\n")

        assert target.read_text(encoding="utf-8") == "new prose\n"
        assert not list(target.parent.glob("*.tmp"))


if __name__ == "__main__":
    test_transaction_backups_preserve_repo_and_external_layout()
    test_restore_transaction_paths_restores_backups_and_removes_created_files()
    test_atomic_write_many_rolls_back_replaced_files_on_failure()
    test_execute_source_json_write_dry_run_suppresses_write()
    test_execute_source_json_write_reports_relative_backup_paths()
    test_execute_source_json_write_rolls_back_replaced_files_on_failure()
    test_execute_source_json_write_rejects_empty_payload_map()
    test_atomic_write_text_no_backup_replaces_text_without_backup()
    print("catalogue transaction tests passed")
