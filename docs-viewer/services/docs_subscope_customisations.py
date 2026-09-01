"""Registered Docs Viewer sub-scope customisations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Callable, Mapping, Sequence

import docs_dotlineform_projects_customisation as dotlineform_projects
import docs_dotlineform_processing_customisation as dotlineform_processing
from docs_document_subjects import AUTHORING_SUBJECT_FIELDS
from docs_tag_documents import TAG_ID_FIELD, normalize_tag_declaration


CUSTOMISATION_ID_PATTERN = re.compile(r"\A[a-z][a-z0-9_]*\Z")
VALUE_ID_PATTERN = re.compile(r"\A[a-z0-9][a-z0-9_-]*\Z")
ANALYSIS_TAGS_CUSTOMISATION_ID = "analysis_tags"
ANALYSIS_WORKS_CUSTOMISATION_ID = "analysis_works"
DOTLINEFORM_PROJECTS_CUSTOMISATION_ID = dotlineform_projects.CUSTOMISATION_ID
DOTLINEFORM_PROCESSING_CUSTOMISATION_ID = dotlineform_processing.CUSTOMISATION_ID
PUBLIC_ACCESS = "public"
MANAGE_ACCESS = "manage"
SUPPORTED_BROWSER_ACCESSES = frozenset({PUBLIC_ACCESS, MANAGE_ACCESS})
LINEAGE_SOURCE_ROLE = "source"
LINEAGE_EDITORIAL_ROLE = "editorial"
SUPPORTED_LINEAGE_ROLES = frozenset({LINEAGE_SOURCE_ROLE, LINEAGE_EDITORIAL_ROLE})
PROJECTS_TO_ANALYSIS_WORKS_LINEAGE_CONTRACT = (
    dotlineform_projects.LINEAGE_CONTRACT_ID
)
PROCESSING_TO_ANALYSIS_WORKS_LINEAGE_CONTRACT = (
    dotlineform_processing.LINEAGE_CONTRACT_ID
)


@dataclass(frozen=True)
class DocsSubScopeCustomisationConfig:
    customisation_id: str
    settings: Mapping[str, Any]


@dataclass(frozen=True)
class DocsSubScopeManifestProjectionAspect:
    project: Callable[
        [Mapping[str, Any], Sequence[Any], Path, str, str],
        dict[str, Any],
    ]


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
class DocsSubScopeAuthoringSubjectAspect:
    field_names: tuple[str, ...]


@dataclass(frozen=True)
class DocsSubScopeTransferAspect:
    contract_id: str
    owned_field_names: tuple[str, ...]
    validate_field: Callable[[Mapping[str, Any], str, Any], None]


@dataclass(frozen=True)
class DocsSubScopeDocumentLineageAspect:
    contract_id: str
    role: str
    copy_action_label: str = ""
    copy_modal_title: str = ""


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
    authoring_subject: DocsSubScopeAuthoringSubjectAspect | None = None
    transfer: DocsSubScopeTransferAspect | None = None
    document_lineages: tuple[DocsSubScopeDocumentLineageAspect, ...] = ()


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


def _analysis_tags_metadata_record(
    settings: Mapping[str, Any],
    front_matter: Mapping[str, Any],
    *,
    doc_id: str,
) -> dict[str, Any]:
    del doc_id
    raw_group = front_matter.get("group")
    _validate_analysis_tags_transfer_field(settings, "group", raw_group)
    return {
        "group": str(raw_group or "").strip().lower(),
        TAG_ID_FIELD: front_matter.get(TAG_ID_FIELD, ""),
    }


def _normalize_analysis_tags_metadata_update(
    settings: Mapping[str, Any],
    raw: Any,
    *,
    repo_root: Path,
    front_matter: Mapping[str, Any],
    doc_id: str,
) -> dict[str, Any]:
    del repo_root
    if not isinstance(raw, dict):
        raise ValueError("customisation must be an object")
    if set(raw) != {"group", TAG_ID_FIELD}:
        raise ValueError("customisation must contain exactly group, tag_id")
    raw_group = raw["group"]
    if not isinstance(raw_group, str):
        raise ValueError("customisation.group must be a scalar string")
    group = raw_group.strip().lower()
    if raw_group != group:
        raise ValueError("customisation.group must be one exact configured group")
    _validate_analysis_tags_transfer_field(settings, "group", group)
    current_record = _analysis_tags_metadata_record(
        settings,
        front_matter,
        doc_id=doc_id,
    )
    raw_tag_id = raw[TAG_ID_FIELD]
    current_raw_tag_id = current_record[TAG_ID_FIELD]
    current_declaration = normalize_tag_declaration(front_matter)
    preserve_malformed = (
        current_declaration["state"] == "malformed"
        and raw_tag_id == current_raw_tag_id
    )
    if not preserve_malformed:
        if not isinstance(raw_tag_id, str):
            raise ValueError("customisation.tag_id must be a scalar string")
        if raw_tag_id:
            declaration = normalize_tag_declaration({TAG_ID_FIELD: raw_tag_id})
            if declaration["state"] != "valid":
                raise ValueError("customisation.tag_id must be one exact canonical tag id")
    desired_tag_id = raw_tag_id if preserve_malformed or raw_tag_id else None
    tag_id_changed = (
        (TAG_ID_FIELD in front_matter) != (desired_tag_id is not None)
        or (
            desired_tag_id is not None
            and desired_tag_id != front_matter.get(TAG_ID_FIELD)
        )
    )
    return {
        "front_matter_updates": {
            "group": group or None,
            TAG_ID_FIELD: desired_tag_id,
        },
        "record": {
            "group": group,
            TAG_ID_FIELD: raw_tag_id,
        },
        "changes": {
            "group_changed": group != current_record["group"],
            "tag_id_changed": tag_id_changed,
        },
    }


def _validate_analysis_tags_transfer_field(
    settings: Mapping[str, Any],
    field_name: str,
    value: Any,
) -> None:
    if field_name == TAG_ID_FIELD:
        normalize_tag_declaration({TAG_ID_FIELD: value})
        return
    if field_name != "group":
        raise ValueError(f"unsupported Analysis Tags field {field_name!r}")
    if value is None:
        return
    if not isinstance(value, str):
        raise ValueError("group must be a scalar string")
    normalized = value.strip().lower()
    if normalized and normalized not in _analysis_tags_document_groups(settings):
        raise ValueError(f"group {normalized!r} is not configured for the target")


def _validate_analysis_tags_source(
    settings: Mapping[str, Any],
    front_matter: Mapping[str, Any],
    *,
    doc_id: str,
) -> None:
    del settings, doc_id
    normalize_tag_declaration(front_matter)


def _normalize_analysis_tags_import_front_matter(
    settings: Mapping[str, Any],
    raw: Any,
    *,
    doc_id: str,
) -> dict[str, str]:
    del doc_id
    if not isinstance(raw, dict):
        raise ValueError("custom import front matter must be an object")
    if set(raw) - {"group", TAG_ID_FIELD}:
        raise ValueError("custom import front matter contains unknown fields")
    result: dict[str, str] = {}
    if "group" in raw:
        group = raw["group"]
        if not isinstance(group, str) or group != group.strip().lower():
            raise ValueError("custom import group must be one exact configured group")
        _validate_analysis_tags_transfer_field(settings, "group", group)
        if group:
            result["group"] = group
    if TAG_ID_FIELD in raw:
        tag_id = raw[TAG_ID_FIELD]
        if not isinstance(tag_id, str):
            raise ValueError("custom import tag_id must be a scalar string")
        if tag_id:
            declaration = normalize_tag_declaration({TAG_ID_FIELD: tag_id})
            if declaration["state"] != "valid":
                raise ValueError("custom import tag_id must be one exact canonical tag id")
            result[TAG_ID_FIELD] = tag_id
    return result


def _normalize_empty_settings(raw: Any, field: str) -> Mapping[str, Any]:
    settings = _strict_object(raw, field=field, keys=set())
    return settings


def _project_analysis_tags_manifest(
    settings: Mapping[str, Any],
    documents: Sequence[Any],
    repo_root: Path,
    scope: str,
    sub_scope: str,
) -> dict[str, Any]:
    del repo_root, scope, sub_scope
    groups = _analysis_tags_document_groups(settings)
    rows: dict[str, dict[str, Any]] = {}
    for document in documents:
        row: dict[str, Any] = {}
        group = str(getattr(document, "group", "") or "").strip()
        if group:
            row["group"] = group
        front_matter = getattr(document, "front_matter", {})
        if isinstance(front_matter, Mapping) and TAG_ID_FIELD in front_matter:
            row[TAG_ID_FIELD] = front_matter[TAG_ID_FIELD]
        if row:
            rows[str(document.doc_id)] = row
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
        source_validation=DocsSubScopeSourceValidationAspect(
            validate=_validate_analysis_tags_source,
        ),
        metadata=DocsSubScopeMetadataAspect(
            read_record=_analysis_tags_metadata_record,
            normalize_update=_normalize_analysis_tags_metadata_update,
        ),
        import_front_matter=DocsSubScopeImportFrontMatterAspect(
            normalize=_normalize_analysis_tags_import_front_matter,
        ),
        browser_composition=DocsSubScopeBrowserCompositionAspect(
            accesses=frozenset({MANAGE_ACCESS}),
        ),
        assignable_field_groups=(
            DocsSubScopeAssignableFieldGroup(
                group_id="tag_fields",
                field_names=("group", TAG_ID_FIELD),
            ),
        ),
        transfer=DocsSubScopeTransferAspect(
            contract_id="analysis_tag_fields",
            owned_field_names=("group", TAG_ID_FIELD),
            validate_field=_validate_analysis_tags_transfer_field,
        ),
    ),
    ANALYSIS_WORKS_CUSTOMISATION_ID: DocsSubScopeCustomisationDefinition(
        customisation_id=ANALYSIS_WORKS_CUSTOMISATION_ID,
        normalize_settings=_normalize_empty_settings,
        authoring_subject=DocsSubScopeAuthoringSubjectAspect(
            field_names=AUTHORING_SUBJECT_FIELDS,
        ),
        document_lineages=(
            DocsSubScopeDocumentLineageAspect(
                contract_id=PROJECTS_TO_ANALYSIS_WORKS_LINEAGE_CONTRACT,
                role=LINEAGE_EDITORIAL_ROLE,
            ),
            DocsSubScopeDocumentLineageAspect(
                contract_id=PROCESSING_TO_ANALYSIS_WORKS_LINEAGE_CONTRACT,
                role=LINEAGE_EDITORIAL_ROLE,
            ),
        ),
    ),
    DOTLINEFORM_PROJECTS_CUSTOMISATION_ID: DocsSubScopeCustomisationDefinition(
        customisation_id=DOTLINEFORM_PROJECTS_CUSTOMISATION_ID,
        normalize_settings=dotlineform_projects.normalize_settings,
        manifest_projection=DocsSubScopeManifestProjectionAspect(
            project=dotlineform_projects.project_manifest,
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
        assignable_field_groups=(
            DocsSubScopeAssignableFieldGroup(
                group_id="authoring_subject",
                field_names=(
                    dotlineform_projects.FOLDER_PATH_FIELD,
                    dotlineform_projects.WORK_ID_FIELD,
                    dotlineform_projects.SERIES_ID_FIELD,
                ),
            ),
        ),
        authoring_subject=DocsSubScopeAuthoringSubjectAspect(
            field_names=AUTHORING_SUBJECT_FIELDS,
        ),
        document_lineages=(
            DocsSubScopeDocumentLineageAspect(
                contract_id=PROJECTS_TO_ANALYSIS_WORKS_LINEAGE_CONTRACT,
                role=LINEAGE_SOURCE_ROLE,
                copy_action_label="Copy to Analysis",
                copy_modal_title="Copy to analysis/works",
            ),
        ),
    ),
    DOTLINEFORM_PROCESSING_CUSTOMISATION_ID: DocsSubScopeCustomisationDefinition(
        customisation_id=DOTLINEFORM_PROCESSING_CUSTOMISATION_ID,
        normalize_settings=dotlineform_processing.normalize_settings,
        manifest_projection=DocsSubScopeManifestProjectionAspect(
            project=dotlineform_processing.project_manifest,
        ),
        metadata=DocsSubScopeMetadataAspect(
            read_record=dotlineform_processing.metadata_record,
            normalize_update=dotlineform_processing.normalize_metadata_update,
        ),
        import_front_matter=DocsSubScopeImportFrontMatterAspect(
            normalize=dotlineform_processing.normalize_import_front_matter,
        ),
        browser_composition=DocsSubScopeBrowserCompositionAspect(
            accesses=frozenset({MANAGE_ACCESS}),
        ),
        assignable_field_groups=(
            DocsSubScopeAssignableFieldGroup(
                group_id="authoring_subject",
                field_names=(
                    dotlineform_processing.FOLDER_PATH_FIELD,
                    dotlineform_processing.WORK_ID_FIELD,
                    dotlineform_processing.SERIES_ID_FIELD,
                ),
            ),
        ),
        authoring_subject=DocsSubScopeAuthoringSubjectAspect(
            field_names=AUTHORING_SUBJECT_FIELDS,
        ),
        document_lineages=(
            DocsSubScopeDocumentLineageAspect(
                contract_id=PROCESSING_TO_ANALYSIS_WORKS_LINEAGE_CONTRACT,
                role=LINEAGE_SOURCE_ROLE,
                copy_action_label="Copy to Analysis",
                copy_modal_title="Copy to analysis/works",
            ),
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
        (
            "authoring_subject",
            definition.authoring_subject,
            DocsSubScopeAuthoringSubjectAspect,
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
        if set(transfer.owned_field_names) & set(AUTHORING_SUBJECT_FIELDS):
            raise ValueError(
                f"{field} transfer must not own shared authoring-subject fields"
            )
        if not callable(transfer.validate_field):
            raise ValueError(f"{field} transfer validate_field must be callable")

    document_lineages = definition.document_lineages
    if not isinstance(document_lineages, tuple):
        raise ValueError(f"{field} document_lineages must be a tuple")
    seen_lineage_contracts: set[str] = set()
    for document_lineage in document_lineages:
        if not isinstance(document_lineage, DocsSubScopeDocumentLineageAspect):
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
        presentation_values = (
            document_lineage.copy_action_label,
            document_lineage.copy_modal_title,
        )
        if document_lineage.role == LINEAGE_SOURCE_ROLE:
            if any(
                not isinstance(value, str) or not value.strip() or value != value.strip()
                for value in presentation_values
            ):
                raise ValueError(
                    f"{field} source document_lineages require exact Copy presentation"
                )
        elif any(presentation_values):
            raise ValueError(
                f"{field} Editorial document_lineages must not declare Copy presentation"
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


def sub_scope_customisation_authoring_subject_fields(
    customisation: DocsSubScopeCustomisationConfig | None,
) -> tuple[str, ...]:
    if customisation is None:
        return ()
    aspect = _definition_for(customisation).authoring_subject
    return aspect.field_names if aspect is not None else ()


def sub_scope_customisation_transfer_contract(
    customisation: DocsSubScopeCustomisationConfig | None,
) -> DocsSubScopeTransferAspect | None:
    if customisation is None:
        return None
    return _definition_for(customisation).transfer


def sub_scope_customisation_document_lineage_contracts(
    customisation: DocsSubScopeCustomisationConfig | None,
) -> tuple[DocsSubScopeDocumentLineageAspect, ...]:
    if customisation is None:
        return ()
    return _definition_for(customisation).document_lineages


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
    repo_root: Path,
    scope: str,
    sub_scope: str,
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
    return aspect.project(
        customisation.settings,
        documents,
        repo_root,
        scope,
        sub_scope,
    )


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
        return None
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
    "ANALYSIS_WORKS_CUSTOMISATION_ID",
    "DOTLINEFORM_PROJECTS_CUSTOMISATION_ID",
    "DOTLINEFORM_PROCESSING_CUSTOMISATION_ID",
    "DocsSubScopeAssignableFieldGroup",
    "DocsSubScopeAuthoringSubjectAspect",
    "DocsSubScopeBrowserCompositionAspect",
    "DocsSubScopeCustomisationConfig",
    "DocsSubScopeCustomisationDefinition",
    "DocsSubScopeDocumentGroupsAspect",
    "DocsSubScopeDocumentLineageAspect",
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
    "sub_scope_customisation_authoring_subject_fields",
    "sub_scope_customisation_metadata_record",
    "sub_scope_customisation_document_groups",
    "sub_scope_customisation_document_lineage_contracts",
    "sub_scope_customisation_transfer_contract",
    "validate_sub_scope_customisation_document",
]
