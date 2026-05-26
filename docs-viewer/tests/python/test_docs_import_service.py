#!/usr/bin/env python3
"""Focused checks for Docs Management Library import service handlers."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_DIR = REPO_ROOT / "docs-viewer" / "services"
DOCS_MANAGEMENT_PATH = DOCS_DIR / "docs_management_service.py"


def load_docs_management_module():
    if str(DOCS_DIR) not in sys.path:
        sys.path.insert(0, str(DOCS_DIR))
    spec = importlib.util.spec_from_file_location("docs_management_service", DOCS_MANAGEMENT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load docs_management_service.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


docs_management = load_docs_management_module()
documents_data_sharing_adapter = sys.modules["documents_data_sharing_adapter"]
import docs_import_source_service as import_source_service  # noqa: E402
import docs_html_import  # noqa: E402
import docs_source_model as source_model  # noqa: E402


def handle_documents_import_files(root: Path, data_domain: str) -> dict[str, object]:
    return documents_data_sharing_adapter.list_returned_packages(
        root,
        data_domain,
        dependencies=docs_management.documents_data_sharing_dependencies(),
    )


def handle_documents_import_preview(root: Path, body: dict[str, object], dry_run: bool) -> dict[str, object]:
    return documents_data_sharing_adapter.review_returned_package(
        root,
        body,
        dry_run,
        dependencies=docs_management.documents_data_sharing_dependencies(),
    )


def handle_documents_import_apply(root: Path, body: dict[str, object], dry_run: bool) -> dict[str, object]:
    return documents_data_sharing_adapter.apply_returned_changes(
        root,
        body,
        dry_run,
        dependencies=docs_management.documents_data_sharing_dependencies(),
    )


def handle_docs_export(root: Path, body: dict[str, object], dry_run: bool) -> dict[str, object]:
    return documents_data_sharing_adapter.prepare_package(
        root,
        body,
        dry_run,
        dependencies=docs_management.documents_data_sharing_dependencies(),
    )


def make_repo() -> tempfile.TemporaryDirectory:
    temp_dir = tempfile.TemporaryDirectory()
    root = Path(temp_dir.name)
    (root / "_config.yml").write_text("title: Test\n", encoding="utf-8")
    (root / "var/studio/data-sharing/library/import-staging").mkdir(parents=True, exist_ok=True)
    index_path = root / "assets/data/docs/scopes/library/index.json"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    docs = [
        {"doc_id": "library", "title": "Library", "parent_id": "", "viewable": True},
        {"doc_id": "alpha", "title": "Alpha", "parent_id": "library", "viewable": True},
    ]
    index_path.write_text(json.dumps({"docs": docs}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    payload_root = root / "assets/data/docs/scopes/library/by-id"
    payload_root.mkdir(parents=True, exist_ok=True)
    for doc in docs:
        (payload_root / f"{doc['doc_id']}.json").write_text(
            json.dumps({"doc_id": doc["doc_id"], "title": doc["title"]}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    config_path = root / "studio/data/config/data-sharing/library-export-configs.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(
            {
                "schema_version": "library_export_configs_v1",
                "configs": [
                    {
                        "id": "library-document-summaries",
                        "label": "Document summaries",
                        "description": "Exports summary metadata.",
                        "enabled": True,
                        "scopes": ["library"],
                        "target": {
                            "format": "jsonl",
                            "record_shape": "document_rows",
                            "include_export_metadata": True,
                        },
                        "output": {
                            "path_pattern": "var/studio/data-sharing/{scope}/exports/{export_id}-{timestamp}.jsonl",
                            "timestamp_format": "%Y%m%d-%H%M%S",
                        },
                        "selection": {
                            "mode": "explicit_doc_ids",
                            "include_descendants": False,
                            "include_non_viewable": True,
                            "exclude_archived": False,
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
                        "document_fields": [
                            {"source": "doc_id", "output_path": "doc_id", "required": True},
                            {"source": "title", "output_path": "title", "required": True},
                        ],
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    adapter_path = root / "studio/data/config/data-sharing/data-sharing-adapters.json"
    adapter_path.write_text(
        json.dumps(
            {
                "schema_version": "data_sharing_adapters_v2",
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
                                "label": "Library",
                                "scope": "library",
                                "status": "active",
                                "selection_model": "documents",
                                "paths": {
                                    "outbound_package_root": "var/studio/data-sharing/library/exports",
                                    "returned_package_staging_root": "var/studio/data-sharing/library/import-staging",
                                    "review_output_root": "var/studio/data-sharing/library/import-preview",
                                    "source_root": "docs-viewer/source/library",
                                    "backup_root": "var/docs/backups",
                                },
                                "source_write_targets": {
                                    "documents": "docs-viewer/source/library",
                                },
                                "sources": {
                                    "docs_index": "assets/data/docs/scopes/library/index.json",
                                    "docs_payload_root": "assets/data/docs/scopes/library/by-id",
                                    "source_root": "docs-viewer/source/library",
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
                                    "backup_root": "backup_root",
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
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return temp_dir


def write_staged(root: Path, filename: str, payload: object, scope: str = "library") -> None:
    path = root / "var/studio/data-sharing" / scope / "import-staging" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    if filename.endswith(".jsonl"):
        rows = payload if isinstance(payload, list) else [payload]
        path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    else:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_staged_html(root: Path, filename: str, html: str) -> None:
    path = root / "var/docs/import-staging" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")


def write_staged_markdown(root: Path, filename: str, markdown: str) -> None:
    path = root / "var/docs/import-staging" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown, encoding="utf-8")


def write_staged_text(root: Path, filename: str, text: str) -> None:
    path = root / "var/docs/import-staging" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_staged_bytes(root: Path, filename: str, payload: bytes) -> None:
    path = root / "var/docs/import-staging" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def write_staged_package_file(root: Path, package: str, filename: str, payload: bytes | str) -> Path:
    path = root / "var/docs/import-staging" / package / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, bytes):
        path.write_bytes(payload)
    else:
        path.write_text(payload, encoding="utf-8")
    return path


def write_test_image(path: Path, size: tuple[int, int]) -> None:
    from PIL import Image

    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, (180, 40, 30)).save(path)


def write_library_doc(root: Path, filename: str, front_matter: dict[str, object], body: str = "# Body\n") -> None:
    lines = ["---"]
    for key, value in front_matter.items():
        lines.append(f"{key}: {source_model.format_front_matter_value(value)}")
    lines.extend(["---", "", body])
    path = root / "docs-viewer/source/library" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def stub_rebuild():
    original = docs_management.write_rebuild.perform_source_write_and_rebuild

    def fake_rebuild(repo_root, scope, changed_paths, write_operation, **kwargs):
        write_operation()
        docs_doc_ids = list(kwargs.get("docs_doc_ids") or [])
        search_doc_ids = list(kwargs.get("search_doc_ids") or [])
        return {
            "ok": True,
            "steps": [],
            "docs": {
                "mode": "targeted" if docs_doc_ids else "full",
                "doc_ids": docs_doc_ids,
                "reason": "targeted docs payload ids provided" if docs_doc_ids else "full-scope fallback",
            },
            "search": {"mode": "targeted" if search_doc_ids else "none", "doc_ids": search_doc_ids},
            "diagnostics": {
                "docs": {"scope": scope, "build_mode": "targeted" if docs_doc_ids else "full"},
                "search": {"mode": "targeted" if search_doc_ids else "none", "doc_ids": search_doc_ids},
            },
        }

    docs_management.write_rebuild.perform_source_write_and_rebuild = fake_rebuild
    return original


def handle_import_source(root: Path, body: dict[str, object], dry_run: bool) -> dict[str, object]:
    return import_source_service.handle_import_source(
        root,
        body,
        dry_run,
        docs_management.import_source_dependencies(),
    )


def test_library_import_files_lists_json_and_jsonl_only() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged(root, "summaries.jsonl", [{"doc_id": "alpha", "title": "Alpha"}])
        write_staged(root, "relationships.json", {"documents": []})
        (root / "var/studio/data-sharing/library/import-staging/notes.txt").write_text("ignore\n", encoding="utf-8")
        payload = handle_documents_import_files(root, "library")

    assert payload["ok"] is True
    assert payload["scope"] == "library"
    assert payload["staging_root"] == "var/studio/data-sharing/library/import-staging"
    assert [item["filename"] for item in payload["files"]] == ["relationships.json", "summaries.jsonl"]
    assert [item["format"] for item in payload["files"]] == ["json", "jsonl"]


def test_library_import_preview_writes_when_not_dry_run() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged(
            root,
            "summaries.jsonl",
            [{"doc_id": "alpha", "title": "Alpha", "parent_id": "library", "summary": "Preview summary."}],
        )
        payload = handle_documents_import_preview(
            root,
            {"data_domain": "library", "operation": "review", "staged_filename": "summaries.jsonl"},
            dry_run=False,
        )
        preview_paths = sorted((root / "var/studio/data-sharing/library/import-preview").glob("alpha-*.md"))
        tree_paths = sorted((root / "var/studio/data-sharing/library/import-preview").glob("summaries-tree-*.md"))
        preview_text = preview_paths[0].read_text(encoding="utf-8")

    assert payload["ok"] is True
    assert payload["preview_written"] is True
    assert len(preview_paths) == 1
    assert len(tree_paths) == 1
    assert f"var/studio/data-sharing/library/import-preview/{preview_paths[0].name}" in [
        item["path"] for item in payload["preview_files"]
    ]
    assert payload["summary_text"] == "Generated 2 Library import preview files."
    assert "Preview summary." in preview_text


def test_library_import_preview_dry_run_reports_without_writing() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged(root, "summaries.jsonl", [{"doc_id": "alpha", "title": "Alpha"}])
        payload = handle_documents_import_preview(
            root,
            {"data_domain": "library", "operation": "review", "staged_filename": "summaries.jsonl"},
            dry_run=True,
        )
        preview_exists = list((root / "var/studio/data-sharing/library/import-preview").glob("alpha-*.md"))

    assert payload["ok"] is True
    assert payload["preview_written"] is False
    assert payload["preview_files"][0]["path"].startswith("var/studio/data-sharing/library/import-preview/alpha-")
    assert payload["preview_files"][0]["path"].endswith(".md")
    assert payload["summary_text"] == "Validated 1 Library import preview file without writing."
    assert preview_exists == []


def test_documents_import_rejects_unconfigured_data_domain() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged(root, "works.jsonl", [{"doc_id": "work-1", "title": "Work 1"}], scope="catalogue")
        try:
            handle_documents_import_preview(
                root,
                {"data_domain": "catalogue", "staged_filename": "works.jsonl"},
                dry_run=True,
            )
        except ValueError as error:
            message = str(error)
        else:
            raise AssertionError("unconfigured data domain should fail closed")

    assert "no Data Sharing adapter configured for catalogue/review" in message


def test_docs_export_summary_text_uses_context_aware_document_plural() -> None:
    with make_repo() as temp:
        root = Path(temp)
        singular = handle_docs_export(
            root,
            {
                "data_domain": "library",
                "config_id": "library-document-summaries",
                "doc_ids": ["alpha"],
                "select_all": False,
                "missing_summary_only": None,
            },
            dry_run=True,
        )
        plural = handle_docs_export(
            root,
            {
                "data_domain": "library",
                "config_id": "library-document-summaries",
                "doc_ids": ["library", "alpha"],
                "select_all": False,
                "missing_summary_only": None,
            },
            dry_run=True,
        )

    assert singular["summary_text"].startswith("Validated package 1 document to ")
    assert plural["summary_text"].startswith("Validated package 2 documents to ")


def test_html_import_create_uses_staged_filename_for_doc_id_and_path() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
        write_staged_html(
            root,
            "compact-name.html",
            """
            <html>
              <head><title>An Overly Descriptive Document Title</title></head>
              <body><h1>An Overly Descriptive Document Title</h1><p>Imported body.</p></body>
            </html>
            """,
        )
        original_rebuild = stub_rebuild()
        validation_globals = import_source_service.generate_import_preview.__globals__
        original_validation = validation_globals["validate_markdown_with_jekyll"]
        validation_globals["validate_markdown_with_jekyll"] = lambda repo_root, markdown: {
            "ok": True,
            "html_chars": len(markdown),
            "renderer": "stub",
        }
        try:
            payload = handle_import_source(
                root,
                {"scope": "library", "staged_filename": "compact-name.html"},
                dry_run=False,
            )
        finally:
            docs_management.write_rebuild.perform_source_write_and_rebuild = original_rebuild
            validation_globals["validate_markdown_with_jekyll"] = original_validation

        source_path = root / "docs-viewer/source/library/compact-name.md"
        source_exists = source_path.exists()
        source_text = source_path.read_text(encoding="utf-8")

    assert payload["ok"] is True
    assert payload["operation"] == "create"
    assert payload["doc_id"] == "compact-name"
    assert payload["path"] == "docs-viewer/source/library/compact-name.md"
    assert payload["title"] == "An Overly Descriptive Document Title"
    assert payload["import_preview"]["proposed_doc_id_source"] == "filename"
    assert source_exists
    assert "doc_id: compact-name" in source_text
    assert "title: An Overly Descriptive Document Title" in source_text


def test_html_import_copies_role_marked_interactive_assets() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
        write_staged_html(
            root,
            "worksheet.html",
            """
            <html>
              <head><title>Worksheet</title></head>
              <body><h1>Worksheet</h1><p>Readable body.</p></body>
            </html>
            """,
        )
        write_staged_html(
            root,
            "Worksheet Widget.html",
            """
            <!doctype html>
            <html>
              <head><meta name="dlf:docs-import-role" content="interactive-html"></head>
              <body><button>Run</button><script>window.ready = true;</script></body>
            </html>
            """,
        )
        write_staged_html(
            root,
            "second-widget.html",
            """
            <!doctype html>
            <html>
              <head><meta name="dlf:docs-import-role" content="interactive-html"></head>
              <body>Second widget</body>
            </html>
            """,
        )
        original_rebuild = stub_rebuild()
        validation_globals = import_source_service.generate_import_preview.__globals__
        original_validation = validation_globals["validate_markdown_with_jekyll"]
        validation_globals["validate_markdown_with_jekyll"] = lambda repo_root, markdown: {
            "ok": True,
            "html_chars": len(markdown),
            "renderer": "stub",
        }
        try:
            payload = handle_import_source(
                root,
                {"scope": "library", "staged_filename": "worksheet.html"},
                dry_run=False,
            )
        finally:
            docs_management.write_rebuild.perform_source_write_and_rebuild = original_rebuild
            validation_globals["validate_markdown_with_jekyll"] = original_validation

        source_text = (root / "docs-viewer/source/library/worksheet.md").read_text(encoding="utf-8")
        asset_path = root / "assets/docs/interactive/library/worksheet-widget.html"
        asset_text = asset_path.read_text(encoding="utf-8")
        second_asset_path = root / "assets/docs/interactive/library/second-widget.html"
        second_asset_text = second_asset_path.read_text(encoding="utf-8")

    assert payload["ok"] is True
    assert "[[interactive-html:worksheet-widget.html]]" not in source_text
    assert payload["import_preview"]["interactive_html_plans"][0]["token"] == "[[interactive-html:second-widget.html]]"
    assert payload["import_preview"]["interactive_html_plans"][1]["token"] == "[[interactive-html:worksheet-widget.html]]"
    assert [item["target_path"] for item in payload["interactive_html_written"]] == [
        "assets/docs/interactive/library/second-widget.html",
        "assets/docs/interactive/library/worksheet-widget.html",
    ]
    assert payload["interactive_html_written"][1]["display_name"] == "worksheet-widget"
    assert payload["interactive_html_written"][1]["result_type"] == "script file"
    assert "window.ready = true" in asset_text
    assert "Second widget" in second_asset_text
    assert "Copied 2 interactive HTML script files." in payload["summary_text"]


def test_html_import_reports_role_marked_interactive_assets_in_preview_only() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
        write_staged_html(root, "worksheet.html", "<html><body><h1>Worksheet</h1></body></html>")
        write_staged_html(
            root,
            "Worksheet Widget.html",
            """
            <!doctype html>
            <html>
              <head><meta name="dlf:docs-import-role" content="interactive-html"></head>
              <body>Interactive</body>
            </html>
            """,
        )
        original_rebuild = stub_rebuild()
        validation_globals = import_source_service.generate_import_preview.__globals__
        original_validation = validation_globals["validate_markdown_with_jekyll"]
        validation_globals["validate_markdown_with_jekyll"] = lambda repo_root, markdown: {
            "ok": True,
            "html_chars": len(markdown),
            "renderer": "stub",
        }
        try:
            payload = handle_import_source(
                root,
                {"scope": "library", "staged_filename": "worksheet.html", "preview_only": True},
                dry_run=False,
            )
            files = import_source_service.handle_import_source_files(root)["files"]
        finally:
            docs_management.write_rebuild.perform_source_write_and_rebuild = original_rebuild
            validation_globals["validate_markdown_with_jekyll"] = original_validation

        asset_exists = (root / "assets/docs/interactive/library/worksheet-widget.html").exists()

    assert payload["ok"] is True
    assert payload["preview_only"] is True
    assert payload["import_preview"]["interactive_html_plans"][0]["target_path"] == "assets/docs/interactive/library/worksheet-widget.html"
    assert [file["filename"] for file in files] == ["worksheet.html"]
    assert asset_exists is False


def test_html_import_confirms_existing_role_marked_interactive_asset_target() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
        write_staged_html(root, "worksheet.html", "<html><body><h1>Worksheet</h1></body></html>")
        write_staged_html(
            root,
            "worksheet-widget.html",
            """
            <!doctype html>
            <html>
              <head><meta name="dlf:docs-import-role" content="interactive-html"></head>
              <body>Interactive</body>
            </html>
            """,
        )
        existing_asset = root / "assets/docs/interactive/library/worksheet-widget.html"
        existing_asset.parent.mkdir(parents=True, exist_ok=True)
        existing_asset.write_text("existing\n", encoding="utf-8")
        original_rebuild = stub_rebuild()
        validation_globals = import_source_service.generate_import_preview.__globals__
        original_validation = validation_globals["validate_markdown_with_jekyll"]
        validation_globals["validate_markdown_with_jekyll"] = lambda repo_root, markdown: {
            "ok": True,
            "html_chars": len(markdown),
            "renderer": "stub",
        }
        try:
            preview_payload = handle_import_source(
                root,
                {"scope": "library", "staged_filename": "worksheet.html"},
                dry_run=False,
            )
            apply_payload = handle_import_source(
                root,
                {"scope": "library", "staged_filename": "worksheet.html", "confirm_overwrite": True},
                dry_run=False,
            )
        finally:
            docs_management.write_rebuild.perform_source_write_and_rebuild = original_rebuild
            validation_globals["validate_markdown_with_jekyll"] = original_validation

        source_text = (root / "docs-viewer/source/library/worksheet.md").read_text(encoding="utf-8")
        asset_text = existing_asset.read_text(encoding="utf-8")

    assert preview_payload["ok"] is True
    assert preview_payload["preview_only"] is True
    assert preview_payload["requires_interactive_html_confirmation"] is True
    assert preview_payload["summary_text"] == "Interactive HTML asset overwrite required for assets/docs/interactive/library/worksheet-widget.html."
    assert apply_payload["ok"] is True
    assert apply_payload["interactive_html_written"][0]["overwrote"] is True
    assert "doc_id: worksheet" in source_text
    assert "Interactive" in asset_text
    assert asset_text != "existing\n"


def test_source_import_files_list_html_and_markdown() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged_html(root, "source.html", "<html><body><h1>Source</h1></body></html>")
        write_staged_markdown(root, "source.md", "# Source\n")
        write_staged_text(root, "source.txt", "Source\n")
        write_staged_text(root, "source.svg", "<svg viewBox='0 0 10 10'></svg>\n")
        write_staged_bytes(root, "source.png", b"fake image")
        write_staged_bytes(root, "source.pdf", b"fake pdf")
        write_staged_package_file(root, "package-note", "Note.md", "# Package Note\n")

        files = import_source_service.list_staged_import_source_files(root)

    by_filename = {item["filename"]: item for item in files}
    assert by_filename["source.html"]["source_format"] == "html"
    assert by_filename["source.md"]["source_format"] == "markdown"
    assert by_filename["source.txt"]["source_format"] == "text"
    assert by_filename["source.svg"]["source_format"] == "svg"
    assert by_filename["source.png"]["source_format"] == "image"
    assert by_filename["source.pdf"]["source_format"] == "file"
    assert by_filename["package-note"]["source_format"] == "markdown_package"
    assert by_filename["package-note"]["package_markdown_count"] == 1


def test_markdown_import_create_wraps_body_with_generated_front_matter() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
        write_staged_markdown(
            root,
            "markdown-note.md",
            "# Imported Markdown\n\nBody from staged Markdown with [a link](https://example.com).\n",
        )
        original_rebuild = stub_rebuild()
        validation_globals = import_source_service.generate_import_preview.__globals__
        original_validation = validation_globals["validate_markdown_with_jekyll"]
        validation_globals["validate_markdown_with_jekyll"] = lambda repo_root, markdown: {
            "ok": True,
            "html_chars": len(markdown),
            "renderer": "stub",
        }
        try:
            payload = handle_import_source(
                root,
                {"scope": "library", "staged_filename": "markdown-note.md"},
                dry_run=False,
            )
        finally:
            docs_management.write_rebuild.perform_source_write_and_rebuild = original_rebuild
            validation_globals["validate_markdown_with_jekyll"] = original_validation

        source_path = root / "docs-viewer/source/library/markdown-note.md"
        source_text = source_path.read_text(encoding="utf-8")

    assert payload["ok"] is True
    assert payload["operation"] == "create"
    assert payload["doc_id"] == "markdown-note"
    assert payload["title"] == "Imported Markdown"
    assert payload["import_preview"]["source_format"] == "markdown"
    assert payload["import_preview"]["proposed_doc_id_source"] == "filename"
    assert "doc_id: markdown-note" in source_text
    assert "title: Imported Markdown" in source_text
    assert "# Imported Markdown" in source_text
    assert "Body from staged Markdown" in source_text


def test_text_import_autolinks_plain_urls() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
        write_staged_text(root, "plain-note.txt", "Plain Note\n\nSee https://example.com/path.\n")
        original_rebuild = stub_rebuild()
        validation_globals = import_source_service.generate_import_preview.__globals__
        original_validation = validation_globals["validate_markdown_with_jekyll"]
        validation_globals["validate_markdown_with_jekyll"] = lambda repo_root, markdown: {
            "ok": True,
            "html_chars": len(markdown),
            "renderer": "stub",
        }
        try:
            payload = handle_import_source(
                root,
                {"scope": "library", "staged_filename": "plain-note.txt"},
                dry_run=False,
            )
        finally:
            docs_management.write_rebuild.perform_source_write_and_rebuild = original_rebuild
            validation_globals["validate_markdown_with_jekyll"] = original_validation

        source_text = (root / "docs-viewer/source/library/plain-note.md").read_text(encoding="utf-8")

    assert payload["ok"] is True
    assert payload["import_preview"]["source_format"] == "text"
    assert "<https://example.com/path>" in source_text


def test_svg_import_strips_unsafe_content() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
        write_staged_text(
            root,
            "diagram.svg",
            """
            <svg viewBox="0 0 10 10" onclick="alert(1)">
              <title>Unsafe Diagram</title>
              <script>alert(1)</script>
              <rect width="10" height="10" />
            </svg>
            """,
        )
        original_rebuild = stub_rebuild()
        validation_globals = import_source_service.generate_import_preview.__globals__
        original_validation = validation_globals["validate_markdown_with_jekyll"]
        validation_globals["validate_markdown_with_jekyll"] = lambda repo_root, markdown: {
            "ok": True,
            "html_chars": len(markdown),
            "renderer": "stub",
        }
        try:
            payload = handle_import_source(
                root,
                {"scope": "library", "staged_filename": "diagram.svg"},
                dry_run=False,
            )
        finally:
            docs_management.write_rebuild.perform_source_write_and_rebuild = original_rebuild
            validation_globals["validate_markdown_with_jekyll"] = original_validation

        source_text = (root / "docs-viewer/source/library/diagram.md").read_text(encoding="utf-8")

    assert payload["ok"] is True
    assert payload["title"] == "Unsafe Diagram"
    assert payload["import_preview"]["source_format"] == "svg"
    assert "<script" not in source_text
    assert "onclick" not in source_text
    assert "<title>Unsafe Diagram</title>" in source_text
    assert any("script" in warning for warning in payload["import_preview"]["warnings"])


def test_image_import_creates_media_path_plan_wrapper() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
        write_staged_bytes(root, "reference-image.png", b"fake image")
        original_rebuild = stub_rebuild()
        validation_globals = import_source_service.generate_import_preview.__globals__
        original_validation = validation_globals["validate_markdown_with_jekyll"]
        validation_globals["validate_markdown_with_jekyll"] = lambda repo_root, markdown: {
            "ok": True,
            "html_chars": len(markdown),
            "renderer": "stub",
        }
        try:
            payload = handle_import_source(
                root,
                {"scope": "library", "staged_filename": "reference-image.png"},
                dry_run=False,
            )
        finally:
            docs_management.write_rebuild.perform_source_write_and_rebuild = original_rebuild
            validation_globals["validate_markdown_with_jekyll"] = original_validation

        source_text = (root / "docs-viewer/source/library/reference-image.md").read_text(encoding="utf-8")

    assert payload["ok"] is True
    assert payload["import_preview"]["source_format"] == "image"
    assert payload["import_preview"]["media_plan"]["media_path"] == "docs/library/img/reference-image.png"
    assert "[[media:docs/library/img/reference-image.png]]" in source_text


def test_media_path_comes_from_scope_config() -> None:
    assert docs_html_import.media_path_for("analysis", "img", "diagram.png") == "docs/analysis/img/diagram.png"
    assert docs_html_import.media_token("analysis", "img", "diagram.png") == "[[media:docs/analysis/img/diagram.png]]"


def test_html_import_extracts_inline_png_to_staged_media_plan() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
        write_staged_html(
            root,
            "inline-diagram.html",
            """
            <html>
              <head><title>Inline Diagram</title></head>
              <body>
                <h1>Inline Diagram</h1>
                <p><img alt="Layered diagram" src="data:image/png;base64,aW5saW5lLXBuZw=="></p>
              </body>
            </html>
            """,
        )
        original_rebuild = stub_rebuild()
        validation_globals = import_source_service.generate_import_preview.__globals__
        original_validation = validation_globals["validate_markdown_with_jekyll"]
        validation_globals["validate_markdown_with_jekyll"] = lambda repo_root, markdown: {
            "ok": True,
            "html_chars": len(markdown),
            "renderer": "stub",
        }
        try:
            payload = handle_import_source(
                root,
                {"scope": "library", "staged_filename": "inline-diagram.html"},
                dry_run=False,
            )
        finally:
            docs_management.write_rebuild.perform_source_write_and_rebuild = original_rebuild
            validation_globals["validate_markdown_with_jekyll"] = original_validation

        source_text = (root / "docs-viewer/source/library/inline-diagram.md").read_text(encoding="utf-8")
        media_path = root / "var/docs/import-staging/inline-diagram-image-01.png"
        media_bytes = media_path.read_bytes()

    assert payload["ok"] is True
    assert payload["import_preview"]["media_plans"][0]["source_path"] == "inline-diagram-image-01.png"
    assert payload["import_preview"]["media_plans"][0]["media_path"] == "docs/library/img/inline-diagram-image-01.png"
    assert payload["inline_media_written"][0]["staging_path"] == "var/docs/import-staging/inline-diagram-image-01.png"
    assert media_bytes == b"inline-png"
    assert "data:image/png;base64" not in source_text
    assert "![Layered diagram]([[media:docs/library/img/inline-diagram-image-01.png]])" in source_text


def test_markdown_import_extracts_inline_png_with_incremented_filename() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
        write_staged_bytes(root, "inline-note-image-01.png", b"existing")
        write_staged_markdown(
            root,
            "inline-note.md",
            "# Inline Note\n\n![Inline](data:image/png;base64,bWFya2Rvd24tcG5n)\n",
        )
        original_rebuild = stub_rebuild()
        validation_globals = import_source_service.generate_import_preview.__globals__
        original_validation = validation_globals["validate_markdown_with_jekyll"]
        validation_globals["validate_markdown_with_jekyll"] = lambda repo_root, markdown: {
            "ok": True,
            "html_chars": len(markdown),
            "renderer": "stub",
        }
        try:
            payload = handle_import_source(
                root,
                {"scope": "library", "staged_filename": "inline-note.md"},
                dry_run=False,
            )
        finally:
            docs_management.write_rebuild.perform_source_write_and_rebuild = original_rebuild
            validation_globals["validate_markdown_with_jekyll"] = original_validation

        source_text = (root / "docs-viewer/source/library/inline-note.md").read_text(encoding="utf-8")
        media_path = root / "var/docs/import-staging/inline-note-image-02.png"
        media_bytes = media_path.read_bytes()

    assert payload["ok"] is True
    assert payload["import_preview"]["source_format"] == "markdown"
    assert payload["import_preview"]["media_plans"][0]["source_path"] == "inline-note-image-02.png"
    assert media_bytes == b"markdown-png"
    assert "data:image/png;base64" not in source_text
    assert "[[media:docs/library/img/inline-note-image-02.png]]" in source_text


def test_inline_media_write_skips_invalid_data_urls_before_valid_images() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
        write_staged_markdown(
            root,
            "mixed-inline.md",
            "# Mixed Inline\n\n![Broken](data:image/png;base64,abc)\n\n![Valid](data:image/png;base64,dmFsaWQtcG5n)\n",
        )
        original_rebuild = stub_rebuild()
        validation_globals = import_source_service.generate_import_preview.__globals__
        original_validation = validation_globals["validate_markdown_with_jekyll"]
        validation_globals["validate_markdown_with_jekyll"] = lambda repo_root, markdown: {
            "ok": True,
            "html_chars": len(markdown),
            "renderer": "stub",
        }
        try:
            payload = handle_import_source(
                root,
                {"scope": "library", "staged_filename": "mixed-inline.md"},
                dry_run=False,
            )
        finally:
            docs_management.write_rebuild.perform_source_write_and_rebuild = original_rebuild
            validation_globals["validate_markdown_with_jekyll"] = original_validation

        source_text = (root / "docs-viewer/source/library/mixed-inline.md").read_text(encoding="utf-8")
        media_path = root / "var/docs/import-staging/mixed-inline-image-01.png"
        media_bytes = media_path.read_bytes()

    assert payload["ok"] is True
    assert len(payload["import_preview"]["media_plans"]) == 1
    assert media_bytes == b"valid-png"
    assert "![Broken](data:image/png;base64,abc)" in source_text
    assert "[[media:docs/library/img/mixed-inline-image-01.png]]" in source_text


def test_file_media_import_creates_file_media_path_plan_wrapper() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
        write_staged_bytes(root, "reference-file.pdf", b"fake pdf")
        original_rebuild = stub_rebuild()
        validation_globals = import_source_service.generate_import_preview.__globals__
        original_validation = validation_globals["validate_markdown_with_jekyll"]
        validation_globals["validate_markdown_with_jekyll"] = lambda repo_root, markdown: {
            "ok": True,
            "html_chars": len(markdown),
            "renderer": "stub",
        }
        try:
            payload = handle_import_source(
                root,
                {"scope": "library", "staged_filename": "reference-file.pdf"},
                dry_run=False,
            )
        finally:
            docs_management.write_rebuild.perform_source_write_and_rebuild = original_rebuild
            validation_globals["validate_markdown_with_jekyll"] = original_validation

        source_text = (root / "docs-viewer/source/library/reference-file.md").read_text(encoding="utf-8")

    assert payload["ok"] is True
    assert payload["import_preview"]["source_format"] == "file"
    assert payload["import_preview"]["media_plan"]["media_path"] == "docs/library/files/reference-file.pdf"
    assert "[[media:docs/library/files/reference-file.pdf]]" in source_text


def test_markdown_package_import_rewrites_media_and_materializes_outputs() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
        image_path = write_staged_package_file(root, "my-note", "images/opaque-name.png", b"")
        write_test_image(image_path, (1000, 500))
        write_staged_package_file(root, "my-note", "attachments/report.pdf", b"%PDF-1.4 fake\n")
        write_staged_package_file(
            root,
            "my-note",
            "My Note.md",
            """# My Note

