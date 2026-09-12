"""Same-stage placement and completed source/generated ownership contracts."""

from copy import deepcopy
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from urllib.parse import quote

import pytest

import docs_management_mutations as mutations
import docs_management_mutation_service as executor
import docs_management_service as service
from docs_management_document_target import managed_document_metadata
from docs_scope_config import load_docs_scope_stage, document_source_path, generated_documents_path, resolve_location_path
from repo_factory import docs_scope_record, docs_sub_scope_record, write_docs_scope_config, write_site_tools_config, write_text, write_json

BUILD_DIR = Path(__file__).resolve().parents[2] / "build"
if str(BUILD_DIR) not in sys.path:
    sys.path.insert(0, str(BUILD_DIR))

from docs_builder.pipeline import DocsDataBuilder  # noqa: E402
from docs_builder.sub_scope import SubScopeDocsBuilder  # noqa: E402


REPO = Path(__file__).resolve().parents[3]
A, B, P, X, CHILD, WORKS, CONCEPTS, DEFAULT = [f"d-20260912-160000-{number:06x}" for number in range(1, 9)]


@pytest.fixture
def working(tmp_path, monkeypatch):
    record = docs_scope_record("analysis", scope_type="public", default_doc_id=DEFAULT, viewer_base_url="/analysis/", include_scope_param=False)
    record["media"]["build_sources"]["mermaid"] = {"producer": "mermaid", "publishes_to": "svg"}
    record["media"]["types"]["svg"]["build_inputs"] = ["mermaid"]
    record["stages"] = {
        stage: {"default_doc_id": DEFAULT, "media": deepcopy(record["media"]), "sub_scopes": [
            docs_sub_scope_record(
                "analysis", name, scope_type="local" if stage == "working" else "public",
                sub_scope_customisation={"id": "working_works" if stage == "working" else "pre_publish_works", "settings": {}} if name == "works" else None,
            )
            for name in ("works", "concepts")
        ]} for stage in ("working", "pre-publish")
    }
    write_site_tools_config(tmp_path)
    write_docs_scope_config(tmp_path, [record])
    for relative in ("docs-viewer/config/routes/docs-viewer-routes.json", "docs-viewer/config/semantic-tokens/registry.json"):
        write_text(tmp_path / relative, (REPO / relative).read_text())
    write_json(tmp_path / "docs-viewer/config/links-builder.json", {"scope": "analysis", "stage": "working"})
    config = load_docs_scope_stage(tmp_path, "analysis", "working")
    owners = {"": config, **{owner.sub_scope: owner for owner in config.sub_scopes}}
    for owner in owners.values():
        (tmp_path / document_source_path(owner)).mkdir(parents=True)
        for media in owner.media.types.values():
            resolve_location_path(tmp_path, media.source_location).mkdir(parents=True, exist_ok=True)
        for build in owner.media.build_sources.values():
            resolve_location_path(tmp_path, build.location).mkdir(parents=True, exist_ok=True)

    def source(doc_id, collection="", body="", **metadata):
        path = tmp_path / document_source_path(owners[collection]) / f"{doc_id}.md"
        write_text(path, mutations.source_model.format_source({
            "doc_id": doc_id, "title": doc_id, "added_date": "2026-09-12 16:00:00", "draft": False, **metadata,
        }, body or f"# {doc_id}\n", sub_scope=collection))
        return path

    for host, collection in ((WORKS, "works"), (CONCEPTS, "concepts")):
        source(host, body=f":::report\nid: docs_subscope\naccess: local\nsub_scope: {collection}\n:::\n")
    source(DEFAULT)
    source(P)
    source(A, work_id="00523")
    source(B, "concepts")
    source(X, body=f"[A](/docs/?scope=analysis&doc={A}#detail)", publishable=False)
    calls = []

    def build(collection=""):
        builder = (SubScopeDocsBuilder(repo_root=tmp_path, config=config, sub_scope=owners[collection], skip_media_builds=True)
                   if collection else DocsDataBuilder(repo_root=tmp_path, config=config, skip_media_builds=True))
        return builder.run(write=True)

    def rebuild_parent(repo_root, scope, **options):
        assert repo_root == tmp_path and scope == "analysis" and options["stage"] == "working"
        assert options["include_search"] is False
        calls.append("")
        return build()

    def rebuild_child(repo_root, scope, collection, **options):
        assert repo_root == tmp_path and scope == "analysis" and options["stage"] == "working"
        calls.append(collection)
        return build(collection)

    monkeypatch.setattr(executor.write_rebuild, "rebuild_scope_outputs", rebuild_parent)
    monkeypatch.setattr(executor.write_rebuild, "rebuild_sub_scope_outputs", rebuild_child)
    return SimpleNamespace(root=tmp_path, config=config, owners=owners, source=source, build=build, calls=calls)


