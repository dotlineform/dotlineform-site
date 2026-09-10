"""Exact, read-only document-link lookup across authoring collections."""

from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import sys

from bs4 import BeautifulSoup
import pytest

from docs_management_test_support import docs_scope_config as scopes
from repo_factory import docs_scope_record, docs_sub_scope_record, write_docs_scope_config
from docs_document_link_targets import read_document_link_targets
from docs_document_location import canonical_sub_scope_document_url
from docs_management_read_service import docs_management_get_payload
from docs_management_routes import DOCUMENT_LINK_TARGETS_PATH
from docs_viewer_service import DocsViewerRequestHandler

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "build"))
from docs_builder.common import render_markdown_to_html  # noqa: E402
from docs_builder.rendering import ContentRenderingMixin  # noqa: E402
from docs_builder.source import SourceLoadingMixin  # noqa: E402


HOST = "d-20260910-100000-aaaaaa"
OTHER_HOST = "d-20260910-100001-bbbbbb"
CHILD = "d-20260910-100002-cccccc"
PLAIN = "d-20260910-100003-dddddd"


def write_document(root: Path, doc_id: str, title: str, body: str = "", metadata: str = "") -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{doc_id}.md"
    path.write_text(f"---\ndoc_id: {doc_id}\ntitle: {title}\n{metadata}---\n{body}\n", encoding="utf-8")
    return path


@pytest.fixture
def authoring_repo(tmp_path: Path) -> Path:
    analysis = docs_scope_record("analysis", scope_type="public", viewer_base_url="/analysis/", include_scope_param=False)
    analysis["stages"] = {
        stage: {"media": deepcopy(analysis["media"]), "sub_scopes": [
            docs_sub_scope_record("analysis", name, scope_type="public" if stage == "pre-publish" else "local")
            for name in ("concepts", "works", "moments", "processing")
        ]}
        for stage in ("working", "pre-publish")
    }
    write_docs_scope_config(tmp_path, [analysis, docs_scope_record("studio")])
    for stage in ("working", "pre-publish"):
        config = scopes.load_docs_scope_stage(tmp_path, "analysis", stage)
        root = tmp_path / scopes.document_source_path(config)
        for owner in config.sub_scopes:
            (tmp_path / scopes.document_source_path(owner)).mkdir(parents=True)
        write_document(root, HOST if stage == "working" else OTHER_HOST, "Works",
                       ":::report\nid: docs_subscope\naccess: local\nsub_scope: works\n:::")
        write_document(root, PLAIN, "Same title", metadata="publishable: false\ndraft: true\n")
        write_document(tmp_path / scopes.document_source_path(config.sub_scopes[1]), CHILD, "Same title", metadata="draft: true\n")
    studio = scopes.load_docs_scope_configs(tmp_path, scope_ids=["studio"])["studio"]
    write_document(tmp_path / scopes.document_source_path(studio), PLAIN, "Studio")
    return tmp_path


@pytest.mark.parametrize("publishable", [None, True, False])
def test_lookup_keeps_exact_stage_child_and_excludes_only_unpublishable_targets(
    authoring_repo: Path, publishable: bool | None,
) -> None:
    config = scopes.load_docs_scope_stage(authoring_repo, "analysis", "working")
    metadata = "draft: true\n"
    if publishable is not None:
        metadata += f"publishable: {str(publishable).lower()}\n"
    write_document(authoring_repo / scopes.document_source_path(config), PLAIN, "Same title", metadata=metadata)
    before = {path: path.read_bytes() for path in authoring_repo.rglob("*") if path.is_file()}
    payload = docs_management_get_payload(authoring_repo, DOCUMENT_LINK_TARGETS_PATH, {"scope": ["analysis"], "stage": ["working"]})
    assert payload["sub_scopes"] == ["concepts", "works", "moments", "processing"]
    assert payload["stage"] == "working"
    records = {row["target"]["doc_id"]: row for row in payload["documents"]}
    assert records[CHILD] == {
        "target": {"scope": "analysis", "sub_scope": "works", "doc_id": CHILD},
        "title": "Same title", "href": f"/docs/?scope=analysis&doc={HOST}&subdoc={CHILD}",
    }
    assert set(records) == ({HOST, CHILD} if publishable is False else {HOST, CHILD, PLAIN})
    if publishable is not False:
        assert records[PLAIN]["href"] == f"/docs/?scope=analysis&doc={PLAIN}"
    assert OTHER_HOST not in records
    assert canonical_sub_scope_document_url(authoring_repo, "analysis", "works", CHILD, stage="working") == records[CHILD]["href"]
    assert before == {path: path.read_bytes() for path in authoring_repo.rglob("*") if path.is_file()}
    studio = read_document_link_targets(authoring_repo, scope="studio")
    assert studio["documents"][0]["href"] == f"/docs/?scope=studio&doc={PLAIN}"


