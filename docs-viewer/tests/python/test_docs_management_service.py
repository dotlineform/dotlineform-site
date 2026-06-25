#!/usr/bin/env python3
"""Focused checks for Docs Management service behavior."""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path


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
from docs_data_sharing import package as docs_data_sharing_package  # noqa: E402
from adapters.documents import prepare as documents_prepare  # noqa: E402
import analytics_data_sharing_api  # noqa: E402

EXTERNAL_DATA_ROOT_MARKER = "$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer"


def write_doc(root: Path, filename: str, front_matter: dict[str, object], body: str = "", scope: str = "studio") -> None:
    lines = ["---"]
    for key, value in front_matter.items():
        lines.append(f"{key}: {docs_source_model.format_front_matter_value(value)}")
    lines.extend(["---", "", body or f"# {front_matter['title']}", ""])
    path = root / "docs-viewer/source" / scope / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


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
            "schema_version": "data_sharing_adapters_v2",
            "dispatch": [
                {"data_domain": "documents", "operation": "prepare", "adapter_id": "documents"},
            ],
            "paths": {
                "outbound_package_root": "var/analytics/data-sharing/exports",
                "returned_package_staging_root": "var/analytics/data-sharing/import-staging",
                "review_output_root": "var/analytics/data-sharing/import-preview",
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
                                "documents": "docs-viewer/source/library",
                            },
                            "sources": {
                                "docs_scope_config": "docs-viewer/config/scopes/docs_scopes.json",
                                "docs_payload_root": "site/assets/data/docs/scopes/library/by-id",
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
                        }
                    ],
                }
            ],
        },
    )
    return temp_dir


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


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
            "content_url": "/docs-viewer/generated/docs/studio/by-id/non-viewable-doc.json",
        },
        {
            "scope": "studio",
            "doc_id": "child",
            "title": "Child",
            "viewable": True,
            "content_url": "/docs-viewer/generated/docs/studio/by-id/child.json",
        },
    ]
    write_json(
        root / "docs-viewer/generated/docs/studio/index-tree.json",
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
        root / "docs-viewer/generated/docs/studio/recently-added.json",
        {
            "schema": "docs_recently_added_v1",
            "limit": 10,
            "docs": [docs[1]],
        },
    )
    write_json(root / "docs-viewer/generated/docs/studio/by-id/non-viewable-doc.json", {"doc_id": "non-viewable-doc"})
    write_json(root / "docs-viewer/generated/docs/studio/by-id/child.json", {"doc_id": "child"})
    write_json(root / "docs-viewer/generated/search/studio/index.json", {"entries": [{"doc_id": "child"}]})


def write_docs_scope_config(root: Path) -> None:
    write_json(
        root / "docs-viewer/config/scopes/docs_scopes.json",
        {
            "schema_version": "docs_scopes_v1",
            "scopes": [
                {
                    "scope_id": "studio",
                    "source": "docs-viewer/source/studio",
                    "media_path_prefix": "docs/studio",
                    "output": "docs-viewer/generated/docs/studio",
                    "search_output": "docs-viewer/generated/search/studio/index.json",
                    "viewer_base_url": "/docs/",
                    "include_scope_param": True,
                    "default_doc_id": "child",
                    "non_loadable_doc_ids": [],
                    "manage_only_tree_root_ids": [],
                    "allow_unresolved_parent_ids": False,
                    "import_media_storage": {
                        "storage_mode": "staging_manual",
                        "repo_assets_path_prefix": "site/assets/docs/studio",
                        "repo_assets_public_path_prefix": "/assets/docs/studio",
                    },
                }
            ],
            "docs_viewer": {
                "recently_added_limit": 10,
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
                    "media_path_prefix": "docs/studio",
                    "index_tree_url": "/docs-viewer/generated/docs/studio/index-tree.json",
                    "recently_added_url": "/docs-viewer/generated/docs/studio/recently-added.json",
                    "search_index_url": "/docs-viewer/generated/search/studio/index.json",
                }
            ],
            "docs_viewer": {
                "recently_added_limit": 10,
            },
        },
    )


def test_hidden_doc_is_editable_in_dry_run() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        result = docs_management_service.handle_update_metadata(
            repo_root,
            {
                "scope": "studio",
                "doc_id": "non-viewable-doc",
                "title": "Non-viewable Doc",
                "parent_id": "",
            },
            dry_run=True,
        )

    assert result["ok"] is True
    assert result["doc_id"] == "non-viewable-doc"
    assert result["record"]["parent_id"] == ""


def test_update_metadata_can_change_viewability_in_dry_run() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        result = docs_management_service.handle_update_metadata(
            repo_root,
            {
                "scope": "studio",
                "doc_id": "other",
                "title": "Other",
                "parent_id": "",
                "ui_status": "",
                "viewable": False,
            },
            dry_run=True,
        )

    assert result["ok"] is True
    assert result["record"]["viewable"] is False
    assert result["changes"]["viewable_changed"] is True
    assert result["changes"]["status_changed"] is False


def test_hidden_doc_viewability_can_be_changed_in_dry_run() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        result = docs_management_service.handle_update_viewability(
            repo_root,
            {
                "scope": "studio",
                "doc_id": "non-viewable-doc",
                "viewable": True,
            },
            dry_run=True,
        )

    assert result["ok"] is True
    assert result["changed_doc_ids"] == ["non-viewable-doc"]
    assert result["records"][0]["viewable"] is True


def test_hidden_parent_delete_is_blocked_only_by_children() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        result = docs_management_mutations.plan_delete_preview(repo_root, "studio", "non-viewable-doc")

    assert result["allowed"] is False
    assert result["blockers"] == ["1 child docs still depend on this parent"]


def test_capabilities_advertise_generated_data_reads() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_generated_docs(repo_root)
        payload = docs_management_service.capabilities_payload(repo_root)

    assert payload["capabilities"]["generated_data_reads"] is True
    assert payload["capabilities"]["scopes"]["studio"]["generated_data_reads"] is True
    assert payload["capabilities"]["scopes"]["studio"]["generated_search_reads"] is True


def test_capabilities_advertise_source_config_reads() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        payload = docs_management_service.capabilities_payload(repo_root)

    assert payload["capabilities"]["source_config_reads"] is True
    assert payload["capabilities"]["source_config_settings_reads"] is True
    assert payload["capabilities"]["source_config_settings_writes"] is True
    assert payload["capabilities"]["scope_lifecycle"]["manifest"] is True
    assert payload["capabilities"]["scope_lifecycle"]["create_preview"] is True
    assert payload["capabilities"]["scope_lifecycle"]["create_apply"] is True
    assert payload["capabilities"]["scope_lifecycle"]["delete_preview"] is True
    assert payload["capabilities"]["scope_lifecycle"]["delete_apply"] is True
    assert payload["capabilities"]["scope_lifecycle"]["sub_scope_create_preview"] is True
    assert payload["capabilities"]["scope_lifecycle"]["sub_scope_create_apply"] is True
    assert payload["capabilities"]["scope_lifecycle"]["sub_scope_delete_preview"] is True
    assert payload["capabilities"]["scope_lifecycle"]["sub_scope_delete_apply"] is True
    assert payload["capabilities"]["scope_lifecycle"]["publishing_modes"] == [
        "public_readonly",
        "local_external",
        "local_committed",
    ]
    assert payload["capabilities"]["scopes"]["studio"]["sub_scope_lifecycle"]["create_eligible"] is True
    assert payload["capabilities"]["scopes"]["studio"]["sub_scope_lifecycle"]["sub_scopes"] == []


