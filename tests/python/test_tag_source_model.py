#!/usr/bin/env python3
"""Verify tag source model validation and loading helpers."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from analytics import tag_source_model as source  # noqa: E402


def assert_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def assert_raises_contains(fn: Callable[[], Any], expected: str, label: str) -> None:
    try:
        fn()
    except ValueError as exc:
        if expected not in str(exc):
            raise AssertionError(f"{label}: expected error containing {expected!r}, got {str(exc)!r}") from exc
        return
    raise AssertionError(f"{label}: expected ValueError")


def test_tag_id_and_alias_key_validation() -> None:
    assert_equal(source.sanitize_tag_id(" Subject:Trees "), "subject:trees", "tag id normalized")
    assert_raises_contains(lambda: source.sanitize_tag_id("trees"), "must match <group>:<slug>", "tag id missing group")
    assert_raises_contains(lambda: source.sanitize_tag_id("subject:bad_slug"), "must match <group>:<slug>", "tag id unsafe slug")

    assert_equal(source.sanitize_alias_key(" Foliage ", 0), "foliage", "alias key normalized")
    assert_raises_contains(lambda: source.sanitize_alias_key("", 1), "must not be empty", "empty alias")
    assert_raises_contains(lambda: source.sanitize_alias_key("bad alias", 2), "must be slug-safe", "unsafe alias")


def test_group_and_manual_weight_validation() -> None:
    registry = {"policy": {"allowed_groups": ["Subject", "theme", "theme", ""]}}
    groups = source.extract_allowed_groups(registry)
    assert_equal(groups, ["subject", "theme"], "allowed groups normalized")
    assert_equal(source.sanitize_group(" Subject ", groups), "subject", "group normalized")
    assert_raises_contains(lambda: source.sanitize_group("domain", groups), "must be one of", "invalid group")

    assert_equal(source.sanitize_manual_weight("0.6", "w_manual"), 0.6, "manual weight normalized")
    assert_equal(source.sanitize_manual_weight(0.7, "w_manual", strict=False), 0.6, "manual weight rounded")
    assert_raises_contains(lambda: source.sanitize_manual_weight(None, "w_manual"), "is required", "missing weight")
    assert_raises_contains(lambda: source.sanitize_manual_weight(0.4, "w_manual"), "must be one of", "invalid weight")


def test_assignment_tag_normalization() -> None:
    raw = [
        {"tag_id": "Subject:Trees", "w_manual": "0.9", "alias": "Foliage"},
        {"tag_id": "subject:trees", "w_manual": "0.3"},
        {"tag_id": "theme:growth", "w_manual": 0.6},
    ]
    assert_equal(
        source.sanitize_assignment_tags(raw, "tags"),
        [
            {"tag_id": "subject:trees", "w_manual": 0.9, "alias": "foliage"},
            {"tag_id": "theme:growth", "w_manual": 0.6},
        ],
        "assignment tags normalize and de-duplicate",
    )
    assert_raises_contains(lambda: source.sanitize_assignment_tags(["subject:trees"], "tags"), "must be an object", "strict strings")
    assert_equal(
        source.sanitize_assignment_tags(["subject:trees", "bad"], "tags", strict=False),
        [{"tag_id": "subject:trees", "w_manual": source.DEFAULT_TAG_WEIGHT}],
        "non-strict assignment rows skip invalid entries",
    )


def test_import_assignment_rows_and_filename_sanitization() -> None:
    session = source.sanitize_import_assignments_session(
        {
            "version": "tag_assignments_export_v1",
            "series": {
                " Series-1 ": {
                    "base_row_snapshot": None,
                    "staged_row": {
                        "tags": [{"tag_id": "subject:trees", "w_manual": 0.6}],
                        "works": {"00002": {"tags": [{"tag_id": "theme:growth", "w_manual": 0.3}]}},
                    },
                }
            },
        }
    )
    assert_equal(sorted(session["series"].keys()), ["series-1"], "series id normalized")
    assert_equal(session["series"]["series-1"]["base_row_snapshot"], {"tags": []}, "missing base snapshot default")
    assert_equal(
        source.sanitize_import_filename("/private/tmp/tag import.json"),
        "tag import.json",
        "import filename basename",
    )
    assert_raises_contains(
        lambda: source.sanitize_import_assignments_session({"series": {"series": {"staged_row": {"works": {"2": {}}}}}}),
        "works keys must be 5-digit work ids",
        "invalid import work id",
    )
    assert_raises_contains(lambda: source.sanitize_import_filename("bad\nname.json"), "control characters", "unsafe filename")


def test_default_payload_loading() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        assignments = source.load_assignments(root / "missing-assignments.json")
        registry = source.load_registry(root / "missing-registry.json")
        aliases = source.load_aliases(root / "missing-aliases.json")
        series_index = source.load_series_index(root / "missing-series-index.json")

    assert_equal(assignments["tag_assignments_version"], "tag_assignments_v1", "assignment default version")
    assert_equal(assignments["series"], {}, "assignment default series")
    assert_equal(registry["policy"]["allowed_groups"], source.DEFAULT_ALLOWED_GROUPS, "registry default groups")
    assert_equal(aliases["aliases"], {}, "aliases default")
    assert_equal(series_index["series"], {}, "series index default")


def main() -> None:
    test_tag_id_and_alias_key_validation()
    test_group_and_manual_weight_validation()
    test_assignment_tag_normalization()
    test_import_assignment_rows_and_filename_sanitization()
    test_default_payload_loading()
    print("Tag source model tests OK")


if __name__ == "__main__":
    main()
