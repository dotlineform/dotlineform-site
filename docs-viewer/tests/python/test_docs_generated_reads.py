#!/usr/bin/env python3
"""Focused checks for generated Docs Viewer read helpers."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
if str(DOCS_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(DOCS_SERVICES_DIR))

import docs_generated_reads as generated_reads  # noqa: E402


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def scope_config(scope_id: str, output: str, search_output: str) -> dict[str, object]:
    return {
        "scope_id": scope_id,
        "source": f"docs-viewer/source/{scope_id}",
        "media_path_prefix": f"docs/{scope_id}",
        "output": output,
        "search_output": search_output,
        "viewer_base_url": "/docs/" if output.startswith("docs-viewer/") else f"/{scope_id}/",
        "include_scope_param": output.startswith("docs-viewer/"),
        "default_doc_id": scope_id,
    }


def write_scope_config(root: Path, extra_scopes: list[dict[str, object]] | None = None) -> None:
    scopes = [
        scope_config("studio", "docs-viewer/generated/docs/studio", "docs-viewer/generated/search/studio/index.json"),
        scope_config("library", "assets/data/docs/scopes/library", "assets/data/search/library/index.json"),
        scope_config("analysis", "assets/data/docs/scopes/analysis", "assets/data/search/analysis/index.json"),
    ]
    scopes.extend(extra_scopes or [])
    write_json(
        root / "docs-viewer/config/scopes/docs_scopes.json",
        {
            "schema_version": "docs_scopes_v1",
            "scopes": scopes,
        },
    )


def write_generated_docs(root: Path) -> None:
    write_scope_config(root)
    docs = [
        {
            "scope": "studio",
            "doc_id": "hidden-doc",
            "title": "Hidden Doc",
            "viewable": False,
            "content_url": "/docs-viewer/generated/docs/studio/by-id/hidden-doc.json",
        },
        {
            "scope": "studio",
            "doc_id": "child",
            "title": "Child",
            "viewable": True,
            "content_url": "/docs-viewer/generated/docs/studio/by-id/child.json",
        },
    ]
    write_json(root / "docs-viewer/generated/docs/studio/index.json", {"docs": docs})
    write_json(root / "docs-viewer/generated/docs/studio/by-id/hidden-doc.json", {"doc_id": "hidden-doc"})
    write_json(root / "docs-viewer/generated/docs/studio/by-id/child.json", {"doc_id": "child"})
    write_json(
        root / "docs-viewer/generated/docs/studio/references/index.json",
        {"targets": [{"target_kind": "work", "target_id": "00638"}]},
    )
    write_json(
        root / "docs-viewer/generated/docs/studio/references/by-target/work/00638.json",
        {"target_kind": "work", "target_id": "00638", "references": []},
    )
    write_json(root / "docs-viewer/generated/search/studio/index.json", {"entries": [{"doc_id": "child"}]})


def test_generated_data_availability_checks_scope_files() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        write_generated_docs(repo_root)

        assert not (repo_root / "assets/data/docs/scopes/studio/index.json").exists()
        assert not (repo_root / "assets/data/search/studio/index.json").exists()
        assert generated_reads.generated_scope_data_available(repo_root, "studio") is True
        assert generated_reads.generated_search_data_available(repo_root, "studio") is True
        assert generated_reads.generated_scope_data_available(repo_root, "library") is False
        assert generated_reads.generated_search_data_available(repo_root, "library") is False


def test_generated_doc_payload_allows_non_viewable_indexed_doc() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        write_generated_docs(repo_root)
        payload = generated_reads.read_generated_doc_payload(repo_root, "studio", "hidden-doc")

    assert payload["doc_id"] == "hidden-doc"


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
            repo_root / "docs-viewer/generated/docs/studio/by-id/unlisted.json",
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
            repo_root / "docs-viewer/generated/docs/studio/index.json",
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
            repo_root / "docs-viewer/generated/docs/studio/index.json",
            {
                "docs": [
                    {
                        "doc_id": "child",
                        "content_url": "https://example.com/docs-viewer/generated/docs/studio/by-id/child.json",
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
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        write_scope_config(
            repo_root,
            [
                scope_config(
                    "research",
                    "custom/generated/research",
                    "custom/generated/search/research/index.json",
                )
            ],
        )
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

    assert payload["doc_id"] == "research"


def test_generated_search_path_uses_scope_config_search_output() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        write_scope_config(
            repo_root,
            [
                scope_config(
                    "research",
                    "custom/generated/research",
                    "custom/generated/search/research/index.json",
                )
            ],
        )
        write_json(
            repo_root / "custom/generated/search/research/index.json",
            {"entries": [{"doc_id": "research"}]},
        )

        assert (
            generated_reads.generated_search_index_path(repo_root, "research")
            == repo_root / "custom/generated/search/research/index.json"
        )
        payload = generated_reads.read_generated_search_index(repo_root, "research")

    assert payload["entries"][0]["doc_id"] == "research"


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
    test_generated_reference_target_rejects_unsafe_path_parts()
    test_generated_doc_paths_use_scope_config_output()
    test_generated_search_path_uses_scope_config_search_output()
    test_read_generated_json_reports_invalid_json()
    print("Docs generated-read tests OK")


if __name__ == "__main__":
    main()
