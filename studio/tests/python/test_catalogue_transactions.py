#!/usr/bin/env python3
"""Verify catalogue transaction atomic-write helpers."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from catalogue import catalogue_transactions as transactions  # noqa: E402


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_transaction_snapshots_capture_existing_unique_paths() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "repo"
        repo_target = root / "assets/data/works_index.json"
        external_target = Path(tmp) / "external-source.md"
        write_text(repo_target, "repo")
        write_text(external_target, "external")

        snapshots = transactions.snapshot_transaction_paths([repo_target, external_target, repo_target])

        assert snapshots == {
            repo_target.resolve(): b"repo",
            external_target.resolve(): b"external",
        }


def test_restore_transaction_paths_restores_snapshots_and_removes_created_files() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        existing = root / "source.json"
        created = root / "created.json"
        write_text(existing, "before")
        snapshots = {existing.resolve(): b"before"}
        write_text(existing, "after")
        write_text(created, "created")

        transactions.restore_transaction_paths([existing, created], snapshots)

        assert existing.read_text(encoding="utf-8") == "before"
        assert not created.exists()


def test_atomic_write_many_rolls_back_replaced_files_on_failure() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
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
                transactions.atomic_write_many({first: {"after": 1}, second: {"after": 2}})
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
        target = root / "studio/data/canonical/catalogue/works.json"
        write_text(target, json.dumps({"works": {"00001": {"title": "Before"}}}) + "\n")

        result = transactions.execute_source_json_write(
            {target: {"works": {"00001": {"title": "After"}}}},
            dry_run=True,
            repo_root=root,
        )

        assert result.written_paths == []
        assert json.loads(target.read_text(encoding="utf-8")) == {"works": {"00001": {"title": "Before"}}}


def test_execute_source_json_write_reports_written_paths() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        target = root / "studio/data/canonical/catalogue/works.json"
        write_text(target, json.dumps({"works": {"00001": {"title": "Before"}}}) + "\n")

        result = transactions.execute_source_json_write(
            {target: {"works": {"00001": {"title": "After"}}}},
            dry_run=False,
            repo_root=root,
        )

        assert json.loads(target.read_text(encoding="utf-8")) == {"works": {"00001": {"title": "After"}}}
        assert result.written_paths == [target.resolve()]


def test_execute_source_json_write_rolls_back_replaced_files_on_failure() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
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
                dry_run=False,
                repo_root=root,
            )
        except ValueError as exc:
            assert "source write payloads are required" in str(exc)
        else:
            raise AssertionError("expected empty payload map to be rejected")


def test_catalogue_cleanup_transaction_writes_deletes_and_reports_written_paths() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source = root / "studio/data/canonical/catalogue/works.json"
        artifact = root / "assets/works/index/00001.json"
        search_index = root / "assets/data/search/catalogue/index.json"
        write_text(source, json.dumps({"before": 1}) + "\n")
        write_text(artifact, "generated")
        write_text(search_index, json.dumps({"search": []}) + "\n")
        calls: list[str] = []

        result = transactions.execute_catalogue_cleanup_transaction(
            repo_root=root,
            dry_run=False,
            allowed_write_paths={source},
            payloads={source: {"after": 1}},
            cleanup={"delete_paths": [artifact], "catalogue_search": True},
            rebuild_catalogue_search=lambda repo_root: calls.append(str(repo_root)) or {"ok": True, "exit_code": 0},
            refresh_lookup_payloads=lambda: calls.append("lookup"),
        )

        assert json.loads(source.read_text(encoding="utf-8")) == {"after": 1}
        assert not artifact.exists()
        assert result.payload["deleted_files"] == 1
        assert result.payload["updated_json_files"] == 1
        assert result.payload["catalogue_search_rebuilt"] is True
        assert calls == [str(root), "lookup"]
        assert [path.resolve() for path in result.written_paths] == [source.resolve()]


def test_catalogue_cleanup_transaction_restores_deleted_files_on_failure() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source = root / "studio/data/canonical/catalogue/works.json"
        artifact = root / "assets/works/index/00001.json"
        search_index = root / "assets/data/search/catalogue/index.json"
        write_text(source, json.dumps({"before": 1}) + "\n")
        write_text(artifact, "generated")
        write_text(search_index, json.dumps({"search": []}) + "\n")

        try:
            transactions.execute_catalogue_cleanup_transaction(
                repo_root=root,
                dry_run=False,
                allowed_write_paths={source},
                payloads={source: {"after": 1}},
                cleanup={"delete_paths": [artifact], "catalogue_search": True},
                rebuild_catalogue_search=lambda repo_root: (_ for _ in ()).throw(RuntimeError("search failed")),
            )
        except RuntimeError as exc:
            assert "search failed" in str(exc)
        else:
            raise AssertionError("expected transaction failure")

        assert json.loads(source.read_text(encoding="utf-8")) == {"before": 1}
        assert artifact.read_text(encoding="utf-8") == "generated"


def test_moment_cleanup_transaction_dry_run_reports_moment_keys() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        metadata = root / "studio/data/canonical/catalogue/moments.json"
        moments_index = root / "assets/data/moments_index.json"
        write_text(metadata, json.dumps({"moments": {"keys": {"title": "Keys"}}}) + "\n")
        write_text(moments_index, json.dumps({"moments": {"keys": {}}}) + "\n")

        result = transactions.execute_moment_cleanup_transaction(
            repo_root=root,
            dry_run=True,
            allowed_write_paths={metadata},
            metadata_path=metadata,
            metadata_payload={"moments": {}},
            cleanup={"delete_paths": []},
            moment_id="keys",
            rebuild_catalogue_search=lambda repo_root: {"ok": True, "exit_code": 0},
        )

        assert result.payload["moments_index_updated"] is False
        assert result.payload["would_update_moments_index"] is True
        assert result.payload["would_rebuild_catalogue_search"] is True
        assert result.written_paths == []


def test_atomic_write_text_no_backup_replaces_text_without_backup() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        target = root / "source/prose.md"

        transactions.atomic_write_text_no_backup(target, "new prose\n")

        assert target.read_text(encoding="utf-8") == "new prose\n"
        assert not list(target.parent.glob("*.tmp"))


if __name__ == "__main__":
    test_transaction_snapshots_capture_existing_unique_paths()
    test_restore_transaction_paths_restores_snapshots_and_removes_created_files()
    test_atomic_write_many_rolls_back_replaced_files_on_failure()
    test_execute_source_json_write_dry_run_suppresses_write()
    test_execute_source_json_write_reports_written_paths()
    test_execute_source_json_write_rolls_back_replaced_files_on_failure()
    test_execute_source_json_write_rejects_empty_payload_map()
    test_catalogue_cleanup_transaction_writes_deletes_and_reports_written_paths()
    test_catalogue_cleanup_transaction_restores_deleted_files_on_failure()
    test_moment_cleanup_transaction_dry_run_reports_moment_keys()
    test_atomic_write_text_no_backup_replaces_text_without_backup()
    print("catalogue transaction tests passed")
