"""Registered Docs Viewer sub-scope report customisations."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Callable, Mapping, Sequence


CUSTOMISATION_ID_PATTERN = re.compile(r"\A[a-z][a-z0-9_]*\Z")
VALUE_ID_PATTERN = re.compile(r"\A[a-z0-9][a-z0-9_-]*\Z")
ANALYSIS_TAGS_CUSTOMISATION_ID = "analysis_tags"


@dataclass(frozen=True)
class DocsSubScopeReportCustomisationConfig:
    customisation_id: str
    settings: Mapping[str, Any]


@dataclass(frozen=True)
class DocsSubScopeReportCustomisationDefinition:
    customisation_id: str
    normalize_settings: Callable[[Any, str], Mapping[str, Any]]
    public_browser: bool
    manage_browser: bool


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


REPORT_CUSTOMISATION_DEFINITIONS = {
    ANALYSIS_TAGS_CUSTOMISATION_ID: DocsSubScopeReportCustomisationDefinition(
        customisation_id=ANALYSIS_TAGS_CUSTOMISATION_ID,
        normalize_settings=_normalize_analysis_tags_settings,
        public_browser=False,
        manage_browser=True,
    )
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


def analysis_tags_groups(
    customisation: DocsSubScopeReportCustomisationConfig | None,
) -> tuple[str, ...]:
    if customisation is None or customisation.customisation_id != ANALYSIS_TAGS_CUSTOMISATION_ID:
        return ()
    return tuple(str(value) for value in customisation.settings.get("groups", ()))


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
    if customisation.customisation_id != ANALYSIS_TAGS_CUSTOMISATION_ID:
        raise ValueError(
            f"Docs sub-scope report customisation projector is unavailable: "
            f"{customisation.customisation_id}"
        )
    groups = analysis_tags_groups(customisation)
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
    "DocsSubScopeReportCustomisationConfig",
    "analysis_tags_groups",
    "browser_report_customisation_payload",
    "normalize_docs_subscope_report_customisation",
    "project_report_customisation_manifest",
    "registered_report_customisation_access",
]
