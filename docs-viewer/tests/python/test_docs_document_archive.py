"""Archive service boundaries: fixed destination, subtree identity and safe apply."""

from __future__ import annotations

import json

import pytest

import docs_document_archive as archive
import docs_document_archive_apply as archive_apply
import docs_management_service as service
import docs_source_model as source
from docs_scope_config import load_docs_scope_stage, document_source_path, generated_documents_path, resolve_location_path
from repo_factory import docs_scope_record, docs_sub_scope_record, write_docs_scope_config, write_json

ROOT = "d-20260914-170000-000001"
CHILD = "d-20260914-170000-000002"
GRAND = "d-20260914-170000-000003"
OUTSIDE = "d-20260914-170000-000004"


def owner(repo, scope):
    return load_docs_scope_stage(repo, scope, "working")


def documents(repo, scope):
    return repo / document_source_path(owner(repo, scope))


def put(repo, doc_id, parent="", body="# Document\n", scope="studio"):
    path = documents(repo, scope) / f"{doc_id}.md"
    path.write_text(source.format_source({
        "doc_id": doc_id, "title": doc_id, "parent_id": parent, "draft": True,
        "added_date": "2026-09-14 17:00:00",
    }, body))
    return path


@pytest.fixture
def repo(tmp_path):
    write_docs_scope_config(tmp_path, [docs_scope_record(name) for name in ("studio", "notes")])
    for scope in ("studio", "notes"):
        config = owner(tmp_path, scope)
        documents(tmp_path, scope).mkdir(parents=True)
        write_json(documents(tmp_path, scope) / "unpublishable.json", [])
        for media in config.media.types.values():
            for location in (media.source_location, media.generated_location):
                resolve_location_path(tmp_path, location).mkdir(parents=True, exist_ok=True)
    put(tmp_path, ROOT)
    put(tmp_path, CHILD, ROOT)
    put(tmp_path, GRAND, CHILD)
    put(tmp_path, OUTSIDE)
    return tmp_path


def request(ids=None):
    return {"scope": "studio", "stage": "working", "doc_ids": ids or [ROOT]}


def confirmed(plan):
    return {"scope": "studio", "stage": "working", "receipt": plan.receipt(), "confirm": True}


def writer(calls, fail_scope=""):
    def write(_repo, scope, paths, operation, **kwargs):
        operation()
        calls.append((scope, kwargs["stage"], tuple(kwargs["docs_doc_ids"])))
        if scope == fail_scope:
            raise RuntimeError("Rebuild failed")
        return {"ok": True}
    return write


def test_preview_deduplicates_descendants_and_has_only_count_and_receipt(repo):
    plan = archive.plan_archive(repo, request([ROOT, CHILD, ROOT]))
    assert {item.original.doc_id for item in plan.documents} == {ROOT, CHILD, GRAND}
    assert plan.preview() == {"ok": True, "document_count": 3, "receipt": plan.receipt()}
    assert not list(documents(repo, "notes").glob("*.md"))
    assert len(list(documents(repo, "studio").glob("*.md"))) == 4


@pytest.mark.parametrize("change", [
    {"scope": "notes"}, {"stage": "pre-publish"}, {"stage": "published"},
    {"sub_scope": "works"}, {"target_scope": "studio"}, {"include_descendants": False},
    {"doc_ids": []},
])
def test_archive_rejects_other_operations(repo, change):
    with pytest.raises(ValueError):
        archive.plan_archive(repo, {**request(), **change})


