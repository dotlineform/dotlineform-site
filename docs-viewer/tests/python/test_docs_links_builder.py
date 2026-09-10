"""Normal Doc Build, closed pilot writes and schema-independent link maintenance."""

from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "build"))
from docs_builder import links_builder
from docs_builder.pipeline import DocsDataBuilder
from docs_builder.sub_scope import SubScopeDocsBuilder
from docs_builder.links_model import DocumentTarget
from docs_builder.links_schema import relationship_payload
from docs_builder.browser_config import browser_scope_record
from docs_scope_config import load_docs_scope_stage, document_source_path, generated_documents_path
from repo_factory import docs_scope_record, docs_sub_scope_record, write_docs_scope_config, write_json, write_site_tools_config, write_text


REPO = Path(__file__).resolve().parents[3]
A, B, C, D, X, F, HOST, OUTSIDE = [f"d-20260910-120000-{number:06x}" for number in range(1, 9)]


@pytest.fixture
def pilot(tmp_path):
    record = docs_scope_record("analysis", scope_type="public", viewer_base_url="/analysis/", include_scope_param=False)
    record["stages"] = {
        stage: {"media": deepcopy(record["media"]), "sub_scopes": [docs_sub_scope_record("analysis", "works", scope_type="local" if stage == "working" else "public")]}
        for stage in ("working", "pre-publish")
    }
    write_site_tools_config(tmp_path)
    write_docs_scope_config(tmp_path, [record])
    for relative in ("docs-viewer/config/routes/docs-viewer-routes.json", "docs-viewer/config/semantic-tokens/registry.json"):
        write_text(tmp_path / relative, (REPO / relative).read_text())
    config = load_docs_scope_stage(tmp_path, "analysis", "working")
    write_json(tmp_path / links_builder.CONFIG_PATH, {
        "scope": "analysis", "stage": "working",
        "test_documents": [{"sub_scope": "works" if doc_id == B else "", "doc_id": doc_id} for doc_id in (A, B, C, D, X, F)],
    })

    def source(doc_id, body="", metadata="", title=None):
        owner = config.sub_scopes[0] if doc_id == B else config
        path = tmp_path / document_source_path(owner) / f"{doc_id}.md"
        write_text(path, f'---\ndoc_id: {doc_id}\ntitle: {title or doc_id}\nadded_date: "2026-09-10 12:00:00"\n{metadata}---\n{body}\n')
        return path

    source(HOST, ":::report\nid: docs_subscope\naccess: local\nsub_scope: works\n:::")
    source(A, f"[B](/docs/?scope=analysis&doc={HOST}&subdoc={B})\n\n[B detail](/docs/?scope=analysis&doc={HOST}&subdoc={B}#detail)")
    source(B, metadata='work_id: "00523"\ndraft: true\n')
    source(C, f"[A](/docs/?scope=analysis&doc={A})")
    source(D)
    source(X, f"[B](/docs/?scope=analysis&doc={HOST}&subdoc={B})", "publishable: false\n")
    source(F, f"[B](/docs/?scope=analysis&doc={HOST}&subdoc={B})", 'folder_path: "projects/example"\n')
    source(OUTSIDE, f"[B](/docs/?scope=analysis&doc={HOST}&subdoc={B})")

    def build(doc_id=None):
        if doc_id == B:
            builder = SubScopeDocsBuilder(repo_root=tmp_path, config=config, sub_scope=config.sub_scopes[0], skip_media_builds=True)
        else:
            builder = DocsDataBuilder(repo_root=tmp_path, config=config, only_doc_ids=[doc_id] if doc_id else None, skip_media_builds=True)
        return builder.run(write=True)

    output = tmp_path / generated_documents_path(config)
    build()
    build(B)
    return tmp_path, config, source, build, output


def test_links_view_availability_comes_from_pilot_config(pilot):
    root, config, *_ = pilot
    assert browser_scope_record(root, {}, config)["links_enabled"] is True
    pre_publish = load_docs_scope_stage(root, "analysis", "pre-publish")
    assert "links_enabled" not in browser_scope_record(root, {}, pre_publish)
    assert "links_enabled" not in browser_scope_record(root, {}, config, published=True)
    (root / links_builder.CONFIG_PATH).unlink()
    assert "links_enabled" not in browser_scope_record(root, {}, config)


def read_links(output, doc_id):
    return json.loads((output / "links-by-id" / f"{doc_id}.json").read_text())


def ids(entries):
    return [row["document"]["target"]["doc_id"] for row in entries]


