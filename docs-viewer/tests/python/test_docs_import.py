#!/usr/bin/env python3
"""Contract checks for Docs Viewer returned-package import parsing."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
if str(DOCS_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(DOCS_SERVICES_DIR))


import docs_returned_import_parser  # noqa: E402
from services.paths import workspace_paths  # noqa: E402


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
    del root
    path = workspace_paths().import_staging / filename
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


def write_internal_meta(
    root: Path,
    export_id: str,
    profile_id: str,
    *,
    supports_return_import: bool | None = None,
) -> None:
    payload = {
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
    if supports_return_import is not None:
        payload["supports_return_import"] = supports_return_import
    write_text(
        workspace_paths().meta / f"{export_id}.meta.json",
        json.dumps(payload) + "\n",
    )


def parse(root: Path, filename: str) -> dict:
    paths = workspace_paths()
    return docs_returned_import_parser.parse_staged_import(
        repo_root=root,
        scope="library",
        staged_file=filename,
        staging_root=paths.import_staging,
        metadata_root=paths.meta,
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
            workspace_paths().meta / f"{export_id}.meta.json",
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
                    "content": "Export context that should not determine import type.",
                }
            ],
        )
        report = parse(root, "content.jsonl")

    assert report["ok"] is True
    assert report["detected_import_type"] == "document_changes"
    assert report["source_export_id"] == export_id
    assert report["source_profile_id"] == "document-content"
    assert report["records"][0]["metadata"]["summary"] == "New summary."
    assert report["records"][0]["relationships"]["children"] == [{"id": "alpha-child", "title": "Alpha Child"}]


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
    assert report["source_metadata_file"] == f"$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/meta/{export_id}.meta.json"


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


def test_export_only_profile_metadata_fails_before_import_action_matching() -> None:
    with make_repo() as temp:
        root = Path(temp)
        export_id = "ds_20260627T120006Z"
        write_internal_meta(root, export_id, "document-content", supports_return_import=False)
        write_staged(root, "returned.json", {"export_id": export_id, "records": [{"doc_id": "alpha", "title": "Alpha"}]})
        report = parse(root, "returned.json")

    assert report["ok"] is False
    assert report["detected_import_type"] == "export_only"
    assert report["counts"]["errors"] == 1
    assert [item["code"] for item in report["issues"]] == ["export_only_profile"]


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
        paths = workspace_paths()
        report = docs_returned_import_parser.parse_staged_import(
            repo_root=root,
            scope="library",
            staged_file=str(outside),
            staging_root=paths.import_staging,
            metadata_root=paths.meta,
        )

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
        test_unsupported_profile_metadata_fails_closed,
        test_export_only_profile_metadata_fails_before_import_action_matching,
        test_invalid_jsonl_is_a_file_level_blocker,
        test_parser_rejects_paths_outside_staging_root,
    ]
    for test in tests:
        test()


if __name__ == "__main__":
    main()
