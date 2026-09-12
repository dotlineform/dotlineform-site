"""Scoped Links contributions, exact destinations and synchronous build outcomes."""

from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "build"))
from docs_builder import links_builder
from docs_builder.pipeline import DocsDataBuilder
from docs_builder.sub_scope import SubScopeDocsBuilder
from docs_builder.browser_config import browser_scope_record
from docs_scope_config import load_docs_scope_stage, document_source_path, generated_documents_path
from repo_factory import docs_scope_record, docs_sub_scope_record, write_docs_scope_config, write_json, write_site_tools_config, write_text

REPO = Path(__file__).resolve().parents[3]
A, B, C, D, X, F, HOST, OUTSIDE = [f"d-20260910-120000-{number:06x}" for number in range(1, 9)]


@pytest.fixture
def working_scope(tmp_path):
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
    write_json(tmp_path / links_builder.CONFIG_PATH, {"scope": "analysis", "stage": "working"})

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

    def build(doc_id=None, *, created=()):
        if doc_id == B:
            builder = SubScopeDocsBuilder(repo_root=tmp_path, config=config, sub_scope=config.sub_scopes[0], skip_media_builds=True,
                                          links_doc_ids=[B], links_created_doc_ids=list(created))
        else:
            builder = DocsDataBuilder(repo_root=tmp_path, config=config, only_doc_ids=[doc_id] if doc_id else None, skip_media_builds=True,
                                      links_created_doc_ids=list(created))
        return builder.run(write=True)

    output = tmp_path / generated_documents_path(config)
    build(created=(A, C, D, X, F, HOST, OUTSIDE))
    build(B, created=(B,))
    # B was unavailable during the parent build. Only explicitly rebuilding
    # each referring document discovers its link once B is available.
    for doc_id in (A, F, OUTSIDE):
        build(doc_id)
    return tmp_path, config, source, build, output


def read_links(output, doc_id):
    return json.loads((output / "links-by-id" / f"{doc_id}.json").read_text())


def ids(entries):
    return [row["document"]["target"]["doc_id"] for row in entries]


def test_links_view_availability_comes_from_scope_stage_config(working_scope):
    root, config, *_ = working_scope
    assert browser_scope_record(root, {}, config)["links_enabled"] is True
    pre_publish = load_docs_scope_stage(root, "analysis", "pre-publish")
    assert "links_enabled" not in browser_scope_record(root, {}, pre_publish)
    assert "links_enabled" not in browser_scope_record(root, {}, config, published=True)
    (root / links_builder.CONFIG_PATH).unlink()
    assert "links_enabled" not in browser_scope_record(root, {}, config)


def test_parent_child_records_preserve_occurrences_subjects_and_fixed_eligibility(working_scope):
    _, _, _, _, output = working_scope
    assert sorted(path.stem for path in (output / "links-by-id").glob("*.json")) == sorted((A, B, C, D, F, HOST, OUTSIDE))
    assert ids(read_links(output, A)["outgoing"]) == [B]
    assert ids(read_links(output, A)["incoming"]) == [C]
    assert ids(read_links(output, B)["incoming"]) == [A, F, OUTSIDE]
    assert read_links(output, A)["counts"]["outgoing_occurrences"] == 2
    assert read_links(output, B)["self"]["target"]["sub_scope"] == "works"
    assert "stage=" not in read_links(output, B)["self"]["href"]
    assert read_links(output, F)["self"]["subject"]["kind"] == "folder"
    assert read_links(output, D)["counts"] == dict.fromkeys(("outgoing_documents", "incoming_documents", "outgoing_occurrences", "incoming_occurrences"), 0)
    assert "relationships" not in json.loads((output / "by-id" / f"{A}.json").read_text())


