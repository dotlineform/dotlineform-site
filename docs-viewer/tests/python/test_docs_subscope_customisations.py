#!/usr/bin/env python3
"""Registered Docs Viewer sub-scope customisation aspect tests."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

import docs_subscope_customisations as customisations


def _empty_settings(raw: object, field: str) -> dict[str, object]:
    if raw != {}:
        raise ValueError(f"{field} must be empty")
    return {}


def _empty_manifest(
    settings: object,
    documents: object,
) -> dict[str, object]:
    assert settings == {}
    assert documents == ()
    return {
        "root": {"id": "synthetic", "data": {}},
        "rows": {},
    }


def test_current_customisations_declare_explicit_aspects() -> None:
    analysis = customisations.SUB_SCOPE_CUSTOMISATION_DEFINITIONS["analysis_tags"]
    works = customisations.SUB_SCOPE_CUSTOMISATION_DEFINITIONS["analysis_works"]
    projects = customisations.SUB_SCOPE_CUSTOMISATION_DEFINITIONS[
        "dotlineform_projects"
    ]

    assert isinstance(
        analysis.manifest_projection,
        customisations.DocsSubScopeManifestProjectionAspect,
    )
    assert isinstance(
        analysis.document_groups,
        customisations.DocsSubScopeDocumentGroupsAspect,
    )
    assert analysis.source_validation is None
    assert isinstance(analysis.metadata, customisations.DocsSubScopeMetadataAspect)
    assert analysis.import_front_matter is None
    assert analysis.browser_composition == (
        customisations.DocsSubScopeBrowserCompositionAspect(
            accesses=frozenset({"manage"}),
        )
    )
    assert analysis.assignable_field_groups == (
        customisations.DocsSubScopeAssignableFieldGroup(
            group_id="tag_fields",
            field_names=("group",),
        ),
    )
    assert analysis.transfer is not None
    assert analysis.transfer.contract_id == "analysis_tag_fields"
    assert analysis.transfer.owned_field_names == ("group",)

    assert works.browser_composition is None
    assert works.assignable_field_groups == ()
    assert works.authoring_subject == (
        customisations.DocsSubScopeAuthoringSubjectAspect(
            field_names=("folder_path", "work_id", "series_id"),
        )
    )
    assert works.transfer is None
    assert works.document_lineage == (
        customisations.DocsSubScopeDocumentLineageAspect(
            contract_id="dotlineform_projects_to_analysis_works",
            role="editorial",
        )
    )

    assert isinstance(
        projects.manifest_projection,
        customisations.DocsSubScopeManifestProjectionAspect,
    )
    assert projects.document_groups is None
    assert projects.source_validation is None
    assert isinstance(projects.metadata, customisations.DocsSubScopeMetadataAspect)
    assert isinstance(
        projects.import_front_matter,
        customisations.DocsSubScopeImportFrontMatterAspect,
    )
    assert projects.browser_composition == (
        customisations.DocsSubScopeBrowserCompositionAspect(
            accesses=frozenset({"manage"}),
        )
    )
    assert projects.assignable_field_groups == (
        customisations.DocsSubScopeAssignableFieldGroup(
            group_id="authoring_subject",
            field_names=("folder_path", "work_id", "series_id"),
        ),
    )
    assert projects.transfer is None
    assert projects.document_lineage == (
        customisations.DocsSubScopeDocumentLineageAspect(
            contract_id="dotlineform_projects_to_analysis_works",
            role="source",
        )
    )

    projects_config = customisations.normalize_docs_subscope_customisation(
        {"id": "dotlineform_projects", "settings": {}},
        field="sub_scope_customisation",
    )
    assert customisations.browser_sub_scope_customisation_payload(
        projects_config,
        published=False,
    ) == {
        "id": "dotlineform_projects",
        "capabilities": {
            "assignable_field_groups": ["authoring_subject"],
        },
    }
    assert customisations.browser_sub_scope_customisation_payload(
        projects_config,
        published=True,
    ) is None

    analysis_config = customisations.normalize_docs_subscope_customisation(
        {
            "id": "analysis_tags",
            "settings": {"groups": ["subject", "domain", "form", "theme"]},
        },
        field="sub_scope_customisation",
    )
    assert customisations.browser_sub_scope_customisation_payload(
        analysis_config,
        published=False,
    ) == {
        "id": "analysis_tags",
        "capabilities": {
            "assignable_field_groups": ["tag_fields"],
        },
    }
    assert customisations.browser_sub_scope_customisation_payload(
        analysis_config,
        published=True,
    ) is None
    assert customisations.sub_scope_customisation_metadata_record(
        analysis_config,
        {"group": " Theme "},
        doc_id="tag-doc",
    ) == {"group": "theme"}
    assert customisations.sub_scope_customisation_metadata_record(
        analysis_config,
        {},
        doc_id="untagged-doc",
    ) == {"group": ""}
    assert customisations.normalize_sub_scope_customisation_metadata_update(
        analysis_config,
        {"group": "domain"},
        provided=True,
        repo_root=Path("."),
        front_matter={"group": "theme"},
        doc_id="tag-doc",
    ) == {
        "front_matter_updates": {"group": "domain"},
        "record": {"group": "domain"},
        "changes": {"group_changed": True},
    }
    assert customisations.normalize_sub_scope_customisation_metadata_update(
        analysis_config,
        {"group": ""},
        provided=True,
        repo_root=Path("."),
        front_matter={"group": "theme"},
        doc_id="tag-doc",
    )["front_matter_updates"] == {"group": None}
    with pytest.raises(ValueError, match="one exact configured group"):
        customisations.normalize_sub_scope_customisation_metadata_update(
            analysis_config,
            {"group": " Theme "},
            provided=True,
            repo_root=Path("."),
            front_matter={"group": "theme"},
            doc_id="tag-doc",
        )
    with pytest.raises(ValueError, match="not configured for the target"):
        customisations.sub_scope_customisation_metadata_record(
            analysis_config,
            {"group": "retired"},
            doc_id="retired-tag-doc",
        )

    works_config = customisations.normalize_docs_subscope_customisation(
        {"id": "analysis_works", "settings": {}},
        field="sub_scope_customisation",
    )
    assert customisations.browser_sub_scope_customisation_payload(
        works_config,
        published=False,
    ) is None
    assert customisations.sub_scope_customisation_assignable_field_groups(
        works_config
    ) == ()
    assert customisations.sub_scope_customisation_authoring_subject_fields(
        works_config
    ) == ("folder_path", "work_id", "series_id")
    assert customisations.sub_scope_customisation_document_lineage_contract(
        works_config
    ) == works.document_lineage
    assert customisations.sub_scope_customisation_document_lineage_contract(
        projects_config
    ) == projects.document_lineage


def test_assignable_and_transfer_seams_are_typed_and_access_safe() -> None:
    definition = customisations.DocsSubScopeCustomisationDefinition(
        customisation_id="synthetic",
        normalize_settings=_empty_settings,
        manifest_projection=customisations.DocsSubScopeManifestProjectionAspect(
            project=_empty_manifest,
        ),
        browser_composition=customisations.DocsSubScopeBrowserCompositionAspect(
            accesses=frozenset({"manage"}),
        ),
        assignable_field_groups=(
            customisations.DocsSubScopeAssignableFieldGroup(
                group_id="authoring_subject",
                field_names=("folder_path", "work_id", "series_id"),
            ),
        ),
        transfer=customisations.DocsSubScopeTransferAspect(
            contract_id="synthetic_fields",
            owned_field_names=("synthetic_field",),
            validate_field=lambda _settings, _field_name, _value: None,
        ),
    )
    with patch.dict(
        customisations.SUB_SCOPE_CUSTOMISATION_DEFINITIONS,
        {"synthetic": definition},
    ):
        config = customisations.normalize_docs_subscope_customisation(
            {"id": "synthetic", "settings": {}},
            field="sub_scope_customisation",
        )
        manage_payload = customisations.browser_sub_scope_customisation_payload(
            config,
            published=False,
        )
        public_payload = customisations.browser_sub_scope_customisation_payload(
            config,
            published=True,
        )
        groups = customisations.sub_scope_customisation_assignable_field_groups(
            config
        )
        transfer = customisations.sub_scope_customisation_transfer_contract(config)

    assert manage_payload == {
        "id": "synthetic",
        "capabilities": {
            "assignable_field_groups": ["authoring_subject"],
        },
    }
    assert public_payload is None
    assert groups == definition.assignable_field_groups
    assert transfer == definition.transfer


def test_assignable_field_groups_require_manage_browser_access() -> None:
    definition = customisations.DocsSubScopeCustomisationDefinition(
        customisation_id="synthetic",
        normalize_settings=_empty_settings,
        manifest_projection=customisations.DocsSubScopeManifestProjectionAspect(
            project=_empty_manifest,
        ),
        browser_composition=customisations.DocsSubScopeBrowserCompositionAspect(
            accesses=frozenset({"public"}),
        ),
        assignable_field_groups=(
            customisations.DocsSubScopeAssignableFieldGroup(
                group_id="authoring_subject",
                field_names=("folder_path",),
            ),
        ),
    )
    with patch.dict(
        customisations.SUB_SCOPE_CUSTOMISATION_DEFINITIONS,
        {"synthetic": definition},
    ):
        with pytest.raises(ValueError, match="require Manage browser access"):
            customisations.normalize_docs_subscope_customisation(
                {"id": "synthetic", "settings": {}},
                field="sub_scope_customisation",
            )


def test_browser_composition_requires_manifest_projection() -> None:
    definition = customisations.DocsSubScopeCustomisationDefinition(
        customisation_id="synthetic",
        normalize_settings=_empty_settings,
        browser_composition=customisations.DocsSubScopeBrowserCompositionAspect(
            accesses=frozenset({"manage"}),
        ),
    )
    with patch.dict(
        customisations.SUB_SCOPE_CUSTOMISATION_DEFINITIONS,
        {"synthetic": definition},
    ):
        with pytest.raises(ValueError, match="requires manifest_projection"):
            customisations.normalize_docs_subscope_customisation(
                {"id": "synthetic", "settings": {}},
                field="sub_scope_customisation",
            )


def test_transfer_contract_cannot_claim_shared_subject_fields() -> None:
    definition = customisations.DocsSubScopeCustomisationDefinition(
        customisation_id="synthetic",
        normalize_settings=_empty_settings,
        transfer=customisations.DocsSubScopeTransferAspect(
            contract_id="synthetic_fields",
            owned_field_names=("work_id",),
            validate_field=lambda _settings, _field_name, _value: None,
        ),
    )
    with patch.dict(
        customisations.SUB_SCOPE_CUSTOMISATION_DEFINITIONS,
        {"synthetic": definition},
    ):
        with pytest.raises(ValueError, match="must not own shared"):
            customisations.normalize_docs_subscope_customisation(
                {"id": "synthetic", "settings": {}},
                field="sub_scope_customisation",
            )


def test_document_lineage_contract_requires_a_supported_exact_role() -> None:
    definition = customisations.DocsSubScopeCustomisationDefinition(
        customisation_id="synthetic",
        normalize_settings=_empty_settings,
        document_lineage=customisations.DocsSubScopeDocumentLineageAspect(
            contract_id="synthetic_lineage",
            role="primary",
        ),
    )
    with patch.dict(
        customisations.SUB_SCOPE_CUSTOMISATION_DEFINITIONS,
        {"synthetic": definition},
    ):
        with pytest.raises(ValueError, match="invalid role"):
            customisations.normalize_docs_subscope_customisation(
                {"id": "synthetic", "settings": {}},
                field="sub_scope_customisation",
            )
