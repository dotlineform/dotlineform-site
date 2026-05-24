#!/usr/bin/env python3
"""Focused checks for Docs Management service behavior."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_DIR = REPO_ROOT / "studio" / "docs-viewer" / "services"
DOCS_MANAGEMENT_SERVICE_PATH = DOCS_DIR / "docs_management_service.py"


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
docs_source_model = sys.modules["docs_source_model"]


def write_doc(root: Path, filename: str, front_matter: dict[str, object], body: str = "") -> None:
    lines = ["---"]
    for key, value in front_matter.items():
        lines.append(f"{key}: {docs_source_model.format_front_matter_value(value)}")
    lines.extend(["---", "", body or f"# {front_matter['title']}", ""])
    path = root / "studio/docs-viewer/source/studio" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def make_repo() -> tempfile.TemporaryDirectory[str]:
    temp_dir = tempfile.TemporaryDirectory()
    repo_root = Path(temp_dir.name)
    (repo_root / "_config.yml").write_text("title: test\n", encoding="utf-8")
    write_doc(
        repo_root,
        "archive.md",
        {
            "doc_id": "archive",
            "title": "Archive",
            "published": True,
            "viewable": False,
        },
    )
    write_doc(
        repo_root,
        "child.md",
        {
            "doc_id": "child",
            "title": "Child",
            "parent_id": "archive",
            "published": True,
            "viewable": True,
        },
    )
    write_doc(
        repo_root,
        "other.md",
        {
            "doc_id": "other",
            "title": "Other",
            "published": True,
            "viewable": True,
        },
    )
    write_json(
        repo_root / "studio/data/config/data-sharing/data-sharing-adapters.json",
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
                                "outbound_package_root": "var/studio/data-sharing/library/exports",
                                "returned_package_staging_root": "var/studio/data-sharing/library/import-staging",
                                "review_output_root": "var/studio/data-sharing/library/import-preview",
                                "source_root": "studio/docs-viewer/source/library",
                                "backup_root": "var/docs/backups",
                            },
                            "source_write_targets": {
                                "documents": "studio/docs-viewer/source/library",
                            },
                            "sources": {
                                "docs_index": "assets/data/docs/scopes/library/index.json",
                                "docs_payload_root": "assets/data/docs/scopes/library/by-id",
                                "source_root": "studio/docs-viewer/source/library",
                            },
                            "config": {
                                "sharing_profiles_path": "studio/data/config/data-sharing/library-export-configs.json",
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
            "doc_id": "archive",
            "title": "Archive",
            "published": True,
            "viewable": False,
            "content_url": "/assets/data/docs/scopes/studio/by-id/archive.json",
        },
        {
            "scope": "studio",
            "doc_id": "child",
            "title": "Child",
            "published": True,
            "viewable": True,
            "content_url": "/assets/data/docs/scopes/studio/by-id/child.json",
        },
    ]
    write_json(
        root / "assets/data/docs/scopes/studio/index.json",
        {
            "viewer_options": {
                "show_updated_date": True,
                "non_loadable_doc_ids": [],
                "manage_only_tree_root_ids": [],
            },
            "docs": docs,
        },
    )
    write_json(root / "assets/data/docs/scopes/studio/by-id/archive.json", {"doc_id": "archive"})
    write_json(root / "assets/data/docs/scopes/studio/by-id/child.json", {"doc_id": "child"})
    write_json(root / "assets/data/search/studio/index.json", {"entries": [{"doc_id": "child"}]})


def write_docs_scope_config(root: Path) -> None:
    write_json(
        root / "studio/docs-viewer/config/scopes/docs_scopes.json",
        {
            "schema_version": "docs_scopes_v1",
            "scopes": [
                {
                    "scope_id": "studio",
                    "source": "studio/docs-viewer/source/studio",
                    "media_path_prefix": "docs/studio",
                    "output": "assets/data/docs/scopes/studio",
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
            },
        },
    )


def write_docs_viewer_browser_config(root: Path) -> None:
    write_json(
        root / "studio/docs-viewer/config/runtime/docs-viewer-config.json",
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
                    "index_url": "/assets/data/docs/scopes/studio/index.json",
                    "search_index_url": "/assets/data/search/studio/index.json",
                }
            ],
            "docs_viewer": {
                "recently_added_limit": 10,
            },
        },
    )


def test_archive_doc_is_editable_in_dry_run() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        result = docs_management_service.handle_update_metadata(
            repo_root,
            {
                "scope": "studio",
                "doc_id": "archive",
                "title": "Archive",
                "parent_id": "",
                "sort_order": 30,
            },
            dry_run=True,
        )

    assert result["ok"] is True
    assert result["doc_id"] == "archive"
    assert result["record"]["sort_order"] == 30


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
                "sort_order": "",
                "ui_status": "",
                "viewable": False,
            },
            dry_run=True,
        )

    assert result["ok"] is True
    assert result["record"]["viewable"] is False
    assert result["changes"]["viewable_changed"] is True
    assert result["changes"]["status_changed"] is False


def test_archive_doc_viewability_can_be_changed_in_dry_run() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        result = docs_management_service.handle_update_viewability(
            repo_root,
            {
                "scope": "studio",
                "doc_id": "archive",
                "viewable": True,
            },
            dry_run=True,
        )

    assert result["ok"] is True
    assert result["changed_doc_ids"] == ["archive"]
    assert result["records"][0]["viewable"] is True


def test_archive_parent_delete_is_blocked_only_by_children() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        result = docs_management_mutations.plan_delete_preview(repo_root, "studio", "archive")

    assert result["allowed"] is False
    assert result["blockers"] == ["1 child docs still depend on this parent"]


def test_archive_command_noops_on_archive_parent() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        result = docs_management_service.handle_archive(
            repo_root,
            {
                "scope": "studio",
                "doc_id": "archive",
            },
            dry_run=True,
        )

    assert result["ok"] is True
    assert result["doc_id"] == "archive"
    assert "not changed" in result["summary_text"]


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
    assert any(file["path"] == "studio/docs-viewer/source/studio/child.md" for file in records["studio"]["files"])


def test_scope_create_preview_reports_write_set_and_urls() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_docs_scope_config(repo_root)
        payload = docs_management_service.docs_scope_manifest.plan_create_scope_preview(
            repo_root,
            {
                "scope_id": "research",
                "title": "Research",
                "source_root": "studio/docs-viewer/source/research",
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
    assert payload["urls"]["management"] == "/docs/?scope=research&mode=manage"
    assert payload["urls"]["public"] == "/research/"
    assert any(file["path"] == "studio/docs-viewer/source/research/research.md" for file in payload["created_files"])
    assert any(command["command"] == "./scripts/build_docs.rb --scope research --write" for command in payload["build_commands"])


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
                    "source_root": "studio/docs-viewer/source/research",
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
                    "source_root": "studio/docs-viewer/source/research",
                    "default_doc_id": "research",
                    "publishing_mode": "public_readonly",
                    "public_route_path": "/research/",
                    "build_inline_search": True,
                    "write_generated_outputs": True,
                    "confirm": True,
                },
                dry_run=False,
            )
            source_payload = json.loads((repo_root / "studio/docs-viewer/config/scopes/docs_scopes.json").read_text(encoding="utf-8"))
            manifest_payload = json.loads((repo_root / "studio/docs-viewer/config/scopes/docs_scope_manifest.json").read_text(encoding="utf-8"))
            default_doc_exists = (repo_root / "studio/docs-viewer/source/research/research.md").exists()
            route_exists = (repo_root / "research/index.md").exists()
    finally:
        docs_management_service.write_rebuild.rebuild_scope_outputs = original_rebuild

    assert payload["ok"] is True
    assert payload["schema_version"] == "docs_scope_lifecycle_apply_v1"
    assert payload["backup_dir"].startswith("var/docs/backups/")
    assert payload["build_commands"][0]["status"] == "completed"
    assert calls == [(repo_root, "research", {"include_search": True})]
    assert default_doc_exists is True
    assert route_exists is True
    assert source_payload["scopes"][1]["scope_id"] == "research"
    records = {record["scope_id"]: record for record in manifest_payload["scopes"]}
    assert records["research"]["user_created"] is True
    assert records["research"]["created_by_tool"] is True
    assert any(file["path"] == "studio/docs-viewer/config/scopes/docs_scopes.json" for file in records["research"]["files"])


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
                    "source_root": "studio/docs-viewer/source/research",
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
    assert any(file["path"] == "studio/docs-viewer/source/research" for file in payload["delete_files"])


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
                    "source_root": "studio/docs-viewer/source/research",
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
            source_payload = json.loads((repo_root / "studio/docs-viewer/config/scopes/docs_scopes.json").read_text(encoding="utf-8"))
            manifest_payload = json.loads((repo_root / "studio/docs-viewer/config/scopes/docs_scope_manifest.json").read_text(encoding="utf-8"))
            source_root_exists = (repo_root / "studio/docs-viewer/source/research").exists()
            route_exists = (repo_root / "research/index.md").exists()
            generated_docs_exists = (repo_root / "assets/data/docs/scopes/research").exists()
            generated_search_exists = (repo_root / "assets/data/search/research/index.json").exists()
    finally:
        docs_management_service.write_rebuild.rebuild_scope_outputs = original_create_rebuild
        docs_management_service.write_rebuild.rebuild_all_docs_outputs = original_delete_rebuild

    assert payload["ok"] is True
    assert payload["schema_version"] == "docs_scope_lifecycle_apply_v1"
    assert payload["backup_dir"].startswith("var/docs/backups/")
    assert delete_calls == [repo_root]
    assert create_calls == [(repo_root, "research", {"include_search": True})]
    assert [scope["scope_id"] for scope in source_payload["scopes"]] == ["studio"]
    assert "research" not in {record["scope_id"] for record in manifest_payload["scopes"]}
    assert source_root_exists is False
    assert route_exists is False
    assert generated_docs_exists is False
    assert generated_search_exists is False
    assert any(file["path"] == "studio/docs-viewer/source/research" for file in payload["deleted_files"])


def test_source_config_report_reads_known_config_files() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_docs_scope_config(repo_root)
        write_docs_viewer_browser_config(repo_root)
        write_generated_docs(repo_root)
        payload = docs_management_service.docs_source_config_report.build_source_config_report(repo_root)

    assert payload["ok"] is True
    assert payload["schema_version"] == "docs_source_config_report_v1"
    assert payload["source_config_path"] == "studio/docs-viewer/config/scopes/docs_scopes.json"
    assert payload["scopes"][0]["scope_id"] == "studio"
    assert payload["scopes"][0]["source_config"]["source"] == "studio/docs-viewer/source/studio"
    assert payload["scopes"][0]["browser_config"]["index_url"] == "/assets/data/docs/scopes/studio/index.json"
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
    assert payload["affected_artifacts"] == ["assets/data/docs/scopes/studio/index.json"]
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
        source_payload = json.loads((repo_root / "studio/docs-viewer/config/scopes/docs_scopes.json").read_text(encoding="utf-8"))

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
        source_payload = json.loads((repo_root / "studio/docs-viewer/config/scopes/docs_scopes.json").read_text(encoding="utf-8"))

    assert result["ok"] is True
    assert result["changed"] is True
    assert source_payload["scopes"][0]["show_updated_date"] is True


def test_source_config_settings_warns_when_generated_projection_is_stale() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_docs_scope_config(repo_root)
        write_generated_docs(repo_root)
        index_path = repo_root / "assets/data/docs/scopes/studio/index.json"
        payload = json.loads(index_path.read_text(encoding="utf-8"))
        payload["viewer_options"]["show_updated_date"] = False
        write_json(index_path, payload)

        result = docs_management_service.docs_source_config_settings.build_settings_contract(repo_root, "studio")

    warnings = result["scopes"][0]["fields"][0]["warnings"]
    assert any("does not match source config" in warning for warning in warnings)


def test_docs_export_request_passes_target_format() -> None:
    calls: list[dict[str, object]] = []
    original_build_export = docs_management_service.documents_data_sharing_adapter.build_export

    def fake_build_export(**kwargs):
        calls.append(kwargs)
        return {
            "ok": True,
            "target_format": kwargs["target_format"],
            "output_file": "var/studio/data-sharing/library/exports/test.json",
            "output_written": False,
            "counts": {"selected": 1, "exported": 1, "skipped": 0, "failed": 0, "truncated": 0},
            "issue_counts": {"errors": 0, "warnings": 0},
        }

    docs_management_service.documents_data_sharing_adapter.build_export = fake_build_export
    try:
        with make_repo() as temp_path:
            repo_root = Path(temp_path)
            result = docs_management_service.documents_data_sharing_adapter.prepare_package(
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
                dependencies=docs_management_service.documents_data_sharing_dependencies(),
            )
    finally:
        docs_management_service.documents_data_sharing_adapter.build_export = original_build_export

    assert result["ok"] is True
    assert result["target_format"] == "json"
    assert calls[0]["target_format"] == "json"
    assert calls[0]["write"] is False


def main() -> None:
    tests = [
        test_archive_doc_is_editable_in_dry_run,
        test_update_metadata_can_change_viewability_in_dry_run,
        test_archive_doc_viewability_can_be_changed_in_dry_run,
        test_archive_parent_delete_is_blocked_only_by_children,
        test_archive_command_noops_on_archive_parent,
        test_capabilities_advertise_generated_data_reads,
        test_capabilities_advertise_source_config_reads,
        test_scope_manifest_backfills_existing_scopes_as_system_owned,
        test_scope_create_preview_reports_write_set_and_urls,
        test_scope_create_apply_requires_confirmation,
        test_scope_create_apply_writes_allowlisted_files_and_runs_rebuild,
        test_scope_delete_preview_blocks_system_scopes,
        test_scope_delete_preview_keeps_config_as_changed_file,
        test_scope_delete_apply_requires_confirmation,
        test_scope_delete_apply_removes_manifest_scope_and_runs_rebuild,
        test_source_config_report_reads_known_config_files,
        test_source_config_settings_contract_allows_updated_date_only,
        test_source_config_settings_validation_reports_rebuild_artifact,
        test_source_config_settings_rejects_blocked_and_deferred_fields,
        test_source_config_settings_rejects_invalid_updated_date_value,
        test_source_config_settings_warns_when_generated_projection_is_stale,
        test_json_responses_are_not_cached,
        test_docs_export_request_passes_target_format,
    ]
    for test in tests:
        test()


if __name__ == "__main__":
    main()