def test_removal_keeps_other_incoming_and_leaves_unaffected_documents_untouched(working_scope):
    _, _, source, build, output = working_scope
    ordinary = {path: path.read_bytes() for path in output.rglob("by-id/*.json")}
    untouched = {doc_id: (output / "links-by-id" / f"{doc_id}.json").stat().st_mtime_ns for doc_id in (C, D)}
    source(A)
    result = build(A)["links_build"]
    assert result["occurrences_deleted"] == 2
    assert result["written"] == [f"{A}.json", f"{B}.json"]
    assert ids(read_links(output, B)["incoming"]) == [F, OUTSIDE]
    assert ids(read_links(output, A)["incoming"]) == [C]
    for path, content in ordinary.items():
        if path.stem != A:
            assert path.read_bytes() == content
    for doc_id, timestamp in untouched.items():
        assert (output / "links-by-id" / f"{doc_id}.json").stat().st_mtime_ns == timestamp


def test_metadata_refreshes_direct_neighbours_and_draft_is_not_eligibility(working_scope):
    _, _, source, build, output = working_scope
    source(B, metadata='work_id: "00524"\ndraft: true\n', title="Changed Work document")
    result = build(B)["links_build"]
    assert set(result["written"]) == {f"{A}.json", f"{B}.json", f"{F}.json", f"{OUTSIDE}.json"}
    assert read_links(output, A)["outgoing"][0]["document"]["subject"]["key"] == "00524"
    source(B, metadata='work_id: "00524"\ndraft: false\n', title="Changed Work document")
    assert build(B)["links_build"]["written"] == []


@pytest.mark.parametrize("metadata", ['folder_path: "projects/test"\n', 'work_id: "00524"\n', 'series_id: "test-series"\n', 'detail_uid: "test-detail"\n', ""])
def test_subject_changes_only_refresh_metadata(working_scope, metadata):
    _, _, source, build, output = working_scope
    source(A, f"[B](/docs/?scope=analysis&doc={HOST}&subdoc={B})", metadata)
    build(A)
    assert ids(read_links(output, A)["incoming"]) == [C]
    assert ids(read_links(output, A)["outgoing"]) == [B]
    assert read_links(output, C)["outgoing"][0]["document"]["subject"] == read_links(output, A)["self"]["subject"]


def test_unavailable_target_is_silent_and_not_restored_by_its_build(working_scope):
    root, config, _, build, output = working_scope
    payload = root / generated_documents_path(config.sub_scopes[0]) / "by-id" / f"{B}.json"
    payload.unlink()
    result = build(A)["links_build"]
    assert result["warnings"] == []
    assert read_links(output, A)["outgoing"] == []
    build(B)
    assert read_links(output, A)["outgoing"] == []


@pytest.mark.parametrize("missing", [A, B])
def test_missing_links_warns_and_skips_without_replacing_record(working_scope, missing):
    _, _, _, build, output = working_scope
    path = output / "links-by-id" / f"{missing}.json"
    path.unlink()
    result = build(A)
    assert not path.exists()
    assert len(result["links_build"]["warnings"]) == 1
    assert missing in result["links_build"]["warnings"][0]
    assert "analysis/working/" in result["links_build"]["warnings"][0]
    assert result["diagnostics"]["warning_count"] >= 1
    assert result["links_build"]["warnings"][0] in result["diagnostics"]["warnings"]


def test_missing_ordinary_and_links_files_do_not_imply_creation(working_scope):
    _, _, _, build, output = working_scope
    (output / "by-id" / f"{A}.json").unlink()
    (output / "links-by-id" / f"{A}.json").unlink()
    assert build(A)["links_build"]["warnings"]
    assert not (output / "links-by-id" / f"{A}.json").exists()


@pytest.mark.parametrize("deleted", [A, B])
def test_scoped_deletion_removes_record_and_known_contributions(working_scope, deleted):
    _, _, source, build, output = working_scope
    source(deleted).unlink()
    result = build(deleted)["links_build"]
    assert result["removed"] == [f"{deleted}.json"]
    assert not (output / "links-by-id" / f"{deleted}.json").exists()
    if deleted == A:
        assert ids(read_links(output, B)["incoming"]) == [F, OUTSIDE]
        assert read_links(output, C)["outgoing"] == []
    else:
        assert read_links(output, A)["outgoing"] == []
        assert read_links(output, OUTSIDE)["outgoing"] == []


