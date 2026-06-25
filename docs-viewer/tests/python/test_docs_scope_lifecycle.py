#!/usr/bin/env python3
"""Docs scope lifecycle tests."""

from __future__ import annotations

import json
import os
from pathlib import Path

from docs_management_test_support import (
    EXTERNAL_DATA_ROOT_MARKER,
    docs_management_service,
    make_repo,
    write_docs_scope_config,
    write_generated_docs,
    write_json,
)

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
