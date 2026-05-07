#!/usr/bin/env python3
"""Focused checks for Docs Management Library import service handlers."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = REPO_ROOT / "scripts" / "docs"
DOCS_MANAGEMENT_PATH = DOCS_DIR / "docs_management_server.py"


def load_docs_management_module():
    if str(DOCS_DIR) not in sys.path:
        sys.path.insert(0, str(DOCS_DIR))
    spec = importlib.util.spec_from_file_location("docs_management_server", DOCS_MANAGEMENT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load docs_management_server.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


docs_management = load_docs_management_module()


def make_repo() -> tempfile.TemporaryDirectory:
    temp_dir = tempfile.TemporaryDirectory()
    root = Path(temp_dir.name)
    (root / "_config.yml").write_text("title: Test\n", encoding="utf-8")
    (root / "var/studio/export-import/library/import-staging").mkdir(parents=True, exist_ok=True)
    index_path = root / "assets/data/docs/scopes/library/index.json"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    docs = [
        {"doc_id": "library", "title": "Library", "parent_id": "", "published": True, "viewable": True},
        {"doc_id": "alpha", "title": "Alpha", "parent_id": "library", "published": True, "viewable": True},
    ]
    index_path.write_text(json.dumps({"docs": docs}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    payload_root = root / "assets/data/docs/scopes/library/by-id"
    payload_root.mkdir(parents=True, exist_ok=True)
    for doc in docs:
        (payload_root / f"{doc['doc_id']}.json").write_text(
            json.dumps({"doc_id": doc["doc_id"], "title": doc["title"]}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    config_path = root / "assets/studio/data/library_export_configs.json"
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
                            "path_pattern": "var/studio/export-import/{scope}/exports/{export_id}-{timestamp}.jsonl",
                            "timestamp_format": "%Y%m%d-%H%M%S",
                        },
                        "selection": {
                            "mode": "explicit_doc_ids",
                            "include_descendants": False,
                            "include_non_viewable": True,
                            "exclude_archived": False,
                            "exclude_unpublished": True,
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
    adapter_path = root / "assets/studio/data/export_import_adapters.json"
    adapter_path.write_text(
        json.dumps(
            {
                "schema_version": "export_import_adapters_v1",
                "dispatch": [
                    {"data_domain": "library", "operation": "export", "adapter_id": "documents"},
                    {"data_domain": "library", "operation": "import_files", "adapter_id": "documents"},
                    {"data_domain": "library", "operation": "import_preview", "adapter_id": "documents"},
                    {"data_domain": "library", "operation": "summary_apply", "adapter_id": "documents"},
                    {"data_domain": "library", "operation": "hierarchy_apply", "adapter_id": "documents"},
                ],
                "adapters": [
                    {
                        "id": "documents",
                        "module": "documents",
                        "label": "Documents",
                        "data_domains": {
                            "library": {
                                "label": "Library",
                                "scope": "library",
                                "paths": {
                                    "export_root": "var/studio/export-import/library/exports",
                                    "staging_root": "var/studio/export-import/library/import-staging",
                                    "preview_root": "var/studio/export-import/library/import-preview",
                                    "source_root": "_docs_library_src",
                                },
                                "sources": {
                                    "docs_index": "assets/data/docs/scopes/library/index.json",
                                    "docs_payload_root": "assets/data/docs/scopes/library/by-id",
                                    "source_root": "_docs_library_src",
                                },
                                "config": {
                                    "export_configs_path": "assets/studio/data/library_export_configs.json",
                                },
                            }
                        },
                        "capabilities": [
                            "export",
                            "import_files",
                            "import_preview",
                            "summary_apply",
                            "hierarchy_apply",
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
    path = root / "var/studio/export-import" / scope / "import-staging" / filename
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


def write_library_doc(root: Path, filename: str, front_matter: dict[str, object], body: str = "# Body\n") -> None:
    lines = ["---"]
    for key, value in front_matter.items():
        lines.append(f"{key}: {docs_management.format_front_matter_value(value)}")
    lines.extend(["---", "", body])
    path = root / "_docs_library_src" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def stub_rebuild():
    original = docs_management.perform_source_write_and_rebuild

    def fake_rebuild(repo_root, scope, changed_paths, write_operation, **kwargs):
        write_operation()
        return {
            "ok": True,
            "steps": [],
            "search": {"mode": "targeted", "doc_ids": kwargs.get("search_doc_ids") or []},
        }

    docs_management.perform_source_write_and_rebuild = fake_rebuild
    return original


def test_library_import_files_lists_json_and_jsonl_only() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged(root, "summaries.jsonl", [{"doc_id": "alpha", "title": "Alpha"}])
        write_staged(root, "relationships.json", {"documents": []})
        (root / "var/studio/export-import/library/import-staging/notes.txt").write_text("ignore\n", encoding="utf-8")
        payload = docs_management.handle_documents_import_files(root, "library")

    assert payload["ok"] is True
    assert payload["scope"] == "library"
    assert payload["staging_root"] == "var/studio/export-import/library/import-staging"
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
        payload = docs_management.handle_documents_import_preview(
            root,
            {"data_domain": "library", "operation": "summary_apply", "staged_filename": "summaries.jsonl"},
            dry_run=False,
        )
        preview_paths = sorted((root / "var/studio/export-import/library/import-preview").glob("alpha-*.md"))
        tree_paths = sorted((root / "var/studio/export-import/library/import-preview").glob("summaries-tree-*.md"))
        preview_text = preview_paths[0].read_text(encoding="utf-8")

    assert payload["ok"] is True
    assert payload["preview_written"] is True
    assert len(preview_paths) == 1
    assert len(tree_paths) == 1
    assert f"var/studio/export-import/library/import-preview/{preview_paths[0].name}" in [
        item["path"] for item in payload["preview_files"]
    ]
    assert payload["summary_text"] == "Generated 2 Library import preview files."
    assert "Preview summary." in preview_text


def test_library_import_preview_dry_run_reports_without_writing() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged(root, "summaries.jsonl", [{"doc_id": "alpha", "title": "Alpha"}])
        payload = docs_management.handle_documents_import_preview(
            root,
            {"data_domain": "library", "operation": "summary_apply", "staged_filename": "summaries.jsonl"},
            dry_run=True,
        )
        preview_exists = list((root / "var/studio/export-import/library/import-preview").glob("alpha-*.md"))

    assert payload["ok"] is True
    assert payload["preview_written"] is False
    assert payload["preview_files"][0]["path"].startswith("var/studio/export-import/library/import-preview/alpha-")
    assert payload["preview_files"][0]["path"].endswith(".md")
    assert payload["summary_text"] == "Validated 1 Library import preview file without writing."
    assert preview_exists == []


def test_documents_import_rejects_unconfigured_data_domain() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged(root, "works.jsonl", [{"doc_id": "work-1", "title": "Work 1"}], scope="catalogue")
        try:
            docs_management.handle_documents_import_preview(
                root,
                {"data_domain": "catalogue", "staged_filename": "works.jsonl"},
                dry_run=True,
            )
        except ValueError as error:
            message = str(error)
        else:
            raise AssertionError("unconfigured data domain should fail closed")

    assert "no export/import adapter configured for catalogue/import_preview" in message


def test_docs_export_summary_text_uses_context_aware_document_plural() -> None:
    with make_repo() as temp:
        root = Path(temp)
        singular = docs_management.handle_docs_export(
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
        plural = docs_management.handle_docs_export(
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

    assert singular["summary_text"].startswith("Validated export 1 document to ")
    assert plural["summary_text"].startswith("Validated export 2 documents to ")


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
        validation_globals = docs_management.generate_import_preview.__globals__
        original_validation = validation_globals["validate_markdown_with_jekyll"]
        validation_globals["validate_markdown_with_jekyll"] = lambda repo_root, markdown: {
            "ok": True,
            "html_chars": len(markdown),
            "renderer": "stub",
        }
        try:
            payload = docs_management.handle_import_html(
                root,
                {"scope": "library", "staged_filename": "compact-name.html"},
                dry_run=False,
            )
        finally:
            docs_management.perform_source_write_and_rebuild = original_rebuild
            validation_globals["validate_markdown_with_jekyll"] = original_validation

        source_path = root / "_docs_library_src/compact-name.md"
        source_exists = source_path.exists()
        source_text = source_path.read_text(encoding="utf-8")

    assert payload["ok"] is True
    assert payload["operation"] == "create"
    assert payload["doc_id"] == "compact-name"
    assert payload["path"] == "_docs_library_src/compact-name.md"
    assert payload["title"] == "An Overly Descriptive Document Title"
    assert payload["import_preview"]["proposed_doc_id_source"] == "filename"
    assert source_exists
    assert "doc_id: compact-name" in source_text
    assert "title: An Overly Descriptive Document Title" in source_text


def test_source_import_files_list_html_and_markdown() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged_html(root, "source.html", "<html><body><h1>Source</h1></body></html>")
        write_staged_markdown(root, "source.md", "# Source\n")

        files = docs_management.list_staged_import_source_files(root)

    by_filename = {item["filename"]: item for item in files}
    assert by_filename["source.html"]["source_format"] == "html"
    assert by_filename["source.md"]["source_format"] == "markdown"


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
        validation_globals = docs_management.generate_import_preview.__globals__
        original_validation = validation_globals["validate_markdown_with_jekyll"]
        validation_globals["validate_markdown_with_jekyll"] = lambda repo_root, markdown: {
            "ok": True,
            "html_chars": len(markdown),
            "renderer": "stub",
        }
        try:
            payload = docs_management.handle_import_source(
                root,
                {"scope": "library", "staged_filename": "markdown-note.md"},
                dry_run=False,
            )
        finally:
            docs_management.perform_source_write_and_rebuild = original_rebuild
            validation_globals["validate_markdown_with_jekyll"] = original_validation

        source_path = root / "_docs_library_src/markdown-note.md"
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
        payload = docs_management.handle_documents_import_apply(
            root,
            {"data_domain": "library", "operation": "summary_apply", "staged_filename": "summaries.jsonl", "record_indices": [0, 1]},
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
            payload = docs_management.handle_documents_import_apply(
                root,
                {"data_domain": "library", "operation": "summary_apply", "staged_filename": "summaries.jsonl", "record_indices": [0], "confirm": True},
                dry_run=False,
            )
            source_text = (root / "_docs_library_src/alpha.md").read_text(encoding="utf-8")
            backup_dir = root / payload["backup_dir"]
            manifest = json.loads((backup_dir / "manifest.json").read_text(encoding="utf-8"))
            backup_exists = backup_dir.exists()
            backup_source_exists = (backup_dir / "alpha.md").exists()
    finally:
        docs_management.perform_source_write_and_rebuild = original_rebuild

    assert payload["ok"] is True
    assert payload["summary_apply_written"] is True
    assert payload["counts"]["updates"] == 1
    assert payload["backup_dir"].startswith("var/docs/backups/")
    assert backup_exists
    assert backup_source_exists
    assert manifest["operation"] == "documents-summary-apply"
    assert manifest["metadata"]["updated_doc_ids"] == ["alpha"]
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
        payload = docs_management.handle_documents_import_apply(
            root,
            {"data_domain": "library", "operation": "summary_apply", "staged_filename": "summaries.jsonl", "record_indices": [0, 1]},
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
        payload = docs_management.handle_documents_import_apply(
            root,
            {"data_domain": "library", "operation": "hierarchy_apply", "staged_filename": "hierarchy.jsonl", "record_indices": [0, 1]},
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
            payload = docs_management.handle_documents_import_apply(
                root,
                {"data_domain": "library", "operation": "hierarchy_apply", "staged_filename": "hierarchy.jsonl", "record_indices": [1], "confirm": True},
                dry_run=False,
            )
            alpha_text = (root / "_docs_library_src/alpha.md").read_text(encoding="utf-8")
            library_text = (root / "_docs_library_src/library.md").read_text(encoding="utf-8")
            backup_dir = root / payload["backup_dir"]
            manifest = json.loads((backup_dir / "manifest.json").read_text(encoding="utf-8"))
    finally:
        docs_management.perform_source_write_and_rebuild = original_rebuild

    assert payload["ok"] is True
    assert payload["hierarchy_apply_written"] is True
    assert payload["counts"]["changed"] == 1
    assert payload["backup_dir"].startswith("var/docs/backups/")
    assert manifest["operation"] == "documents-hierarchy-apply"
    assert manifest["metadata"]["updated_doc_ids"] == ["alpha"]
    assert 'parent_id: ""' in alpha_text
    assert "sort_order: 30" in alpha_text
    assert "parent_id: external-root" not in library_text


def test_library_import_hierarchy_apply_allows_unknown_parent_and_dry_run_no_write() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_library_doc(root, "alpha.md", {"doc_id": "alpha", "title": "Alpha", "parent_id": "library"})
        write_staged(root, "hierarchy.jsonl", [{"doc_id": "alpha", "title": "Alpha", "parent_id": "external-root"}])
        payload = docs_management.handle_documents_import_apply(
            root,
            {"data_domain": "library", "operation": "hierarchy_apply", "staged_filename": "hierarchy.jsonl", "record_indices": [0], "confirm": True},
            dry_run=True,
        )
        source_text = (root / "_docs_library_src/alpha.md").read_text(encoding="utf-8")

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
        payload = docs_management.handle_documents_import_apply(
            root,
            {"data_domain": "library", "operation": "hierarchy_apply", "staged_filename": "hierarchy.jsonl", "record_indices": [0, 1]},
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