Some text.

![Opaque](images/opaque-name.png)
<span style="font-size: 11.285714;">
    3 symbols
</span>

[Research PDF](attachments/report.pdf)
""",
        )
        original_rebuild = stub_rebuild()
        validation_globals = import_source_service.generate_import_preview.__globals__
        original_validation = validation_globals["validate_markdown_with_jekyll"]
        validation_globals["validate_markdown_with_jekyll"] = lambda repo_root, markdown: {
            "ok": True,
            "html_chars": len(markdown),
            "renderer": "stub",
        }
        try:
            payload = handle_import_source(
                root,
                {"scope": "library", "staged_filename": "my-note"},
                dry_run=False,
            )
        finally:
            docs_management.write_rebuild.perform_source_write_and_rebuild = original_rebuild
            validation_globals["validate_markdown_with_jekyll"] = original_validation

        source_text = (root / "docs-viewer/source/library/my-note.md").read_text(encoding="utf-8")
        webp_path = root / "var/docs/import-staging/my-note-image-01.webp"
        attachment_path = root / "var/docs/import-staging/my-note-attachment-01.pdf"
        from PIL import Image

        with Image.open(webp_path) as converted:
            output_size = converted.size
        attachment_bytes = attachment_path.read_bytes()

    assert payload["ok"] is True
    assert payload["import_preview"]["source_format"] == "markdown_package"
    assert payload["import_preview"]["media_plans"][0]["source_path"] == "my-note-image-01.webp"
    assert payload["import_preview"]["media_plans"][0]["kind"] == "image"
    assert payload["import_preview"]["media_plans"][0]["title"] == "my note image 01"
    assert payload["import_preview"]["media_plans"][1]["source_path"] == "my-note-attachment-01.pdf"
    assert payload["import_preview"]["media_plans"][1]["kind"] == "attachment"
    assert payload["inline_media_written"][0]["kind"] == "image"
    assert payload["inline_media_written"][0]["conversion"]["output_width"] == 800
    assert output_size == (800, 400)
    assert attachment_bytes == b"%PDF-1.4 fake\n"
    assert '![my note image 01]([[media:docs/library/img/my-note-image-01.webp]] "my note image 01")' in source_text
    assert "[Research PDF]([[media:docs/library/files/my-note-attachment-01.pdf]])" in source_text
    assert "font-size: var(--font-caption)" in source_text


def test_markdown_package_image_conversion_does_not_upscale() -> None:
    with make_repo() as temp:
        root = Path(temp)
        source = root / "small.png"
        target = root / "small.webp"
        write_test_image(source, (320, 160))
        result = docs_html_import.convert_package_image_to_webp(source, target, max_width=800)
        from PIL import Image

        with Image.open(target) as converted:
            output_size = converted.size

    assert result["resized"] is False
    assert output_size == (320, 160)


def test_markdown_package_import_reports_unresolved_and_unsupported_links() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
        write_staged_package_file(root, "broken-note", "attachments/archive.exe", b"fake exe")
        write_staged_package_file(
            root,
            "broken-note",
            "Broken Note.md",
            "# Broken Note\n\n![Missing](images/missing.png)\n\n[Unsupported](attachments/archive.exe)\n",
        )
        original_rebuild = stub_rebuild()
        validation_globals = import_source_service.generate_import_preview.__globals__
        original_validation = validation_globals["validate_markdown_with_jekyll"]
        validation_globals["validate_markdown_with_jekyll"] = lambda repo_root, markdown: {
            "ok": True,
            "html_chars": len(markdown),
            "renderer": "stub",
        }
        try:
            payload = handle_import_source(
                root,
                {"scope": "library", "staged_filename": "broken-note", "preview_only": True},
                dry_run=False,
            )
        finally:
            docs_management.write_rebuild.perform_source_write_and_rebuild = original_rebuild
            validation_globals["validate_markdown_with_jekyll"] = original_validation

    warnings = payload["import_preview"]["warnings"]
    assert payload["ok"] is True
    assert payload["preview_only"] is True
    assert any("Package image target was not found" in warning for warning in warnings)
    assert any("Unsupported package attachment type .exe" in warning for warning in warnings)


def test_import_collision_prompts_for_replacement_doc_id() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
        write_library_doc(root, "reference-file.md", {"doc_id": "reference-file", "title": "Reference File", "parent_id": ""})
        write_staged_bytes(root, "reference-file.pdf", b"fake pdf")
        original_rebuild = stub_rebuild()
        validation_globals = import_source_service.generate_import_preview.__globals__
        original_validation = validation_globals["validate_markdown_with_jekyll"]
        validation_globals["validate_markdown_with_jekyll"] = lambda repo_root, markdown: {
            "ok": True,
            "html_chars": len(markdown),
            "renderer": "stub",
        }
        try:
            preview_payload = handle_import_source(
                root,
                {"scope": "library", "staged_filename": "reference-file.pdf"},
                dry_run=False,
            )
            apply_payload = handle_import_source(
                root,
                {
                    "scope": "library",
                    "staged_filename": "reference-file.pdf",
                    "replacement_doc_id": "reference-file-2",
                },
                dry_run=False,
            )
        finally:
            docs_management.write_rebuild.perform_source_write_and_rebuild = original_rebuild
            validation_globals["validate_markdown_with_jekyll"] = original_validation

        source_path = root / "docs-viewer/source/library/reference-file-2.md"
        source_exists = source_path.exists()
        source_text = source_path.read_text(encoding="utf-8")

    assert preview_payload["preview_only"] is True
    assert preview_payload["replacement_doc_id_required"] is True
    assert preview_payload["replacement_title_required"] is True
    assert preview_payload["collision"]["doc_id"] == "reference-file"
    assert apply_payload["ok"] is True
    assert apply_payload["operation"] == "create"
    assert apply_payload["doc_id"] == "reference-file-2"
    assert source_exists
    assert "title: Reference File" in source_text


def test_library_import_summary_apply_preflight_reports_missing_target_doc() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "alpha.md", {"doc_id": "alpha", "title": "Alpha", "summary": "Old summary."})
        write_staged(
            root,
            "summaries.jsonl",
            [
                {"doc_id": "alpha", "title": "Alpha", "summary": "New summary."},
                {"doc_id": "missing", "title": "Missing", "summary": "Missing summary."},
            ],
        )
        payload = handle_documents_import_apply(
            root,
            {"data_domain": "library", "operation": "apply", "apply_action": "summary_apply", "staged_filename": "summaries.jsonl", "record_indices": [0, 1]},
            dry_run=True,
        )

    assert payload["ok"] is False
    assert payload["counts"]["updates"] == 1
    assert payload["counts"]["errors"] == 1
    assert payload["errors"][0]["reason"] == "missing_target_doc"
    assert payload["summary_apply_written"] is False


def test_library_import_summary_apply_creates_backup_and_writes_source() -> None:
    original_rebuild = stub_rebuild()
    try:
        with make_repo() as temp:
            root = Path(temp)
            write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library"})
            write_library_doc(
                root,
                "alpha.md",
                {
                    "doc_id": "alpha",
                    "title": "Alpha",
                    "added_date": "2026-05-01",
                    "last_updated": "2026-05-01",
                    "summary": "Old summary.",
                    "parent_id": "library",
                },
            )
            write_staged(root, "summaries.jsonl", [{"doc_id": "alpha", "title": "Alpha", "summary": "New summary."}])
            payload = handle_documents_import_apply(
                root,
                {"data_domain": "library", "operation": "apply", "apply_action": "summary_apply", "staged_filename": "summaries.jsonl", "record_indices": [0], "confirm": True},
                dry_run=False,
            )
            source_text = (root / "docs-viewer/source/library/alpha.md").read_text(encoding="utf-8")
            backup_dir = root / payload["backup_dir"]
            manifest = json.loads((backup_dir / "manifest.json").read_text(encoding="utf-8"))
            backup_exists = backup_dir.exists()
            backup_source_exists = (backup_dir / "alpha.md").exists()
    finally:
        docs_management.write_rebuild.perform_source_write_and_rebuild = original_rebuild

    assert payload["ok"] is True
    assert payload["summary_apply_written"] is True
    assert payload["counts"]["updates"] == 1
    assert payload["backup_dir"].startswith("var/docs/backups/")
    assert payload["rebuild"]["docs"]["mode"] == "targeted"
    assert payload["rebuild"]["docs"]["doc_ids"] == ["alpha"]
    assert payload["rebuild"]["search"]["doc_ids"] == ["alpha"]
    assert payload["rebuild"]["diagnostics"]["docs"]["build_mode"] == "targeted"
    assert backup_exists
    assert backup_source_exists
    assert manifest["operation"] == "documents-summary-apply"
    assert manifest["metadata"]["updated_doc_ids"] == ["alpha"]
    assert "last_updated: 2026-05-01" in source_text
    assert "summary: New summary." in source_text


def test_library_import_summary_apply_skips_unchanged_and_missing_summary_rows() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "alpha.md", {"doc_id": "alpha", "title": "Alpha", "summary": "Same summary."})
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library"})
        write_staged(
            root,
            "summaries.jsonl",
            [
                {"doc_id": "alpha", "title": "Alpha", "summary": "Same summary."},
                {"doc_id": "library", "title": "Library"},
            ],
        )
        payload = handle_documents_import_apply(
            root,
            {"data_domain": "library", "operation": "apply", "apply_action": "summary_apply", "staged_filename": "summaries.jsonl", "record_indices": [0, 1]},
            dry_run=True,
        )

    assert payload["ok"] is True
    assert payload["counts"]["updates"] == 0
    assert payload["counts"]["skipped"] == 2
    assert {item["reason"] for item in payload["skipped"]} == {"unchanged", "missing_summary"}


def test_library_import_hierarchy_apply_preflight_reports_missing_target_doc() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
        write_library_doc(root, "alpha.md", {"doc_id": "alpha", "title": "Alpha", "parent_id": "library"})
        write_staged(
            root,
            "hierarchy.jsonl",
            [
                {"doc_id": "alpha", "title": "Alpha", "parent_id": ""},
                {"doc_id": "missing", "title": "Missing", "parent_id": "library"},
            ],
        )
        payload = handle_documents_import_apply(
            root,
            {"data_domain": "library", "operation": "apply", "apply_action": "hierarchy_apply", "staged_filename": "hierarchy.jsonl", "record_indices": [0, 1]},
            dry_run=True,
        )

    assert payload["ok"] is False
    assert payload["counts"]["changed"] == 1
    assert payload["counts"]["errors"] == 1
    assert payload["errors"][0]["reason"] == "missing_target_doc"
    assert payload["hierarchy_apply_written"] is False


def test_library_import_hierarchy_apply_creates_backup_and_preserves_sort_order() -> None:
    original_rebuild = stub_rebuild()
    try:
        with make_repo() as temp:
            root = Path(temp)
            write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
            write_library_doc(
                root,
                "alpha.md",
                {
                    "doc_id": "alpha",
                    "title": "Alpha",
                    "added_date": "2026-05-01",
                    "last_updated": "2026-05-01",
                    "parent_id": "library",
                    "sort_order": 30,
                },
            )
            write_staged(
                root,
                "hierarchy.jsonl",
                [
                    {"doc_id": "library", "title": "Library", "parent_id": "external-root"},
                    {"doc_id": "alpha", "title": "Alpha", "parent_id": ""},
                ],
            )
            payload = handle_documents_import_apply(
                root,
                {"data_domain": "library", "operation": "apply", "apply_action": "hierarchy_apply", "staged_filename": "hierarchy.jsonl", "record_indices": [1], "confirm": True},
                dry_run=False,
            )
            alpha_text = (root / "docs-viewer/source/library/alpha.md").read_text(encoding="utf-8")
            library_text = (root / "docs-viewer/source/library/library.md").read_text(encoding="utf-8")
            backup_dir = root / payload["backup_dir"]
            manifest = json.loads((backup_dir / "manifest.json").read_text(encoding="utf-8"))
    finally:
        docs_management.write_rebuild.perform_source_write_and_rebuild = original_rebuild

    assert payload["ok"] is True
    assert payload["hierarchy_apply_written"] is True
    assert payload["counts"]["changed"] == 1
    assert payload["backup_dir"].startswith("var/docs/backups/")
    assert payload["rebuild"]["docs"]["mode"] == "targeted"
    assert payload["rebuild"]["docs"]["doc_ids"] == ["alpha"]
    assert payload["rebuild"]["search"]["doc_ids"] == ["alpha"]
    assert payload["rebuild"]["diagnostics"]["search"]["mode"] == "targeted"
    assert manifest["operation"] == "documents-hierarchy-apply"
    assert manifest["metadata"]["updated_doc_ids"] == ["alpha"]
    assert "last_updated: 2026-05-01" in alpha_text
    assert 'parent_id: ""' in alpha_text
    assert "sort_order: 30" in alpha_text
    assert "parent_id: external-root" not in library_text


def test_library_import_hierarchy_apply_allows_unknown_parent_and_dry_run_no_write() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "alpha.md", {"doc_id": "alpha", "title": "Alpha", "parent_id": "library"})
        write_staged(root, "hierarchy.jsonl", [{"doc_id": "alpha", "title": "Alpha", "parent_id": "external-root"}])
        payload = handle_documents_import_apply(
            root,
            {"data_domain": "library", "operation": "apply", "apply_action": "hierarchy_apply", "staged_filename": "hierarchy.jsonl", "record_indices": [0], "confirm": True},
            dry_run=True,
        )
        source_text = (root / "docs-viewer/source/library/alpha.md").read_text(encoding="utf-8")

    assert payload["ok"] is True
    assert payload["hierarchy_apply_written"] is False
    assert payload["counts"]["changed"] == 1
    assert payload["counts"]["warnings"] == 1
    assert payload["warnings"][0]["reason"] == "unknown_parent_id"
    assert "parent_id: library" in source_text


def test_library_import_hierarchy_apply_reports_unchanged_and_skipped_rows() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
        write_library_doc(root, "alpha.md", {"doc_id": "alpha", "title": "Alpha", "parent_id": "library"})
        write_staged(
            root,
            "hierarchy.jsonl",
            [
                {"doc_id": "alpha", "title": "Alpha", "parent_id": "library"},
                {"doc_id": "library", "title": "Library", "parent_id": "library"},
            ],
        )
        payload = handle_documents_import_apply(
            root,
            {"data_domain": "library", "operation": "apply", "apply_action": "hierarchy_apply", "staged_filename": "hierarchy.jsonl", "record_indices": [0, 1]},
            dry_run=True,
        )

    assert payload["ok"] is True
    assert payload["counts"]["changed"] == 0
    assert payload["counts"]["unchanged"] == 1
    assert payload["counts"]["skipped"] == 1
    assert payload["skipped"][0]["reason"] == "self_parent_id"


def main() -> None:
    tests = [
        test_library_import_files_lists_json_and_jsonl_only,
        test_library_import_preview_writes_when_not_dry_run,
        test_library_import_preview_dry_run_reports_without_writing,
        test_documents_import_rejects_unconfigured_data_domain,
        test_docs_export_summary_text_uses_context_aware_document_plural,
        test_html_import_create_uses_staged_filename_for_doc_id_and_path,
        test_html_import_copies_role_marked_interactive_assets,
        test_html_import_reports_role_marked_interactive_assets_in_preview_only,
        test_html_import_confirms_existing_role_marked_interactive_asset_target,
        test_source_import_files_list_html_and_markdown,
        test_markdown_import_create_wraps_body_with_generated_front_matter,
        test_text_import_autolinks_plain_urls,
        test_svg_import_strips_unsafe_content,
        test_image_import_creates_media_path_plan_wrapper,
        test_media_path_comes_from_scope_config,
        test_html_import_extracts_inline_png_to_staged_media_plan,
        test_markdown_import_extracts_inline_png_with_incremented_filename,
        test_inline_media_write_skips_invalid_data_urls_before_valid_images,
        test_file_media_import_creates_file_media_path_plan_wrapper,
        test_markdown_package_import_rewrites_media_and_materializes_outputs,
        test_markdown_package_image_conversion_does_not_upscale,
        test_markdown_package_import_reports_unresolved_and_unsupported_links,
        test_import_collision_prompts_for_replacement_doc_id,
        test_library_import_summary_apply_preflight_reports_missing_target_doc,
        test_library_import_summary_apply_creates_backup_and_writes_source,
        test_library_import_summary_apply_skips_unchanged_and_missing_summary_rows,
        test_library_import_hierarchy_apply_preflight_reports_missing_target_doc,
        test_library_import_hierarchy_apply_creates_backup_and_preserves_sort_order,
        test_library_import_hierarchy_apply_allows_unknown_parent_and_dry_run_no_write,
        test_library_import_hierarchy_apply_reports_unchanged_and_skipped_rows,
    ]
    for test in tests:
        test()


if __name__ == "__main__":
    main()