def test_scope_manifest_backfills_existing_scopes_as_system_owned() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_docs_scope_config(repo_root)
        write_generated_docs(repo_root)
        payload = docs_management_service.docs_scope_manifest.build_backfilled_manifest(repo_root)

    assert payload["schema_version"] == "docs_scope_manifest_v1"
    records = {record["scope_id"]: record for record in payload["scopes"]}
    assert records["studio"]["owner"] == "system"
    assert records["studio"]["user_created"] is False
    assert records["studio"]["created_by_tool"] is False
    assert any(file["path"] == "docs-viewer/source/studio/child.md" for file in records["studio"]["files"])


def test_scope_create_preview_reports_public_readonly_site_route_and_payloads() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_docs_scope_config(repo_root)
        payload = docs_management_service.docs_scope_manifest.plan_create_scope_preview(
            repo_root,
            {
                "scope_id": "research",
                "title": "Research",
                "source_root": "docs-viewer/source/research",
                "default_doc_id": "research",
                "publishing_mode": "public_readonly",
                "public_route_path": "/research/",
            },
        )

    assert payload["ok"] is True
    assert payload["planned_scope_config"]["viewer_base_url"] == "/research/"
    assert payload["planned_scope_config"]["include_scope_param"] is False
    assert payload["planned_scope_config"]["publish_output"] == "site/assets/data/docs/scopes/research"
    assert payload["planned_scope_config"]["publish_search_output"] == "site/assets/data/search/research/index.json"
    assert payload["urls"]["public"] == "/research/"
    assert any(file["path"] == "site/research/index.html" for file in payload["created_files"])
    assert any(file["path"] == "site/assets/data/docs/scopes/research" for file in payload["publish_files"])
    assert any(file["path"] == "site/assets/data/docs/scopes/research/by-id" for file in payload["publish_files"])
    assert any(file["path"] == "site/assets/data/search/research/index.json" for file in payload["publish_files"])
    changed_paths = {file["path"] for file in payload["changed_files"]}
    assert "docs-viewer/config/routes/docs-viewer-routes.json" in changed_paths
    assert "site/docs-viewer/config/routes/docs-viewer-public-routes.json" in changed_paths


def test_scope_create_preview_reports_local_tracked_outputs() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_docs_scope_config(repo_root)
        payload = docs_management_service.docs_scope_manifest.plan_create_scope_preview(
            repo_root,
            {
                "scope_id": "notes",
                "title": "Notes",
                "source_root": "docs-viewer/source/notes",
                "default_doc_id": "notes",
                "publishing_mode": "local_committed",
                "public_route_path": "/notes/",
            },
        )

    assert payload["ok"] is True
    assert payload["planned_scope_config"]["viewer_base_url"] == "/docs/"
    assert payload["planned_scope_config"]["include_scope_param"] is True
    assert payload["planned_scope_config"]["output"] == "docs-viewer/generated/docs/notes"
    assert payload["planned_scope_config"]["search_output"] == "docs-viewer/generated/search/notes/index.json"
    assert payload["storage_contract"]["public_static_assets"] is False
    assert "non-public Docs Viewer" in payload["storage_contract"]["summary"]
    assert payload["urls"]["public"] == ""
    assert not any(file["kind"] == "route_file" for file in payload["created_files"])
    assert any(file["path"] == "docs-viewer/generated/docs/notes" for file in payload["created_files"])
    assert any(file["path"] == "docs-viewer/generated/docs/notes/index-tree.json" for file in payload["created_files"])
    assert any(file["path"] == "docs-viewer/generated/docs/notes/recently-added.json" for file in payload["created_files"])
    assert any(file["path"] == "docs-viewer/generated/search/notes/index.json" for file in payload["created_files"])
    assert not any(file["path"].startswith("site/assets/data/docs/scopes/notes") for file in payload["created_files"])
    assert not any(file["path"].startswith("site/assets/data/search/notes") for file in payload["created_files"])


def test_sub_scope_create_apply_updates_parent_config_and_creates_nested_roots() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_docs_scope_config(repo_root)
        payload = docs_management_service.handle_sub_scope_create_apply(
            repo_root,
            {
                "parent_scope": "studio",
                "sub_scope": "tags",
                "title": "Tags",
                "confirm": True,
            },
            dry_run=False,
        )
        source_payload = json.loads((repo_root / "docs-viewer/config/scopes/docs_scopes.json").read_text(encoding="utf-8"))
        source_root_exists = (repo_root / "docs-viewer/source/studio/tags").is_dir()
        generated_payload_root_exists = (repo_root / "docs-viewer/generated/docs/studio/tags/by-id").is_dir()
        top_level_source_exists = (repo_root / "docs-viewer/source/tags").exists()
        default_doc_exists = (repo_root / "docs-viewer/source/studio/tags/tags.md").exists()

    assert payload["ok"] is True
    assert payload["action"] == "create_sub_scope"
    assert payload["parent_scope"] == "studio"
    assert payload["sub_scope"] == "tags"
    assert source_root_exists is True
    assert generated_payload_root_exists is True
    assert top_level_source_exists is False
    assert default_doc_exists is False
    assert [scope["scope_id"] for scope in source_payload["scopes"]] == ["studio"]
    assert source_payload["scopes"][0]["sub_scopes"] == [
        {
            "sub_scope": "tags",
            "title": "Tags",
            "source": "docs-viewer/source/studio/tags",
            "output": "docs-viewer/generated/docs/studio/tags",
            "publish_output": "docs-viewer/generated/docs/studio/tags",
        }
    ]
    assert any(file["path"] == "docs-viewer/source/studio/tags" for file in payload["created_files"])
    assert any(file["path"] == "docs-viewer/generated/docs/studio/tags/by-id" for file in payload["created_files"])
    assert payload["publish_files"] == []


def test_sub_scope_delete_apply_removes_config_source_generated_and_published_payloads() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_docs_scope_config(repo_root)
        config_path = repo_root / "docs-viewer/config/scopes/docs_scopes.json"
        source_payload = json.loads(config_path.read_text(encoding="utf-8"))
        source_payload["scopes"][0].update(
            {
                "scope_type": "public",
                "meta": "public scope",
                "viewer_base_url": "/studio/",
                "include_scope_param": False,
                "publish_output": "site/assets/data/docs/scopes/studio",
                "publish_search_output": "site/assets/data/search/studio/index.json",
            }
        )
        write_json(config_path, source_payload)
        docs_management_service.handle_sub_scope_create_apply(
            repo_root,
            {
                "parent_scope": "studio",
                "sub_scope": "tags",
                "title": "Tags",
                "confirm": True,
            },
            dry_run=False,
        )
        (repo_root / "docs-viewer/source/studio/tags/scale.md").write_text("# Scale\n", encoding="utf-8")
        write_json(repo_root / "docs-viewer/generated/docs/studio/tags/manifest.json", {"doc_ids": "scale"})
        write_json(repo_root / "docs-viewer/generated/docs/studio/tags/by-id/scale.json", {"doc_id": "scale"})
        write_json(repo_root / "site/assets/data/docs/scopes/studio/tags/manifest.json", {"doc_ids": "scale"})
        write_json(repo_root / "site/assets/data/docs/scopes/studio/tags/by-id/scale.json", {"doc_id": "scale"})
        preview = docs_management_service.docs_scope_manifest.plan_delete_sub_scope_preview(
            repo_root,
            {
                "parent_scope": "studio",
                "sub_scope": "tags",
            },
        )
        payload = docs_management_service.handle_sub_scope_delete_apply(
            repo_root,
            {
                "parent_scope": "studio",
                "sub_scope": "tags",
                "confirm": True,
            },
            dry_run=False,
        )
        final_config = json.loads(config_path.read_text(encoding="utf-8"))
        source_root_exists = (repo_root / "docs-viewer/source/studio/tags").exists()
        generated_root_exists = (repo_root / "docs-viewer/generated/docs/studio/tags").exists()
        published_root_exists = (repo_root / "site/assets/data/docs/scopes/studio/tags").exists()

    assert preview["ok"] is True
    assert preview["allowed"] is True
    assert any(file["path"] == "docs-viewer/source/studio/tags" for file in preview["delete_files"])
    assert any(file["path"] == "docs-viewer/generated/docs/studio/tags" for file in preview["delete_files"])
    assert any(file["path"] == "site/assets/data/docs/scopes/studio/tags" for file in preview["delete_files"])
    assert payload["ok"] is True
    assert payload["action"] == "delete_sub_scope"
    assert source_root_exists is False
    assert generated_root_exists is False
    assert published_root_exists is False
    assert "sub_scopes" not in final_config["scopes"][0]


