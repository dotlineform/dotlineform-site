#!/usr/bin/env python3
"""Smoke-check Docs Viewer management workflows against a fixture repo."""

from __future__ import annotations

import argparse
from dataclasses import replace
import json
import os
import shutil
import sys
import tempfile
import urllib.request
from pathlib import Path
from threading import Thread
from types import SimpleNamespace
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "docs-viewer" / "services"))

import docs_management_service  # noqa: E402
from docs_viewer_service import DocsViewerServer, DocsViewerServiceConfig  # noqa: E402


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_doc(path: Path, *, doc_id: str, title: str, parent_id: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "---",
                f"doc_id: {doc_id}",
                f"title: {title}",
                "added_date: 2026-05-22 00:00",
                "last_updated: 2026-05-22 00:00",
                f"parent_id: {parent_id}",
                "---",
                f"# {title}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def copy_scripts_fixture(target_root: Path) -> None:
    scripts_source = REPO_ROOT / "scripts"
    scripts_target = target_root / "scripts"
    if scripts_source.exists():
        shutil.copytree(
            scripts_source,
            scripts_target,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
    else:
        scripts_target.mkdir(parents=True, exist_ok=True)
    shutil.copytree(REPO_ROOT / "site" / "docs-viewer" / "runtime", target_root / "site" / "docs-viewer" / "runtime")
    shutil.copytree(REPO_ROOT / "site" / "docs-viewer" / "static", target_root / "site" / "docs-viewer" / "static")
    shutil.copytree(REPO_ROOT / "site" / "docs-viewer" / "config", target_root / "site" / "docs-viewer" / "config")
    shutil.copytree(REPO_ROOT / "docs-viewer" / "runtime", target_root / "docs-viewer" / "runtime")
    shutil.copytree(REPO_ROOT / "docs-viewer" / "static", target_root / "docs-viewer" / "static")
    shutil.copytree(REPO_ROOT / "docs-viewer" / "shell", target_root / "docs-viewer" / "shell")
    shutil.copytree(REPO_ROOT / "docs-viewer" / "config" / "ui-text", target_root / "docs-viewer" / "config" / "ui-text")
    shutil.copytree(REPO_ROOT / "docs-viewer" / "config" / "routes", target_root / "docs-viewer" / "config" / "routes")
    shutil.copytree(REPO_ROOT / "docs-viewer" / "config" / "reports", target_root / "docs-viewer" / "config" / "reports")
    (target_root / "docs-viewer" / "config" / "defaults").mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        REPO_ROOT / "docs-viewer" / "config" / "defaults" / "docs-viewer-service.json",
        target_root / "docs-viewer" / "config" / "defaults" / "docs-viewer-service.json",
    )


def write_docs_scope_config(target_root: Path) -> None:
    write_json(
        target_root / "docs-viewer/config/scopes/docs_scopes.json",
        {
            "schema_version": "docs_scopes_v1",
            "scopes": [
                {
                    "scope_id": "studio",
                    "scope_type": "local",
                    "meta": "local management",
                    "source": "docs-viewer/source/studio",
                    "media_path_prefix": "docs/studio",
                    "output": "docs-viewer/generated/docs/studio",
                    "search_output": "docs-viewer/generated/search/studio/index.json",
                    "viewer_base_url": "/docs/",
                    "include_scope_param": True,
                    "default_doc_id": "root-doc",
                    "non_loadable_doc_ids": [],
                    "manage_only_tree_root_ids": [],
                    "allow_unresolved_parent_ids": False,
                    "import_media_storage": {
                        "storage_mode": "staging_manual",
                        "repo_assets_path_prefix": "site/assets/docs/studio",
                        "repo_assets_public_path_prefix": "/assets/docs/studio",
                    },
                },
                {
                    "scope_id": "library",
                    "scope_type": "public",
                    "meta": "public scope",
                    "source": "docs-viewer/source/library",
                    "media_path_prefix": "docs/library",
                    "output": "docs-viewer/generated/docs/library",
                    "search_output": "docs-viewer/generated/search/library/index.json",
                    "publish_output": "site/assets/data/docs/scopes/library",
                    "publish_search_output": "site/assets/data/search/library/index.json",
                    "viewer_base_url": "/library/",
                    "include_scope_param": False,
                    "default_doc_id": "library",
                    "non_loadable_doc_ids": [],
                    "manage_only_tree_root_ids": [],
                    "allow_unresolved_parent_ids": False,
                    "import_media_storage": {
                        "storage_mode": "staging_manual",
                        "repo_assets_path_prefix": "site/assets/docs/library",
                        "repo_assets_public_path_prefix": "/assets/docs/library",
                    },
                },
                {
                    "scope_id": "analysis",
                    "scope_type": "public",
                    "meta": "public scope",
                    "source": "docs-viewer/source/analysis",
                    "media_path_prefix": "docs/analysis",
                    "output": "docs-viewer/generated/docs/analysis",
                    "search_output": "docs-viewer/generated/search/analysis/index.json",
                    "publish_output": "site/assets/data/docs/scopes/analysis",
                    "publish_search_output": "site/assets/data/search/analysis/index.json",
                    "viewer_base_url": "/analysis/",
                    "include_scope_param": False,
                    "default_doc_id": "analysis",
                    "non_loadable_doc_ids": [],
                    "manage_only_tree_root_ids": [],
                    "allow_unresolved_parent_ids": False,
                    "import_media_storage": {
                        "storage_mode": "staging_manual",
                        "repo_assets_path_prefix": "site/assets/docs/analysis",
                        "repo_assets_public_path_prefix": "/assets/docs/analysis",
                    },
                },
            ],
            "docs_viewer": {
                "recently_added_limit": 10,
                "ui_statuses_by_scope": {
                    "studio": [
                        {"ui_status": "draft", "label": "Draft", "emoji": "D"},
                        {"ui_status": "review", "label": "Review", "emoji": "R"},
                        {"ui_status": "done", "label": "Done", "emoji": "Y"},
                    ]
                },
            },
        },
    )


def write_browser_config(target_root: Path) -> None:
    write_json(
        target_root / "docs-viewer/config/defaults/docs-viewer-config.json",
        {
            "schema_version": "docs_viewer_config_v1",
            "default_scope_id": "studio",
            "scopes": [
                {
                    "scope_id": "studio",
                    "scope_type": "local",
                    "meta": "local management",
                    "viewer_base_url": "/docs/",
                    "include_scope_param": True,
                    "default_doc_id": "root-doc",
                    "media_path_prefix": "docs/studio",
                    "index_tree_url": "/docs-viewer/generated/docs/studio/index-tree.json",
                    "recently_added_url": "/docs-viewer/generated/docs/studio/recently-added.json",
                    "search_index_url": "/docs-viewer/generated/search/studio/index.json",
                },
                {
                    "scope_id": "library",
                    "scope_type": "public",
                    "meta": "public scope",
                    "viewer_base_url": "/library/",
                    "include_scope_param": False,
                    "default_doc_id": "library",
                    "media_path_prefix": "docs/library",
                    "index_tree_url": "/assets/data/docs/scopes/library/index-tree.json",
                    "recently_added_url": "/assets/data/docs/scopes/library/recently-added.json",
                    "search_index_url": "/assets/data/search/library/index.json",
                },
                {
                    "scope_id": "analysis",
                    "scope_type": "public",
                    "meta": "public scope",
                    "viewer_base_url": "/analysis/",
                    "include_scope_param": False,
                    "default_doc_id": "analysis",
                    "media_path_prefix": "docs/analysis",
                    "index_tree_url": "/assets/data/docs/scopes/analysis/index-tree.json",
                    "recently_added_url": "/assets/data/docs/scopes/analysis/recently-added.json",
                    "search_index_url": "/assets/data/search/analysis/index.json",
                },
            ],
            "docs_viewer": {"recently_added_limit": 10},
        },
    )


def refresh_browser_config_from_scope_config(target_root: Path) -> None:
    scope_payload = json.loads((target_root / "docs-viewer/config/scopes/docs_scopes.json").read_text(encoding="utf-8"))
    scopes = [scope for scope in scope_payload.get("scopes", []) if isinstance(scope, dict)]
    docs_viewer_settings = scope_payload.get("docs_viewer")
    if isinstance(docs_viewer_settings, dict):
        docs_viewer_settings = json.loads(json.dumps(docs_viewer_settings))
        statuses_by_scope = docs_viewer_settings.get("ui_statuses_by_scope")
        if isinstance(statuses_by_scope, dict):
            scope_ids = {str(scope.get("scope_id") or "") for scope in scopes}
            docs_viewer_settings["ui_statuses_by_scope"] = {
                scope_id: value for scope_id, value in statuses_by_scope.items() if scope_id in scope_ids
            }
    else:
        docs_viewer_settings = None
    def scope_generated_urls(scope: dict[str, Any]) -> dict[str, str]:
        scope_id = str(scope.get("scope_id") or "")
        if str(scope.get("scope_type") or "") == "local_external":
            return {
                "index_tree_url": f"/docs/generated/index-tree?scope={scope_id}",
                "recently_added_url": f"/docs/generated/recently-added?scope={scope_id}",
                "search_index_url": f"/docs/generated/search?scope={scope_id}",
            }
        return {
            "index_tree_url": f"/{str(scope.get('output') or '').strip('/')}/index-tree.json",
            "recently_added_url": f"/{str(scope.get('output') or '').strip('/')}/recently-added.json",
            "search_index_url": f"/{str(scope.get('search_output') or '').strip('/')}",
        }

    payload: dict[str, Any] = {
        "schema_version": "docs_viewer_config_v1",
        "default_scope_id": str(scopes[0].get("scope_id") or "") if scopes else "",
        "scopes": [
            {
                "scope_id": str(scope.get("scope_id") or ""),
                "scope_type": str(scope.get("scope_type") or ""),
                "meta": str(scope.get("meta") or ""),
                "viewer_base_url": str(scope.get("viewer_base_url") or "/docs/"),
                "include_scope_param": scope.get("include_scope_param") is True,
                "default_doc_id": str(scope.get("default_doc_id") or ""),
                "media_path_prefix": str(scope.get("media_path_prefix") or ""),
                **scope_generated_urls(scope),
                "search": {
                    "domain": "docs_viewer",
                    "schema": f"search_index_{scope.get('scope_id')}_v1",
                    "index_url": scope_generated_urls(scope)["search_index_url"],
                    "targeted_policy": "record_update",
                    "targeted_operations": ["create", "update", "delete"],
                },
            }
            for scope in scopes
        ],
    }
    if docs_viewer_settings is not None:
        payload["docs_viewer"] = docs_viewer_settings
    write_json(target_root / "docs-viewer/config/defaults/docs-viewer-config.json", payload)


def create_fixture_repo(target_root: Path) -> None:
    copy_scripts_fixture(target_root)
    (target_root / "site-tools/config").mkdir(parents=True, exist_ok=True); (target_root / "site-tools/config/site-tools.json").write_text("{\"schema_version\":\"site_tools_config_v1\"}\n", encoding="utf-8")
    write_docs_scope_config(target_root)
    write_browser_config(target_root)
    for scope, default_doc in {
        "studio": "root-doc",
        "library": "library",
        "analysis": "analysis",
    }.items():
        source_root = {
            "studio": "docs-viewer/source/studio",
            "library": "docs-viewer/source/library",
            "analysis": "docs-viewer/source/analysis",
        }[scope]
        write_doc(target_root / source_root / f"{default_doc}.md", doc_id=default_doc, title=default_doc.replace("-", " ").title())
    write_doc(target_root / "docs-viewer/source/studio" / "non-viewable-doc.md", doc_id="non-viewable-doc", title="Non-viewable Doc")
    write_doc(target_root / "docs-viewer/source/studio" / "sibling-doc.md", doc_id="sibling-doc", title="Sibling Doc")
    write_doc(target_root / "docs-viewer/source/studio" / "child-doc.md", doc_id="child-doc", title="Child Doc", parent_id="root-doc")
    (target_root / "var" / "docs" / "import-staging").mkdir(parents=True)
    (target_root / "var" / "docs" / "import-staging" / "staged-doc.md").write_text("# Staged Doc\n", encoding="utf-8")

    materialize_fixture_generated_docs(target_root, "studio")


def materialize_fixture_generated_docs(repo_root: Path, scope: str) -> None:
    source_model = docs_management_service.source_model
    configs = docs_management_service.docs_source_config_settings.load_docs_scope_configs(repo_root)
    config = configs[scope]
    try:
        docs = source_model.load_scope_docs(repo_root, scope)
    except (KeyError, ValueError):
        docs = []
        source_root = repo_root / config.source
        for path in sorted(source_root.glob("*.md")):
            front_matter, body = source_model.parse_source(path)
            doc_id = str(front_matter.get("doc_id") or path.stem).strip()
            title = str(front_matter.get("title") or source_model.humanize(doc_id or path.stem)).strip() or doc_id
            docs.append(
                SimpleNamespace(
                    doc_id=doc_id,
                    title=title,
                    front_matter=dict(front_matter),
                    ui_status=source_model.normalize_ui_status(front_matter.get("ui_status")),
                    parent_id=str(front_matter.get("parent_id") or "").strip(),
                    viewable=source_model.doc_is_viewable(front_matter),
                    body=body,
                )
            )
    output_root = repo_root / config.output
    docs_payload = []
    for doc in docs:
        content_url = (
            f"/docs/generated/payload?scope={scope}&doc_id={doc.doc_id}"
            if config.scope_type == "local_external"
            else f"/{(config.output / 'by-id' / f'{doc.doc_id}.json').as_posix()}"
        )
        docs_payload.append(
            {
                "doc_id": doc.doc_id,
                "title": doc.title,
                "summary": str(doc.front_matter.get("summary") or ""),
                "ui_status": doc.ui_status,
                "parent_id": doc.parent_id,
                "viewable": doc.viewable,
                "content_url": content_url,
            }
        )
        write_json(
            output_root / "by-id" / f"{doc.doc_id}.json",
            {
                "doc_id": doc.doc_id,
                "title": doc.title,
                "parent_id": doc.parent_id,
                "content_html": f"<h1 id=\"{doc.doc_id}\">{doc.title}</h1>",
            },
        )
    tree_nodes = {
        row["doc_id"]: {
            "doc_id": row["doc_id"],
            "title": row["title"],
            "content_url": row["content_url"],
            **({"ui_status": row["ui_status"]} if row.get("ui_status") else {}),
            **({"viewable": False} if row.get("viewable") is False else {}),
            "children": [],
        }
        for row in docs_payload
    }
    tree_docs = []
    for row in docs_payload:
        node = tree_nodes[row["doc_id"]]
        parent_id = str(row.get("parent_id") or "")
        if parent_id and parent_id in tree_nodes:
            tree_nodes[parent_id]["children"].append(node)
        else:
            tree_docs.append(node)
    for node in tree_nodes.values():
        if not node["children"]:
            node.pop("children", None)
    write_json(
        output_root / "index.json",
        {
            "viewer_options": {
                "default_doc_id": config.default_doc_id,
            },
            "docs": docs_payload,
        },
    )
    write_json(
        output_root / "index-tree.json",
        {
            "schema": "docs_index_tree_v1",
            "viewer_options": {
                "default_doc_id": config.default_doc_id,
            },
            "docs": tree_docs,
        },
    )
    write_json(
        output_root / "recently-added.json",
        {
            "schema": "docs_recently_added_v1",
            "docs": [
                {
                    **row,
                    "added_date": "2026-05-22",
                }
                for row in docs_payload
            ],
        },
    )
    write_json(output_root / "references" / "index.json", {"targets": []})
    write_json(repo_root / "site" / "assets" / "data" / "search" / scope / "index.json", {"entries": []})


def patch_rebuilds(repo_root: Path) -> None:
    def fake_rebuild_scope_outputs(
        _repo_root: Path,
        scope: str,
        include_search: bool = True,
        search_doc_ids: list[str] | None = None,
        docs_doc_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        materialize_fixture_generated_docs(_repo_root, scope)
        refresh_browser_config_from_scope_config(_repo_root)
        return {
            "ok": True,
            "fixture_rebuild": True,
            "scope": scope,
            "include_search": include_search,
            "search": {"mode": "targeted" if search_doc_ids else "none", "doc_ids": search_doc_ids or []},
            "docs": {"mode": "targeted" if docs_doc_ids else "full", "doc_ids": docs_doc_ids or []},
            "steps": [],
        }

    def fake_rebuild_all_docs_outputs(_repo_root: Path) -> dict[str, Any]:
        configs = docs_management_service.docs_source_config_settings.load_docs_scope_configs(_repo_root)
        for scope in sorted(configs):
            materialize_fixture_generated_docs(_repo_root, scope)
        return {
            "ok": True,
            "fixture_rebuild": True,
            "scope": "",
            "include_search": True,
            "search": {"mode": "full", "doc_ids": []},
            "docs": {"mode": "full", "doc_ids": []},
            "steps": [],
        }

    def fake_perform_source_write_and_rebuild(
        _repo_root: Path,
        scope: str,
        _changed_paths: list[Path],
        write_operation,
        *,
        include_search: bool = True,
        search_doc_ids: list[str] | None = None,
        docs_doc_ids: list[str] | None = None,
        **_kwargs: Any,
    ) -> dict[str, Any]:
        write_operation()
        return fake_rebuild_scope_outputs(
            _repo_root,
            scope,
            include_search=include_search,
            search_doc_ids=search_doc_ids,
            docs_doc_ids=docs_doc_ids,
        )

    def fake_validate_markdown_preview(markdown: str, *, title: str = "") -> dict[str, Any]:
        return {
            "ok": True,
            "html_chars": len(markdown),
            "renderer": "fixture-markdown-validator",
        }

    docs_management_service.write_rebuild.rebuild_scope_outputs = fake_rebuild_scope_outputs
    docs_management_service.write_rebuild.rebuild_all_docs_outputs = fake_rebuild_all_docs_outputs
    docs_management_service.write_rebuild.perform_source_write_and_rebuild = fake_perform_source_write_and_rebuild
    sys.modules["docs_html_import"].validate_markdown_preview = fake_validate_markdown_preview


def start_server(repo_root: Path) -> tuple[DocsViewerServer, str]:
    patch_rebuilds(repo_root)
    config = DocsViewerServiceConfig(
        host="127.0.0.1",
        port=0,
        base_url="http://127.0.0.1:0",
        management_enabled=True,
        generated_reads_enabled=True,
        watch_enabled=True,
    )
    server = DocsViewerServer(("127.0.0.1", 0), repo_root, config)
    base_url = f"http://127.0.0.1:{server.server_address[1]}"
    server.docs_viewer_config = replace(config, port=server.server_address[1], base_url=base_url)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, base_url


def request_json(base_url: str, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = json.dumps(payload or {}).encode("utf-8") if method == "POST" else None
    request = urllib.request.Request(
        f"{base_url}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def assert_ok(payload: dict[str, Any], label: str) -> None:
    if payload.get("ok") is not True:
        raise AssertionError(f"{label} failed: {payload!r}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)

    with tempfile.TemporaryDirectory(prefix="dlf-docs-workflow-") as tmp_dir:
        fixture_root = Path(tmp_dir) / "site"
        projects_root = Path(tmp_dir) / "external-docs-data"
        external_root = projects_root / "docs-viewer"
        external_root.mkdir(parents=True)
        old_projects_base = os.environ.get("DOTLINEFORM_PROJECTS_BASE_DIR")
        os.environ["DOTLINEFORM_PROJECTS_BASE_DIR"] = projects_root.as_posix()
        create_fixture_repo(fixture_root)
        server, base_url = start_server(fixture_root)
        try:
            settings = request_json(base_url, "GET", "/docs/source-config-settings?scope=studio")
            assert_ok(settings, "source config settings")
            if settings["scopes"][0]["scope_id"] != "studio":
                raise AssertionError(f"unexpected settings payload: {settings!r}")
            fields = settings["scopes"][0]["fields"]
            if [field.get("field") for field in settings["editable_scope_fields"]] != ["default_doc_id"]:
                raise AssertionError(f"settings payload should expose default_doc_id: {settings!r}")
            if len(fields) != 1 or fields[0].get("field") != "default_doc_id" or fields[0].get("current_value") != "root-doc":
                raise AssertionError(f"settings payload did not expose the active scope default doc id: {settings!r}")

            import_listing = request_json(base_url, "GET", "/docs/import-source-files")
            assert_ok(import_listing, "import source files")
            if not any(item.get("filename") == "staged-doc.md" for item in import_listing.get("files", [])):
                raise AssertionError(f"staged import file not listed: {import_listing!r}")

            created = request_json(
                base_url,
                "POST",
                "/docs/create",
                {"scope": "studio", "title": "API Smoke Created", "parent_id": ""},
            )
            assert_ok(created, "create")
            doc_id = str(created["doc_id"])
            created_path = fixture_root / str(created["path"])
            if doc_id != "api-smoke-created" or not created_path.exists():
                raise AssertionError(f"created doc was not written in fixture: {created!r}")

            metadata = request_json(
                base_url,
                "POST",
                "/docs/update-metadata",
                {
                    "scope": "studio",
                    "doc_id": doc_id,
                    "title": "API Smoke Renamed",
                    "summary": "workflow fixture",
                    "ui_status": "review",
                    "parent_id": "",
                    "viewable": True,
                },
            )
            assert_ok(metadata, "metadata update")
            if metadata["record"]["title"] != "API Smoke Renamed":
                raise AssertionError(f"metadata title did not update: {metadata!r}")

            moved = request_json(
                base_url,
                "POST",
                "/docs/move",
                {"scope": "studio", "doc_id": doc_id, "parent_id": "sibling-doc"},
            )
            assert_ok(moved, "move")
            if moved["record"]["parent_id"] != "sibling-doc":
                raise AssertionError(f"move changed parent unexpectedly: {moved!r}")

            delete_preview = request_json(
                base_url,
                "POST",
                "/docs/delete-preview",
                {"scope": "studio", "doc_id": doc_id},
            )
            assert_ok(delete_preview, "delete preview")
            if delete_preview.get("allowed") is not True:
                raise AssertionError(f"delete preview should be allowed for fixture doc: {delete_preview!r}")

            deleted = request_json(
                base_url,
                "POST",
                "/docs/delete-apply",
                {"scope": "studio", "doc_id": doc_id, "confirm": True},
            )
            assert_ok(deleted, "delete apply")
            created_path = fixture_root / "docs-viewer/source/studio/api-smoke-created.md"
            if created_path.exists():
                raise AssertionError(f"delete apply did not remove fixture source file: {created_path}")

            rebuild = request_json(
                base_url,
                "POST",
                "/docs/rebuild",
                {"scope": "studio"},
            )
            assert_ok(rebuild, "rebuild")
            if rebuild.get("fixture_rebuild") is not True:
                raise AssertionError(f"rebuild route did not use fixture rebuild: {rebuild!r}")

            scope_create_preview = request_json(
                base_url,
                "POST",
                "/docs/scopes/create-preview",
                {
                    "scope_id": "apismoke",
                    "title": "API Smoke Scope",
                    "default_doc_id": "apismoke",
                    "publishing_mode": "local_external",
                },
            )
            assert_ok(scope_create_preview, "scope create preview")
            if scope_create_preview.get("scope_id") != "apismoke":
                raise AssertionError(f"scope create preview returned unexpected payload: {scope_create_preview!r}")

            scope_created = request_json(
                base_url,
                "POST",
                "/docs/scopes/create-apply",
                {
                    "scope_id": "apismoke",
                    "title": "API Smoke Scope",
                    "default_doc_id": "apismoke",
                    "publishing_mode": "local_external",
                    "confirm": True,
                },
            )
            assert_ok(scope_created, "scope create apply")
            if not (external_root / "source/apismoke" / "apismoke.md").exists():
                raise AssertionError(f"scope create did not write fixture source: {scope_created!r}")

            scope_delete_preview = request_json(
                base_url,
                "POST",
                "/docs/scopes/delete-preview",
                {"scope_id": "apismoke"},
            )
            assert_ok(scope_delete_preview, "scope delete preview")
            if scope_delete_preview.get("allowed") is not True:
                raise AssertionError(f"scope delete preview should be allowed: {scope_delete_preview!r}")

            scope_deleted = request_json(
                base_url,
                "POST",
                "/docs/scopes/delete-apply",
                {"scope_id": "apismoke", "confirm": True},
            )
            assert_ok(scope_deleted, "scope delete apply")
            if (external_root / "source/apismoke").exists():
                raise AssertionError(f"scope delete did not remove fixture source root: {scope_deleted!r}")

            docs_config = (fixture_root / "docs-viewer" / "config" / "scopes" / "docs_scopes.json").read_text(encoding="utf-8")
            if "apismoke" in docs_config:
                raise AssertionError("scope delete did not remove fixture scope config")
            print(f"Docs Viewer service management workflows OK: {base_url}")
            return 0
        finally:
            server.shutdown()
            server.server_close()
            if old_projects_base is None:
                os.environ.pop("DOTLINEFORM_PROJECTS_BASE_DIR", None)
            else:
                os.environ["DOTLINEFORM_PROJECTS_BASE_DIR"] = old_projects_base


if __name__ == "__main__":
    raise SystemExit(main())
