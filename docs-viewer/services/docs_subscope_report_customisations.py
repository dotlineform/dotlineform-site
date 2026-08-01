"""Registered Docs Viewer sub-scope report customisations."""

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


@dataclass(frozen=True)
class DocsSubScopeReportCustomisationConfig:
    customisation_id: str
    settings: Mapping[str, Any]


@dataclass(frozen=True)
class DocsSubScopeReportCustomisationDefinition:
    customisation_id: str
    normalize_settings: Callable[[Any, str], Mapping[str, Any]]
    document_groups: Callable[[Mapping[str, Any]], tuple[str, ...]] | None
    public_browser: bool
    manage_browser: bool
    project_manifest: Callable[[Mapping[str, Any], Sequence[Any]], dict[str, Any]]
    validate_document: Callable[..., None] | None = None
    metadata_record: Callable[..., dict[str, Any]] | None = None
    normalize_metadata_update: Callable[..., dict[str, Any]] | None = None
    collections: tuple[tuple[str, str], ...] | None = None


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


REPORT_CUSTOMISATION_DEFINITIONS = {
    ANALYSIS_TAGS_CUSTOMISATION_ID: DocsSubScopeReportCustomisationDefinition(
        customisation_id=ANALYSIS_TAGS_CUSTOMISATION_ID,
        normalize_settings=_normalize_analysis_tags_settings,
        document_groups=_analysis_tags_document_groups,
        public_browser=False,
        manage_browser=True,
        project_manifest=_project_analysis_tags_manifest,
    ),
    DOTLINEFORM_PROJECTS_CUSTOMISATION_ID: DocsSubScopeReportCustomisationDefinition(
        customisation_id=DOTLINEFORM_PROJECTS_CUSTOMISATION_ID,
        normalize_settings=dotlineform_projects.normalize_settings,
        document_groups=None,
        public_browser=False,
        manage_browser=True,
        project_manifest=dotlineform_projects.project_manifest,
        validate_document=dotlineform_projects.validate_document,
        metadata_record=dotlineform_projects.metadata_record,
        normalize_metadata_update=dotlineform_projects.normalize_metadata_update,
        collections=(("dotlineform", "projects"),),
    ),
}


def normalize_docs_subscope_report_customisation(
    raw: Any,
    *,
    field: str,
) -> DocsSubScopeReportCustomisationConfig | None:
    if raw is None:
        return None
    value = _strict_object(raw, field=field, keys={"id", "settings"})
    customisation_id = str(value.get("id") or "").strip()
    if not CUSTOMISATION_ID_PATTERN.fullmatch(customisation_id):
        raise ValueError(f"docs scope config field {field}.id is invalid")
    definition = REPORT_CUSTOMISATION_DEFINITIONS.get(customisation_id)
    if definition is None:
        raise ValueError(
            f"docs scope config field {field}.id is unknown: {customisation_id!r}"
        )
    return DocsSubScopeReportCustomisationConfig(
        customisation_id=customisation_id,
        settings=definition.normalize_settings(
            value["settings"],
            f"{field}.settings",
        ),
    )


def browser_report_customisation_payload(
    customisation: DocsSubScopeReportCustomisationConfig | None,
    *,
    published: bool,
) -> dict[str, str] | None:
    if customisation is None:
        return None
    definition = REPORT_CUSTOMISATION_DEFINITIONS[customisation.customisation_id]
    browser_enabled = definition.public_browser if published else definition.manage_browser
    if not browser_enabled:
        return None
    return {"id": customisation.customisation_id}


def validate_report_customisation_collection(
    customisation: DocsSubScopeReportCustomisationConfig | None,
    *,
    scope: str,
    sub_scope: str,
) -> None:
    if customisation is None:
        return
    definition = REPORT_CUSTOMISATION_DEFINITIONS[customisation.customisation_id]
    if definition.collections is None:
        return
    collection = (str(scope).strip().lower(), str(sub_scope).strip().lower())
    if collection not in definition.collections:
        raise ValueError(
            "docs sub-scope report customisation "
            f"{customisation.customisation_id!r} is unavailable for "
            f"{collection[0]}/{collection[1]}"
        )


