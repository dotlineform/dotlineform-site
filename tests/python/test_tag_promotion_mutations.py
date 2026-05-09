#!/usr/bin/env python3
"""Verify tag alias promotion and canonical tag demotion planners."""

from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import tag_promotion_mutations as promotions  # noqa: E402


NOW = "2026-05-09T12:00:00Z"


def row(tag_id: str, description: str = "") -> dict[str, str]:
    group, slug = tag_id.split(":", 1)
    return {
        "tag_id": tag_id,
        "group": group,
        "label": slug,
        "status": "active",
        "description": description,
    }


def registry_payload() -> dict[str, Any]:
    return {
        "policy": {"allowed_groups": ["subject", "theme", "domain"]},
        "tags": [
            row("subject:trees"),
            row("subject:canopy"),
            row("theme:growth"),
            row("domain:studio"),
        ],
    }


def aliases_payload() -> dict[str, Any]:
    return {
        "aliases": {
            "foliage": {"description": "Leaf forms", "tags": ["subject:trees"]},
            "combo": {"description": "", "tags": ["subject:trees", "theme:growth"]},
            "studio": {"description": "", "tags": ["domain:studio"]},
        }
    }


def assignments_payload() -> dict[str, Any]:
    return {
        "series": {
            "001": {
                "tags": [
                    {"tag_id": "subject:trees", "w_manual": 0.9},
                    {"tag_id": "domain:studio", "w_manual": 0.3},
                ],
                "works": {
                    "00001": {
                        "tags": [
                            {"tag_id": "subject:trees", "w_manual": 0.6},
                            {"tag_id": "theme:growth", "w_manual": 0.3},
                        ]
                    }
                },
            }
        }
    }


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
    registry = {"tags": [row("subject:trees")]}
    aliases = {"aliases": {"foliage": {"description": "", "tags": ["subject:trees"]}, "growth": {"tags": ["theme:growth"]}}}

    registry_updated, aliases_updated, stats, registry_changed, aliases_changed = promotions.promote_alias_to_canonical_tag(
        registry,
        aliases,
        alias_key="foliage",
        group="theme",
        now_utc=NOW,
    )

    assert_true(registry_changed, "promotion creates registry row")
    assert_true(aliases_changed, "promotion removes alias")
    assert_equal([item["tag_id"] for item in registry_updated["tags"]], ["subject:trees", "theme:foliage"], "promoted tag order")
    assert_equal(list(aliases_updated["aliases"].keys()), ["growth"], "promoted alias removed")
    assert_equal(stats["canonical_added"], 1, "canonical added count")
    assert_equal(
        promotions.build_promote_summary_text(stats),
        "mode promote_alias; foliage -> theme:foliage; canonical_added 1; alias_deleted 1; registry final 2; aliases final 1",
        "promote summary",
    )


def test_promote_alias_existing_canonical_removes_alias_only() -> None:
    registry = {"tags": [row("subject:foliage"), row("theme:growth")]}
    aliases = {"aliases": {"foliage": {"description": "", "tags": ["theme:growth"]}}}

    registry_updated, aliases_updated, stats, registry_changed, aliases_changed = promotions.promote_alias_to_canonical_tag(
        registry,
        aliases,
        alias_key="foliage",
        group="subject",
        now_utc=NOW,
    )

    assert_false(registry_changed, "existing canonical avoids registry write")
    assert_true(aliases_changed, "existing canonical still removes alias")
    assert_equal([item["tag_id"] for item in registry_updated["tags"]], ["subject:foliage", "theme:growth"], "registry unchanged")
    assert_equal(aliases_updated["aliases"], {}, "alias removed")
    assert_equal(stats["canonical_exists"], True, "canonical exists stat")
    assert_equal(stats["canonical_added"], 0, "no canonical added")


def test_demote_tag_rewrites_alias_refs_and_assignments() -> None:
    registry_updated, aliases_updated, assignments_updated, stats, assignments_changed = promotions.demote_tag_to_alias(
        registry_payload=copy.deepcopy(registry_payload()),
        aliases_payload=copy.deepcopy(aliases_payload()),
        assignments_payload=copy.deepcopy(assignments_payload()),
        old_tag_id="subject:trees",
        alias_targets=["subject:canopy", "theme:growth"],
        now_utc=NOW,
    )

    assert_equal([item["tag_id"] for item in registry_updated["tags"]], ["subject:canopy", "theme:growth", "domain:studio"], "demoted tag removed")
    assert_equal(aliases_updated["aliases"]["foliage"]["tags"], ["subject:canopy", "theme:growth"], "demoted alias points to targets")
    assert_equal(aliases_updated["aliases"]["combo"]["tags"], ["subject:canopy", "theme:growth"], "other alias refs rewritten")
    assert_true(assignments_changed, "assignments changed")
    assert_equal(
        assignments_updated["series"]["001"]["tags"],
        [
            {"tag_id": "subject:canopy", "w_manual": 0.9},
            {"tag_id": "theme:growth", "w_manual": 0.9},
            {"tag_id": "domain:studio", "w_manual": 0.3},
        ],
        "series assignment rewritten",
    )
    assert_equal(
        assignments_updated["series"]["001"]["works"]["00001"]["tags"],
        [
            {"tag_id": "subject:canopy", "w_manual": 0.6},
            {"tag_id": "theme:growth", "w_manual": 0.6},
        ],
        "work assignment rewritten without duplicate target",
    )
    assert_equal(stats["alias_tag_refs_rewritten"], 2, "alias refs rewritten count")
    assert_equal(stats["series_tag_refs_rewritten"], 1, "series refs rewritten count")
    assert_equal(stats["work_tag_refs_rewritten"], 1, "work refs rewritten count")
    assert_equal(
        promotions.build_demote_summary_text(stats),
        "mode demote_tag; subject:trees -> alias trees; targets 2; series rows 1; series refs 1; work rows 1; work refs 1; alias refs 2; aliases rewritten 2",
        "demote summary",
    )


def test_demote_tag_validation_guards() -> None:
    assert_raises_contains(
        lambda: promotions.demote_tag_to_alias(
            registry_payload(),
            aliases_payload(),
            assignments_payload(),
            old_tag_id="subject:missing",
            alias_targets=["subject:canopy"],
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
            old_tag_id="subject:trees",
            alias_targets=["subject:trees"],
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
            old_tag_id="subject:trees",
            alias_targets=["subject:missing"],
            now_utc=NOW,
        ),
        "is not present in registry",
        "missing alias target",
    )


def test_rewrite_assignments_no_refs_reports_no_change() -> None:
    payload = {"series": {"001": {"tags": [{"tag_id": "domain:studio", "w_manual": 0.3}]}}}
    updated, stats, changed = promotions.rewrite_assignments_for_targets(payload, "subject:trees", ["subject:canopy"], NOW)

    assert_false(changed, "no assignment refs changed")
    assert_equal(updated["series"]["001"]["tags"], [{"tag_id": "domain:studio", "w_manual": 0.3}], "assignments preserved")
    assert_equal(stats["series_rows_touched"], 0, "no series rows touched")


def main() -> None:
    test_promote_alias_creates_canonical_tag_and_removes_alias()
    test_promote_alias_existing_canonical_removes_alias_only()
    test_demote_tag_rewrites_alias_refs_and_assignments()
    test_demote_tag_validation_guards()
    test_rewrite_assignments_no_refs_reports_no_change()
    print("Tag promotion mutation tests OK")


if __name__ == "__main__":
    main()
