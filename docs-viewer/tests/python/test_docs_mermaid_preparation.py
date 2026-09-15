"""Approved Pre-publish Mermaid snapshot and downstream media projection coverage."""

from __future__ import annotations

import html
import json
from pathlib import Path

import pytest

from repo_factory import docs_scope_record, docs_sub_scope_record, write_docs_scope_config, write_json, write_text
from studio.shared.python.studio_python_paths import ensure_studio_python_paths

REPO_ROOT = ensure_studio_python_paths(__file__)

import docs_deploy_repo  # noqa: E402
import docs_mermaid_preparation as preparation  # noqa: E402
import docs_public_mermaid_producer as producer  # noqa: E402
import docs_scope_publish as publication  # noqa: E402
import docs_write_rebuild as rebuild  # noqa: E402
from docs_mermaid_renderer import RenderedMermaidSvg  # noqa: E402
from docs_scope_config import document_source_path, generated_documents_path, load_docs_scope_stage, resolve_location_path, resolve_scope_path  # noqa: E402


DOC_ID = "d-20260915-120000-aaaaaa"
CHILD_ID = "d-20260915-120001-bbbbbb"
SOURCE = "flowchart LR\n  accTitle: Diagram\n  accDescr: A goes to B.\n  A --> B\n"


def fixture_scope(root: Path, *, stage: str = "pre-publish"):
    child = docs_sub_scope_record("analysis", "items", title="Items", scope_type="public")
    record = docs_scope_record(
        "analysis", scope_type="public", viewer_base_url="/analysis/", include_scope_param=False,
        default_doc_id=DOC_ID, media_provider="r2", sub_scopes=[child],
    )
    write_docs_scope_config(root, [record])
    config = load_docs_scope_stage(root, "analysis", stage)
    for collection, doc_id in ((config, DOC_ID), (config.sub_scopes[0], CHILD_ID)):
        sources = resolve_scope_path(root, document_source_path(collection))
        output = resolve_scope_path(root, generated_documents_path(collection))
        write_text(sources / f"{doc_id}.md", f"---\ndoc_id: {doc_id}\ntitle: Diagram\ndraft: false\n---\n```mermaid\n{SOURCE}```\n")
        write_json(output / "by-id" / f"{doc_id}.json", {
            "doc_id": doc_id, "title": "Diagram",
            "content_html": f'<pre><code class="language-mermaid">{html.escape(SOURCE)}</code></pre>',
        })
    output = resolve_scope_path(root, generated_documents_path(config))
    write_json(output / "index-tree.json", {"docs": [{"doc_id": DOC_ID, "title": "Diagram"}]})
    write_text(root / producer.DOCS_VIEWER_THEME_CSS_REL_PATH, (REPO_ROOT / producer.DOCS_VIEWER_THEME_CSS_REL_PATH).read_text())
    return config


@pytest.fixture
def renderer(monkeypatch):
    calls = []

    def render(identity, source_path, **_kwargs):
        calls.append(identity)
        data = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><title>Diagram</title><desc>A goes to B.</desc><rect width="10" height="10"/></svg>'
        return RenderedMermaidSvg(data, "Diagram", "A goes to B.", (0, 0, 10, 10))

    monkeypatch.setattr(producer, "render_mermaid_path", render)
    return calls


def generated_files(root: Path, config):
    directory = resolve_location_path(root, config.stage_root) / "generated"
    return publication._files_from_root(directory)


