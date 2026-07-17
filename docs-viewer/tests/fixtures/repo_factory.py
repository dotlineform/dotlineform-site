"""Data-oriented fixtures for Docs Viewer tests."""

from __future__ import annotations

import json
import os
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


def data_sharing_workspace_root() -> Path:
    projects_base = Path(os.environ["DOTLINEFORM_PROJECTS_BASE_DIR"])
    return projects_base / "data-sharing"


def resolve_data_sharing_marker(value: str) -> Path:
    marker = "$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing"
    if value == marker:
        return data_sharing_workspace_root()
    prefix = f"{marker}/"
    if not value.startswith(prefix):
        raise ValueError(f"not a Data Sharing marker path: {value}")
    return data_sharing_workspace_root() / value[len(prefix):]


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
        "schema_version": "docs_scopes_v2",
        "scopes": scopes,
    }
    if docs_viewer is not None:
        payload["docs_viewer"] = docs_viewer
    write_json(root / "docs-viewer/config/scopes/docs_scopes.json", payload, indent=2)


def docs_scope_record(
    scope_id: str,
    *,
    scope_type: str = "local",
    source_path: str | None = None,
    published_docs_path: str | None = None,
    published_search_path: str | None = None,
    viewer_base_url: str = "/docs/",
    include_scope_param: bool = True,
    default_doc_id: str = "",
    non_loadable_doc_ids: list[str] | None = None,
    manage_only_tree_root_ids: list[str] | None = None,
    allow_unresolved_parent_ids: bool = False,
    media_provider: str | None = None,
    media_location_root: str | None = None,
    media_served_root: str | None = None,
    public_docs_path: str | None = None,
    public_search_path: str | None = None,
    sub_scopes: list[dict[str, object]] | None = None,
    meta: str = "",
) -> dict[str, object]:
    external = scope_type == "local_external"
    local_provider = "external_local" if external else "repository"
    source = source_path or (
        f"$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/source/{scope_id}"
        if external
        else f"docs-viewer/source/{scope_id}"
    )
    published_docs = published_docs_path or (
        f"$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/published/docs/{scope_id}"
        if external
        else f"docs-viewer/published/docs/{scope_id}"
    )
    published_search = published_search_path or (
        f"$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/published/search/{scope_id}/index.json"
        if external
        else f"docs-viewer/published/search/{scope_id}/index.json"
    )
    resolved_media_provider = media_provider or (
        "external_local" if external else ("r2" if scope_type == "public" else "repository")
    )
    media_root = media_location_root or (
        f"{source}/media" if resolved_media_provider in {"repository", "external_local"} else f"docs/{scope_id}"
    )
    served_root = (media_served_root or (
        f"https://media.example.test/docs/{scope_id}"
        if resolved_media_provider == "r2"
        else f"/docs/media/{scope_id}"
    )).rstrip("/")
    media = {
        media_type: {
            "reference_prefix": f"docs/{scope_id}/{media_type}",
            "location": {
                "provider": resolved_media_provider,
                "path": f"{media_root.rstrip('/')}/{media_type}",
            },
            "served_path_prefix": f"{served_root}/{media_type}",
            "build_inputs": [],
        }
        for media_type in ("img", "files")
    }
    public_projection = None
    if scope_type == "public":
        public_projection = {
            "documents": {
                "location": {
                    "provider": "repository",
                    "path": public_docs_path or f"site/assets/data/docs/scopes/{scope_id}",
                }
            },
            "search": {
                "location": {
                    "provider": "repository",
                    "path": public_search_path or f"site/assets/data/search/{scope_id}/index.json",
                }
            },
        }
    return {
        "scope_id": scope_id,
        "scope_type": scope_type,
        "meta": meta or scope_type.replace("_", " "),
        "source": {
            "location": {"provider": local_provider, "path": source},
            "documents_path": ".",
            "build_media": {},
            "sub_scopes_path": ".",
        },
        "published": {
            "documents": {"location": {"provider": local_provider, "path": published_docs}},
            "search": {"location": {"provider": local_provider, "path": published_search}},
            "media": media,
        },
        "public_projection": public_projection,
        "viewer_base_url": viewer_base_url,
        "include_scope_param": include_scope_param,
        "default_doc_id": default_doc_id,
        "non_loadable_doc_ids": non_loadable_doc_ids or [],
        "manage_only_tree_root_ids": manage_only_tree_root_ids or [],
        "allow_unresolved_parent_ids": allow_unresolved_parent_ids,
        "sub_scopes": sub_scopes or [],
    }


