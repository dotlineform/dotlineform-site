#!/usr/bin/env python3
"""Focused checks for Docs Broken Links audit behavior."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path


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


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_doc_payload(repo_root: Path, scope: str, doc_id: str, content_html: str) -> None:
    write_json(
        repo_root / "docs-viewer/generated/docs" / scope / "by-id" / f"{doc_id}.json",
        {
            "doc_id": doc_id,
            "title": "Source",
            "viewer_url": "/docs/?scope=studio&doc=source",
            "content_html": content_html,
        },
    )


def write_public_reader_doc_payload(repo_root: Path, scope: str, doc_id: str, title: str, content_html: str) -> None:
    write_json(
        repo_root / "docs-viewer/generated/docs" / scope / "by-id" / f"{doc_id}.json",
        {
            "title": title,
            "last_updated": "2026-06-10",
            "content_html": content_html,
        },
    )


def make_repo(content_html: str) -> tempfile.TemporaryDirectory[str]:
    temp_dir = tempfile.TemporaryDirectory()
    repo_root = Path(temp_dir.name)
    (repo_root / "site-tools/config").mkdir(parents=True, exist_ok=True); (repo_root / "site-tools/config/site-tools.json").write_text("{\"schema_version\":\"site_tools_config_v1\"}\n", encoding="utf-8")
    write_json(
        repo_root / "docs-viewer/generated/docs/studio/index-tree.json",
        {
            "schema": "docs_index_tree_v1",
            "docs": [
                {
                    "doc_id": "source",
                    "title": "Source",
                    "content_url": "/docs-viewer/generated/docs/studio/by-id/source.json",
                }
            ]
        },
    )
    for scope, output_dir in docs_broken_links.SCOPE_OUTPUT_DIRS.items():
        if scope == "studio":
            continue
        write_json(repo_root / output_dir / "index-tree.json", {"schema": "docs_index_tree_v1", "docs": []})
    write_doc_payload(repo_root, "studio", "source", content_html)
    return temp_dir


def make_public_repo(scope: str, content_html: str) -> tempfile.TemporaryDirectory[str]:
    temp_dir = tempfile.TemporaryDirectory()
    repo_root = Path(temp_dir.name)
    (repo_root / "site-tools/config").mkdir(parents=True, exist_ok=True); (repo_root / "site-tools/config/site-tools.json").write_text("{\"schema_version\":\"site_tools_config_v1\"}\n", encoding="utf-8")
    for known_scope, output_dir in docs_broken_links.SCOPE_OUTPUT_DIRS.items():
        docs = []
        if known_scope == scope:
            docs = [
                {
                    "doc_id": "source",
                    "title": "Source",
                    "content_url": f"/assets/data/docs/scopes/{scope}/by-id/source.json",
                }
            ]
        write_json(repo_root / output_dir / "index-tree.json", {"schema": "docs_index_tree_v1", "docs": docs})
    write_public_reader_doc_payload(repo_root, scope, "source", "Source", content_html)
    return temp_dir


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


def main() -> None:
    tests = [
        test_missing_docs_links_inside_code_blocks_are_ignored,
        test_public_reader_payloads_do_not_need_viewer_url_metadata,
    ]
    for test in tests:
        test()


if __name__ == "__main__":
    main()
