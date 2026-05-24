#!/usr/bin/env python3
"""Focused checks for generated Docs Viewer read helpers."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace


REPO_ROOT = Path(__file__).resolve().parents[3]
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
    write_json(
        root / "assets/data/docs/scopes/studio/references/index.json",
        {"targets": [{"target_kind": "work", "target_id": "00638"}]},
    )
    write_json(
        root / "assets/data/docs/scopes/studio/references/by-target/work/00638.json",
        {"target_kind": "work", "target_id": "00638", "references": []},
    )
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


def test_generated_references_reads_scope_index_and_target() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        write_generated_docs(repo_root)

        index_payload = generated_reads.read_generated_references_index(repo_root, "studio")
        target_payload = generated_reads.read_generated_reference_target(repo_root, "studio", "work", "00638")

    assert index_payload["targets"][0]["target_id"] == "00638"
    assert target_payload["target_kind"] == "work"


def test_generated_docs_log_projection_uses_allowlisted_names() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        write_json(repo_root / "studio/workflows/change-requests/generated/search-index.json", {"entries": [{"id": "change-1"}]})

        payload = generated_reads.read_generated_docs_log_projection(repo_root, "search-index")
        try:
            generated_reads.read_generated_docs_log_projection(repo_root, "../schema")
        except ValueError as exc:
            error = str(exc)
        else:
            error = ""

    assert payload["entries"][0]["id"] == "change-1"
    assert "unsupported docs-log projection" in error


def test_generated_reference_target_rejects_unsafe_path_parts() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        write_generated_docs(repo_root)
        try:
            generated_reads.read_generated_reference_target(repo_root, "studio", "../work", "00638")
        except ValueError as exc:
            assert "unsupported characters" in str(exc)
        else:
            raise AssertionError("Expected unsafe reference target kind to be rejected")


def test_generated_doc_paths_use_scope_config_output() -> None:
    original_configs = generated_reads.DOCS_SCOPE_CONFIGS
    generated_reads.DOCS_SCOPE_CONFIGS = {
        **original_configs,
        "research": SimpleNamespace(output=Path("custom/generated/research")),
    }
    try:
        with tempfile.TemporaryDirectory() as temp_path:
            repo_root = Path(temp_path)
            docs = [
                {
                    "doc_id": "research",
                    "content_url": "/custom/generated/research/by-id/research.json",
                }
            ]
            write_json(repo_root / "custom/generated/research/index.json", {"docs": docs})
            write_json(repo_root / "custom/generated/research/by-id/research.json", {"doc_id": "research"})

            assert (
                generated_reads.generated_docs_index_path(repo_root, "research")
                == repo_root / "custom/generated/research/index.json"
            )
            payload = generated_reads.read_generated_doc_payload(repo_root, "research", "research")
    finally:
        generated_reads.DOCS_SCOPE_CONFIGS = original_configs

    assert payload["doc_id"] == "research"


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
    test_generated_references_reads_scope_index_and_target()
    test_generated_docs_log_projection_uses_allowlisted_names()
    test_generated_reference_target_rejects_unsafe_path_parts()
    test_generated_doc_paths_use_scope_config_output()
    test_read_generated_json_reports_invalid_json()
    print("Docs generated-read tests OK")


if __name__ == "__main__":
    main()
