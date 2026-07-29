#!/usr/bin/env python3
"""Focused checks for public Docs Viewer document-location projection."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from typing import Any

from repo_factory import (
    docs_scope_record,
    docs_sub_scope_record,
    write_docs_scope_config,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
BUILD_DIR = REPO_ROOT / "docs-viewer" / "build"
SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
for path in (BUILD_DIR, SERVICES_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import build_document_locations  # noqa: E402
import docs_document_location_projection as projection  # noqa: E402
from docs_scope_config import load_docs_scope_configs  # noqa: E402


ROOT_ID = "d-20260426-164043-e14f49"
REPORT_ONE_ID = "d-20260624-213316-478639"
REPORT_TWO_ID = "d-20260729-111111-abcdef"
TAG_ONE_ID = "d-20260727-225608-63967a"
TAG_TWO_ID = "d-20260727-225608-b235c6"
NOTE_ID = "d-20260729-121212-fedcba"


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def analysis_scope() -> dict[str, object]:
    return docs_scope_record(
        "analysis",
        scope_type="public",
        viewer_base_url="/analysis/",
        include_scope_param=False,
        default_doc_id=ROOT_ID,
        sub_scopes=[
            docs_sub_scope_record(
                "analysis",
                "tags",
                title="Tags",
                public_title="Concepts",
                scope_type="public",
            ),
            docs_sub_scope_record(
                "analysis",
                "notes",
                title="Notes",
                scope_type="public",
            ),
        ],
    )


def search_entry(doc_id: str, title: str) -> dict[str, str]:
    return {
        "id": doc_id,
        "kind": "doc",
        "title": title,
        "href": f"/analysis/?doc={doc_id}",
    }


def test_projection_emits_only_actual_public_report_placements() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        write_docs_scope_config(root, [analysis_scope()])
        config = load_docs_scope_configs(root, scope_ids=["analysis"])["analysis"]

        payload = projection.build_document_location_payload(
            config,
            search_payload={
                "header": {"scope": "analysis"},
                "entries": [
                    search_entry(ROOT_ID, "Analysis"),
                    search_entry(REPORT_ONE_ID, "All Tags"),
                    search_entry(REPORT_TWO_ID, "Made-up Tags"),
                ],
            },
            parent_documents={
                ROOT_ID: {"title": "Analysis"},
                REPORT_ONE_ID: {
                    "viewer_report": "docs_subscope",
                    "viewer_report_access": "public",
                    "viewer_report_subscope": "tags",
                },
                REPORT_TWO_ID: {
                    "viewer_report": "docs_subscope",
                    "viewer_report_access": "public",
                    "viewer_report_subscope": "tags",
                },
            },
            sub_scope_manifests={
                "tags": {
                    "docs": [
                        {"doc_id": TAG_ONE_ID, "title": "bird-nerve"},
                        {"doc_id": TAG_TWO_ID, "title": "bird-nerve"},
                    ]
                },
                "notes": {
                    "docs": [{"doc_id": NOTE_ID, "title": "Private working note"}]
                },
            },
        )

    assert payload["schema_version"] == "docs_document_locations_v1"
    assert payload["scope_id"] == "analysis"
    records = payload["records"]
    assert len(records) == 7
    assert records[0] == {
        "url": f"/analysis/?doc={ROOT_ID}",
        "scope_id": "analysis",
        "document_title": "Analysis",
        "report_title": "",
    }
    placements = [record for record in records if "&subdoc=" in record["url"]]
    assert [record["report_title"] for record in placements] == [
        "All Tags",
        "All Tags",
        "Made-up Tags",
        "Made-up Tags",
    ]
    assert [record["document_title"] for record in placements] == [
        "bird-nerve",
        "bird-nerve",
        "bird-nerve",
        "bird-nerve",
    ]
    assert placements[-1]["url"] == (
        f"/analysis/?doc={REPORT_TWO_ID}&subdoc={TAG_TWO_ID}"
    )
    assert all(NOTE_ID not in record["url"] for record in records)


def test_projection_rejects_noncanonical_search_location() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        write_docs_scope_config(root, [analysis_scope()])
        config = load_docs_scope_configs(root, scope_ids=["analysis"])["analysis"]

        try:
            projection.build_document_location_payload(
                config,
                search_payload={
                    "header": {"scope": "analysis"},
                    "entries": [
                        {
                            **search_entry(ROOT_ID, "Analysis"),
                            "href": f"https://example.test/analysis/?doc={ROOT_ID}",
                        }
                    ],
                },
                parent_documents={ROOT_ID: {"title": "Analysis"}},
                sub_scope_manifests={},
            )
        except ValueError as exc:
            assert "configured canonical viewer route" in str(exc)
        else:
            raise AssertionError("projection should reject external search URLs")


def test_public_projection_loader_does_not_read_source_or_manage_manifest() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        write_docs_scope_config(root, [analysis_scope()])
        write_json(
            root / "site/assets/data/search/analysis/index.json",
            {
                "header": {"scope": "analysis"},
                "entries": [
                    search_entry(ROOT_ID, "Analysis"),
                    search_entry(REPORT_ONE_ID, "Concepts"),
                ],
            },
        )
        write_json(
            root / f"site/assets/data/docs/scopes/analysis/by-id/{ROOT_ID}.json",
            {"title": "Analysis"},
        )
        write_json(
            root
            / f"site/assets/data/docs/scopes/analysis/by-id/{REPORT_ONE_ID}.json",
            {
                "viewer_report": "docs_subscope",
                "viewer_report_access": "public",
                "viewer_report_subscope": "tags",
            },
        )
        write_json(
            root / "site/assets/data/docs/scopes/analysis/tags/manifest.json",
            {"docs": [{"doc_id": TAG_ONE_ID, "title": "Published tag"}]},
        )
        write_json(
            root / "site/assets/data/docs/scopes/analysis/tags/manage-manifest.json",
            {
                "docs": [
                    {"doc_id": TAG_ONE_ID, "title": "Published tag"},
                    {"doc_id": TAG_TWO_ID, "title": "Manage-only tag"},
                ]
            },
        )
        source_path = (
            root
            / f"docs-viewer/scopes/analysis/source/sub-scopes/tags/documents/{TAG_TWO_ID}.md"
        )
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_text(
            f"---\ndoc_id: {TAG_TWO_ID}\ntitle: Source-only tag\n---\n",
            encoding="utf-8",
        )
        config = load_docs_scope_configs(root, scope_ids=["analysis"])["analysis"]

        payload = projection.load_public_document_location_payload(root, config)

    assert [record["document_title"] for record in payload["records"]] == [
        "Analysis",
        "Concepts",
        "Published tag",
    ]


def test_builder_writes_analysis_and_library_indexes_from_public_data() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        root = Path(temp_path)
        library_id = "d-20260330-172255-8399b7"
        write_docs_scope_config(
            root,
            [
                analysis_scope(),
                docs_scope_record(
                    "library",
                    scope_type="public",
                    viewer_base_url="/library/",
                    include_scope_param=False,
                    default_doc_id=library_id,
                ),
            ],
        )
        write_json(
            root / "site/assets/data/search/analysis/index.json",
            {
                "header": {"scope": "analysis"},
                "entries": [search_entry(ROOT_ID, "Analysis")],
            },
        )
        write_json(
            root / f"site/assets/data/docs/scopes/analysis/by-id/{ROOT_ID}.json",
            {"title": "Analysis"},
        )
        write_json(
            root / "site/assets/data/docs/scopes/analysis/tags/manifest.json",
            {"docs": []},
        )
        write_json(
            root / "site/assets/data/docs/scopes/analysis/notes/manifest.json",
            {"docs": []},
        )
        write_json(
            root / "site/assets/data/search/library/index.json",
            {
                "header": {"scope": "library"},
                "entries": [
                    {
                        "id": library_id,
                        "kind": "doc",
                        "title": "Library",
                        "href": f"/library/?doc={library_id}",
                    }
                ],
            },
        )
        write_json(
            root / f"site/assets/data/docs/scopes/library/by-id/{library_id}.json",
            {"title": "Library"},
        )
        stdout = StringIO()
        previous_cwd = Path.cwd()
        try:
            os.chdir(root)
            with redirect_stdout(stdout):
                exit_code = build_document_locations.main(["--write"])
        finally:
            os.chdir(previous_cwd)

        analysis_payload = json.loads(
            (
                root
                / "site/assets/data/search/analysis/document-locations.json"
            ).read_text(encoding="utf-8")
        )
        library_payload = json.loads(
            (
                root
                / "site/assets/data/search/library/document-locations.json"
            ).read_text(encoding="utf-8")
        )

    assert exit_code == 0
    assert len(analysis_payload["records"]) == 1
    assert len(library_payload["records"]) == 1
    assert "scope=analysis: wrote" in stdout.getvalue()
    assert "scope=library: wrote" in stdout.getvalue()


def test_builder_requires_supported_explicit_scopes() -> None:
    try:
        build_document_locations.selected_scope_ids(["studio"])
    except ValueError as exc:
        assert "unsupported document-location scope: studio" in str(exc)
    else:
        raise AssertionError("builder should reject unsupported scopes")
