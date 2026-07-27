#!/usr/bin/env python3
"""Verify Studio tag service route ownership and handler dispatch."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
STUDIO_SERVICES_DIR = REPO_ROOT / "studio" / "services"
STUDIO_SERVER_DIR = REPO_ROOT / "studio" / "app" / "server" / "studio"
for path in (STUDIO_SERVICES_DIR, STUDIO_SERVER_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from tags import tag_routes as routes  # noqa: E402
from studio_tag_api import aliases  # noqa: E402
from studio_tag_api import assignments  # noqa: E402
from studio_tag_api import promotions  # noqa: E402
from studio_tag_api import registry  # noqa: E402
import studio_tags_api  # noqa: E402


def assert_equal(actual, expected, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def assert_no_duplicates(values: tuple[str, ...], label: str) -> None:
    duplicates = sorted({value for value in values if values.count(value) > 1})
    if duplicates:
        raise AssertionError(f"{label} contains duplicate routes: {duplicates!r}")


def test_post_routes_are_unique() -> None:
    assert_no_duplicates(routes.POST_PATHS, "POST_PATHS")


def test_options_routes_cover_each_post_route() -> None:
    assert_no_duplicates(routes.OPTIONS_PATHS, "OPTIONS_PATHS")
    assert_equal(set(routes.OPTIONS_PATHS), set(routes.POST_PATHS), "OPTIONS_PATHS")
    if routes.HEALTH_PATH in routes.OPTIONS_PATHS:
        raise AssertionError("health route should not gain CORS preflight handling implicitly")


def test_studio_adapter_covers_each_post_route() -> None:
    assert_equal(set(studio_tags_api.TAG_POST_PATHS), set(routes.POST_PATHS), "Studio tag route keys")
    assert_equal(set(studio_tags_api.POST_HANDLERS), set(routes.POST_PATHS), "Studio tag handler keys")


def test_retired_vocabulary_import_routes_are_absent() -> None:
    retired_paths = {"/import-tag-registry", "/import-tag-aliases"}
    assert_equal(retired_paths.isdisjoint(routes.POST_PATHS), True, "retired routes in POST_PATHS")
    assert_equal(retired_paths.isdisjoint(studio_tags_api.POST_HANDLERS), True, "retired routes in POST_HANDLERS")


def test_retired_assignment_import_routes_are_absent() -> None:
    retired_paths = {"/import-tag-assignments-preview", "/import-tag-assignments"}
    assert_equal(retired_paths.isdisjoint(routes.POST_PATHS), True, "retired assignment routes in POST_PATHS")
    assert_equal(retired_paths.isdisjoint(studio_tags_api.POST_HANDLERS), True, "retired assignment routes in POST_HANDLERS")


def test_tag_write_handlers_live_in_functional_modules() -> None:
    expected_handlers = (
        assignments.save_tags_response,
        registry.create_tag_response,
        registry.mutate_tag_response,
        aliases.create_tag_alias_response,
        aliases.delete_tag_alias_response,
        aliases.mutate_tag_alias_response,
        promotions.promote_tag_alias_response,
        promotions.demote_tag_response,
    )
    if not all(callable(handler) for handler in expected_handlers):
        raise AssertionError("tag write handlers must be callable from functional modules")


def main() -> None:
    test_post_routes_are_unique()
    test_options_routes_cover_each_post_route()
    test_studio_adapter_covers_each_post_route()
    test_retired_vocabulary_import_routes_are_absent()
    test_retired_assignment_import_routes_are_absent()
    test_tag_write_handlers_live_in_functional_modules()
    print("Tag route tests OK")


if __name__ == "__main__":
    main()
