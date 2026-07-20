"""Shared fixtures for Docs import service tests."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from repo_factory import (
    data_sharing_workspace_root,
    docs_scope_record,
    make_docs_import_repo,
    write_docs_scope_config,
    write_library_doc as write_fixture_library_doc,
    write_staged_data_file,
    write_staged_import_file,
    write_staged_package_file as write_fixture_staged_package_file,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_DIR = REPO_ROOT / "docs-viewer" / "services"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
for path in (DOCS_DIR,):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)


import docs_import_source_service as import_source_service  # noqa: E402
import docs_source_model as source_model  # noqa: E402
import docs_write_rebuild as write_rebuild  # noqa: E402
from docs_management_import_service import handle_import_source as handle_managed_import_source  # noqa: E402
from docs_document_packages import service as document_package_service  # noqa: E402


def handle_documents_import_preview(root: Path, body: dict[str, object], dry_run: bool) -> dict[str, object]:
    return document_package_service.review_returned(root, {**body, "dry_run": dry_run})


def handle_documents_import_apply(root: Path, body: dict[str, object], dry_run: bool) -> dict[str, object]:
    return document_package_service.apply_returned(root, {**body, "dry_run": dry_run})


def make_repo() -> tempfile.TemporaryDirectory:
    return make_docs_import_repo(source_model.format_front_matter_value)


def write_scope_config(root: Path) -> None:
    write_docs_scope_config(
        root,
        [
            docs_scope_record(
                "library",
                scope_type="public",
                viewer_base_url="/library/",
                include_scope_param=False,
                default_doc_id="library",
                allow_unresolved_parent_ids=True,
                media_provider="repository",
                media_location_root="site/assets/data/docs/scopes/library/media",
                media_served_root="/assets/data/docs/scopes/library/media",
                media_types=("img", "svg", "files", "html"),
            )
        ],
    )


def write_staged(root: Path, filename: str, payload: object, scope: str = "library") -> None:
    del scope
    write_staged_data_file(root, filename, payload)


def write_returned_jsonl(
    root: Path,
    filename: str,
    records: list[dict[str, object]],
    *,
    export_id: str = "ds_20260627T120000Z",
    profile_id: str = "document-content",
    scope: str = "library",
) -> None:
    meta_path = data_sharing_workspace_root() / "meta" / f"{export_id}.meta.json"
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(
        json.dumps(
            {
                "schema_version": "data_sharing_export_meta_v1",
                "export_id": export_id,
                "app": "docs-viewer",
                "adapter_id": "documents",
                "data_domain": "documents",
                "profile_id": profile_id,
                "config_id": profile_id,
                "scope": scope,
                "target_format": "jsonl",
                "record_shape": "document_rows",
                "supports_return_import": True,
                "generated_at": "2026-06-27T12:00:00Z",
                "selected_doc_ids": [
                    str(record.get("doc_id") or "").strip()
                    for record in records
                    if str(record.get("doc_id") or "").strip()
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    write_staged_data_file(
        root,
        filename,
        [
            {
                "record_type": "data_sharing_header",
                "schema_version": "data_sharing_returned_package_v1",
                "export_id": export_id,
            },
            *records,
        ],
    )


def write_staged_html(root: Path, filename: str, html: str) -> None:
    write_staged_import_file(root, filename, html)


def write_staged_markdown(root: Path, filename: str, markdown: str) -> None:
    write_staged_import_file(root, filename, markdown)


def write_staged_text(root: Path, filename: str, text: str) -> None:
    write_staged_import_file(root, filename, text)


def write_staged_bytes(root: Path, filename: str, payload: bytes) -> None:
    write_staged_import_file(root, filename, payload)


def write_staged_package_file(root: Path, package: str, filename: str, payload: bytes | str) -> Path:
    return write_fixture_staged_package_file(root, package, filename, payload)


def write_test_image(path: Path, size: tuple[int, int]) -> None:
    from PIL import Image

    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, (180, 40, 30)).save(path)


def write_library_doc(root: Path, filename: str, front_matter: dict[str, object], body: str = "# Body\n") -> None:
    write_fixture_library_doc(root, filename, front_matter, body=body, format_value=source_model.format_front_matter_value)


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
    return handle_managed_import_source(root, body, dry_run)
