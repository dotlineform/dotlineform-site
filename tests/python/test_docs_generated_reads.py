#!/usr/bin/env python3
"""Focused checks for generated Docs Viewer read helpers."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DOCS_DIR = REPO_ROOT / "scripts" / "docs"
if str(SCRIPTS_DOCS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DOCS_DIR))

import docs_generated_reads as generated_reads  # noqa: E402


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


def test_generated_data_availability_checks_scope_files() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        write_generated_docs(repo_root)

        assert generated_reads.generated_scope_data_available(repo_root, "studio") is True
        assert generated_reads.generated_search_data_available(repo_root, "studio") is True
        assert generated_reads.generated_scope_data_available(repo_root, "library") is False
        assert generated_reads.generated_search_data_available(repo_root, "library") is False


def test_generated_doc_payload_allows_non_viewable_indexed_doc() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        write_generated_docs(repo_root)
        payload = generated_reads.read_generated_doc_payload(repo_root, "studio", "archive")

    assert payload["doc_id"] == "archive"


def test_generated_doc_payload_rejects_unsafe_doc_id() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        write_generated_docs(repo_root)
        try:
            generated_reads.read_generated_doc_payload(repo_root, "studio", "../child")
        except ValueError as exc:
            assert "unsupported characters" in str(exc)
        else:
            raise AssertionError("Expected unsafe generated payload doc_id to be rejected")


def test_generated_doc_payload_requires_index_record() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        write_generated_docs(repo_root)
        write_json(
            repo_root / "assets/data/docs/scopes/studio/by-id/unlisted.json",
            {"doc_id": "unlisted"},
        )
        try:
            generated_reads.read_generated_doc_payload(repo_root, "studio", "unlisted")
        except FileNotFoundError as exc:
            assert "not found" in str(exc)
        else:
            raise AssertionError("Expected unlisted generated payload to be rejected")


def test_generated_doc_payload_rejects_unexpected_content_url() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        write_generated_docs(repo_root)
        write_json(
            repo_root / "assets/data/docs/scopes/studio/index.json",
            {
                "docs": [
                    {
                        "doc_id": "child",
                        "content_url": "/assets/data/docs/scopes/library/by-id/child.json",
                    }
                ]
            },
        )
        try:
            generated_reads.read_generated_doc_payload(repo_root, "studio", "child")
        except RuntimeError as exc:
            assert "unexpected payload path" in str(exc)
        else:
            raise AssertionError("Expected mismatched generated payload path to be rejected")


def test_generated_doc_payload_allows_external_content_url_with_expected_path() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        write_generated_docs(repo_root)
        write_json(
            repo_root / "assets/data/docs/scopes/studio/index.json",
            {
                "docs": [
                    {
                        "doc_id": "child",
                        "content_url": "https://example.com/assets/data/docs/scopes/studio/by-id/child.json",
                    }
                ]
            },
        )
        payload = generated_reads.read_generated_doc_payload(repo_root, "studio", "child")

    assert payload["doc_id"] == "child"


def test_read_generated_json_reports_invalid_json() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        path = Path(temp_path) / "index.json"
        path.write_text("{", encoding="utf-8")
        try:
            generated_reads.read_generated_json(path, "generated docs index for studio")
        except RuntimeError as exc:
            assert "not valid JSON" in str(exc)
        else:
            raise AssertionError("Expected invalid generated JSON to be rejected")


def main() -> None:
    test_generated_data_availability_checks_scope_files()
    test_generated_doc_payload_allows_non_viewable_indexed_doc()
    test_generated_doc_payload_rejects_unsafe_doc_id()
    test_generated_doc_payload_requires_index_record()
    test_generated_doc_payload_rejects_unexpected_content_url()
    test_generated_doc_payload_allows_external_content_url_with_expected_path()
    test_read_generated_json_reports_invalid_json()
    print("Docs generated-read tests OK")


if __name__ == "__main__":
    main()