def test_new_document_uses_explicit_creation_and_joins_existing_neighbour(working_scope):
    _, _, source, build, output = working_scope
    new_id = "d-20260910-120000-000009"
    source(new_id, f"[Work](/docs/?scope=analysis&doc={HOST}&subdoc={B})")
    result = build(new_id, created=(new_id,))["links_build"]
    assert set(result["written"]) == {f"{new_id}.json", f"{B}.json"}
    assert ids(read_links(output, B)["incoming"]) == [A, F, OUTSIDE, new_id]


@pytest.mark.parametrize("sub_scope", ["", "works"])
def test_cli_carries_explicit_creation_to_parent_and_child_builds(working_scope, monkeypatch, sub_scope):
    from docs_builder.cli import main

    root, config, _, _, output = working_scope
    new_id = "d-20260910-120000-000009"
    owner = config.sub_scopes[0] if sub_scope else config
    path = root / document_source_path(owner) / f"{new_id}.md"
    write_text(path, f'---\ndoc_id: {new_id}\ntitle: Created\nadded_date: "2026-09-10 12:00:00"\n---\n[A](/docs/?scope=analysis&doc={A})\n')
    monkeypatch.chdir(root)
    args = ["--scope", "analysis", "--stage", "working", "--skip-browser-config", "--skip-media-builds", "--links-doc-ids", new_id,
            "--links-created-doc-ids", new_id, "--write"]
    args.extend(["--sub-scope", sub_scope] if sub_scope else ["--only-doc-ids", new_id])
    assert main(args) == 0
    assert read_links(output, new_id)["self"]["target"]["sub_scope"] == sub_scope
    assert ids(read_links(output, new_id)["outgoing"]) == [A]


def test_unchanged_build_and_dry_run_do_not_mutate_links(working_scope):
    root, config, _, build, output = working_scope
    paths = list((output / "links-by-id").glob("*.json"))
    before = {path: path.read_bytes() for path in paths}
    assert build(OUTSIDE)["links_build"]["written"] == []
    DocsDataBuilder(repo_root=root, config=config, only_doc_ids=[A], skip_media_builds=True).run(write=False)
    assert before == {path: path.read_bytes() for path in paths}


def test_reference_parser_retains_only_exact_authored_document_targets(working_scope):
    _, _, source, build, output = working_scope
    good = f"/docs/?scope=analysis&doc={HOST}&subdoc={B}"
    source(A, f"[valid]({good})\n\n`[code]({good})`\n\n<!-- [comment]({good}) -->\n\n[wrong host](/docs/?scope=analysis&doc={A}&subdoc={B})\n\n[external](https://example.test{good})\n\n[wrong stage]({good}&stage=pre-publish)\n\n[outside](/docs/?scope=analysis&doc={OUTSIDE})\n\n[relative](./{C}.md)\n\n[local section](#part)")
    build(A)
    assert ids(read_links(output, A)["outgoing"]) == [B, C, OUTSIDE]


def test_reciprocal_self_links_and_occurrence_changes_preserve_both_directions(working_scope):
    _, _, source, build, output = working_scope
    source(A, f"[C](/analysis/?doc={C})\n\n[self](/docs/?scope=analysis&doc={A})\n\n[[catalogue:media:work:00523|[Not a doc link](/docs/?scope=analysis&doc={D})]]")
    build(A)
    assert ids(read_links(output, A)["outgoing"]) == [A, C]
    assert ids(read_links(output, A)["incoming"]) == [A, C]
    assert ids(read_links(output, C)["incoming"]) == [A]
    assert read_links(output, D)["incoming"] == []
    source(A, f"[Changed label](/docs/?scope=analysis&doc={C}#part)")
    result = build(A)["links_build"]
    assert result["occurrences_deleted"] == 2
    assert result["occurrences_added"] == 1
    assert ids(read_links(output, A)["incoming"]) == [C]
    assert read_links(output, C)["incoming"][0]["occurrences"] == [{"label": "Changed label", "href": f"/docs/?scope=analysis&doc={C}#part"}]


