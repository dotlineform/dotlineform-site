#!/usr/bin/env python3
"""Working Works Subject authoring and publication preparation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from docs_local_links import (
    configured_base_dir,
    normalize_structured_local_target_input,
)
from docs_document_subjects import (
    AUTHORING_SUBJECT_FIELDS,
    FOLDER_PATH_FIELD,
    WORK_ID_FIELD,
    subject_key_is_canonical,
    normalize_authoring_subject,
    project_reader_subject,
    SUBJECT_KIND_BY_FIELD,
)


CUSTOMISATION_ID = "working_works"


def publication_front_matter(front_matter: Mapping[str, Any]) -> dict[str, Any]:
    """Keep the Work Subject ID needed by publication rendering; omit Folder paths."""
    prepared = dict(front_matter)
    subject = project_reader_subject(front_matter)
    for field in AUTHORING_SUBJECT_FIELDS:
        prepared.pop(field, None)
    if subject is not None:
        prepared[WORK_ID_FIELD] = subject
    return prepared


def normalize_settings(raw: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError(f"Docs workspace config field {field} must be an object")
    if raw:
        raise ValueError(
            f"Docs workspace config field {field} contains unknown fields: "
            + ", ".join(sorted(str(key) for key in raw))
        )
    return {}


def metadata_record(
    settings: Mapping[str, Any],
    front_matter: Mapping[str, Any],
    *,
    doc_id: str,
    folder_supported: bool = True,
) -> dict[str, str]:
    if settings:
        raise ValueError("working_works settings must be empty")
    del doc_id
    subject = normalize_authoring_subject(front_matter, folder_supported=folder_supported)
    record = dict.fromkeys(AUTHORING_SUBJECT_FIELDS, "")
    if subject["kind"] != "none":
        field_name = next(field for field, kind in SUBJECT_KIND_BY_FIELD.items() if kind == subject["kind"])
        record[field_name] = subject["key"]
    return record


def _strict_scalar_subject_fields(raw: Any, *, field: str) -> dict[str, str]:
    if not isinstance(raw, dict):
        raise ValueError(f"{field} must be an object")
    if set(raw) != set(AUTHORING_SUBJECT_FIELDS):
        raise ValueError(
            f"{field} must contain exactly " + ", ".join(AUTHORING_SUBJECT_FIELDS)
        )
    values: dict[str, str] = {}
    for field_name in AUTHORING_SUBJECT_FIELDS:
        value = raw[field_name]
        if not isinstance(value, str):
            raise ValueError(f"{field}.{field_name} must be a scalar string")
        if value and value != value.strip():
            raise ValueError(f"{field}.{field_name} must be one exact nonblank string")
        values[field_name] = value
    if sum(bool(value) for value in values.values()) > 1:
        raise ValueError(f"{field} must select at most one authoring subject")
    if values[WORK_ID_FIELD] and not subject_key_is_canonical("work", values[WORK_ID_FIELD]):
        raise ValueError(f"{field}.{WORK_ID_FIELD} must be one canonical work id")
    return values


def normalize_metadata_update(
    settings: Mapping[str, Any],
    raw: Any,
    *,
    repo_root: Path,
    front_matter: Mapping[str, Any],
    doc_id: str,
    folder_supported: bool = True,
) -> dict[str, Any]:
    if settings:
        raise ValueError("working_works settings must be empty")
    values = _strict_scalar_subject_fields(raw, field="customisation")
    if values[FOLDER_PATH_FIELD] and not folder_supported:
        raise ValueError("This collection does not support Folder subjects")
    if values[FOLDER_PATH_FIELD]:
        base_path = configured_base_dir(repo_root)
        try:
            values[FOLDER_PATH_FIELD] = normalize_structured_local_target_input(
                values[FOLDER_PATH_FIELD],
                base_path,
            )
        except ValueError as error:
            raise ValueError(f"customisation.folder_path is invalid: {error}") from error
    normalize_authoring_subject(
        {field: value for field, value in values.items() if value}, folder_supported=folder_supported,
    )
    current = metadata_record(settings, front_matter, doc_id=doc_id, folder_supported=folder_supported)
    changed = values != current
    return {
        "front_matter_updates": {
            field_name: values[field_name] or None
            for field_name in AUTHORING_SUBJECT_FIELDS
        },
        "record": values,
        "changes": {"authoring_subject_changed": changed},
    }


def normalize_import_front_matter(
    settings: Mapping[str, Any],
    raw: Any,
    *,
    doc_id: str,
) -> dict[str, str]:
    """Validate optional Works-owned front matter for create-only import."""

    if settings:
        raise ValueError("working_works settings must be empty")
    if not isinstance(raw, dict):
        raise ValueError("custom import front matter must be an object")
    if set(raw) - set(AUTHORING_SUBJECT_FIELDS):
        raise ValueError("custom import front matter contains unknown fields")
    values = dict.fromkeys(AUTHORING_SUBJECT_FIELDS, "")
    for field_name, value in raw.items():
        if not isinstance(value, str):
            raise ValueError(f"custom import {field_name} must be a scalar string")
        if value and value != value.strip():
            raise ValueError(f"custom import {field_name} must be one exact nonblank string")
        values[field_name] = value
    if sum(bool(value) for value in values.values()) > 1:
        raise ValueError(
            f"custom import authoring subject is conflicting for {doc_id!r}"
        )
    declarations = {
        field_name: value
        for field_name, value in values.items()
        if value
    }
    normalize_authoring_subject(declarations, folder_supported=True)
    return declarations


__all__ = [
    "CUSTOMISATION_ID",
    "FOLDER_PATH_FIELD",
    "WORK_ID_FIELD",
    "metadata_record",
    "normalize_metadata_update",
    "normalize_import_front_matter",
    "normalize_settings",
]
