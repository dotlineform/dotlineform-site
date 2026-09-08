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
    works = customisations.SUB_SCOPE_CUSTOMISATION_DEFINITIONS["pre_publish_works"]
    projects = customisations.SUB_SCOPE_CUSTOMISATION_DEFINITIONS[
        "working_works"
    ]
    processing = customisations.SUB_SCOPE_CUSTOMISATION_DEFINITIONS[
        "working_processing"
    ]

    assert works.browser_composition.accesses == frozenset({"manage"})
    assert works.assignable_field_groups == (
        customisations.DocsSubScopeAssignableFieldGroup(
            group_id="authoring_subject",
            field_names=("folder_path", "work_id", "series_id", "detail_uid"),
        ),
    )
    assert works.authoring_subject == (
        customisations.DocsSubScopeAuthoringSubjectAspect(
            field_names=("work_id", "series_id", "detail_uid"),
        )
    )
    assert works.transfer is None
    assert works.document_lineages == ()

    assert isinstance(
        projects.manifest_projection,
        customisations.DocsSubScopeManifestProjectionAspect,
    )
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
            field_names=("folder_path", "work_id", "series_id", "detail_uid"),
        ),
    )
    assert projects.transfer is None
    assert projects.document_lineages == ()

    assert isinstance(
        processing.manifest_projection,
        customisations.DocsSubScopeManifestProjectionAspect,
    )
    assert isinstance(processing.metadata, customisations.DocsSubScopeMetadataAspect)
    assert isinstance(
        processing.import_front_matter,
        customisations.DocsSubScopeImportFrontMatterAspect,
    )
    assert processing.browser_composition == (
        customisations.DocsSubScopeBrowserCompositionAspect(
            accesses=frozenset({"manage"}),
        )
    )
    assert processing.assignable_field_groups == (
        customisations.DocsSubScopeAssignableFieldGroup(
            group_id="authoring_subject",
            field_names=("folder_path", "work_id", "series_id", "detail_uid"),
        ),
    )
    assert processing.transfer is None
    assert processing.document_lineages == ()

    projects_config = customisations.normalize_docs_subscope_customisation(
        {"id": "working_works", "settings": {}},
        field="sub_scope_customisation",
    )
    assert customisations.browser_sub_scope_customisation_payload(
        projects_config,
        published=False,
    ) == {
        "id": "working_works",
        "capabilities": {
            "assignable_field_groups": ["authoring_subject"],
        },
    }
    assert customisations.browser_sub_scope_customisation_payload(
        projects_config,
        published=True,
    ) is None

    processing_config = customisations.normalize_docs_subscope_customisation(
        {"id": "working_processing", "settings": {}},
        field="sub_scope_customisation",
    )
    assert customisations.browser_sub_scope_customisation_payload(
        processing_config,
        published=False,
    ) == {
        "id": "working_processing",
        "capabilities": {
            "assignable_field_groups": ["authoring_subject"],
        },
    }
    assert customisations.browser_sub_scope_customisation_payload(
        processing_config,
        published=True,
    ) is None
    assert customisations.sub_scope_customisation_document_lineage_contracts(
        processing_config
    ) == processing.document_lineages

    works_config = customisations.normalize_docs_subscope_customisation(
        {"id": "pre_publish_works", "settings": {}},
        field="sub_scope_customisation",
    )
    assert customisations.browser_sub_scope_customisation_payload(
        works_config,
        published=False,
    ) == {
        "id": "pre_publish_works",
        "capabilities": {"assignable_field_groups": ["authoring_subject"]},
    }
    assert customisations.browser_sub_scope_customisation_payload(
        works_config, published=True,
    ) is None
    assert customisations.sub_scope_customisation_assignable_field_groups(
        works_config
    ) == works.assignable_field_groups
    assert customisations.sub_scope_customisation_authoring_subject_fields(
        works_config
    ) == ("work_id", "series_id", "detail_uid")
    assert customisations.sub_scope_customisation_document_lineage_contracts(
        works_config
    ) == works.document_lineages
    assert customisations.sub_scope_customisation_document_lineage_contracts(
        projects_config
    ) == projects.document_lineages


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
        document_lineages=(
            customisations.DocsSubScopeDocumentLineageAspect(
                contract_id="synthetic_lineage",
                role="primary",
            ),
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
