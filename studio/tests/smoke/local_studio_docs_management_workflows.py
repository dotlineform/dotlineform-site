#!/usr/bin/env python3
"""Smoke-check local Studio Docs management workflows against a fixture repo."""

from __future__ import annotations

import argparse
import json
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

from studio.app.server.studio import studio_docs_api  # noqa: E402
from studio.app.server.studio.studio_app_server import StudioAppServer  # noqa: E402


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_doc(path: Path, *, doc_id: str, title: str, parent_id: str = "", sort_order: int = 1000) -> None:
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
                f"sort_order: {sort_order}",
                "published: true",
                "viewable: true",
                "---",
                f"# {title}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def copy_scripts_fixture(target_root: Path) -> None:
    shutil.copytree(
        REPO_ROOT / "scripts",
        target_root / "scripts",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    (target_root / "_includes").mkdir(parents=True, exist_ok=True)
    shutil.copy2(REPO_ROOT / "_includes" / "docs_viewer_shell.html", target_root / "_includes" / "docs_viewer_shell.html")
    shutil.copytree(REPO_ROOT / "assets" / "docs-viewer", target_root / "assets" / "docs-viewer")
    shutil.copytree(REPO_ROOT / "assets" / "studio", target_root / "assets" / "studio")
    (target_root / "assets" / "css").mkdir(parents=True, exist_ok=True)
    shutil.copy2(REPO_ROOT / "assets" / "css" / "main.css", target_root / "assets" / "css" / "main.css")
    reports_path = REPO_ROOT / "assets" / "data" / "docs" / "reports.json"
    if reports_path.exists():
        (target_root / "assets" / "data" / "docs").mkdir(parents=True, exist_ok=True)
        shutil.copy2(reports_path, target_root / "assets" / "data" / "docs" / "reports.json")


def create_fixture_repo(target_root: Path) -> None:
    copy_scripts_fixture(target_root)
    (target_root / "_config.yml").write_text("title: docs workflow fixture\n", encoding="utf-8")
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
    write_doc(target_root / "docs-viewer/source/studio" / "archive.md", doc_id="archive", title="Archive", sort_order=9000)
    write_doc(target_root / "docs-viewer/source/studio" / "sibling-doc.md", doc_id="sibling-doc", title="Sibling Doc", sort_order=2000)
    write_doc(target_root / "docs-viewer/source/studio" / "child-doc.md", doc_id="child-doc", title="Child Doc", parent_id="root-doc", sort_order=1000)
    (target_root / "var" / "docs" / "import-staging").mkdir(parents=True)
    (target_root / "var" / "docs" / "import-staging" / "staged-doc.md").write_text("# Staged Doc\n", encoding="utf-8")

    materialize_fixture_generated_docs(target_root, "studio")


def materialize_fixture_generated_docs(repo_root: Path, scope: str) -> None:
    module = studio_docs_api.load_docs_management_service_module(repo_root)
    source_model = module.source_model
    configs = module.docs_source_config_settings.load_docs_scope_configs(repo_root)
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
            sort_order = front_matter.get("sort_order")
            if sort_order is not None:
                sort_order = int(sort_order)
            hidden = source_model.doc_is_hidden(front_matter)
            docs.append(
                SimpleNamespace(
                    doc_id=doc_id,
                    title=title,
                    front_matter=dict(front_matter),
                    ui_status=source_model.normalize_ui_status(front_matter.get("ui_status")),
                    parent_id=str(front_matter.get("parent_id") or "").strip(),
                    sort_order=sort_order,
                    published=source_model.doc_is_published(front_matter),
                    hidden=hidden,
                    viewable=not hidden,
                    body=body,
                )
            )
    output_root = repo_root / config.output
    docs_payload = []
    for doc in docs:
        content_url = f"/{(config.output / 'by-id' / f'{doc.doc_id}.json').as_posix()}"
        docs_payload.append(
            {
                "doc_id": doc.doc_id,
                "title": doc.title,
                "summary": str(doc.front_matter.get("summary") or ""),
                "ui_status": doc.ui_status,
                "parent_id": doc.parent_id,
                "sort_order": doc.sort_order,
                "published": doc.published,
                "hidden": doc.hidden,
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
                "sort_order": doc.sort_order,
                "content_html": f"<h1 id=\"{doc.doc_id}\">{doc.title}</h1>",
            },
        )
    write_json(
        output_root / "index.json",
        {
            "viewer_options": {
                "show_updated_date": config.show_updated_date,
                "default_doc_id": config.default_doc_id,
            },
            "docs": docs_payload,
        },
    )
    write_json(output_root / "references" / "index.json", {"targets": []})
    write_json(repo_root / "assets" / "data" / "search" / scope / "index.json", {"entries": []})


def patch_rebuilds(repo_root: Path) -> None:
    module = studio_docs_api.load_docs_management_service_module(repo_root)

    def fake_rebuild_scope_outputs(
        _repo_root: Path,
        scope: str,
        include_search: bool = True,
        search_doc_ids: list[str] | None = None,
        docs_doc_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        materialize_fixture_generated_docs(_repo_root, scope)
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
        configs = module.docs_source_config_settings.load_docs_scope_configs(_repo_root)
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

    def fake_validate_markdown_with_jekyll(_repo_root: Path, markdown: str) -> dict[str, Any]:
        return {
            "ok": True,
            "html_chars": len(markdown),
            "renderer": "fixture-markdown-validator",
        }

    module.write_rebuild.rebuild_scope_outputs = fake_rebuild_scope_outputs
    module.write_rebuild.rebuild_all_docs_outputs = fake_rebuild_all_docs_outputs
    module.write_rebuild.perform_source_write_and_rebuild = fake_perform_source_write_and_rebuild
    sys.modules["docs_html_import"].validate_markdown_with_jekyll = fake_validate_markdown_with_jekyll


def start_server(repo_root: Path) -> tuple[StudioAppServer, str]:
    patch_rebuilds(repo_root)
    server = StudioAppServer(("127.0.0.1", 0), repo_root)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


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
        create_fixture_repo(fixture_root)
        server, base_url = start_server(fixture_root)
        try:
            settings = request_json(base_url, "GET", "/studio/api/docs/docs/source-config-settings?scope=studio")
            assert_ok(settings, "source config settings")
            if settings["scopes"][0]["scope_id"] != "studio":
                raise AssertionError(f"unexpected settings payload: {settings!r}")

            settings_apply = request_json(
                base_url,
                "POST",
                "/studio/api/docs/docs/source-config-settings",
                {"scope": "studio", "changes": {"show_updated_date": False}},
            )
            assert_ok(settings_apply, "source config settings apply")
            if settings_apply.get("rebuild", {}).get("fixture_rebuild") is not True:
                raise AssertionError(f"settings apply did not rebuild through fixture patch: {settings_apply!r}")

            import_listing = request_json(base_url, "GET", "/studio/api/docs/docs/import-source-files")
            assert_ok(import_listing, "import source files")
            if not any(item.get("filename") == "staged-doc.md" for item in import_listing.get("files", [])):
                raise AssertionError(f"staged import file not listed: {import_listing!r}")

            created = request_json(
                base_url,
                "POST",
                "/studio/api/docs/docs/create",
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
                "/studio/api/docs/docs/update-metadata",
                {
                    "scope": "studio",
                    "doc_id": doc_id,
                    "title": "API Smoke Renamed",
                    "summary": "workflow fixture",
                    "ui_status": "review",
                    "parent_id": "",
                    "sort_order": "append",
                    "viewable": True,
                },
            )
            assert_ok(metadata, "metadata update")
            if metadata["record"]["title"] != "API Smoke Renamed":
                raise AssertionError(f"metadata title did not update: {metadata!r}")

            moved = request_json(
                base_url,
                "POST",
                "/studio/api/docs/docs/move",
                {"scope": "studio", "doc_id": doc_id, "target_doc_id": "sibling-doc", "position": "after"},
            )
            assert_ok(moved, "move")
            if moved["record"]["parent_id"] != "":
                raise AssertionError(f"move changed parent unexpectedly: {moved!r}")

            archived = request_json(
                base_url,
                "POST",
                "/studio/api/docs/docs/archive",
                {"scope": "studio", "doc_id": doc_id},
            )
            assert_ok(archived, "archive")
            if archived["record"]["parent_id"] != "archive":
                raise AssertionError(f"archive did not move doc under archive: {archived!r}")

            delete_preview = request_json(
                base_url,
                "POST",
                "/studio/api/docs/docs/delete-preview",
                {"scope": "studio", "doc_id": doc_id},
            )
            assert_ok(delete_preview, "delete preview")
            if delete_preview.get("allowed") is not True:
                raise AssertionError(f"delete preview should be allowed for fixture doc: {delete_preview!r}")

            deleted = request_json(
                base_url,
                "POST",
                "/studio/api/docs/docs/delete-apply",
                {"scope": "studio", "doc_id": doc_id, "confirm": True},
            )
            assert_ok(deleted, "delete apply")
            if created_path.exists():
                raise AssertionError(f"delete apply did not remove fixture source file: {created_path}")

            rebuild = request_json(
                base_url,
                "POST",
                "/studio/api/docs/docs/rebuild",
                {"scope": "studio"},
            )
            assert_ok(rebuild, "rebuild")
            if rebuild.get("fixture_rebuild") is not True:
                raise AssertionError(f"rebuild route did not use fixture rebuild: {rebuild!r}")

            scope_create_preview = request_json(
                base_url,
                "POST",
                "/studio/api/docs/docs/scopes/create-preview",
                {
                    "scope_id": "apismoke",
                    "title": "API Smoke Scope",
                    "source_root": "docs-viewer/source/apismoke",
                    "default_doc_id": "apismoke",
                    "publishing_mode": "local_uncommitted",
                    "write_generated_outputs": True,
                    "build_inline_search": True,
                },
            )
            assert_ok(scope_create_preview, "scope create preview")
            if scope_create_preview.get("scope_id") != "apismoke":
                raise AssertionError(f"scope create preview returned unexpected payload: {scope_create_preview!r}")

            scope_created = request_json(
                base_url,
                "POST",
                "/studio/api/docs/docs/scopes/create-apply",
                {
                    "scope_id": "apismoke",
                    "title": "API Smoke Scope",
                    "source_root": "docs-viewer/source/apismoke",
                    "default_doc_id": "apismoke",
                    "publishing_mode": "local_uncommitted",
                    "write_generated_outputs": True,
                    "build_inline_search": True,
                    "confirm": True,
                },
            )
            assert_ok(scope_created, "scope create apply")
            if not (fixture_root / "docs-viewer/source/apismoke" / "apismoke.md").exists():
                raise AssertionError(f"scope create did not write fixture source: {scope_created!r}")

            scope_delete_preview = request_json(
                base_url,
                "POST",
                "/studio/api/docs/docs/scopes/delete-preview",
                {"scope_id": "apismoke"},
            )
            assert_ok(scope_delete_preview, "scope delete preview")
            if scope_delete_preview.get("allowed") is not True:
                raise AssertionError(f"scope delete preview should be allowed: {scope_delete_preview!r}")

            scope_deleted = request_json(
                base_url,
                "POST",
                "/studio/api/docs/docs/scopes/delete-apply",
                {"scope_id": "apismoke", "confirm": True},
            )
            assert_ok(scope_deleted, "scope delete apply")
            if (fixture_root / "docs-viewer/source/apismoke").exists():
                raise AssertionError(f"scope delete did not remove fixture source root: {scope_deleted!r}")

            docs_config = (fixture_root / "studio" / "docs-viewer" / "config" / "scopes" / "docs_scopes.json").read_text(encoding="utf-8")
            if '"show_updated_date": false' not in docs_config:
                raise AssertionError("settings apply did not update fixture docs_scopes.json")
            if "apismoke" in docs_config:
                raise AssertionError("scope delete did not remove fixture scope config")
            print(f"local Studio Docs management workflows OK: {base_url}/studio/api/docs")
            return 0
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
