"""Registered Docs Viewer collection customisations."""

from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from pathlib import Path
import re
from typing import Any, Callable, Mapping

import docs_working_works_customisation as working_works
from docs_document_subjects import AUTHORING_SUBJECT_FIELDS, FOLDER_PATH_FIELD


CUSTOMISATION_ID_PATTERN = re.compile(r"\A[a-z][a-z0-9_]*\Z")
PREVIEW_WORKS_CUSTOMISATION_ID = "preview_works"
WORKING_WORKS_CUSTOMISATION_ID = working_works.CUSTOMISATION_ID
LINEAGE_SOURCE_ROLE = "source"
LINEAGE_EDITORIAL_ROLE = "editorial"
SUPPORTED_LINEAGE_ROLES = frozenset({LINEAGE_SOURCE_ROLE, LINEAGE_EDITORIAL_ROLE})


@dataclass(frozen=True)
class DocsCollectionCustomisationConfig:
    customisation_id: str
    settings: Mapping[str, Any]


@dataclass(frozen=True)
class DocsCollectionMetadataAspect:
    read_record: Callable[..., dict[str, Any]]
    normalize_update: Callable[..., dict[str, Any]] | None = None


@dataclass(frozen=True)
class DocsCollectionImportFrontMatterAspect:
    normalize: Callable[..., dict[str, Any]]


@dataclass(frozen=True)
class DocsCollectionAssignableFieldGroup:
    group_id: str
    field_names: tuple[str, ...]


@dataclass(frozen=True)
class DocsCollectionAuthoringSubjectAspect:
    field_names: tuple[str, ...]


@dataclass(frozen=True)
class DocsCollectionDocumentLineageAspect:
    contract_id: str
    role: str


@dataclass(frozen=True)
class DocsCollectionCustomisationDefinition:
    customisation_id: str
    normalize_settings: Callable[[Any, str], Mapping[str, Any]]
    metadata: DocsCollectionMetadataAspect | None = None
    import_front_matter: DocsCollectionImportFrontMatterAspect | None = None
    assignable_field_groups: tuple[DocsCollectionAssignableFieldGroup, ...] = ()
    authoring_subject: DocsCollectionAuthoringSubjectAspect | None = None
    document_lineages: tuple[DocsCollectionDocumentLineageAspect, ...] = ()
    prepare_publication: Callable[[Mapping[str, Any]], dict[str, Any]] | None = None


def _strict_object(raw: Any, *, field: str, keys: set[str]) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError(f"Docs workspace config field {field} must be an object")
    unknown = sorted(set(raw) - keys)
    if unknown:
        raise ValueError(
            f"Docs workspace config field {field} contains unknown fields: "
            f"{', '.join(unknown)}"
        )
    missing = sorted(keys - set(raw))
    if missing:
        raise ValueError(
            f"Docs workspace config field {field} is missing required fields: "
            f"{', '.join(missing)}"
        )
    return raw


def _normalize_empty_settings(raw: Any, field: str) -> Mapping[str, Any]:
    settings = _strict_object(raw, field=field, keys=set())
    return settings


