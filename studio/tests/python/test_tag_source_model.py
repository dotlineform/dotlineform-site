#!/usr/bin/env python3
"""Verify tag source model validation and loading helpers."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[3]
STUDIO_SERVICES_DIR = REPO_ROOT / "studio" / "services"
for path in (STUDIO_SERVICES_DIR,):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from tags import tag_source_model as source  # noqa: E402


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
    assert_equal(source.sanitize_tag_id(" Trees "), "trees", "tag id normalized")
    assert_raises_contains(lambda: source.sanitize_tag_id("subject:trees"), "must be slug-safe", "tag id includes group")
    assert_raises_contains(lambda: source.sanitize_tag_id("bad_slug"), "must be slug-safe", "tag id unsafe slug")

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
        {"tag_id": " Trees ", "w_manual": "0.9", "alias": "Foliage"},
        {"tag_id": "trees", "w_manual": "0.3"},
        {"tag_id": "growth", "w_manual": 0.6},
    ]
    assert_equal(
        source.sanitize_assignment_tags(raw, "tags"),
        [
            {"tag_id": "trees", "w_manual": 0.9, "alias": "foliage"},
            {"tag_id": "growth", "w_manual": 0.6},
        ],
        "assignment tags normalize and de-duplicate",
    )
    assert_raises_contains(lambda: source.sanitize_assignment_tags(["trees"], "tags"), "must be an object", "strict strings")
    assert_equal(
        source.sanitize_assignment_tags(["trees", "bad_value"], "tags", strict=False),
        [{"tag_id": "trees", "w_manual": source.DEFAULT_TAG_WEIGHT}],
        "non-strict assignment rows skip invalid entries",
    )


def test_default_payload_loading() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        assignments = source.load_assignments(root / "missing-assignments.json")
        registry = source.load_registry(root / "missing-registry.json")
        aliases = source.load_aliases(root / "missing-aliases.json")

    assert_equal(assignments["tag_assignments_version"], "tag_assignments_v2", "assignment default version")
    assert_equal(registry["tag_registry_version"], "tag_registry_v6", "registry default version")
    assert_equal(aliases["tag_aliases_version"], "tag_aliases_v2", "aliases default version")
    assert_equal(assignments["series"], {}, "assignment default series")
    assert_equal(registry["policy"]["allowed_groups"], source.DEFAULT_ALLOWED_GROUPS, "registry default groups")
    assert_equal(aliases["aliases"], {}, "aliases default")


def test_registry_v6_primary_document_validation() -> None:
    primary = {
        "scope": "analysis",
        "sub_scope": "tags",
        "doc_id": "d-20260729-120000-000001",
    }
    payload = {
        "tag_registry_version": "tag_registry_v6",
        "updated_at_utc": "2026-07-29T12:00:00Z",
        "policy": {"allowed_groups": ["subject", "theme"]},
        "tags": [
            {
                "tag_id": "trees",
                "group": "subject",
                "primary_document": primary,
                "updated_at_utc": "2026-07-28T12:00:00Z",
            },
            {
                "tag_id": "growth",
                "group": "theme",
                "updated_at_utc": "2026-07-28T12:00:00Z",
            },
        ],
    }
    assert_equal(
        source.validate_registry_payload(payload),
        {"tag_count": 2, "primary_document_count": 1},
        "valid optional exact primary",
    )
    for invalid, expected in (
        ({**primary, "scope": "studio"}, "Analysis Tags collection"),
        ({**primary, "sub_scope": "other"}, "Analysis Tags collection"),
        ({**primary, "doc_id": "not-an-id"}, "immutable document identity"),
        ({"scope": "analysis", "sub_scope": "tags"}, "missing fields"),
        ({**primary, "url": "/analysis/"}, "unsupported fields"),
        (None, "exact document target object"),
    ):
        broken = {
            **payload,
            "tags": [{**payload["tags"][0], "primary_document": invalid}],
        }
        assert_raises_contains(
            lambda broken=broken: source.validate_registry_payload(broken),
            expected,
            f"reject primary {invalid}",
        )
    retired = {
        **payload,
        "tags": [{**payload["tags"][0], "doc_url": []}],
    }
    assert_raises_contains(
        lambda: source.validate_registry_payload(retired),
        "unsupported fields",
        "retired doc_url",
    )
    legacy = {
        **payload,
        "tags": [
            {
                **payload["tags"][0],
                "description": "retired",
            }
        ],
    }
    assert_raises_contains(
        lambda: source.validate_registry_payload(legacy),
        "unsupported fields",
        "retired description",
    )


def main() -> None:
    test_tag_id_and_alias_key_validation()
    test_group_and_manual_weight_validation()
    test_assignment_tag_normalization()
    test_default_payload_loading()
    test_registry_v6_primary_document_validation()
    print("Tag source model tests OK")


if __name__ == "__main__":
    main()
