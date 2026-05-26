#!/usr/bin/env python3
"""Verify Docs Management route constant ownership."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
if str(DOCS_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(DOCS_SERVICES_DIR))

import docs_management_routes as routes  # noqa: E402


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
    assert_equal(set(routes.OPTIONS_PATHS), {*routes.GET_PATHS, *routes.POST_PATHS}, "OPTIONS_PATHS")


def test_docs_management_routes_do_not_publish_data_sharing_endpoints() -> None:
    paths = (*routes.GET_PATHS, *routes.POST_PATHS, *routes.OPTIONS_PATHS)
    if any(path.startswith("/data-sharing/") for path in paths):
        raise AssertionError("Docs Management routes must not publish Data Sharing endpoints")


def main() -> None:
    test_get_routes_are_unique()
    test_post_routes_are_unique()
    test_options_routes_are_get_and_post_routes()
    print("Docs Management route tests OK")


if __name__ == "__main__":
    main()
