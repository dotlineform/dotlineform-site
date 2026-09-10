#!/usr/bin/env python3
"""Focused checks for Docs Broken Links audit behavior."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
import importlib.util
import json
import subprocess
import sys
import tempfile

import pytest
from pathlib import Path

from repo_factory import (
    docs_scope_record,
    docs_sub_scope_record,
    write_docs_scope_config,
)


SOURCE_ID = "d-20260101-000000-000001"
CHILD_ID = "d-20260101-000000-000003"
TARGET_ID = "d-20260101-000000-000004"

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
    scope: Path("docs-viewer/scopes") / scope / "generated/documents"
    for scope in ("analysis", "studio")
}


def write_scope_contract(repo_root: Path) -> None:
    write_docs_scope_config(
        repo_root,
        [
            docs_scope_record("studio", default_doc_id=SOURCE_ID),
            docs_scope_record(
                "analysis",
                scope_type="public",
                viewer_base_url="/analysis/",
                include_scope_param=False,
                default_doc_id=SOURCE_ID,
            ),
        ],
    )


def test_standalone_cli_starts_without_python_path_overrides() -> None:
    result = subprocess.run(
        [sys.executable, "-E", str(DOCS_BROKEN_LINKS_PATH), "--help"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "--scope" in result.stdout


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
        repo_root / "docs-viewer/scopes" / scope / "generated/documents/by-id" / f"{doc_id}.json",
        {
            "doc_id": doc_id,
            "title": "Source",
            "viewer_url": "/docs/?scope=studio&doc=source",
            "content_html": content_html,
        },
    )


def write_public_reader_doc_payload(repo_root: Path, scope: str, doc_id: str, title: str, content_html: str) -> None:
    write_json(
        repo_root / "docs-viewer/scopes" / scope / "generated/documents/by-id" / f"{doc_id}.json",
        {
            "title": title,
            "last_updated": "2026-06-10",
            "content_html": content_html,
        },
    )


def write_semantic_token_contract(repo_root: Path) -> None:
    families = json.loads((REPO_ROOT / "docs-viewer/config/semantic-tokens/registry.json").read_text())["families"]
    write_json(
        repo_root / "docs-viewer/config/semantic-tokens/registry.json",
        {
            "schema_version": "docs_semantic_token_registry_v1",
            "target_lookup_url": "/docs-viewer/data/generated/semantic-tokens/target-lookup.json",
            "families": families,
        },
    )
    write_json(
        repo_root / "docs-viewer/data/generated/semantic-tokens/target-lookup.json",
        {
            "schema_version": "docs_semantic_token_target_lookup_v2",
            "targets": [
                {
                    "family": "catalogue",
                    "target_type": "series",
                    "target_id": "00638",
                    "title": "3 symbols",
                    "href": "/series/?series=00638",
                    "image": {"src": "https://media.example.test/series.webp"},
                },
                {
                    "family": "catalogue",
                    "target_type": "series",
                    "target_id": "00008",
                    "title": "nerve",
                    "href": "",
                },
            ],
        },
    )


def write_source_doc(repo_root: Path, scope: str, body: str) -> None:
    path = repo_root / "docs-viewer/scopes" / scope / f"source/documents/{SOURCE_ID}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\n"
        f"doc_id: {SOURCE_ID}\n"
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
        (repo_root / "site-tools/config").mkdir(parents=True, exist_ok=True)
        (repo_root / "site-tools/config/site-tools.json").write_text(
            '{"schema_version":"site_tools_config_v1"}\n',
            encoding="utf-8",
        )
        write_semantic_token_contract(repo_root)
        write_scope_contract(repo_root)
        write_json(
            repo_root / "docs-viewer/scopes/studio/generated/documents/index-tree.json",
            {
                "schema": "docs_index_tree_v1",
                "docs": [
                    {
                        "doc_id": SOURCE_ID,
                        "title": "Source",
                        "content_url": "/docs-viewer/scopes/studio/generated/documents/by-id/source.json",
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
        write_doc_payload(repo_root, "studio", SOURCE_ID, content_html)
        write_source_doc(repo_root, "studio", source_body)
        yield temp_path


@contextmanager
def make_public_repo(scope: str, content_html: str) -> Iterator[str]:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        (repo_root / "site-tools/config").mkdir(parents=True, exist_ok=True)
        (repo_root / "site-tools/config/site-tools.json").write_text(
            '{"schema_version":"site_tools_config_v1"}\n',
            encoding="utf-8",
        )
        write_semantic_token_contract(repo_root)
        write_scope_contract(repo_root)
        for known_scope, output_dir in FIXTURE_SCOPE_OUTPUT_DIRS.items():
            docs = []
            if known_scope == scope:
                docs = [
                    {
                        "doc_id": SOURCE_ID,
                        "title": "Source",
                        "content_url": f"/assets/data/docs/scopes/{scope}/by-id/source.json",
                    }
                ]
            write_json(
                repo_root / output_dir / "index-tree.json",
                {"schema": "docs_index_tree_v1", "docs": docs},
            )
        write_public_reader_doc_payload(repo_root, scope, SOURCE_ID, "Source", content_html)
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
    assert result["entries"][0]["from_page_doc_id"] == SOURCE_ID
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
    assert result["entries"][0]["from_page_doc_id"] == SOURCE_ID
    assert result["entries"][0]["from_page_url"] == f"/docs/?scope=analysis&doc={SOURCE_ID}"


def test_semantic_token_audit_reads_source_independently_of_rendered_usage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    projects_base = tmp_path / "projects"
    monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(projects_base))
    generated = projects_base / "catalogue/generated/works/index"
    write_json(generated / "00638.json", {
        "work": {
            "work_id": "00638", "title": "3 symbols", "width_px": 1600, "height_px": 1200,
            "media": {"primary": [{
                "width": 1600, "url": "https://media.example.test/works/00638.webp?v=1",
            }]},
        },
        "sections": [{"details": [{
            "work_id": "00638", "detail_id": "001", "detail_uid": "00638-001",
            "title": "3 symbols detail", "width_px": 800, "height_px": 600,
            "media": {"primary": [{
                "width": 800, "url": "https://media.example.test/details/00638-001.webp?v=1",
            }]},
        }]}],
    })
    write_json(generated / "00009.json", {
        "work": {
            "work_id": "00009", "title": "image unavailable", "width_px": 1600, "height_px": 1200,
            "media": {"primary": []},
        },
    })
    source_body = (
        "Resolved [[catalogue:media:work:00638|3 symbols]].\n"
        "Missing [[catalogue:image:series:99999|alt=Missing%20series]].\n"
        "No destination [[catalogue:image:series:00008|alt=nerve]].\n"
        "Missing image [[catalogue:image:work:00009|alt=image%20unavailable]].\n"
        "Resolved image [[catalogue:image:work:00638|alt=3%20symbols]].\n"
        "Missing detail [[catalogue:image:work:00638|alt=missing%20detail&detail_id=999]].\n"
        "Resolved detail [[catalogue:image:work:00638|alt=3%20symbols%20detail&detail_id=001]].\n"
        "Unsupported [[catalogue:image:asset:abc|alt=asset]].\n"
        "`Ignored [[catalogue:media:work:99998|inline code]]`.\n"
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
        "missing_media",
        "missing_detail_image",
    ])
    assert all(entry["source_scope"] == "studio" for entry in semantic_entries)
    assert all(entry["source_doc_id"] == SOURCE_ID for entry in semantic_entries)
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
        source_body="Missing [[catalogue:image:series:99999|alt=Missing%20series]].\n",
    ) as temp_path:
        repo_root = Path(temp_path)
        broken = docs_broken_links.audit_docs_broken_links(repo_root, "studio")
        write_source_doc(
            repo_root,
            "studio",
            "Resolved [[catalogue:image:series:00638|alt=3%20symbols]].\n",
        )
        repaired = docs_broken_links.audit_docs_broken_links(repo_root, "studio")

    assert broken["summary"] == {"total": 1}
    assert broken["entries"][0]["reason"] == "missing_target"
    assert repaired["summary"] == {"total": 0}


def write_collection_doc(
    repo_root: Path, scope: str, doc_id: str, html: str = "", *,
    stage: str | None = None, sub_scope: str = "", body: str = "",
    metadata: dict[str, object] | None = None, report: dict[str, object] | None = None,
) -> Path:
    from docs_scope_config import document_source_path, generated_documents_path, load_docs_scope_stage
    from docs_source_model import format_source

    config = load_docs_scope_stage(repo_root, scope, stage)
    collection = next(item for item in config.sub_scopes if item.sub_scope == sub_scope) if sub_scope else config
    source_dir = repo_root / document_source_path(collection)
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / f"{doc_id}.md").write_text(format_source({
        "doc_id": doc_id, "title": doc_id, "parent_id": "", **(metadata or {}),
    }, body), encoding="utf-8")
    path = repo_root / generated_documents_path(collection) / "by-id" / f"{doc_id}.json"
    write_json(path, {"doc_id": doc_id, "content_html": html, **({"report": report} if report else {})})
    return path


def staged_scope_contract(repo_root: Path) -> None:
    analysis = docs_scope_record("analysis", scope_type="public", viewer_base_url="/analysis/", include_scope_param=False)
    analysis["stages"] = {
        stage: {"media": analysis["media"], "sub_scopes": [
            docs_sub_scope_record("analysis", name, title=name, scope_type="public" if stage == "pre-publish" else "local")
            for name in ("works", "concepts", "processing", "moments")
        ]}
        for stage in ("working", "pre-publish")
    }
    write_docs_scope_config(repo_root, [docs_scope_record("studio"), docs_scope_record("notes"), analysis])
    for stage in ("working", "pre-publish"):
        for index, name in enumerate(("works", "concepts", "processing", "moments"), start=10):
            host_id = f"d-20260101-000000-{index:06d}"
            write_collection_doc(
                repo_root, "analysis", host_id, stage=stage,
                body=f":::report\nid: docs_subscope\naccess: local\nsub_scope: {name}\n:::\n",
                report={"id": "docs_subscope", "sub_scope": name},
            )
            write_collection_doc(repo_root, "analysis", CHILD_ID, stage=stage, sub_scope=name)


def test_working_audits_every_collection_and_keeps_exact_correction_identity() -> None:
    with make_repo("") as tmp:
        root = Path(tmp)
        staged_scope_contract(root)
        for name in ("", "works", "concepts", "processing", "moments"):
            write_collection_doc(
                root, "analysis", SOURCE_ID, f'<a href="/analysis/?doc={TARGET_ID}">missing</a>',
                stage="working", sub_scope=name,
                metadata={"folder": "example", **({"publishable": False} if not name else {})},
                body="[[catalogue:media:work:99999|missing token]]",
            )
        # A stale Working index and a payload in another stage cannot satisfy the target.
        write_json(root / "docs-viewer/scopes/analysis/working/generated/documents/index-tree.json", {
            "docs": [{"doc_id": TARGET_ID, "title": "stale"}],
        })
        write_collection_doc(root, "analysis", TARGET_ID, stage="pre-publish")
        result = docs_broken_links.audit_docs_broken_links(root, "analysis", "working")
        assert result["summary"]["total"] == 10
        assert not result["unavailable_sources"]
        assert {row["from_page_sub_scope"] for row in result["entries"]} == {"", "works", "concepts", "processing", "moments"}
        for row in result["entries"]:
            assert row["from_page_scope"] == "analysis"
            assert row["from_page_stage"] == "working"
            assert row["from_page_doc_id"] == SOURCE_ID
            assert row["from_page_url"].startswith("/docs/?scope=analysis&stage=working&doc=")
            assert row["from_page_url"].endswith(("subdoc=" if row["from_page_sub_scope"] else "doc=") + SOURCE_ID)
        # Repairing the exact by-ID target clears the document findings without relationships.
        write_collection_doc(root, "analysis", TARGET_ID, stage="working")
        repaired = docs_broken_links.audit_docs_broken_links(root, "analysis", "working")
        assert repaired["summary"]["total"] == 5
        assert all(row["issue_type"] == "semantic_token" for row in repaired["entries"])


def test_studio_destination_lookup_preserves_analysis_stage_and_child_identity() -> None:
    with make_repo("") as tmp:
        root = Path(tmp)
        staged_scope_contract(root)
        works_host = "d-20260101-000000-000010"
        concepts_host = "d-20260101-000000-000011"
        write_collection_doc(root, "analysis", TARGET_ID, stage="working", sub_scope="works")
        links = {
            "existing working child": f"/analysis/?doc={works_host}&subdoc={TARGET_ID}",
            "wrong collection": f"/docs/?scope=analysis&stage=working&doc={concepts_host}&subdoc={TARGET_ID}",
            "wrong stage": f"/analysis/?stage=pre-publish&doc={works_host}&subdoc={TARGET_ID}",
            "existing pre-publish child": f"/analysis/?stage=pre-publish&doc={works_host}&subdoc={CHILD_ID}",
            "unknown scope": f"/docs/?scope=unknown&doc={SOURCE_ID}",
            "unsafe target": "/docs/?scope=studio&doc=../outside",
        }
        write_collection_doc(root, "studio", SOURCE_ID, "".join(f'<a href="{url}">{label}</a>' for label, url in links.items()))
        result = docs_broken_links.audit_docs_broken_links(root, "studio")
        assert {row["link_text"] for row in result["entries"]} == {"wrong collection", "wrong stage", "unknown scope", "unsafe target"}
        assert all(row["from_page_scope"] == "studio" for row in result["entries"])


def test_missing_source_payload_does_not_hide_other_findings_or_token_diagnosis() -> None:
    with make_repo("") as tmp:
        root = Path(tmp)
        missing = write_collection_doc(root, "studio", TARGET_ID, body="[[catalogue:media:work:99999|missing token]]")
        missing.unlink()
        write_collection_doc(root, "studio", SOURCE_ID, f'<a href="/docs/?scope=studio&doc={TARGET_ID}">unbuilt</a>')
        result = docs_broken_links.audit_docs_broken_links(root, "studio")
        assert result["summary"]["total"] == 2
        assert [row["from_page_doc_id"] for row in result["unavailable_sources"]] == [TARGET_ID]


def test_fragment_ignores_require_the_same_stage_and_child_route() -> None:
    with make_repo("") as tmp:
        root = Path(tmp)
        staged_scope_contract(root)
        host = "d-20260101-000000-000010"
        links = ["#section", f"{SOURCE_ID}.md#section", f"/analysis/?doc={host}&subdoc={SOURCE_ID}#section"]
        wrong = f"/analysis/?stage=pre-publish&doc={host}&subdoc={SOURCE_ID}#section"
        write_collection_doc(root, "analysis", SOURCE_ID, "".join(f'<a href="{url}">section</a>' for url in [*links, wrong]), stage="working", sub_scope="works")
        result = docs_broken_links.audit_docs_broken_links(root, "analysis", "working")
        assert [row["link_url"] for row in result["entries"]] == [wrong]


@pytest.mark.parametrize("body, allowed", [
    ({"scope": "studio", "report_context": {"scope": "studio"}}, True),
    ({"scope": "notes", "report_context": {"scope": "studio"}}, True),
    ({"scope": "analysis", "stage": "working", "report_context": {"scope": "analysis", "stage": "working"}}, True),
    ({"scope": "analysis", "stage": "working", "report_context": {"scope": "studio"}}, False),
    ({"scope": "analysis", "report_context": {"scope": "analysis", "stage": "working"}}, False),
    ({"scope": "analysis", "stage": "pre-publish", "report_context": {"scope": "analysis", "stage": "pre-publish"}}, False),
    ({"scope": "studio", "report_context": {"scope": "analysis", "stage": "working"}}, False),
    ({"scope": "studio"}, False),
])
def test_management_dispatch_validates_report_source_partition(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, body: dict, allowed: bool) -> None:
    import docs_management_broken_links_service as adapter
    import docs_management_service as management
    import docs_management_routes as routes

    staged_scope_contract(tmp_path)
    calls = []
    monkeypatch.setattr(adapter, "audit_docs_broken_links", lambda root, scope, stage: calls.append((scope, stage)) or {"ok": True, "summary": {"total": 0}})
    monkeypatch.setattr(adapter, "log_event", lambda *args: None)
    if allowed:
        status, payload = management.docs_management_post_response(tmp_path, routes.BROKEN_LINKS_PATH, body)
        assert status == 200 and payload["ok"]
        assert calls == [(body["scope"], body.get("stage"))]
    else:
        with pytest.raises(ValueError):
            management.docs_management_post_response(tmp_path, routes.BROKEN_LINKS_PATH, body)
        assert calls == []


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