def test_normal_parent_and_child_builds_complete_closed_relationship_files(pilot):
    _, _, _, _, output = pilot
    assert sorted(path.stem for path in (output / "links-by-id").glob("*.json")) == sorted((A, B, C, D))
    assert ids(read_links(output, A)["outgoing"]) == [B]
    assert ids(read_links(output, A)["incoming"]) == [C]
    assert ids(read_links(output, B)["incoming"]) == [A]
    assert read_links(output, A)["counts"]["outgoing_occurrences"] == 2
    assert read_links(output, B)["self"]["target"]["sub_scope"] == "works"
    assert "stage=" not in read_links(output, B)["self"]["href"]
    assert read_links(output, D)["counts"] == dict.fromkeys(("outgoing_documents", "incoming_documents", "outgoing_occurrences", "incoming_occurrences"), 0)
    assert "relationships" not in json.loads((output / "by-id" / f"{A}.json").read_text())


def test_removal_keeps_other_incoming_and_leaves_unaffected_documents_untouched(pilot):
    _, _, source, build, output = pilot
    ordinary = {path: path.read_bytes() for path in output.rglob("by-id/*.json")}
    untouched = {doc_id: (output / "links-by-id" / f"{doc_id}.json").stat().st_mtime_ns for doc_id in (C, D)}
    source(A)
    result = build(A)["links_build"]
    assert result["occurrences_deleted"] == 2
    assert result["written"] == [f"{A}.json", f"{B}.json"]
    assert read_links(output, B)["incoming"] == []
    assert ids(read_links(output, A)["incoming"]) == [C]
    for path, content in ordinary.items():
        if path.stem != A:
            assert path.read_bytes() == content
    for doc_id, timestamp in untouched.items():
        assert (output / "links-by-id" / f"{doc_id}.json").stat().st_mtime_ns == timestamp


def test_metadata_refreshes_direct_neighbours_and_draft_is_not_eligibility(pilot):
    _, _, source, build, output = pilot
    source(B, metadata='work_id: "00524"\ndraft: true\n', title="Changed Work document")
    result = build(B)["links_build"]
    assert set(result["written"]) == {f"{A}.json", f"{B}.json"}
    assert read_links(output, A)["outgoing"][0]["document"]["subject"]["key"] == "00524"
    source(B, metadata='work_id: "00524"\ndraft: false\n', title="Changed Work document")
    assert build(B)["links_build"]["written"] == []


@pytest.mark.parametrize("metadata", ["publishable: false\n", 'folder_path: "projects/test"\n'])
def test_eligibility_removal_and_restoration_use_unfiltered_references(pilot, metadata):
    _, _, source, build, output = pilot
    body = f"[B](/docs/?scope=analysis&doc={HOST}&subdoc={B})"
    source(A, body, metadata)
    assert build(A)["links_build"]["removed"] == [f"{A}.json"]
    assert read_links(output, B)["incoming"] == []
    assert read_links(output, C)["outgoing"] == []
    source(A, body, "draft: true\n")
    build(A)
    assert ids(read_links(output, A)["incoming"]) == [C]
    assert ids(read_links(output, B)["incoming"]) == [A]


def test_missing_document_payload_is_omitted_but_missing_links_file_is_rebuilt(pilot):
    root, config, _, build, output = pilot
    (output / "links-by-id" / f"{B}.json").unlink()
    build(A)
    assert ids(read_links(output, B)["incoming"]) == [A]
    payload = root / generated_documents_path(config.sub_scopes[0]) / "by-id" / f"{B}.json"
    payload.unlink()
    build(A)
    assert not payload.exists()
    assert not (output / "links-by-id" / f"{B}.json").exists()
    assert read_links(output, A)["outgoing"] == []
    build(B)
    assert ids(read_links(output, A)["outgoing"]) == [B]


def test_deleting_source_removes_relationship_file_and_contributions(pilot):
    _, config, source, build, output = pilot
    source(A).unlink()
    build()
    assert not (output / "links-by-id" / f"{A}.json").exists()
    assert read_links(output, B)["incoming"] == []
    assert read_links(output, C)["outgoing"] == []


def test_schema_changes_reproject_without_changing_reference_detection(pilot):
    root, config, _, _, output = pilot
    targets = links_builder.pilot_targets(root, config)
    baseline = root / "var/docs-viewer/links-builder/analysis/working/state.json"
    before = baseline.read_bytes()
    def revised(view, documents):
        payload = relationship_payload(view, documents)
        return {"version": 2, "links": payload}
    result = links_builder.rebuild_links(root, config, targets, write=True, serializer=revised)
    assert result["documents_changed"] == 0
    assert result["occurrences_added"] == result["occurrences_deleted"] == 0
    assert set(result["written"]) == {f"{doc_id}.json" for doc_id in (A, B, C, D)}
    assert read_links(output, A)["version"] == 2
    assert baseline.read_bytes() == before


def test_unscoped_build_and_dry_run_do_not_mutate_links(pilot):
    root, config, _, build, output = pilot
    paths = list((output / "links-by-id").glob("*.json"))
    before = {path: path.read_bytes() for path in paths}
    assert build(OUTSIDE)["links_build"] is None
    links_builder.rebuild_links(root, config, links_builder.pilot_targets(root, config), write=False)
    assert before == {path: path.read_bytes() for path in paths}
    other = load_docs_scope_stage(root, "analysis", "pre-publish")
    assert links_builder.pilot_targets(root, other) == set()