def test_docs_scope_config_requires_search_output() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_json(
            repo_root / "docs-viewer/config/scopes/docs_scopes.json",
            {
                "schema_version": "docs_scopes_v1",
                "scopes": [
                    {
                        "scope_id": "studio",
                        "source": "docs-viewer/source/studio",
                        "media_path_prefix": "docs/studio",
                        "output": "docs-viewer/generated/docs/studio",
                        "viewer_base_url": "/docs/",
                        "include_scope_param": True,
                        "default_doc_id": "child",
                    }
                ],
            },
        )
        try:
            docs_scope_config.load_docs_scope_configs(repo_root)
        except ValueError as exc:
            assert "scopes[0].search_output" in str(exc)
        else:
            raise AssertionError("Expected docs scope config to require search_output")


def test_docs_scope_config_rejects_local_assets_outputs() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_json(
            repo_root / "docs-viewer/config/scopes/docs_scopes.json",
            {
                "schema_version": "docs_scopes_v1",
                "scopes": [
                    {
                        "scope_id": "studio",
                        "source": "docs-viewer/source/studio",
                        "media_path_prefix": "docs/studio",
                        "output": "site/assets/data/docs/scopes/studio",
                        "search_output": "site/assets/data/search/studio/index.json",
                        "viewer_base_url": "/docs/",
                        "include_scope_param": True,
                        "default_doc_id": "child",
                    }
                ],
            },
        )
        try:
            docs_scope_config.load_docs_scope_configs(repo_root)
        except ValueError as exc:
            assert "local scope 'studio'" in str(exc)
            assert "site/assets/data/docs/scopes" in str(exc)
        else:
            raise AssertionError("Expected local scope config to reject public generated asset roots")


def test_docs_scope_config_requires_public_readonly_publish_outputs() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_json(
            repo_root / "docs-viewer/config/scopes/docs_scopes.json",
            {
                "schema_version": "docs_scopes_v1",
                "scopes": [
                    {
                        "scope_id": "research",
                        "source": "docs-viewer/source/research",
                        "media_path_prefix": "docs/research",
                        "output": "docs-viewer/generated/docs/research",
                        "search_output": "docs-viewer/generated/search/research/index.json",
                        "publish_output": "site/assets/data/docs/scopes/research",
                        "publish_search_output": "site/assets/data/search/research/index.json",
                        "viewer_base_url": "/research/",
                        "include_scope_param": False,
                        "default_doc_id": "research",
                    }
                ],
            },
        )
        configs = docs_scope_config.load_docs_scope_configs(repo_root)

    assert configs["research"].output.as_posix() == "docs-viewer/generated/docs/research"
    assert configs["research"].search_output.as_posix() == "docs-viewer/generated/search/research/index.json"
    assert configs["research"].publish_output.as_posix() == "site/assets/data/docs/scopes/research"
    assert configs["research"].publish_search_output.as_posix() == "site/assets/data/search/research/index.json"


def test_docs_scope_config_accepts_nested_sub_scopes() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_json(
            repo_root / "docs-viewer/config/scopes/docs_scopes.json",
            {
                "schema_version": "docs_scopes_v1",
                "scopes": [
                    {
                        "scope_id": "research",
                        "scope_type": "public",
                        "source": "docs-viewer/source/research",
                        "media_path_prefix": "docs/research",
                        "output": "docs-viewer/generated/docs/research",
                        "search_output": "docs-viewer/generated/search/research/index.json",
                        "publish_output": "site/assets/data/docs/scopes/research",
                        "publish_search_output": "site/assets/data/search/research/index.json",
                        "viewer_base_url": "/research/",
                        "include_scope_param": False,
                        "default_doc_id": "research",
                        "sub_scopes": [
                            {
                                "sub_scope": "tags",
                                "source": "docs-viewer/source/research/tags",
                                "output": "docs-viewer/generated/docs/research/tags",
                                "publish_output": "site/assets/data/docs/scopes/research/tags",
                            }
                        ],
                    }
                ],
            },
        )
        config = docs_scope_config.load_docs_scope_configs(repo_root)["research"]

    assert config.sub_scopes[0].sub_scope == "tags"
    assert config.sub_scopes[0].source.as_posix() == "docs-viewer/source/research/tags"
    assert config.sub_scopes[0].output.as_posix() == "docs-viewer/generated/docs/research/tags"
    assert config.sub_scopes[0].publish_output.as_posix() == "site/assets/data/docs/scopes/research/tags"


def test_docs_scope_config_rejects_duplicate_sub_scopes() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_docs_scope_config(repo_root)
        config_path = repo_root / "docs-viewer/config/scopes/docs_scopes.json"
        payload = json.loads(config_path.read_text(encoding="utf-8"))
        payload["scopes"][0]["sub_scopes"] = [
            {
                "sub_scope": "tags",
                "source": "docs-viewer/source/studio/tags",
                "output": "docs-viewer/generated/docs/studio/tags",
            },
            {
                "sub_scope": "tags",
                "source": "docs-viewer/source/studio/more-tags",
                "output": "docs-viewer/generated/docs/studio/more-tags",
            },
        ]
        write_json(config_path, payload)
        try:
            docs_scope_config.load_docs_scope_configs(repo_root)
        except ValueError as exc:
            assert "duplicated in scope 'studio'" in str(exc)
        else:
            raise AssertionError("Expected duplicate sub_scope ids to be rejected")


def test_docs_scope_config_rejects_sub_scope_paths_outside_parent() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_docs_scope_config(repo_root)
        config_path = repo_root / "docs-viewer/config/scopes/docs_scopes.json"
        payload = json.loads(config_path.read_text(encoding="utf-8"))
        payload["scopes"][0]["sub_scopes"] = [
            {
                "sub_scope": "tags",
                "source": "docs-viewer/source/tags",
                "output": "docs-viewer/generated/docs/studio/tags",
            }
        ]
        write_json(config_path, payload)
        try:
            docs_scope_config.load_docs_scope_configs(repo_root)
        except ValueError as exc:
            assert "sub-scope studio/tags" in str(exc)
            assert "must be under scopes[0].source" in str(exc)
        else:
            raise AssertionError("Expected sub_scope source paths outside the parent source to be rejected")


