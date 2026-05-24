#!/usr/bin/env python3
"""Verify catalogue local-service route ownership."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
STUDIO_SCRIPTS_DIR = SCRIPTS_DIR / "studio"
for path in (SCRIPTS_DIR, STUDIO_SCRIPTS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from catalogue import catalogue_activity as activity  # noqa: E402
from catalogue import catalogue_routes as routes  # noqa: E402
from studio.app.server.studio import studio_catalogue_api  # noqa: E402


def assert_equal(actual, expected, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def assert_no_duplicates(values: tuple[str, ...], label: str) -> None:
    duplicates = sorted({value for value in values if values.count(value) > 1})
    if duplicates:
        raise AssertionError(f"{label} contains duplicate routes: {duplicates!r}")


def test_post_routes_are_unique() -> None:
    assert_no_duplicates(routes.POST_PATHS, "POST_PATHS")


def test_options_routes_are_post_routes_plus_catalogue_read() -> None:
    assert_no_duplicates(routes.OPTIONS_PATHS, "OPTIONS_PATHS")
    assert_equal(set(routes.OPTIONS_PATHS), {*routes.POST_PATHS, routes.CATALOGUE_READ_PATH}, "OPTIONS_PATHS")
    if routes.HEALTH_PATH in routes.OPTIONS_PATHS:
        raise AssertionError("health route should not gain CORS preflight handling implicitly")


def test_activity_profile_endpoints_are_known_post_routes() -> None:
    local_app_post_routes = {
        f"/studio/api/catalogue{api_path}"
        for api_path in {
            "/import-preview",
            "/import-apply",
            "/project-state-report",
            "/thumbnail-quality-preview",
            *studio_catalogue_api.catalogue_write_service.SERVICE_POST_PATHS,
        }
    }
    known_endpoints = {*routes.POST_PATHS, *local_app_post_routes}
    unknown_endpoints = sorted(
        {
            profile.endpoint
            for profile in activity.ACTIVITY_ACTION_PROFILES
            if profile.endpoint not in known_endpoints
        }
    )
    assert_equal(unknown_endpoints, [], "activity profile endpoints")


def main() -> None:
    test_post_routes_are_unique()
    test_options_routes_are_post_routes_plus_catalogue_read()
    test_activity_profile_endpoints_are_known_post_routes()
    print("Catalogue route tests OK")


if __name__ == "__main__":
    main()
