#!/usr/bin/env python3
"""Verify Studio tag API atomic JSON write helpers."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
STUDIO_SERVICES_DIR = REPO_ROOT / "studio" / "services"
for path in (STUDIO_SERVICES_DIR,):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from tags import tag_write_transactions as transactions  # noqa: E402


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_equal(actual, expected, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def test_single_file_write_replaces_existing_file() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        target = root / "tag_registry.json"
        write_json(target, {"tags": [{"tag_id": "trees"}]})

        transactions.atomic_write(target, {"tags": [{"tag_id": "canopy"}]})

        assert_equal(read_json(target), {"tags": [{"tag_id": "canopy"}]}, "updated target")


def test_single_file_write_creates_new_file() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        target = root / "tag_assignments.json"

        transactions.atomic_write(target, {"series": {}})

        assert_equal(read_json(target), {"series": {}}, "created target")


def test_multi_file_write_replaces_targets() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        first = root / "tag_registry.json"
        second = root / "tag_aliases.json"
        write_json(first, {"before": 1})
        write_json(second, {"before": 2})

        transactions.atomic_write_many({first: {"after": 1}, second: {"after": 2}})

        assert_equal(read_json(first), {"after": 1}, "first target")
        assert_equal(read_json(second), {"after": 2}, "second target")


def test_multi_file_byte_write_preserves_exact_payloads() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        first = root / "tag_registry.json"
        second = root / "document.md"

        transactions.atomic_write_bytes_many(
            {
                first: b'{"tag_registry_version":"tag_registry_v6"}\n',
                second: b"---\r\ntag_id: trees\r\n---\r\n",
            }
        )

        assert_equal(
            first.read_bytes(),
            b'{"tag_registry_version":"tag_registry_v6"}\n',
            "exact registry bytes",
        )
        assert_equal(
            second.read_bytes(),
            b"---\r\ntag_id: trees\r\n---\r\n",
            "exact source bytes",
        )


def test_multi_file_write_rolls_back_replaced_and_created_files_on_failure() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        existing = root / "tag_registry.json"
        created = root / "tag_aliases.json"
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
                transactions.atomic_write_many({existing: {"after": 1}, created: {"after": 2}})
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
    test_single_file_write_replaces_existing_file()
    test_single_file_write_creates_new_file()
    test_multi_file_write_replaces_targets()
    test_multi_file_byte_write_preserves_exact_payloads()
    test_multi_file_write_rolls_back_replaced_and_created_files_on_failure()
    print("Tag write transaction tests OK")


if __name__ == "__main__":
    main()
