#!/usr/bin/env python3
"""Focused checks for Docs Management service behavior."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_DIR = REPO_ROOT / "docs-viewer" / "services"
DOCS_MANAGEMENT_SERVICE_PATH = DOCS_DIR / "docs_management_service.py"
ANALYTICS_SERVER_DIR = REPO_ROOT / "analytics-app" / "app" / "server"
ANALYTICS_PACKAGE_DIR = ANALYTICS_SERVER_DIR / "analytics_app"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
for path in (ANALYTICS_SERVER_DIR, ANALYTICS_PACKAGE_DIR):
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
import analytics_data_sharing_api  # noqa: E402


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
    (repo_root / "_config.yml").write_text("title: test\n", encoding="utf-8")
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
                {"data_domain": "library", "operation": "prepare", "adapter_id": "documents"},
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
                            "label": "Library",
                            "scope": "library",
                            "status": "active",
                            "selection_model": "documents",
                            "paths": {
                                "outbound_package_root": "var/analytics/data-sharing/library/exports",
                                "returned_package_staging_root": "var/analytics/data-sharing/library/import-staging",
                                "review_output_root": "var/analytics/data-sharing/library/import-preview",
                                "source_root": "docs-viewer/source/library",
                            },
                            "source_write_targets": {
                                "documents": "docs-viewer/source/library",
                            },
                            "sources": {
                                "docs_payload_root": "assets/data/docs/scopes/library/by-id",
                                "source_root": "docs-viewer/source/library",
                            },
                            "config": {
                                "sharing_profiles_path": "data-sharing/config/library-export-configs.json",
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
                "show_updated_date": True,
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
                    "allow_nested_source": False,
                    "non_loadable_doc_ids": [],
                    "manage_only_tree_root_ids": [],
                    "show_updated_date": True,
                    "allow_unresolved_parent_ids": False,
                    "import_media_storage": {
                        "storage_mode": "staging_manual",
                        "repo_assets_path_prefix": "assets/docs/studio",
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
        old_docs_assets_exist = (repo_root / "assets/data/docs/scopes/studio/index.json").exists()
        old_search_assets_exist = (repo_root / "assets/data/search/studio/index.json").exists()

    assert old_docs_assets_exist is False
    assert old_search_assets_exist is False
    assert payload["capabilities"]["generated_data_reads"] is True
    assert payload["capabilities"]["scopes"]["studio"]["generated_data_reads"] is True
    assert payload["capabilities"]["scopes"]["studio"]["generated_search_reads"] is True


def test_generated_index_endpoint_is_retired_in_favor_of_index_tree() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_docs_scope_config(repo_root)
        write_generated_docs(repo_root)
        index_tree = docs_management_service.docs_management_get_payload(
            repo_root,
            "/docs/generated/index-tree",
            {"scope": ["studio"]},
        )
        try:
            docs_management_service.docs_management_get_payload(
                repo_root,
                "/docs/generated/index",
                {"scope": ["studio"]},
            )
        except FileNotFoundError:
            retired_missing = True
        else:
            retired_missing = False

    assert index_tree["schema"] == "docs_index_tree_v1"
    assert retired_missing is True


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


def test_scope_create_preview_reports_write_set_and_urls() -> None:
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
                "build_inline_search": True,
                "write_generated_outputs": True,
            },
        )

    assert payload["ok"] is True
    assert payload["scope_id"] == "research"
    assert payload["planned_scope_config"]["viewer_base_url"] == "/research/"
    assert payload["planned_scope_config"]["output"] == "assets/data/docs/scopes/research"
    assert payload["planned_scope_config"]["search_output"] == "assets/data/search/research/index.json"
    assert payload["storage_contract"]["public_static_assets"] is True
    assert "public static assets" in payload["storage_contract"]["summary"]
    assert payload["urls"]["management"] == "/docs/?scope=research&mode=manage"
    assert payload["urls"]["public"] == "/research/"
    assert any(file["path"] == "docs-viewer/source/research/research.md" for file in payload["created_files"])
    assert any(file["path"] == "assets/data/docs/scopes/research" for file in payload["created_files"])
    assert not any(file["path"] == "assets/data/docs/scopes/research/index.json" for file in payload["created_files"])
    assert any(file["path"] == "assets/data/docs/scopes/research/index-tree.json" for file in payload["created_files"])
    assert any(file["path"] == "assets/data/docs/scopes/research/recently-added.json" for file in payload["created_files"])
    assert any(file["path"] == "assets/data/search/research/index.json" for file in payload["created_files"])
    assert any(command["command"] == "./docs-viewer/build/build_docs.py --scope research --write" for command in payload["build_commands"])


def test_scope_create_preview_reports_committed_manage_mode_outputs() -> None:
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
                "build_inline_search": True,
                "write_generated_outputs": True,
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
    assert not any(file["path"].startswith("assets/data/docs/scopes/notes") for file in payload["created_files"])
    assert not any(file["path"].startswith("assets/data/search/notes") for file in payload["created_files"])


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


def test_docs_scope_config_rejects_manage_mode_assets_outputs() -> None:
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
                        "output": "assets/data/docs/scopes/studio",
                        "search_output": "assets/data/search/studio/index.json",
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
            assert "manage-mode scope 'studio'" in str(exc)
            assert "assets/data/docs/scopes" in str(exc)
        else:
            raise AssertionError("Expected manage-mode scope config to reject public generated asset roots")


def test_docs_scope_config_allows_public_readonly_assets_outputs() -> None:
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
                        "output": "assets/data/docs/scopes/research",
                        "search_output": "assets/data/search/research/index.json",
                        "viewer_base_url": "/research/",
                        "include_scope_param": False,
                        "default_doc_id": "research",
                    }
                ],
            },
        )
        configs = docs_scope_config.load_docs_scope_configs(repo_root)

    assert configs["research"].output.as_posix() == "assets/data/docs/scopes/research"
    assert configs["research"].search_output.as_posix() == "assets/data/search/research/index.json"


def test_scope_create_preview_blocks_committed_manage_mode_assets_regression() -> None:
    original_docs_output = docs_management_service.docs_scope_manifest.planned_docs_output
    original_search_output = docs_management_service.docs_scope_manifest.planned_search_output
    docs_management_service.docs_scope_manifest.planned_docs_output = lambda scope_id, _mode: Path("assets/data/docs/scopes") / scope_id
    docs_management_service.docs_scope_manifest.planned_search_output = (
        lambda scope_id, _mode: Path("assets/data/search") / scope_id / "index.json"
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
                assert "must not write generated docs under assets/data/docs/scopes" in str(exc)
            else:
                raise AssertionError("Expected committed manage-mode preview to reject assets output roots")
    finally:
        docs_management_service.docs_scope_manifest.planned_docs_output = original_docs_output
        docs_management_service.docs_scope_manifest.planned_search_output = original_search_output


def test_scope_create_apply_blocks_committed_manage_mode_assets_regression() -> None:
    original_docs_output = docs_management_service.docs_scope_manifest.planned_docs_output
    original_search_output = docs_management_service.docs_scope_manifest.planned_search_output
    docs_management_service.docs_scope_manifest.planned_docs_output = lambda scope_id, _mode: Path("assets/data/docs/scopes") / scope_id
    docs_management_service.docs_scope_manifest.planned_search_output = (
        lambda scope_id, _mode: Path("assets/data/search") / scope_id / "index.json"
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
                assert "must not write generated docs under assets/data/docs/scopes" in str(exc)
            else:
                raise AssertionError("Expected committed manage-mode apply to reject assets output roots")
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
                    "build_inline_search": True,
                    "write_generated_outputs": True,
                    "confirm": True,
                },
                dry_run=False,
            )
            source_payload = json.loads((repo_root / "docs-viewer/config/scopes/docs_scopes.json").read_text(encoding="utf-8"))
            manifest_payload = json.loads((repo_root / "docs-viewer/config/scopes/docs_scope_manifest.json").read_text(encoding="utf-8"))
            default_doc_exists = (repo_root / "docs-viewer/source/research/research.md").exists()
            default_doc_text = (repo_root / "docs-viewer/source/research/research.md").read_text(encoding="utf-8")
            route_text = (repo_root / "research/index.md").read_text(encoding="utf-8")
    finally:
        docs_management_service.write_rebuild.rebuild_scope_outputs = original_rebuild

    assert payload["ok"] is True
    assert payload["schema_version"] == "docs_scope_lifecycle_apply_v1"
    assert "backup_dir" not in payload
    assert payload["build_commands"][0]["status"] == "completed"
    assert calls == [(repo_root, "research", {"include_search": True})]
    assert default_doc_exists is True
    assert "viewable:" not in default_doc_text
    assert "published:" not in default_doc_text
    assert "hidden:" not in default_doc_text
    assert "permalink: /research/" in route_text
    assert "docs_viewer_readonly_route.html" in route_text
    assert "docs_viewer_management_route.html" not in route_text
    assert "allow_management" not in route_text
    assert "docs-viewer/runtime/js/docs-viewer-manage.js" not in route_text
    assert "docs-viewer/static/css/docs-viewer-manage.css" not in route_text
    assert "docs-viewer/static/css/docs-viewer-reports.css" not in route_text
    assert source_payload["scopes"][1]["scope_id"] == "research"
    assert source_payload["scopes"][1]["viewer_base_url"] == "/research/"
    assert source_payload["scopes"][1]["output"] == "assets/data/docs/scopes/research"
    assert source_payload["scopes"][1]["search_output"] == "assets/data/search/research/index.json"
    assert source_payload["scopes"][1]["include_scope_param"] is False
    records = {record["scope_id"]: record for record in manifest_payload["scopes"]}
    assert records["research"]["user_created"] is True
    assert records["research"]["created_by_tool"] is True
    recorded_paths = {file["path"] for file in records["research"]["files"]}
    assert "assets/data/docs/scopes/research/index-tree.json" in recorded_paths
    assert "assets/data/docs/scopes/research/recently-added.json" in recorded_paths
    assert any(file["path"] == "docs-viewer/config/scopes/docs_scopes.json" for file in records["research"]["files"])
    assert any(file["path"] == "research/index.md" and file["kind"] == "route_file" for file in records["research"]["files"])
    assert "docs-viewer/runtime/js/docs-viewer-public.js" not in recorded_paths
    assert "docs-viewer/runtime/js/docs-viewer-manage.js" not in recorded_paths
    assert "docs-viewer/static/css/docs-viewer.css" not in recorded_paths
    assert "docs-viewer/static/css/docs-viewer-manage.css" not in recorded_paths
    assert "docs-viewer/config/routes/docs-viewer-public-routes.json" not in recorded_paths


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
            payload = docs_management_service.docs_scope_manifest.plan_delete_scope_preview(
                repo_root,
                {
                    "scope_id": "research",
                },
            )
    finally:
        docs_management_service.write_rebuild.rebuild_scope_outputs = original_rebuild

    assert payload["ok"] is True
    assert payload["allowed"] is True
    assert not any(file["kind"] == "scope_config" for file in payload["delete_files"])
    assert any(file["kind"] == "scope_config" for file in payload["changed_files"])
    assert any(file["path"] == "docs-viewer/source/research" for file in payload["delete_files"])


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
        docs_output = repo_root / "assets/data/docs/scopes" / scope
        (docs_output / "by-id").mkdir(parents=True)
        (docs_output / "index.json").write_text("{}", encoding="utf-8")
        (docs_output / "by-id/research.json").write_text("{}", encoding="utf-8")
        search_output = repo_root / "assets/data/search" / scope
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
                    "publishing_mode": "public_readonly",
                    "public_route_path": "/research/",
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
            generated_docs_exists = (repo_root / "assets/data/docs/scopes/research").exists()
            generated_search_exists = (repo_root / "assets/data/search/research/index.json").exists()
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
    assert payload["scopes"][0]["viewer_options"]["show_updated_date"] is True
    assert payload["scopes"][0]["warnings"] == []


def test_source_config_settings_contract_allows_updated_date_only() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_docs_scope_config(repo_root)
        write_generated_docs(repo_root)
        payload = docs_management_service.docs_source_config_settings.build_settings_contract(repo_root, "studio")

    assert payload["ok"] is True
    assert payload["schema_version"] == "docs_source_config_settings_v1"
    assert [field["field"] for field in payload["editable_scope_fields"]] == ["show_updated_date"]
    assert payload["deferred_global_fields"][0]["field"] == "recently_added_limit"
    assert any(field["field"] == "source" for field in payload["blocked_scope_fields"])
    scope = payload["scopes"][0]
    assert scope["scope_id"] == "studio"
    assert scope["fields"][0]["field"] == "show_updated_date"
    assert scope["fields"][0]["current_value"] is True
    assert scope["fields"][0]["generated_value"] is True
    assert scope["fields"][0]["warnings"] == []


def test_source_config_settings_validation_reports_rebuild_artifact() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_docs_scope_config(repo_root)
        write_generated_docs(repo_root)
        payload = docs_management_service.docs_source_config_settings.validate_scope_settings_change(
            repo_root,
            "studio",
            {"show_updated_date": False},
        )

    assert payload["ok"] is True
    assert payload["requires_rebuild"] is True
    assert payload["changes"]["show_updated_date"]["current_value"] is True
    assert payload["changes"]["show_updated_date"]["proposed_value"] is False
    assert payload["affected_artifacts"] == ["docs-viewer/generated/docs/studio/index-tree.json"]
    assert any("requires rebuilding" in warning for warning in payload["warnings"])


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


def test_source_config_settings_rejects_invalid_updated_date_value() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_docs_scope_config(repo_root)
        write_generated_docs(repo_root)

        try:
            docs_management_service.docs_source_config_settings.validate_scope_settings_change(
                repo_root,
                "studio",
                {"show_updated_date": "false"},
            )
        except ValueError as exc:
            assert "must be a boolean" in str(exc)
        else:
            raise AssertionError("non-boolean show_updated_date should be rejected")


def test_source_config_settings_apply_writes_allowed_field() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_docs_scope_config(repo_root)
        write_generated_docs(repo_root)

        result = docs_management_service.docs_source_config_settings.apply_scope_settings_change(
            repo_root,
            "studio",
            {"show_updated_date": False},
        )
        source_payload = json.loads((repo_root / "docs-viewer/config/scopes/docs_scopes.json").read_text(encoding="utf-8"))

    assert result["ok"] is True
    assert result["changed"] is True
    assert result["requires_rebuild"] is True
    assert source_payload["scopes"][0]["show_updated_date"] is False


def test_source_config_settings_apply_dry_run_does_not_write() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_docs_scope_config(repo_root)
        write_generated_docs(repo_root)

        result = docs_management_service.docs_source_config_settings.apply_scope_settings_change(
            repo_root,
            "studio",
            {"show_updated_date": False},
            dry_run=True,
        )
        source_payload = json.loads((repo_root / "docs-viewer/config/scopes/docs_scopes.json").read_text(encoding="utf-8"))

    assert result["ok"] is True
    assert result["changed"] is True
    assert source_payload["scopes"][0]["show_updated_date"] is True


def test_source_config_settings_warns_when_generated_projection_is_stale() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_docs_scope_config(repo_root)
        write_generated_docs(repo_root)
        index_path = repo_root / "docs-viewer/generated/docs/studio/index-tree.json"
        payload = json.loads(index_path.read_text(encoding="utf-8"))
        payload["viewer_options"]["show_updated_date"] = False
        write_json(index_path, payload)

        result = docs_management_service.docs_source_config_settings.build_settings_contract(repo_root, "studio")

    warnings = result["scopes"][0]["fields"][0]["warnings"]
    assert any("does not match source config" in warning for warning in warnings)


def test_docs_export_request_passes_target_format() -> None:
    calls: list[dict[str, object]] = []
    original_build_export = docs_data_sharing_package.build_export

    def fake_build_export(**kwargs):
        calls.append(kwargs)
        return {
            "ok": True,
            "target_format": kwargs["target_format"],
            "output_file": "var/analytics/data-sharing/library/exports/test.json",
            "output_written": False,
            "counts": {"selected": 1, "exported": 1, "skipped": 0, "failed": 0, "truncated": 0},
            "issue_counts": {"errors": 0, "warnings": 0},
        }

    docs_data_sharing_package.build_export = fake_build_export
    try:
        with make_repo() as temp_path:
            repo_root = Path(temp_path)
            adapter = analytics_data_sharing_api.data_sharing_service.resolve_for_service(repo_root, "library", "prepare")
            result = analytics_data_sharing_api.documents_data_sharing_adapter.prepare_package(
                repo_root,
                {
                    "data_domain": "library",
                    "config_id": "library-document-summaries",
                    "doc_ids": ["library"],
                    "select_all": False,
                    "missing_summary_only": False,
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
        test_generated_index_endpoint_is_retired_in_favor_of_index_tree,
        test_capabilities_advertise_source_config_reads,
        test_scope_manifest_backfills_existing_scopes_as_system_owned,
        test_scope_create_preview_reports_write_set_and_urls,
        test_scope_create_preview_reports_committed_manage_mode_outputs,
        test_docs_scope_config_requires_search_output,
        test_docs_scope_config_rejects_manage_mode_assets_outputs,
        test_docs_scope_config_allows_public_readonly_assets_outputs,
        test_scope_create_preview_blocks_committed_manage_mode_assets_regression,
        test_scope_create_apply_blocks_committed_manage_mode_assets_regression,
        test_scope_create_apply_requires_confirmation,
        test_scope_create_apply_writes_allowlisted_files_and_runs_rebuild,
        test_scope_create_apply_skips_public_route_for_local_scopes,
        test_scope_delete_preview_blocks_system_scopes,
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
