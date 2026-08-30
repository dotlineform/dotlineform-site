#!/usr/bin/env python3
"""Focused checks for Docs Viewer public publish gate."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from repo_factory import docs_scope_record, docs_sub_scope_record, write_docs_scope_config


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
if str(DOCS_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(DOCS_SERVICES_DIR))

import docs_publish_gate  # noqa: E402
import docs_public_media_reconciliation  # noqa: E402
from catalogue import catalogue_document_url_refresh  # noqa: E402


LIBRARY_DOC_ID = "d-20260330-172255-8399b7"
LINEAGE_SOURCE_ID = "d-20260801-100000-aaaaaa"
LINEAGE_EDITORIAL_ID = "d-20260802-110000-bbbbbb"
LINEAGE_REPORT_HOST_ID = "d-20260807-082735-54d9d5"


class FakeR2Client:
    def __init__(self, objects: dict[str, bytes] | None = None) -> None:
        self.objects = dict(objects or {})

    def list_objects(self, prefix: str):
        return [
            SimpleNamespace(key=key, size=len(data), etag=f"etag-{len(data)}")
            for key, data in sorted(self.objects.items())
            if key.startswith(prefix)
        ]

    def get_object(self, key: str) -> bytes:
        return self.objects[key]

    def head_object(self, key: str):
        data = self.objects.get(key)
        return None if data is None else SimpleNamespace(size=len(data), etag=f"etag-{len(data)}")

    def put_object(self, key: str, path: Path, content_type: str) -> None:
        del content_type
        self.objects[key] = path.read_bytes()

    def delete_object(self, key: str) -> None:
        self.objects.pop(key, None)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_scope_config(root: Path) -> None:
    write_text(
        root / "docs-viewer/config/reports/reports.json",
        (REPO_ROOT / "docs-viewer/config/reports/reports.json").read_text(
            encoding="utf-8"
        ),
    )
    example = docs_scope_record(
        "example",
        scope_type="public",
        viewer_base_url="/example/",
        include_scope_param=False,
        default_doc_id=LIBRARY_DOC_ID,
        media_provider="repository",
        media_types=("img", "svg", "files", "html"),
    )
    write_docs_scope_config(
        root,
        [docs_scope_record("studio", default_doc_id="studio"), example],
    )


def prepare_publish_repo(root: Path) -> None:
    write_scope_config(root)
    write_json(
        root / "docs-viewer/scopes/example/generated/documents/index-tree.json",
        {
            "schema": "docs_index_tree_v1",
            "viewer_options": {"manage_only_tree_root_ids": ["manage-root"]},
            "docs": [
                {
                    "doc_id": LIBRARY_DOC_ID,
                    "title": "Example",
                    "content_url": f"/assets/data/docs/scopes/example/by-id/{LIBRARY_DOC_ID}.json",
                    "report_id": "docs_subscope",
                    "children": [
                        {
                            "doc_id": "hidden",
                            "title": "Hidden",
                            "content_url": "/assets/data/docs/scopes/example/by-id/hidden.json",
                            "publishable": False,
                            "children": [
                                {
                                    "doc_id": "hidden-child",
                                    "title": "Hidden Child",
                                    "content_url": "/assets/data/docs/scopes/example/by-id/hidden-child.json",
                                }
                            ],
                        }
                    ],
                },
                {
                    "doc_id": "manage-root",
                    "title": "Manage Root",
                    "content_url": "/assets/data/docs/scopes/example/by-id/manage-root.json",
                },
            ],
        },
    )
    write_json(
        root / "docs-viewer/scopes/example/generated/documents/recent.json",
        {
            "schema": "docs_recent_v1",
            "basis": "edited",
            "docs": [
                {"doc_id": "hidden", "title": "Hidden", "content_url": "/assets/data/docs/scopes/example/by-id/hidden.json", "timestamp": "2026-06-02 10:00:00"},
                {"doc_id": LIBRARY_DOC_ID, "title": "Example", "content_url": f"/assets/data/docs/scopes/example/by-id/{LIBRARY_DOC_ID}.json", "timestamp": "2026-06-01 10:00:00"},
            ],
        },
    )
    write_json(
        root / "docs-viewer/scopes/example/generated/documents/.publish/recent.json",
        {
            "schema": "docs_recent_v1",
            "basis": "edited",
            "docs": [
                {"doc_id": LIBRARY_DOC_ID, "title": "Example", "content_url": f"/assets/data/docs/scopes/example/by-id/{LIBRARY_DOC_ID}.json", "timestamp": "2026-06-01 10:00:00"},
            ],
        },
    )
    write_json(
        root / f"docs-viewer/scopes/example/generated/documents/by-id/{LIBRARY_DOC_ID}.json",
        {
            "title": "Example",
            "content_html": (
                '<p><a href="#" title=">" DATA-DOCS-VIEWER-LOCAL-TARGET="projects/3%20symbols">3 <em>symbols</em></a> '
                '<a href=dlf-local:bad%ZZ>/Users/private</a> '
                '<a href="#" data-docs-viewer-local-target=""></a> '
                '<a href="https://example.com">ordinary</a> '
                '<img src="/docs/media/example/img/diagram.png?size=2#view"> '
                "<iframe src='/docs/media/example/html/widget.html'></iframe> "
                '<span data-src="/docs/media/example/img/data.png" '
                'data-path="/docs/media/example/img/prose.png">'
                'src="/docs/media/example/img/text.png"</span></p>'
            ),
        },
    )
    write_json(root / "docs-viewer/scopes/example/generated/documents/by-id/hidden.json", {"title": "Hidden"})
    write_json(root / "docs-viewer/scopes/example/generated/documents/by-id/hidden-child.json", {"title": "Hidden Child"})
    write_json(root / "docs-viewer/scopes/example/generated/documents/by-id/manage-root.json", {"title": "Manage Root"})
    write_json(
        root / "docs-viewer/scopes/example/generated/documents/semantic-tokens/index.json",
        {
            "schema_version": "docs_semantic_token_usage_index_v1",
            "scope": "example",
            "occurrences": [],
        },
    )
    write_json(
        root / "docs-viewer/scopes/example/generated/documents/backlinks.json",
        {
            "schema": "docs_backlinks_v1",
            "scope": "example",
            "by_target": {LIBRARY_DOC_ID: []},
        },
    )
    write_json(
        root / "docs-viewer/scopes/example/generated/search/index.json",
        {
            "header": {
                "schema": "docs_viewer_search_index_v2",
                "scope": "example",
                "version": "fixture",
                "count": 1,
            },
            "fields": ["title", "parent_title", "identity", "last_updated"],
            "docs": [
                {
                    "id": LIBRARY_DOC_ID,
                    "title": "Example",
                    "href": f"/example/?doc={LIBRARY_DOC_ID}",
                }
            ],
            "terms": {
                "example": {"title": [0]},
                LIBRARY_DOC_ID: {"identity": [0]},
            },
        },
    )
    write_json(root / "site/assets/data/docs/scopes/example/index-tree.json", {"docs": []})
    write_json(root / "site/assets/data/docs/scopes/example/by-id/stale.json", {"title": "Stale"})
    write_json(root / "site/assets/data/docs/scopes/example/by-id/hidden.json", {"title": "Old Hidden"})
    write_json(
        root / "site/assets/data/docs/scopes/example/by-id/hidden-child.json",
        {"title": "Old Hidden Child"},
    )
    write_text(
        root
        / "site/assets/data/docs/scopes/example/projection-assets/mermaid"
        / "hidden--mermaid-0001/dark.svg",
        "<svg>old hidden dark</svg>",
    )
    write_text(
        root
        / "site/assets/data/docs/scopes/example/projection-assets/mermaid"
        / "hidden--mermaid-0001/light.svg",
        "<svg>old hidden light</svg>",
    )
    write_json(
        root / "site/assets/data/docs/scopes/example/semantic-tokens/index.json",
        {"schema_version": "stale"},
    )
    write_json(
        root / "site/assets/data/docs/scopes/example/references/index.json",
        {"schema_version": "stale-pilot"},
    )
    write_text(
        root / "site/assets/data/docs/scopes/example/media/html/widget.html",
        "<!doctype html><title>Widget</title>",
    )
    write_text(root / "site/assets/data/docs/scopes/example/media/img/diagram.png", "image bytes")
    write_json(
        root / "site/assets/data/search/example/index.json",
        {
            "header": {
                "schema": "docs_viewer_search_index_v2",
                "scope": "example",
                "version": "stale",
                "count": 0,
            },
            "fields": ["title", "parent_title", "identity", "last_updated"],
            "docs": [],
            "terms": {},
        },
    )


def write_example_subject_source(root: Path, field_name: str, value: str) -> None:
    write_text(
        root / f"docs-viewer/scopes/example/source/documents/{LIBRARY_DOC_ID}.md",
        "\n".join(
            [
                "---",
                f'doc_id: "{LIBRARY_DOC_ID}"',
                'title: "Example"',
                "publishable: true",
                f'{field_name}: "{value}"',
                "---",
                "",
                "# Example",
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
            "schema": "series_record_v3",
            "version": "before",
            "generated_at_utc": "2026-08-01T00:00:00Z",
            "series_id": series_id,
            "count": 0,
        },
        "series": {"series_id": series_id, "title": "Series", "doc_url": urls},
        "member_works": [],
    }


def test_publish_confirm_applies_explicit_exclusions_and_retains_unrelated_files() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        prepare_publish_repo(repo_root)

        preview = docs_publish_gate.publish_confirm(repo_root, {"scope": "example"})
        applied = docs_publish_gate.publish_apply(repo_root, {"scope": "example", "confirm": True})

        assert preview["operation"] == "confirm"
        assert preview["schema_version"] == "docs_publish_gate_v3"
        assert preview["changed_count"] >= 3
        assert preview["document_publish_count"] == 2
        assert preview["document_changed_count"] > preview["document_publish_count"]
        assert preview["docs"]["excluded"] == [
            "site/assets/data/docs/scopes/example/by-id/hidden.json",
            "site/assets/data/docs/scopes/example/by-id/hidden-child.json",
            (
                "site/assets/data/docs/scopes/example/projection-assets/mermaid/"
                "hidden--mermaid-0001/dark.svg"
            ),
            (
                "site/assets/data/docs/scopes/example/projection-assets/mermaid/"
                "hidden--mermaid-0001/light.svg"
            ),
        ]
        assert "removed" not in preview["docs"]
        assert "removed_count" not in preview
        assert "site/assets/data/docs/scopes/example/by-id/stale.json" not in preview["docs"]["excluded"]
        assert "site/assets/data/docs/scopes/example/media/html/widget.html" not in preview["docs"]["excluded"]
        assert "site/assets/data/docs/scopes/example/media/img/diagram.png" not in preview["docs"]["excluded"]
        assert preview["document_locations"] == {"changed": [], "excluded": []}
        assert applied["operation"] == "apply"
        public_tree = json.loads((repo_root / "site/assets/data/docs/scopes/example/index-tree.json").read_text(encoding="utf-8"))
        recent = json.loads((repo_root / "site/assets/data/docs/scopes/example/recent.json").read_text(encoding="utf-8"))
        public_doc = json.loads(
            (repo_root / f"site/assets/data/docs/scopes/example/by-id/{LIBRARY_DOC_ID}.json").read_text(encoding="utf-8")
        )

        assert public_tree["docs"][0]["doc_id"] == LIBRARY_DOC_ID
        assert public_tree["docs"][0]["report_id"] == "docs_subscope"
        assert "children" not in public_tree["docs"][0]
        assert recent["docs"][0]["doc_id"] == LIBRARY_DOC_ID
        assert public_doc["content_html"] == (
            '<p>3 symbols [local file or folder] [local file or folder] '
            '<a href="https://example.com">ordinary</a> '
            '<img src="/assets/data/docs/scopes/example/media/img/diagram.png?size=2#view"> '
            "<iframe src='/assets/data/docs/scopes/example/media/html/widget.html'></iframe> "
            '<span data-src="/docs/media/example/img/data.png" '
            'data-path="/docs/media/example/img/prose.png">'
            'src="/docs/media/example/img/text.png"</span></p>'
        )
        assert "dlf-local:" not in json.dumps(public_doc)
        assert "data-docs-viewer-local-target" not in json.dumps(public_doc)
        assert (
            repo_root
            / f"site/assets/data/docs/scopes/example/by-id/{LIBRARY_DOC_ID}.json"
        ).exists()
        assert not (repo_root / "site/assets/data/docs/scopes/example/by-id/hidden.json").exists()
        assert not (repo_root / "site/assets/data/docs/scopes/example/by-id/hidden-child.json").exists()
        assert not (
            repo_root
            / "site/assets/data/docs/scopes/example/projection-assets/mermaid/hidden--mermaid-0001"
        ).exists()
        assert (repo_root / "site/assets/data/docs/scopes/example/by-id/manage-root.json").is_file()
        assert (repo_root / "site/assets/data/docs/scopes/example/references").is_dir()
        assert (repo_root / "site/assets/data/docs/scopes/example/semantic-tokens").is_dir()
        assert not (
            repo_root / "site/assets/data/docs/scopes/example/backlinks.json"
        ).exists()
        assert json.loads(
            (
                repo_root
                / "site/assets/data/docs/scopes/example/semantic-tokens/index.json"
            ).read_text(encoding="utf-8")
        ) == {"schema_version": "stale"}
        assert (repo_root / "site/assets/data/docs/scopes/example/by-id/stale.json").is_file()
        assert (repo_root / "site/assets/data/docs/scopes/example/media/html/widget.html").is_file()
        assert (repo_root / "site/assets/data/docs/scopes/example/media/img/diagram.png").is_file()
        assert json.loads((repo_root / "site/assets/data/search/example/index.json").read_text(encoding="utf-8"))["docs"][0]["id"] == LIBRARY_DOC_ID
        assert not (
            repo_root / "site/assets/data/search/example/document-locations.json"
        ).exists()


def test_one_publish_action_reconciles_repository_and_r2_media_without_blocking_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        prepare_publish_repo(repo_root)
        config_path = repo_root / "docs-viewer/config/scopes/docs_scopes.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        public_files = config["scopes"][1]["public_projection"]["media"]["files"]
        public_files["location"] = {
            "provider": "r2",
            "path": "docs/example/files",
        }
        public_files["served_path_prefix"] = "https://media.example.test/docs/example/files"
        write_json(config_path, config)
        working_doc_path = (
            repo_root
            / f"docs-viewer/scopes/example/generated/documents/by-id/{LIBRARY_DOC_ID}.json"
        )
        working_doc = json.loads(working_doc_path.read_text(encoding="utf-8"))
        working_doc["content_html"] = working_doc["content_html"].replace(
            "</p>",
            '<a href="/docs/media/example/files/download.pdf">Download</a></p>',
        )
        write_json(working_doc_path, working_doc)
        managed_root = repo_root / "docs-viewer/scopes/example/generated/media"
        (managed_root / "img").mkdir(parents=True, exist_ok=True)
        (managed_root / "files").mkdir(parents=True, exist_ok=True)
        (managed_root / "img/diagram.png").write_bytes(b"managed image")
        (managed_root / "files/download.pdf").write_bytes(b"managed pdf")
        public_img = repo_root / "site/assets/data/docs/scopes/example/media/img"
        (public_img / "stale.png").write_bytes(b"stale")
        client = FakeR2Client(
            {
                "docs/example/files/": b"",
                "docs/example/files/stale.pdf": b"stale",
            }
        )
        monkeypatch.setattr(
            docs_public_media_reconciliation,
            "authenticated_remote_client_for_locations",
            lambda *_args, **_kwargs: client,
        )

        preview = docs_publish_gate.publish_confirm(repo_root, {"scope": "example"})
        applied = docs_publish_gate.publish_apply(
            repo_root,
            {"scope": "example", "confirm": True},
        )

        assert preview["media"]["copy_count"] == 2
        assert preview["media"]["remove_count"] == 2
        assert preview["media"]["retained_count"] == 1
        assert preview["media"]["missing_count"] == 1
        assert preview["media"]["error_count"] == 0
        assert applied["applied"] is True
        assert applied["media"]["copied_count"] == 2
        assert applied["media"]["removed_count"] == 2
        assert applied["media"]["retained_count"] == 1
        assert applied["media"]["missing_count"] == 0
        assert applied["media"]["error_count"] == 0
        assert (public_img / "diagram.png").read_bytes() == b"managed image"
        assert not (public_img / "stale.png").exists()
        assert (
            repo_root / "site/assets/data/docs/scopes/example/media/html/widget.html"
        ).is_file()
        assert client.objects["docs/example/files/download.pdf"] == b"managed pdf"
        assert "docs/example/files/stale.pdf" not in client.objects
        assert "docs/example/files/" in client.objects


def test_publish_follow_through_adds_reassigns_and_removes_exact_catalogue_urls() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        prepare_publish_repo(repo_root)
        work_path = repo_root / "site/assets/works/index/00042.json"
        series_path = repo_root / "site/assets/series/index/009.json"
        write_json(work_path, catalogue_work_payload("00042", []))
        write_json(series_path, catalogue_series_payload("009", []))
        write_example_subject_source(repo_root, "work_id", "00042")
        public_url = f"/example/?doc={LIBRARY_DOC_ID}"

        first = docs_publish_gate.publish_apply(
            repo_root,
            {"scope": "example", "confirm": True},
        )

        assert first["catalogue_document_urls"] == {
            "status": "updated",
            "stale": False,
            "affected_targets": [{"kind": "work", "key": "00042"}],
            "updated_paths": ["site/assets/works/index/00042.json"],
        }
        assert json.loads(work_path.read_text(encoding="utf-8"))["work"]["doc_url"] == [public_url]

        write_example_subject_source(repo_root, "series_id", "009")
        reassigned = docs_publish_gate.publish_apply(
            repo_root,
            {"scope": "example", "confirm": True},
        )

        assert reassigned["catalogue_document_urls"]["affected_targets"] == [
            {"kind": "series", "key": "009"},
            {"kind": "work", "key": "00042"},
        ]
        assert json.loads(work_path.read_text(encoding="utf-8"))["work"]["doc_url"] == []
        assert json.loads(series_path.read_text(encoding="utf-8"))["series"]["doc_url"] == [public_url]

        working_tree_path = repo_root / "docs-viewer/scopes/example/generated/documents/index-tree.json"
        working_tree = json.loads(working_tree_path.read_text(encoding="utf-8"))
        working_tree["docs"] = [
            {
                "doc_id": LIBRARY_DOC_ID,
                "title": "Example",
                "content_url": (
                    f"/assets/data/docs/scopes/example/by-id/{LIBRARY_DOC_ID}.json"
                ),
                "publishable": False,
            }
        ]
        write_json(working_tree_path, working_tree)
        working_search_path = repo_root / "docs-viewer/scopes/example/generated/search/index.json"
        working_search = json.loads(working_search_path.read_text(encoding="utf-8"))
        working_search["docs"] = []
        working_search["terms"] = {}
        working_search["header"]["count"] = 0
        write_json(working_search_path, working_search)
        unpublished = docs_publish_gate.publish_apply(
            repo_root,
            {"scope": "example", "confirm": True},
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
        write_example_subject_source(repo_root, "work_id", "00042")

        def fail_follow_through(_plan: object) -> object:
            raise OSError("simulated post-publication Catalogue failure")

        monkeypatch.setattr(
            catalogue_document_url_refresh,
            "apply_catalogue_document_url_refresh_plan",
            fail_follow_through,
        )

        applied = docs_publish_gate.publish_apply(
            repo_root,
            {"scope": "example", "confirm": True},
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
            / f"site/assets/data/docs/scopes/example/by-id/{LIBRARY_DOC_ID}.json"
        ).is_file()
        assert work_path.read_bytes() == work_before


def test_document_publish_remains_applied_when_media_reconciliation_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        prepare_publish_repo(repo_root)

        def fail_media(*_args: object, **_kwargs: object) -> object:
            raise OSError("simulated media reconciliation failure")

        monkeypatch.setattr(
            docs_publish_gate,
            "apply_public_media_reconciliation",
            fail_media,
        )

        applied = docs_publish_gate.publish_apply(
            repo_root,
            {"scope": "example", "confirm": True},
        )

        assert applied["applied"] is True
        assert applied["media"]["error_count"] == 1
        assert applied["media"]["errors"] == [
            "simulated media reconciliation failure"
        ]
        assert (
            repo_root
            / f"site/assets/data/docs/scopes/example/by-id/{LIBRARY_DOC_ID}.json"
        ).is_file()


def test_publish_confirm_and_apply_include_configured_sub_scope_payloads() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        prepare_publish_repo(repo_root)
        config_path = repo_root / "docs-viewer/config/scopes/docs_scopes.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["scopes"][1]["sub_scopes"] = [
            docs_sub_scope_record("example", "tags", title="Tags", scope_type="public")
        ]
        write_json(config_path, config)
        write_json(
            repo_root / "docs-viewer/scopes/example/generated/documents/sub-scopes/tags/manifest.json",
            {"docs": [{"doc_id": "scale", "title": "Scale"}]},
        )
        write_json(
            repo_root
            / "docs-viewer/scopes/example/generated/documents/sub-scopes/tags/manage-manifest.json",
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
        write_json(repo_root / "docs-viewer/scopes/example/generated/documents/sub-scopes/tags/by-id/scale.json", {"doc_id": "scale", "title": "Scale"})
        write_json(repo_root / "docs-viewer/scopes/example/generated/documents/sub-scopes/tags/by-id/hidden.json", {"doc_id": "hidden", "title": "Hidden"})
        write_json(repo_root / "site/assets/data/docs/scopes/example/tags/manifest.json", {"doc_ids": "old"})
        write_json(
            repo_root / "site/assets/data/docs/scopes/example/tags/manage-manifest.json",
            {"docs": [{"doc_id": "leaked"}]},
        )
        write_json(repo_root / "site/assets/data/docs/scopes/example/tags/by-id/old.json", {"doc_id": "old"})
        write_json(repo_root / "site/assets/data/docs/scopes/example/tags/by-id/hidden.json", {"doc_id": "hidden", "title": "Old Hidden"})
        working_scale_bytes = (
            repo_root
            / "docs-viewer/scopes/example/generated/documents/sub-scopes/tags/by-id/scale.json"
        ).read_bytes()

        preview = docs_publish_gate.publish_confirm(repo_root, {"scope": "example"})
        applied = docs_publish_gate.publish_apply(repo_root, {"scope": "example", "confirm": True})

        assert preview["operation"] == "confirm"
        assert preview["sub_scopes"] == [
            {
                "sub_scope": "tags",
                "changed": [
                    "site/assets/data/docs/scopes/example/tags/by-id/scale.json",
                    "site/assets/data/docs/scopes/example/tags/manifest.json",
                ],
                "excluded": [
                    "site/assets/data/docs/scopes/example/tags/by-id/hidden.json",
                ],
                "changed_count": 2,
                "excluded_count": 1,
            }
        ]
        assert "site/assets/data/docs/scopes/example/tags/by-id/old.json" not in preview["docs"]["excluded"]
        assert not any("/sub-scopes/tags/" in path for path in preview["docs"]["changed"])
        assert applied["operation"] == "apply"
        public_manifest = json.loads((repo_root / "site/assets/data/docs/scopes/example/tags/manifest.json").read_text(encoding="utf-8"))
        public_scale = json.loads((repo_root / "site/assets/data/docs/scopes/example/tags/by-id/scale.json").read_text(encoding="utf-8"))

        assert public_manifest == {"docs": [{"doc_id": "scale", "title": "Scale"}]}
        assert public_scale["title"] == "Scale"
        assert (
            repo_root / "site/assets/data/docs/scopes/example/tags/by-id/scale.json"
        ).read_bytes() == working_scale_bytes
        assert not (repo_root / "site/assets/data/docs/scopes/example/tags/by-id/hidden.json").exists()
        assert (repo_root / "site/assets/data/docs/scopes/example/tags/by-id/old.json").is_file()
        assert (
            repo_root
            / "site/assets/data/docs/scopes/example/tags/manage-manifest.json"
        ).is_file()
        assert not (repo_root / "site/assets/data/docs/scopes/example/sub-scopes/tags").exists()


def test_public_projection_keeps_public_reports_and_strips_local_reports() -> None:
    host = (
        '<section class="docsViewerReport" data-docs-viewer-report-host '
        'aria-label="Document report"></section>'
    )
    public_payload = {
        "report": {
            "id": "reports_list",
            "access": "public",
            "scope": None,
            "preset": None,
            "sub_scope": None,
        },
        "content_html": f"<h1>Public</h1>{host}",
    }
    local_payload = {
        "report": {
            "id": "reports_list",
            "access": "local",
            "scope": None,
            "preset": None,
            "sub_scope": None,
        },
        "content_html": f"<h1>Local</h1>{host}",
    }

    assert docs_publish_gate.project_public_report_payload(public_payload) is False
    assert public_payload["content_html"].endswith(host)
    assert docs_publish_gate.project_public_report_payload(local_payload) is True
    assert "report" not in local_payload
    assert "data-docs-viewer-report-host" not in local_payload["content_html"]


def test_public_media_url_projection_handles_quoted_and_unquoted_exact_attributes() -> None:
    projected = docs_publish_gate.project_public_media_urls(
        (
            '<img src="/docs/media/example/img/quoted.png">'
            "<a href=/docs/media/example/files/unquoted.pdf>Download</a>"
            '<span data-src="/docs/media/example/img/ignored.png">'
            'src="/docs/media/example/img/prose.png"</span>'
        ),
        {
            "/docs/media/example/img": "/public/img",
            "/docs/media/example/files": "https://media.example.test/files",
        },
    )

    assert projected == (
        '<img src="/public/img/quoted.png">'
        "<a href=https://media.example.test/files/unquoted.pdf>Download</a>"
        '<span data-src="/docs/media/example/img/ignored.png">'
        'src="/docs/media/example/img/prose.png"</span>'
    )


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
                "example",
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
            / "docs-viewer/scopes/example/generated/documents/sub-scopes/works"
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
                "schema_version": "docs_document_publication_lineage_v3",
                "working_collection": {
                    "scope": "dotlineform",
                    "sub_scope": "projects",
                },
                "editorial_collection": {
                    "scope": "example",
                    "sub_scope": "works",
                },
                "records": [
                    {
                        "working_doc_id": LINEAGE_SOURCE_ID,
                        "editorials": [
                            {
                                "doc_id": LINEAGE_EDITORIAL_ID,
                                "created_at": "2026-08-08T10:00:00Z",
                                "last_copied_at": "2026-08-08T10:00:00Z",
                                "published_url": None,
                            }
                        ],
                    }
                ],
            },
        )

        docs_publish_gate.publish_apply(
            repo_root,
            {"scope": "example", "confirm": True},
        )

        table = json.loads(lineage_path.read_text(encoding="utf-8"))
        assert table["records"][0]["editorials"][0]["published_url"] == (
            f"/example/?doc={LINEAGE_REPORT_HOST_ID}"
            f"&subdoc={LINEAGE_EDITORIAL_ID}"
        )
        assert rebuilds == [("dotlineform", "projects")]
        published_bytes = lineage_path.read_bytes()
        write_json(
            working_root / f"by-id/{LINEAGE_EDITORIAL_ID}.json",
            {"doc_id": LINEAGE_EDITORIAL_ID, "title": "Editorial B updated"},
        )
        docs_publish_gate.publish_apply(
            repo_root,
            {"scope": "example", "confirm": True},
        )
        assert lineage_path.read_bytes() == published_bytes
        assert rebuilds == [("dotlineform", "projects")]
        assert json.loads(
            (
                repo_root
                / f"site/assets/data/docs/scopes/example/works/by-id/{LINEAGE_EDITORIAL_ID}.json"
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
            {"scope": "example", "confirm": True},
        )

        table = json.loads(lineage_path.read_text(encoding="utf-8"))
        assert table["records"][0]["editorials"][0]["published_url"] is None
        assert rebuilds == [
            ("dotlineform", "projects"),
            ("dotlineform", "projects"),
        ]
        assert not (
            repo_root
            / f"site/assets/data/docs/scopes/example/works/by-id/{LINEAGE_EDITORIAL_ID}.json"
        ).exists()


def test_publish_rejects_configured_sub_scope_without_manifest() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        prepare_publish_repo(repo_root)
        config_path = repo_root / "docs-viewer/config/scopes/docs_scopes.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["scopes"][1]["sub_scopes"] = [
            docs_sub_scope_record("example", "tags", title="Tags", scope_type="public")
        ]
        write_json(config_path, config)
        (repo_root / "docs-viewer/scopes/example/generated/documents/sub-scopes/tags").mkdir(parents=True)

        try:
            docs_publish_gate.publish_confirm(repo_root, {"scope": "example"})
        except FileNotFoundError as exc:
            assert "sub-scope tags manifest not found" in str(exc)
        else:
            raise AssertionError("publish should reject configured sub-scope output without manifest")


def test_publish_apply_requires_confirmation() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        prepare_publish_repo(repo_root)

        try:
            docs_publish_gate.publish_apply(repo_root, {"scope": "example"})
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