def target(doc_id=A, collection=""):
    return {"scope": "analysis", "stage": "working", "doc_id": doc_id, **({"sub_scope": collection} if collection else {})}


@pytest.mark.parametrize("parent", ["", P, WORKS])
def test_metadata_and_drop_share_placement(working, parent):
    drop = mutations.plan_move(working.root, {**target(), "parent_id": parent})
    metadata = mutations.plan_update_metadata(working.root, {**target(), "title": A, "parent_id": parent})
    assert drop.response["placement"] == metadata.response["placement"]
    assert drop.response["target"] == metadata.response["target"]
    assert [item.path for item in drop.source_writes] == [item.path for item in metadata.source_writes]


@pytest.mark.parametrize("protected", [A, WORKS, DEFAULT])
def test_collection_refusal_is_silent_and_preserves_other_metadata(working, protected):
    # The source tree changes after the metadata read, before confirmation/drop.
    managed_document_metadata(working.root, target(protected))
    if protected == A:
        working.source(CHILD, parent_id=A)
    before = (working.root / document_source_path(working.config) / f"{protected}.md").read_bytes()
    drop = mutations.plan_move(working.root, {**target(protected), "parent_id": CONCEPTS})
    assert drop.response["placement"] == {"changed": False, "collection_changed": False, "ignored": True}
    assert not drop.has_source_changes
    status, result = service.docs_management_post_response(working.root, service.routes.UPDATE_METADATA_PATH, {
        **target(protected), "title": "Renamed", "parent_id": CONCEPTS,
    })
    assert status == 200 and result["placement"] == drop.response["placement"]
    assert result["target"] == target(protected)
    assert result["record"]["title"] == "Renamed"
    path = working.root / document_source_path(working.config) / f"{protected}.md"
    assert path.read_bytes() != before and "sub-scope:" not in path.read_text()
    ordinary = mutations.plan_move(working.root, {**target(protected), "parent_id": P})
    assert ordinary.response["placement"]["changed"] is True
    assert len(ordinary.source_writes) == 1 and not ordinary.rebuilds