def docs_sub_scope_record(
    scope_id: str,
    sub_scope: str,
    *,
    title: str = "",
    scope_type: str = "local",
    source_path: str | None = None,
    published_docs_path: str | None = None,
    published_search_path: str | None = None,
    public_docs_path: str | None = None,
) -> dict[str, object]:
    external = scope_type == "local_external"
    provider = "external_local" if external else "repository"
    marker = "$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer"
    source = source_path or (
        f"{marker}/source/{scope_id}/{sub_scope}"
        if external
        else f"docs-viewer/source/{scope_id}/{sub_scope}"
    )
    published_docs = published_docs_path or (
        f"{marker}/published/docs/{scope_id}/{sub_scope}"
        if external
        else f"docs-viewer/published/docs/{scope_id}/{sub_scope}"
    )
    published_search = published_search_path or (
        f"{marker}/published/search/{scope_id}/{sub_scope}/index.json"
        if external
        else f"docs-viewer/published/search/{scope_id}/{sub_scope}/index.json"
    )
    return {
        "sub_scope": sub_scope,
        "title": title,
        "source": {
            "location": {"provider": provider, "path": source},
            "documents_path": ".",
            "build_media": {},
            "sub_scopes_path": ".",
        },
        "published": {
            "documents": {"location": {"provider": provider, "path": published_docs}},
            "search": {"location": {"provider": provider, "path": published_search}},
            "media": {},
        },
        "public_projection": (
            {
                "documents": {
                    "location": {
                        "provider": "repository",
                        "path": public_docs_path or f"site/assets/data/docs/scopes/{scope_id}/{sub_scope}",
                    }
                },
                "search": None,
            }
            if scope_type == "public"
            else None
        ),
    }


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
    del root
    path = data_sharing_workspace_root() / "import-staging" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    if filename.endswith(".jsonl"):
        rows = payload if isinstance(payload, list) else [payload]
        path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    else:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def write_staged_import_file(root: Path, filename: str, payload: bytes | str) -> Path:
    del root
    path = data_sharing_workspace_root() / "import-staging" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, bytes):
        path.write_bytes(payload)
    else:
        path.write_text(payload, encoding="utf-8")
    return path


def write_staged_package_file(root: Path, package: str, filename: str, payload: bytes | str) -> Path:
    del root
    path = data_sharing_workspace_root() / "import-staging" / package / filename
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
            docs_scope_record(
                "library",
                scope_type="public",
                viewer_base_url="/library/",
                include_scope_param=False,
                default_doc_id="library",
                allow_unresolved_parent_ids=allow_unresolved_parent_ids,
                media_provider="repository",
                media_location_root="docs-viewer/source/library/media",
                media_served_root="/docs/media/library",
            )
        ],
    )


def write_documents_prepare_profiles(root: Path) -> None:
    write_json(
        root / "data-sharing/adapters/documents/config/prepare-profiles.json",
        {
            "schema_version": "documents_prepare_profiles_v1",
            "configs": [
                {
                    "id": "document-content",
                    "label": "Document content",
                    "description": "Exports document content.",
                    "enabled": True,
                    "data_domains": ["library"],
                    "scopes": ["library"],
                    "target": {
                        "format": "jsonl",
                        "record_shape": "document_rows",
                    },
                    "output": {
                        "path_pattern": "{timestamp}-{data_domain}-{profile_id}.jsonl",
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
                        "task": "review_document_content",
                        "response_guidance": "Return only proposed changed fields keyed by doc_id.",
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
            "schema_version": "data_sharing_adapters_v3",
            "paths": {
                "outbound_package_root": "$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/exports",
                "returned_package_staging_root": "$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-staging",
                "review_output_root": "$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-preview",
                "metadata_root": "$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/meta",
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
    write_json(
        root / "docs-viewer/config/routes/docs-viewer-routes.json",
        {
            "schema_version": "docs_viewer_routes_v1",
            "routes": [
                {
                    "route_id": "manage",
                    "app_kind": "manage",
                    "default_scope_id": "studio",
                    "features": ["recent"],
                    "recent_basis": "edited",
                }
            ],
        },
        indent=2,
    )
    (data_sharing_workspace_root() / "import-staging").mkdir(parents=True, exist_ok=True)
    write_library_scope_config(root)
    write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""}, format_value=format_value)
    write_library_doc(root, "alpha.md", {"doc_id": "alpha", "title": "Alpha", "parent_id": "library"}, format_value=format_value)
    write_documents_prepare_profiles(root)
    write_documents_data_sharing_registry(root)
    return temp_dir
