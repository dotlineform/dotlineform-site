"""Registered Docs Viewer sub-scope customisations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Callable, Mapping, Sequence

import docs_dotlineform_projects_customisation as dotlineform_projects


CUSTOMISATION_ID_PATTERN = re.compile(r"\A[a-z][a-z0-9_]*\Z")
VALUE_ID_PATTERN = re.compile(r"\A[a-z0-9][a-z0-9_-]*\Z")
ANALYSIS_TAGS_CUSTOMISATION_ID = "analysis_tags"
DOTLINEFORM_PROJECTS_CUSTOMISATION_ID = dotlineform_projects.CUSTOMISATION_ID
PUBLIC_ACCESS = "public"
MANAGE_ACCESS = "manage"
SUPPORTED_BROWSER_ACCESSES = frozenset({PUBLIC_ACCESS, MANAGE_ACCESS})


@dataclass(frozen=True)
class DocsSubScopeCustomisationConfig:
    customisation_id: str
    settings: Mapping[str, Any]


@dataclass(frozen=True)
class DocsSubScopeManifestProjectionAspect:
    project: Callable[[Mapping[str, Any], Sequence[Any]], dict[str, Any]]


@dataclass(frozen=True)
class DocsSubScopeDocumentGroupsAspect:
    resolve: Callable[[Mapping[str, Any]], tuple[str, ...]]


@dataclass(frozen=True)
class DocsSubScopeSourceValidationAspect:
    validate: Callable[..., None]


@dataclass(frozen=True)
class DocsSubScopeMetadataAspect:
    read_record: Callable[..., dict[str, Any]]
    normalize_update: Callable[..., dict[str, Any]] | None = None


@dataclass(frozen=True)
class DocsSubScopeImportFrontMatterAspect:
    normalize: Callable[..., dict[str, Any]]


@dataclass(frozen=True)
class DocsSubScopeBrowserCompositionAspect:
    accesses: frozenset[str]


@dataclass(frozen=True)
class DocsSubScopeAssignableFieldGroup:
    group_id: str
    field_names: tuple[str, ...]


@dataclass(frozen=True)
class DocsSubScopeTransferAspect:
    contract_id: str
    owned_field_names: tuple[str, ...]


@dataclass(frozen=True)
class DocsSubScopeCustomisationDefinition:
    customisation_id: str
    normalize_settings: Callable[[Any, str], Mapping[str, Any]]
    manifest_projection: DocsSubScopeManifestProjectionAspect | None = None
    document_groups: DocsSubScopeDocumentGroupsAspect | None = None
    source_validation: DocsSubScopeSourceValidationAspect | None = None
    metadata: DocsSubScopeMetadataAspect | None = None
    import_front_matter: DocsSubScopeImportFrontMatterAspect | None = None
    browser_composition: DocsSubScopeBrowserCompositionAspect | None = None
    assignable_field_groups: tuple[DocsSubScopeAssignableFieldGroup, ...] = ()
    transfer: DocsSubScopeTransferAspect | None = None


def _strict_object(raw: Any, *, field: str, keys: set[str]) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError(f"docs scope config field {field} must be an object")
    unknown = sorted(set(raw) - keys)
    if unknown:
        raise ValueError(
            f"docs scope config field {field} contains unknown fields: "
            f"{', '.join(unknown)}"
        )
    missing = sorted(keys - set(raw))
    if missing:
        raise ValueError(
            f"docs scope config field {field} is missing required fields: "
            f"{', '.join(missing)}"
        )
    return raw


def _normalize_ordered_ids(raw: Any, *, field: str) -> tuple[str, ...]:
    if not isinstance(raw, list):
        raise ValueError(f"docs scope config field {field} must be an array")
    values: list[str] = []
    seen: set[str] = set()
    for index, raw_value in enumerate(raw):
        if not isinstance(raw_value, str):
            raise ValueError(
                f"docs scope config field {field}[{index}] must be a string"
            )
        value = raw_value.strip().lower()
        if not VALUE_ID_PATTERN.fullmatch(value):
            raise ValueError(
                f"docs scope config field {field}[{index}] is invalid"
            )
        if value in seen:
            raise ValueError(
                f"docs scope config field {field} must not contain duplicates"
            )
        seen.add(value)
        values.append(value)
    if not values:
        raise ValueError(f"docs scope config field {field} must not be empty")
    return tuple(values)


def _normalize_analysis_tags_settings(raw: Any, field: str) -> Mapping[str, Any]:
    settings = _strict_object(raw, field=field, keys={"groups"})
    return {
        "groups": _normalize_ordered_ids(
            settings["groups"],
            field=f"{field}.groups",
        )
    }


def _analysis_tags_document_groups(settings: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(str(value) for value in settings.get("groups", ()))


def _project_analysis_tags_manifest(
    settings: Mapping[str, Any],
    documents: Sequence[Any],
) -> dict[str, Any]:
    groups = _analysis_tags_document_groups(settings)
    rows = {
        str(document.doc_id): {"group": str(document.group)}
        for document in documents
        if str(getattr(document, "group", "") or "").strip()
    }
    return {
        "root": {
            "id": ANALYSIS_TAGS_CUSTOMISATION_ID,
            "data": {"groups": list(groups)},
        },
        "rows": rows,
    }


SUB_SCOPE_CUSTOMISATION_DEFINITIONS = {
    ANALYSIS_TAGS_CUSTOMISATION_ID: DocsSubScopeCustomisationDefinition(
        customisation_id=ANALYSIS_TAGS_CUSTOMISATION_ID,
        normalize_settings=_normalize_analysis_tags_settings,
        manifest_projection=DocsSubScopeManifestProjectionAspect(
            project=_project_analysis_tags_manifest,
        ),
        document_groups=DocsSubScopeDocumentGroupsAspect(
            resolve=_analysis_tags_document_groups,
        ),
        browser_composition=DocsSubScopeBrowserCompositionAspect(
            accesses=frozenset({MANAGE_ACCESS}),
        ),
    ),
    DOTLINEFORM_PROJECTS_CUSTOMISATION_ID: DocsSubScopeCustomisationDefinition(
        customisation_id=DOTLINEFORM_PROJECTS_CUSTOMISATION_ID,
        normalize_settings=dotlineform_projects.normalize_settings,
        manifest_projection=DocsSubScopeManifestProjectionAspect(
            project=dotlineform_projects.project_manifest,
        ),
        source_validation=DocsSubScopeSourceValidationAspect(
            validate=dotlineform_projects.validate_document,
        ),
        metadata=DocsSubScopeMetadataAspect(
            read_record=dotlineform_projects.metadata_record,
            normalize_update=dotlineform_projects.normalize_metadata_update,
        ),
        import_front_matter=DocsSubScopeImportFrontMatterAspect(
            normalize=dotlineform_projects.normalize_import_front_matter,
        ),
        browser_composition=DocsSubScopeBrowserCompositionAspect(
            accesses=frozenset({MANAGE_ACCESS}),
        ),
    ),
}


def _validate_owned_field_names(
    field_names: tuple[str, ...],
    *,
    field: str,
) -> None:
    if not isinstance(field_names, tuple) or not field_names:
        raise ValueError(f"{field} must be a non-empty tuple")
    seen_field_names: set[str] = set()
    for field_name in field_names:
        if not isinstance(field_name, str) or not CUSTOMISATION_ID_PATTERN.fullmatch(
            field_name
        ):
            raise ValueError(f"{field} contains an invalid field name")
        if field_name in seen_field_names:
            raise ValueError(f"{field} must not contain duplicates")
        seen_field_names.add(field_name)


def _validate_definition(
    registry_id: str,
    definition: DocsSubScopeCustomisationDefinition,
) -> DocsSubScopeCustomisationDefinition:
    field = f"Docs sub-scope customisation definition {registry_id!r}"
    if definition.customisation_id != registry_id:
        raise ValueError(f"{field} identity does not match its registry key")
    if not callable(definition.normalize_settings):
        raise ValueError(f"{field} normalize_settings must be callable")

    aspect_types = (
        (
            "manifest_projection",
            definition.manifest_projection,
            DocsSubScopeManifestProjectionAspect,
        ),
        (
            "document_groups",
            definition.document_groups,
            DocsSubScopeDocumentGroupsAspect,
        ),
        (
            "source_validation",
            definition.source_validation,
            DocsSubScopeSourceValidationAspect,
        ),
        ("metadata", definition.metadata, DocsSubScopeMetadataAspect),
        (
            "import_front_matter",
            definition.import_front_matter,
            DocsSubScopeImportFrontMatterAspect,
        ),
        (
            "browser_composition",
            definition.browser_composition,
            DocsSubScopeBrowserCompositionAspect,
        ),
        ("transfer", definition.transfer, DocsSubScopeTransferAspect),
    )
    for aspect_name, aspect, aspect_type in aspect_types:
        if aspect is not None and not isinstance(aspect, aspect_type):
            raise ValueError(f"{field} {aspect_name} contains an invalid aspect")

    aspect_callbacks = (
        (
            "manifest_projection.project",
            definition.manifest_projection.project
            if definition.manifest_projection is not None
            else None,
        ),
        (
            "document_groups.resolve",
            definition.document_groups.resolve
            if definition.document_groups is not None
            else None,
        ),
        (
            "source_validation.validate",
            definition.source_validation.validate
            if definition.source_validation is not None
            else None,
        ),
        (
            "metadata.read_record",
            definition.metadata.read_record
            if definition.metadata is not None
            else None,
        ),
        (
            "import_front_matter.normalize",
            definition.import_front_matter.normalize
            if definition.import_front_matter is not None
            else None,
        ),
    )
    for callback_name, callback in aspect_callbacks:
        if callback is not None and not callable(callback):
            raise ValueError(f"{field} {callback_name} must be callable")
    metadata = definition.metadata
    if (
        metadata is not None
        and metadata.normalize_update is not None
        and not callable(metadata.normalize_update)
    ):
        raise ValueError(f"{field} metadata.normalize_update must be callable")

    browser = definition.browser_composition
    manifest = definition.manifest_projection
    if browser is None:
        if manifest is not None:
            raise ValueError(f"{field} manifest_projection requires browser_composition")
    else:
        accesses = browser.accesses
        if not isinstance(accesses, frozenset) or not accesses:
            raise ValueError(
                f"{field} browser_composition accesses must be a non-empty frozenset"
            )
        if any(not isinstance(access, str) for access in accesses):
            raise ValueError(
                f"{field} browser_composition contains an invalid access"
            )
        unknown_accesses = sorted(accesses - SUPPORTED_BROWSER_ACCESSES)
        if unknown_accesses:
            raise ValueError(
                f"{field} browser_composition contains unknown access: "
                f"{', '.join(unknown_accesses)}"
            )
        if manifest is None:
            raise ValueError(f"{field} browser_composition requires manifest_projection")

    if not isinstance(definition.assignable_field_groups, tuple):
        raise ValueError(f"{field} assignable_field_groups must be a tuple")
    seen_group_ids: set[str] = set()
    for group in definition.assignable_field_groups:
        group_field = f"{field} assignable_field_groups"
        if not isinstance(group, DocsSubScopeAssignableFieldGroup):
            raise ValueError(f"{group_field} contains an invalid declaration")
        if not isinstance(
            group.group_id,
            str,
        ) or not CUSTOMISATION_ID_PATTERN.fullmatch(group.group_id):
            raise ValueError(f"{group_field} contains an invalid group id")
        if group.group_id in seen_group_ids:
            raise ValueError(f"{group_field} contains duplicate group ids")
        seen_group_ids.add(group.group_id)
        _validate_owned_field_names(
            group.field_names,
            field=f"{group_field} {group.group_id!r} field_names",
        )
    if definition.assignable_field_groups and (
        browser is None or MANAGE_ACCESS not in browser.accesses
    ):
        raise ValueError(f"{field} assignable_field_groups require Manage browser access")

    transfer = definition.transfer
    if transfer is not None:
        if not isinstance(
            transfer.contract_id,
            str,
        ) or not CUSTOMISATION_ID_PATTERN.fullmatch(transfer.contract_id):
            raise ValueError(f"{field} transfer contains an invalid contract id")
        _validate_owned_field_names(
            transfer.owned_field_names,
            field=f"{field} transfer owned_field_names",
        )
    return definition


def _definition_for(
    customisation: DocsSubScopeCustomisationConfig,
) -> DocsSubScopeCustomisationDefinition:
    definition = SUB_SCOPE_CUSTOMISATION_DEFINITIONS.get(
        customisation.customisation_id
    )
    if definition is None:
        raise ValueError(
            "Docs sub-scope customisation is not registered: "
            f"{customisation.customisation_id}"
        )
    return _validate_definition(customisation.customisation_id, definition)


def normalize_docs_subscope_customisation(
    raw: Any,
    *,
    field: str,
) -> DocsSubScopeCustomisationConfig | None:
    if raw is None:
        return None
    value = _strict_object(raw, field=field, keys={"id", "settings"})
    customisation_id = str(value.get("id") or "").strip()
    if not CUSTOMISATION_ID_PATTERN.fullmatch(customisation_id):
        raise ValueError(f"docs scope config field {field}.id is invalid")
    definition = SUB_SCOPE_CUSTOMISATION_DEFINITIONS.get(customisation_id)
    if definition is None:
        raise ValueError(
            f"docs scope config field {field}.id is unknown: {customisation_id!r}"
        )
    definition = _validate_definition(customisation_id, definition)
    return DocsSubScopeCustomisationConfig(
        customisation_id=customisation_id,
        settings=definition.normalize_settings(
            value["settings"],
            f"{field}.settings",
        ),
    )


def browser_sub_scope_customisation_payload(
    customisation: DocsSubScopeCustomisationConfig | None,
    *,
    published: bool,
) -> dict[str, Any] | None:
    if customisation is None:
        return None
    definition = _definition_for(customisation)
    browser = definition.browser_composition
    access = PUBLIC_ACCESS if published else MANAGE_ACCESS
    if browser is None or access not in browser.accesses:
        return None
    payload: dict[str, Any] = {"id": customisation.customisation_id}
    assignable_groups = definition.assignable_field_groups
    if not published and assignable_groups:
        payload["capabilities"] = {
            "assignable_field_groups": [
                group.group_id for group in assignable_groups
            ]
        }
    return payload


def sub_scope_customisation_assignable_field_groups(
    customisation: DocsSubScopeCustomisationConfig | None,
) -> tuple[DocsSubScopeAssignableFieldGroup, ...]:
    if customisation is None:
        return ()
    return _definition_for(customisation).assignable_field_groups


def sub_scope_customisation_transfer_contract(
    customisation: DocsSubScopeCustomisationConfig | None,
) -> DocsSubScopeTransferAspect | None:
    if customisation is None:
        return None
    return _definition_for(customisation).transfer


def sub_scope_customisation_document_groups(
    customisation: DocsSubScopeCustomisationConfig | None,
) -> tuple[str, ...]:
    """Return document-group choices owned by the selected customisation."""

    if customisation is None:
        return ()
    definition = _definition_for(customisation)
    aspect = definition.document_groups
    if aspect is None:
        return ()
    return aspect.resolve(customisation.settings)


def project_sub_scope_customisation_manifest(
    customisation: DocsSubScopeCustomisationConfig | None,
    documents: Sequence[Any],
    *,
    published: bool,
) -> dict[str, Any] | None:
    if customisation is None:
        return None
    definition = _definition_for(customisation)
    browser = definition.browser_composition
    access = PUBLIC_ACCESS if published else MANAGE_ACCESS
    if browser is None or access not in browser.accesses:
        return None
    aspect = definition.manifest_projection
    if aspect is None:
        raise ValueError(
            "Docs sub-scope customisation browser access has no manifest projection: "
            f"{customisation.customisation_id}"
        )
    return aspect.project(customisation.settings, documents)


def validate_sub_scope_customisation_document(
    customisation: DocsSubScopeCustomisationConfig | None,
    front_matter: Mapping[str, Any],
    *,
    doc_id: str,
) -> None:
    if customisation is None:
        return
    aspect = _definition_for(customisation).source_validation
    if aspect is not None:
        aspect.validate(
            customisation.settings,
            front_matter,
            doc_id=doc_id,
        )


def sub_scope_customisation_metadata_record(
    customisation: DocsSubScopeCustomisationConfig | None,
    front_matter: Mapping[str, Any],
    *,
    doc_id: str,
) -> dict[str, Any] | None:
    if customisation is None:
        return None
    aspect = _definition_for(customisation).metadata
    if aspect is None:
        return None
    return aspect.read_record(
        customisation.settings,
        front_matter,
        doc_id=doc_id,
    )


def normalize_sub_scope_customisation_metadata_update(
    customisation: DocsSubScopeCustomisationConfig | None,
    raw: Any,
    *,
    provided: bool,
    repo_root: Path,
    front_matter: Mapping[str, Any],
    doc_id: str,
) -> dict[str, Any] | None:
    if customisation is None:
        if provided:
            raise ValueError("customisation is not configured for this sub-scope")
        return None
    aspect = _definition_for(customisation).metadata
    if aspect is None or aspect.normalize_update is None:
        if provided:
            raise ValueError("customisation metadata is not editable for this sub-scope")
        return None
    if not provided:
        raise ValueError("customisation is required for this sub-scope metadata update")
    return aspect.normalize_update(
        customisation.settings,
        raw,
        repo_root=repo_root,
        front_matter=front_matter,
        doc_id=doc_id,
    )


def normalize_sub_scope_customisation_import_front_matter(
    customisation: DocsSubScopeCustomisationConfig | None,
    raw: Any,
    *,
    doc_id: str,
) -> dict[str, Any]:
    if customisation is None:
        raise ValueError("custom import front matter requires a configured sub-scope")
    aspect = _definition_for(customisation).import_front_matter
    if aspect is None:
        raise ValueError("custom import front matter is unavailable for this sub-scope")
    return aspect.normalize(
        customisation.settings,
        raw,
        doc_id=doc_id,
    )


def registered_sub_scope_customisation_access() -> dict[str, tuple[str, ...]]:
    access_by_id: dict[str, tuple[str, ...]] = {}
    for customisation_id, raw_definition in sorted(
        SUB_SCOPE_CUSTOMISATION_DEFINITIONS.items()
    ):
        definition = _validate_definition(customisation_id, raw_definition)
        browser = definition.browser_composition
        access_by_id[customisation_id] = tuple(
            sorted(browser.accesses if browser is not None else ())
        )
    return access_by_id


__all__ = [
    "ANALYSIS_TAGS_CUSTOMISATION_ID",
    "DOTLINEFORM_PROJECTS_CUSTOMISATION_ID",
    "DocsSubScopeAssignableFieldGroup",
    "DocsSubScopeBrowserCompositionAspect",
    "DocsSubScopeCustomisationConfig",
    "DocsSubScopeCustomisationDefinition",
    "DocsSubScopeDocumentGroupsAspect",
    "DocsSubScopeImportFrontMatterAspect",
    "DocsSubScopeManifestProjectionAspect",
    "DocsSubScopeMetadataAspect",
    "DocsSubScopeSourceValidationAspect",
    "DocsSubScopeTransferAspect",
    "browser_sub_scope_customisation_payload",
    "normalize_docs_subscope_customisation",
    "project_sub_scope_customisation_manifest",
    "registered_sub_scope_customisation_access",
    "normalize_sub_scope_customisation_metadata_update",
    "normalize_sub_scope_customisation_import_front_matter",
    "sub_scope_customisation_assignable_field_groups",
    "sub_scope_customisation_metadata_record",
    "sub_scope_customisation_document_groups",
    "sub_scope_customisation_transfer_contract",
    "validate_sub_scope_customisation_document",
]
