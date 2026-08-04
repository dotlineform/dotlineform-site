#!/usr/bin/env python3
"""Manage-only Projects report and authoring-subject customisation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from docs_local_links import (
    configured_base_dir,
    normalize_decoded_relative_target,
    normalize_structured_local_target_input,
)
from docs_document_subjects import (
    AUTHORING_SUBJECT_FIELDS,
    FOLDER_PATH_FIELD,
    SERIES_ID_FIELD,
    WORK_ID_FIELD,
    catalogue_subject_key_is_canonical,
    normalize_authoring_subject,
)


CUSTOMISATION_ID = "dotlineform_projects"


def normalize_settings(raw: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError(f"docs scope config field {field} must be an object")
    if raw:
        raise ValueError(
            f"docs scope config field {field} contains unknown fields: "
            + ", ".join(sorted(str(key) for key in raw))
        )
    return {}


def project_manifest(
    settings: Mapping[str, Any],
    documents: Sequence[Any],
) -> dict[str, Any]:
    if settings:
        raise ValueError("dotlineform_projects settings must be empty")
    rows: dict[str, dict[str, str]] = {}
    for document in documents:
        doc_id = str(getattr(document, "doc_id", "") or "").strip()
        front_matter = getattr(document, "front_matter", None)
        if not isinstance(front_matter, Mapping):
            raise ValueError(
                f"dotlineform_projects source metadata is unavailable for {doc_id!r}"
            )
        subject = normalize_authoring_subject(
            front_matter,
            folder_supported=True,
        )
        if subject["state"] == "valid" and subject["kind"] == "folder":
            rows[doc_id] = {FOLDER_PATH_FIELD: subject["key"]}
    return {
        "root": {"id": CUSTOMISATION_ID, "data": {}},
        "rows": rows,
    }


def metadata_record(
    settings: Mapping[str, Any],
    front_matter: Mapping[str, Any],
    *,
    doc_id: str,
) -> dict[str, str]:
    if settings:
        raise ValueError("dotlineform_projects settings must be empty")
    del doc_id
    subject = normalize_authoring_subject(front_matter, folder_supported=True)
    record = dict.fromkeys(AUTHORING_SUBJECT_FIELDS, "")
    if subject["state"] == "valid":
        field_name = subject["fields"][0]
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
    for field_name, kind in ((WORK_ID_FIELD, "work"), (SERIES_ID_FIELD, "series")):
        if values[field_name] and not catalogue_subject_key_is_canonical(
            kind,
            values[field_name],
        ):
            raise ValueError(f"{field}.{field_name} must be one canonical {kind} id")
    return values


def normalize_metadata_update(
    settings: Mapping[str, Any],
    raw: Any,
    *,
    repo_root: Path,
    front_matter: Mapping[str, Any],
    doc_id: str,
) -> dict[str, Any]:
    if settings:
        raise ValueError("dotlineform_projects settings must be empty")
    values = _strict_scalar_subject_fields(raw, field="customisation")
    if values[FOLDER_PATH_FIELD]:
        base_path = configured_base_dir(repo_root)
        try:
            values[FOLDER_PATH_FIELD] = normalize_structured_local_target_input(
                values[FOLDER_PATH_FIELD],
                base_path,
            )
        except ValueError as error:
            raise ValueError(f"customisation.folder_path is invalid: {error}") from error
    current = metadata_record(settings, front_matter, doc_id=doc_id)
    changed = values != current or normalize_authoring_subject(
        front_matter,
        folder_supported=True,
    )["state"] not in {"none", "valid"}
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
    """Validate optional Projects-owned front matter for create-only import."""

    if settings:
        raise ValueError("dotlineform_projects settings must be empty")
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
    for field_name, kind in ((WORK_ID_FIELD, "work"), (SERIES_ID_FIELD, "series")):
        if values[field_name] and not catalogue_subject_key_is_canonical(
            kind,
            values[field_name],
        ):
            raise ValueError(
                f"custom import {field_name} must be one canonical {kind} id"
            )
    if values[FOLDER_PATH_FIELD]:
        try:
            values[FOLDER_PATH_FIELD] = normalize_decoded_relative_target(
                values[FOLDER_PATH_FIELD]
            )
        except ValueError as error:
            raise ValueError(
                f"custom import folder_path is invalid for {doc_id!r}: {error}"
            ) from error
    return {
        field_name: value
        for field_name, value in values.items()
        if value
    }


__all__ = [
    "CUSTOMISATION_ID",
    "FOLDER_PATH_FIELD",
    "SERIES_ID_FIELD",
    "WORK_ID_FIELD",
    "metadata_record",
    "normalize_metadata_update",
    "normalize_import_front_matter",
    "normalize_settings",
    "project_manifest",
]
