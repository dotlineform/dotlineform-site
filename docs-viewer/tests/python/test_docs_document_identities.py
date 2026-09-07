"""Numeric entity ownership, exact allocation writes and generated identity boundaries."""

from pathlib import Path
import json

import pytest

from test_docs_workflow_stages import stage_repo, DOC_ID  # noqa: F401
from docs_document_identities import normalize_document_identity, next_document_identity
from docs_document_identity_allocation import plan_allocate_document_identity
from docs_management_document_target import managed_document_metadata, resolve_managed_document_target
from docs_management_mutations import ManagedDocumentRevisionConflict
from docs_scope_config import CONFIG_REL_PATH, load_docs_scope_stage, document_source_path, generated_documents_path
from docs_source_model import parse_source_text, format_source
from docs_builder.sub_scope import SubScopeDocsBuilder


@pytest.mark.parametrize("field", ["concept_id", "moment_id"])
def test_exact_optional_identity_and_sequence(field):
    for raw in ({}, {field: None}, {field: ""}, {"title": "001"}):
        assert normalize_document_identity(raw, field) == {"state": "none", field: ""}
    for value in (1, True, "1", "01", "0001", "001\n", " 001", "٠٠١", "absence"):
        assert normalize_document_identity({field: value}, field)["state"] == "malformed"
    declarations = {key: normalize_document_identity({field: value}, field) for key, value in (("first", "001"), ("last", "009"), ("plain", None))}
    assert next_document_identity({}, field) == "001"
    assert next_document_identity(declarations, field) == "010"
    with pytest.raises(ValueError, match="duplicate"):
        next_document_identity({**declarations, "copy": declarations["last"]}, field)
    with pytest.raises(ValueError, match="No three-digit"):
        next_document_identity({"last": normalize_document_identity({field: "999"}, field)}, field)


def test_moment_import_transfer_and_metadata_keep_an_independent_exact_identity():
    import docs_moments_customisation as moments
    from docs_subscope_customisations import SUB_SCOPE_CUSTOMISATION_DEFINITIONS

    definition = SUB_SCOPE_CUSTOMISATION_DEFINITIONS["moments"]
    assert definition.identity_kind == "moment" and definition.authoring_subject is None
    assert definition.transfer.owned_field_names == ("moment_id",)
    assert moments.normalize_import({}, {"moment_id": "056"}, doc_id=DOC_ID) == {"moment_id": "056"}
    assert moments.normalize_import({}, {}, doc_id=DOC_ID) == {}
    assert moments.metadata_record({}, {"moment_id": "056", "work_id": "00293"}, doc_id=DOC_ID) == {"moment_id": "056"}
    moments.validate_transfer({}, "moment_id", "056")
    with pytest.raises(ValueError, match="three-digit"):
        moments.validate_transfer({}, "moment_id", 56)
    with pytest.raises(ValueError, match="only moment_id"):
        moments.normalize_import({}, {"work_id": "00293"}, doc_id=DOC_ID)