def test_apply_preserves_identity_hierarchy_metadata_and_media(repo):
    image = resolve_location_path(repo, owner(repo, "studio").media.types["img"].source_location) / "one.png"
    image.write_bytes(b"image")
    put(repo, ROOT, body=f"# Parent\n\n[Child](/docs/?scope=studio&stage=working&doc={CHILD})\n"
        f"[Prepared](/docs/?scope=studio&stage=pre-publish&doc={CHILD})\n"
        f"[Outside]({OUTSIDE}.md)\n\n[[media:docs/studio/img/one.png]]\n")
    plan = archive.plan_archive(repo, request())
    calls = []
    result = archive_apply.apply_archive(repo, confirmed(plan), perform_write=writer(calls))
    assert result["archived_count"] == 3
    assert "scope=notes" in result["viewer_url"] and "stage=working" in result["viewer_url"]
    assert [scope for scope, _, _ in calls] == ["notes", "studio"]
    assert all(stage == "working" for _, stage, _ in calls)
    for doc_id, parent in ((ROOT, ""), (CHILD, ROOT), (GRAND, CHILD)):
        assert not (documents(repo, "studio") / f"{doc_id}.md").exists()
        metadata, _ = source.parse_source_text((documents(repo, "notes") / f"{doc_id}.md").read_text())
        assert metadata["doc_id"] == doc_id and metadata["parent_id"] == parent
        assert metadata["draft"] is True and metadata["added_date"] == "2026-09-14 17:00:00"
    body = (documents(repo, "notes") / f"{ROOT}.md").read_text()
    assert f"scope=notes&stage=working&doc={CHILD}" in body
    assert f"scope=studio&stage=pre-publish&doc={CHILD}" in body
    assert f"scope=studio&doc={OUTSIDE}&stage=working" in body
    assert "docs/notes/img/one.png" in body
    for location in (owner(repo, "notes").media.types["img"].source_location, owner(repo, "notes").media.types["img"].generated_location):
        assert (resolve_location_path(repo, location) / "one.png").read_bytes() == b"image"
    assert image.exists()  # Shared source assets remain available.
    assert (documents(repo, "studio") / f"{OUTSIDE}.md").exists()


@pytest.mark.parametrize("mutation", ["source", "descendant", "destination", "config"])
def test_apply_rejects_changed_preview_before_writes(repo, mutation):
    plan = archive.plan_archive(repo, request())
    if mutation == "source":
        put(repo, CHILD, ROOT, body="# Changed\n")
    elif mutation == "descendant":
        put(repo, OUTSIDE, GRAND)
    elif mutation == "destination":
        put(repo, CHILD, scope="notes")
    else:
        path = repo / "docs-viewer/config/scopes/docs_scopes.json"
        config = json.loads(path.read_text())
        config["scopes"][0]["stages"]["working"]["default_doc_id"] = ROOT
        write_json(path, config)
    calls = []
    with pytest.raises(ValueError):
        archive_apply.apply_archive(repo, confirmed(plan), perform_write=writer(calls))
    assert calls == []
    assert (documents(repo, "studio") / f"{ROOT}.md").exists()


def test_target_rebuild_failure_keeps_source_and_reports_actual_writes(repo):
    plan = archive.plan_archive(repo, request())
    with pytest.raises(archive_apply.ArchiveApplyError) as error:
        archive_apply.apply_archive(repo, confirmed(plan), perform_write=writer([], fail_scope="notes"))
    assert error.value.result["phase"] == "notes"
    assert set(error.value.result["written_doc_ids"]) == {ROOT, CHILD, GRAND}
    assert error.value.result["removed_doc_ids"] == []
    assert all((documents(repo, "studio") / f"{doc_id}.md").exists() for doc_id in (ROOT, CHILD, GRAND))


@pytest.mark.parametrize("mutation", ["source", "destination", "generated", "symlink"])
def test_media_changes_or_unsafe_destination_prevent_archive_writes(repo, mutation):
    source_image = resolve_location_path(repo, owner(repo, "studio").media.types["img"].source_location) / "one.png"
    source_image.write_bytes(b"original")
    put(repo, ROOT, body="[[media:docs/studio/img/one.png]]\n")
    plan = archive.plan_archive(repo, request())
    notes_media = owner(repo, "notes").media.types["img"]
    if mutation == "source":
        source_image.write_bytes(b"changed")
    elif mutation == "symlink":
        destination = resolve_location_path(repo, notes_media.source_location) / "one.png"
        destination.symlink_to(source_image)
    else:
        location = notes_media.generated_location if mutation == "generated" else notes_media.source_location
        (resolve_location_path(repo, location) / "one.png").write_bytes(b"conflict")
    calls = []
    with pytest.raises(ValueError):
        archive_apply.apply_archive(repo, confirmed(plan), perform_write=writer(calls))
    assert calls == []
    assert not list(documents(repo, "notes").glob("*.md"))


