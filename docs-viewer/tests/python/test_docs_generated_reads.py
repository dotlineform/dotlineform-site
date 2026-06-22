#!/usr/bin/env python3
"""Focused checks for generated Docs Viewer read helpers."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
if str(DOCS_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(DOCS_SERVICES_DIR))

import docs_generated_reads as generated_reads  # noqa: E402
from docs_scope_config import load_docs_scope_configs  # noqa: E402

EXTERNAL_DATA_ROOT_MARKER = "$DOTLINEFORM_PROJECTS_BASE_DIR/docs-viewer"


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def scope_config(scope_id: str, output: str, search_output: str) -> dict[str, object]:
    public_scope = scope_id in {"library", "analysis"}
    return {
        "scope_id": scope_id,
        "source": f"docs-viewer/source/{scope_id}",
        "media_path_prefix": f"docs/{scope_id}",
        "output": output,
        "search_output": search_output,
        "publish_output": f"site/assets/data/docs/scopes/{scope_id}" if public_scope else output,
        "publish_search_output": f"site/assets/data/search/{scope_id}/index.json" if public_scope else search_output,
        "viewer_base_url": f"/{scope_id}/" if public_scope else "/docs/",
        "include_scope_param": not public_scope,
        "default_doc_id": scope_id,
    }


def external_scope_config(scope_id: str, external_root: Path) -> dict[str, object]:
    del external_root
    return {
        "scope_id": scope_id,
        "scope_type": "local_external",
        "external_data_root": EXTERNAL_DATA_ROOT_MARKER,
        "source": f"{EXTERNAL_DATA_ROOT_MARKER}/source/{scope_id}",
        "media_path_prefix": f"docs/{scope_id}",
        "output": f"{EXTERNAL_DATA_ROOT_MARKER}/generated/docs/{scope_id}",
        "search_output": f"{EXTERNAL_DATA_ROOT_MARKER}/generated/search/{scope_id}/index.json",
        "viewer_base_url": "/docs/",
        "include_scope_param": True,
        "default_doc_id": scope_id,
    }


def write_scope_config(root: Path, extra_scopes: list[dict[str, object]] | None = None) -> None:
    scopes = [
        scope_config("studio", "docs-viewer/generated/docs/studio", "docs-viewer/generated/search/studio/index.json"),
        scope_config("library", "docs-viewer/generated/docs/library", "docs-viewer/generated/search/library/index.json"),
        scope_config("analysis", "docs-viewer/generated/docs/analysis", "docs-viewer/generated/search/analysis/index.json"),
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
            "doc_id": "non-viewable-doc",
            "title": "Non-viewable Doc",
            "viewable": False,
            "content_url": "/docs-viewer/generated/docs/studio/by-id/non-viewable-doc.json",
        },
        {
            "scope": "studio",
            "doc_id": "child",
            "title": "Child",
            "viewable": True,
            "content_url": "/docs-viewer/generated/docs/studio/by-id/child.json",
        },
    ]
    write_json(
        root / "docs-viewer/generated/docs/studio/index-tree.json",
        {"schema": "docs_index_tree_v1", "viewer_options": {}, "docs": docs},
    )
    write_json(
        root / "docs-viewer/generated/docs/studio/recently-added.json",
        {"schema": "docs_recently_added_v1", "limit": 10, "docs": [docs[1]]},
    )
    write_json(root / "docs-viewer/generated/docs/studio/by-id/non-viewable-doc.json", {"doc_id": "non-viewable-doc"})
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


def write_public_generated_docs(root: Path) -> None:
    write_scope_config(root)
    docs = [
        {
            "doc_id": "library",
            "title": "Library",
            "content_url": "/assets/data/docs/scopes/library/by-id/library.json",
            "children": [
                {
                    "doc_id": "child",
                    "title": "Child",
                    "content_url": "/assets/data/docs/scopes/library/by-id/child.json",
                }
            ],
        }
    ]
    write_json(
        root / "docs-viewer/generated/docs/library/index-tree.json",
        {"schema": "docs_index_tree_v1", "viewer_options": {}, "docs": docs},
    )
    write_json(
        root / "docs-viewer/generated/docs/library/recently-added.json",
        {"schema": "docs_recently_added_v1", "limit": 10, "docs": docs},
    )
    write_json(
        root / "docs-viewer/generated/docs/library/by-id/library.json",
        {"title": "Library", "content_html": "<h1>Library</h1>"},
    )
    write_json(
        root / "docs-viewer/generated/docs/library/by-id/child.json",
        {"title": "Child", "content_html": "<h1>Child</h1>"},
    )


def test_generated_data_availability_checks_scope_files() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        write_generated_docs(repo_root)

        assert generated_reads.generated_scope_data_available(repo_root, "studio") is True
        assert generated_reads.generated_search_data_available(repo_root, "studio") is True
        assert generated_reads.generated_scope_data_available(repo_root, "library") is False
        assert generated_reads.generated_search_data_available(repo_root, "library") is False


def test_docs_scope_config_default_doc_id_is_optional() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        config = scope_config("moments", "docs-viewer/generated/docs/moments", "docs-viewer/generated/search/moments/index.json")
        config["default_doc_id"] = ""
        write_scope_config(repo_root, extra_scopes=[config])

        configs = load_docs_scope_configs(repo_root)

    assert configs["moments"].default_doc_id == ""


def test_generated_doc_payload_allows_non_viewable_tree_doc() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        write_generated_docs(repo_root)
        payload = generated_reads.read_generated_doc_payload(repo_root, "studio", "non-viewable-doc")

    assert payload["doc_id"] == "non-viewable-doc"


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


def test_generated_doc_payload_requires_tree_record() -> None:
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
            raise AssertionError("Expected generated payload missing from index tree to be rejected")


def test_generated_doc_payload_rejects_unexpected_content_url() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        write_generated_docs(repo_root)
        write_json(
            repo_root / "docs-viewer/generated/docs/studio/index-tree.json",
            {
                "schema": "docs_index_tree_v1",
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
            repo_root / "docs-viewer/generated/docs/studio/index-tree.json",
            {
                "schema": "docs_index_tree_v1",
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


def test_generated_tree_and_recently_added_reads_scope_payloads() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        write_generated_docs(repo_root)

        index_tree = generated_reads.read_generated_docs_index_tree(repo_root, "studio")
        recently_added = generated_reads.read_generated_recently_added(repo_root, "studio")

    assert index_tree["schema"] == "docs_index_tree_v1"
    assert index_tree["docs"][0]["doc_id"] == "non-viewable-doc"
    assert recently_added["schema"] == "docs_recently_added_v1"
    assert recently_added["docs"][0]["doc_id"] == "child"


def test_public_generated_doc_payload_uses_tree_without_flat_index() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        write_public_generated_docs(repo_root)
        payload = generated_reads.read_generated_doc_payload(repo_root, "library", "library")
        child_payload = generated_reads.read_generated_doc_payload(repo_root, "library", "child")

        assert payload["title"] == "Library"
        assert child_payload["title"] == "Child"
        assert generated_reads.generated_scope_data_available(repo_root, "library") is True


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
                "children": [
                    {
                        "doc_id": "finding",
                        "content_url": "/custom/generated/research/by-id/finding.json",
                    }
                ],
            }
        ]
        write_json(repo_root / "custom/generated/research/index-tree.json", {"schema": "docs_index_tree_v1", "docs": docs})
        write_json(repo_root / "custom/generated/research/by-id/research.json", {"doc_id": "research"})
        write_json(repo_root / "custom/generated/research/by-id/finding.json", {"doc_id": "finding"})

        assert (
            generated_reads.generated_docs_index_tree_path(repo_root, "research")
            == repo_root / "custom/generated/research/index-tree.json"
        )
        payload = generated_reads.read_generated_doc_payload(repo_root, "research", "finding")

    assert payload["doc_id"] == "finding"


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


def test_generated_reads_support_external_local_scope_payloads() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        projects_root = (repo_root.parent / f"{repo_root.name}-external").resolve()
        external_root = projects_root / "docs-viewer"
        external_root.mkdir(parents=True)
        old_projects_base = os.environ.get("DOTLINEFORM_PROJECTS_BASE_DIR")
        os.environ["DOTLINEFORM_PROJECTS_BASE_DIR"] = projects_root.as_posix()
        write_scope_config(repo_root, [external_scope_config("private", external_root)])
        docs_root = external_root / "generated/docs/private"
        write_json(
            docs_root / "index-tree.json",
            {
                "schema": "docs_index_tree_v1",
                "docs": [
                    {
                        "doc_id": "private",
                        "content_url": "/docs/generated/payload?scope=private&doc_id=private",
                    }
                ],
            },
        )
        write_json(docs_root / "by-id/private.json", {"doc_id": "private"})
        write_json(external_root / "generated/search/private/index.json", {"entries": [{"id": "private"}]})

        try:
            payload = generated_reads.read_generated_doc_payload(repo_root, "private", "private")
            search = generated_reads.read_generated_search_index(repo_root, "private")
        finally:
            if old_projects_base is None:
                os.environ.pop("DOTLINEFORM_PROJECTS_BASE_DIR", None)
            else:
                os.environ["DOTLINEFORM_PROJECTS_BASE_DIR"] = old_projects_base

    assert payload == {"doc_id": "private"}
    assert search["entries"] == [{"id": "private"}]


def test_read_generated_json_reports_invalid_json() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        path = Path(temp_path) / "index-tree.json"
        path.write_text("{", encoding="utf-8")
        try:
            generated_reads.read_generated_json(path, "generated docs index tree for studio")
        except RuntimeError as exc:
            assert "not valid JSON" in str(exc)
        else:
            raise AssertionError("Expected invalid generated JSON to be rejected")


def main() -> None:
    test_generated_data_availability_checks_scope_files()
    test_generated_doc_payload_allows_non_viewable_tree_doc()
    test_generated_doc_payload_rejects_unsafe_doc_id()
    test_generated_doc_payload_requires_tree_record()
    test_generated_doc_payload_rejects_unexpected_content_url()
    test_generated_doc_payload_allows_external_content_url_with_expected_path()
    test_generated_references_reads_scope_index_and_target()
    test_generated_tree_and_recently_added_reads_scope_payloads()
    test_public_generated_doc_payload_uses_tree_without_flat_index()
    test_generated_reference_target_rejects_unsafe_path_parts()
    test_generated_doc_paths_use_scope_config_output()
    test_generated_search_path_uses_scope_config_search_output()
    test_generated_reads_support_external_local_scope_payloads()
    test_read_generated_json_reports_invalid_json()
    print("Docs generated-read tests OK")


if __name__ == "__main__":
    main()
