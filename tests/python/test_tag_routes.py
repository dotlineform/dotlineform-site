#!/usr/bin/env python3
"""Verify tag local-service route ownership and handler dispatch."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
STUDIO_SCRIPTS_DIR = SCRIPTS_DIR / "studio"
ANALYTICS_SCRIPTS_DIR = SCRIPTS_DIR / "analytics"
for path in (SCRIPTS_DIR, ANALYTICS_SCRIPTS_DIR, STUDIO_SCRIPTS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from analytics import tag_routes as routes  # noqa: E402
from analytics import tag_write_server  # noqa: E402


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


def test_handler_dispatch_covers_each_post_route() -> None:
    dispatch = tag_write_server.Handler.POST_HANDLERS
    assert_equal(set(dispatch), set(routes.POST_PATHS), "POST_HANDLERS route keys")
    for route_path, handler_name in dispatch.items():
        handler = getattr(tag_write_server.Handler, handler_name, None)
        if handler is None:
            raise AssertionError(f"{route_path} dispatches to missing handler {handler_name!r}")


def main() -> None:
    test_post_routes_are_unique()
    test_options_routes_cover_each_post_route()
    test_handler_dispatch_covers_each_post_route()
    print("Tag route tests OK")


if __name__ == "__main__":
    main()
