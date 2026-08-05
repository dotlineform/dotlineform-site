#!/usr/bin/env python3
"""Verify Docs Management route constant ownership."""

from __future__ import annotations

import json
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


def test_dedicated_viewability_routes_are_retired() -> None:
    paths = (*routes.GET_PATHS, *routes.POST_PATHS, *routes.OPTIONS_PATHS)
    retired_paths = {
        "/docs/update-viewability",
        "/docs/update-viewability-bulk",
    }
    published_retired_paths = sorted(retired_paths.intersection(paths))
    if published_retired_paths:
        raise AssertionError(
            f"Dedicated viewability routes must remain retired: {published_retired_paths!r}"
        )


def test_dedicated_viewability_config_entries_are_retired() -> None:
    config_path = REPO_ROOT / "docs-viewer/config/defaults/docs-viewer-service.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    endpoint_keys = set(config.get("endpoints", {}))
    retired_keys = {"update_viewability", "update_viewability_bulk"}
    configured_retired_keys = sorted(retired_keys.intersection(endpoint_keys))
    if configured_retired_keys:
        raise AssertionError(
            f"Dedicated viewability config entries must remain retired: {configured_retired_keys!r}"
        )


def test_abandoned_review_session_routes_remain_retired() -> None:
    paths = (*routes.GET_PATHS, *routes.POST_PATHS)
    assert not any(path.startswith("/docs/review-sessions") for path in paths)


def test_static_html_export_routes_are_management_owned() -> None:
    assert routes.STATIC_HTML_EXPORT_PREVIEW_PATH in routes.POST_PATHS
    assert routes.STATIC_HTML_EXPORT_APPLY_PATH in routes.POST_PATHS
    assert "/docs/export/static-html/delete" not in routes.POST_PATHS


def test_document_transfer_routes_are_management_owned_and_singular_copy_is_retired() -> None:
    assert routes.DOCUMENT_TRANSFER_PREVIEW_PATH in routes.POST_PATHS
    assert routes.DOCUMENT_TRANSFER_APPLY_PATH in routes.POST_PATHS
    assert "/docs/copy-subtree-preview" not in routes.POST_PATHS
    assert "/docs/copy-subtree-apply" not in routes.POST_PATHS


def test_staged_media_routes_are_management_owned() -> None:
    assert routes.STAGED_MEDIA_FILES_PATH in routes.GET_PATHS
    assert routes.STAGED_MEDIA_PREVIEW_PATH in routes.POST_PATHS
    assert routes.STAGED_MEDIA_APPLY_PATH in routes.POST_PATHS


def test_import_source_directory_route_is_management_owned() -> None:
    assert routes.IMPORT_SOURCE_DIRECTORIES_PATH == "/docs/import-source-directories"
    assert routes.IMPORT_SOURCE_DIRECTORIES_PATH in routes.GET_PATHS
    config_path = REPO_ROOT / "docs-viewer/config/defaults/docs-viewer-service.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    assert config["routes"]["import_source_directories"] == routes.IMPORT_SOURCE_DIRECTORIES_PATH


def test_diagram_source_routes_are_management_owned() -> None:
    assert routes.DIAGRAM_SOURCES_PATH in routes.GET_PATHS
    assert routes.OPEN_DIAGRAM_SOURCE_PATH in routes.POST_PATHS


def test_local_target_route_is_management_owned() -> None:
    assert routes.OPEN_LOCAL_TARGET_PATH == "/docs/open-local-target"
    assert routes.OPEN_LOCAL_TARGET_PATH in routes.POST_PATHS


def test_assignable_field_group_route_is_management_owned() -> None:
    assert routes.ASSIGN_FIELD_GROUP_PATH == "/docs/assign-field-group"
    assert routes.ASSIGN_FIELD_GROUP_PATH in routes.POST_PATHS
    config_path = REPO_ROOT / "docs-viewer/config/defaults/docs-viewer-service.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    assert config["routes"]["assign_field_group"] == routes.ASSIGN_FIELD_GROUP_PATH


def test_semantic_token_usage_route_is_management_owned() -> None:
    assert routes.GENERATED_SEMANTIC_TOKENS_PATH in routes.GET_PATHS


def test_project_state_route_is_management_owned() -> None:
    assert routes.PROJECT_STATE_PATH == "/docs/project-state"
    assert routes.PROJECT_STATE_PATH in routes.POST_PATHS


def test_source_backed_sub_scope_document_inventory_route_is_retired() -> None:
    assert "/docs/sub-scope-documents" not in routes.GET_PATHS
    config_path = REPO_ROOT / "docs-viewer/config/defaults/docs-viewer-service.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    assert "sub_scope_documents" not in config["routes"]


def test_metadata_read_route_is_management_owned() -> None:
    assert routes.METADATA_PATH in routes.GET_PATHS
    config_path = REPO_ROOT / "docs-viewer/config/defaults/docs-viewer-service.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    assert config["routes"]["metadata"] == routes.METADATA_PATH


def main() -> None:
    test_get_routes_are_unique()
    test_post_routes_are_unique()
    test_options_routes_are_get_and_post_routes()
    test_docs_management_routes_do_not_publish_data_sharing_endpoints()
    test_dedicated_viewability_routes_are_retired()
    test_dedicated_viewability_config_entries_are_retired()
    test_abandoned_review_session_routes_remain_retired()
    test_static_html_export_routes_are_management_owned()
    test_document_transfer_routes_are_management_owned_and_singular_copy_is_retired()
    test_staged_media_routes_are_management_owned()
    test_import_source_directory_route_is_management_owned()
    test_diagram_source_routes_are_management_owned()
    test_local_target_route_is_management_owned()
    test_semantic_token_usage_route_is_management_owned()
    test_project_state_route_is_management_owned()
    test_source_backed_sub_scope_document_inventory_route_is_retired()
    test_metadata_read_route_is_management_owned()
    print("Docs Management route tests OK")


if __name__ == "__main__":
    main()
