#!/usr/bin/env python3
"""Verify tag alias promotion and canonical tag demotion planners."""

from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES_DIR = REPO_ROOT / "studio" / "tests" / "fixtures"
STUDIO_SERVICES_DIR = REPO_ROOT / "studio" / "services"
for path in (FIXTURES_DIR, STUDIO_SERVICES_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from tag_factory import (  # noqa: E402
    promotion_aliases_payload as aliases_payload,
    promotion_assignments_payload as assignments_payload,
    promotion_registry_payload as registry_payload,
    tag_row as row,
)
from tags import tag_promotion_mutations as promotions  # noqa: E402


NOW = "2026-05-09T12:00:00Z"


def assert_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def assert_true(value: Any, label: str) -> None:
    if value is not True:
        raise AssertionError(f"{label}: expected True, got {value!r}")


def assert_false(value: Any, label: str) -> None:
    if value is not False:
        raise AssertionError(f"{label}: expected False, got {value!r}")


def assert_raises_contains(fn: Callable[[], Any], expected: str, label: str) -> None:
    try:
        fn()
    except ValueError as exc:
        if expected not in str(exc):
            raise AssertionError(f"{label}: expected error containing {expected!r}, got {str(exc)!r}") from exc
        return
    raise AssertionError(f"{label}: expected ValueError")


def test_promote_alias_creates_canonical_tag_and_removes_alias() -> None:
    registry = {
        "tag_registry_version": "tag_registry_v5",
        "updated_at_utc": NOW,
        "policy": {"allowed_groups": ["subject", "theme"]},
        "tags": [
            row("trees", "subject"),
            row("growth", "theme"),
        ]
    }
    aliases = {
        "aliases": {
            "foliage": {"description": "", "tags": ["trees"]},
            "renewal": {"tags": ["growth"]},
        }
    }

    registry_updated, aliases_updated, stats, registry_changed, aliases_changed = promotions.promote_alias_to_canonical_tag(
        registry,
        aliases,
        alias_key="foliage",
        group="theme",
        now_utc=NOW,
    )

    assert_true(registry_changed, "promotion creates registry row")
    assert_true(aliases_changed, "promotion removes alias")
    assert_equal([item["tag_id"] for item in registry_updated["tags"]], ["trees", "growth", "foliage"], "promoted tag order")
    assert_equal(list(aliases_updated["aliases"].keys()), ["renewal"], "promoted alias removed")
    assert_equal(stats["canonical_added"], 1, "canonical added count")
    assert_equal(
        promotions.build_promote_summary_text(stats),
        "mode promote_alias; foliage -> foliage; canonical_added 1; alias_deleted 1; registry final 3; aliases final 1",
        "promote summary",
    )


def test_promote_alias_existing_canonical_removes_alias_only() -> None:
    registry = {
        "tag_registry_version": "tag_registry_v5",
        "updated_at_utc": NOW,
        "policy": {"allowed_groups": ["subject", "theme"]},
        "tags": [
            row("foliage", "subject"),
            row("growth", "theme"),
        ]
    }
    aliases = {"aliases": {"foliage": {"description": "", "tags": ["growth"]}}}

    registry_updated, aliases_updated, stats, registry_changed, aliases_changed = promotions.promote_alias_to_canonical_tag(
        registry,
        aliases,
        alias_key="foliage",
        group="subject",
        now_utc=NOW,
    )

    assert_false(registry_changed, "existing canonical avoids registry write")
    assert_true(aliases_changed, "existing canonical still removes alias")
    assert_equal([item["tag_id"] for item in registry_updated["tags"]], ["foliage", "growth"], "registry unchanged")
    assert_equal(aliases_updated["aliases"], {}, "alias removed")
    assert_equal(stats["canonical_exists"], True, "canonical exists stat")
    assert_equal(stats["canonical_added"], 0, "no canonical added")


def test_promote_alias_existing_canonical_requires_matching_group() -> None:
    registry = {
        "tag_registry_version": "tag_registry_v5",
        "updated_at_utc": NOW,
        "policy": {"allowed_groups": ["subject", "theme"]},
        "tags": [
            row("foliage", "subject"),
            row("growth", "theme"),
        ]
    }
    aliases = {"aliases": {"foliage": {"description": "", "tags": ["growth"]}}}

    assert_raises_contains(
        lambda: promotions.promote_alias_to_canonical_tag(
            registry,
            aliases,
            alias_key="foliage",
            group="theme",
            now_utc=NOW,
        ),
        "must match the existing canonical tag group",
        "existing canonical group mismatch",
    )


def test_demote_tag_rewrites_alias_refs_and_assignments() -> None:
    registry_updated, aliases_updated, assignments_updated, stats, assignments_changed = promotions.demote_tag_to_alias(
        registry_payload=copy.deepcopy(registry_payload()),
        aliases_payload=copy.deepcopy(aliases_payload()),
        assignments_payload=copy.deepcopy(assignments_payload()),
        old_tag_id="trees",
        alias_targets=["canopy", "growth"],
        now_utc=NOW,
    )

    assert_equal([item["tag_id"] for item in registry_updated["tags"]], ["canopy", "growth", "studio"], "demoted tag removed")
    assert_equal(aliases_updated["aliases"]["foliage"]["tags"], ["canopy", "growth"], "demoted alias points to targets")
    assert_equal(aliases_updated["aliases"]["combo"]["tags"], ["canopy", "growth"], "other alias refs rewritten")
    assert_true(assignments_changed, "assignments changed")
    assert_equal(
        assignments_updated["series"]["001"]["tags"],
        [
            {"tag_id": "canopy", "w_manual": 0.9},
            {"tag_id": "growth", "w_manual": 0.9},
            {"tag_id": "studio", "w_manual": 0.3},
        ],
        "series assignment rewritten",
    )
    assert_equal(
        assignments_updated["series"]["001"]["works"]["00001"]["tags"],
        [
            {"tag_id": "canopy", "w_manual": 0.6},
            {"tag_id": "growth", "w_manual": 0.6},
        ],
        "work assignment rewritten without duplicate target",
    )
    assert_equal(stats["alias_tag_refs_rewritten"], 2, "alias refs rewritten count")
    assert_equal(stats["series_tag_refs_rewritten"], 1, "series refs rewritten count")
    assert_equal(stats["work_tag_refs_rewritten"], 1, "work refs rewritten count")
    assert_equal(
        promotions.build_demote_summary_text(stats),
        "mode demote_tag; trees -> alias trees; targets 2; series rows 1; series refs 1; work rows 1; work refs 1; alias refs 2; aliases rewritten 2",
        "demote summary",
    )


def test_demote_tag_validation_guards() -> None:
    assert_raises_contains(
        lambda: promotions.demote_tag_to_alias(
            registry_payload(),
            aliases_payload(),
            assignments_payload(),
            old_tag_id="missing",
            alias_targets=["canopy"],
            now_utc=NOW,
        ),
        "tag not found",
        "missing demote target",
    )
    assert_raises_contains(
        lambda: promotions.demote_tag_to_alias(
            registry_payload(),
            aliases_payload(),
            assignments_payload(),
            old_tag_id="trees",
            alias_targets=["trees"],
            now_utc=NOW,
        ),
        "must not include the demoted tag_id",
        "self demote target",
    )
    assert_raises_contains(
        lambda: promotions.demote_tag_to_alias(
            registry_payload(),
            aliases_payload(),
            assignments_payload(),
            old_tag_id="trees",
            alias_targets=["missing"],
            now_utc=NOW,
        ),
        "is not present in registry",
        "missing alias target",
    )


def test_rewrite_assignments_no_refs_reports_no_change() -> None:
    payload = {"series": {"001": {"tags": [{"tag_id": "studio", "w_manual": 0.3}]}}}
    updated, stats, changed = promotions.rewrite_assignments_for_targets(payload, "trees", ["canopy"], NOW)

    assert_false(changed, "no assignment refs changed")
    assert_equal(updated["series"]["001"]["tags"], [{"tag_id": "studio", "w_manual": 0.3}], "assignments preserved")
    assert_equal(stats["series_rows_touched"], 0, "no series rows touched")


def main() -> None:
    test_promote_alias_creates_canonical_tag_and_removes_alias()
    test_promote_alias_existing_canonical_removes_alias_only()
    test_promote_alias_existing_canonical_requires_matching_group()
    test_demote_tag_rewrites_alias_refs_and_assignments()
    test_demote_tag_validation_guards()
    test_rewrite_assignments_no_refs_reports_no_change()
    print("Tag promotion mutation tests OK")


if __name__ == "__main__":
    main()
