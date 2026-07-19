"""Data-oriented fixtures for Analytics Data Sharing tests."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
import json
import tempfile
from pathlib import Path


DATA_SHARING_REGISTRY_REL_PATH = Path("data-sharing/config/adapters.json")


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_site_tools_config(root: Path) -> None:
    write_json(root / "site-tools/config/site-tools.json", {"schema_version": "site_tools_config_v1"})


def write_source_doc(
    root: Path,
    filename: str,
    *,
    doc_id: str,
    title: str,
    summary: str = "",
    viewable: bool = True,
    body: str = "Body text.",
) -> None:
    lines = [
        "---",
        f"doc_id: {doc_id}",
        f"title: {title}",
        "added_date: 2026-01-01",
        "last_updated: 2026-01-02",
    ]
    if summary:
        lines.append(f"summary: {summary}")
    if not viewable:
        lines.append("viewable: false")
    lines.extend(["---", "", f"# {title}", "", body])
    path = root / "docs-viewer/scopes/library/source/documents" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_docs_scope_config(root: Path) -> None:
    write_json(
        root / "docs-viewer/config/scopes/docs_scopes.json",
        {
            "schema_version": "docs_scopes_v3",
            "scopes": [
                {
                    "scope_id": "library",
                    "scope_type": "public",
                    "scope_root": {
                        "provider": "repository",
                        "path": "docs-viewer/scopes/library",
                    },
                    "source": {
                        "build_media": {},
                    },
                    "published": {
                        "media": {
                            "img": {
                                "reference_prefix": "docs/library/img",
                                "location": {
                                    "provider": "repository",
                                    "path": "site/assets/data/docs/scopes/library/media/img",
                                },
                                "served_path_prefix": "/assets/data/docs/scopes/library/media/img",
                                "build_inputs": [],
                            },
                            "files": {
                                "reference_prefix": "docs/library/files",
                                "location": {
                                    "provider": "r2",
                                    "path": "docs/library/files",
                                },
                                "served_path_prefix": "https://media.example.test/docs/library/files",
                                "build_inputs": [],
                            },
                        },
                    },
                    "public_projection": {
                        "documents": {
                            "location": {
                                "provider": "repository",
                                "path": "site/assets/data/docs/scopes/library",
                            }
                        },
                        "search": {
                            "location": {
                                "provider": "repository",
                                "path": "site/assets/data/search/library/index.json",
                            }
                        },
                    },
                    "viewer_base_url": "/library/",
                    "include_scope_param": False,
                    "default_doc_id": "library",
                    "non_loadable_doc_ids": [],
                    "manage_only_tree_root_ids": [],
                    "allow_unresolved_parent_ids": False,
                    "sub_scopes": [],
                }
            ],
            "docs_viewer": {
                "recently_added_limit": 10,
            },
        },
    )


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
            "sharing_profiles_path": "data-sharing/adapters/documents/config/prepare-profiles.json",
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
        "schema_version": "data_sharing_adapters_v3",
        "paths": {
            "outbound_package_root": "$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/exports",
            "returned_package_staging_root": "$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-staging",
            "review_output_root": "$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-preview",
            "metadata_root": "$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/meta",
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


def documents_adapter_registry_payload() -> dict[str, object]:
    payload = registry_payload()
    payload["dispatch"] = [
        {"data_domain": "documents", "operation": "prepare", "adapter_id": "documents"},
        {"data_domain": "documents", "operation": "list_returned", "adapter_id": "documents"},
        {"data_domain": "documents", "operation": "review", "adapter_id": "documents"},
        {"data_domain": "documents", "operation": "apply", "adapter_id": "documents"},
    ]
    payload["adapters"] = [
        adapter_payload(
            capabilities=[
                {
                    **capability("prepare"),
                    "input_formats": [],
                    "output_formats": ["json"],
                    "path_contract": {"output_root": "outbound_package_root"},
                    "activity": {"script_purpose": "data-sharing-prepare", "record_groups": ["documents"]},
                },
                {
                    **capability("list_returned"),
                    "input_formats": ["json"],
                    "path_contract": {"staging_root": "returned_package_staging_root"},
                    "activity": {"script_purpose": "data-sharing-list-returned", "record_groups": ["files"]},
                },
                {
                    **capability("review"),
                    "input_formats": ["json"],
                    "output_formats": ["markdown"],
                    "path_contract": {"staging_root": "returned_package_staging_root"},
                    "review_rows": {"fields": ["id"]},
                    "activity": {"script_purpose": "data-sharing-review", "record_groups": ["documents"]},
                },
                {
                    **capability("apply"),
                    "input_formats": ["json"],
                    "path_contract": {"staging_root": "returned_package_staging_root"},
                    "apply_actions": [
                        {
                            "id": "summary_apply",
                            "label": "Update summaries",
                            "status": "active",
                            "confirmation": {"title": "Update?", "body": "Update selected rows."},
                            "activity": {"script_purpose": "data-sharing-apply", "record_groups": ["documents"]},
                        }
                    ],
                },
            ],
        )
    ]
    payload["adapters"][0]["portability"] = {"package": "docs-viewer-documents-data-sharing"}
    return payload


def write_adapter_registry(root: Path, payload: dict[str, object] | None = None) -> None:
    write_json(root / DATA_SHARING_REGISTRY_REL_PATH, payload or documents_adapter_registry_payload())


def write_prepare_profiles(root: Path) -> None:
    write_json(
        root / "data-sharing/adapters/documents/config/prepare-profiles.json",
        {
            "schema_version": "documents_prepare_profiles_v1",
            "configs": [
                {
                    "id": "library-smoke",
                    "label": "Library smoke",
                    "enabled": True,
                    "data_domains": ["documents"],
                    "target": {
                        "format": "json",
                        "supported_formats": ["json"],
                        "record_shape": "document_rows",
                    },
                    "output": {
                        "path_pattern": "{timestamp}-{data_domain}-{profile_id}.json",
                    },
                    "selection": {
                        "mode": "explicit_doc_ids",
                        "include_descendants": True,
                        "include_non_viewable": True,
                        "supports_missing_summary_only": True,
                        "default_missing_summary_only": False,
                    },
                    "metadata": {"include": ["export_id", "data_domain"]},
                    "external_context": {
                        "task": "review_documents",
                        "response_guidance": "Return proposed changes keyed by doc_id.",
                        "field_descriptions": {
                            "doc_id": "Stable document identifier.",
                        },
                    },
                    "document_fields": [
                        {"source": "doc_id", "output_path": "doc_id"},
                    ],
                }
            ],
        },
    )


def make_documents_data_sharing_repo() -> tempfile.TemporaryDirectory[str]:
    temp_dir: tempfile.TemporaryDirectory[str] = tempfile.TemporaryDirectory()
    root = Path(temp_dir.name)
    write_site_tools_config(root)
    write_docs_scope_config(root)
    write_adapter_registry(root)
    write_prepare_profiles(root)
    write_source_doc(
        root,
        "library.md",
        doc_id="library",
        title="Library",
        summary="Library root.",
        body="Library body.",
    )
    write_source_doc(
        root,
        "hidden-doc.md",
        doc_id="hidden-doc",
        title="Hidden",
        viewable=False,
        body="Hidden body.",
    )
    return temp_dir


@contextmanager
def registry_repo(
    payload: dict[str, object],
    registry_rel_path: str | Path = DATA_SHARING_REGISTRY_REL_PATH,
) -> Iterator[Path]:
    with tempfile.TemporaryDirectory() as temp:
        repo_root = Path(temp)
        write_json(repo_root / registry_rel_path, payload)
        yield repo_root
