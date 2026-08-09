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
FIXTURE_SCOPE_OUTPUT_DIRS = {
    scope: Path("docs-viewer/scopes") / scope / "published/documents"
    for scope in docs_broken_links.SCOPE_OUTPUT_DIRS
}


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


def write_semantic_token_contract(repo_root: Path) -> None:
    write_json(
        repo_root / "docs-viewer/config/semantic-tokens/registry.json",
        {
            "schema_version": "docs_semantic_token_registry_v1",
            "target_lookup_url": "/docs-viewer/data/generated/semantic-tokens/target-lookup.json",
            "families": [
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
            ],
        },
    )
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
                '{"schema_version":"site_tools_config_v1"}\n',
                encoding="utf-8",
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
    ])
    assert all(entry["source_scope"] == "studio" for entry in semantic_entries)
    assert all(entry["source_doc_id"] == "source" for entry in semantic_entries)
    assert all(entry["source_range"]["end"] > entry["source_range"]["start"] for entry in semantic_entries)
    assert not any("00638" in entry["raw"] for entry in semantic_entries)
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


def main() -> None:
    tests = [
        test_missing_docs_links_inside_code_blocks_are_ignored,
        test_public_reader_payloads_do_not_need_viewer_url_metadata,
        test_semantic_token_audit_reads_source_independently_of_rendered_usage,
        test_semantic_token_source_repair_clears_the_audit,
    ]
    for test in tests:
        test()


if __name__ == "__main__":
    main()
