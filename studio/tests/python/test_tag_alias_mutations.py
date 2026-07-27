#!/usr/bin/env python3
"""Verify focused tag alias create, edit, delete, and rewrite planners."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES_DIR = REPO_ROOT / "studio" / "tests" / "fixtures"
STUDIO_SERVICES_DIR = REPO_ROOT / "studio" / "services"
for path in (FIXTURES_DIR, STUDIO_SERVICES_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from tag_factory import alias_mutation_registry_payload as registry_payload  # noqa: E402
from tags import tag_alias_mutations as aliases  # noqa: E402


NOW = "2026-05-09T12:00:00Z"


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


def test_alias_create_adds_one_normalized_entry() -> None:
    payload = {
        "tag_aliases_version": "tag_aliases_v2",
        "updated_at_utc": "2026-05-01T00:00:00Z",
        "aliases": {
            "foliage": {"description": "Old", "tags": ["trees"]},
        },
    }
    existing_entry = payload["aliases"]["foliage"]

    created, stats = aliases.create_alias(
        payload,
        registry_payload(),
        alias=" Leaf-Growth ",
        description="  Leaf growth  ",
        tags=["canopy", "growth"],
        now_utc=NOW,
    )

    assert_equal(list(created["aliases"]), ["foliage", "leaf-growth"], "create appends one alias")
    assert_equal(created["aliases"]["foliage"], existing_entry, "create preserves existing entry")
    assert_equal(
        created["aliases"]["leaf-growth"],
        {"description": "Leaf growth", "tags": ["canopy", "growth"]},
        "create normalizes new entry",
    )
    assert_equal(list(payload["aliases"]), ["foliage"], "planner does not mutate input aliases")
    assert_equal(stats["action"], "create_alias", "create action")
    assert_equal(stats["added"], 1, "create added count")
    assert_equal(stats["final_total"], 2, "create final count")
    assert_equal(
        aliases.build_alias_create_summary_text(stats),
        "created alias leaf-growth; targets 2; final 2",
        "create summary",
    )


def test_alias_create_guards() -> None:
    payload = {"aliases": {"foliage": {"description": "", "tags": ["trees"]}}}
    cases = (
        (
            {"alias": "Bad Alias", "description": "", "tags": ["trees"]},
            "alias must be slug-safe",
            "invalid alias key",
        ),
        (
            {"alias": " Foliage ", "description": "", "tags": ["trees"]},
            "alias already exists",
            "duplicate alias key",
        ),
        (
            {"alias": "canopy", "description": "", "tags": []},
            "must include at least one",
            "missing target",
        ),
        (
            {"alias": "canopy", "description": "", "tags": ["missing"]},
            "is not present in registry",
            "unknown target",
        ),
        (
            {"alias": "canopy", "description": "", "tags": ["trees", "trees"]},
            "duplicates target",
            "duplicate target",
        ),
        (
            {"alias": "canopy", "description": "", "tags": ["trees", "canopy"]},
            "duplicates group",
            "repeated target group",
        ),
        (
            {"alias": "canopy", "description": {"bad": True}, "tags": ["trees"]},
            "description must be a string",
            "invalid description",
        ),
    )
    for request, expected, label in cases:
        assert_raises_contains(
            lambda request=request: aliases.create_alias(
                payload,
                registry_payload(),
                now_utc=NOW,
                **request,
            ),
            expected,
            label,
        )


def test_alias_edit_delete_and_summary() -> None:
    payload = {
        "aliases": {
            "foliage": {"description": "old", "tags": ["trees"]},
            "growth": {"description": "keep", "tags": ["growth"]},
        }
    }
    edited, edit_stats = aliases.mutate_alias_entry(
        payload,
        registry_payload(),
        alias_key="foliage",
        new_alias_key="canopy",
        description="new",
        tags=["canopy", "growth"],
        now_utc=NOW,
    )
    assert_equal(list(edited["aliases"].keys()), ["canopy", "growth"], "alias rename keeps position")
    assert_equal(edited["aliases"]["canopy"]["tags"], ["canopy", "growth"], "alias edit updates tags")
    assert_equal(edit_stats["renamed"], True, "alias edit tracks rename")
    assert_equal(
        aliases.build_alias_mutation_summary_text(edit_stats),
        "mode edit_alias; foliage -> canopy; changed 1; renamed 1; tags_changed 1; description_changed 1; final 2",
        "alias edit summary",
    )

    deleted, delete_stats = aliases.delete_alias_key(edited, "growth", NOW)
    assert_equal(list(deleted["aliases"].keys()), ["canopy"], "alias delete removes key")
    assert_equal(delete_stats["final_total"], 1, "delete final count")


def test_alias_mutation_guards() -> None:
    payload = {"aliases": {"foliage": {"tags": ["trees"]}, "growth": {"tags": ["growth"]}}}
    assert_raises_contains(
        lambda: aliases.mutate_alias_entry(payload, registry_payload(), "foliage", "growth", "", ["trees"], NOW),
        "alias already exists",
        "duplicate alias rename target",
    )
    assert_raises_contains(
        lambda: aliases.mutate_alias_entry(payload, registry_payload(), "foliage", "foliage", "", ["trees", "canopy"], NOW),
        "duplicates group",
        "one target per group",
    )
    assert_raises_contains(
        lambda: aliases.mutate_alias_entry(
            payload,
            registry_payload(),
            "foliage",
            "foliage",
            "",
            ["trees", "growth", "studio", "quiet", "paper"],
            NOW,
        ),
        "may include at most",
        "max alias targets",
    )
    assert_raises_contains(
        lambda: aliases.mutate_alias_entry(payload, registry_payload(), "foliage", "foliage", "", ["missing"], NOW),
        "is not present in registry",
        "unknown registry target",
    )


def test_alias_rewrite_for_tag_removes_empty_and_redundant_aliases() -> None:
    payload = {
        "aliases": {
            "old": {"description": "", "tags": ["trees"]},
            "canopy": {"description": "", "tags": ["trees"]},
            "combo": {"description": "", "tags": ["trees", "growth"]},
            "untouched": {"description": "", "tags": ["studio"]},
        }
    }

    renamed, rename_stats = aliases.rewrite_aliases_for_tag(
        payload,
        "trees",
        "canopy",
        NOW,
        registry_payload(),
    )
    assert_equal("old" in renamed["aliases"], True, "non-redundant renamed alias remains")
    assert_equal("canopy" in renamed["aliases"], False, "redundant self-map is removed")
    assert_equal(renamed["aliases"]["combo"]["tags"], ["canopy", "growth"], "combo alias target rewritten")
    assert_equal(rename_stats["aliases_removed_redundant"], 1, "redundant removal count")

    deleted, delete_stats = aliases.rewrite_aliases_for_tag(
        {"aliases": {"foliage": {"tags": ["trees"]}, "combo": {"tags": ["trees", "growth"]}}},
        "trees",
        None,
        NOW,
        registry_payload(),
    )
    assert_equal("foliage" in deleted["aliases"], False, "empty alias removed")
    assert_equal(deleted["aliases"]["combo"]["tags"], ["growth"], "delete removes target ref from combo")
    assert_equal(delete_stats["aliases_removed_empty"], 1, "empty removal count")


def test_alias_rewrite_for_demote_targets() -> None:
    payload = {
        "aliases": {
            "foliage": {"description": "overwrite", "tags": ["trees"]},
            "combo": {"description": "", "tags": ["trees", "growth"]},
        }
    }
    updated, stats = aliases.rewrite_aliases_for_targets(
        payload,
        old_tag_id="trees",
        replacement_tag_ids=["canopy", "growth"],
        demoted_alias_key="foliage",
        now_utc=NOW,
        registry_payload=registry_payload(),
    )

    assert_equal(updated["aliases"]["foliage"]["tags"], ["canopy", "growth"], "demoted alias points to targets")
    assert_equal(updated["aliases"]["combo"]["tags"], ["canopy", "growth"], "alias refs rewritten without duplicate targets")
    assert_equal(stats["demoted_alias_overwritten"], 1, "demoted alias overwrite count")
    assert_equal(stats["alias_tag_refs_rewritten"], 1, "alias ref rewrite count")


def main() -> None:
    test_alias_create_adds_one_normalized_entry()
    test_alias_create_guards()
    test_alias_edit_delete_and_summary()
    test_alias_mutation_guards()
    test_alias_rewrite_for_tag_removes_empty_and_redundant_aliases()
    test_alias_rewrite_for_demote_targets()
    print("Tag alias mutation tests OK")


if __name__ == "__main__":
    main()
