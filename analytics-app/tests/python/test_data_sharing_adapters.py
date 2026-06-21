#!/usr/bin/env python3
"""Focused checks for Data Sharing adapter registry dispatch."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
import importlib.util
import json
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
ADAPTERS_PATH = REPO_ROOT / "analytics-app" / "app" / "server" / "analytics_app" / "data_sharing_adapters.py"


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


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def capability(operation: str, status: str = "active") -> dict[str, object]:
    payload: dict[str, object] = {
        "operation": operation,
        "status": status,
        "selection_model": {
            "prepare": "documents",
            "list_returned": "none",
            "review": "file_only",
            "apply": "records",
        }[operation],
        "input_formats": [] if operation == "prepare" else ["json", "jsonl"],
        "output_formats": ["json"] if operation in {"prepare", "review"} else [],
        "path_contract": {},
        "activity": {
            "script_purpose": f"data-sharing-{operation}",
            "record_groups": ["documents"],
        },
    }
    if status != "active":
        payload["message"] = f"{operation} is {status}"
    if operation == "review":
        payload["review_rows"] = {
            "fields": ["id", "type", "title", "meta", "record_index", "selectable", "record_groups", "issues"]
        }
    if operation == "apply":
        payload["requires_confirmation"] = True
        payload["apply_actions"] = [
            {
                "id": "summary_apply",
                "label": "Update summaries",
                "status": status,
                "confirmation": {
                    "title": "Update summaries?",
                    "body": "Back up and update selected source files.",
                },
                "activity": {
                    "script_purpose": "data-sharing-apply",
                    "record_groups": ["documents"],
                },
            }
        ]
    return payload


def domain_payload(status: str = "active", data_domain: str = "documents") -> dict[str, object]:
    return {
        "app": "docs-viewer",
        "label": "Documents",
        "status": status,
        "selection_model": "documents",
        "record_selectors": {
            "docs_scope": {
                "source": "docs_scope_config",
                "required": True,
            },
        },
        "source_write_targets": {},
        "sources": {
            "docs_scope_config": "docs-viewer/config/scopes/docs_scopes.json",
        },
        "config": {
            "sharing_profiles_path": "data-sharing/config/library-export-configs.json",
        },
    }


def adapter_payload(
    *,
    adapter_id: str = "documents",
    module: str = "documents",
    label: str = "Documents",
    status: str = "active",
    data_domain: str = "documents",
    domain: dict[str, object] | None = None,
    capabilities: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "id": adapter_id,
        "module": module,
        "label": label,
        "status": status,
        "portability": {
            "package": f"{adapter_id}-package",
        },
        "data_domains": {
            data_domain: domain or domain_payload(status="active", data_domain=data_domain),
        },
        "capabilities": capabilities or [capability("prepare")],
    }


def registry_payload() -> dict[str, object]:
    return {
        "schema_version": "data_sharing_adapters_v2",
        "paths": {
            "outbound_package_root": "var/analytics/data-sharing/exports",
            "returned_package_staging_root": "var/analytics/data-sharing/import-staging",
            "review_output_root": "var/analytics/data-sharing/import-preview",
        },
        "dispatch": [
            {"data_domain": "documents", "operation": "prepare", "adapter_id": "documents"},
            {"data_domain": "documents", "operation": "list_returned", "adapter_id": "documents"},
            {"data_domain": "documents", "operation": "review", "adapter_id": "documents"},
            {"data_domain": "documents", "operation": "apply", "adapter_id": "documents"},
            {"data_domain": "tags", "operation": "review", "adapter_id": "analytics-tags"},
        ],
        "adapters": [
            adapter_payload(
                capabilities=[
                    capability("prepare"),
                    capability("list_returned"),
                    capability("review"),
                    capability("apply"),
                ],
            ),
            adapter_payload(
                adapter_id="analytics-tags",
                module="analytics.tags",
                label="Tags",
                status="stub",
                data_domain="tags",
                domain={
                    **domain_payload(status="stub", data_domain="tags"),
                    "app": "analytics",
                    "label": "Tags",
                    "record_selectors": {},
                    "selection_model": "records",
                    "source_write_targets": {
                        "tag_registry": "analytics-app/data/canonical/tag-registry.json",
                        "tag_aliases": "analytics-app/data/canonical/tag-aliases.json",
                        "tag_assignments": "analytics-app/data/canonical/tag-assignments.json",
                    },
                },
                capabilities=[capability("review", status="planned")],
            ),
        ],
    }


@contextmanager
def registry_repo(payload: dict[str, object]) -> Iterator[Path]:
    with tempfile.TemporaryDirectory() as temp:
        repo_root = Path(temp)
        write_json(repo_root / adapters.REGISTRY_REL_PATH, payload)
        yield repo_root


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
        assert resolution.config_path("sharing_profiles_path").as_posix() == "data-sharing/config/library-export-configs.json"
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