def analysis_tags_groups(
    customisation: DocsSubScopeReportCustomisationConfig | None,
) -> tuple[str, ...]:
    if customisation is None or customisation.customisation_id != ANALYSIS_TAGS_CUSTOMISATION_ID:
        return ()
    return _analysis_tags_document_groups(customisation.settings)


def report_customisation_document_groups(
    customisation: DocsSubScopeReportCustomisationConfig | None,
) -> tuple[str, ...]:
    """Return document-group choices owned by the selected customisation."""

    if customisation is None:
        return ()
    definition = REPORT_CUSTOMISATION_DEFINITIONS.get(
        customisation.customisation_id
    )
    if definition is None:
        raise ValueError(
            "Docs sub-scope report customisation is not registered: "
            f"{customisation.customisation_id}"
        )
    if definition.document_groups is None:
        return ()
    return definition.document_groups(customisation.settings)


def project_report_customisation_manifest(
    customisation: DocsSubScopeReportCustomisationConfig | None,
    documents: Sequence[Any],
    *,
    published: bool,
) -> dict[str, Any] | None:
    if customisation is None:
        return None
    definition = REPORT_CUSTOMISATION_DEFINITIONS[customisation.customisation_id]
    projector_enabled = definition.public_browser if published else definition.manage_browser
    if not projector_enabled:
        return None
    return definition.project_manifest(customisation.settings, documents)


def validate_report_customisation_document(
    customisation: DocsSubScopeReportCustomisationConfig | None,
    front_matter: Mapping[str, Any],
    *,
    doc_id: str,
) -> None:
    if customisation is None:
        return
    definition = REPORT_CUSTOMISATION_DEFINITIONS[customisation.customisation_id]
    if definition.validate_document is not None:
        definition.validate_document(
            customisation.settings,
            front_matter,
            doc_id=doc_id,
        )


def report_customisation_metadata_record(
    customisation: DocsSubScopeReportCustomisationConfig | None,
    front_matter: Mapping[str, Any],
    *,
    doc_id: str,
) -> dict[str, Any] | None:
    if customisation is None:
        return None
    definition = REPORT_CUSTOMISATION_DEFINITIONS[customisation.customisation_id]
    if definition.metadata_record is None:
        return None
    return definition.metadata_record(
        customisation.settings,
        front_matter,
        doc_id=doc_id,
    )


def normalize_report_customisation_metadata_update(
    customisation: DocsSubScopeReportCustomisationConfig | None,
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
    definition = REPORT_CUSTOMISATION_DEFINITIONS[customisation.customisation_id]
    if definition.normalize_metadata_update is None:
        if provided:
            raise ValueError("customisation metadata is not editable for this sub-scope")
        return None
    if not provided:
        raise ValueError("customisation is required for this sub-scope metadata update")
    return definition.normalize_metadata_update(
        customisation.settings,
        raw,
        repo_root=repo_root,
        front_matter=front_matter,
        doc_id=doc_id,
    )


def registered_report_customisation_access() -> dict[str, tuple[str, ...]]:
    return {
        customisation_id: tuple(
            access
            for access, enabled in (
                ("public", definition.public_browser),
                ("manage", definition.manage_browser),
            )
            if enabled
        )
        for customisation_id, definition in sorted(
            REPORT_CUSTOMISATION_DEFINITIONS.items()
        )
    }


__all__ = [
    "ANALYSIS_TAGS_CUSTOMISATION_ID",
    "DOTLINEFORM_PROJECTS_CUSTOMISATION_ID",
    "DocsSubScopeReportCustomisationConfig",
    "analysis_tags_groups",
    "browser_report_customisation_payload",
    "normalize_docs_subscope_report_customisation",
    "project_report_customisation_manifest",
    "registered_report_customisation_access",
    "normalize_report_customisation_metadata_update",
    "report_customisation_metadata_record",
    "report_customisation_document_groups",
    "validate_report_customisation_document",
    "validate_report_customisation_collection",
]
