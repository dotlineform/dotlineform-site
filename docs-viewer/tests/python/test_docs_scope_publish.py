#!/usr/bin/env python3
"""Focused checks for consumer-neutral scope Publish."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from repo_factory import (
    docs_scope_record,
    docs_sub_scope_record,
    write_docs_scope_config,
    write_json,
    write_text,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
SERVICES = REPO_ROOT / "docs-viewer" / "services"
if str(SERVICES) not in sys.path:
    sys.path.insert(0, str(SERVICES))

import docs_published_reads  # noqa: E402
import docs_scope_build_manifest  # noqa: E402
import docs_scope_publish  # noqa: E402
from docs_scope_config import load_docs_scope_configs  # noqa: E402


ROOT_ID = "d-20260830-100000-aaaaaa"
HIDDEN_ID = "d-20260830-100100-bbbbbb"
HIDDEN_CHILD_ID = "d-20260830-100200-cccccc"
REPORT_ID = "d-20260830-100300-dddddd"
SUB_ID = "d-20260830-100400-eeeeee"
HIDDEN_SUB_ID = "d-20260830-100500-ffffff"


def search_payload() -> dict[str, object]:
    docs = [
        {"id": ROOT_ID, "title": "Root", "href": f"/docs/?scope=example&doc={ROOT_ID}"},
        {"id": HIDDEN_ID, "title": "Hidden", "href": f"/docs/?scope=example&doc={HIDDEN_ID}"},
        {"id": HIDDEN_CHILD_ID, "title": "Hidden child", "href": f"/docs/?scope=example&doc={HIDDEN_CHILD_ID}"},
        {"id": REPORT_ID, "title": "Report", "href": f"/docs/?scope=example&doc={REPORT_ID}"},
        {
            "id": SUB_ID,
            "title": "Sub doc",
            "href": f"/docs/?scope=example&doc={REPORT_ID}&subdoc={SUB_ID}",
            "sub_scope": "items",
            "report_doc_id": REPORT_ID,
            "collection_title": "Items",
        },
        {
            "id": HIDDEN_SUB_ID,
            "title": "Hidden sub doc",
            "href": f"/docs/?scope=example&doc={REPORT_ID}&subdoc={HIDDEN_SUB_ID}",
            "sub_scope": "items",
            "report_doc_id": REPORT_ID,
            "collection_title": "Items",
        },
    ]
    return {
        "header": {
            "schema": "docs_viewer_search_index_v2",
            "scope": "example",
            "version": "generated",
            "generated_at_utc": "2026-08-30T10:00:00Z",
            "count": len(docs),
        },
        "fields": ["title"],
        "docs": docs,
        "terms": {
            "root": {"title": [0]},
            "hidden": {"title": [1, 2, 5]},
            "report": {"title": [3]},
            "sub": {"title": [4, 5]},
        },
    }


def prepare_repo(root: Path) -> None:
    scope = docs_scope_record(
        "example",
        default_doc_id=ROOT_ID,
        media_types=("img", "svg", "files", "html"),
    )
    scope["sub_scopes"] = [
        docs_sub_scope_record(
            "example",
            "items",
            title="Items",
            sub_scope_customisation={"id": "analysis_works", "settings": {}},
        )
    ]
    write_docs_scope_config(root, [scope])
    write_text(root / "docs-viewer/config/reports/reports.json", '{"reports": []}\n')
    scope_root = root / "docs-viewer/scopes/example"
    for role in ("source", "generated", "published"):
        for relative in (
            "documents",
            "search",
            "references",
            "reports",
            "media/img",
            "media/svg",
            "media/files",
            "media/html",
        ):
            (scope_root / role / relative).mkdir(parents=True, exist_ok=True)
    write_text(scope_root / "source/documents/root.md", "# Root\n")

    tree = {
        "schema": "docs_index_tree_v1",
        "docs": [
            {
                "doc_id": ROOT_ID,
                "title": "Root",
                "content_url": f"/docs/doc?scope=example&doc_id={ROOT_ID}",
                "children": [
                    {
                        "doc_id": HIDDEN_ID,
                        "title": "Hidden",
                        "publishable": False,
                        "content_url": f"/docs/doc?scope=example&doc_id={HIDDEN_ID}",
                        "children": [
                            {
                                "doc_id": HIDDEN_CHILD_ID,
                                "title": "Hidden child",
                                "content_url": f"/docs/doc?scope=example&doc_id={HIDDEN_CHILD_ID}",
                            }
                        ],
                    }
                ],
            },
            {
                "doc_id": REPORT_ID,
                "title": "Report",
                "content_url": f"/docs/doc?scope=example&doc_id={REPORT_ID}",
            },
        ],
    }
    documents = scope_root / "generated/documents"
    write_json(documents / "index-tree.json", tree)
    recent = {
        "schema": "docs_recent_v1",
        "basis": "edited",
        "docs": [
            {"doc_id": HIDDEN_ID, "title": "Hidden"},
            {"doc_id": ROOT_ID, "title": "Root"},
        ],
    }
    write_json(documents / "recent.json", recent)
    write_json(
        documents / ".publish/recent.json",
        {**recent, "docs": [{"doc_id": ROOT_ID, "title": "Root"}]},
    )
    write_json(
        documents / "backlinks.json",
        {
            "schema": "docs_backlinks_v1",
            "scope": "example",
            "by_target": {
                ROOT_ID: [
                    {"doc_id": REPORT_ID, "title": "Report", "viewer_url": "/docs/"},
                    {"doc_id": HIDDEN_ID, "title": "Hidden", "viewer_url": "/docs/"},
                ],
                HIDDEN_ID: [{"doc_id": ROOT_ID, "title": "Root", "viewer_url": "/docs/"}],
            },
        },
    )
    write_json(
        documents / "semantic-tokens/index.json",
        {
            "schema_version": "docs_semantic_token_usage_index_v1",
            "scope": "example",
            "occurrences": [
                {"source_doc_id": ROOT_ID},
                {"source_doc_id": HIDDEN_ID},
            ],
        },
    )
    write_json(
        documents / f"by-id/{ROOT_ID}.json",
        {
            "doc_id": ROOT_ID,
            "title": "Root",
            "content_html": (
                '<p><img src="/docs/media/example/img/keep.png?size=2">'
                '<a href="/docs/media/example/files/keep.pdf">file</a></p>'
            ),
        },
    )
    write_json(
        documents / f"by-id/{HIDDEN_ID}.json",
        {
            "doc_id": HIDDEN_ID,
            "title": "Hidden",
            "content_html": '<img src="/docs/media/example/img/hidden.png">',
        },
    )
    write_json(
        documents / f"by-id/{HIDDEN_CHILD_ID}.json",
        {"doc_id": HIDDEN_CHILD_ID, "title": "Hidden child"},
    )
    write_json(
        documents / f"by-id/{REPORT_ID}.json",
        {"doc_id": REPORT_ID, "title": "Report", "content_html": "<p>Report</p>"},
    )
    sub_scope = documents / "sub-scopes/items"
    write_json(sub_scope / "manifest.json", {"docs": [{"doc_id": SUB_ID, "title": "Sub doc"}]})
    write_json(
        sub_scope / "manage-manifest.json",
        {
            "docs": [
                {"doc_id": SUB_ID, "title": "Sub doc"},
                {"doc_id": HIDDEN_SUB_ID, "title": "Hidden sub doc", "publishable": False},
            ]
        },
    )
    write_json(
        sub_scope / f"by-id/{SUB_ID}.json",
        {"doc_id": SUB_ID, "title": "Sub doc", "content_html": "<p>Sub</p>"},
    )
    write_json(
        sub_scope / f"by-id/{HIDDEN_SUB_ID}.json",
        {"doc_id": HIDDEN_SUB_ID, "title": "Hidden sub doc"},
    )
    write_json(
        sub_scope / "subject-associations.json",
        {
            "schema_version": "docs_subject_associations_v1",
            "scope": "example",
            "sub_scope": "items",
            "subject_generation": "sha256:" + "0" * 64,
            "associations": [
                {
                    "subject": {"kind": "work", "key": "00123"},
                    "documents": [
                        {
                            "target": {"scope": "example", "sub_scope": "items", "doc_id": SUB_ID},
                            "title": "Sub doc",
                            "locations": [],
                        }
                    ],
                },
                {
                    "subject": {"kind": "series", "key": "001"},
                    "documents": [
                        {
                            "target": {"scope": "example", "sub_scope": "items", "doc_id": HIDDEN_SUB_ID},
                            "title": "Hidden sub doc",
                            "locations": [],
                        }
                    ],
                },
            ],
        },
    )
    write_json(scope_root / "generated/search/index.json", search_payload())
    write_text(scope_root / "generated/media/img/keep.png", "kept image")
    write_text(scope_root / "generated/media/img/hidden.png", "hidden image")
    write_text(scope_root / "generated/media/files/keep.pdf", "kept file")
    write_json(scope_root / "published/documents/stale.json", {"stale": True})
    (scope_root / "published/reports/intentionally-empty").mkdir(parents=True)
    config = load_docs_scope_configs(root)["example"]
    docs_scope_build_manifest.write_build_manifest(root, config)


def test_scope_publish_is_exact_rerunnable_and_does_not_touch_site(tmp_path: Path) -> None:
    prepare_repo(tmp_path)
    site_marker = tmp_path / "site/assets/data/unchanged.json"
    write_json(site_marker, {"unchanged": True})
    before_site = site_marker.read_bytes()

    preview = docs_scope_publish.preview_scope_publish(tmp_path, {"scope": "example"})
    result = docs_scope_publish.apply_scope_publish(
        tmp_path,
        {
            "scope": "example",
            "confirm": True,
            "plan_revision": preview["plan_revision"],
            "target_published_revision": preview["target_published_revision"],
        },
    )

    published = tmp_path / "docs-viewer/scopes/example/published"
    assert result["applied"] is True
    assert result["excluded_doc_ids"] == [HIDDEN_ID, HIDDEN_CHILD_ID, HIDDEN_SUB_ID]
    assert (published / "publish-manifest.json").is_file()
    assert not (published / "documents/stale.json").exists()
    assert not (published / f"documents/by-id/{HIDDEN_ID}.json").exists()
    assert not (published / f"documents/sub-scopes/items/by-id/{HIDDEN_SUB_ID}.json").exists()
    subjects = json.loads(
        (published / "documents/sub-scopes/items/subject-associations.json").read_text(
            encoding="utf-8"
        )
    )
    assert subjects["associations"] == [
        {
            "subject": {"kind": "work", "key": "00123"},
            "documents": [
                {
                    "target": {"scope": "example", "sub_scope": "items", "doc_id": SUB_ID},
                    "title": "Sub doc",
                    "locations": [],
                }
            ],
        }
    ]
    assert not (published / "media/img/hidden.png").exists()
    assert (published / "media/img/keep.png").read_text(encoding="utf-8") == "kept image"
    assert (published / "reports/intentionally-empty").is_dir()
    root_payload = json.loads(
        (published / f"documents/by-id/{ROOT_ID}.json").read_text(encoding="utf-8")
    )
    assert "/docs/published/media/example/img/keep.png?size=2" in root_payload["content_html"]
    search = json.loads((published / "search/index.json").read_text(encoding="utf-8"))
    assert [row["id"] for row in search["docs"]] == [ROOT_ID, REPORT_ID, SUB_ID]
    assert search["terms"]["sub"]["title"] == [2]
    assert "hidden" not in search["terms"]
    assert site_marker.read_bytes() == before_site
    assert docs_scope_publish.preview_scope_publish(
        tmp_path,
        {"scope": "example"},
    )["up_to_date"] is True


def test_scope_publish_rejects_build_manifest_for_another_scope(tmp_path: Path) -> None:
    prepare_repo(tmp_path)
    manifest_path = (
        tmp_path
        / "docs-viewer/scopes/example/generated"
        / docs_scope_build_manifest.BUILD_MANIFEST_FILENAME
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["scope"] = "another-scope"
    write_json(manifest_path, manifest)

    with pytest.raises(RuntimeError, match="wrong scope identity"):
        docs_scope_publish.preview_scope_publish(tmp_path, {"scope": "example"})


def test_published_reads_require_current_completion_manifest(tmp_path: Path) -> None:
    prepare_repo(tmp_path)
    preview = docs_scope_publish.preview_scope_publish(tmp_path, {"scope": "example"})
    docs_scope_publish.apply_scope_publish(
        tmp_path,
        {
            "scope": "example",
            "confirm": True,
            "plan_revision": preview["plan_revision"],
            "target_published_revision": preview["target_published_revision"],
        },
    )
    payload = docs_published_reads.read_published_doc_payload(tmp_path, "example", ROOT_ID)
    assert payload["doc_id"] == ROOT_ID
    media_path, media_type = docs_published_reads.published_media_path(
        tmp_path,
        "/docs/published/media/example/img/keep.png",
    )
    assert media_type == "img"
    assert media_path.read_text(encoding="utf-8") == "kept image"

    published = tmp_path / "docs-viewer/scopes/example/published"
    (published / f"documents/by-id/{ROOT_ID}.json").write_text("{}\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="is stale"):
        docs_published_reads.read_published_docs_index_tree(tmp_path, "example")

    (published / "publish-manifest.json").unlink()
    with pytest.raises(FileNotFoundError, match="is unavailable"):
        docs_published_reads.read_published_docs_index_tree(tmp_path, "example")


def test_scope_publish_apply_revalidates_confirmed_preview(tmp_path: Path) -> None:
    prepare_repo(tmp_path)
    preview = docs_scope_publish.preview_scope_publish(tmp_path, {"scope": "example"})
    with pytest.raises(ValueError, match="preview is stale"):
        docs_scope_publish.apply_scope_publish(
            tmp_path,
            {
                "scope": "example",
                "confirm": True,
                "plan_revision": "sha256:" + "0" * 64,
                "target_published_revision": preview["target_published_revision"],
            },
        )