@pytest.mark.parametrize("kind,customisation", [("concept", "concepts"), ("moment", "moments")])
def test_allocation_exact_write_noop_revision_and_projection(stage_repo: Path, monkeypatch, kind, customisation):
    import docs_management_mutation_service as service
    from docs_management_service import docs_management_post_response, routes

    config_path = stage_repo / CONFIG_REL_PATH
    config = json.loads(config_path.read_text())
    # Capability, not the collection's name, owns allocation.
    for stage in ("working", "pre-publish"):
        config["scopes"][0]["stages"][stage]["sub_scopes"][0]["sub_scope_customisation"] = {
            "id": customisation, "settings": {"groups": ["theme"]} if kind == "concept" else {},
        }
    config_path.write_text(json.dumps(config))
    parent_config = load_docs_scope_stage(stage_repo, "analysis", "working")
    host_path = stage_repo / document_source_path(parent_config) / f"{DOC_ID}.md"
    host_path.write_text(host_path.read_text() + "\n:::report\nid: docs_subscope\naccess: local\nsub_scope: works\n:::\n")
    target = {"scope": "analysis", "stage": "working", "sub_scope": "works", "doc_id": DOC_ID}
    resolved = resolve_managed_document_target(stage_repo, target)
    source = resolved.document.path
    body = "# A different header\n\nAn unchanged final line"
    other_field = "moment_id" if kind == "concept" else "concept_id"
    source.write_text(format_source({"doc_id": DOC_ID, "title": "A title", "work_id": "00293", other_field: "999"}, body))
    original_body = parse_source_text(source.read_text())[1]
    previous = source.parent / "d-20260907-230000-aaaaaa.md"
    previous.write_text(format_source({"doc_id": previous.stem, "title": "Previous", kind + "_id": "009"}, "# Previous\n"))
    metadata = managed_document_metadata(stage_repo, target)
    request = {**target, "source_revision": metadata["source_revision"], "confirm": True}
    plan = plan_allocate_document_identity(stage_repo, request)
    assert plan.stage == "working" and plan.response["target"] == target
    assert plan.response["value"] == "010" and plan.response["changed"] is True
    assert len(plan.source_writes) == 1 and plan.source_writes[0].path == source
    fm, output_body = parse_source_text(plan.source_writes[0].text)
    assert fm[kind + "_id"] == "010" and fm["work_id"] == "00293"
    assert fm[other_field] == "999"
    assert fm["title"] == "A title" and output_body == original_body
    assert f'{kind}_id: "010"' in plan.source_writes[0].text
    with pytest.raises(ManagedDocumentRevisionConflict):
        plan_allocate_document_identity(stage_repo, {**request, "source_revision": "sha256:" + "0" * 64})
    with pytest.raises(ValueError, match="Pre-publish"):
        plan_allocate_document_identity(stage_repo, {**request, "stage": "pre-publish"})
    with pytest.raises(ValueError, match="requires scope"):
        plan_allocate_document_identity(stage_repo, {**request, "value": "123"})
    calls = []
    def rebuild(repo_root, scope, sub_scope, changed_paths, write_operation, **options):
        calls.append((scope, sub_scope, options))
        write_operation()
        return {"ok": True}
    monkeypatch.setattr(service.write_rebuild, "perform_sub_scope_source_write_and_rebuild", rebuild)
    before_write = source.read_bytes()
    source.write_bytes(before_write + b"\n")
    with pytest.raises(ManagedDocumentRevisionConflict) as conflict:
        service.execute_management_mutation_plan(stage_repo, plan, False)
    assert conflict.value.payload["target"] == target
    source.write_bytes(before_write)
    calls.clear()
    status, response = docs_management_post_response(stage_repo, routes.ALLOCATE_IDENTITY_PATH, request, dry_run=False)
    assert status == 200 and response["target"] == target and response["value"] == "010"
    assert calls[0][0:2] == ("analysis", "works") and calls[0][2]["stage"] == "working"
    request["source_revision"] = managed_document_metadata(stage_repo, target)["source_revision"]
    before = source.read_bytes()
    unchanged = plan_allocate_document_identity(stage_repo, request)
    assert not unchanged.source_writes and unchanged.response["changed"] is False
    assert unchanged.response["value"] == "010" and source.read_bytes() == before
    if kind == "concept":
        status, assigned = docs_management_post_response(stage_repo, routes.ASSIGN_FIELD_GROUP_PATH, {
            **request, "field_group": "concept_group", "fields": {"group": "theme"},
        })
        assert status == 200 and assigned["fields"] == {"group": "theme"}
        updated_fm, updated_body = parse_source_text(source.read_text())
        assert updated_fm["concept_id"] == "010" and updated_fm["moment_id"] == "999"
        assert updated_body == original_body
        request["source_revision"] = assigned["source_revision"]
    parent = load_docs_scope_stage(stage_repo, "analysis", "working")
    builder = SubScopeDocsBuilder(repo_root=stage_repo, config=parent, sub_scope=parent.sub_scopes[0], skip_media_builds=True)
    builder._parent_report_doc_id = ""
    builder.run(write=True)
    output = stage_repo / generated_documents_path(parent.sub_scopes[0])
    manifest = json.loads((output / "manage-manifest.json").read_text())
    row = next(row for row in manifest["docs"] if row["doc_id"] == DOC_ID)
    assert row["customisation"][kind + "_id"] == "010"
    assert row["authoring_subject"]["kind"] == "work"
    previous.write_text(previous.read_text().replace('"009"', '"010"'))
    with pytest.raises(ValueError, match="duplicate"):
        builder.run(write=False)
    with pytest.raises(ValueError, match="duplicate"):
        plan_allocate_document_identity(stage_repo, request)
    config["scopes"][0]["stages"]["working"]["sub_scopes"][0]["sub_scope_customisation"] = {"id": "working_works", "settings": {}}
    config_path.write_text(json.dumps(config))
    with pytest.raises(ValueError, match="not configured"):
        plan_allocate_document_identity(stage_repo, request)