def test_docs_scope_config_rejects_public_sub_scope_publish_paths_outside_parent() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_json(
            repo_root / "docs-viewer/config/scopes/docs_scopes.json",
            {
                "schema_version": "docs_scopes_v1",
                "scopes": [
                    {
                        "scope_id": "research",
                        "scope_type": "public",
                        "source": "docs-viewer/source/research",
                        "media_path_prefix": "docs/research",
                        "output": "docs-viewer/generated/docs/research",
                        "search_output": "docs-viewer/generated/search/research/index.json",
                        "publish_output": "site/assets/data/docs/scopes/research",
                        "publish_search_output": "site/assets/data/search/research/index.json",
                        "viewer_base_url": "/research/",
                        "include_scope_param": False,
                        "default_doc_id": "research",
                        "sub_scopes": [
                            {
                                "sub_scope": "tags",
                                "source": "docs-viewer/source/research/tags",
                                "output": "docs-viewer/generated/docs/research/tags",
                                "publish_output": "site/assets/data/docs/tags",
                            }
                        ],
                    }
                ],
            },
        )
        try:
            docs_scope_config.load_docs_scope_configs(repo_root)
        except ValueError as exc:
            assert "sub-scope research/tags" in str(exc)
            assert "must be under scopes[0].publish_output" in str(exc)
        else:
            raise AssertionError("Expected public sub_scope publish paths outside the parent publish root to be rejected")


def test_scope_create_preview_blocks_local_tracked_assets_regression() -> None:
    original_docs_output = docs_management_service.docs_scope_manifest.planned_docs_output
    original_search_output = docs_management_service.docs_scope_manifest.planned_search_output
    docs_management_service.docs_scope_manifest.planned_docs_output = lambda scope_id, _mode: Path("site/assets/data/docs/scopes") / scope_id
    docs_management_service.docs_scope_manifest.planned_search_output = (
        lambda scope_id, _mode: Path("site/assets/data/search") / scope_id / "index.json"
    )
    try:
        with make_repo() as temp_path:
            repo_root = Path(temp_path)
            write_docs_scope_config(repo_root)
            try:
                docs_management_service.docs_scope_manifest.plan_create_scope_preview(
                    repo_root,
                    {
                        "scope_id": "notes",
                        "title": "Notes",
                        "source_root": "docs-viewer/source/notes",
                        "default_doc_id": "notes",
                        "publishing_mode": "local_committed",
                    },
                )
            except ValueError as exc:
                assert "must not write generated docs under site/assets/data/docs/scopes" in str(exc)
            else:
                raise AssertionError("Expected local tracked preview to reject assets output roots")
    finally:
        docs_management_service.docs_scope_manifest.planned_docs_output = original_docs_output
        docs_management_service.docs_scope_manifest.planned_search_output = original_search_output


def test_scope_create_apply_blocks_local_tracked_assets_regression() -> None:
    original_docs_output = docs_management_service.docs_scope_manifest.planned_docs_output
    original_search_output = docs_management_service.docs_scope_manifest.planned_search_output
    docs_management_service.docs_scope_manifest.planned_docs_output = lambda scope_id, _mode: Path("site/assets/data/docs/scopes") / scope_id
    docs_management_service.docs_scope_manifest.planned_search_output = (
        lambda scope_id, _mode: Path("site/assets/data/search") / scope_id / "index.json"
    )
    try:
        with make_repo() as temp_path:
            repo_root = Path(temp_path)
            write_docs_scope_config(repo_root)
            try:
                docs_management_service.handle_scope_create_apply(
                    repo_root,
                    {
                        "scope_id": "notes",
                        "title": "Notes",
                        "source_root": "docs-viewer/source/notes",
                        "default_doc_id": "notes",
                        "publishing_mode": "local_committed",
                        "confirm": True,
                    },
                    dry_run=True,
                )
            except ValueError as exc:
                assert "must not write generated docs under site/assets/data/docs/scopes" in str(exc)
            else:
                raise AssertionError("Expected local tracked apply to reject assets output roots")
    finally:
        docs_management_service.docs_scope_manifest.planned_docs_output = original_docs_output
        docs_management_service.docs_scope_manifest.planned_search_output = original_search_output


def test_scope_create_apply_requires_confirmation() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_docs_scope_config(repo_root)
        try:
            docs_management_service.handle_scope_create_apply(
                repo_root,
                {
                    "scope_id": "research",
                    "title": "Research",
                    "source_root": "docs-viewer/source/research",
                    "default_doc_id": "research",
                    "publishing_mode": "public_readonly",
                    "public_route_path": "/research/",
                },
                dry_run=True,
            )
        except ValueError as exc:
            assert "confirm must be true" in str(exc)
        else:
            raise AssertionError("scope create apply should require explicit confirmation")


def test_scope_create_preview_requires_existing_external_docs_viewer_root() -> None:
    old_projects_base = os.environ.get("DOTLINEFORM_PROJECTS_BASE_DIR")
    try:
        with make_repo() as temp_path:
            repo_root = Path(temp_path)
            projects_root = (repo_root.parent / f"{repo_root.name}-external-docs-data").resolve()
            projects_root.mkdir()
            os.environ["DOTLINEFORM_PROJECTS_BASE_DIR"] = projects_root.as_posix()
            write_docs_scope_config(repo_root)
            try:
                docs_management_service.docs_scope_manifest.plan_create_scope_preview(
                    repo_root,
                    {
                        "scope_id": "research",
                        "title": "Research",
                        "default_doc_id": "research",
                        "publishing_mode": "local_external",
                    },
                )
            except ValueError as exc:
                error = str(exc)
            else:
                raise AssertionError("external local preview should require an existing docs-viewer external root")
    finally:
        if old_projects_base is None:
            os.environ.pop("DOTLINEFORM_PROJECTS_BASE_DIR", None)
        else:
            os.environ["DOTLINEFORM_PROJECTS_BASE_DIR"] = old_projects_base

    assert "external_data_root does not exist" in error
    assert not (projects_root / "docs-viewer").exists()


