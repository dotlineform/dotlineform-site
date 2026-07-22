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
        "schema_version": "docs_scopes_v3",
        "scopes": scopes,
    }
    if docs_viewer is not None:
        payload["docs_viewer"] = docs_viewer
    write_json(root / "docs-viewer/config/scopes/docs_scopes.json", payload, indent=2)


def docs_scope_record(
    scope_id: str,
    *,
    scope_type: str = "local",
    scope_root_path: str | None = None,
    viewer_base_url: str = "/docs/",
    include_scope_param: bool = True,
    default_doc_id: str = "",
    non_loadable_doc_ids: list[str] | None = None,
    manage_only_tree_root_ids: list[str] | None = None,
    allow_unresolved_parent_ids: bool = False,
    media_provider: str | None = None,
    media_location_root: str | None = None,
    media_served_root: str | None = None,
    media_types: tuple[str, ...] = ("img", "svg", "files"),
    public_docs_path: str | None = None,
    public_search_path: str | None = None,
    sub_scopes: list[dict[str, object]] | None = None,
    meta: str = "",
) -> dict[str, object]:
    external = scope_type == "local_external"
    local_provider = "external_local" if external else "repository"
    scope_root = scope_root_path or (
        f"$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer/scopes/{scope_id}"
        if external
        else f"docs-viewer/scopes/{scope_id}"
    )
    resolved_media_provider = media_provider or (
        "external_local" if external else ("r2" if scope_type == "public" else "repository")
    )
    media_root = media_location_root or (
        f"{scope_root}/published/media"
        if resolved_media_provider == local_provider
        else f"docs/{scope_id}"
    )
    served_root = (media_served_root or (
        f"https://media.example.test/docs/{scope_id}"
        if resolved_media_provider == "r2"
        else f"/docs/media/{scope_id}"
    )).rstrip("/")
    media: dict[str, dict[str, object]] = {}
    for media_type in media_types:
        record: dict[str, object] = {
            "reference_prefix": f"docs/{scope_id}/{media_type}",
            "served_path_prefix": f"{served_root}/{media_type}",
            "build_inputs": [],
        }
        if media_location_root is not None or resolved_media_provider != local_provider:
            record["location"] = {
                "provider": resolved_media_provider,
                "path": f"{media_root.rstrip('/')}/{media_type}",
            }
        media[media_type] = record
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
        "scope_root": {"provider": local_provider, "path": scope_root},
        "source": {
            "build_media": {},
        },
        "published": {
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
    public_docs_path: str | None = None,
) -> dict[str, object]:
    return {
        "sub_scope": sub_scope,
        "title": title,
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
    path = root / "docs-viewer/scopes" / scope / "source/documents" / filename
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
                media_location_root="site/assets/data/docs/scopes/library/media",
                media_served_root="/assets/data/docs/scopes/library/media",
                media_types=("img", "svg", "files", "html"),
            )
        ],
    )


def write_documents_prepare_profiles(root: Path) -> None:
    write_json(
        root / "docs-viewer/config/document-packages/profiles.json",
        {
            "schema_version": "documents_prepare_profiles_v1",
            "configs": [
                {
                    "id": "document-content",
                    "label": "Document content",
                    "description": "Exports document content.",
                    "enabled": True,
                    "data_domains": ["documents"],
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
                        "supports_include_non_viewable": True,
                        "supports_missing_summary_only": True,
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
    return temp_dir
