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
    (root / "var/docs/import-staging/library").mkdir(parents=True, exist_ok=True)
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
    return temp_dir


def write_staged(root: Path, filename: str, payload: object) -> None:
    path = root / "var/docs/import-staging/library" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    if filename.endswith(".jsonl"):
        rows = payload if isinstance(payload, list) else [payload]
        path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    else:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_library_import_files_lists_json_and_jsonl_only() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged(root, "summaries.jsonl", [{"doc_id": "alpha", "title": "Alpha"}])
        write_staged(root, "relationships.json", {"documents": []})
        (root / "var/docs/import-staging/library/notes.txt").write_text("ignore\n", encoding="utf-8")
        payload = docs_management.handle_library_import_files(root, "library")

    assert payload["ok"] is True
    assert payload["scope"] == "library"
    assert payload["staging_root"] == "var/docs/import-staging/library"
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
        payload = docs_management.handle_library_import_preview(
            root,
            {"scope": "library", "staged_filename": "summaries.jsonl"},
            dry_run=False,
        )
        preview_text = (root / "var/docs/import-preview/library/alpha.md").read_text(encoding="utf-8")

    assert payload["ok"] is True
    assert payload["preview_written"] is True
    assert payload["preview_files"][0]["path"] == "var/docs/import-preview/library/alpha.md"
    assert payload["summary_text"] == "Generated 1 Library import preview file(s)."
    assert "Preview summary." in preview_text


def test_library_import_preview_dry_run_reports_without_writing() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged(root, "summaries.jsonl", [{"doc_id": "alpha", "title": "Alpha"}])
        payload = docs_management.handle_library_import_preview(
            root,
            {"scope": "library", "staged_filename": "summaries.jsonl"},
            dry_run=True,
        )
        preview_exists = (root / "var/docs/import-preview/library/alpha.md").exists()

    assert payload["ok"] is True
    assert payload["preview_written"] is False
    assert payload["preview_files"][0]["path"] == "var/docs/import-preview/library/alpha.md"
    assert payload["summary_text"] == "Validated 1 Library import preview file(s) without writing."
    assert preview_exists is False


def test_library_import_preview_rejects_non_library_scope() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged(root, "summaries.jsonl", [{"doc_id": "alpha", "title": "Alpha"}])
        try:
            docs_management.handle_library_import_preview(
                root,
                {"scope": "studio", "staged_filename": "summaries.jsonl"},
                dry_run=False,
            )
        except ValueError as exc:
            message = str(exc)
        else:
            raise AssertionError("non-library import scope should fail")

    assert "only supports scope library" in message


def main() -> None:
    tests = [
        test_library_import_files_lists_json_and_jsonl_only,
        test_library_import_preview_writes_when_not_dry_run,
        test_library_import_preview_dry_run_reports_without_writing,
        test_library_import_preview_rejects_non_library_scope,
    ]
    for test in tests:
        test()


if __name__ == "__main__":
    main()