def test_scope_create_apply_writes_allowlisted_files_and_runs_rebuild() -> None:
    calls: list[tuple[Path, str, dict[str, object]]] = []
    original_rebuild = docs_management_service.write_rebuild.rebuild_scope_outputs

    def fake_rebuild(repo_root: Path, scope: str, **kwargs):
        calls.append((repo_root, scope, kwargs))
        return {
            "ok": True,
            "steps": [{"command": "fake build", "returncode": 0, "stdout": "", "stderr": ""}],
            "search": {"mode": "full", "doc_ids": []},
        }

    docs_management_service.write_rebuild.rebuild_scope_outputs = fake_rebuild
    original_projects_base = os.environ.get("DOTLINEFORM_PROJECTS_BASE_DIR")
    try:
        with make_repo() as temp_path:
            repo_root = Path(temp_path)
            projects_root = (repo_root.parent / f"{repo_root.name}-external-docs-data").resolve()
            external_root = projects_root / "docs-viewer"
            external_root.mkdir(parents=True)
            os.environ["DOTLINEFORM_PROJECTS_BASE_DIR"] = projects_root.as_posix()
            write_docs_scope_config(repo_root)
            payload = docs_management_service.handle_scope_create_apply(
                repo_root,
                {
                    "scope_id": "research",
                    "title": "Research",
                    "default_doc_id": "research",
                    "publishing_mode": "local_external",
                    "confirm": True,
                },
                dry_run=False,
            )
            source_payload = json.loads((repo_root / "docs-viewer/config/scopes/docs_scopes.json").read_text(encoding="utf-8"))
            manifest_payload = json.loads((repo_root / "docs-viewer/config/scopes/docs_scope_manifest.json").read_text(encoding="utf-8"))
            default_doc_path = external_root / "source/research/research.md"
            default_doc_exists = default_doc_path.exists()
            default_doc_text = default_doc_path.read_text(encoding="utf-8")
            route_exists = (repo_root / "research/index.md").exists()
    finally:
        docs_management_service.write_rebuild.rebuild_scope_outputs = original_rebuild
        if original_projects_base is None:
            os.environ.pop("DOTLINEFORM_PROJECTS_BASE_DIR", None)
        else:
            os.environ["DOTLINEFORM_PROJECTS_BASE_DIR"] = original_projects_base

    assert payload["ok"] is True
    assert payload["schema_version"] == "docs_scope_lifecycle_apply_v1"
    assert "backup_dir" not in payload
    assert payload["build_commands"][0]["status"] == "completed"
    assert calls == [(repo_root, "research", {"include_search": True})]
    assert default_doc_exists is True
    assert "viewable:" not in default_doc_text
    assert "published:" not in default_doc_text
    assert "hidden:" not in default_doc_text
    assert route_exists is False
    assert source_payload["scopes"][1]["scope_id"] == "research"
    assert source_payload["scopes"][1]["scope_type"] == "local_external"
    assert source_payload["scopes"][1]["viewer_base_url"] == "/docs/"
    assert source_payload["scopes"][1]["external_data_root"] == EXTERNAL_DATA_ROOT_MARKER
    assert source_payload["scopes"][1]["source"] == f"{EXTERNAL_DATA_ROOT_MARKER}/source/research"
    assert source_payload["scopes"][1]["output"] == f"{EXTERNAL_DATA_ROOT_MARKER}/generated/docs/research"
    assert source_payload["scopes"][1]["search_output"] == f"{EXTERNAL_DATA_ROOT_MARKER}/generated/search/research/index.json"
    assert "publish_output" not in source_payload["scopes"][1]
    assert "publish_search_output" not in source_payload["scopes"][1]
    assert source_payload["scopes"][1]["include_scope_param"] is True
    records = {record["scope_id"]: record for record in manifest_payload["scopes"]}
    assert records["research"]["user_created"] is True
    assert records["research"]["created_by_tool"] is True
    assert records["research"]["scope_type"] == "local"
    assert records["research"]["repo_status_at_creation"] == "external"
    assert records["research"]["metadata"]["external_data_root"] == EXTERNAL_DATA_ROOT_MARKER
    recorded_paths = {file["path"] for file in records["research"]["files"]}
    assert (external_root / "generated/docs/research/index-tree.json").as_posix() in recorded_paths
    assert (external_root / "generated/docs/research/recently-added.json").as_posix() in recorded_paths
    assert any(file["path"] == "docs-viewer/config/scopes/docs_scopes.json" for file in records["research"]["files"])
    assert not any(file["kind"] == "route_file" for file in records["research"]["files"])
    assert "docs-viewer/runtime/js/docs-viewer-public.js" not in recorded_paths
    assert "docs-viewer/runtime/js/docs-viewer-manage.js" not in recorded_paths
    assert "docs-viewer/static/css/docs-viewer.css" not in recorded_paths
    assert "docs-viewer/static/css/docs-viewer-manage.css" not in recorded_paths
    assert "docs-viewer/config/routes/docs-viewer-public-routes.json" not in recorded_paths


def test_scope_create_apply_writes_public_site_route_config_and_payloads() -> None:
    calls: list[tuple[Path, str, dict[str, object]]] = []
    original_rebuild = docs_management_service.write_rebuild.rebuild_scope_outputs

    def fake_rebuild(repo_root: Path, scope: str, **kwargs):
        calls.append((repo_root, scope, kwargs))
        docs_output = repo_root / "docs-viewer/generated/docs" / scope
        (docs_output / "by-id").mkdir(parents=True)
        (docs_output / "index-tree.json").write_text("{}", encoding="utf-8")
        (docs_output / "recently-added.json").write_text("{}", encoding="utf-8")
        (docs_output / f"by-id/{scope}.json").write_text(json.dumps({"doc_id": scope}), encoding="utf-8")
        search_output = repo_root / "docs-viewer/generated/search" / scope
        search_output.mkdir(parents=True)
        (search_output / "index.json").write_text(json.dumps({"entries": []}), encoding="utf-8")
        return {"ok": True}

    docs_management_service.write_rebuild.rebuild_scope_outputs = fake_rebuild
    try:
        with make_repo() as temp_path:
            repo_root = Path(temp_path)
            write_docs_scope_config(repo_root)
            payload = docs_management_service.handle_scope_create_apply(
                repo_root,
                {
                    "scope_id": "research",
                    "title": "Research",
                    "source_root": "docs-viewer/source/research",
                    "default_doc_id": "research",
                    "publishing_mode": "public_readonly",
                    "public_route_path": "/research/",
                    "confirm": True,
                },
                dry_run=False,
            )
            route_html = (repo_root / "site/research/index.html").read_text(encoding="utf-8")
            scope_payload = json.loads((repo_root / "docs-viewer/config/scopes/docs_scopes.json").read_text(encoding="utf-8"))
            public_routes = json.loads((repo_root / "site/docs-viewer/config/routes/docs-viewer-public-routes.json").read_text(encoding="utf-8"))
            all_routes = json.loads((repo_root / "docs-viewer/config/routes/docs-viewer-routes.json").read_text(encoding="utf-8"))
            manifest_payload = json.loads((repo_root / "docs-viewer/config/scopes/docs_scope_manifest.json").read_text(encoding="utf-8"))
            public_doc_exists = (repo_root / "site/assets/data/docs/scopes/research/by-id/research.json").exists()
            public_search_exists = (repo_root / "site/assets/data/search/research/index.json").exists()
    finally:
        docs_management_service.write_rebuild.rebuild_scope_outputs = original_rebuild

    assert payload["ok"] is True
    assert payload["publishing_mode"] == "public_readonly"
    assert calls == [(repo_root, "research", {"include_search": True})]
    assert 'data-allow-management="false"' in route_html
    assert 'data-include-scope-param="false"' in route_html
    assert 'data-route-config-url="/docs-viewer/config/routes/docs-viewer-public-routes.json"' in route_html
    assert 'data-route-id="research"' not in route_html
    assert "Research | dotlineform" not in route_html
    assert "__ROUTE_ID__" not in route_html
    assert 'src="/docs-viewer/runtime/js/public/docs-viewer-public.js?v=' in route_html
    assert "docs_viewer_readonly_route.html" not in route_html
    assert scope_payload["scopes"][1]["scope_id"] == "research"
    assert scope_payload["scopes"][1]["viewer_base_url"] == "/research/"
    assert scope_payload["scopes"][1]["include_scope_param"] is False
    assert public_routes["routes"][0]["route_id"] == "research"
    assert public_routes["routes"][0]["route_path"] == "/research/"
    assert public_routes["routes"][0]["ui"]["route_shell"]["page_title"] == "Research | dotlineform"
    assert public_routes["routes"][0]["ui"]["route_shell"]["body_class"] == "research"
    assert public_routes["routes"][0]["ui"]["viewer_search"]["placeholder"] == "search research"
    assert public_routes["routes"][0]["docs_paths"]["index_tree_url"] == "/assets/data/docs/scopes/research/index-tree.json"
    assert any(route["route_id"] == "research" for route in all_routes["routes"])
    assert public_doc_exists is True
    assert public_search_exists is True
    records = {record["scope_id"]: record for record in manifest_payload["scopes"]}
    assert records["research"]["scope_type"] == "public"
    recorded_paths = {file["path"] for file in records["research"]["files"]}
    assert "site/research/index.html" in recorded_paths
    assert "site/docs-viewer/config/routes/docs-viewer-public-routes.json" in recorded_paths


