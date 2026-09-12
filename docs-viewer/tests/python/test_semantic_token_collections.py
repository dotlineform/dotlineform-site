"""Sequential collection Build updates and exact semantic-token report sources."""

from copy import deepcopy
import json
from pathlib import Path
import sys
from urllib.parse import parse_qs, urlparse

import pytest

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "docs-viewer/build"))

from docs_builder.pipeline import DocsDataBuilder
from docs_builder.sub_scope import SubScopeDocsBuilder
from docs_generated_reads import read_generated_semantic_tokens_index
from docs_scope_config import document_source_path, load_docs_scope_stage
from repo_factory import docs_scope_record, docs_sub_scope_record, write_docs_scope_config, write_site_tools_config, write_text


MAIN, WORK, MOMENT, WORKS_HOST, MOMENTS_HOST = [f"d-20260912-120000-{number:06x}" for number in range(1, 6)]
MEDIA = "[[catalogue:media:work:00638|Three symbols]]"
IMAGE = "[[catalogue:image:work:00008|alt=Nerve]]"
DETAIL = "[[catalogue:image:work:00008|alt=Detail&detail_id=003]]"


@pytest.fixture
def collections(tmp_path):
    record = docs_scope_record("analysis", scope_type="public", viewer_base_url="/analysis/", include_scope_param=False)
    record["stages"] = {
        stage: {
            "media": deepcopy(record["media"]),
            "sub_scopes": [docs_sub_scope_record("analysis", child, scope_type="local" if stage == "working" else "public") for child in ("works", "moments")],
        }
        for stage in ("working", "pre-publish")
    }
    write_site_tools_config(tmp_path)
    write_docs_scope_config(tmp_path, [record])
    for relative in ("docs-viewer/config/semantic-tokens/registry.json", "docs-viewer/config/routes/docs-viewer-routes.json"):
        write_text(tmp_path / relative, (REPO / relative).read_text())

    def source(collection, doc_id, body="", metadata="", title=None, stage="working"):
        config = load_docs_scope_stage(tmp_path, "analysis", stage)
        owner = next(child for child in config.sub_scopes if child.sub_scope == collection) if collection else config
        path = tmp_path / document_source_path(owner) / f"{doc_id}.md"
        membership = f"sub-scope: {collection}\n" if collection else ""
        write_text(path, f'---\ndoc_id: {doc_id}\ntitle: {title or doc_id}\nadded_date: "2026-09-12 12:00:00"\n{membership}{metadata}---\n{body}\n')
        return path

    def builder(collection="", doc_id=None, stage="working"):
        config = load_docs_scope_stage(tmp_path, "analysis", stage)
        options = dict(repo_root=tmp_path, config=config, skip_media_builds=True)
        if collection:
            return SubScopeDocsBuilder(**options, sub_scope=next(child for child in config.sub_scopes if child.sub_scope == collection))
        return DocsDataBuilder(**options, only_doc_ids=[doc_id] if doc_id else None)

    for stage in ("working", "pre-publish"):
        for child, host in (("works", WORKS_HOST), ("moments", MOMENTS_HOST)):
            source("", host, f":::report\nid: docs_subscope\naccess: public\nsub_scope: {child}\n:::", stage=stage)
        flags = "publishable: false\ndraft: true\n" if stage == "working" else ""
        draft = "draft: true\n" if stage == "working" else ""
        source("", MAIN, MEDIA, flags, title=f"Main {stage}", stage=stage)
        source("works", WORK, f"{IMAGE}\n\n{IMAGE}", draft + 'work_id: "00008"\n', f"Work {stage}", stage)
        source("moments", MOMENT, DETAIL, draft, f"Moment {stage}", stage)
    return tmp_path, source, builder


def usage(builder, stage="working"):
    return json.loads((builder(stage=stage).semantic_tokens_dir / "index.json").read_text())


