#!/usr/bin/env python3
"""Focused checks for Docs Broken Links audit behavior."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from repo_factory import (
    docs_scope_record,
    docs_sub_scope_record,
    write_docs_scope_config,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_BROKEN_LINKS_PATH = REPO_ROOT / "docs-viewer" / "services" / "docs_broken_links.py"
DOCS_SERVICES_DIR = DOCS_BROKEN_LINKS_PATH.parent
if str(DOCS_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(DOCS_SERVICES_DIR))


def load_docs_broken_links_module():
    spec = importlib.util.spec_from_file_location("docs_broken_links", DOCS_BROKEN_LINKS_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load docs_broken_links.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


docs_broken_links = load_docs_broken_links_module()
import docs_rendered_links  # noqa: E402


FIXTURE_SCOPE_OUTPUT_DIRS = {
    scope: Path("docs-viewer/scopes") / scope / "published/documents"
    for scope in docs_broken_links.SCOPE_OUTPUT_DIRS
}


def test_broken_links_reuses_the_pure_rendered_link_owner() -> None:
    assert docs_broken_links.collect_anchors is docs_rendered_links.collect_anchors
    assert docs_broken_links.resolve_href is docs_rendered_links.resolve_href
    assert docs_broken_links.parse_docs_target is docs_rendered_links.parse_docs_target
    assert docs_broken_links.is_same_doc_fragment_link is (
        docs_rendered_links.is_same_doc_fragment_link
    )
    assert docs_rendered_links.collect_anchors(
        '<a href="/docs/?scope=studio&doc=live">Live</a>'
        '<pre><code><a href="/docs/?scope=studio&doc=code">Code</a></code></pre>'
    ) == [
        {"href": "/docs/?scope=studio&doc=live", "text": "Live"}
    ]


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_doc_payload(repo_root: Path, scope: str, doc_id: str, content_html: str) -> None:
    write_json(
        repo_root / "docs-viewer/scopes" / scope / "published/documents/by-id" / f"{doc_id}.json",
        {
            "doc_id": doc_id,
            "title": "Source",
            "viewer_url": "/docs/?scope=studio&doc=source",
            "content_html": content_html,
        },
    )


def write_public_reader_doc_payload(repo_root: Path, scope: str, doc_id: str, title: str, content_html: str) -> None:
    write_json(
        repo_root / "docs-viewer/scopes" / scope / "published/documents/by-id" / f"{doc_id}.json",
        {
            "title": title,
            "last_updated": "2026-06-10",
            "content_html": content_html,
        },
    )


def tag_family_definition() -> dict[str, object]:
    return {
        "schema_version": "docs_semantic_token_family_definition_v1",
        "key": "tag",
        "labels": {},
        "occurrence_fields": [],
        "ui_contributions": {},
        "target_types": [
            {
                "key": "tag",
                "label": "Tag",
                "id_policy": {
                    "normalizer": "slug",
                    "input_pattern": "^[a-z0-9][a-z0-9-]*$",
                    "canonical_pattern": "^[a-z0-9][a-z0-9-]*$",
                },
                "lookup_adapter": "tag-target-lookup",
                "lookup_fields": ["title", "href", "meta", "aliases"],
            }
        ],
    }


def write_semantic_token_contract(repo_root: Path, *, include_tag: bool = False) -> None:
    families: list[dict[str, object]] = [
        {
            "schema_version": "docs_semantic_token_family_definition_v1",
            "key": "catalogue",
            "labels": {},
            "occurrence_fields": [],
            "ui_contributions": {},
            "target_types": [
                {
                    "key": "work",
                    "label": "Work",
                    "id_policy": {
                        "normalizer": "digits_left_pad",
                        "width": 5,
                        "input_pattern": "^\\d{1,5}$",
                        "canonical_pattern": "^\\d{5}$",
                    },
                    "lookup_adapter": "catalogue-work-target-lookup",
                    "lookup_fields": ["title", "href", "image"],
                }
            ],
        }
    ]
    if include_tag:
        families.append(tag_family_definition())
    write_json(
        repo_root / "docs-viewer/config/semantic-tokens/registry.json",
        {
            "schema_version": "docs_semantic_token_registry_v1",
            "target_lookup_url": "/docs-viewer/data/generated/semantic-tokens/target-lookup.json",
            "families": families,
        },
    )
    tag_targets: list[dict[str, object]] = []
    if include_tag:
        tag_targets = [
            {
                "family": "tag",
                "target_type": "tag",
                "target_id": tag_id,
                "title": tag_id,
                "href": f"/analysis/?doc=report&subdoc={doc_id}",
                "meta": ["subject", title],
                "aliases": [],
            }
            for tag_id, doc_id, title in (
                ("resolved", "d-20260811-120000-100001", "Resolved document"),
                ("stale", "d-20260811-120000-400001", "Fallback document"),
                ("unavailable", "d-20260811-120000-500001", "Stale unavailable row"),
                ("unknown", "d-20260811-120000-600001", "Stale unknown row"),
                ("zero", "d-20260811-120000-700001", "Stale zero row"),
            )
        ]
    write_json(
        repo_root / "docs-viewer/data/generated/semantic-tokens/target-lookup.json",
        {
            "schema_version": "docs_semantic_token_target_lookup_v2",
            "targets": [
                {
                    "family": "catalogue",
                    "target_type": "work",
                    "target_id": "00638",
                    "title": "3 symbols",
                    "href": "/works/?work=00638",
                    "has_details": True,
                    "image": {
                        "src": "https://media.dotlineform.test/works/img/00638-primary-1600.webp?v=1"
                    },
                },
                {
                    "family": "catalogue",
                    "target_type": "work",
                    "target_id": "00008",
                    "title": "nerve",
                    "href": "",
                },
                {
                    "family": "catalogue",
                    "target_type": "work",
                    "target_id": "00009",
                    "title": "image unavailable",
                    "href": "/works/?work=00009",
                },
            ] + tag_targets,
        },
    )


def write_tag_diagnosis_contract(repo_root: Path) -> None:
    write_semantic_token_contract(repo_root, include_tag=True)
    write_docs_scope_config(
        repo_root,
        [
            docs_scope_record(
                "analysis",
                scope_type="public",
                viewer_base_url="/analysis/",
                include_scope_param=False,
                default_doc_id="d-20260811-120000-000001",
                sub_scopes=[
                    docs_sub_scope_record(
                        "analysis",
                        "tags",
                        scope_type="public",
                    )
                ],
            )
        ],
    )
    target = lambda doc_id: {  # noqa: E731
        "scope": "analysis",
        "sub_scope": "tags",
        "doc_id": doc_id,
    }
    write_json(
        repo_root / "studio/data/canonical/tags/tag-registry.json",
        {
            "tag_registry_version": "tag_registry_v6",
            "updated_at_utc": "2026-08-11T12:00:00Z",
            "policy": {"allowed_groups": ["subject"]},
            "tags": [
                {
                    "tag_id": tag_id,
                    "group": "subject",
                    "updated_at_utc": "2026-08-11T12:00:00Z",
                    **(
                        {"primary_document": target("d-20260811-120000-499999")}
                        if tag_id == "stale"
                        else {}
                    ),
                }
                for tag_id in ("resolved", "stale", "unavailable", "zero")
            ],
        },
    )
    def document(doc_id: str, title: str, *, public: bool) -> dict[str, object]:
        locations = [
            {
                "access": "manage",
                "url": f"/docs/?scope=analysis&doc=report&subdoc={doc_id}",
                "title": title,
            }
        ]
        if public:
            locations.append(
                {
                    "access": "public",
                    "url": f"/analysis/?doc=report&subdoc={doc_id}",
                    "title": title,
                }
            )
        return {"target": target(doc_id), "title": title, "locations": locations}

    write_json(
        repo_root
        / "docs-viewer/scopes/analysis/published/documents/sub-scopes/tags/tag-associations.json",
        {
            "schema_version": "docs_tag_associations_v1",
            "scope": "analysis",
            "sub_scope": "tags",
            "declaration_generation": "sha256:fixture",
            "associations": [
                {
                    "tag_id": "resolved",
                    "documents": [
                        document(
                            "d-20260811-120000-100001",
                            "Resolved document",
                            public=True,
                        )
                    ],
                },
                {
                    "tag_id": "stale",
                    "documents": [
                        document(
                            "d-20260811-120000-400001",
                            "Fallback document",
                            public=True,
                        )
                    ],
                },
                {
                    "tag_id": "unavailable",
                    "documents": [
                        document(
                            "d-20260811-120000-500001",
                            "Unavailable document",
                            public=False,
                        )
                    ],
                },
            ],
        },
    )


def write_source_doc(repo_root: Path, scope: str, body: str) -> None:
    path = repo_root / "docs-viewer/scopes" / scope / "source/documents/source.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\n"
        "doc_id: source\n"
        "title: Source\n"
        "added_date: 2026-07-26 00:00:00\n"
        "last_updated: 2026-07-26 00:00:00\n"
        "---\n"
        f"{body}",
        encoding="utf-8",
    )


@contextmanager
def make_repo(content_html: str, *, source_body: str = "") -> Iterator[str]:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        with patch.object(docs_broken_links, "SCOPE_OUTPUT_DIRS", FIXTURE_SCOPE_OUTPUT_DIRS):
            (repo_root / "site-tools/config").mkdir(parents=True, exist_ok=True)
            (repo_root / "site-tools/config/site-tools.json").write_text(
                '{"schema_version":"site_tools_config_v1","media":{"base":"https://media.dotlineform.test","image_work_details":"/work_details/img"}}\n',
                encoding="utf-8",
            )
            write_json(
                repo_root / "_data/pipeline.json",
                {
                    "variants": {
                        "primary": {
                            "preferred_width": 1600,
                            "suffix": "primary",
                        },
                    },
                    "encoding": {"format": "webp"},
                },
            )
            write_json(
                repo_root / "studio/data/canonical/catalogue/work_details/00638.json",
                {
                    "header": {
                        "schema": "catalogue_source_work_detail_record_v1",
                        "work_id": "00638",
                    },
                    "work_id": "00638",
                    "detail_sections": [
                        {
                            "section_id": "00638-1",
                            "details": [
                                {
                                    "detail_uid": "00638-001",
                                    "detail_id": "001",
                                    "project_filename": "3 symbols detail.jpg",
                                    "media_version": 1,
                                    "title": "3 symbols detail",
                                    "width_px": 1600,
                                    "height_px": 1200,
                                },
                            ],
                        },
                    ],
                },
            )
            write_semantic_token_contract(repo_root)
            write_json(
                repo_root / "docs-viewer/scopes/studio/published/documents/index-tree.json",
                {
                    "schema": "docs_index_tree_v1",
                    "docs": [
                        {
                            "doc_id": "source",
                            "title": "Source",
                            "content_url": "/docs-viewer/scopes/studio/published/documents/by-id/source.json",
                        }
                    ],
                },
            )
            for scope, output_dir in FIXTURE_SCOPE_OUTPUT_DIRS.items():
                if scope == "studio":
                    continue
                write_json(
                    repo_root / output_dir / "index-tree.json",
                    {"schema": "docs_index_tree_v1", "docs": []},
                )
            write_doc_payload(repo_root, "studio", "source", content_html)
            write_source_doc(repo_root, "studio", source_body)
            yield temp_path


@contextmanager
def make_public_repo(scope: str, content_html: str) -> Iterator[str]:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        with patch.object(docs_broken_links, "SCOPE_OUTPUT_DIRS", FIXTURE_SCOPE_OUTPUT_DIRS):
            (repo_root / "site-tools/config").mkdir(parents=True, exist_ok=True)
            (repo_root / "site-tools/config/site-tools.json").write_text(
                '{"schema_version":"site_tools_config_v1"}\n',
                encoding="utf-8",
            )
            write_semantic_token_contract(repo_root)
            for known_scope, output_dir in FIXTURE_SCOPE_OUTPUT_DIRS.items():
                docs = []
                if known_scope == scope:
                    docs = [
                        {
                            "doc_id": "source",
                            "title": "Source",
                            "content_url": f"/assets/data/docs/scopes/{scope}/by-id/source.json",
                        }
                    ]
                write_json(
                    repo_root / output_dir / "index-tree.json",
                    {"schema": "docs_index_tree_v1", "docs": docs},
                )
            write_public_reader_doc_payload(repo_root, scope, "source", "Source", content_html)
            write_source_doc(repo_root, scope, "")
            yield temp_path


def test_fixture_scope_outputs_are_repo_relative() -> None:
    assert all(not output_dir.is_absolute() for output_dir in FIXTURE_SCOPE_OUTPUT_DIRS.values())


def test_missing_docs_links_inside_code_blocks_are_ignored() -> None:
    content_html = """
    <p><a href="/docs/?scope=studio&amp;doc=missing-prose">Missing Prose</a></p>
    <p><code><a href="/docs/?scope=studio&amp;doc=missing-inline-code">Missing Inline Code</a></code></p>
    <pre><code><a href="/docs/?scope=studio&amp;doc=missing-code">Missing Code</a></code></pre>
    <div class="language-json highlighter-rouge"><div class="highlight"><pre class="highlight"><code><span class="s2"><a href="/docs/?scope=studio&amp;doc=missing-highlighted-code">Missing Highlighted Code</a></span></code></pre></div></div>
    """
    with make_repo(content_html) as temp_path:
        result = docs_broken_links.audit_docs_broken_links(Path(temp_path), "studio")

    assert result["summary"] == {"total": 1}
    assert [entry["link_url"] for entry in result["entries"]] == ["/docs/?scope=studio&doc=missing-prose"]
    assert result["entries"][0]["from_page_scope"] == "studio"
    assert result["entries"][0]["from_page_doc_id"] == "source"
    assert "from_page_source_path" not in result["entries"][0]


def test_public_reader_payloads_do_not_need_viewer_url_metadata() -> None:
    content_html = """
    <p><a href="/analysis/?doc=missing-analysis">Missing Analysis</a></p>
    """
    with make_public_repo("analysis", content_html) as temp_path:
        result = docs_broken_links.audit_docs_broken_links(Path(temp_path), "analysis")

    assert result["summary"] == {"total": 1}
    assert result["entries"][0]["link_url"] == "/analysis/?doc=missing-analysis"
    assert result["entries"][0]["from_page_scope"] == "analysis"
    assert result["entries"][0]["from_page_doc_id"] == "source"
    assert result["entries"][0]["from_page_url"] == "/analysis/?doc=source"


def test_semantic_token_audit_reads_source_independently_of_rendered_usage() -> None:
    source_body = (
        "Resolved [[catalogue:work:00638|3 symbols]].\n"
        "Missing [[catalogue:work:99999|missing work]].\n"
        "No destination [[catalogue:work:00008|nerve]].\n"
        "Missing image [[catalogue:image:work:00009|alt=image%20unavailable]].\n"
        "Resolved image [[catalogue:image:work:00638|alt=3%20symbols]].\n"
        "Missing detail [[catalogue:image:work:00638|alt=missing%20detail&detail_id=999]].\n"
        "Resolved detail [[catalogue:image:work:00638|alt=3%20symbols%20detail&detail_id=001]].\n"
        "Unsupported [[catalogue:asset:abc|asset]].\n"
        "`Ignored [[catalogue:work:99998|inline code]]`.\n"
    )
    with make_repo("<p>No semantic-token anchors here.</p>", source_body=source_body) as temp_path:
        result = docs_broken_links.audit_docs_broken_links(Path(temp_path), "studio")

    semantic_entries = [
        entry for entry in result["entries"]
        if entry.get("issue_type") == "semantic_token"
    ]
    assert sorted(entry["reason"] for entry in semantic_entries) == sorted([
        "unsupported_kind",
        "missing_target",
        "missing_destination",
        "missing_image",
        "missing_detail_image",
    ])
    assert all(entry["source_scope"] == "studio" for entry in semantic_entries)
    assert all(entry["source_doc_id"] == "source" for entry in semantic_entries)
    assert all(entry["source_range"]["end"] > entry["source_range"]["start"] for entry in semantic_entries)
    assert not any(
        entry["raw"] == "[[catalogue:image:work:00638|alt=3%20symbols]]"
        for entry in semantic_entries
    )
    assert not any("detail_id=001" in entry["raw"] for entry in semantic_entries)
    assert not any("99998" in entry["raw"] for entry in semantic_entries)


def test_semantic_token_source_repair_clears_the_audit() -> None:
    with make_repo(
        "<p>The unresolved source remains ordinary text.</p>",
        source_body="Missing [[catalogue:work:99999|missing work]].\n",
    ) as temp_path:
        repo_root = Path(temp_path)
        broken = docs_broken_links.audit_docs_broken_links(repo_root, "studio")
        write_source_doc(
            repo_root,
            "studio",
            "Resolved [[catalogue:work:00638|3 symbols]].\n",
        )
        repaired = docs_broken_links.audit_docs_broken_links(repo_root, "studio")

    assert broken["summary"] == {"total": 1}
    assert broken["entries"][0]["reason"] == "missing_target"
    assert repaired["summary"] == {"total": 0}


def test_tag_semantic_token_audit_diagnoses_exact_resolution_state() -> None:
    source_body = (
        "Resolved [[tag:tag:resolved|Resolved]].\n"
        "Stale primary fallback [[tag:tag:stale|Stale]].\n"
        "Unknown [[tag:tag:unknown|Unknown]].\n"
        "Zero associations [[tag:tag:zero|Zero]].\n"
        "Unavailable chosen destination [[tag:tag:unavailable|Unavailable]].\n"
    )
    with make_repo("<p>No semantic-token anchors here.</p>", source_body=source_body) as temp_path:
        repo_root = Path(temp_path)
        write_tag_diagnosis_contract(repo_root)
        result = docs_broken_links.audit_docs_broken_links(repo_root, "studio")

    entries = [
        entry for entry in result["entries"]
        if entry.get("issue_type") == "semantic_token"
    ]
    assert {
        entry["target_id"]: entry["reason"]
        for entry in entries
    } == {
        "unknown": "unknown_tag",
        "zero": "missing_tag_association",
        "unavailable": "missing_tag_destination",
    }
    assert not any(entry["target_id"] in {"resolved", "stale"} for entry in entries)
    assert all(entry["link_url"] == "" for entry in entries)


def main() -> None:
    tests = [
        test_missing_docs_links_inside_code_blocks_are_ignored,
        test_public_reader_payloads_do_not_need_viewer_url_metadata,
        test_semantic_token_audit_reads_source_independently_of_rendered_usage,
        test_semantic_token_source_repair_clears_the_audit,
        test_tag_semantic_token_audit_diagnoses_exact_resolution_state,
    ]
    for test in tests:
        test()


if __name__ == "__main__":
    main()
