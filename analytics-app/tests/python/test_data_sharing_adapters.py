#!/usr/bin/env python3
"""Focused checks for Data Sharing adapter registry dispatch."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES_DIR = REPO_ROOT / "analytics-app" / "tests" / "fixtures"
ADAPTERS_PATH = REPO_ROOT / "analytics-app" / "app" / "server" / "analytics_app" / "data_sharing_adapters.py"
if str(FIXTURES_DIR) not in sys.path:
    sys.path.insert(0, str(FIXTURES_DIR))

from data_sharing_factory import adapter_payload, capability, domain_payload, registry_payload, registry_repo  # noqa: E402


def load_adapters_module():
    scripts_studio_dir = ADAPTERS_PATH.parent
    if str(scripts_studio_dir) not in sys.path:
        sys.path.insert(0, str(scripts_studio_dir))
    spec = importlib.util.spec_from_file_location("data_sharing_adapters", ADAPTERS_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load data_sharing_adapters.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


adapters = load_adapters_module()


def expect_value_error(callback, expected: str) -> None:
    try:
        callback()
    except ValueError as error:
        message = str(error)
    else:
        raise AssertionError("expected ValueError")
    assert expected in message, message


def test_active_documents_adapter_resolves_with_v2_metadata() -> None:
    with registry_repo(registry_payload()) as repo_root:
        resolution = adapters.resolve_adapter(repo_root, data_domain="documents", operation="prepare")

        assert resolution.adapter_id == "documents"
        assert resolution.path("outbound_package_root").as_posix() == "var/analytics/data-sharing/exports"
        assert resolution.config_path("sharing_profiles_path").as_posix() == "data-sharing/adapters/documents/config/prepare-profiles.json"
        assert resolution.capability["selection_model"] == "documents"
        assert resolution.capability["output_formats"] == ["json"]
        assert resolution.domain["record_selectors"]["docs_scope"]["source"] == "docs_scope_config"


def test_tags_adapter_definition_resolves_for_inspection() -> None:
    with registry_repo(registry_payload()) as repo_root:
        resolution = adapters.resolve_adapter(repo_root, data_domain="tags", operation="review", require_active=False)

        assert resolution.adapter_id == "analytics-tags"
        assert resolution.adapter["module"] == "analytics.tags"
        assert resolution.domain["source_write_targets"]["tag_registry"] == "analytics-app/data/canonical/tag-registry.json"
        assert resolution.capability["status"] == "planned"


def test_stub_tags_adapter_fails_closed_for_service_resolution() -> None:
    with registry_repo(registry_payload()) as repo_root:
        expect_value_error(
            lambda: adapters.resolve_adapter(repo_root, data_domain="tags", operation="review"),
            "adapter 'analytics-tags' is stub",
        )


def test_registry_rejects_duplicate_domain_operation_dispatch() -> None:
    payload = registry_payload()
    payload["dispatch"] = [
        {"data_domain": "documents", "operation": "prepare", "adapter_id": "documents"},
        {"data_domain": "documents", "operation": "prepare", "adapter_id": "documents"},
    ]
    with registry_repo(payload) as repo_root:
        expect_value_error(
            lambda: adapters.load_registry(repo_root),
            "multiple Data Sharing adapters configured for documents/prepare",
        )


def test_registry_rejects_unsafe_paths() -> None:
    payload = registry_payload()
    payload["adapters"][0]["data_domains"]["documents"]["sources"]["docs_scope_config"] = "../docs-viewer/config/scopes/docs_scopes.json"
    with registry_repo(payload) as repo_root:
        expect_value_error(
            lambda: adapters.load_registry(repo_root),
            "must be a safe relative path",
        )


def test_registry_rejects_non_standard_runtime_artifact_roots() -> None:
    payload = registry_payload()
    payload["paths"]["returned_package_staging_root"] = "var/studio/export-import/import-staging"
    with registry_repo(payload) as repo_root:
        expect_value_error(
            lambda: adapters.load_registry(repo_root),
            "must be var/analytics/data-sharing/import-staging",
        )


def test_registry_rejects_domain_level_runtime_paths() -> None:
    payload = registry_payload()
    payload["adapters"][0]["data_domains"]["documents"]["paths"] = {
        "outbound_package_root": "var/analytics/data-sharing/exports",
    }
    with registry_repo(payload) as repo_root:
        expect_value_error(
            lambda: adapters.load_registry(repo_root),
            "is no longer supported; use top-level paths",
        )


def test_registry_distinguishes_non_active_capability_statuses() -> None:
    for status in ("planned", "stub", "disabled"):
        payload = registry_payload()
        payload["dispatch"] = [{"data_domain": "documents", "operation": "review", "adapter_id": "documents"}]
        payload["adapters"][0]["capabilities"] = [capability("review", status=status)]
        with registry_repo(payload) as repo_root:
            expect_value_error(
                lambda: adapters.resolve_adapter(repo_root, data_domain="documents", operation="review"),
                f"capability 'review' is {status}",
            )


def test_registry_rejects_unknown_operation_names() -> None:
    payload = registry_payload()
    payload["dispatch"] = [{"data_domain": "documents", "operation": "archive", "adapter_id": "documents"}]
    with registry_repo(payload) as repo_root:
        expect_value_error(
            lambda: adapters.load_registry(repo_root),
            "operation 'archive' is not canonical",
        )


def test_repo_registry_loads_and_resolves_documents_and_tags() -> None:
    payload = adapters.load_registry(REPO_ROOT)

    operations = {item["operation"] for item in payload["dispatch"]}
    assert operations == {"prepare", "list_returned", "review", "apply"}
    document_resolution = adapters.resolve_adapter(REPO_ROOT, data_domain="documents", operation="apply")
    tags_resolution = adapters.resolve_adapter(REPO_ROOT, data_domain="tags", operation="review", require_active=False)
    for resolution in (document_resolution, tags_resolution):
        assert resolution.path("outbound_package_root").as_posix() == "var/analytics/data-sharing/exports"
        assert resolution.path("returned_package_staging_root").as_posix() == "var/analytics/data-sharing/import-staging"
        assert resolution.path("review_output_root").as_posix() == "var/analytics/data-sharing/import-preview"
    assert document_resolution.capability["apply_actions"][0]["id"] == "summary_apply"
    assert tags_resolution.adapter_id == "analytics-tags"


def test_repo_documents_adapter_declares_docs_scope_config_not_generated_docs_sources() -> None:
    resolution = adapters.resolve_adapter(REPO_ROOT, data_domain="documents", operation="prepare")
    sources = resolution.domain.get("sources")

    assert sources == {"docs_scope_config": "docs-viewer/config/scopes/docs_scopes.json"}
    assert resolution.domain.get("record_selectors") == {
        "docs_scope": {"source": "docs_scope_config", "required": True}
    }


def main() -> None:
    tests = [
        test_active_documents_adapter_resolves_with_v2_metadata,
        test_tags_adapter_definition_resolves_for_inspection,
        test_stub_tags_adapter_fails_closed_for_service_resolution,
        test_registry_rejects_duplicate_domain_operation_dispatch,
        test_registry_rejects_unsafe_paths,
        test_registry_rejects_non_standard_runtime_artifact_roots,
        test_registry_rejects_domain_level_runtime_paths,
        test_registry_distinguishes_non_active_capability_statuses,
        test_registry_rejects_unknown_operation_names,
        test_repo_registry_loads_and_resolves_documents_and_tags,
        test_repo_documents_adapter_declares_docs_scope_config_not_generated_docs_sources,
    ]
    for test in tests:
        test()


if __name__ == "__main__":
    main()