def test_prepared_pairs_keep_collection_identity_through_publish_and_deploy(tmp_path, monkeypatch, renderer):
    config = fixture_scope(tmp_path)
    original_sources = {path: path.read_bytes() for path in tmp_path.rglob("*.md")}
    result = preparation.prepare_scope_mermaid(tmp_path, config)
    assert result["collections"] == [
        {"collection": "analysis", "diagrams": 1, "variants": 2},
        {"collection": "analysis/items", "diagrams": 1, "variants": 2},
    ]
    assert len(renderer) == 4
    assert all(path.read_bytes() == data for path, data in original_sources.items())

    def forbid_render(*_args, **_kwargs):
        pytest.fail("Publish/Deploy must not render Mermaid")

    monkeypatch.setattr(producer, "render_mermaid_path", forbid_render)
    accepted, _summary = publication._published_files(config, generated_files(tmp_path, config))
    media_projection = docs_deploy_repo.public_media_url_projection(config)
    for collection, doc_id in ((config, DOC_ID), (config.sub_scopes[0], CHILD_ID)):
        child = getattr(collection, "sub_scope", "")
        prefix = Path("sub-scopes") / child if child else Path()
        payload_path = prefix / "documents/by-id" / f"{doc_id}.json"
        text = json.loads(accepted[payload_path])["content_html"]
        assert "language-mermaid" not in text and "flowchart" not in text
        assert "/pre-publish/" not in text
        projected = json.loads(docs_deploy_repo.project_document_payload(
            accepted[payload_path], label=doc_id, media_projection=media_projection,
        ))["content_html"]
        assert "/docs/published/media/" not in projected
        for theme in ("light", "dark"):
            identity = f"projection-assets/mermaid/{doc_id}--mermaid-0001/{theme}.svg"
            assert prefix / "media/svg" / identity in accepted
            assert f'data-docs-viewer-diagram-{theme}-src="https://media.example.test/' in projected
            assert f"/{identity}" in projected


def test_working_keeps_fences_and_does_not_render(tmp_path, renderer):
    config = fixture_scope(tmp_path, stage="working")
    before = generated_files(tmp_path, config)
    assert preparation.prepare_scope_mermaid(tmp_path, config) is None
    assert generated_files(tmp_path, config) == before
    assert renderer == []


@pytest.mark.parametrize("failure", ["accessibility", "renderer", "payload_identity", "stale_payload"])
def test_preparation_failure_prevents_complete_build(tmp_path, monkeypatch, renderer, failure):
    config = fixture_scope(tmp_path)
    source = resolve_scope_path(tmp_path, document_source_path(config)) / f"{DOC_ID}.md"
    output = resolve_scope_path(tmp_path, generated_documents_path(config))
    payload_path = output / "by-id" / f"{DOC_ID}.json"
    if failure == "accessibility":
        source.write_text(source.read_text().replace("  accDescr: A goes to B.\n", ""))
    elif failure == "renderer":
        def fail(*_args, **_kwargs):
            raise RuntimeError("renderer failed")
        monkeypatch.setattr(producer, "render_mermaid_path", fail)
    else:
        payload = json.loads(payload_path.read_text())
        if failure == "payload_identity":
            payload["doc_id"] = CHILD_ID
        else:
            payload["content_html"] = payload["content_html"].replace("flowchart LR", "flowchart TD")
        write_json(payload_path, payload)
    manifest = output.parent / "build-manifest.json"
    write_json(manifest, {"old": True})
    monkeypatch.setattr(rebuild, "run_rebuild_command", lambda *_args: {
        "returncode": 0, "stdout": "", "stderr": "", "elapsed_seconds": 0,
    })
    with pytest.raises((ValueError, RuntimeError), match="Mermaid"):
        rebuild.rebuild_scope_outputs(tmp_path, "analysis", stage="pre-publish", include_search=True)
    assert not manifest.exists()
    assert not list(output.parent.glob("media/svg/**/*.svg"))


def test_publish_rejects_unprepared_fences_and_missing_dark_variant(tmp_path, renderer):
    config = fixture_scope(tmp_path)
    with pytest.raises(ValueError, match="Mermaid preparation is incomplete"):
        publication._published_files(config, generated_files(tmp_path, config))
    preparation.prepare_scope_mermaid(tmp_path, config)
    files = generated_files(tmp_path, config)
    dark = next(path for path in files if path.name == "dark.svg")
    del files[dark]
    with pytest.raises(FileNotFoundError, match="generated media required"):
        publication._published_files(config, files)
