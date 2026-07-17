#!/usr/bin/env python3
"""Focused checks for generated Docs Viewer read helpers."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

from repo_factory import docs_scope_record


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
if str(DOCS_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(DOCS_SERVICES_DIR))

import docs_generated_reads as generated_reads  # noqa: E402
from docs_scope_config import load_docs_scope_configs  # noqa: E402

NON_VIEWABLE_DOC_ID = "d-20260101-000000-000001"
CHILD_DOC_ID = "d-20260101-000000-000002"
LIBRARY_DOC_ID = "d-20260101-000000-000003"
LIBRARY_CHILD_DOC_ID = "d-20260101-000000-000004"
RESEARCH_DOC_ID = "d-20260101-000000-000005"
FINDING_DOC_ID = "d-20260101-000000-000006"
PRIVATE_DOC_ID = "d-20260101-000000-000007"
UNLISTED_DOC_ID = "d-20260101-000000-000008"


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def scope_config(scope_id: str, output: str, search_output: str) -> dict[str, object]:
    public_scope = scope_id in {"library", "analysis"}
    return docs_scope_record(
        scope_id,
        scope_type="public" if public_scope else "local",
        published_docs_path=output,
        published_search_path=search_output,
        viewer_base_url=f"/{scope_id}/" if public_scope else "/docs/",
        include_scope_param=not public_scope,
        default_doc_id=scope_id,
    )


def external_scope_config(scope_id: str, external_root: Path) -> dict[str, object]:
    del external_root
    return docs_scope_record(
        scope_id,
        scope_type="local_external",
        default_doc_id=scope_id,
    )


def write_scope_config(root: Path, extra_scopes: list[dict[str, object]] | None = None) -> None:
    scopes = [
        scope_config("studio", "docs-viewer/published/docs/studio", "docs-viewer/published/search/studio/index.json"),
        scope_config("library", "docs-viewer/published/docs/library", "docs-viewer/published/search/library/index.json"),
        scope_config("analysis", "docs-viewer/published/docs/analysis", "docs-viewer/published/search/analysis/index.json"),
    ]
    scopes.extend(extra_scopes or [])
    write_json(
        root / "docs-viewer/config/scopes/docs_scopes.json",
        {
            "schema_version": "docs_scopes_v2",
            "scopes": scopes,
        },
    )


def write_generated_docs(root: Path) -> None:
    write_scope_config(root)
    docs = [
        {
            "scope": "studio",
            "doc_id": NON_VIEWABLE_DOC_ID,
            "title": "Non-viewable Doc",
            "viewable": False,
            "content_url": f"/docs-viewer/published/docs/studio/by-id/{NON_VIEWABLE_DOC_ID}.json",
        },
        {
            "scope": "studio",
            "doc_id": CHILD_DOC_ID,
            "title": "Child",
            "viewable": True,
            "content_url": f"/docs-viewer/published/docs/studio/by-id/{CHILD_DOC_ID}.json",
        },
    ]
    write_json(
        root / "docs-viewer/published/docs/studio/index-tree.json",
        {"schema": "docs_index_tree_v1", "viewer_options": {}, "docs": docs},
    )
    write_json(
        root / "docs-viewer/published/docs/studio/recent.json",
        {"schema": "docs_recent_v1", "basis": "edited", "limit": 10, "docs": [docs[1]]},
    )
    write_json(root / f"docs-viewer/published/docs/studio/by-id/{NON_VIEWABLE_DOC_ID}.json", {"doc_id": NON_VIEWABLE_DOC_ID})
    write_json(root / f"docs-viewer/published/docs/studio/by-id/{CHILD_DOC_ID}.json", {"doc_id": CHILD_DOC_ID})
    write_json(
        root / "docs-viewer/published/docs/studio/references/index.json",
        {"targets": [{"target_kind": "work", "target_id": "00638"}]},
    )
    write_json(
        root / "docs-viewer/published/docs/studio/references/by-target/work/00638.json",
        {"target_kind": "work", "target_id": "00638", "references": []},
    )
    write_json(root / "docs-viewer/published/search/studio/index.json", {"entries": [{"doc_id": CHILD_DOC_ID}]})


def write_public_generated_docs(root: Path) -> None:
    write_scope_config(root)
    docs = [
        {
            "doc_id": LIBRARY_DOC_ID,
            "title": "Library",
            "content_url": f"/assets/data/docs/scopes/library/by-id/{LIBRARY_DOC_ID}.json",
            "children": [
                {
                    "doc_id": LIBRARY_CHILD_DOC_ID,
                    "title": "Child",
                    "content_url": f"/assets/data/docs/scopes/library/by-id/{LIBRARY_CHILD_DOC_ID}.json",
                }
            ],
        }
    ]
    write_json(
        root / "docs-viewer/published/docs/library/index-tree.json",
        {"schema": "docs_index_tree_v1", "viewer_options": {}, "docs": docs},
    )
    write_json(
        root / "docs-viewer/published/docs/library/recent.json",
        {"schema": "docs_recent_v1", "basis": "edited", "limit": 10, "docs": docs},
    )
    write_json(
        root / f"docs-viewer/published/docs/library/by-id/{LIBRARY_DOC_ID}.json",
        {"title": "Library", "content_html": "<h1>Library</h1>"},
    )
    write_json(
        root / f"docs-viewer/published/docs/library/by-id/{LIBRARY_CHILD_DOC_ID}.json",
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
        config = scope_config("moments", "docs-viewer/published/docs/moments", "docs-viewer/published/search/moments/index.json")
        config["default_doc_id"] = ""
        write_scope_config(repo_root, extra_scopes=[config])

        configs = load_docs_scope_configs(repo_root)

    assert configs["moments"].default_doc_id == ""


def test_generated_doc_payload_allows_non_viewable_tree_doc() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        write_generated_docs(repo_root)
        payload = generated_reads.read_generated_doc_payload(repo_root, "studio", NON_VIEWABLE_DOC_ID)

    assert payload["doc_id"] == NON_VIEWABLE_DOC_ID


def test_generated_doc_payload_rejects_unsafe_doc_id() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        write_generated_docs(repo_root)
        try:
            generated_reads.read_generated_doc_payload(repo_root, "studio", "../child")
        except ValueError as exc:
            assert "immutable document ID format" in str(exc)
        else:
            raise AssertionError("Expected unsafe generated payload doc_id to be rejected")


def test_generated_doc_payload_rejects_legacy_doc_id() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        write_generated_docs(repo_root)
        try:
            generated_reads.read_generated_doc_payload(repo_root, "studio", "child")
        except ValueError as exc:
            assert "immutable document ID format" in str(exc)
        else:
            raise AssertionError("Expected legacy generated payload doc_id to be rejected")


def test_generated_doc_payload_requires_tree_record() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        write_generated_docs(repo_root)
        write_json(
            repo_root / f"docs-viewer/published/docs/studio/by-id/{UNLISTED_DOC_ID}.json",
            {"doc_id": UNLISTED_DOC_ID},
        )
        try:
            generated_reads.read_generated_doc_payload(repo_root, "studio", UNLISTED_DOC_ID)
        except FileNotFoundError as exc:
            assert "not found" in str(exc)
        else:
            raise AssertionError("Expected generated payload missing from index tree to be rejected")


def test_generated_doc_payload_rejects_unexpected_content_url() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        write_generated_docs(repo_root)
        write_json(
            repo_root / "docs-viewer/published/docs/studio/index-tree.json",
            {
                "schema": "docs_index_tree_v1",
                "docs": [
                    {
                        "doc_id": CHILD_DOC_ID,
                        "content_url": f"/assets/data/docs/scopes/library/by-id/{CHILD_DOC_ID}.json",
                    }
                ]
            },
        )
        try:
            generated_reads.read_generated_doc_payload(repo_root, "studio", CHILD_DOC_ID)
        except RuntimeError as exc:
            assert "unexpected payload path" in str(exc)
        else:
            raise AssertionError("Expected mismatched generated payload path to be rejected")


def test_generated_doc_payload_allows_external_content_url_with_expected_path() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        write_generated_docs(repo_root)
        write_json(
            repo_root / "docs-viewer/published/docs/studio/index-tree.json",
            {
                "schema": "docs_index_tree_v1",
                "docs": [
                    {
                        "doc_id": CHILD_DOC_ID,
                        "content_url": f"https://example.com/docs-viewer/published/docs/studio/by-id/{CHILD_DOC_ID}.json",
                    }
                ]
            },
        )
        payload = generated_reads.read_generated_doc_payload(repo_root, "studio", CHILD_DOC_ID)

    assert payload["doc_id"] == CHILD_DOC_ID


def test_generated_references_reads_scope_index_and_target() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        write_generated_docs(repo_root)

        index_payload = generated_reads.read_generated_references_index(repo_root, "studio")
        target_payload = generated_reads.read_generated_reference_target(repo_root, "studio", "work", "00638")

    assert index_payload["targets"][0]["target_id"] == "00638"
    assert target_payload["target_kind"] == "work"


def test_generated_tree_and_recent_reads_scope_payloads() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        write_generated_docs(repo_root)

        index_tree = generated_reads.read_generated_docs_index_tree(repo_root, "studio")
        recent = generated_reads.read_generated_recent(repo_root, "studio")

    assert index_tree["schema"] == "docs_index_tree_v1"
    assert index_tree["docs"][0]["doc_id"] == NON_VIEWABLE_DOC_ID
    assert recent["schema"] == "docs_recent_v1"
    assert recent["basis"] == "edited"
    assert recent["docs"][0]["doc_id"] == CHILD_DOC_ID


def test_public_generated_doc_payload_uses_tree_without_flat_index() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        write_public_generated_docs(repo_root)
        payload = generated_reads.read_generated_doc_payload(repo_root, "library", LIBRARY_DOC_ID)
        child_payload = generated_reads.read_generated_doc_payload(repo_root, "library", LIBRARY_CHILD_DOC_ID)

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
                    "docs-viewer/published/docs/custom/research",
                    "docs-viewer/published/search/custom/research/index.json",
                )
            ],
        )
        docs = [
            {
                "doc_id": RESEARCH_DOC_ID,
                "content_url": f"/docs-viewer/published/docs/custom/research/by-id/{RESEARCH_DOC_ID}.json",
                "children": [
                    {
                        "doc_id": FINDING_DOC_ID,
                        "content_url": f"/docs-viewer/published/docs/custom/research/by-id/{FINDING_DOC_ID}.json",
                    }
                ],
            }
        ]
        write_json(repo_root / "docs-viewer/published/docs/custom/research/index-tree.json", {"schema": "docs_index_tree_v1", "docs": docs})
        write_json(repo_root / f"docs-viewer/published/docs/custom/research/by-id/{RESEARCH_DOC_ID}.json", {"doc_id": RESEARCH_DOC_ID})
        write_json(repo_root / f"docs-viewer/published/docs/custom/research/by-id/{FINDING_DOC_ID}.json", {"doc_id": FINDING_DOC_ID})

        assert (
            generated_reads.generated_docs_index_tree_path(repo_root, "research")
            == repo_root / "docs-viewer/published/docs/custom/research/index-tree.json"
        )
        payload = generated_reads.read_generated_doc_payload(repo_root, "research", FINDING_DOC_ID)

    assert payload["doc_id"] == FINDING_DOC_ID


def test_generated_search_path_uses_scope_config_search_output() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        write_scope_config(
            repo_root,
            [
                scope_config(
                    "research",
                    "docs-viewer/published/docs/custom/research",
                    "docs-viewer/published/search/custom/research/index.json",
                )
            ],
        )
        write_json(
            repo_root / "docs-viewer/published/search/custom/research/index.json",
            {"entries": [{"doc_id": RESEARCH_DOC_ID}]},
        )

        assert (
            generated_reads.generated_search_index_path(repo_root, "research")
            == repo_root / "docs-viewer/published/search/custom/research/index.json"
        )
        payload = generated_reads.read_generated_search_index(repo_root, "research")

    assert payload["entries"][0]["doc_id"] == RESEARCH_DOC_ID


def test_generated_reads_support_external_local_scope_payloads() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        projects_root = (repo_root.parent / f"{repo_root.name}-external").resolve()
        external_root = projects_root / "docs-viewer"
        external_root.mkdir(parents=True)
        old_projects_base = os.environ.get("DOTLINEFORM_PROJECTS_BASE_DIR")
        os.environ["DOTLINEFORM_PROJECTS_BASE_DIR"] = projects_root.as_posix()
        write_scope_config(repo_root, [external_scope_config("private", external_root)])
        docs_root = external_root / "published/docs/private"
        write_json(
            docs_root / "index-tree.json",
            {
                "schema": "docs_index_tree_v1",
                "docs": [
                    {
                        "doc_id": PRIVATE_DOC_ID,
                        "content_url": f"/docs/doc?scope=private&doc_id={PRIVATE_DOC_ID}",
                    }
                ],
            },
        )
        write_json(docs_root / f"by-id/{PRIVATE_DOC_ID}.json", {"doc_id": PRIVATE_DOC_ID})
        write_json(external_root / "published/search/private/index.json", {"entries": [{"id": PRIVATE_DOC_ID}]})

        try:
            payload = generated_reads.read_generated_doc_payload(repo_root, "private", PRIVATE_DOC_ID)
            search = generated_reads.read_generated_search_index(repo_root, "private")
        finally:
            if old_projects_base is None:
                os.environ.pop("DOTLINEFORM_PROJECTS_BASE_DIR", None)
            else:
                os.environ["DOTLINEFORM_PROJECTS_BASE_DIR"] = old_projects_base

    assert payload == {"doc_id": PRIVATE_DOC_ID}
    assert search["entries"] == [{"id": PRIVATE_DOC_ID}]


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
    test_generated_tree_and_recent_reads_scope_payloads()
    test_public_generated_doc_payload_uses_tree_without_flat_index()
    test_generated_reference_target_rejects_unsafe_path_parts()
    test_generated_doc_paths_use_scope_config_output()
    test_generated_search_path_uses_scope_config_search_output()
    test_generated_reads_support_external_local_scope_payloads()
    test_read_generated_json_reports_invalid_json()
    print("Docs generated-read tests OK")


if __name__ == "__main__":
    main()