def test_scope_create_apply_skips_public_route_for_local_scopes() -> None:
    original_rebuild = docs_management_service.write_rebuild.rebuild_scope_outputs
    docs_management_service.write_rebuild.rebuild_scope_outputs = lambda *_args, **_kwargs: {"ok": True}
    try:
        with make_repo() as temp_path:
            repo_root = Path(temp_path)
            write_docs_scope_config(repo_root)
            payload = docs_management_service.handle_scope_create_apply(
                repo_root,
                {
                    "scope_id": "notes",
                    "title": "Notes",
                    "source_root": "docs-viewer/source/notes",
                    "default_doc_id": "notes",
                    "publishing_mode": "local_committed",
                    "public_route_path": "/notes/",
                    "confirm": True,
                },
                dry_run=False,
            )
            source_payload = json.loads((repo_root / "docs-viewer/config/scopes/docs_scopes.json").read_text(encoding="utf-8"))
            manifest_payload = json.loads((repo_root / "docs-viewer/config/scopes/docs_scope_manifest.json").read_text(encoding="utf-8"))
            default_doc_text = (repo_root / "docs-viewer/source/notes/notes.md").read_text(encoding="utf-8")
            route_exists = (repo_root / "notes/index.md").exists()
    finally:
        docs_management_service.write_rebuild.rebuild_scope_outputs = original_rebuild

    assert payload["ok"] is True
    assert payload["urls"]["public"] == ""
    assert route_exists is False
    assert "viewable:" not in default_doc_text
    assert "published:" not in default_doc_text
    assert "hidden:" not in default_doc_text
    assert source_payload["scopes"][1]["viewer_base_url"] == "/docs/"
    assert source_payload["scopes"][1]["include_scope_param"] is True
    assert source_payload["scopes"][1]["output"] == "docs-viewer/generated/docs/notes"
    assert source_payload["scopes"][1]["search_output"] == "docs-viewer/generated/search/notes/index.json"
    assert payload["storage_contract"]["public_static_assets"] is False
    records = {record["scope_id"]: record for record in manifest_payload["scopes"]}
    assert records["notes"]["scope_type"] == "local"
    assert any(file["path"] == "docs-viewer/generated/docs/notes" for file in records["notes"]["files"])
    assert any(file["path"] == "docs-viewer/generated/docs/notes/index-tree.json" for file in records["notes"]["files"])
    assert any(file["path"] == "docs-viewer/generated/docs/notes/recently-added.json" for file in records["notes"]["files"])
    assert any(file["path"] == "docs-viewer/generated/search/notes/index.json" for file in records["notes"]["files"])
    assert not any(file["kind"] == "route_file" for file in records["notes"]["files"])


def test_scope_delete_preview_blocks_system_scopes() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_docs_scope_config(repo_root)
        write_generated_docs(repo_root)
        payload = docs_management_service.docs_scope_manifest.plan_delete_scope_preview(
            repo_root,
            {
                "scope_id": "studio",
            },
        )

    assert payload["ok"] is True
    assert payload["allowed"] is False
    assert "system-owned" in payload["blockers"][0]


def test_scope_delete_preview_allows_public_user_created_scopes() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_docs_scope_config(repo_root)
        write_json(
            repo_root / "docs-viewer/config/scopes/docs_scope_manifest.json",
            {
                "schema_version": "docs_scope_manifest_v1",
                "tool_id": "docs-viewer-scope-lifecycle",
                "updated_at": "2026-06-12T00:00:00Z",
                "scopes": [
                    {
                        "scope_id": "research",
                        "scope_type": "public",
                        "owner": "user",
                        "user_created": True,
                        "created_by_tool": True,
                        "tool_id": "docs-viewer-scope-lifecycle",
                        "repo_status_at_creation": "tracked",
                        "created_at": "2026-06-12T00:00:00Z",
                        "updated_at": "2026-06-12T00:00:00Z",
                        "files": [],
                        "metadata": {"publishing_mode": "public_readonly"},
                    }
                ],
            },
        )
        payload = docs_management_service.docs_scope_manifest.plan_delete_scope_preview(
            repo_root,
            {
                "scope_id": "research",
            },
        )

    assert payload["ok"] is True
    assert payload["allowed"] is True
    assert payload["blockers"] == []


def test_scope_delete_preview_blocks_manage_route_default_scope() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_docs_scope_config(repo_root)
        write_json(
            repo_root / "docs-viewer/config/scopes/docs_scope_manifest.json",
            {
                "schema_version": "docs_scope_manifest_v1",
                "tool_id": "docs-viewer-scope-lifecycle",
                "updated_at": "2026-06-13T00:00:00Z",
                "scopes": [
                    {
                        "scope_id": "notes",
                        "scope_type": "local",
                        "owner": "user",
                        "user_created": True,
                        "created_by_tool": True,
                        "tool_id": "docs-viewer-scope-lifecycle",
                        "repo_status_at_creation": "tracked",
                        "created_at": "2026-06-13T00:00:00Z",
                        "updated_at": "2026-06-13T00:00:00Z",
                        "files": [],
                        "metadata": {"publishing_mode": "local_committed"},
                    }
                ],
            },
        )
        write_json(
            repo_root / "docs-viewer/config/routes/docs-viewer-routes.json",
            {
                "schema_version": "docs_viewer_route_config_registry_v1",
                "routes": [
                    {
                        "schema_version": "docs_viewer_route_config_v1",
                        "route_id": "docs-manage",
                        "route_path": "/docs/",
                        "default_scope_id": "notes",
                    }
                ],
            },
        )
        payload = docs_management_service.docs_scope_manifest.plan_delete_scope_preview(
            repo_root,
            {
                "scope_id": "notes",
            },
        )

    assert payload["ok"] is True
    assert payload["allowed"] is False
    assert payload["delete_files"] == []
    assert payload["changed_files"] == []
    assert "default scope for management route(s): docs-manage" in payload["blockers"][0]


def test_scope_delete_preview_keeps_config_as_changed_file() -> None:
    original_rebuild = docs_management_service.write_rebuild.rebuild_scope_outputs
    docs_management_service.write_rebuild.rebuild_scope_outputs = lambda *_args, **_kwargs: {"ok": True}
    try:
        with make_repo() as temp_path:
            repo_root = Path(temp_path)
            write_docs_scope_config(repo_root)
            docs_management_service.handle_scope_create_apply(
                repo_root,
                {
                    "scope_id": "notes",
                    "title": "Notes",
                    "source_root": "docs-viewer/source/notes",
                    "default_doc_id": "notes",
                    "publishing_mode": "local_committed",
                    "confirm": True,
                },
                dry_run=False,
            )
            payload = docs_management_service.docs_scope_manifest.plan_delete_scope_preview(
                repo_root,
                {
                    "scope_id": "notes",
                },
            )
    finally:
        docs_management_service.write_rebuild.rebuild_scope_outputs = original_rebuild

    assert payload["ok"] is True
    assert payload["allowed"] is True
    assert not any(file["kind"] == "scope_config" for file in payload["delete_files"])
    assert any(file["kind"] == "scope_config" for file in payload["changed_files"])
    assert any(file["path"] == "docs-viewer/source/notes" for file in payload["delete_files"])