@pytest.mark.parametrize("stage", [None, "pre-publish"])
def test_lookup_does_not_default_authoring_to_pre_publish(authoring_repo: Path, stage: str | None) -> None:
    with pytest.raises(ValueError):
        read_document_link_targets(authoring_repo, scope="analysis", stage=stage)


@pytest.mark.parametrize("ambiguous", [False, True])
def test_child_host_must_resolve_exactly_once(authoring_repo: Path, ambiguous: bool) -> None:
    config = scopes.load_docs_scope_stage(authoring_repo, "analysis", "working")
    root = authoring_repo / scopes.document_source_path(config)
    if ambiguous:
        write_document(root, OTHER_HOST, "Second host", ":::report\nid: docs_subscope\naccess: local\nsub_scope: works\n:::")
    else:
        (root / f"{HOST}.md").unlink()
    with pytest.raises(ValueError, match="resolve exactly once"):
        read_document_link_targets(authoring_repo, scope="analysis", stage="working")


def test_unavailable_collection_and_invalid_identity_are_not_inferred(authoring_repo: Path) -> None:
    config = scopes.load_docs_scope_stage(authoring_repo, "analysis", "working")
    empty = authoring_repo / scopes.document_source_path(config.sub_scopes[0])
    empty.rmdir()
    with pytest.raises(FileNotFoundError, match="unavailable"):
        read_document_link_targets(authoring_repo, scope="analysis", stage="working")
    assert not empty.exists()
    empty.mkdir()
    root = authoring_repo / scopes.document_source_path(config)
    path = root / f"{PLAIN}.md"
    path.write_text(path.read_text().replace(PLAIN, "not-an-id"))
    with pytest.raises(ValueError, match="immutable"):
        read_document_link_targets(authoring_repo, scope="analysis", stage="working")


@pytest.mark.parametrize("management,origin", [(False, True), (True, False), (True, True)])
def test_lookup_http_gate_requires_management_and_allowed_origin(management: bool, origin: bool) -> None:
    handler = object.__new__(DocsViewerRequestHandler)
    handler.path = DOCUMENT_LINK_TARGETS_PATH + "?scope=studio"
    handler.server = SimpleNamespace(docs_viewer_config=SimpleNamespace(management_enabled=management, generated_reads_enabled=True))
    handler.origin_allowed_for_local_api = lambda: origin
    outcomes = []
    handler.send_json = lambda payload, status: outcomes.append(status)
    handler.send_docs_api_json = lambda path, query: outcomes.append((path, query))
    handler.do_GET()
    assert outcomes == ([(DOCUMENT_LINK_TARGETS_PATH, {"scope": ["studio"]})] if management and origin else [403])


@pytest.mark.parametrize("stage,path,scope_query", [("working", "/docs/", "scope=analysis&"), ("", "/analysis/", "")])
def test_rendered_ordinary_link_preserves_child_and_literal_title(stage: str, path: str, scope_query: str) -> None:
    class Renderer(ContentRenderingMixin, SourceLoadingMixin):
        pass

    renderer = Renderer()
    renderer.viewer_base_url = path
    renderer.scope_id = "analysis"
    renderer.include_scope_param = bool(scope_query)
    renderer.config = SimpleNamespace(stage=stage)
    doc = SimpleNamespace(doc_id=HOST)
    href = f"{path}?{scope_query}doc={HOST}&subdoc={CHILD}#part"
    # These are the ordinary Markdown bytes produced by the picker for a literal title.
    source = f"[A \\[label\\] \\*literal\\* &lt;b&gt; &amp; \\\\ end](<{href}>)"
    rendered = renderer.rewrite_doc_links(render_markdown_to_html(source), current_doc=doc, docs=[doc])
    anchor = BeautifulSoup(rendered, "html.parser").find("a")
    assert anchor.get_text() == "A [label] *literal* <b> & \\ end"
    assert not anchor.find("b") and not anchor.find("em")
    expected_stage = f"stage={stage}&" if stage else ""
    assert anchor["href"] == f"{path}?{scope_query}{expected_stage}doc={HOST}&subdoc={CHILD}#part"