def test_sequential_builds_preserve_collections_occurrences_and_unfiltered_sources(collections):
    root, source, builder = collections
    for collection in ("", "works", "moments"):
        builder(collection).run(write=True)
    rows = usage(builder)["occurrences"]
    assert [(row["source_sub_scope"], row["source_doc_id"]) for row in rows] == [("", MAIN), ("moments", MOMENT), ("works", WORK), ("works", WORK)]
    assert [row["raw"] for row in rows] == [MEDIA, DETAIL, IMAGE, IMAGE]
    assert all(row["source_scope"] == "analysis" for row in rows)
    assert rows[1]["target_id"] == "00008" and rows[1]["target_type"] == "work"
    assert rows[2]["source_range"] != rows[3]["source_range"]
    assert all(row["source_range"]["end"] - row["source_range"]["start"] == len(row["raw"]) for row in rows)

    # A targeted parent Save preserves both children, even with excluded/draft/Subject metadata.
    source("", MAIN, MEDIA, 'publishable: false\ndraft: true\nwork_id: "00638"\n')
    builder(doc_id=MAIN).run(write=True)
    assert usage(builder)["occurrences"] == rows
    source("works", WORK, IMAGE, "draft: false\n")
    builder("works").run(write=True)
    assert [row["raw"] for row in usage(builder)["occurrences"]] == [MEDIA, DETAIL, IMAGE]
    builder().run(write=True)
    assert [row["raw"] for row in usage(builder)["occurrences"]] == [MEDIA, DETAIL, IMAGE]

    # Removing the last token and deleting the final document in a child both remove its rows.
    source("moments", MOMENT, "No tokens remain.")
    builder("moments").run(write=True)
    source("works", WORK).unlink()
    builder("works").run(write=True)
    assert [row["source_doc_id"] for row in usage(builder)["occurrences"]] == [MAIN]
    source("", MAIN).unlink()
    builder().run(write=True)
    assert usage(builder)["occurrences"] == []
    assert len(list(root.glob("docs-viewer/scopes/analysis/working/generated/**/semantic-tokens/index.json"))) == 1


def test_report_reads_exact_collection_titles_hosts_and_stage_without_publication_filtering(collections):
    root, source, builder = collections
    for stage in ("working", "pre-publish"):
        for collection in ("", "works", "moments"):
            builder(collection, stage=stage).run(write=True)
        payload = read_generated_semantic_tokens_index(root, "analysis", stage)
        assert payload["stage"] == stage
        assert len(payload["occurrences"]) == 4
        sources = {row["target"]["doc_id"]: row for row in payload["source_documents"]}
        for doc_id, title, host, collection in ((MAIN, "Main", MAIN, ""), (WORK, "Work", WORKS_HOST, "works"), (MOMENT, "Moment", MOMENTS_HOST, "moments")):
            row = sources[doc_id]
            assert row["title"] == f"{title} {stage}"
            assert row["target"] == {"scope": "analysis", "sub_scope": collection, "doc_id": doc_id}
            query = parse_qs(urlparse(row["href"]).query)
            assert query == {"scope": ["analysis"], "stage": [stage], "doc": [host], **({"subdoc": [doc_id]} if collection else {})}
        assert "source_documents" not in usage(builder, stage)
    before = usage(builder, "pre-publish")
    source("", MAIN, "Removed in Working")
    builder(doc_id=MAIN).run(write=True)
    assert usage(builder, "pre-publish") == before


def test_report_does_not_guess_missing_child_or_ambiguous_host(collections):
    root, source, builder = collections
    for collection in ("", "works", "moments"):
        builder(collection).run(write=True)
    child_payload = builder("works").items_dir / f"{WORK}.json"
    original = child_payload.read_text()
    child_payload.unlink()
    with pytest.raises(FileNotFoundError, match="source document"):
        read_generated_semantic_tokens_index(root, "analysis", "working")
    write_text(child_payload, original)
    source("", MAIN, ":::report\nid: docs_subscope\naccess: public\nsub_scope: works\n:::")
    with pytest.raises(ValueError, match="must resolve exactly once"):
        read_generated_semantic_tokens_index(root, "analysis", "working")