def test_scope_delete_apply_requires_confirmation() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_docs_scope_config(repo_root)
        try:
            docs_management_service.handle_scope_delete_apply(
                repo_root,
                {
                    "scope_id": "studio",
                },
                dry_run=True,
            )
        except ValueError as exc:
            assert "confirm must be true" in str(exc)
        else:
            raise AssertionError("scope delete apply should require explicit confirmation")


def test_scope_delete_apply_removes_manifest_scope_and_runs_rebuild() -> None:
    create_calls: list[tuple[Path, str, dict[str, object]]] = []
    delete_calls: list[Path] = []
    original_create_rebuild = docs_management_service.write_rebuild.rebuild_scope_outputs
    original_delete_rebuild = docs_management_service.write_rebuild.rebuild_all_docs_outputs

    def fake_create_rebuild(repo_root: Path, scope: str, **kwargs):
        create_calls.append((repo_root, scope, kwargs))
        docs_output = repo_root / "docs-viewer/generated/docs" / scope
        (docs_output / "by-id").mkdir(parents=True)
        (docs_output / "index-tree.json").write_text("{}", encoding="utf-8")
        (docs_output / "recently-added.json").write_text("{}", encoding="utf-8")
        (docs_output / "by-id/research.json").write_text("{}", encoding="utf-8")
        search_output = repo_root / "docs-viewer/generated/search" / scope
        search_output.mkdir(parents=True)
        (search_output / "index.json").write_text("{}", encoding="utf-8")
        return {"ok": True}

    def fake_delete_rebuild(repo_root: Path):
        delete_calls.append(repo_root)
        return {"ok": True, "steps": [], "search": {"mode": "full", "doc_ids": []}}

    docs_management_service.write_rebuild.rebuild_scope_outputs = fake_create_rebuild
    docs_management_service.write_rebuild.rebuild_all_docs_outputs = fake_delete_rebuild
    try:
        with make_repo() as temp_path:
            repo_root = Path(temp_path)
            write_docs_scope_config(repo_root)
            docs_management_service.handle_scope_create_apply(
                repo_root,
                {
                    "scope_id": "research",
                    "title": "Research",
                    "source_root": "docs-viewer/source/research",
                    "default_doc_id": "research",
                    "publishing_mode": "local_committed",
                    "confirm": True,
                },
                dry_run=False,
            )
            config_path = repo_root / "docs-viewer/config/scopes/docs_scopes.json"
            created_source_payload = json.loads(config_path.read_text(encoding="utf-8"))
            created_source_payload["docs_viewer"]["ui_statuses_by_scope"]["research"] = [
                {"ui_status": "draft", "label": "Draft", "emoji": "D"},
            ]
            write_json(config_path, created_source_payload)
            payload = docs_management_service.handle_scope_delete_apply(
                repo_root,
                {
                    "scope_id": "research",
                    "confirm": True,
                },
                dry_run=False,
            )
            source_payload = json.loads((repo_root / "docs-viewer/config/scopes/docs_scopes.json").read_text(encoding="utf-8"))
            manifest_payload = json.loads((repo_root / "docs-viewer/config/scopes/docs_scope_manifest.json").read_text(encoding="utf-8"))
            source_root_exists = (repo_root / "docs-viewer/source/research").exists()
            route_exists = (repo_root / "research/index.md").exists()
            generated_docs_exists = (repo_root / "docs-viewer/generated/docs/research").exists()
            generated_search_exists = (repo_root / "docs-viewer/generated/search/research/index.json").exists()
    finally:
        docs_management_service.write_rebuild.rebuild_scope_outputs = original_create_rebuild
        docs_management_service.write_rebuild.rebuild_all_docs_outputs = original_delete_rebuild

    assert payload["ok"] is True
    assert payload["schema_version"] == "docs_scope_lifecycle_apply_v1"
    assert "backup_dir" not in payload
    assert delete_calls == [repo_root]
    assert create_calls == [(repo_root, "research", {"include_search": True})]
    assert [scope["scope_id"] for scope in source_payload["scopes"]] == ["studio"]
    assert "research" not in source_payload["docs_viewer"]["ui_statuses_by_scope"]
    assert "studio" in source_payload["docs_viewer"]["ui_statuses_by_scope"]
    assert "research" not in {record["scope_id"] for record in manifest_payload["scopes"]}
    assert source_root_exists is False
    assert route_exists is False
    assert generated_docs_exists is False
    assert generated_search_exists is False
    assert any(file["path"] == "docs-viewer/source/research" for file in payload["deleted_files"])


def test_scope_delete_apply_removes_user_created_public_route_and_payloads() -> None:
    create_calls: list[tuple[Path, str, dict[str, object]]] = []
    delete_calls: list[Path] = []
    original_create_rebuild = docs_management_service.write_rebuild.rebuild_scope_outputs
    original_delete_rebuild = docs_management_service.write_rebuild.rebuild_all_docs_outputs

    def fake_create_rebuild(repo_root: Path, scope: str, **kwargs):
        create_calls.append((repo_root, scope, kwargs))
        docs_output = repo_root / "docs-viewer/generated/docs" / scope
        (docs_output / "by-id").mkdir(parents=True)
        (docs_output / "index-tree.json").write_text("{}", encoding="utf-8")
        (docs_output / "recently-added.json").write_text("{}", encoding="utf-8")
        (docs_output / f"by-id/{scope}.json").write_text(json.dumps({"doc_id": scope}), encoding="utf-8")
        search_output = repo_root / "docs-viewer/generated/search" / scope
        search_output.mkdir(parents=True)
        (search_output / "index.json").write_text(json.dumps({"entries": []}), encoding="utf-8")
        return {"ok": True}

    def fake_delete_rebuild(repo_root: Path):
        delete_calls.append(repo_root)
        return {"ok": True, "steps": [], "search": {"mode": "full", "doc_ids": []}}

    docs_management_service.write_rebuild.rebuild_scope_outputs = fake_create_rebuild
    docs_management_service.write_rebuild.rebuild_all_docs_outputs = fake_delete_rebuild
    try:
        with make_repo() as temp_path:
            repo_root = Path(temp_path)
            write_docs_scope_config(repo_root)
            docs_management_service.handle_scope_create_apply(
                repo_root,
                {
                    "scope_id": "research",
                    "title": "Research",
                    "source_root": "docs-viewer/source/research",
                    "default_doc_id": "research",
                    "publishing_mode": "public_readonly",
                    "public_route_path": "/research/",
                    "confirm": True,
                },
                dry_run=False,
            )
            payload = docs_management_service.handle_scope_delete_apply(
                repo_root,
                {
                    "scope_id": "research",
                    "confirm": True,
                },
                dry_run=False,
            )
            source_payload = json.loads((repo_root / "docs-viewer/config/scopes/docs_scopes.json").read_text(encoding="utf-8"))
            public_routes = json.loads((repo_root / "site/docs-viewer/config/routes/docs-viewer-public-routes.json").read_text(encoding="utf-8"))
            all_routes = json.loads((repo_root / "docs-viewer/config/routes/docs-viewer-routes.json").read_text(encoding="utf-8"))
            route_exists = (repo_root / "site/research/index.html").exists()
            public_docs_exists = (repo_root / "site/assets/data/docs/scopes/research").exists()
            public_search_exists = (repo_root / "site/assets/data/search/research/index.json").exists()
            source_root_exists = (repo_root / "docs-viewer/source/research").exists()
    finally:
        docs_management_service.write_rebuild.rebuild_scope_outputs = original_create_rebuild
        docs_management_service.write_rebuild.rebuild_all_docs_outputs = original_delete_rebuild

    assert payload["ok"] is True
    assert delete_calls == [repo_root]
    assert create_calls == [(repo_root, "research", {"include_search": True})]
    assert [scope["scope_id"] for scope in source_payload["scopes"]] == ["studio"]
    assert public_routes["routes"] == []
    assert all_routes["routes"] == []
    assert route_exists is False
    assert public_docs_exists is False
    assert public_search_exists is False
    assert source_root_exists is False
    deleted_paths = {file["path"] for file in payload["deleted_files"]}
    assert "site/research/index.html" in deleted_paths
    assert "site/assets/data/docs/scopes/research" in deleted_paths
    assert "site/assets/data/search/research/index.json" in deleted_paths


