#!/usr/bin/env python3
"""Verify Docs Management local-service route ownership and handler dispatch."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DOCS_DIR = REPO_ROOT / "scripts" / "docs"
if str(SCRIPTS_DOCS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DOCS_DIR))

import docs_management_routes as routes  # noqa: E402
import docs_management_server  # noqa: E402


def assert_equal(actual, expected, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def assert_no_duplicates(values: tuple[str, ...], label: str) -> None:
    duplicates = sorted({value for value in values if values.count(value) > 1})
    if duplicates:
        raise AssertionError(f"{label} contains duplicate routes: {duplicates!r}")


def test_get_routes_are_unique() -> None:
    assert_no_duplicates(routes.GET_PATHS, "GET_PATHS")


def test_post_routes_are_unique() -> None:
    assert_no_duplicates(routes.POST_PATHS, "POST_PATHS")


def test_options_routes_are_get_and_post_routes() -> None:
    assert_no_duplicates(routes.OPTIONS_PATHS, "OPTIONS_PATHS")
    assert_equal(set(routes.OPTIONS_PATHS), {*routes.GET_PATHS, *routes.POST_PATHS}, "OPTIONS_PATHS")


def test_handler_dispatch_covers_each_get_route() -> None:
    dispatch = docs_management_server.DocsManagementHandler.GET_HANDLERS
    assert_equal(set(dispatch), set(routes.GET_PATHS), "GET_HANDLERS route keys")
    for route_path, handler_name in dispatch.items():
        handler = getattr(docs_management_server.DocsManagementHandler, handler_name, None)
        if handler is None:
            raise AssertionError(f"{route_path} dispatches to missing handler {handler_name!r}")


def test_handler_dispatch_covers_each_post_route() -> None:
    dispatch = docs_management_server.DocsManagementHandler.POST_HANDLERS
    assert_equal(set(dispatch), set(routes.POST_PATHS), "POST_HANDLERS route keys")
    for route_path, handler_name in dispatch.items():
        handler = getattr(docs_management_server.DocsManagementHandler, handler_name, None)
        if handler is None:
            raise AssertionError(f"{route_path} dispatches to missing handler {handler_name!r}")


def main() -> None:
    test_get_routes_are_unique()
    test_post_routes_are_unique()
    test_options_routes_are_get_and_post_routes()
    test_handler_dispatch_covers_each_get_route()
    test_handler_dispatch_covers_each_post_route()
    print("Docs Management route tests OK")


if __name__ == "__main__":
    main()
