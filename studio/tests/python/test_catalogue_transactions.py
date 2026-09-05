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