@pytest.mark.parametrize("title_changed", [False, True])
def test_links_reads_are_bounded_and_use_no_collection_index(working_scope, monkeypatch, title_changed):
    root, config, source, build, output = working_scope
    if title_changed:
        source(C, f"[A](/docs/?scope=analysis&doc={A})\n\n[D](/docs/?scope=analysis&doc={D})")
        build(C)
        source(A, f"[B](/docs/?scope=analysis&doc={HOST}&subdoc={B})", title="Changed")
    builder = DocsDataBuilder(repo_root=root, config=config, only_doc_ids=[A], skip_media_builds=True)
    docs = builder.load_docs()
    read_text = Path.read_text
    forbidden_names = {f"{doc_id}.{extension}" for doc_id in ({D, F, X, OUTSIDE} | ({C} if not title_changed else set())) for extension in ("md", "json")}

    def guarded(path, *args, **kwargs):
        assert path.name not in forbidden_names, f"unrelated read: {path}"
        assert path.name not in {"index-tree.json", "manifest.json", "manage-manifest.json", "links.json"}
        return read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", guarded)
    plan = links_builder.prepare_document_links(builder, docs, [A], [])
    result = links_builder.build_document_links(builder, plan, write=False)
    assert set(result["written"]) == ({f"{doc_id}.json" for doc_id in (A, B, C)} if title_changed else set())


@pytest.mark.parametrize("self_link", [False, True])
def test_collection_move_transfers_prior_relationships_and_old_delete_cannot_remove_new_owner(working_scope, self_link):
    root, config, source, build, output = working_scope
    if self_link:
        source(A, f"[B](/docs/?scope=analysis&doc={HOST}&subdoc={B})\n\n[self](/docs/?scope=analysis&doc={A}#part)")
        build(A)
    original = root / document_source_path(config) / f"{A}.md"
    destination = root / document_source_path(config.sub_scopes[0]) / f"{A}.md"
    destination.write_text(original.read_text().replace(f"doc={A}", f"doc={HOST}&subdoc={A}"))
    original.unlink()
    source(C, f"[A](/docs/?scope=analysis&doc={HOST}&subdoc={A}#part)")
    child = SubScopeDocsBuilder(repo_root=root, config=config, sub_scope=config.sub_scopes[0], links_doc_ids=[A], links_created_doc_ids=[A], skip_media_builds=True)
    child.run(write=True)
    # Placement owns the incoming source rewrites; its parent build follows the
    # child build and includes the exact old deletion identity.
    DocsDataBuilder(repo_root=root, config=config, links_doc_ids=[A, C], skip_media_builds=True).run(write=True)
    moved = read_links(output, A)
    assert moved["self"]["target"]["sub_scope"] == "works"
    assert ids(moved["outgoing"]) == ([A, B] if self_link else [B])
    assert ids(moved["incoming"]) == ([A, C] if self_link else [C])
    if self_link:
        for direction in ("incoming", "outgoing"):
            self_entry = next(row for row in moved[direction] if row["document"]["target"]["doc_id"] == A)
            assert self_entry["document"] == moved["self"]
            assert self_entry["occurrences"] == [{"label": "self", "href": moved["self"]["href"] + "#part"}]
    outgoing = read_links(output, C)["outgoing"][0]
    assert outgoing["document"]["target"] == moved["self"]["target"]
    assert outgoing["occurrences"][0]["href"] == f"/docs/?scope=analysis&doc={HOST}&subdoc={A}#part"
    assert next(row for row in read_links(output, B)["incoming"] if row["document"]["target"]["doc_id"] == A)["document"]["target"] == moved["self"]["target"]

    # The reverse move prepares the parent destination before the child deletes
    # its old identity, including a self-link whose viewer location changes.
    original.write_text(destination.read_text().replace(f"doc={HOST}&subdoc={A}", f"doc={A}"))
    destination.unlink()
    source(C, f"[A](/docs/?scope=analysis&doc={A}#part)")
    DocsDataBuilder(repo_root=root, config=config, links_doc_ids=[A, C], links_created_doc_ids=[A], skip_media_builds=True).run(write=True)
    SubScopeDocsBuilder(repo_root=root, config=config, sub_scope=config.sub_scopes[0], links_doc_ids=[A], skip_media_builds=True).run(write=True)
    returned = read_links(output, A)
    assert returned["self"]["target"]["sub_scope"] == ""
    assert ids(returned["outgoing"]) == ([A, B] if self_link else [B])
    assert ids(returned["incoming"]) == ([A, C] if self_link else [C])
    if self_link:
        for direction in ("incoming", "outgoing"):
            assert returned[direction][0]["document"] == returned["self"]
            assert returned[direction][0]["occurrences"] == [{"label": "self", "href": returned["self"]["href"] + "#part"}]
    assert read_links(output, C)["outgoing"][0]["document"] == returned["self"]
    assert next(row for row in read_links(output, B)["incoming"] if row["document"]["target"]["doc_id"] == A)["document"] == returned["self"]