def test_reference_parser_retains_only_exact_authored_document_targets(pilot):
    root, config, source, _, _ = pilot
    good = f"/docs/?scope=analysis&doc={HOST}&subdoc={B}"
    source(A, f"[valid]({good})\n\n`[code]({good})`\n\n<!-- [comment]({good}) -->\n\n[wrong host](/docs/?scope=analysis&doc={A}&subdoc={B})\n\n[external](https://example.test{good})\n\n[outside](/docs/?scope=analysis&doc={OUTSIDE})\n\n[relative](./{C}.md)\n\n[local section](#part)")
    documents = links_builder.load_link_documents(root, config, links_builder.pilot_targets(root, config))
    assert [ref.target.doc_id for ref in documents[DocumentTarget("analysis", "", A)].references] == [B, C]


def test_addition_occurrence_changes_public_route_and_media_labels(pilot):
    _, _, source, build, output = pilot
    source(A, f"[C](/analysis/?doc={C})\n\n[[catalogue:media:work:00523|[Not a doc link](/docs/?scope=analysis&doc={D})]]")
    result = build(A)["links_build"]
    assert result["occurrences_deleted"] == 2
    assert result["occurrences_added"] == 1
    assert ids(read_links(output, A)["outgoing"]) == [C]
    assert ids(read_links(output, C)["incoming"]) == [A]
    assert read_links(output, D)["incoming"] == []
    source(A, f"[Changed label](/docs/?scope=analysis&doc={C}#part)")
    result = build(A)["links_build"]
    assert result["occurrences_deleted"] == result["occurrences_added"] == 1
    assert read_links(output, C)["incoming"][0]["occurrences"] == [{"label": "Changed label", "href": f"/docs/?scope=analysis&doc={C}#part"}]


def test_dry_doc_build_accounts_for_its_pending_document_payload(pilot):
    root, config, _, _, output = pilot
    (output / "by-id" / f"{A}.json").unlink()
    (output / "links-by-id" / f"{A}.json").unlink()
    result = DocsDataBuilder(repo_root=root, config=config, skip_media_builds=True).run(write=False)
    assert f"{A}.json" in result["links_build"]["written"]
    assert not (output / "by-id" / f"{A}.json").exists()
    assert not (output / "links-by-id" / f"{A}.json").exists()


def test_failed_write_keeps_baseline_for_retry_and_unrelated_files_are_not_owned(pilot, monkeypatch):
    root, config, source, build, output = pilot
    baseline = root / "var/docs-viewer/links-builder/analysis/working/state.json"
    previous = baseline.read_bytes()
    outside = output / "links-by-id" / f"{OUTSIDE}.json"
    outside.write_text("unrelated file")
    source(A)
    writer = links_builder.write_text_atomic
    def fail(path, content):
        if path.name == f"{B}.json":
            raise OSError("write unavailable")
        writer(path, content)
    monkeypatch.setattr(links_builder, "write_text_atomic", fail)
    with pytest.raises(OSError, match="write unavailable"):
        build(A)
    assert baseline.read_bytes() == previous
    monkeypatch.setattr(links_builder, "write_text_atomic", writer)
    build(A)
    assert read_links(output, B)["incoming"] == []
    assert outside.read_text() == "unrelated file"


@pytest.mark.parametrize("row", [
    {"sub_scope": "", "doc_id": A},
    {"sub_scope": "unknown", "doc_id": OUTSIDE},
    {"sub_scope": "", "doc_id": "../outside"},
])
def test_pilot_policy_rejects_ambiguous_or_inexact_identity(pilot, row):
    root, config, _, _, _ = pilot
    path = root / links_builder.CONFIG_PATH
    policy = json.loads(path.read_text())
    policy["test_documents"].append(row)
    write_json(path, policy)
    with pytest.raises(ValueError):
        links_builder.pilot_targets(root, config)


def test_missing_private_baseline_recovers_from_sources(pilot):
    root, _, _, build, output = pilot
    (root / "var/docs-viewer/links-builder/analysis/working/state.json").unlink()
    (output / "links-by-id" / f"{B}.json").unlink()
    build(A)
    assert ids(read_links(output, B)["incoming"]) == [A]
    assert read_links(output, B)["counts"]["incoming_occurrences"] == 2


def test_relationship_output_cannot_follow_a_symlink(pilot):
    root, _, _, build, output = pilot
    path = output / "links-by-id" / f"{A}.json"
    outside = root / "outside.json"
    path.rename(outside)
    path.symlink_to(outside)
    before = outside.read_bytes()
    with pytest.raises(ValueError, match="configured directory"):
        build(A)
    assert outside.read_bytes() == before
