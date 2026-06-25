#!/usr/bin/env python3
"""Verify tag alias import, edit, delete, and rewrite planners."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES_DIR = REPO_ROOT / "analytics-app" / "tests" / "fixtures"
SCRIPTS_DIR = REPO_ROOT / "scripts"
ANALYTICS_PACKAGE_DIR = REPO_ROOT / "analytics-app" / "app" / "server" / "analytics_app"
for path in (FIXTURES_DIR, SCRIPTS_DIR, ANALYTICS_PACKAGE_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from tag_factory import alias_mutation_registry_payload as registry_payload  # noqa: E402
from tag_services import tag_alias_mutations as aliases  # noqa: E402


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


def test_alias_import_modes() -> None:
    existing = {
        "aliases": {
            "foliage": {"description": "old", "tags": ["subject:trees"]},
            "growth": {"description": "keep", "tags": ["theme:growth"]},
        }
    }
    incoming = {
        "aliases": {
            "foliage": {"description": "new", "tags": ["subject:canopy"]},
            "studio": {"description": "added", "tags": ["domain:studio"]},
        }
    }

    replaced, replace_stats = aliases.apply_aliases_import({"aliases": dict(existing["aliases"])}, incoming, "replace", NOW)
    assert_equal(list(replaced["aliases"].keys()), ["foliage", "studio"], "replace alias order")
    assert_equal(replace_stats["removed"], 1, "replace removed count")

    merged, merge_stats = aliases.apply_aliases_import({"aliases": dict(existing["aliases"])}, incoming, "merge", NOW)
    assert_equal(list(merged["aliases"].keys()), ["foliage", "growth", "studio"], "merge alias order")
    assert_equal(merged["aliases"]["foliage"]["description"], "new", "merge overwrites existing alias")
    assert_equal(merge_stats["unchanged"], 1, "merge unchanged count")

    added, add_stats = aliases.apply_aliases_import({"aliases": dict(existing["aliases"])}, incoming, "add", NOW)
    assert_equal(added["aliases"]["foliage"]["description"], "old", "add preserves existing alias")
    assert_equal(list(added["aliases"].keys()), ["foliage", "growth", "studio"], "add alias order")
    assert_equal(add_stats["unchanged"], 1, "add unchanged count")


def test_alias_import_duplicate_handling() -> None:
    imported, stats = aliases.apply_aliases_import(
        {"aliases": {}},
        {
            "aliases": {
                " Foliage ": {"description": "first", "tags": ["subject:trees"]},
                "foliage": {"description": "second", "tags": ["subject:canopy"]},
            }
        },
        "add",
        NOW,
    )

    assert_equal(list(imported["aliases"].keys()), ["foliage"], "duplicate alias keys compact")
    assert_equal(imported["aliases"]["foliage"]["description"], "second", "last duplicate alias wins")
    assert_equal(stats["imported_total"], 1, "stats count normalized alias imports")


def test_alias_edit_delete_and_summary() -> None:
    payload = {
        "aliases": {
            "foliage": {"description": "old", "tags": ["subject:trees"]},
            "growth": {"description": "keep", "tags": ["theme:growth"]},
        }
    }
    edited, edit_stats = aliases.mutate_alias_entry(
        payload,
        registry_payload(),
        alias_key="foliage",
        new_alias_key="canopy",
        description="new",
        tags=["subject:canopy", "theme:growth"],
        now_utc=NOW,
    )
    assert_equal(list(edited["aliases"].keys()), ["canopy", "growth"], "alias rename keeps position")
    assert_equal(edited["aliases"]["canopy"]["tags"], ["subject:canopy", "theme:growth"], "alias edit updates tags")
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
    payload = {"aliases": {"foliage": {"tags": ["subject:trees"]}, "growth": {"tags": ["theme:growth"]}}}
    assert_raises_contains(
        lambda: aliases.mutate_alias_entry(payload, registry_payload(), "foliage", "growth", "", ["subject:trees"], NOW),
        "alias already exists",
        "duplicate alias rename target",
    )
    assert_raises_contains(
        lambda: aliases.mutate_alias_entry(payload, registry_payload(), "foliage", "foliage", "", ["subject:trees", "subject:canopy"], NOW),
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
            ["subject:trees", "theme:growth", "domain:studio", "mood:quiet", "material:paper"],
            NOW,
        ),
        "may include at most",
        "max alias targets",
    )
    assert_raises_contains(
        lambda: aliases.mutate_alias_entry(payload, registry_payload(), "foliage", "foliage", "", ["subject:missing"], NOW),
        "is not present in registry",
        "unknown registry target",
    )


def test_alias_rewrite_for_tag_removes_empty_and_redundant_aliases() -> None:
    payload = {
        "aliases": {
            "old": {"description": "", "tags": ["subject:trees"]},
            "canopy": {"description": "", "tags": ["subject:trees"]},
            "combo": {"description": "", "tags": ["subject:trees", "theme:growth"]},
            "untouched": {"description": "", "tags": ["domain:studio"]},
        }
    }

    renamed, rename_stats = aliases.rewrite_aliases_for_tag(payload, "subject:trees", "subject:canopy", NOW)
    assert_equal("old" in renamed["aliases"], True, "non-redundant renamed alias remains")
    assert_equal("canopy" in renamed["aliases"], False, "redundant self-map is removed")
    assert_equal(renamed["aliases"]["combo"]["tags"], ["subject:canopy", "theme:growth"], "combo alias target rewritten")
    assert_equal(rename_stats["aliases_removed_redundant"], 1, "redundant removal count")

    deleted, delete_stats = aliases.rewrite_aliases_for_tag(
        {"aliases": {"foliage": {"tags": ["subject:trees"]}, "combo": {"tags": ["subject:trees", "theme:growth"]}}},
        "subject:trees",
        None,
        NOW,
    )
    assert_equal("foliage" in deleted["aliases"], False, "empty alias removed")
    assert_equal(deleted["aliases"]["combo"]["tags"], ["theme:growth"], "delete removes target ref from combo")
    assert_equal(delete_stats["aliases_removed_empty"], 1, "empty removal count")


def test_alias_rewrite_for_demote_targets() -> None:
    payload = {
        "aliases": {
            "foliage": {"description": "overwrite", "tags": ["subject:trees"]},
            "combo": {"description": "", "tags": ["subject:trees", "theme:growth"]},
        }
    }
    updated, stats = aliases.rewrite_aliases_for_targets(
        payload,
        old_tag_id="subject:trees",
        replacement_tag_ids=["subject:canopy", "theme:growth"],
        demoted_alias_key="foliage",
        now_utc=NOW,
    )

    assert_equal(updated["aliases"]["foliage"]["tags"], ["subject:canopy", "theme:growth"], "demoted alias points to targets")
    assert_equal(updated["aliases"]["combo"]["tags"], ["subject:canopy", "theme:growth"], "alias refs rewritten without duplicate targets")
    assert_equal(stats["demoted_alias_overwritten"], 1, "demoted alias overwrite count")
    assert_equal(stats["alias_tag_refs_rewritten"], 1, "alias ref rewrite count")


def main() -> None:
    test_alias_import_modes()
    test_alias_import_duplicate_handling()
    test_alias_edit_delete_and_summary()
    test_alias_mutation_guards()
    test_alias_rewrite_for_tag_removes_empty_and_redundant_aliases()
    test_alias_rewrite_for_demote_targets()
    print("Tag alias mutation tests OK")


if __name__ == "__main__":
    main()