def test_child_links_targets_exclude_other_rendered_children(working_scope):
    root, config, _, _, output = working_scope
    sibling = "d-20260910-120000-000009"
    path = root / document_source_path(config.sub_scopes[0]) / f"{sibling}.md"
    write_text(path, f'---\ndoc_id: {sibling}\ntitle: Sibling\nadded_date: "2026-09-10 12:00:00"\n---\n[Parent](/docs/?scope=analysis&doc={A})\n')
    builder = SubScopeDocsBuilder(repo_root=root, config=config, sub_scope=config.sub_scopes[0], links_doc_ids=[B], skip_media_builds=True)
    result = builder.run(write=True)
    assert sibling in result["item_payloads"]
    assert result["links_build"]["written"] == []
    assert result["links_build"]["warnings"] == []
    assert not (output / "links-by-id" / f"{sibling}.json").exists()


def test_failed_neighbour_write_prevents_success(working_scope, monkeypatch):
    _, _, source, build, _ = working_scope
    source(A)
    writer = links_builder.write_text_atomic

    def fail(path, content):
        if path.name == f"{B}.json":
            raise OSError("write unavailable")
        writer(path, content)

    monkeypatch.setattr(links_builder, "write_text_atomic", fail)
    with pytest.raises(OSError, match="write unavailable"):
        build(A)


@pytest.mark.parametrize("damage", ["identity", "schema", "counts"])
def test_invalid_prior_record_fails_without_replacement(working_scope, damage):
    _, _, _, build, output = working_scope
    path = output / "links-by-id" / f"{A}.json"
    payload = json.loads(path.read_text())
    if damage == "identity":
        payload["self"]["target"]["sub_scope"] = "works"
    elif damage == "schema":
        payload["schema_version"] = 2
    else:
        payload["counts"]["outgoing_occurrences"] = 100
    write_json(path, payload)
    before = path.read_bytes()
    with pytest.raises(ValueError):
        build(A)
    assert path.read_bytes() == before


@pytest.mark.parametrize("policy", [{"scope": "analysis", "stage": "pre-publish"}, {"scope": " analysis", "stage": "working"}, {"scope": "analysis"}])
def test_scope_policy_requires_exact_scope_and_working_stage(working_scope, policy):
    root, config, _, _, _ = working_scope
    write_json(root / links_builder.CONFIG_PATH, policy)
    with pytest.raises(ValueError):
        links_builder.links_enabled(root, config)


def test_relationship_output_cannot_follow_a_symlink(working_scope):
    root, _, _, build, output = working_scope
    path = output / "links-by-id" / f"{A}.json"
    outside = root / "outside.json"
    path.rename(outside)
    path.symlink_to(outside)
    before = outside.read_bytes()
    with pytest.raises(ValueError, match="configured directory"):
        build(A)
    assert outside.read_bytes() == before
