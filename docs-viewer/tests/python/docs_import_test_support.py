"""Shared fixtures for Docs import service tests."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_DIR = REPO_ROOT / "docs-viewer" / "services"
DATA_SHARING_DIR = REPO_ROOT / "data-sharing"
ANALYTICS_SERVER_DIR = REPO_ROOT / "analytics-app" / "app" / "server"
ANALYTICS_PACKAGE_DIR = ANALYTICS_SERVER_DIR / "analytics_app"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
for path in (DOCS_DIR, DATA_SHARING_DIR, ANALYTICS_SERVER_DIR, ANALYTICS_PACKAGE_DIR):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)


import docs_import_source_service as import_source_service  # noqa: E402
import docs_html_import  # noqa: E402
import docs_source_model as source_model  # noqa: E402
import docs_write_rebuild as write_rebuild  # noqa: E402
from docs_management_import_service import import_source_dependencies  # noqa: E402
from adapters.documents import prepare as documents_prepare  # noqa: E402
from adapters.documents import returned as documents_returned  # noqa: E402
import analytics_data_sharing_api  # noqa: E402


def handle_documents_import_files(root: Path, data_domain: str) -> dict[str, object]:
    adapter = analytics_data_sharing_api.data_sharing_service.resolve_for_service(root, data_domain, "list_returned")
    return documents_returned.list_returned_packages(
        root,
        data_domain,
        adapter=adapter,
        dependencies=analytics_data_sharing_api.documents_data_sharing_dependencies(),
    )


def handle_documents_import_preview(root: Path, body: dict[str, object], dry_run: bool) -> dict[str, object]:
    adapter = analytics_data_sharing_api.data_sharing_service.resolve_for_service(root, body.get("data_domain"), "review")
    return documents_returned.review_returned_package(
        root,
        body,
        dry_run,
        adapter=adapter,
        dependencies=analytics_data_sharing_api.documents_data_sharing_dependencies(),
    )


def handle_documents_import_apply(root: Path, body: dict[str, object], dry_run: bool) -> dict[str, object]:
    adapter = analytics_data_sharing_api.data_sharing_service.resolve_for_service(root, body.get("data_domain"), "apply")
    return documents_returned.apply_returned_changes(
        root,
        body,
        dry_run,
        adapter=adapter,
        dependencies=analytics_data_sharing_api.documents_data_sharing_dependencies(),
    )


def handle_docs_export(root: Path, body: dict[str, object], dry_run: bool) -> dict[str, object]:
    adapter = analytics_data_sharing_api.data_sharing_service.resolve_for_service(root, body.get("data_domain"), "prepare")
    return documents_prepare.prepare_package(
        root,
        body,
        dry_run,
        adapter=adapter,
        dependencies=analytics_data_sharing_api.documents_data_sharing_dependencies(),
    )


def make_repo() -> tempfile.TemporaryDirectory:
    temp_dir = tempfile.TemporaryDirectory()
    root = Path(temp_dir.name)
    (root / "site-tools/config").mkdir(parents=True, exist_ok=True); (root / "site-tools/config/site-tools.json").write_text("{\"schema_version\":\"site_tools_config_v1\"}\n", encoding="utf-8")
    (root / "var/analytics/data-sharing/library/import-staging").mkdir(parents=True, exist_ok=True)
    write_scope_config(root)
    write_library_doc(root, "library.md", {"doc_id": "library", "title": "Library", "parent_id": ""})
    write_library_doc(root, "alpha.md", {"doc_id": "alpha", "title": "Alpha", "parent_id": "library"})
    config_path = root / "data-sharing/adapters/documents/config/prepare-profiles.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(
            {
                "schema_version": "documents_prepare_profiles_v1",
                "configs": [
                    {
                        "id": "library-document-summaries",
                        "label": "Document summaries",
                        "description": "Exports summary metadata.",
                        "enabled": True,
                        "data_domains": ["library"],
                        "scopes": ["library"],
                        "target": {
                            "format": "jsonl",
                            "record_shape": "document_rows",
                            "include_export_metadata": True,
                        },
                        "output": {
                            "path_pattern": "var/analytics/data-sharing/exports/{data_domain}-{export_id}-{timestamp}.jsonl",
                            "timestamp_format": "%Y%m%d-%H%M%S",
                        },
                        "selection": {
                            "mode": "explicit_doc_ids",
                            "include_descendants": False,
                            "include_non_viewable": True,
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
    adapter_path = root / "data-sharing/config/adapters.json"
    adapter_path.parent.mkdir(parents=True, exist_ok=True)
    adapter_path.write_text(
        json.dumps(
            {
                "schema_version": "data_sharing_adapters_v2",
                "paths": {
                    "outbound_package_root": "var/analytics/data-sharing/exports",
                    "returned_package_staging_root": "var/analytics/data-sharing/import-staging",
                    "review_output_root": "var/analytics/data-sharing/import-preview",
                },
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
                                "app": "docs-viewer",
                                "label": "Library",
                                "scope": "library",
                                "status": "active",
                                "selection_model": "documents",
                                "source_write_targets": {
                                    "documents": "docs-viewer/source/library",
                                },
                                "sources": {
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


def write_scope_config(root: Path) -> None:
    path = root / "docs-viewer/config/scopes/docs_scopes.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "docs_scopes_v1",
                "scopes": [
                    {
                        "scope_id": "library",
                        "scope_type": "public",
                        "source": "docs-viewer/source/library",
                        "media_path_prefix": "docs/library",
                        "output": "docs-viewer/generated/docs/library",
                        "search_output": "docs-viewer/generated/search/library/index.json",
                        "publish_output": "site/assets/data/docs/scopes/library",
                        "publish_search_output": "site/assets/data/search/library/index.json",
                        "viewer_base_url": "/library/",
                        "include_scope_param": False,
                        "default_doc_id": "library",
                        "allow_unresolved_parent_ids": True,
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def write_staged(root: Path, filename: str, payload: object, scope: str = "library") -> None:
    del scope
    path = root / "var/analytics/data-sharing/import-staging" / filename
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
    original = write_rebuild.perform_source_write_and_rebuild

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

    write_rebuild.perform_source_write_and_rebuild = fake_rebuild
    return original


def handle_import_source(root: Path, body: dict[str, object], dry_run: bool) -> dict[str, object]:
    return import_source_service.handle_import_source(
        root,
        body,
        dry_run,
        import_source_dependencies(),
    )
