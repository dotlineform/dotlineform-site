"""Small staged document source fixture for Concept identity and token lookup checks."""

from copy import deepcopy
from pathlib import Path

from repo_factory import docs_scope_record, docs_sub_scope_record, write_docs_scope_config
from docs_scope_config import document_source_path, load_docs_scope_stage


HOST_ID = "d-20260811-120000-000001"
CONCEPT_DOC_ID = "d-20260811-120000-100001"


def write_concept_sources(root: Path, *, concept_id: str = "order", extra_scopes: list | None = None) -> None:
    """Create matching identities in both stages with independently readable source roots."""

    analysis = docs_scope_record("analysis", scope_type="public", default_doc_id=HOST_ID, viewer_base_url="/analysis/", include_scope_param=False)
    analysis["stages"] = {
        stage: {
            "media": deepcopy(analysis["media"]),
            "sub_scopes": [docs_sub_scope_record("analysis", "concepts", scope_type="public" if stage == "pre-publish" else "local", sub_scope_customisation={"id": "concepts", "settings": {"groups": ["theme"]}})],
        }
        for stage in ("working", "pre-publish")
    }
    write_docs_scope_config(root, [*(extra_scopes or []), analysis])
    for stage in ("working", "pre-publish"):
        parent = load_docs_scope_stage(root, "analysis", stage)
        parent_source = root / document_source_path(parent)
        parent_source.mkdir(parents=True, exist_ok=True)
        (parent_source / f"{HOST_ID}.md").write_text(
            f"---\ndoc_id: {HOST_ID}\ntitle: Concepts\n---\n# Concepts\n"
            "\n:::report\nid: docs_subscope\naccess: public\nsub_scope: concepts\n:::\n",
        )
        source = root / document_source_path(parent.sub_scopes[0])
        source.mkdir(parents=True, exist_ok=True)
        (source / f"{CONCEPT_DOC_ID}.md").write_text(
            f"---\ndoc_id: {CONCEPT_DOC_ID}\ntitle: Order\nconcept_id: {concept_id}\n"
            "group: theme\n---\n# Order\n",
        )