def test_source_config_report_reads_known_config_files() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_docs_scope_config(repo_root)
        write_docs_viewer_browser_config(repo_root)
        write_generated_docs(repo_root)
        payload = docs_management_service.docs_source_config_report.build_source_config_report(repo_root)

    assert payload["ok"] is True
    assert payload["schema_version"] == "docs_source_config_report_v1"
    assert payload["source_config_path"] == "docs-viewer/config/scopes/docs_scopes.json"
    assert payload["scopes"][0]["scope_id"] == "studio"
    assert payload["scopes"][0]["source_config"]["source"] == "docs-viewer/source/studio"
    assert payload["scopes"][0]["browser_config"]["index_tree_url"] == "/docs-viewer/generated/docs/studio/index-tree.json"
    assert payload["scopes"][0]["browser_config"]["recently_added_url"] == "/docs-viewer/generated/docs/studio/recently-added.json"
    assert payload["scopes"][0]["generated"]["docs_index_tree"] == "docs-viewer/generated/docs/studio/index-tree.json"
    assert payload["scopes"][0]["generated"]["recently_added"] == "docs-viewer/generated/docs/studio/recently-added.json"
    assert payload["scopes"][0]["generated"]["search_index"] == "docs-viewer/generated/search/studio/index.json"
    assert payload["scopes"][0]["warnings"] == []


def test_source_config_settings_contract_has_no_editable_fields() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_docs_scope_config(repo_root)
        write_generated_docs(repo_root)
        payload = docs_management_service.docs_source_config_settings.build_settings_contract(repo_root, "studio")

    assert payload["ok"] is True
    assert payload["schema_version"] == "docs_source_config_settings_v1"
    assert payload["editable_scope_fields"] == []
    assert payload["deferred_global_fields"][0]["field"] == "recently_added_limit"
    assert any(field["field"] == "source" for field in payload["blocked_scope_fields"])
    scope = payload["scopes"][0]
    assert scope["scope_id"] == "studio"
    assert scope["fields"] == []


def test_source_config_settings_rejects_blocked_and_deferred_fields() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_docs_scope_config(repo_root)
        write_generated_docs(repo_root)

        try:
            docs_management_service.docs_source_config_settings.validate_scope_settings_change(
                repo_root,
                "studio",
                {"source": "_docs2"},
            )
        except ValueError as exc:
            assert "source" in str(exc)
        else:
            raise AssertionError("blocked source field should be rejected")

        try:
            docs_management_service.docs_source_config_settings.validate_scope_settings_change(
                repo_root,
                "studio",
                {"recently_added_limit": 12},
            )
        except ValueError as exc:
            assert "recently_added_limit" in str(exc)
        else:
            raise AssertionError("deferred global field should be rejected")


def test_docs_export_request_passes_target_format() -> None:
    calls: list[dict[str, object]] = []
    original_build_export = docs_data_sharing_package.build_export

    def fake_build_export(**kwargs):
        calls.append(kwargs)
        return {
            "ok": True,
            "target_format": kwargs["target_format"],
            "output_file": "var/analytics/data-sharing/exports/test.json",
            "output_written": False,
            "counts": {"selected": 1, "exported": 1, "skipped": 0, "failed": 0, "truncated": 0},
            "issue_counts": {"errors": 0, "warnings": 0},
        }

    docs_data_sharing_package.build_export = fake_build_export
    try:
        with make_repo() as temp_path:
            repo_root = Path(temp_path)
            adapter = analytics_data_sharing_api.data_sharing_service.resolve_for_service(repo_root, "documents", "prepare")
            result = documents_prepare.prepare_package(
                repo_root,
                {
                    "data_domain": "documents",
                    "config_id": "library-document-summaries",
                    "selection": {
                        "docs_scope": "studio",
                        "doc_ids": ["child"],
                        "select_all": False,
                        "missing_summary_only": False,
                    },
                    "target_format": "json",
                },
                dry_run=True,
                adapter=adapter,
                dependencies=analytics_data_sharing_api.documents_data_sharing_dependencies(),
            )
    finally:
        docs_data_sharing_package.build_export = original_build_export

    assert result["ok"] is True
    assert result["target_format"] == "json"
    assert calls[0]["target_format"] == "json"
    assert calls[0]["write"] is False


def main() -> None:
    tests = [
        test_hidden_doc_is_editable_in_dry_run,
        test_update_metadata_can_change_viewability_in_dry_run,
        test_hidden_doc_viewability_can_be_changed_in_dry_run,
        test_hidden_parent_delete_is_blocked_only_by_children,
        test_capabilities_advertise_generated_data_reads,
        test_capabilities_advertise_source_config_reads,
        test_scope_manifest_backfills_existing_scopes_as_system_owned,
        test_scope_create_preview_blocks_public_readonly_until_routes_are_data_driven,
        test_scope_create_preview_reports_local_tracked_outputs,
        test_docs_scope_config_requires_search_output,
        test_docs_scope_config_rejects_local_assets_outputs,
        test_docs_scope_config_requires_public_readonly_publish_outputs,
        test_scope_create_preview_blocks_local_tracked_assets_regression,
        test_scope_create_apply_blocks_local_tracked_assets_regression,
        test_scope_create_apply_requires_confirmation,
        test_scope_create_preview_requires_existing_external_docs_viewer_root,
        test_scope_create_apply_writes_allowlisted_files_and_runs_rebuild,
        test_scope_create_apply_skips_public_route_for_local_scopes,
        test_scope_delete_preview_blocks_system_scopes,
        test_scope_delete_preview_blocks_public_user_created_scopes,
        test_scope_delete_preview_keeps_config_as_changed_file,
        test_scope_delete_apply_requires_confirmation,
        test_scope_delete_apply_removes_manifest_scope_and_runs_rebuild,
        test_source_config_report_reads_known_config_files,
        test_source_config_settings_contract_allows_updated_date_only,
        test_source_config_settings_validation_reports_rebuild_artifact,
        test_source_config_settings_rejects_blocked_and_deferred_fields,
        test_source_config_settings_rejects_invalid_updated_date_value,
        test_source_config_settings_apply_writes_allowed_field,
        test_source_config_settings_apply_dry_run_does_not_write,
        test_source_config_settings_warns_when_generated_projection_is_stale,
        test_docs_export_request_passes_target_format,
    ]
    for test in tests:
        test()


if __name__ == "__main__":
    main()
