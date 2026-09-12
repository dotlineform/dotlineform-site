"""Exact workflow stage storage and authoring boundaries."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import json
import subprocess
import sys

import pytest

from docs_management_test_support import docs_scope_config as scopes
from repo_factory import docs_scope_record, docs_sub_scope_record, write_json
from docs_management_document_target import managed_document_metadata, resolve_managed_document_target
from docs_management_mutations import plan_assign_field_group, plan_create, plan_delete_apply, plan_move
from docs_generated_reads import read_generated_doc_payload
from build_docs_test_support import prepare_repo, run_cli


DOC_ID = "d-20260906-170000-a1b2c3"
REPORT_ID = "d-20260906-170000-d4e5f6"


@pytest.fixture
def stage_repo(tmp_path: Path) -> Path:
    prepare_repo(tmp_path)
    analysis = docs_scope_record("analysis", scope_type="public", viewer_base_url="/analysis/", include_scope_param=False, media_types=("img", "svg", "files", "html"))
    analysis["stages"] = {
        stage: {
            "media": deepcopy(analysis["media"]),
            "sub_scopes": [docs_sub_scope_record("analysis", collection, scope_type="public" if stage == "pre-publish" else "local")],
        }
        for stage, collection in (("working", "works"), ("pre-publish", "works"))
    }
    write_json(tmp_path / scopes.CONFIG_REL_PATH, {
        "schema_version": scopes.SCHEMA_VERSION,
        "scopes": [analysis, docs_scope_record("studio")],
    })
    for stage, collection in (("working", "works"), ("pre-publish", "works")):
        config = scopes.load_docs_scope_stage(tmp_path, "analysis", stage)
        for owner in (config, config.sub_scopes[0]):
            root = tmp_path / scopes.document_source_path(owner)
            root.mkdir(parents=True)
            (root / f"{DOC_ID}.md").write_text(
                f"---\ndoc_id: {DOC_ID}\ntitle: {stage}\n---\n# {stage}\n",
                encoding="utf-8",
            )
        output = tmp_path / scopes.generated_documents_path(config)
        (tmp_path / scopes.document_source_path(config) / f"{REPORT_ID}.md").write_text(
            f"---\ndoc_id: {REPORT_ID}\ntitle: Works\n---\n:::report\nid: docs_subscope\naccess: {'local' if stage == 'working' else 'public'}\nsub_scope: works\n:::\n"
        )
        write_json(output / "index-tree.json", {"docs": [{"doc_id": DOC_ID, "content_url": "/docs/doc"}]})
        write_json(output / "by-id" / f"{DOC_ID}.json", {"doc_id": DOC_ID, "title": stage})
    return tmp_path


@pytest.mark.parametrize("field,key", [("work_id", "00293")])
def test_subject_assignment_preserves_exact_working_stage(stage_repo: Path, field: str, key: str) -> None:
    config_path = stage_repo / scopes.CONFIG_REL_PATH
    config = json.loads(config_path.read_text())
    for stage in ("working", "pre-publish"):
        config["scopes"][0]["stages"][stage]["sub_scopes"][0]["sub_scope_customisation"] = {
            "id": "working_works" if stage == "working" else "pre_publish_works", "settings": {},
        }
    write_json(config_path, config)
    target = {"scope": "analysis", "stage": "working", "sub_scope": "works", "doc_id": DOC_ID}
    working = resolve_managed_document_target(stage_repo, target).document.path
    pre_publish = resolve_managed_document_target(stage_repo, {**target, "stage": "pre-publish"}).document.path
    working_before, pre_publish_before = working.read_bytes(), pre_publish.read_bytes()
    metadata = managed_document_metadata(stage_repo, target)
    assert metadata["stage"] == "working"
    assert metadata["record"]["authoring_subject"]["state"] == "none"
    request = {
        **target, "source_revision": metadata["source_revision"],
        "field_group": "authoring_subject", "confirm": True,
        "fields": {"folder_path": "", "work_id": "", "series_id": "", "detail_uid": "", field: key},
    }
    plan = plan_assign_field_group(stage_repo, request)
    assert plan.stage == "working"
    assert plan.response["target"] == target
    assert len(plan.source_writes) == 1
    assert plan.source_writes[0].path == working
    assert working.read_bytes() == working_before
    working.write_text(plan.source_writes[0].text, encoding="utf-8")
    loaded = managed_document_metadata(stage_repo, target)
    assert loaded["record"]["authoring_subject"]["key"] == key
    unchanged_request = {**request, "source_revision": loaded["source_revision"]}
    unchanged = plan_assign_field_group(stage_repo, unchanged_request)
    assert unchanged.stage == "working"
    assert unchanged.response["target"] == target
    assert not unchanged.source_writes
    for stage, message in ((None, "requires stage"), ("pre-publish", "Pre-publish document authoring is unavailable")):
        rejected = {**unchanged_request, "stage": stage}
        if stage is None:
            del rejected["stage"]
        with pytest.raises(ValueError, match=message):
            plan_assign_field_group(stage_repo, rejected)
    assert pre_publish.read_bytes() == pre_publish_before


def test_report_host_reparenting_keeps_stage_and_child_destinations(stage_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import docs_management_mutation_service as service
    from docs_builder.sub_scope import SubScopeDocsBuilder

    config = scopes.load_docs_scope_stage(stage_repo, "analysis", "working")
    root = stage_repo / scopes.document_source_path(config)
    host = root / f"{DOC_ID}.md"
    (root / f"{REPORT_ID}.md").unlink()
    host.write_text(host.read_text() + "\n:::report\nid: docs_subscope\naccess: local\nsub_scope: works\n:::\n")
    parent_id = "d-20260907-215200-aaaaaa"
    child_id = "d-20260907-215200-bbbbbb"
    (root / f"{parent_id}.md").write_text(f"---\ndoc_id: {parent_id}\ntitle: Parent\n---\n# Parent\n")
    (root / f"{child_id}.md").write_text(f"---\ndoc_id: {child_id}\ntitle: Child\nparent_id: {DOC_ID}\n---\n# Child\n")
    child_source = stage_repo / scopes.document_source_path(config.sub_scopes[0]) / f"{DOC_ID}.md"
    pre_publish = scopes.load_docs_scope_stage(stage_repo, "analysis", "pre-publish")
    other_host = stage_repo / scopes.document_source_path(pre_publish) / f"{DOC_ID}.md"
    before = {path: path.read_bytes() for path in (child_source, other_host, stage_repo / scopes.CONFIG_REL_PATH)}
    original_body = service.source_model.parse_source(host)[1]
    child_href = SubScopeDocsBuilder(repo_root=stage_repo, config=config, sub_scope=config.sub_scopes[0]).viewer_url_for(DOC_ID)
    target = {"scope": "analysis", "stage": "working", "doc_id": DOC_ID}
    request = {**target, "parent_id": parent_id}
    plan = plan_move(stage_repo, request)
    assert plan.stage == "working" and plan.response["target"] == target
    assert [write.path for write in plan.source_writes] == [host]
    calls = []

    def rebuild(repo_root, scope, changed_paths, write_operation, **options):
        calls.append((repo_root, scope, changed_paths, options))
        write_operation()
        return {"ok": True}

    monkeypatch.setattr(service.write_rebuild, "perform_source_write_and_rebuild", rebuild)
    response = service.handle_move(stage_repo, request, dry_run=False)
    assert response["target"] == target and response["stage"] == "working"
    assert calls == [(stage_repo, "analysis", [host], {
        "stage": "working", "docs_doc_ids": [DOC_ID], "suppression_reason": "docs-move",
    })]
    front_matter, body = service.source_model.parse_source(host)
    assert front_matter["doc_id"] == DOC_ID and front_matter["parent_id"] == parent_id
    assert body == original_body
    assert SubScopeDocsBuilder(repo_root=stage_repo, config=config, sub_scope=config.sub_scopes[0]).viewer_url_for(DOC_ID) == child_href
    unchanged = plan_move(stage_repo, request)
    assert unchanged.stage == "working" and unchanged.response["target"] == target
    assert not unchanged.source_writes

    for changes, message in (
        ({"stage": None}, "stage must be a non-blank string"),
        ({"stage": "pre-publish"}, "Pre-publish document authoring is unavailable"),
        ({"parent_id": "missing"}, "Unknown parent_id"),
        ({"parent_id": DOC_ID}, "cannot be the current doc"),
        ({"parent_id": child_id}, "cannot be a child or descendant"),
    ):
        with pytest.raises(ValueError, match=message):
            plan_move(stage_repo, {**request, **changes})
    assert all(path.read_bytes() == content for path, content in before.items())


def test_scope_rebuild_dispatch_preserves_working_and_rejects_other_stages(stage_repo: Path, monkeypatch) -> None:
    import docs_management_service as service

    calls = []
    monkeypatch.setattr(service.write_rebuild, "rebuild_scope_outputs", lambda *args, **kwargs: calls.append((args, kwargs)) or {"ok": True})
    status, payload = service.docs_management_post_response(stage_repo, service.routes.REBUILD_PATH, {
        "scope": "analysis", "stage": "working",
    })
    assert status == 200 and payload["ok"] is True
    assert calls == [((stage_repo, "analysis"), {"include_search": True, "stage": "working"})]
    for stage, message in ((None, "requires stage"), ("pre-publish", "Pre-publish document authoring is unavailable")):
        with pytest.raises(ValueError, match=message):
            service.docs_management_post_response(stage_repo, service.routes.REBUILD_PATH, {"scope": "analysis", "stage": stage})
    assert len(calls) == 1


def test_service_can_import_with_unselected_workflow_parent(stage_repo: Path) -> None:
    services = Path(scopes.__file__).parent
    result = subprocess.run(
        [sys.executable, "-c", "\n".join((
            "import sys",
            "from pathlib import Path",
            f"sys.path.insert(0, {str(services)!r})",
            "import docs_scope_config as scopes",
            f"scopes.DOCS_SCOPE_CONFIGS = scopes.load_docs_scope_configs(Path({str(stage_repo)!r}))",
            "import docs_viewer_service",
        ))],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_sub_scope_creation_binds_config_sources_and_rebuilds_to_working(stage_repo: Path) -> None:
    import docs_sub_scope_lifecycle as lifecycle

    config_path = stage_repo / scopes.CONFIG_REL_PATH
    before = json.loads(config_path.read_text())
    request = {"parent_scope": "analysis", "stage": "working", "sub_scope": "moments", "title": "Moments"}
    preview = lifecycle.plan_create_sub_scope_preview(stage_repo, request)
    host_id = preview["planned_report_host_identity"]["doc_id"]
    assert preview["collection_target"] == {"scope": "analysis", "stage": "working", "sub_scope": "moments"}
    assert preview["report_host_target"] == {"scope": "analysis", "stage": "working", "doc_id": host_id}
    assert "stage=working" in preview["urls"]["management"]
    assert preview["publish_files"] == []
    assert "parent_search" not in preview["rebuild_plan"]
    assert json.loads(config_path.read_text()) == before
    calls = []

    def rebuild(*args, **kwargs):
        calls.append((args, kwargs))
        return {"ok": True}

    result = lifecycle.apply_create_sub_scope(
        stage_repo,
        {**request, "confirm": True, "planned_report_host_identity": preview["planned_report_host_identity"]},
        dry_run=False,
        rebuild_sub_scope_outputs=rebuild,
        rebuild_scope_outputs=rebuild,
    )
    assert result["committed"] is True
    after = json.loads(config_path.read_text())
    new_analysis = after["scopes"][0]
    added = new_analysis["stages"]["working"]["sub_scopes"].pop()
    assert added["sub_scope"] == "moments"
    assert added["public_projection"] is None
    assert after == before
    working = scopes.load_docs_scope_stage(stage_repo, "analysis", "working")
    source = stage_repo / scopes.document_source_path(working)
    assert (source / f"{host_id}.md").is_file()
    collection = next(item for item in working.sub_scopes if item.sub_scope == "moments")
    assert (stage_repo / scopes.document_source_path(collection)).is_dir()
    assert calls[0] == ((stage_repo, "analysis", "moments"), {"stage": "working"})
    assert calls[1][1] == {"include_search": False, "docs_doc_ids": [host_id], "stage": "working"}


@pytest.mark.parametrize("stage", [None, "pre-publish"])
def test_sub_scope_creation_rejects_missing_or_readonly_stage(stage_repo: Path, stage: str | None) -> None:
    import docs_sub_scope_lifecycle as lifecycle

    config_path = stage_repo / scopes.CONFIG_REL_PATH
    before = config_path.read_bytes()
    request = {"parent_scope": "analysis", "sub_scope": "moments", "title": "Moments"}
    if stage:
        request["stage"] = stage
    message = "requires stage" if stage is None else "Pre-publish document authoring is unavailable"
    with pytest.raises(ValueError, match=message):
        lifecycle.plan_create_sub_scope_preview(stage_repo, request)
    assert config_path.read_bytes() == before


def test_stage_storage_retains_scope_owned_snapshot_and_media_identity(stage_repo: Path) -> None:
    working = scopes.load_docs_scope_stage(stage_repo, "analysis", "working")
    pre_publish = scopes.load_docs_scope_stage(stage_repo, "analysis", "pre-publish")
    child = working.sub_scopes[0]
    assert child.media.source_location.path == child.source.location.path / "media"
    assert child.media.generated_location.path == scopes.generated_documents_path(child).parent / "media"
    assert child.media.published_location.path == Path("docs-viewer/scopes/analysis/published/sub-scopes/works/media")
    assert child.media.types["img"].reference_prefix.as_posix() == "docs/analysis/sub-scopes/works/img"
    assert child.media.types["img"].served_path_prefix == "/docs/media/analysis/working/sub-scopes/works/img"
    assert working.scope_id == pre_publish.scope_id == "analysis"
    assert working.published == pre_publish.published
    assert scopes.published_documents_path(working) == Path("docs-viewer/scopes/analysis/published/documents")
    assert scopes.document_source_path(working.sub_scopes[0]) == Path(
        "docs-viewer/scopes/analysis/working/source/sub-scopes/works/documents"
    )
    assert working.media.types["img"].reference_prefix == pre_publish.media.types["img"].reference_prefix == Path("docs/analysis/img")
    assert working.media.types["img"].served_path_prefix == "/docs/media/analysis/working/img"
    assert pre_publish.media.types["img"].served_path_prefix == "/docs/media/analysis/pre-publish/img"
    assert scopes.document_source_path(scopes.load_docs_scope_stage(stage_repo, "studio")) == Path(
        "docs-viewer/scopes/studio/source/documents"
    )


def test_child_media_insertion_replace_build_and_read_stay_in_collection(stage_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import docs_staged_media_service as intake
    from docs_document_packages.workspace import configured_workspace_paths
    from docs_media_storage import local_media_path_from_route
    from docs_builder.sub_scope import SubScopeDocsBuilder

    projects = stage_repo / "projects"
    (projects / "docs-viewer").mkdir(parents=True)
    (projects / "data-sharing").mkdir()
    monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(projects))
    monkeypatch.setenv("DOTLINEFORM_DOCS_BASE_DIR", str(projects / "docs-viewer"))
    staging = configured_workspace_paths(stage_repo).import_staging
    staging.mkdir(parents=True, exist_ok=True)
    input_path = staging / "same.pdf"
    input_path.write_bytes(b"child version one")
    config = scopes.load_docs_scope_stage(stage_repo, "analysis", "working")
    child = config.sub_scopes[0]
    parent_file = stage_repo / config.media.types["files"].source_location.path / "same.pdf"
    parent_file.parent.mkdir(parents=True, exist_ok=True)
    parent_file.write_bytes(b"parent content")
    request = {"scope": "analysis", "stage": "working", "sub_scope": "works", "media_kind": "file", "staged_filename": "same.pdf"}
    first = intake.apply_staged_media(stage_repo, request)
    assert first["media_token"] == "[[media:docs/analysis/sub-scopes/works/files/same.pdf]]"
    child_file = stage_repo / child.media.types["files"].source_location.path / "same.pdf"
    assert child_file.read_bytes() == b"child version one"
    route = "/docs/media/analysis/working/sub-scopes/works/files/same.pdf"
    generated, media_type = local_media_path_from_route(stage_repo, route)
    assert media_type == "files" and generated.read_bytes() == b"child version one"
    input_path.write_bytes(b"child version two")
    assert intake.preview_staged_media(stage_repo, request)["requires_replace_confirmation"] is True
    with pytest.raises(ValueError, match="confirm replacement"):
        intake.apply_staged_media(stage_repo, request)
    assert child_file.read_bytes() == b"child version one"
    intake.apply_staged_media(stage_repo, {**request, "confirm_replace": True})
    assert child_file.read_bytes() == b"child version two"
    assert parent_file.read_bytes() == b"parent content"

    source = stage_repo / scopes.document_source_path(child) / f"{DOC_ID}.md"
    source.write_text(source.read_text() + "\n[File](" + first["media_token"] + ")\n")
    built = SubScopeDocsBuilder(repo_root=stage_repo, config=config, sub_scope=child).run(write=True)
    route = "/docs/media/analysis/working/sub-scopes/works/files/same.pdf"
    assert route in built["item_payloads"][DOC_ID]["content_html"]
    generated, media_type = local_media_path_from_route(stage_repo, route)
    assert media_type == "files" and generated.read_bytes() == b"child version two"
    assert not (stage_repo / child.media.types["files"].published_location.path / "same.pdf").exists()
    for invalid in ({"stage": "pre-publish"}, {"stage": ""}, {"sub_scope": "missing"}):
        with pytest.raises(ValueError):
            intake.apply_staged_media(stage_repo, {**request, **invalid})


@pytest.mark.parametrize("stage", [None, "published", "", "WORKING"])
def test_workflow_scope_requires_exact_stage(stage_repo: Path, stage: str | None) -> None:
    with pytest.raises(ValueError, match="requires stage"):
        scopes.load_docs_scope_stage(stage_repo, "analysis", stage)


def test_child_import_binds_source_and_media_to_the_selected_collection(stage_repo: Path) -> None:
    from docs_import_document import ImportDocumentMediaContext, apply_import_document, plan_import_document
    from docs_import_media import build_media_plan
    from docs_import_content import ImportContent, CONTENT_FORMAT_MARKDOWN, CONTENT_INTENT_REPLACE
    from docs_management_document_target import resolve_managed_document_collection

    collection = resolve_managed_document_collection(stage_repo, scope="analysis", stage="working", sub_scope="works")
    staged = stage_repo / "staging/attachment.pdf"
    staged.parent.mkdir()
    staged.write_bytes(b"imported child attachment")
    media = build_media_plan("analysis", "files", staged, "Attachment", media_config=collection.parent_config.media.types["files"])
    preview = {"scope": "analysis", "markdown_preview": f"[Attachment]({media['media_token']})", "media_plan": media}
    record = ImportContent(
        source_kind="staged-source", source_identity=staged.name, record_identity=staged.name,
        doc_id="imported", title="Imported", content_intent=CONTENT_INTENT_REPLACE,
        content_format=CONTENT_FORMAT_MARKDOWN, content=preview["markdown_preview"], parent_id="",
    )
    plan = plan_import_document(stage_repo, "analysis", record, operation="create", docs=[], import_preview=preview, collection=collection)
    apply_import_document(stage_repo, plan, media_context=ImportDocumentMediaContext(
        staging_root=staged.parent, workspace_root=stage_repo, source_path=staged,
    ))
    assert "docs/analysis/sub-scopes/works/files/attachment.pdf" in plan.target_path.read_text()
    for location in (collection.document_config.media.types["files"].source_location, collection.document_config.media.types["files"].generated_location):
        assert (stage_repo / location.path / staged.name).read_bytes() == staged.read_bytes()
    assert not (stage_repo / collection.parent_config.media.types["files"].source_location.path / staged.name).exists()


@pytest.mark.parametrize("stage", ["working", "pre-publish"])
def test_media_tokens_resolve_shared_identity_in_exact_stage(stage_repo: Path, stage: str) -> None:
    from docs_builder.pipeline import DocsDataBuilder

    config = scopes.load_docs_scope_stage(stage_repo, "analysis", stage)
    builder = DocsDataBuilder(repo_root=stage_repo, config=config, skip_media_builds=True)
    for media_type in ("img", "svg", "files", "html"):
        token = f"[[media:docs/analysis/{media_type}/same-file]]"
        assert builder.resolve_media_tokens(token) == f"/docs/media/analysis/{stage}/{media_type}/same-file"

    html_root = stage_repo / config.media.types["html"].source_location.path
    html_root.mkdir(parents=True)
    (html_root / "same.html").write_text(f"<p>{stage}</p>", encoding="utf-8")
    embedded = builder.resolve_html_media_tokens("[[html-media:docs/analysis/html/same.html]]")
    assert f'src="/docs/media/analysis/{stage}/html/same.html"' in embedded

    # A stale or cross-scope Docs token must not become a generic remote URL.
    builder.site_config["media"] = {"base": "https://media.example.test"}
    for namespace in ("dotlineform", "studio"):
        with pytest.raises(RuntimeError, match=f"no configured role in scope analysis stage {stage}"):
            builder.resolve_media_tokens(f"[[media:docs/{namespace}/img/same-file]]")
    assert builder.resolve_media_url("https://example.test/photo.jpg") == "https://example.test/photo.jpg"


def test_same_document_id_is_read_only_from_requested_stage(stage_repo: Path) -> None:
    for stage in ("working", "pre-publish"):
        target = {"scope": "analysis", "stage": stage, "doc_id": DOC_ID}
        resolved = resolve_managed_document_target(stage_repo, target)
        assert resolved.request_target() == target
        assert resolved.document.title == stage
        assert read_generated_doc_payload(stage_repo, "analysis", DOC_ID, stage)["title"] == stage
    with pytest.raises(ValueError, match="unknown sub_scope"):
        resolve_managed_document_target(stage_repo, {
            "scope": "analysis", "stage": "pre-publish", "sub_scope": "projects", "doc_id": DOC_ID,
        })


@pytest.mark.parametrize("sub_scope", [None])
def test_set_publishable_updates_only_selected_working_collection(stage_repo: Path, monkeypatch: pytest.MonkeyPatch, sub_scope: str | None) -> None:
    import docs_management_publishable as publishable
    import docs_management_service as service
    import docs_management_routes as routes

    collection = {"scope": "analysis", "stage": "working"}
    if sub_scope:
        collection["sub_scope"] = sub_scope
    target = {**collection, "doc_id": DOC_ID}
    source = resolve_managed_document_target(stage_repo, target).document.path
    protected = [resolve_managed_document_target(stage_repo, {
        "scope": "analysis", "stage": stage, "doc_id": DOC_ID,
        **({"sub_scope": child} if child else {}),
    }).document.path for stage in ("working", "pre-publish") for child in (None, "works")]
    before = {path: path.read_bytes() for path in protected if path != source}
    rebuilds = []

    def rebuild(_root, scope, *args, **options):
        rebuilds.append((scope, args, options["stage"]))
        return {"ok": True}

    monkeypatch.setattr(publishable.write_rebuild, "rebuild_scope_outputs", rebuild)
    monkeypatch.setattr(publishable.write_rebuild, "rebuild_sub_scope_outputs", rebuild)
    monkeypatch.setattr(publishable, "log_event", lambda *_args: None)
    capabilities = service.capabilities_payload(stage_repo)["capabilities"]["scopes"]["analysis"]["stages"]
    assert capabilities["working"]["publishable"] is True
    assert capabilities["pre-publish"]["publishable"] is False
    assert capabilities["working"]["publishing"]["apply"] is False
    request = {**collection, "doc_ids": [DOC_ID], "publishable": False, "confirm": True}
    for include in (False, True):
        status, result = service.docs_management_post_response(stage_repo, routes.SET_PUBLISHABLE_PATH, {**request, "publishable": include})
        assert status == 200 and result["target"] == collection
        assert result["stage"] == "working" and result["updated_doc_ids"] == [DOC_ID]
        front_matter, _body = publishable.source_model.parse_source(source)
        assert ("publishable" not in front_matter) if include else front_matter["publishable"] is False
    assert rebuilds == [("analysis", ("works",) if sub_scope else (), "working")] * 2
    for stage in (None, "pre-publish"):
        rejected = {**request, "stage": stage}
        if stage is None:
            del rejected["stage"]
        for operation in (publishable.plan_set_publishable, lambda root, body: service.docs_management_post_response(root, routes.SET_PUBLISHABLE_PATH, body)):
            with pytest.raises(ValueError, match="requires stage|authoring is unavailable|must contain exactly|ordinary Analysis Working"):
                operation(stage_repo, rejected)
    assert all(path.read_bytes() == content for path, content in before.items())


def test_set_publishable_rollback_rebuilds_only_working(stage_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import docs_management_publishable as publishable

    target = {"scope": "analysis", "stage": "working", "doc_id": DOC_ID}
    source = resolve_managed_document_target(stage_repo, target).document.path
    other = resolve_managed_document_target(stage_repo, {**target, "stage": "pre-publish"}).document.path
    before = {path: path.read_bytes() for path in (source, other)}
    rebuilds = []

    def fail_then_recover(_root, scope, **options):
        rebuilds.append((scope, options["stage"]))
        if len(rebuilds) == 1:
            raise RuntimeError("rebuild failed")
        return {"ok": True}

    monkeypatch.setattr(publishable.write_rebuild, "rebuild_scope_outputs", fail_then_recover)
    with pytest.raises(publishable.PublishableSelectionApplyError) as error:
        publishable.set_publishable(stage_repo, {"scope": "analysis", "stage": "working", "doc_ids": [DOC_ID], "publishable": False, "confirm": True})
    assert error.value.payload["rollback"]["status"] == "completed"
    assert rebuilds == [("analysis", "working")] * 2
    assert all(path.read_bytes() == content for path, content in before.items())


@pytest.mark.parametrize("sub_scope", [None, "works"])
def test_working_projects_draft_without_public_projection(stage_repo: Path, sub_scope: str | None) -> None:
    import docs_source_model as source_model

    config = scopes.load_docs_scope_stage(stage_repo, "analysis", "working")
    collection = config.sub_scopes[0] if sub_scope else config
    assert collection.stage == "working" and collection.public_projection is None
    path = stage_repo / scopes.document_source_path(collection) / f"{DOC_ID}.md"
    path.write_text(f"---\ndoc_id: {DOC_ID}\ntitle: Private work\ndraft: true\n---\n# Private work\n")
    documents = source_model.load_document_collection_docs_for_config(stage_repo, config, collection)
    assert documents[0].front_matter["draft"] is True
    code, _stdout, stderr = run_cli(stage_repo, [
        "--scope", "analysis", "--stage", "working",
        *(["--sub-scope", sub_scope] if sub_scope else []),
        "--write", "--skip-browser-config", "--skip-media-builds",
    ])
    assert code == 0, stderr
    output = stage_repo / scopes.generated_documents_path(collection)
    index = "manage-manifest.json" if sub_scope else "index-tree.json"
    assert json.loads((output / index).read_text())["docs"][0]["draft"] is True
    assert json.loads((output / "by-id" / f"{DOC_ID}.json").read_text())["draft"] is True


@pytest.mark.parametrize("sub_scope", [None, "works"])
def test_pre_publish_create_rejected_before_source_changes(stage_repo: Path, sub_scope: str | None) -> None:
    request = {"scope": "analysis", "stage": "pre-publish", "title": "Forbidden"}
    if sub_scope:
        request["sub_scope"] = sub_scope
    with pytest.raises(ValueError, match="authoring is unavailable"):
        plan_create(stage_repo, request)


def test_working_create_and_delete_plan_keep_exact_owner(stage_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import docs_management_mutations as mutations

    def forbidden_cleanup(*args: object, **kwargs: object) -> None:
        pytest.fail("Working Delete must not plan public cleanup")

    monkeypatch.setattr(mutations.public_delete_cleanup, "plan_public_document_delete_cleanup", forbidden_cleanup)
    create = plan_create(stage_repo, {"scope": "analysis", "stage": "working", "title": "New"})
    assert create.stage == "working"
    assert create.response["target"]["stage"] == "working"
    delete = plan_delete_apply(stage_repo, {
        "scope": "analysis", "stage": "working", "doc_ids": [DOC_ID], "confirm": True,
    })
    assert delete.stage == "working"
    assert delete.public_delete_cleanup is None
    assert all("/working/source/" in str(item.path) for item in delete.source_deletes)


def test_stage_build_writes_exact_parent_and_report_payloads(stage_repo: Path) -> None:
    for stage, collection in (("working", "works"), ("pre-publish", "works")):
        config = scopes.load_docs_scope_stage(stage_repo, "analysis", stage)
        root = stage_repo / scopes.document_source_path(config)
        source = root / f"{DOC_ID}.md"
        (root / f"{REPORT_ID}.md").unlink()
        source.write_text(source.read_text() + f"\n:::report\nid: docs_subscope\naccess: public\nsub_scope: {collection}\n:::\n", encoding="utf-8")
        code, stdout, stderr = run_cli(stage_repo, ["--scope", "analysis", "--stage", stage, "--write", "--skip-media-builds"])
        assert code == 0, stdout + stderr
        output = stage_repo / scopes.generated_documents_path(config)
        index = json.loads((output / "index-tree.json").read_text())
        assert len(index["docs"]) == 1  # Child source is never absorbed by the ordinary tree.
        code, stdout, stderr = run_cli(stage_repo, ["--scope", "analysis", "--stage", stage, "--sub-scope", collection, "--write", "--skip-media-builds"])
        assert code == 0, stdout + stderr
        child_root = stage_repo / scopes.generated_documents_path(config.sub_scopes[0])
        manifest = json.loads((child_root / "manage-manifest.json").read_text())
        assert manifest["docs"][0]["doc_id"] == DOC_ID
        child = json.loads((child_root / "by-id" / f"{DOC_ID}.json").read_text())
        assert f"stage={stage}" in child["viewer_url"]
        assert f"subdoc={DOC_ID}" in child["viewer_url"]


@pytest.mark.parametrize("stage", ["working", "pre-publish"])
def test_rendered_links_preserve_explicit_stage_and_child_targets(stage_repo: Path, stage: str) -> None:
    from docs_builder.pipeline import DocsDataBuilder
    from markdown_renderer import render_markdown_to_html

    builder = DocsDataBuilder(
        repo_root=stage_repo,
        config=scopes.load_docs_scope_stage(stage_repo, "analysis", stage),
        skip_media_builds=True,
    )
    documents = builder.load_docs()
    for target_stage in ("working", "pre-publish"):
        for query in (
            f"doc={DOC_ID}&scope=analysis&stage={target_stage}",
            f"scope=analysis&stage={target_stage}&doc={DOC_ID}",
        ):
            href = f"/docs/?{query}&subdoc={DOC_ID}#detail"
            rendered = render_markdown_to_html(f"[Exact target]({href})")
            assert builder.rewrite_doc_links(
                rendered, current_doc=documents[0], docs=documents,
            ) == (rendered.replace("stage=working", "stage=pre-publish") if stage == "pre-publish" else rendered)


@pytest.mark.parametrize("delete_ancestor", [False, True])
def test_working_default_delete_updates_only_local_browser_config(
    stage_repo: Path, monkeypatch: pytest.MonkeyPatch, delete_ancestor: bool,
) -> None:
    from docs_builder.browser_config import write_browser_config
    import docs_management_service as service
    import docs_management_mutation_service as mutation_service
    import docs_write_rebuild as rebuild

    parent_id = "d-20260906-170001-b2c3d4"
    survivor_id = "d-20260906-170002-c3d4e5"
    config_path = stage_repo / scopes.CONFIG_REL_PATH
    raw = json.loads(config_path.read_text())
    raw["scopes"][0]["stages"]["working"]["default_doc_id"] = DOC_ID
    write_json(config_path, raw)
    configs = scopes.load_docs_scope_configs(stage_repo)
    working = scopes.select_scope_stage(configs["analysis"], "working")
    source = stage_repo / scopes.document_source_path(working)
    if delete_ancestor:
        (source / f"{parent_id}.md").write_text(f"---\ndoc_id: {parent_id}\ntitle: Parent\n---\n# Parent\n")
        (source / f"{DOC_ID}.md").write_text(f"---\ndoc_id: {DOC_ID}\ntitle: Default child\nparent_id: {parent_id}\n---\n# Default\n")
    (source / f"{survivor_id}.md").write_text(f"---\ndoc_id: {survivor_id}\ntitle: Retained\n---\n# Retained\n")
    browser_path = Path("docs-viewer/config/defaults/docs-viewer-config.json")
    write_browser_config(stage_repo, list(configs.values()), path=browser_path, label="Fixture local config")
    before_browser = json.loads((stage_repo / browser_path).read_text())
    protected_paths = [
        Path("docs-viewer/config/defaults/docs-viewer-public-config.json"),
        Path("site/docs-viewer/config/defaults/docs-viewer-public-config.json"),
        Path("docs-viewer/scopes/analysis/published/documents/accepted.json"),
    ]
    for path in protected_paths:
        write_json(stage_repo / path, {"frozen": path.as_posix()})
    protected_paths.extend(
        path.relative_to(stage_repo)
        for path in (stage_repo / "docs-viewer/scopes/analysis/pre-publish").rglob("*")
        if path.is_file()
    )
    before_protected = {path: (stage_repo / path).read_bytes() for path in protected_paths}

    def fixture_build(command, repo):
        assert "--stage" in command and "--skip-media-builds" in command
        code, stdout, stderr = run_cli(repo, command[2:])
        return {"returncode": code, "stdout": stdout, "stderr": stderr, "command": " ".join(command), "elapsed_seconds": 0}

    monkeypatch.setattr(rebuild, "run_rebuild_command", fixture_build)
    monkeypatch.setattr(mutation_service, "log_event", lambda *args, **kwargs: None)
    _, result = service.docs_management_post_response(stage_repo, "/docs/delete-apply", {
        "scope": "analysis", "stage": "working",
        "doc_ids": [parent_id if delete_ancestor else DOC_ID], "confirm": True,
    })
    assert result["ok"] is True and result["default_doc_id_changed"] is True
    assert set(result["deleted_doc_ids"]) == ({DOC_ID, parent_id} if delete_ancestor else {DOC_ID})
    assert scopes.load_docs_scope_stage(stage_repo, "analysis", "working").default_doc_id == ""
    assert not (source / f"{DOC_ID}.md").exists()
    assert (source / f"{survivor_id}.md").is_file()
    expected_browser = deepcopy(before_browser)
    analysis = next(record for record in expected_browser["scopes"] if record["scope_id"] == "analysis")
    next(record for record in analysis["stages"] if record["stage"] == "working")["default_doc_id"] = ""
    assert json.loads((stage_repo / browser_path).read_text()) == expected_browser
    assert all((stage_repo / path).read_bytes() == value for path, value in before_protected.items())


def test_working_write_rebuild_and_delete_preserve_other_owners(stage_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import docs_write_rebuild as rebuild
    import docs_management_service as service
    import docs_management_source_service as source_service
    import docs_management_mutation_service as mutation_service

    def forbidden_follow_through(*args, **kwargs):
        pytest.fail("Working Delete must not run public cleanup or lineage")

    monkeypatch.setattr(mutation_service.public_delete_cleanup, "apply_public_document_delete_cleanup", forbidden_follow_through)
    monkeypatch.setattr(mutation_service.publication_lineage, "apply_document_deletes", forbidden_follow_through)
    monkeypatch.setattr(mutation_service, "log_event", lambda *args, **kwargs: None)
    monkeypatch.setattr(source_service, "log_event", lambda *args, **kwargs: None)
    commands = []

    def fixture_build(command, repo):
        assert "--stage" in command and command[command.index("--stage") + 1] == "working"
        assert "--skip-media-builds" in command
        assert "build_search.py" not in " ".join(command)
        commands.append(command)
        code, stdout, stderr = run_cli(repo, command[2:])
        return {"returncode": code, "stdout": stdout, "stderr": stderr, "command": " ".join(command), "elapsed_seconds": 0}

    monkeypatch.setattr(rebuild, "run_rebuild_command", fixture_build)
    protected = stage_repo / "docs-viewer/scopes/analysis/pre-publish"
    before = {path: path.read_bytes() for path in protected.rglob("*") if path.is_file()}
    for relative in ("docs-viewer/scopes/analysis/published/documents/accepted.json", "site/assets/data/docs/scopes/analysis/accepted.json"):
        sentinel = stage_repo / relative
        sentinel.parent.mkdir(parents=True, exist_ok=True)
        sentinel.write_text("accepted\n")
        before[sentinel] = sentinel.read_bytes()
    for sub_scope in (None, "works"):
        collection = {"scope": "analysis", "stage": "working"}
        if sub_scope:
            collection["sub_scope"] = sub_scope
        _, created = service.docs_management_post_response(stage_repo, "/docs/create", {**collection, "title": "Stage test"})
        target = created["target"]
        params = {key: [value] for key, value in target.items()}
        read = source_service.read_source_body(stage_repo, params)
        media_root = "docs/analysis/sub-scopes/works" if collection.get("sub_scope") else "docs/analysis"
        body = f"# Edited\n\n[[media:{media_root}/img/retained.jpg]]\n"
        _, saved = service.docs_management_post_response(stage_repo, "/docs/source/rebuild", {
            **target, "source_body": body, "source_revision": read["source_revision"],
        })
        assert saved["stage"] == "working"
        assert source_service.read_source_body(stage_repo, params)["source_body"] == body
        resolved = resolve_managed_document_target(stage_repo, target)
        output = stage_repo / scopes.generated_documents_path(resolved.document_config)
        assert "Edited" in json.loads((output / "by-id" / f"{target['doc_id']}.json").read_text())["content_html"]
        if sub_scope:
            _, preview = service.docs_management_post_response(stage_repo, "/docs/delete-preview", target)
            delete_body = {**target, "source_revision": preview["source_revision"], "confirm": True}
        else:
            delete_body = {**collection, "doc_ids": [target["doc_id"]], "confirm": True}
        _, deleted = service.docs_management_post_response(stage_repo, "/docs/delete-apply", delete_body)
        assert deleted["stage"] == "working"
        assert not resolved.document.path.exists()
        assert not (output / "by-id" / f"{target['doc_id']}.json").exists()
    assert len(commands) == 6
    assert all(path.read_bytes() == value for path, value in before.items())


@pytest.mark.parametrize("path", ["/docs/create", "/docs/update-metadata", "/docs/source/rebuild", "/docs/delete-preview", "/docs/delete-apply", "/docs/document-transfer-preview"])
def test_pre_publish_services_reject_before_writes(stage_repo: Path, path: str) -> None:
    import docs_management_service as service
    before = {p: p.read_bytes() for p in stage_repo.rglob("*.md")}
    with pytest.raises(ValueError, match="unavailable"):
        service.docs_management_post_response(stage_repo, path, {"scope": "analysis", "stage": "pre-publish", "doc_id": DOC_ID})
    assert all(p.read_bytes() == value for p, value in before.items())


def test_watcher_owns_working_collections_only(stage_repo: Path) -> None:
    import docs_live_rebuild_watcher as watcher
    from docs_watch_suppression import watch_suppression_owner
    configs = scopes.load_docs_scope_configs(stage_repo)
    specs = watcher.desired_watch_state_specs(stage_repo, configs)
    assert "analysis" not in specs
    assert "analysis/working" in specs and "analysis/working/works" in specs
    assert not any("pre-publish" in key for key in specs)
    state = specs["analysis/working"]
    assert set(watcher.state_snapshot(state)) == {f"{DOC_ID}.md", f"{REPORT_ID}.md"}
    assert watch_suppression_owner("analysis", "projects", stage="working") != watch_suppression_owner("analysis", "projects", stage="pre-publish")


def test_external_stage_urls_and_media_use_selected_owner(stage_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from docs_generated_reads import external_sub_scope_payload_path
    from docs_media_storage import local_media_path_from_route
    from docs_media_inventory import source_media_references
    from docs_builder.browser_config import browser_scope_record

    monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(stage_repo / "external"))
    monkeypatch.setenv("DOTLINEFORM_DOCS_BASE_DIR", str((stage_repo / "external") / "docs-viewer"))
    (stage_repo / "external/docs-viewer").mkdir(parents=True)
    raw = json.loads((stage_repo / scopes.CONFIG_REL_PATH).read_text())
    analysis = raw["scopes"][0]
    analysis["scope_root"] = {"provider": "external_local", "path": "$DOTLINEFORM_DOCS_BASE_DIR/scopes/analysis"}
    write_json(stage_repo / scopes.CONFIG_REL_PATH, raw)
    for stage, collection in (("working", "works"), ("pre-publish", "works")):
        config = scopes.load_docs_scope_stage(stage_repo, "analysis", stage)
        parent = scopes.document_source_path(config)
        parent.mkdir(parents=True)
        (parent / f"{DOC_ID}.md").write_text(f"---\ndoc_id: {DOC_ID}\ntitle: {stage}\n---\n:::report\nid: docs_subscope\naccess: public\nsub_scope: {collection}\n:::\n")
        child = scopes.document_source_path(config.sub_scopes[0])
        child.mkdir(parents=True)
        (child / f"{DOC_ID}.md").write_text(f"---\ndoc_id: {DOC_ID}\ntitle: {stage}\n---\n# Child\n")
        generated = scopes.generated_documents_path(config)
        generated.mkdir(parents=True)
        for extra in ([], ["--sub-scope", collection]):
            code, stdout, stderr = run_cli(stage_repo, ["--scope", "analysis", "--stage", stage, "--write", "--skip-media-builds", *extra])
            assert code == 0, stdout + stderr
        record = read_generated_doc_payload(stage_repo, "analysis", DOC_ID, stage)
        assert record["title"] == stage
        record_config = browser_scope_record(stage_repo, {"analysis": analysis}, config)
        assert f"stage={stage}" in record_config["index_tree_url"]
        manifest_url = record_config["sub_scopes"][0]["manifest_url"]
        assert f"/analysis/{stage}/{collection}/" in manifest_url
        assert external_sub_scope_payload_path(stage_repo, manifest_url).parent == scopes.generated_documents_path(config.sub_scopes[0])
        media = config.media.types["img"]
        media.generated_location.path.mkdir(parents=True)
        picture = media.generated_location.path / "same.jpg"
        picture.write_bytes(stage.encode())
        path, kind = local_media_path_from_route(stage_repo, f"/docs/media/analysis/{stage}/img/same.jpg")
        assert kind == "img" and path.read_bytes() == stage.encode()
        token = f"[[media:{media.reference_prefix}/same.jpg]]"
        assert source_media_references(config, token, doc_id=DOC_ID)[0].logical_path.endswith("same.jpg")
    with pytest.raises(ValueError, match="requires stage"):
        local_media_path_from_route(stage_repo, "/docs/media/analysis/img/same.jpg")
    with pytest.raises(ValueError, match="unknown Docs Viewer scope"):
        local_media_path_from_route(stage_repo, "/docs/media/dotlineform/img/same.jpg")


def test_scope_manifest_records_stages_without_retired_source_paths(stage_repo: Path) -> None:
    from docs_scope_manifest import backfilled_scope_record
    config = scopes.load_docs_scope_configs(stage_repo)["analysis"]
    record = backfilled_scope_record(stage_repo, config)
    roles = {item["kind"] for item in record["files"]}
    assert "working/source_documents_root" in roles
    assert "pre-publish/source_documents_root" in roles
    assert "source_documents_root" not in roles
    assert "published_docs_root" in roles


@pytest.mark.parametrize("sub_scope", [None, "works"])
def test_draft_write_is_revision_bound_and_rebuilds_exact_target(stage_repo: Path, monkeypatch: pytest.MonkeyPatch, sub_scope: str | None) -> None:
    import docs_management_service as service
    import docs_management_mutation_service as mutation_service
    import docs_management_routes as routes
    import docs_source_model as source_model

    target = {"scope": "analysis", "stage": "working", "doc_id": DOC_ID, **({"sub_scope": sub_scope} if sub_scope else {})}
    path = resolve_managed_document_target(stage_repo, target).document.path
    fields, body = source_model.parse_source(path)
    fields.update({"draft": False, "ui_status": "review"})
    if not sub_scope:
        fields["publishable"] = False
    path.write_text(source_model.format_source(fields, body, sub_scope=sub_scope or ""))
    other = resolve_managed_document_target(stage_repo, {**target, "stage": "pre-publish"}).document.path
    other_before = other.read_bytes()
    metadata = managed_document_metadata(stage_repo, target)
    rebuilds = []

    def rebuilt(_root, scope, *args, **options):
        assert source_model.parse_source(path)[0]["draft"] is True
        rebuilds.append((scope, args, options["stage"]))
        return {"ok": True}

    monkeypatch.setattr(mutation_service.write_rebuild, "rebuild_scope_outputs", rebuilt)
    monkeypatch.setattr(mutation_service.write_rebuild, "rebuild_sub_scope_outputs", rebuilt)
    request = {**target, "draft": True, "source_revision": metadata["source_revision"]}
    assert routes.SET_DRAFT_PATH in routes.POST_PATHS
    status, result = service.docs_management_post_response(stage_repo, routes.SET_DRAFT_PATH, request)
    assert status == 200 and result["record"]["draft"] is True and result["target"] == target
    assert rebuilds == [("analysis", ("works",) if sub_scope else (), "working")]
    assert source_model.parse_source(path)[0] == {**fields, "draft": True, **({"sub-scope": sub_scope} if sub_scope else {})}
    assert other.read_bytes() == other_before
    status, conflict = service.docs_management_post_response(stage_repo, routes.SET_DRAFT_PATH, {**request, "draft": False})
    assert status == 409 and conflict["operation"] == "set_draft"
    assert source_model.parse_source(path)[0]["draft"] is True
    assert len(rebuilds) == 1
    for invalid in ({**request, "draft": "true"}, {**request, "stage": "pre-publish"}, {**request, "publishable": False}):
        with pytest.raises(ValueError):
            service.docs_management_post_response(stage_repo, routes.SET_DRAFT_PATH, invalid)


@pytest.mark.parametrize("sub_scope", [None, "works"])
def test_new_working_create_and_import_start_draft(stage_repo: Path, sub_scope: str | None) -> None:
    from docs_import_content import ImportContent, CONTENT_INTENT_EMPTY_NEW
    from docs_import_document import plan_import_document, IMPORT_DOCUMENT_CREATE
    from docs_management_document_target import resolve_managed_document_collection
    from docs_source_model import parse_source_text

    target = {"scope": "analysis", "stage": "working", **({"sub_scope": sub_scope} if sub_scope else {})}
    assert managed_document_metadata(stage_repo, {**target, "doc_id": DOC_ID})["record"]["draft"] is True
    create = plan_create(stage_repo, {**target, "title": "New"})
    assert parse_source_text(create.source_writes[0].text)[0]["draft"] is True
    collection = resolve_managed_document_collection(stage_repo, **target)
    record = ImportContent(source_kind="test", source_identity="test", record_identity="one", doc_id="d-20260909-180000-123abc", title="Imported", content_intent=CONTENT_INTENT_EMPTY_NEW, content_format="markdown")
    imported = plan_import_document(stage_repo, "analysis", record, operation=IMPORT_DOCUMENT_CREATE, docs=[], collection=collection,
        create_doc_id=record.doc_id, create_added_date="2026-09-09 18:00:00")
    assert parse_source_text(imported.source_text)[0]["draft"] is True


def test_subscope_rejects_publishable_and_supports_shared_visual_statuses(stage_repo: Path) -> None:
    from docs_management_publishable import plan_set_publishable
    from docs_management_mutations import plan_update_metadata
    from docs_source_model import parse_source_text, validate_document_status_front_matter

    target = {"scope": "analysis", "stage": "working", "sub_scope": "works", "doc_id": DOC_ID}
    with pytest.raises(ValueError, match="must contain exactly"):
        plan_set_publishable(stage_repo, {key: value for key, value in {**target, "doc_ids": [DOC_ID], "publishable": False, "confirm": True}.items() if key != "doc_id"})
    resolved = resolve_managed_document_target(stage_repo, target)
    with pytest.raises(ValueError, match="ordinary Analysis Working"):
        validate_document_status_front_matter({"publishable": False}, collection_config=resolved.document_config, source_name="child.md")
    metadata = managed_document_metadata(stage_repo, target)
    plan = plan_update_metadata(stage_repo, {**target, "title": "Shared visual options", "ui_status": "research", "source_revision": metadata["source_revision"]})
    assert parse_source_text(plan.source_writes[0].text)[0]["ui_status"] == "research"