def test_subscope_report_host_is_rejected_with_its_parent_selection(repo):
    from build_docs_test_support import write_report_registry

    path = repo / "docs-viewer/config/scopes/docs_scopes.json"
    config = json.loads(path.read_text())
    config["scopes"][0]["stages"]["working"]["sub_scopes"] = [docs_sub_scope_record("studio", "concepts")]
    write_json(path, config)
    write_report_registry(repo)
    put(repo, CHILD, ROOT, body=":::report\nid: docs_subscope\nsub_scope: concepts\n:::\n")
    with pytest.raises(ValueError, match="Sub-scope report hosts"):
        archive.plan_archive(repo, request())


def test_archive_rebuilds_both_collections_and_clears_an_archived_default(repo, monkeypatch):
    from build_docs_test_support import write_site_tools_config, write_route_config, write_semantic_token_contract
    from docs_builder.pipeline import DocsDataBuilder
    import docs_write_rebuild as rebuild

    write_site_tools_config(repo)
    write_route_config(repo)
    write_semantic_token_contract(repo)
    path = repo / "docs-viewer/config/scopes/docs_scopes.json"
    config = json.loads(path.read_text())
    config["scopes"][0]["stages"]["working"]["default_doc_id"] = ROOT
    write_json(path, config)
    for scope in ("studio", "notes"):
        DocsDataBuilder(repo_root=repo, config=owner(repo, scope), skip_media_builds=True).run(write=True)
    calls = []

    def build(repo_root, scope, **options):
        assert repo_root == repo and options["stage"] == "working"
        assert options["include_search"] is False and options["skip_media_builds"] is True
        calls.append(scope)
        return DocsDataBuilder(
            repo_root=repo, config=owner(repo, scope), skip_media_builds=True,
            only_doc_ids=options["docs_doc_ids"],
            **{key: value for key, value in options.items() if key.startswith("links_")},
        ).run(write=True)

    monkeypatch.setattr(rebuild, "rebuild_scope_outputs", build)
    result = archive_apply.apply_archive(repo, confirmed(archive.plan_archive(repo, request())))
    assert result["ok"] is True and calls == ["notes", "studio"]
    assert owner(repo, "studio").default_doc_id == ""
    for scope, expected in (("studio", {OUTSIDE}), ("notes", {ROOT, CHILD, GRAND})):
        generated = repo / generated_documents_path(owner(repo, scope))
        assert {path.stem for path in (generated / "by-id").glob("*.json")} == expected


def test_routes_enforce_archive_target_and_confirmation(repo, monkeypatch):
    status, preview = service.docs_management_post_response(repo, "/docs/archive-preview", request())
    assert status == 200 and preview["document_count"] == 3
    plan = archive.plan_archive(repo, request())
    with pytest.raises(ValueError, match="confirmed"):
        archive_apply.apply_archive(repo, {**confirmed(plan), "confirm": False})
    for path in ("/docs/document-transfer-preview", "/docs/document-transfer-apply", "/docs/copy-subtree-preview"):
        assert path not in service.routes.POST_PATHS
    assert archive.archive_capability(repo, owner(repo, "studio"))["available"] is True
    assert archive.archive_capability(repo, owner(repo, "notes"))["available"] is False
    calls = []
    monkeypatch.setattr("docs_write_rebuild.perform_source_write_and_rebuild", writer(calls))
    status, result = service.docs_management_post_response(repo, "/docs/archive-apply", confirmed(plan))
    assert status == 200 and result["archived_count"] == 3
