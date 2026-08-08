#!/usr/bin/env python3
"""Focused checks for Docs Viewer public publish gate."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pytest

from repo_factory import docs_scope_record, docs_sub_scope_record


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
if str(DOCS_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(DOCS_SERVICES_DIR))

import docs_publish_gate  # noqa: E402
from catalogue import catalogue_document_url_refresh  # noqa: E402


LIBRARY_DOC_ID = "d-20260330-172255-8399b7"
LINEAGE_SOURCE_ID = "d-20260801-100000-aaaaaa"
LINEAGE_EDITORIAL_ID = "d-20260802-110000-bbbbbb"
LINEAGE_REPORT_HOST_ID = "d-20260807-082735-54d9d5"


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_scope_config(root: Path) -> None:
    library = docs_scope_record(
        "library",
        scope_type="public",
        viewer_base_url="/library/",
        include_scope_param=False,
        default_doc_id=LIBRARY_DOC_ID,
    )
    library["published"]["media"]["img"] = {  # type: ignore[index]
        "reference_prefix": "docs/library/img",
        "location": {
            "provider": "repository",
            "path": "site/assets/data/docs/scopes/library/media/img",
        },
        "served_path_prefix": "/assets/data/docs/scopes/library/media/img",
        "build_inputs": [],
    }
    library["published"]["media"]["html"] = {  # type: ignore[index]
        "reference_prefix": "docs/library/html",
        "location": {
            "provider": "repository",
            "path": "site/assets/data/docs/scopes/library/media/html",
        },
        "served_path_prefix": "/assets/data/docs/scopes/library/media/html",
        "build_inputs": [],
    }
    write_json(
        root / "docs-viewer/config/scopes/docs_scopes.json",
        {
            "schema_version": "docs_scopes_v3",
            "scopes": [
                docs_scope_record("studio", default_doc_id="studio"),
                library,
            ],
        },
    )


def prepare_publish_repo(root: Path) -> None:
    write_scope_config(root)
    write_json(
        root / "docs-viewer/scopes/library/published/documents/index-tree.json",
        {
            "schema": "docs_index_tree_v1",
            "viewer_options": {"manage_only_tree_root_ids": ["manage-root"]},
            "docs": [
                {
                    "doc_id": LIBRARY_DOC_ID,
                    "title": "Library",
                    "content_url": f"/assets/data/docs/scopes/library/by-id/{LIBRARY_DOC_ID}.json",
                    "children": [
                        {
                            "doc_id": "hidden",
                            "title": "Hidden",
                            "content_url": "/assets/data/docs/scopes/library/by-id/hidden.json",
                            "publishable": False,
                            "children": [
                                {
                                    "doc_id": "hidden-child",
                                    "title": "Hidden Child",
                                    "content_url": "/assets/data/docs/scopes/library/by-id/hidden-child.json",
                                }
                            ],
                        }
                    ],
                },
                {
                    "doc_id": "manage-root",
                    "title": "Manage Root",
                    "content_url": "/assets/data/docs/scopes/library/by-id/manage-root.json",
                },
            ],
        },
    )
    write_json(
        root / "docs-viewer/scopes/library/published/documents/recent.json",
        {
            "schema": "docs_recent_v1",
            "basis": "edited",
            "docs": [
                {"doc_id": "hidden", "title": "Hidden", "content_url": "/assets/data/docs/scopes/library/by-id/hidden.json", "timestamp": "2026-06-02 10:00:00"},
                {"doc_id": LIBRARY_DOC_ID, "title": "Library", "content_url": f"/assets/data/docs/scopes/library/by-id/{LIBRARY_DOC_ID}.json", "timestamp": "2026-06-01 10:00:00"},
            ],
        },
    )
    write_json(
        root / "docs-viewer/scopes/library/published/documents/.publish/recent.json",
        {
            "schema": "docs_recent_v1",
            "basis": "edited",
            "docs": [
                {"doc_id": LIBRARY_DOC_ID, "title": "Library", "content_url": f"/assets/data/docs/scopes/library/by-id/{LIBRARY_DOC_ID}.json", "timestamp": "2026-06-01 10:00:00"},
            ],
        },
    )
    write_json(
        root / f"docs-viewer/scopes/library/published/documents/by-id/{LIBRARY_DOC_ID}.json",
        {
            "title": "Library",
            "content_html": (
                '<p><a href="#" title=">" DATA-DOCS-VIEWER-LOCAL-TARGET="projects/3%20symbols">3 <em>symbols</em></a> '
                '<a href=dlf-local:bad%ZZ>/Users/private</a> '
                '<a href="#" data-docs-viewer-local-target=""></a> '
                '<a href="https://example.com">ordinary</a></p>'
            ),
        },
    )
    write_json(root / "docs-viewer/scopes/library/published/documents/by-id/hidden.json", {"title": "Hidden"})
    write_json(root / "docs-viewer/scopes/library/published/documents/by-id/hidden-child.json", {"title": "Hidden Child"})
    write_json(root / "docs-viewer/scopes/library/published/documents/by-id/manage-root.json", {"title": "Manage Root"})
    write_json(
        root / "docs-viewer/scopes/library/published/documents/semantic-tokens/index.json",
        {
            "schema_version": "docs_semantic_token_usage_index_v1",
            "scope": "library",
            "occurrences": [],
        },
    )
    write_json(
        root / "docs-viewer/scopes/library/published/search/index.json",
        {
            "header": {
                "schema": "search_index_library_v1",
                "scope": "library",
                "version": "fixture",
                "count": 1,
            },
            "entries": [
                {
                    "id": LIBRARY_DOC_ID,
                    "kind": "doc",
                    "title": "Library",
                    "href": f"/library/?doc={LIBRARY_DOC_ID}",
                }
            ],
        },
    )
    write_json(root / "site/assets/data/docs/scopes/library/index-tree.json", {"docs": []})
    write_json(root / "site/assets/data/docs/scopes/library/by-id/stale.json", {"title": "Stale"})
    write_json(root / "site/assets/data/docs/scopes/library/by-id/hidden.json", {"title": "Old Hidden"})
    write_json(
        root / "site/assets/data/docs/scopes/library/by-id/hidden-child.json",
        {"title": "Old Hidden Child"},
    )
    write_text(
        root
        / "site/assets/data/docs/scopes/library/projection-assets/mermaid"
        / "hidden--mermaid-0001/dark.svg",
        "<svg>old hidden dark</svg>",
    )
    write_text(
        root
        / "site/assets/data/docs/scopes/library/projection-assets/mermaid"
        / "hidden--mermaid-0001/light.svg",
        "<svg>old hidden light</svg>",
    )
    write_json(
        root / "site/assets/data/docs/scopes/library/semantic-tokens/index.json",
        {"schema_version": "stale"},
    )
    write_json(
        root / "site/assets/data/docs/scopes/library/references/index.json",
        {"schema_version": "stale-pilot"},
    )
    write_text(
        root / "site/assets/data/docs/scopes/library/media/html/widget.html",
        "<!doctype html><title>Widget</title>",
    )
    write_text(root / "site/assets/data/docs/scopes/library/media/img/diagram.png", "image bytes")
    write_json(root / "site/assets/data/search/library/index.json", {"entries": []})


def write_library_subject_source(root: Path, field_name: str, value: str) -> None:
    write_text(
        root / f"docs-viewer/scopes/library/source/documents/{LIBRARY_DOC_ID}.md",
        "\n".join(
            [
                "---",
                f'doc_id: "{LIBRARY_DOC_ID}"',
                'title: "Library"',
                "publishable: true",
                f'{field_name}: "{value}"',
                "---",
                "",
                "# Library",
                "",
            ]
        ),
    )


def catalogue_work_payload(work_id: str, urls: list[str]) -> dict[str, object]:
    return {
        "header": {
            "schema": "work_record_v4",
            "version": "before",
            "generated_at_utc": "2026-08-01T00:00:00Z",
            "work_id": work_id,
            "count": 0,
        },
        "work": {"work_id": work_id, "title": "Work", "doc_url": urls},
        "sections": [],
    }


def catalogue_series_payload(series_id: str, urls: list[str]) -> dict[str, object]:
    return {
        "header": {
            "schema": "series_record_v2",
            "version": "before",
            "generated_at_utc": "2026-08-01T00:00:00Z",
            "series_id": series_id,
            "count": 0,
        },
        "series": {"series_id": series_id, "title": "Series", "doc_url": urls},
    }


def test_publish_confirm_applies_explicit_exclusions_and_retains_unrelated_files() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        prepare_publish_repo(repo_root)

        preview = docs_publish_gate.publish_confirm(repo_root, {"scope": "library"})
        applied = docs_publish_gate.publish_apply(repo_root, {"scope": "library", "confirm": True})

        assert preview["operation"] == "confirm"
        assert preview["schema_version"] == "docs_publish_gate_v2"
        assert preview["changed_count"] >= 3
        assert preview["docs"]["excluded"] == [
            "site/assets/data/docs/scopes/library/by-id/hidden.json",
            "site/assets/data/docs/scopes/library/by-id/hidden-child.json",
            (
                "site/assets/data/docs/scopes/library/projection-assets/mermaid/"
                "hidden--mermaid-0001/dark.svg"
            ),
            (
                "site/assets/data/docs/scopes/library/projection-assets/mermaid/"
                "hidden--mermaid-0001/light.svg"
            ),
        ]
        assert "removed" not in preview["docs"]
        assert "removed_count" not in preview
        assert "site/assets/data/docs/scopes/library/by-id/stale.json" not in preview["docs"]["excluded"]
        assert "site/assets/data/docs/scopes/library/media/html/widget.html" not in preview["docs"]["excluded"]
        assert "site/assets/data/docs/scopes/library/media/img/diagram.png" not in preview["docs"]["excluded"]
        assert preview["document_locations"] == {
            "changed": [
                "site/assets/data/search/library/document-locations.json"
            ],
            "excluded": [],
        }
        assert applied["operation"] == "apply"
        public_tree = json.loads((repo_root / "site/assets/data/docs/scopes/library/index-tree.json").read_text(encoding="utf-8"))
        recent = json.loads((repo_root / "site/assets/data/docs/scopes/library/recent.json").read_text(encoding="utf-8"))
        public_doc = json.loads(
            (repo_root / f"site/assets/data/docs/scopes/library/by-id/{LIBRARY_DOC_ID}.json").read_text(encoding="utf-8")
        )

        assert public_tree["docs"][0]["doc_id"] == LIBRARY_DOC_ID
        assert "children" not in public_tree["docs"][0]
        assert recent["docs"][0]["doc_id"] == LIBRARY_DOC_ID
        assert public_doc["content_html"] == (
            '<p>3 symbols [local file or folder] [local file or folder] '
            '<a href="https://example.com">ordinary</a></p>'
        )
        assert "dlf-local:" not in json.dumps(public_doc)
        assert "data-docs-viewer-local-target" not in json.dumps(public_doc)
        assert (
            repo_root
            / f"site/assets/data/docs/scopes/library/by-id/{LIBRARY_DOC_ID}.json"
        ).exists()
        assert not (repo_root / "site/assets/data/docs/scopes/library/by-id/hidden.json").exists()
        assert not (repo_root / "site/assets/data/docs/scopes/library/by-id/hidden-child.json").exists()
        assert not (
            repo_root
            / "site/assets/data/docs/scopes/library/projection-assets/mermaid/hidden--mermaid-0001"
        ).exists()
        assert (repo_root / "site/assets/data/docs/scopes/library/by-id/manage-root.json").is_file()
        assert (repo_root / "site/assets/data/docs/scopes/library/references").is_dir()
        assert (repo_root / "site/assets/data/docs/scopes/library/semantic-tokens").is_dir()
        assert (repo_root / "site/assets/data/docs/scopes/library/by-id/stale.json").is_file()
        assert (repo_root / "site/assets/data/docs/scopes/library/media/html/widget.html").is_file()
        assert (repo_root / "site/assets/data/docs/scopes/library/media/img/diagram.png").is_file()
        assert json.loads((repo_root / "site/assets/data/search/library/index.json").read_text(encoding="utf-8"))["entries"][0]["id"] == LIBRARY_DOC_ID
        location_payload = json.loads(
            (
                repo_root
                / "site/assets/data/search/library/document-locations.json"
            ).read_text(encoding="utf-8")
        )
        assert location_payload == {
            "schema_version": "docs_document_locations_v1",
            "scope_id": "library",
            "records": [
                {
                    "url": f"/library/?doc={LIBRARY_DOC_ID}",
                    "scope_id": "library",
                    "document_title": "Library",
                    "report_title": "",
                }
            ],
        }


def test_publish_follow_through_adds_reassigns_and_removes_exact_catalogue_urls() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        prepare_publish_repo(repo_root)
        work_path = repo_root / "site/assets/works/index/00042.json"
        series_path = repo_root / "site/assets/series/index/009.json"
        write_json(work_path, catalogue_work_payload("00042", []))
        write_json(series_path, catalogue_series_payload("009", []))
        write_library_subject_source(repo_root, "work_id", "00042")
        public_url = f"/library/?doc={LIBRARY_DOC_ID}"

        first = docs_publish_gate.publish_apply(
            repo_root,
            {"scope": "library", "confirm": True},
        )

        assert first["catalogue_document_urls"] == {
            "status": "updated",
            "stale": False,
            "affected_targets": [{"kind": "work", "key": "00042"}],
            "updated_paths": ["site/assets/works/index/00042.json"],
        }
        assert json.loads(work_path.read_text(encoding="utf-8"))["work"]["doc_url"] == [public_url]

        write_library_subject_source(repo_root, "series_id", "009")
        reassigned = docs_publish_gate.publish_apply(
            repo_root,
            {"scope": "library", "confirm": True},
        )

        assert reassigned["catalogue_document_urls"]["affected_targets"] == [
            {"kind": "series", "key": "009"},
            {"kind": "work", "key": "00042"},
        ]
        assert json.loads(work_path.read_text(encoding="utf-8"))["work"]["doc_url"] == []
        assert json.loads(series_path.read_text(encoding="utf-8"))["series"]["doc_url"] == [public_url]

        working_tree_path = repo_root / "docs-viewer/scopes/library/published/documents/index-tree.json"
        working_tree = json.loads(working_tree_path.read_text(encoding="utf-8"))
        working_tree["docs"] = [
            {
                "doc_id": LIBRARY_DOC_ID,
                "title": "Library",
                "content_url": (
                    f"/assets/data/docs/scopes/library/by-id/{LIBRARY_DOC_ID}.json"
                ),
                "publishable": False,
            }
        ]
        write_json(working_tree_path, working_tree)
        working_search_path = repo_root / "docs-viewer/scopes/library/published/search/index.json"
        working_search = json.loads(working_search_path.read_text(encoding="utf-8"))
        working_search["entries"] = []
        working_search["header"]["count"] = 0
        write_json(working_search_path, working_search)
        unpublished = docs_publish_gate.publish_apply(
            repo_root,
            {"scope": "library", "confirm": True},
        )

        assert unpublished["catalogue_document_urls"]["affected_targets"] == [
            {"kind": "series", "key": "009"}
        ]
        assert json.loads(series_path.read_text(encoding="utf-8"))["series"]["doc_url"] == []


def test_publish_remains_applied_when_catalogue_follow_through_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        prepare_publish_repo(repo_root)
        work_path = repo_root / "site/assets/works/index/00042.json"
        write_json(work_path, catalogue_work_payload("00042", []))
        work_before = work_path.read_bytes()
        write_library_subject_source(repo_root, "work_id", "00042")

        def fail_follow_through(_plan: object) -> object:
            raise OSError("simulated post-publication Catalogue failure")

        monkeypatch.setattr(
            catalogue_document_url_refresh,
            "apply_catalogue_document_url_refresh_plan",
            fail_follow_through,
        )

        applied = docs_publish_gate.publish_apply(
            repo_root,
            {"scope": "library", "confirm": True},
        )

        assert applied["applied"] is True
        assert applied["catalogue_document_urls"] == {
            "status": "stale",
            "stale": True,
            "affected_targets": [{"kind": "work", "key": "00042"}],
            "updated_paths": [],
            "error": "simulated post-publication Catalogue failure",
        }
        assert (
            repo_root
            / f"site/assets/data/docs/scopes/library/by-id/{LIBRARY_DOC_ID}.json"
        ).is_file()
        assert work_path.read_bytes() == work_before


def test_publish_confirm_and_apply_include_configured_sub_scope_payloads() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        prepare_publish_repo(repo_root)
        config_path = repo_root / "docs-viewer/config/scopes/docs_scopes.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["scopes"][1]["sub_scopes"] = [
            docs_sub_scope_record("library", "tags", title="Tags", scope_type="public")
        ]
        write_json(config_path, config)
        write_json(
            repo_root / "docs-viewer/scopes/library/published/documents/sub-scopes/tags/manifest.json",
            {"docs": [{"doc_id": "scale", "title": "Scale"}]},
        )
        write_json(
            repo_root
            / "docs-viewer/scopes/library/published/documents/sub-scopes/tags/manage-manifest.json",
            {
                "docs": [
                    {
                        "doc_id": "scale",
                        "title": "Scale",
                        "ui_status": "draft",
                        "publishable": True,
                    },
                    {
                        "doc_id": "hidden",
                        "title": "Hidden",
                        "publishable": False,
                    },
                ]
            },
        )
        write_json(repo_root / "docs-viewer/scopes/library/published/documents/sub-scopes/tags/by-id/scale.json", {"doc_id": "scale", "title": "Scale"})
        write_json(repo_root / "docs-viewer/scopes/library/published/documents/sub-scopes/tags/by-id/hidden.json", {"doc_id": "hidden", "title": "Hidden"})
        write_json(repo_root / "site/assets/data/docs/scopes/library/tags/manifest.json", {"doc_ids": "old"})
        write_json(
            repo_root / "site/assets/data/docs/scopes/library/tags/manage-manifest.json",
            {"docs": [{"doc_id": "leaked"}]},
        )
        write_json(repo_root / "site/assets/data/docs/scopes/library/tags/by-id/old.json", {"doc_id": "old"})
        write_json(repo_root / "site/assets/data/docs/scopes/library/tags/by-id/hidden.json", {"doc_id": "hidden", "title": "Old Hidden"})
        working_scale_bytes = (
            repo_root
            / "docs-viewer/scopes/library/published/documents/sub-scopes/tags/by-id/scale.json"
        ).read_bytes()

        preview = docs_publish_gate.publish_confirm(repo_root, {"scope": "library"})
        applied = docs_publish_gate.publish_apply(repo_root, {"scope": "library", "confirm": True})

        assert preview["operation"] == "confirm"
        assert preview["sub_scopes"] == [
            {
                "sub_scope": "tags",
                "changed": [
                    "site/assets/data/docs/scopes/library/tags/by-id/scale.json",
                    "site/assets/data/docs/scopes/library/tags/manifest.json",
                ],
                "excluded": [
                    "site/assets/data/docs/scopes/library/tags/by-id/hidden.json",
                ],
                "changed_count": 2,
                "excluded_count": 1,
            }
        ]
        assert "site/assets/data/docs/scopes/library/tags/by-id/old.json" not in preview["docs"]["excluded"]
        assert not any("/sub-scopes/tags/" in path for path in preview["docs"]["changed"])
        assert applied["operation"] == "apply"
        public_manifest = json.loads((repo_root / "site/assets/data/docs/scopes/library/tags/manifest.json").read_text(encoding="utf-8"))
        public_scale = json.loads((repo_root / "site/assets/data/docs/scopes/library/tags/by-id/scale.json").read_text(encoding="utf-8"))

        assert public_manifest == {"docs": [{"doc_id": "scale", "title": "Scale"}]}
        assert public_scale["title"] == "Scale"
        assert (
            repo_root / "site/assets/data/docs/scopes/library/tags/by-id/scale.json"
        ).read_bytes() == working_scale_bytes
        assert not (repo_root / "site/assets/data/docs/scopes/library/tags/by-id/hidden.json").exists()
        assert (repo_root / "site/assets/data/docs/scopes/library/tags/by-id/old.json").is_file()
        assert (
            repo_root
            / "site/assets/data/docs/scopes/library/tags/manage-manifest.json"
        ).is_file()
        assert not (repo_root / "site/assets/data/docs/scopes/library/sub-scopes/tags").exists()


def test_successful_publish_sets_retains_and_clears_lineage_publication(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        rebuilds: list[tuple[str, str]] = []
        monkeypatch.setattr(
            docs_publish_gate,
            "rebuild_sub_scope_outputs",
            lambda _repo_root, scope, sub_scope: rebuilds.append(
                (scope, sub_scope)
            ),
        )
        prepare_publish_repo(repo_root)
        config_path = repo_root / "docs-viewer/config/scopes/docs_scopes.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["scopes"][1]["sub_scopes"] = [
            docs_sub_scope_record(
                "library",
                "works",
                title="Works",
                scope_type="public",
                sub_scope_customisation={"id": "analysis_works", "settings": {}},
                lifecycle={
                    "tool_id": "docs-viewer-scope-lifecycle",
                    "report_host_doc_id": LINEAGE_REPORT_HOST_ID,
                    "report_host_source_revision": "sha256:" + "1" * 64,
                },
            )
        ]
        write_json(config_path, config)
        working_root = (
            repo_root
            / "docs-viewer/scopes/library/published/documents/sub-scopes/works"
        )
        write_json(
            working_root / "manifest.json",
            {
                "docs": [
                    {"doc_id": LINEAGE_EDITORIAL_ID, "title": "Editorial B"}
                ]
            },
        )
        write_json(
            working_root / f"by-id/{LINEAGE_EDITORIAL_ID}.json",
            {"doc_id": LINEAGE_EDITORIAL_ID, "title": "Editorial B"},
        )
        lineage_path = (
            repo_root
            / "docs-viewer/data/canonical/document-publication-lineage.json"
        )
        write_json(
            lineage_path,
            {
                "schema_version": "docs_document_publication_lineage_v2",
                "rows": [
                    {
                        "lineage_id": "sha256:" + "a" * 64,
                        "working": {
                            "scope": "dotlineform",
                            "sub_scope": "projects",
                            "doc_id": LINEAGE_SOURCE_ID,
                        },
                        "editorial": {
                            "scope": "library",
                            "sub_scope": "works",
                            "doc_id": LINEAGE_EDITORIAL_ID,
                        },
                        "created_at": "2026-08-08T10:00:00Z",
                        "last_copied_at": "2026-08-08T10:00:00Z",
                        "published": None,
                    },
                    {
                        "lineage_id": "sha256:" + "b" * 64,
                        "working": {
                            "scope": "dotlineform",
                            "sub_scope": "projects",
                            "doc_id": "d-20260801-110000-bbbbbb",
                        },
                        "editorial": None,
                        "created_at": "2026-08-08T11:00:00Z",
                        "last_copied_at": "2026-08-08T11:00:00Z",
                        "published": None,
                    }
                ],
            },
        )

        docs_publish_gate.publish_apply(
            repo_root,
            {"scope": "library", "confirm": True},
        )

        table = json.loads(lineage_path.read_text(encoding="utf-8"))
        assert table["rows"][0]["published"] == {
            "public_url": (
                f"/library/?doc={LINEAGE_REPORT_HOST_ID}"
                f"&subdoc={LINEAGE_EDITORIAL_ID}"
            )
        }
        assert table["rows"][1]["editorial"] is None
        assert table["rows"][1]["published"] is None
        assert rebuilds == [("dotlineform", "projects")]
        published_bytes = lineage_path.read_bytes()
        write_json(
            working_root / f"by-id/{LINEAGE_EDITORIAL_ID}.json",
            {"doc_id": LINEAGE_EDITORIAL_ID, "title": "Editorial B updated"},
        )
        docs_publish_gate.publish_apply(
            repo_root,
            {"scope": "library", "confirm": True},
        )
        assert lineage_path.read_bytes() == published_bytes
        assert rebuilds == [("dotlineform", "projects")]
        assert json.loads(
            (
                repo_root
                / f"site/assets/data/docs/scopes/library/works/by-id/{LINEAGE_EDITORIAL_ID}.json"
            ).read_text(encoding="utf-8")
        )["title"] == "Editorial B updated"

        write_json(working_root / "manifest.json", {"docs": []})
        write_json(
            working_root / "manage-manifest.json",
            {
                "docs": [
                    {
                        "doc_id": LINEAGE_EDITORIAL_ID,
                        "title": "Editorial B",
                        "publishable": False,
                    }
                ]
            },
        )
        docs_publish_gate.publish_apply(
            repo_root,
            {"scope": "library", "confirm": True},
        )

        table = json.loads(lineage_path.read_text(encoding="utf-8"))
        assert table["rows"][0]["published"] is None
        assert rebuilds == [
            ("dotlineform", "projects"),
            ("dotlineform", "projects"),
        ]
        assert not (
            repo_root
            / f"site/assets/data/docs/scopes/library/works/by-id/{LINEAGE_EDITORIAL_ID}.json"
        ).exists()


def test_publish_rejects_configured_sub_scope_without_manifest() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        prepare_publish_repo(repo_root)
        config_path = repo_root / "docs-viewer/config/scopes/docs_scopes.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["scopes"][1]["sub_scopes"] = [
            docs_sub_scope_record("library", "tags", title="Tags", scope_type="public")
        ]
        write_json(config_path, config)
        (repo_root / "docs-viewer/scopes/library/published/documents/sub-scopes/tags").mkdir(parents=True)

        try:
            docs_publish_gate.publish_confirm(repo_root, {"scope": "library"})
        except FileNotFoundError as exc:
            assert "sub-scope tags manifest not found" in str(exc)
        else:
            raise AssertionError("publish should reject configured sub-scope output without manifest")


def test_publish_apply_requires_confirmation() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        prepare_publish_repo(repo_root)

        try:
            docs_publish_gate.publish_apply(repo_root, {"scope": "library"})
        except ValueError as exc:
            assert "confirm must be true" in str(exc)
        else:
            raise AssertionError("publish apply should require explicit confirmation")


def test_publish_rejects_non_public_scope() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        write_scope_config(repo_root)

        try:
            docs_publish_gate.publish_confirm(repo_root, {"scope": "studio"})
        except ValueError as exc:
            assert "not a public read-only scope" in str(exc)
        else:
            raise AssertionError("publish should reject non-public scopes")
