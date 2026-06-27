"""Data-oriented fixtures for Docs Viewer tests."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Callable


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: object, *, indent: int | None = None) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=indent)
    write_text(path, text + "\n" if indent is not None else text)


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_site_tools_config(root: Path, *, media_base: str = "https://media.example.test") -> None:
    write_json(
        root / "site-tools/config/site-tools.json",
        {
            "schema_version": "site_tools_config_v1",
            "media": {
                "base": media_base,
            },
        },
        indent=2,
    )


def write_docs_scope_config(root: Path, scopes: list[dict[str, object]], docs_viewer: dict[str, object] | None = None) -> None:
    payload: dict[str, object] = {
        "schema_version": "docs_scopes_v1",
        "scopes": scopes,
    }
    if docs_viewer is not None:
        payload["docs_viewer"] = docs_viewer
    write_json(root / "docs-viewer/config/scopes/docs_scopes.json", payload, indent=2)


def write_doc(
    root: Path,
    filename: str,
    front_matter: dict[str, object],
    *,
    body: str = "",
    scope: str = "studio",
    format_value: Callable[[object], str] = str,
) -> None:
    lines = ["---"]
    for key, value in front_matter.items():
        lines.append(f"{key}: {format_value(value)}")
    lines.extend(["---", "", body or f"# {front_matter['title']}", ""])
    path = root / "docs-viewer/source" / scope / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_library_doc(
    root: Path,
    filename: str,
    front_matter: dict[str, object],
    *,
    body: str = "# Body\n",
    format_value: Callable[[object], str] = str,
) -> None:
    write_doc(root, filename, front_matter, body=body, scope="library", format_value=format_value)


def write_staged_data_file(root: Path, filename: str, payload: object) -> Path:
    path = root / "var/analytics/data-sharing/import-staging" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    if filename.endswith(".jsonl"):
        rows = payload if isinstance(payload, list) else [payload]
        path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    else:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def write_staged_import_file(root: Path, filename: str, payload: bytes | str) -> Path:
    path = root / "var/docs/import-staging" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, bytes):
        path.write_bytes(payload)
    else:
        path.write_text(payload, encoding="utf-8")
    return path


def write_staged_package_file(root: Path, package: str, filename: str, payload: bytes | str) -> Path:
    path = root / "var/docs/import-staging" / package / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, bytes):
        path.write_bytes(payload)
    else:
        path.write_text(payload, encoding="utf-8")
    return path


def write_library_scope_config(root: Path, *, allow_unresolved_parent_ids: bool = True) -> None:
    write_docs_scope_config(
        root,
        [
            {
                "scope_id": "library",
                "scope_type": "public",
                "source": "docs-viewer/source/library",
                "media_path_prefix": "docs/library",
                "output": "docs-viewer/generated/docs/library",
                "search_output": "docs-viewer/generated/search/library/index.json",
                "publish_output": "site/assets/data/docs/scopes/library",
                "publish_search_output": "site/assets/data/search/library/index.json",
                "viewer_base_url": "/library/",
                "include_scope_param": False,
                "default_doc_id": "library",
                "allow_unresolved_parent_ids": allow_unresolved_parent_ids,
            }
        ],
    )


def write_documents_prepare_profiles(root: Path) -> None:
    write_json(
        root / "data-sharing/adapters/documents/config/prepare-profiles.json",
        {
            "schema_version": "documents_prepare_profiles_v1",
            "configs": [
                {
                    "id": "document-summaries",
                    "label": "Document summaries",
                    "description": "Exports summary metadata.",
                    "enabled": True,
                    "data_domains": ["library"],
                    "scopes": ["library"],
                    "target": {
                        "format": "jsonl",
                        "record_shape": "document_rows",
                    },
                    "output": {
                        "path_pattern": "var/analytics/data-sharing/exports/{data_domain}-{profile_id}-{timestamp}.jsonl",
                        "timestamp_format": "%Y%m%d-%H%M%S",
                    },
                    "selection": {
                        "mode": "explicit_doc_ids",
                        "include_descendants": False,
                        "include_non_viewable": True,
                        "supports_missing_summary_only": False,
                        "default_missing_summary_only": False,
                    },
                    "limits": {
                        "max_documents": None,
                        "max_chars_per_document": None,
                        "max_total_chars": None,
                        "truncate": {
                            "enabled": False,
                            "strategy": "paragraph_boundary",
                            "marker": "[truncated]",
                        },
                    },
                    "metadata": {
                        "include": ["export_id", "config_id", "scope", "generated_at", "selected_doc_ids", "counts"],
                    },
                    "external_context": {
                        "task": "suggest_document_summaries",
                        "response_guidance": "Return proposed summary changes keyed by doc_id.",
                        "field_descriptions": {
                            "doc_id": "Stable document identifier. Preserve exactly in responses.",
                            "title": "Document title.",
                        },
                    },
                    "document_fields": [
                        {"source": "doc_id", "output_path": "doc_id", "required": True},
                        {"source": "title", "output_path": "title", "required": True},
                    ],
                }
            ],
        },
        indent=2,
    )


def write_documents_data_sharing_registry(root: Path) -> None:
    write_json(
        root / "data-sharing/config/adapters.json",
        {
            "schema_version": "data_sharing_adapters_v2",
            "paths": {
                "outbound_package_root": "var/analytics/data-sharing/exports",
                "returned_package_staging_root": "var/analytics/data-sharing/import-staging",
                "review_output_root": "var/analytics/data-sharing/import-preview",
            },
            "dispatch": [
                {"data_domain": "library", "operation": "prepare", "adapter_id": "documents"},
                {"data_domain": "library", "operation": "list_returned", "adapter_id": "documents"},
                {"data_domain": "library", "operation": "review", "adapter_id": "documents"},
                {"data_domain": "library", "operation": "apply", "adapter_id": "documents"},
            ],
            "adapters": [
                {
                    "id": "documents",
                    "module": "documents",
                    "label": "Documents",
                    "status": "active",
                    "portability": {"package": "docs-viewer-documents-data-sharing"},
                    "data_domains": {
                        "library": {
                            "app": "docs-viewer",
                            "label": "Library",
                            "scope": "library",
                            "status": "active",
                            "selection_model": "documents",
                            "source_write_targets": {
                                "documents": "docs-viewer/source/library",
                            },
                            "sources": {
                                "source_root": "docs-viewer/source/library",
                            },
                            "config": {
                                "sharing_profiles_path": "data-sharing/adapters/documents/config/prepare-profiles.json",
                            },
                        }
                    },
                    "capabilities": [
                        {
                            "operation": "prepare",
                            "status": "active",
                            "selection_model": "documents",
                            "input_formats": [],
                            "output_formats": ["json", "jsonl"],
                            "path_contract": {"output_root": "outbound_package_root"},
                            "activity": {"script_purpose": "data-sharing-prepare", "record_groups": ["documents"]},
                        },
                        {
                            "operation": "list_returned",
                            "status": "active",
                            "selection_model": "none",
                            "input_formats": ["json", "jsonl"],
                            "output_formats": [],
                            "path_contract": {"staging_root": "returned_package_staging_root"},
                            "activity": {"script_purpose": "data-sharing-list-returned", "record_groups": ["files"]},
                        },
                        {
                            "operation": "review",
                            "status": "active",
                            "selection_model": "file_only",
                            "input_formats": ["json", "jsonl"],
                            "output_formats": ["markdown"],
                            "path_contract": {
                                "staging_root": "returned_package_staging_root",
                                "review_output_root": "review_output_root",
                            },
                            "review_rows": {
                                "fields": ["id", "type", "title", "meta", "record_index", "selectable", "record_groups", "issues"],
                            },
                            "activity": {"script_purpose": "data-sharing-review", "record_groups": ["documents", "files"]},
                        },
                        {
                            "operation": "apply",
                            "status": "active",
                            "selection_model": "records",
                            "input_formats": ["json", "jsonl"],
                            "output_formats": [],
                            "path_contract": {
                                "staging_root": "returned_package_staging_root",
                                "source_root": "source_root",
                            },
                            "requires_confirmation": True,
                            "apply_actions": [
                                {
                                    "id": "summary_apply",
                                    "label": "Update summaries",
                                    "status": "active",
                                    "confirmation": {"title": "Update summaries?", "body": "Update summaries."},
                                    "activity": {"script_purpose": "data-sharing-apply", "record_groups": ["documents"]},
                                },
                                {
                                    "id": "hierarchy_apply",
                                    "label": "Apply hierarchy",
                                    "status": "active",
                                    "confirmation": {"title": "Update hierarchy?", "body": "Update hierarchy."},
                                    "activity": {"script_purpose": "data-sharing-apply", "record_groups": ["documents"]},
                                },
                            ],
                            "activity": {"script_purpose": "data-sharing-apply", "record_groups": ["documents"]},
                        },
                    ],
                }
            ],
        },
        indent=2,
    )


def make_docs_import_repo(format_value: Callable[[object], str] = str) -> tempfile.TemporaryDirectory[str]:
    temp_dir: tempfile.TemporaryDirectory[str] = tempfile.TemporaryDirectory()
    root = Path(temp_dir.name)
    write_json(root / "site-tools/config/site-tools.json", {"schema_version": "site_tools_config_v1"}, indent=2)
    (root / "var/analytics/data-sharing/library/import-staging").mkdir(parents=True, exist_ok=True)
    write_library_scope_config(root)
    write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""}, format_value=format_value)
    write_library_doc(root, "alpha.md", {"doc_id": "alpha", "title": "Alpha", "parent_id": "library"}, format_value=format_value)
    write_documents_prepare_profiles(root)
    write_documents_data_sharing_registry(root)
    return temp_dir