COLLECTION_CUSTOMISATION_DEFINITIONS = {
    PREVIEW_WORKS_CUSTOMISATION_ID: DocsCollectionCustomisationDefinition(
        customisation_id=PREVIEW_WORKS_CUSTOMISATION_ID,
        normalize_settings=_normalize_empty_settings,
        authoring_subject=DocsCollectionAuthoringSubjectAspect(
            field_names=tuple(field for field in AUTHORING_SUBJECT_FIELDS if field != FOLDER_PATH_FIELD),
        ),
        metadata=DocsCollectionMetadataAspect(
            read_record=partial(working_works.metadata_record, folder_supported=False),
            normalize_update=partial(working_works.normalize_metadata_update, folder_supported=False),
        ),
        assignable_field_groups=(
            DocsCollectionAssignableFieldGroup(
                group_id="authoring_subject",
                # Include blank Folder in replacement writes so old declarations can be cleared.
                field_names=AUTHORING_SUBJECT_FIELDS,
            ),
        ),
    ),
    WORKING_WORKS_CUSTOMISATION_ID: DocsCollectionCustomisationDefinition(
        customisation_id=WORKING_WORKS_CUSTOMISATION_ID,
        prepare_publication=working_works.publication_front_matter,
        normalize_settings=working_works.normalize_settings,
        metadata=DocsCollectionMetadataAspect(
            read_record=working_works.metadata_record,
            normalize_update=working_works.normalize_metadata_update,
        ),
        import_front_matter=DocsCollectionImportFrontMatterAspect(
            normalize=working_works.normalize_import_front_matter,
        ),
        assignable_field_groups=(
            DocsCollectionAssignableFieldGroup(
                group_id="authoring_subject",
                field_names=AUTHORING_SUBJECT_FIELDS,
            ),
        ),
        authoring_subject=DocsCollectionAuthoringSubjectAspect(
            field_names=AUTHORING_SUBJECT_FIELDS,
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
    definition: DocsCollectionCustomisationDefinition,
) -> DocsCollectionCustomisationDefinition:
    field = f"Docs collection customisation definition {registry_id!r}"
    if definition.customisation_id != registry_id:
        raise ValueError(f"{field} identity does not match its registry key")
    if not callable(definition.normalize_settings):
        raise ValueError(f"{field} normalize_settings must be callable")
    if definition.prepare_publication is not None and not callable(definition.prepare_publication):
        raise ValueError(f"{field} prepare_publication must be callable")

    aspect_types = (
        ("metadata", definition.metadata, DocsCollectionMetadataAspect),
        (
            "import_front_matter",
            definition.import_front_matter,
            DocsCollectionImportFrontMatterAspect,
        ),
        (
            "authoring_subject",
            definition.authoring_subject,
            DocsCollectionAuthoringSubjectAspect,
        ),
    )
    for aspect_name, aspect, aspect_type in aspect_types:
        if aspect is not None and not isinstance(aspect, aspect_type):
            raise ValueError(f"{field} {aspect_name} contains an invalid aspect")

    aspect_callbacks = (
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

    if not isinstance(definition.assignable_field_groups, tuple):
        raise ValueError(f"{field} assignable_field_groups must be a tuple")
    seen_group_ids: set[str] = set()
    for group in definition.assignable_field_groups:
        group_field = f"{field} assignable_field_groups"
        if not isinstance(group, DocsCollectionAssignableFieldGroup):
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
    authoring_subject = definition.authoring_subject
    if authoring_subject is not None:
        _validate_owned_field_names(
            authoring_subject.field_names,
            field=f"{field} authoring_subject field_names",
        )
        unknown_subject_fields = sorted(
            set(authoring_subject.field_names) - set(AUTHORING_SUBJECT_FIELDS)
        )
        if unknown_subject_fields:
            raise ValueError(
                f"{field} authoring_subject contains unknown fields: "
                f"{', '.join(unknown_subject_fields)}"
            )

    document_lineages = definition.document_lineages
    if not isinstance(document_lineages, tuple):
        raise ValueError(f"{field} document_lineages must be a tuple")
    seen_lineage_contracts: set[str] = set()
    for document_lineage in document_lineages:
        if not isinstance(document_lineage, DocsCollectionDocumentLineageAspect):
            raise ValueError(f"{field} document_lineages contains an invalid aspect")
        if not isinstance(
            document_lineage.contract_id,
            str,
        ) or not CUSTOMISATION_ID_PATTERN.fullmatch(document_lineage.contract_id):
            raise ValueError(
                f"{field} document_lineages contains an invalid contract id"
            )
        if document_lineage.contract_id in seen_lineage_contracts:
            raise ValueError(
                f"{field} document_lineages contains a duplicate contract id"
            )
        seen_lineage_contracts.add(document_lineage.contract_id)
        if document_lineage.role not in SUPPORTED_LINEAGE_ROLES:
            raise ValueError(f"{field} document_lineages contains an invalid role")
    return definition


def _definition_for(
    customisation: DocsCollectionCustomisationConfig,
) -> DocsCollectionCustomisationDefinition:
    definition = COLLECTION_CUSTOMISATION_DEFINITIONS.get(
        customisation.customisation_id
    )
    if definition is None:
        raise ValueError(
            "Docs collection customisation is not registered: "
            f"{customisation.customisation_id}"
        )
    return _validate_definition(customisation.customisation_id, definition)


def normalize_docs_collection_customisation(
    raw: Any,
    *,
    field: str,
) -> DocsCollectionCustomisationConfig | None:
    if raw is None:
        return None
    value = _strict_object(raw, field=field, keys={"id", "settings"})
    customisation_id = str(value.get("id") or "").strip()
    if not CUSTOMISATION_ID_PATTERN.fullmatch(customisation_id):
        raise ValueError(f"Docs workspace config field {field}.id is invalid")
    definition = COLLECTION_CUSTOMISATION_DEFINITIONS.get(customisation_id)
    if definition is None:
        raise ValueError(
            f"Docs workspace config field {field}.id is unknown: {customisation_id!r}"
        )
    definition = _validate_definition(customisation_id, definition)
    return DocsCollectionCustomisationConfig(
        customisation_id=customisation_id,
        settings=definition.normalize_settings(
            value["settings"],
            f"{field}.settings",
        ),
    )


def collection_customisation_assignable_field_groups(
    customisation: DocsCollectionCustomisationConfig | None,
) -> tuple[DocsCollectionAssignableFieldGroup, ...]:
    if customisation is None:
        return ()
    return _definition_for(customisation).assignable_field_groups


def collection_customisation_authoring_subject_fields(
    customisation: DocsCollectionCustomisationConfig | None,
) -> tuple[str, ...]:
    if customisation is None:
        return ()
    aspect = _definition_for(customisation).authoring_subject
    return aspect.field_names if aspect is not None else ()


def prepare_collection_publication(
    customisation: DocsCollectionCustomisationConfig | None,
    front_matter: Mapping[str, Any],
) -> dict[str, Any]:
    """Delegate publication projection only to the configured collection owner."""
    prepare = _definition_for(customisation).prepare_publication if customisation is not None else None
    return prepare(front_matter) if prepare is not None else dict(front_matter)


def collection_customisation_document_lineage_contracts(
    customisation: DocsCollectionCustomisationConfig | None,
) -> tuple[DocsCollectionDocumentLineageAspect, ...]:
    if customisation is None:
        return ()
    return _definition_for(customisation).document_lineages


def collection_customisation_metadata_record(
    customisation: DocsCollectionCustomisationConfig | None,
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


def normalize_collection_customisation_metadata_update(
    customisation: DocsCollectionCustomisationConfig | None,
    raw: Any,
    *,
    provided: bool,
    repo_root: Path,
    front_matter: Mapping[str, Any],
    doc_id: str,
) -> dict[str, Any] | None:
    if customisation is None:
        if provided:
            raise ValueError("customisation is not configured for this collection")
        return None
    aspect = _definition_for(customisation).metadata
    if aspect is None or aspect.normalize_update is None:
        if provided:
            raise ValueError("customisation metadata is not editable for this collection")
        return None
    if not provided:
        return None
    return aspect.normalize_update(
        customisation.settings,
        raw,
        repo_root=repo_root,
        front_matter=front_matter,
        doc_id=doc_id,
    )


def normalize_collection_customisation_import_front_matter(
    customisation: DocsCollectionCustomisationConfig | None,
    raw: Any,
    *,
    doc_id: str,
) -> dict[str, Any]:
    if customisation is None:
        raise ValueError("custom import front matter requires a configured collection")
    aspect = _definition_for(customisation).import_front_matter
    if aspect is None:
        raise ValueError("custom import front matter is unavailable for this collection")
    return aspect.normalize(
        customisation.settings,
        raw,
        doc_id=doc_id,
    )


__all__ = [
    "PREVIEW_WORKS_CUSTOMISATION_ID",
    "WORKING_WORKS_CUSTOMISATION_ID",
    "DocsCollectionAssignableFieldGroup",
    "DocsCollectionAuthoringSubjectAspect",
    "DocsCollectionCustomisationConfig",
    "DocsCollectionCustomisationDefinition",
    "DocsCollectionDocumentLineageAspect",
    "DocsCollectionImportFrontMatterAspect",
    "DocsCollectionMetadataAspect",
    "normalize_docs_collection_customisation",
    "normalize_collection_customisation_metadata_update",
    "normalize_collection_customisation_import_front_matter",
    "collection_customisation_assignable_field_groups",
    "collection_customisation_authoring_subject_fields",
    "collection_customisation_metadata_record",
    "collection_customisation_document_lineage_contracts",
    "prepare_collection_publication",
]
