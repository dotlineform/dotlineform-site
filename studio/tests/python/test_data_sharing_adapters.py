#!/usr/bin/env python3
"""Focused checks for Data Sharing adapter registry dispatch."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
ADAPTERS_PATH = REPO_ROOT / "studio" / "app" / "server" / "studio" / "data_sharing_adapters.py"


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


def domain_payload(status: str = "active") -> dict[str, object]:
    return {
        "label": "Library",
        "scope": "library",
        "status": status,
        "selection_model": "documents",
        "paths": {
            "outbound_package_root": "var/studio/data-sharing/library/exports",
            "returned_package_staging_root": "var/studio/data-sharing/library/import-staging",
            "review_output_root": "var/studio/data-sharing/library/import-preview",
            "source_root": "docs-viewer/source/library",
            "backup_root": "var/docs/backups",
        },
        "source_write_targets": {
            "documents": "docs-viewer/source/library",
        },
        "sources": {
            "docs_index": "assets/data/docs/scopes/library/index.json",
            "docs_payload_root": "assets/data/docs/scopes/library/by-id",
            "source_root": "docs-viewer/source/library",
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
    data_domain: str = "library",
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
            data_domain: domain or domain_payload(status="active"),
        },
        "capabilities": capabilities or [capability("prepare")],
    }


def registry_payload() -> dict[str, object]:
    return {
        "schema_version": "data_sharing_adapters_v2",
        "dispatch": [
            {"data_domain": "library", "operation": "prepare", "adapter_id": "documents"},
            {"data_domain": "library", "operation": "list_returned", "adapter_id": "documents"},
            {"data_domain": "library", "operation": "review", "adapter_id": "documents"},
            {"data_domain": "library", "operation": "apply", "adapter_id": "documents"},
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
                    **domain_payload(status="stub"),
                    "label": "Tags",
                    "scope": "tags",
                    "selection_model": "records",
                    "source_write_targets": {
                        "tag_registry": "studio/data/canonical/analytics/tag-registry.json",
                        "tag_aliases": "studio/data/canonical/analytics/tag-aliases.json",
                        "tag_assignments": "studio/data/canonical/analytics/tag-assignments.json",
                    },
                },
                capabilities=[capability("review", status="planned")],
            ),
        ],
    }


def write_registry(payload: dict[str, object]) -> Path:
    repo_root = Path(tempfile.mkdtemp())
    write_json(repo_root / adapters.REGISTRY_REL_PATH, payload)
    return repo_root


def expect_value_error(callback, expected: str) -> None:
    try:
        callback()
    except ValueError as error:
        message = str(error)
    else:
        raise AssertionError("expected ValueError")
    assert expected in message, message


def test_active_documents_adapter_resolves_with_v2_metadata() -> None:
    repo_root = write_registry(registry_payload())

    resolution = adapters.resolve_adapter(repo_root, data_domain="library", operation="prepare")

    assert resolution.adapter_id == "documents"
    assert resolution.scope == "library"
    assert resolution.path("outbound_package_root").as_posix() == "var/studio/data-sharing/library/exports"
    assert resolution.config_path("sharing_profiles_path").as_posix() == "data-sharing/config/library-export-configs.json"
    assert resolution.capability["selection_model"] == "documents"
    assert resolution.capability["output_formats"] == ["json"]


def test_tags_adapter_definition_resolves_for_inspection() -> None:
    repo_root = write_registry(registry_payload())

    resolution = adapters.resolve_adapter(repo_root, data_domain="tags", operation="review", require_active=False)

    assert resolution.adapter_id == "analytics-tags"
    assert resolution.adapter["module"] == "analytics.tags"
    assert resolution.domain["source_write_targets"]["tag_registry"] == "studio/data/canonical/analytics/tag-registry.json"
    assert resolution.capability["status"] == "planned"


def test_stub_tags_adapter_fails_closed_for_service_resolution() -> None:
    repo_root = write_registry(registry_payload())

    expect_value_error(
        lambda: adapters.resolve_adapter(repo_root, data_domain="tags", operation="review"),
        "adapter 'analytics-tags' is stub",
    )


def test_registry_rejects_duplicate_domain_operation_dispatch() -> None:
    payload = registry_payload()
    payload["dispatch"] = [
        {"data_domain": "library", "operation": "prepare", "adapter_id": "documents"},
        {"data_domain": "library", "operation": "prepare", "adapter_id": "documents"},
    ]
    repo_root = write_registry(payload)

    expect_value_error(
        lambda: adapters.load_registry(repo_root),
        "multiple Data Sharing adapters configured for library/prepare",
    )


def test_registry_rejects_unsafe_paths() -> None:
    payload = registry_payload()
    payload["adapters"][0]["data_domains"]["library"]["paths"]["source_root"] = "../docs-viewer/source/library"
    repo_root = write_registry(payload)

    expect_value_error(
        lambda: adapters.load_registry(repo_root),
        "must be a safe relative path",
    )


def test_registry_distinguishes_non_active_capability_statuses() -> None:
    for status in ("planned", "stub", "disabled"):
        payload = registry_payload()
        payload["dispatch"] = [{"data_domain": "library", "operation": "review", "adapter_id": "documents"}]
        payload["adapters"][0]["capabilities"] = [capability("review", status=status)]
        repo_root = write_registry(payload)

        expect_value_error(
            lambda: adapters.resolve_adapter(repo_root, data_domain="library", operation="review"),
            f"capability 'review' is {status}",
        )


def test_registry_rejects_legacy_operation_names() -> None:
    payload = registry_payload()
    payload["dispatch"] = [{"data_domain": "library", "operation": "export", "adapter_id": "documents"}]
    repo_root = write_registry(payload)

    expect_value_error(
        lambda: adapters.load_registry(repo_root),
        "operation 'export' is not canonical",
    )


def test_repo_registry_loads_and_resolves_documents_and_tags() -> None:
    payload = adapters.load_registry(REPO_ROOT)

    operations = {item["operation"] for item in payload["dispatch"]}
    assert operations == {"prepare", "list_returned", "review", "apply"}
    document_resolution = adapters.resolve_adapter(REPO_ROOT, data_domain="library", operation="apply")
    tags_resolution = adapters.resolve_adapter(REPO_ROOT, data_domain="tags", operation="review", require_active=False)
    assert document_resolution.capability["apply_actions"][0]["id"] == "summary_apply"
    assert tags_resolution.adapter_id == "analytics-tags"


def main() -> None:
    tests = [
        test_active_documents_adapter_resolves_with_v2_metadata,
        test_tags_adapter_definition_resolves_for_inspection,
        test_stub_tags_adapter_fails_closed_for_service_resolution,
        test_registry_rejects_duplicate_domain_operation_dispatch,
        test_registry_rejects_unsafe_paths,
        test_registry_distinguishes_non_active_capability_statuses,
        test_registry_rejects_legacy_operation_names,
        test_repo_registry_loads_and_resolves_documents_and_tags,
    ]
    for test in tests:
        test()


if __name__ == "__main__":
    main()
