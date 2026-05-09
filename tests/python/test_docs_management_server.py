#!/usr/bin/env python3
"""Focused checks for Docs Management Server handling of conventional archive docs."""

from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_MANAGEMENT_SERVER_PATH = REPO_ROOT / "scripts" / "docs" / "docs_management_server.py"


def load_docs_management_server_module():
    scripts_docs_dir = DOCS_MANAGEMENT_SERVER_PATH.parent
    if str(scripts_docs_dir) not in sys.path:
        sys.path.insert(0, str(scripts_docs_dir))
    spec = importlib.util.spec_from_file_location("docs_management_server", DOCS_MANAGEMENT_SERVER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load docs_management_server.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


docs_management_server = load_docs_management_server_module()


def write_doc(root: Path, filename: str, front_matter: dict[str, object], body: str = "") -> None:
    lines = ["---"]
    for key, value in front_matter.items():
        lines.append(f"{key}: {docs_management_server.format_front_matter_value(value)}")
    lines.extend(["---", "", body or f"# {front_matter['title']}", ""])
    path = root / "_docs" / filename
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
        repo_root / "assets/studio/data/export_import_adapters.json",
        {
            "schema_version": "export_import_adapters_v1",
            "dispatch": [
                {"data_domain": "library", "operation": "export", "adapter_id": "documents"},
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
                                "source_root": "_docs_library",
                            },
                            "sources": {
                                "docs_index": "assets/data/docs/scopes/library/index.json",
                                "docs_payload_root": "assets/data/docs/scopes/library/by-id",
                                "source_root": "_docs_library",
                            },
                            "config": {
                                "export_configs_path": "assets/studio/data/library_export_configs.json",
                            },
                        }
                    },
                    "capabilities": ["export"],
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
    write_json(root / "assets/data/docs/scopes/studio/index.json", {"docs": docs})
    write_json(root / "assets/data/docs/scopes/studio/by-id/archive.json", {"doc_id": "archive"})
    write_json(root / "assets/data/docs/scopes/studio/by-id/child.json", {"doc_id": "child"})
    write_json(root / "assets/data/search/studio/index.json", {"entries": [{"doc_id": "child"}]})


def test_archive_doc_is_editable_in_dry_run() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        result = docs_management_server.handle_update_metadata(
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
        result = docs_management_server.handle_update_metadata(
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
        result = docs_management_server.handle_update_viewability(
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
        result = docs_management_server.preview_delete(repo_root, "studio", "archive")

    assert result["allowed"] is False
    assert result["blockers"] == ["1 child docs still depend on this parent"]


def test_archive_command_noops_on_archive_parent() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        result = docs_management_server.handle_archive(
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
        payload = docs_management_server.capabilities_payload(repo_root)

    assert payload["capabilities"]["generated_data_reads"] is True
    assert payload["capabilities"]["scopes"]["studio"]["generated_data_reads"] is True
    assert payload["capabilities"]["scopes"]["studio"]["generated_search_reads"] is True


class FakeHandler:
    def __init__(self) -> None:
        self.headers: dict[str, str] = {}
        self.response_status: int | None = None
        self.sent_headers: dict[str, str] = {}
        self.wfile = io.BytesIO()

    def send_response(self, status: int) -> None:
        self.response_status = status

    def send_header(self, key: str, value: str) -> None:
        self.sent_headers[key] = value

    def end_headers(self) -> None:
        pass


def test_json_responses_are_not_cached() -> None:
    handler = FakeHandler()
    docs_management_server.write_response(handler, docs_management_server.HTTPStatus.OK, {"ok": True})

    assert handler.sent_headers["Cache-Control"] == "no-store"


def test_docs_export_request_passes_target_format() -> None:
    calls: list[dict[str, object]] = []
    original_build_export = docs_management_server.build_export

    def fake_build_export(**kwargs):
        calls.append(kwargs)
        return {
            "ok": True,
            "target_format": kwargs["target_format"],
            "output_file": "var/studio/export-import/library/exports/test.json",
            "output_written": False,
            "counts": {"selected": 1, "exported": 1, "skipped": 0, "failed": 0, "truncated": 0},
            "issue_counts": {"errors": 0, "warnings": 0},
        }

    docs_management_server.build_export = fake_build_export
    try:
        with make_repo() as temp_path:
            repo_root = Path(temp_path)
            result = docs_management_server.handle_docs_export(
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
            )
    finally:
        docs_management_server.build_export = original_build_export

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
        test_json_responses_are_not_cached,
        test_docs_export_request_passes_target_format,
    ]
    for test in tests:
        test()


if __name__ == "__main__":
    main()
