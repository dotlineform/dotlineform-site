"""Document-owned Concept identity and generated relationship contracts."""

from types import SimpleNamespace

import pytest
import docs_concept_documents as concepts
from concept_factory import CONCEPT_DOC_ID, write_concept_sources
from docs_scope_config import document_source_path, load_docs_scope_stage


def test_optional_declarations_and_legacy_field_are_not_concept_identities():
    for fields in ({}, {"concept_id": None}, {"concept_id": ""}, {"tag_id": "001"}):
        assert concepts.normalize_concept_declaration(fields) == {"state": "none", "concept_id": ""}
    assert concepts.normalize_concept_declaration({"concept_id": "001"}) == {"state": "valid", "concept_id": "001"}
    for value in (" Order ", "bad_slug", True, 42):
        assert concepts.normalize_concept_declaration({"concept_id": value}) == {
            "state": "malformed", "concept_id": "", "evidence": value,
        }


def test_projection_rejects_duplicate_definitions_but_allows_undeclared_documents():
    docs = [SimpleNamespace(doc_id="a", title="A"), SimpleNamespace(doc_id="b", title="B")]
    declarations = {"a": {"state": "valid", "concept_id": "001"}, "b": {"state": "none", "concept_id": ""}}
    def project():
        return concepts.project_concept_associations(
            scope="analysis", stage="working", sub_scope="concepts", documents=docs,
            declarations_by_doc_id=declarations, declaration_generation="sha256:fixture",
            management_urls_by_doc_id={"a": "/docs/?scope=analysis&stage=working&doc=a"},
        )
    payload = project()
    assert payload["schema_version"] == "docs_concept_associations_v1"
    assert [row["concept_id"] for row in payload["associations"]] == ["001"]
    assert payload["associations"][0]["documents"][0]["target"] == {
        "scope": "analysis", "stage": "working", "sub_scope": "concepts", "doc_id": "a",
    }
    declarations["b"] = declarations["a"].copy()
    with pytest.raises(ValueError, match="duplicate concept_id '001': a and b"):
        project()


def test_definitions_use_exact_stage_and_unique_document_without_studio(tmp_path):
    write_concept_sources(tmp_path)
    for stage in ("working", "pre-publish"):
        rows = concepts.load_concept_definitions(tmp_path, stage=stage)
        assert len(rows) == 1
        assert rows[0]["concept_id"] == "001"
        assert rows[0]["doc_id"] == CONCEPT_DOC_ID
        assert f"stage={stage}" in rows[0]["href"]
        assert rows[0]["href"].endswith(f"&subdoc={CONCEPT_DOC_ID}")
    assert not (tmp_path / "studio").exists()
    parent = load_docs_scope_stage(tmp_path, "analysis", "working")
    source = tmp_path / document_source_path(parent.sub_scopes[0])
    duplicate_id = "d-20260811-120000-100002"
    raw = (source / f"{CONCEPT_DOC_ID}.md").read_text()
    (source / f"{duplicate_id}.md").write_text(raw.replace(CONCEPT_DOC_ID, duplicate_id))
    with pytest.raises(ValueError, match="duplicate concept_id '001'"):
        concepts.load_concept_definitions(tmp_path)
