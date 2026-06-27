#!/usr/bin/env python3
"""Contract checks for Docs Viewer returned-package import parsing."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_IMPORT_PATH = REPO_ROOT / "docs-viewer" / "services" / "docs_import.py"
DOCS_SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
if str(DOCS_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(DOCS_SERVICES_DIR))


def load_docs_import_module():
    spec = importlib.util.spec_from_file_location("docs_import", DOCS_IMPORT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load docs_import.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


docs_import = load_docs_import_module()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_repo() -> tempfile.TemporaryDirectory:
    temp_dir = tempfile.TemporaryDirectory()
    root = Path(temp_dir.name)
    write_text(root / "site-tools/config/site-tools.json", '{"schema_version":"site_tools_config_v1"}\n')
    write_text(
        root / "docs-viewer/config/scopes/docs_scopes.json",
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
            }
        )
        + "\n",
    )
    write_source_doc(root, "library", "Library")
    write_source_doc(root, "alpha", "Alpha", parent_id="library")
    return temp_dir


def write_source_doc(root: Path, doc_id: str, title: str, *, parent_id: str = "") -> None:
    lines = [
        "---",
        f"doc_id: {doc_id}",
        f"title: {title}",
        "added_date: 2026-05-03",
        "last_updated: 2026-05-03",
    ]
    if parent_id:
        lines.append(f"parent_id: {parent_id}")
    lines.extend(["---", "", f"# {title}", "", "Body text."])
    write_text(root / f"docs-viewer/source/library/{doc_id}.md", "\n".join(lines))


def write_staged(root: Path, filename: str, payload: object | str) -> None:
    path = root / "var/analytics/data-sharing/library/import-staging" / filename
    if isinstance(payload, str):
        write_text(path, payload)
    elif filename.endswith(".jsonl"):
        rows = payload if isinstance(payload, list) else [payload]
        write_text(path, "".join(json.dumps(row) + "\n" for row in rows))
    else:
        write_text(path, json.dumps(payload) + "\n")


def write_sidecar_meta(root: Path, filename: str, profile_id: str, *, export_id: str = "ds_20260627T120000Z") -> None:
    stem = Path(filename).with_suffix("").name
    write_staged(
        root,
        f"{stem}.meta.json",
        {
            "export_id": export_id,
            "config_id": profile_id,
            "profile_id": profile_id,
            "scope": "library",
        },
    )


def write_internal_meta(root: Path, export_id: str, profile_id: str) -> None:
    write_text(
        root / f"var/analytics/data-sharing/meta/{export_id}.meta.json",
        json.dumps(
            {
                "schema_version": "data_sharing_export_meta_v1",
                "export_id": export_id,
                "app": "docs-viewer",
                "adapter_id": "documents",
                "data_domain": "documents",
                "config_id": profile_id,
                "profile_id": profile_id,
                "scope": "library",
                "target_format": "jsonl",
                "record_shape": "document_rows",
            }
        )
        + "\n",
    )


def parse(root: Path, filename: str) -> dict:
    return docs_import.parse_staged_import(repo_root=root, scope="library", staged_file=filename)


def render(root: Path, report: dict) -> dict:
    return docs_import.render_markdown_previews(
        repo_root=root,
        scope="library",
        report=report,
        write=True,
        generated_at="2026-05-03T20:40:00Z",
    )


def test_missing_export_id_fails_closed() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged(root, "returned.json", [{"doc_id": "alpha", "title": "Alpha", "summary": "New summary."}])
        report = parse(root, "returned.json")

    assert report["ok"] is False
    assert report["detected_import_type"] == "unknown"
    assert report["counts"]["errors"] == 1
    assert [item["code"] for item in report["issues"]] == ["missing_export_id"]


def test_sidecar_metadata_is_not_a_fallback() -> None:
    with make_repo() as temp:
        root = Path(temp)
        export_id = "ds_20260627T120000Z"
        write_staged(
            root,
            "content.jsonl",
            [
                {
                    "record_type": "data_sharing_header",
                    "schema_version": "data_sharing_returned_package_v1",
                    "export_id": export_id,
                },
                {"doc_id": "alpha", "title": "Alpha", "summary": "New summary."},
            ],
        )
        write_sidecar_meta(root, "content.jsonl", "document-content", export_id=export_id)
        report = parse(root, "content.jsonl")

    assert report["ok"] is False
    assert report["detected_import_type"] == "unknown"
    assert report["counts"]["errors"] == 1
    assert [item["code"] for item in report["issues"]] == ["missing_export_metadata"]


def test_config_id_is_not_a_profile_id_fallback() -> None:
    with make_repo() as temp:
        root = Path(temp)
        export_id = "ds_20260627T120005Z"
        write_text(
            root / f"var/analytics/data-sharing/meta/{export_id}.meta.json",
            json.dumps(
                {
                    "schema_version": "data_sharing_export_meta_v1",
                    "export_id": export_id,
                    "app": "docs-viewer",
                    "adapter_id": "documents",
                    "data_domain": "documents",
                    "config_id": "document-content",
                    "scope": "library",
                    "target_format": "jsonl",
                    "record_shape": "document_rows",
                }
            )
            + "\n",
        )
        write_staged(
            root,
            "content.jsonl",
            [
                {
                    "record_type": "data_sharing_header",
                    "schema_version": "data_sharing_returned_package_v1",
                    "export_id": export_id,
                },
                {"doc_id": "alpha", "title": "Alpha", "summary": "New summary."},
            ],
        )
        report = parse(root, "content.jsonl")

    assert report["ok"] is False
    assert report["detected_import_type"] == "unknown"
    assert report["counts"]["errors"] == 1
    assert [item["code"] for item in report["issues"]] == ["missing_import_metadata"]


def test_document_content_profile_is_sparse_document_changes() -> None:
    with make_repo() as temp:
        root = Path(temp)
        export_id = "ds_20260627T120001Z"
        write_internal_meta(root, export_id, "document-content")
        write_staged(
            root,
            "content.jsonl",
            [
                {
                    "record_type": "data_sharing_header",
                    "schema_version": "data_sharing_returned_package_v1",
                    "export_id": export_id,
                },
                {
                    "doc_id": "alpha",
                    "title": "Alpha",
                    "summary": "New summary.",
                    "ancestors": [{"id": "library", "title": "Library"}],
                    "children": [{"id": "alpha-child", "title": "Alpha Child"}],
                    "source_text": "Export context that should not determine import type.",
                }
            ],
        )
        report = render(root, parse(root, "content.jsonl"))
        preview = (
            root / "var/analytics/data-sharing/library/import-preview/20260503-204000-alpha.md"
        ).read_text(encoding="utf-8")

    assert report["ok"] is True
    assert report["detected_import_type"] == "document_changes"
    assert report["source_export_id"] == export_id
    assert report["source_profile_id"] == "document-content"
    assert report["records"][0]["metadata"]["summary"] == "New summary."
    assert report["records"][0]["relationships"]["children"] == [{"id": "alpha-child", "title": "Alpha Child"}]
    assert 'import_type: "document_changes"' in preview
    assert "## Proposed Summary\n\nNew summary." in preview
    assert "## Imported Source Text" not in preview


def test_jsonl_header_export_id_loads_internal_profile_metadata() -> None:
    with make_repo() as temp:
        root = Path(temp)
        export_id = "ds_20260627T120000Z"
        write_internal_meta(root, export_id, "document-content")
        write_staged(
            root,
            "content-with-header.jsonl",
            "\n".join(
                [
                    json.dumps(
                        {
                            "record_type": "data_sharing_header",
                            "schema_version": "data_sharing_returned_package_v1",
                            "export_id": export_id,
                        }
                    ),
                    json.dumps(
                        {
                            "doc_id": "alpha",
                            "title": "Alpha",
                            "summary": "New summary.",
                            "children": [{"id": "alpha-child", "title": "Alpha Child"}],
                        }
                    ),
                ]
            )
            + "\n",
        )
        report = parse(root, "content-with-header.jsonl")

    assert report["ok"] is True
    assert report["detected_import_type"] == "document_changes"
    assert report["source_export_id"] == export_id
    assert report["source_profile_id"] == "document-content"
    assert report["source_metadata_file"] == f"var/analytics/data-sharing/meta/{export_id}.meta.json"


def test_relationship_profile_is_selected_only_by_metadata() -> None:
    with make_repo() as temp:
        root = Path(temp)
        export_id = "ds_20260627T120002Z"
        write_internal_meta(root, export_id, "parent-child-relationships")
        write_staged(
            root,
            "relationships.json",
            {
                "export_id": export_id,
                "records": [
                    {
                        "doc_id": "library",
                        "title": "Library",
                        "children": [{"id": "alpha", "title": "Alpha"}],
                    }
                ]
            },
        )
        report = parse(root, "relationships.json")

    assert report["ok"] is True
    assert report["detected_import_type"] == "parent_child_relationships"
    assert report["source_export_id"] == export_id
    assert report["source_profile_id"] == "parent-child-relationships"
    assert report["records"][0]["relationships"]["children"] == [{"id": "alpha", "title": "Alpha"}]


def test_unsupported_profile_metadata_fails_closed() -> None:
    with make_repo() as temp:
        root = Path(temp)
        export_id = "ds_20260627T120003Z"
        write_internal_meta(root, export_id, "future-profile")
        write_staged(root, "returned.json", {"export_id": export_id, "records": [{"doc_id": "alpha", "title": "Alpha"}]})
        report = parse(root, "returned.json")

    assert report["ok"] is False
    assert report["detected_import_type"] == "unknown"
    assert report["counts"]["errors"] == 1
    assert [item["code"] for item in report["issues"]] == ["unsupported_import_profile"]


def test_invalid_jsonl_is_a_file_level_blocker() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_staged(
            root,
            "broken.jsonl",
            json.dumps(
                {
                    "record_type": "data_sharing_header",
                    "schema_version": "data_sharing_returned_package_v1",
                    "export_id": "ds_20260627T120004Z",
                }
            )
            + "\n{bad json}\n",
        )
        report = parse(root, "broken.jsonl")

    assert report["ok"] is False
    assert report["counts"]["errors"] == 1
    assert report["counts"]["records"] == 0
    assert report["records"] == []
    assert report["issues"][0]["code"] == "invalid_jsonl"


def test_parser_rejects_paths_outside_staging_root() -> None:
    with make_repo() as temp:
        root = Path(temp)
        outside = root / "outside.json"
        outside.write_text("[]\n", encoding="utf-8")
        report = docs_import.parse_staged_import(repo_root=root, scope="library", staged_file=str(outside))

    assert report["ok"] is False
    assert report["counts"]["errors"] == 1
    assert report["issues"][0]["code"] == "unsafe_staged_path"


def main() -> None:
    tests = [
        test_missing_export_id_fails_closed,
        test_sidecar_metadata_is_not_a_fallback,
        test_config_id_is_not_a_profile_id_fallback,
        test_document_content_profile_is_sparse_document_changes,
        test_jsonl_header_export_id_loads_internal_profile_metadata,
        test_relationship_profile_is_selected_only_by_metadata,
        test_unsupported_profile_metadata_fails_closed,
        test_invalid_jsonl_is_a_file_level_blocker,
        test_parser_rejects_paths_outside_staging_root,
    ]
    for test in tests:
        test()


if __name__ == "__main__":
    main()
