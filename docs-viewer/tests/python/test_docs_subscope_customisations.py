#!/usr/bin/env python3
"""Registered Docs Viewer sub-scope customisation aspect tests."""

from __future__ import annotations

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
    assert analysis.metadata is None
    assert analysis.import_front_matter is None
    assert analysis.browser_composition == (
        customisations.DocsSubScopeBrowserCompositionAspect(
            accesses=frozenset({"manage"}),
        )
    )
    assert analysis.assignable_field_groups == ()
    assert analysis.transfer is None

    assert isinstance(
        projects.manifest_projection,
        customisations.DocsSubScopeManifestProjectionAspect,
    )
    assert projects.document_groups is None
    assert isinstance(
        projects.source_validation,
        customisations.DocsSubScopeSourceValidationAspect,
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
            field_names=("folder_path",),
        ),
    )
    assert projects.transfer is None

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
            contract_id="subject_fields",
            owned_field_names=("folder_path", "work_id", "series_id"),
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
