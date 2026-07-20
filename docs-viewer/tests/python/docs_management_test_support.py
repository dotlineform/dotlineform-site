"""Shared fixtures for Docs Management service tests."""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

from repo_factory import write_doc as write_fixture_doc
from repo_factory import docs_scope_record, write_json

REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_DIR = REPO_ROOT / "docs-viewer" / "services"
DOCS_MANAGEMENT_SERVICE_PATH = DOCS_DIR / "docs_management_service.py"
DATA_SHARING_DIR = REPO_ROOT / "data-sharing"
ANALYTICS_SERVER_DIR = REPO_ROOT / "analytics-app" / "app" / "server"
ANALYTICS_PACKAGE_DIR = ANALYTICS_SERVER_DIR / "analytics_app"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
for path in (DATA_SHARING_DIR, ANALYTICS_SERVER_DIR, ANALYTICS_PACKAGE_DIR):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)


def load_docs_management_module(module_name: str, module_path: Path):
    if str(DOCS_DIR) not in sys.path:
        sys.path.insert(0, str(DOCS_DIR))
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {module_path.name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


docs_management_service = load_docs_management_module("docs_management_service", DOCS_MANAGEMENT_SERVICE_PATH)
docs_management_mutations = sys.modules["docs_management_mutations"]
docs_scope_config = sys.modules["docs_scope_config"]
docs_source_model = sys.modules["docs_source_model"]
from docs_document_packages import package as document_package  # noqa: E402
from adapters.documents import prepare as documents_prepare  # noqa: E402
import analytics_data_sharing_api  # noqa: E402

EXTERNAL_DATA_ROOT_MARKER = "$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer"


def write_doc(root: Path, filename: str, front_matter: dict[str, object], body: str = "", scope: str = "studio") -> None:
    write_fixture_doc(
        root,
        filename,
        front_matter,
        body=body,
        scope=scope,
        format_value=docs_source_model.format_front_matter_value,
    )


def make_repo() -> tempfile.TemporaryDirectory[str]:
    temp_dir = tempfile.TemporaryDirectory()
    repo_root = Path(temp_dir.name)
    (repo_root / "site-tools/config").mkdir(parents=True, exist_ok=True); (repo_root / "site-tools/config/site-tools.json").write_text("{\"schema_version\":\"site_tools_config_v1\"}\n", encoding="utf-8")
    write_docs_route_configs(repo_root)
    write_doc(
        repo_root,
        "non-viewable-doc.md",
        {
            "doc_id": "non-viewable-doc",
            "title": "Non-viewable Doc",
            "viewable": False,
        },
        scope="scratch",
    )
    write_doc(
        repo_root,
        "non-viewable-doc.md",
        {
            "doc_id": "non-viewable-doc",
            "title": "Non-viewable Doc",
            "viewable": False,
        },
    )
    write_doc(
        repo_root,
        "child.md",
        {
            "doc_id": "child",
            "title": "Child",
            "parent_id": "non-viewable-doc",
            "viewable": True,
        },
    )
    write_doc(
        repo_root,
        "other.md",
        {
            "doc_id": "other",
            "title": "Other",
            "viewable": True,
        },
    )
    write_json(
        repo_root / "data-sharing/config/adapters.json",
        {
            "schema_version": "data_sharing_adapters_v3",
            "dispatch": [
                {"data_domain": "documents", "operation": "prepare", "adapter_id": "documents"},
            ],
            "paths": {
                "outbound_package_root": "$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/exports",
                "returned_package_staging_root": "$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-staging",
                "review_output_root": "$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-preview",
                "metadata_root": "$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/meta",
            },
            "adapters": [
                {
                    "id": "documents",
                    "module": "documents",
                    "label": "Documents",
                    "status": "active",
                    "portability": {"package": "docs-viewer-documents-data-sharing"},
                    "data_domains": {
                        "documents": {
                            "app": "docs-viewer",
                            "label": "Documents",
                            "status": "active",
                            "selection_model": "documents",
                            "record_selectors": {
                                "docs_scope": {
                                    "source": "docs_scope_config",
                                    "required": True,
                                },
                            },
                            "source_write_targets": {
                                "documents": "docs-viewer/scopes/library/source/documents",
                            },
                            "sources": {
                                "docs_scope_config": "docs-viewer/config/scopes/docs_scopes.json",
                                "docs_payload_root": "site/assets/data/docs/scopes/library/by-id",
                                "source_root": "docs-viewer/scopes/library/source/documents",
                            },
                            "config": {
                                "sharing_profiles_path": "docs-viewer/config/document-packages/profiles.json",
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
                        }
                    ],
                }
            ],
        },
    )
    return temp_dir


def write_docs_route_configs(root: Path) -> None:
    registry = {"schema_version": "docs_viewer_route_config_registry_v1", "routes": []}
    write_json(root / "docs-viewer/config/routes/docs-viewer-routes.json", registry)
    write_json(root / "site/docs-viewer/config/routes/docs-viewer-public-routes.json", registry)


def write_generated_docs(root: Path) -> None:
    docs = [
        {
            "scope": "studio",
            "doc_id": "non-viewable-doc",
            "title": "Non-viewable Doc",
            "viewable": False,
            "content_url": "/docs-viewer/scopes/studio/published/documents/by-id/non-viewable-doc.json",
        },
        {
            "scope": "studio",
            "doc_id": "child",
            "title": "Child",
            "viewable": True,
            "content_url": "/docs-viewer/scopes/studio/published/documents/by-id/child.json",
        },
    ]
    write_json(
        root / "docs-viewer/scopes/studio/published/documents/index-tree.json",
        {
            "schema": "docs_index_tree_v1",
            "viewer_options": {
                "non_loadable_doc_ids": [],
                "manage_only_tree_root_ids": [],
            },
            "docs": docs,
        },
    )
    write_json(
        root / "docs-viewer/scopes/studio/published/documents/recent.json",
        {
            "schema": "docs_recent_v1",
            "basis": "edited",
            "limit": 10,
            "docs": [docs[1]],
        },
    )
    write_json(root / "docs-viewer/scopes/studio/published/documents/by-id/non-viewable-doc.json", {"doc_id": "non-viewable-doc"})
    write_json(root / "docs-viewer/scopes/studio/published/documents/by-id/child.json", {"doc_id": "child"})
    write_json(root / "docs-viewer/scopes/studio/published/search/index.json", {"entries": [{"doc_id": "child"}]})


def write_docs_scope_config(root: Path) -> None:
    write_json(
        root / "docs-viewer/config/scopes/docs_scopes.json",
        {
            "schema_version": "docs_scopes_v3",
            "scopes": [
                docs_scope_record("studio", default_doc_id="child")
            ],
            "docs_viewer": {
                "recent_limit": 10,
                "ui_statuses_by_scope": {
                    "studio": [
                        {"ui_status": "draft", "label": "Draft", "emoji": "D"},
                    ],
                },
            },
        },
    )


def write_docs_viewer_browser_config(root: Path) -> None:
    write_json(
        root / "docs-viewer/config/defaults/docs-viewer-config.json",
        {
            "schema_version": "docs_viewer_config_v1",
            "default_scope_id": "studio",
            "scopes": [
                {
                    "scope_id": "studio",
                    "viewer_base_url": "/docs/",
                    "include_scope_param": True,
                    "default_doc_id": "child",
                    "media": {
                        "img": {
                            "reference_prefix": "docs/studio/img",
                            "served_path_prefix": "/docs/media/studio/img",
                        },
                        "svg": {
                            "reference_prefix": "docs/studio/svg",
                            "served_path_prefix": "/docs/media/studio/svg",
                        },
                        "files": {
                            "reference_prefix": "docs/studio/files",
                            "served_path_prefix": "/docs/media/studio/files",
                        },
                    },
                    "index_tree_url": "/docs-viewer/scopes/studio/published/documents/index-tree.json",
                    "recent_url": "/docs-viewer/scopes/studio/published/documents/recent.json",
                    "search_index_url": "/docs-viewer/scopes/studio/published/search/index.json",
                }
            ],
            "docs_viewer": {
                "recent_limit": 10,
            },
        },
    )