def test_collection_round_trip_finishes_sources_media_links_and_projections(working):
    image = working.owners[""].media.types["svg"]
    asset = resolve_location_path(working.root, image.source_location) / "diagram.svg"
    asset.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><path d="M0 0L10 10"/></svg>')
    original_link = f"/docs/?scope=analysis&doc={A}"
    body = f"[Parent]({P}.md#top)\n\n[[media:{image.reference_prefix}/diagram.svg]]\n\n`[Example]({original_link})`\n\n<!-- {original_link} -->\n"
    original = working.source(A, body=body, work_id="00523")
    working.source(P, body=f"[A]({original_link})\n[Remote](https://example.test{original_link})\n[Preview]({original_link}&stage=pre-publish)")
    for collection in ("works", "concepts", ""):
        working.build(collection)
    working.calls.clear()
    for old, new, parent, metadata in (("", "works", WORKS, False), ("works", "concepts", CONCEPTS, True), ("concepts", "", P, False)):
        source_path = working.root / document_source_path(working.owners[old]) / f"{A}.md"
        request = {**target(collection=old), "parent_id": parent}
        route = service.routes.MOVE_PATH
        if metadata:
            loaded = managed_document_metadata(working.root, target(collection=old))
            assert loaded["location_parent_id"] == WORKS
            request.update(title="Moved title", source_revision=loaded["source_revision"])
            route = service.routes.UPDATE_METADATA_PATH
        status, response = service.docs_management_post_response(working.root, route, request)
        assert status == 200 and response["ok"] is True and response["rebuild"]["ok"] is True
        assert response["target"] == target(collection=new)
        assert response["placement"]["collection_changed"] is True
        assert not source_path.exists()
        path = working.root / document_source_path(working.owners[new]) / f"{A}.md"
        fields, content = mutations.source_model.parse_source(path)
        assert fields["doc_id"] == A and fields["work_id"] == "00523"
        assert fields.get("sub-scope", "") == new
        assert ("parent_id" not in fields) if new else fields["parent_id"] == P
        assert f"`[Example]({original_link})`" in content and f"<!-- {original_link} -->" in content
        assert f"doc={P}#top" in content
        media = working.owners[new].media.types["svg"]
        assert f"{media.reference_prefix}/diagram.svg" in content
        assert (resolve_location_path(working.root, media.source_location) / "diagram.svg").read_bytes() == asset.read_bytes()
        output = working.root / generated_documents_path(working.owners[new])
        assert (output / "by-id" / f"{A}.json").is_file()
        assert not (working.root / generated_documents_path(working.owners[old]) / "by-id" / f"{A}.json").exists()
        expected = f"doc={dict(works=WORKS, concepts=CONCEPTS).get(new, A)}" + (f"&subdoc={A}" if new else "")
        excluded = working.root / document_source_path(working.config) / f"{X}.md"
        assert expected + "#detail" in excluded.read_text()
        parent_source = working.root / document_source_path(working.config) / f"{P}.md"
        assert f"https://example.test{original_link}" in parent_source.read_text()
        assert f"{original_link}&stage=pre-publish" in parent_source.read_text()
        links = json.loads((working.root / generated_documents_path(working.config) / "links-by-id" / f"{A}.json").read_text())
        assert links["self"]["target"].get("sub_scope", "") == new
        assert [item["document"]["target"]["doc_id"] for item in links["incoming"]] == [P]
    assert original.is_file() and working.calls == ["works", "", "concepts", "works", "", "concepts", ""]


def test_preflight_conflicts_do_not_relocate_and_rebuild_failure_is_visible(working, monkeypatch):
    original = working.root / document_source_path(working.config) / f"{A}.md"
    destination = working.root / document_source_path(working.owners["works"]) / f"{A}.md"
    plan = mutations.plan_move(working.root, {**target(), "parent_id": WORKS})
    working.source(X, body="Changed since planning", publishable=False)
    with pytest.raises(mutations.ManagedDocumentRevisionConflict) as conflict:
        executor.execute_management_mutation_plan(working.root, plan, dry_run=False)
    assert conflict.value.payload["target"] == target(X)
    assert conflict.value.payload["operation"] == "move"
    assert original.exists() and not destination.exists() and working.calls == []

    def fail(*args, **kwargs):
        raise RuntimeError("fixture rebuild failure")

    monkeypatch.setattr(executor.write_rebuild, "rebuild_sub_scope_outputs", fail)
    status, response = service.docs_management_post_response(working.root, service.routes.MOVE_PATH, {**target(), "parent_id": WORKS})
    assert status == 500 and response["ok"] is False and response["committed"] is True
    assert "fixture rebuild failure" in response["error"]
    assert not original.exists() and destination.exists()


def test_collision_unsupported_metadata_and_readonly_stage_fail_before_write(working):
    source = working.root / document_source_path(working.config) / f"{A}.md"
    before = source.read_bytes()
    destination = working.source(A, "works")
    with pytest.raises(ValueError, match="already contains"):
        mutations.plan_move(working.root, {**target(), "parent_id": WORKS})
    destination.unlink()
    working.source(A, publishable=False)
    with pytest.raises(ValueError, match="ordinary Analysis Working"):
        mutations.plan_move(working.root, {**target(), "parent_id": WORKS})
    source.write_bytes(before)
    with pytest.raises(ValueError, match="Pre-publish document authoring"):
        service.docs_management_post_response(working.root, service.routes.MOVE_PATH, {**target(), "stage": "pre-publish", "parent_id": ""})
    assert source.read_bytes() == before and not destination.exists()


def test_media_collision_is_rejected_and_remote_media_keeps_its_identity(working):
    original_media = working.config.media.types["svg"]
    destination_media = working.owners["works"].media.types["svg"]
    asset = resolve_location_path(working.root, original_media.source_location) / "diagram.svg"
    destination = resolve_location_path(working.root, destination_media.source_location) / "diagram.svg"
    asset.write_bytes(b"original")
    destination.write_bytes(b"different")
    remote = f"https://example.test{original_media.served_path_prefix}/missing.svg"
    source = working.source(A, body=f"[[media:{original_media.reference_prefix}/diagram.svg|caption]]\n![remote]({remote})\n")
    before = source.read_bytes()
    with pytest.raises(ValueError, match="different content"):
        mutations.plan_move(working.root, {**target(), "parent_id": WORKS})
    assert source.read_bytes() == before and destination.read_bytes() == b"different"
    destination.write_bytes(b"original")
    plan = mutations.plan_move(working.root, {**target(), "parent_id": WORKS})
    assert len(plan.media_copies) == 1
    assert remote in plan.source_writes[0].text
    assert f"{destination_media.reference_prefix}/diagram.svg|caption" in plan.source_writes[0].text


@pytest.mark.parametrize("body", [
    "[Remote](https://example.test/?a=1&#38;b=2)",
    "[Other scope](/docs/?scope=studio&#38;doc=old)",
    "    [Example](/docs/?scope=analysis&doc=old)\n",
    "`example\n/docs/?scope=analysis&doc=old`",
    "````\n```\n/docs/?scope=analysis&doc=old\n````\n",
    "<pre>\n/docs/?scope=analysis&doc=old\n</pre>\n",
])
def test_literal_and_unrelated_references_keep_exact_source(body):
    from docs_document_placement_references import _rewrite_active_text

    def rewrite(url):
        return url.replace("doc=old", "doc=new") if "scope=analysis" in url else url

    assert _rewrite_active_text(body, rewrite) == body


@pytest.mark.parametrize("reference,filename", [("relative", "diagram.svg"), ("relative", "diagram name.svg"), ("logical", "diagram.svg")])
def test_diagram_relocation_preserves_editable_source_for_each_reference_form(working, reference, filename):
    media = working.config.media.types["svg"]
    svg = resolve_location_path(working.root, media.source_location) / filename
    mermaid = resolve_location_path(working.root, working.config.media.build_sources["mermaid"].location) / Path(filename).with_suffix(".mmd")
    svg.write_bytes(b"diagram svg")
    mermaid.write_text("flowchart LR\nA --> B\n")
    path = f"{media.reference_prefix}/{quote(filename)}" if reference == "logical" else f"../media/svg/{quote(filename)}"
    working.source(A, body=f"[Diagram]({path})")
    plan = mutations.plan_move(working.root, {**target(), "parent_id": WORKS})
    assert {copy.source for copy in plan.media_copies} == {svg, mermaid}
    assert quote(filename) in plan.source_writes[0].text
    for copy in plan.media_copies:
        assert "/sub-scopes/works/" in copy.destination.as_posix()
        assert copy.content == copy.source.read_bytes()


def test_metadata_move_response_uses_destination_fields_without_assigning_subjects(working):
    plan = mutations.plan_update_metadata(working.root, {**target(P), "title": "Parent", "parent_id": WORKS})
    record = plan.response["record"]
    assert "parent_id" not in record and "publishable" not in record
    assert set(record["customisation"].values()) == {""}
    working.source(A, "works", work_id="00523")
    (working.root / document_source_path(working.config) / f"{A}.md").unlink()
    metadata = managed_document_metadata(working.root, target(collection="works"))
    plan = mutations.plan_update_metadata(working.root, {
        **target(collection="works"), "title": A, "parent_id": "", "source_revision": metadata["source_revision"],
    })
    assert plan.response["record"]["publishable"] is True
    assert "customisation" not in plan.response["record"]
    assert plan.response["record"]["parent_id"] == ""


def test_collection_change_does_not_rebase_unowned_relative_web_links(working):
    body = f"[Viewer](./?scope=analysis&doc={P})\n\n[Page](../about/?name=two%20words#intro)\n"
    working.source(A, body=body)
    plan = mutations.plan_move(working.root, {**target(), "parent_id": WORKS})
    assert mutations.source_model.parse_source_text(plan.source_writes[0].text)[1] == body
    assert not plan.media_copies
