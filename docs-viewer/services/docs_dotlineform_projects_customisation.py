#!/usr/bin/env python3
"""Manage-only Projects report and Folder Link metadata customisation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from docs_local_links import (
    configured_base_dir,
    normalize_decoded_relative_target,
    normalize_structured_local_target_input,
)


CUSTOMISATION_ID = "dotlineform_projects"
FOLDER_PATH_FIELD = "folder_path"


def normalize_settings(raw: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError(f"docs scope config field {field} must be an object")
    if raw:
        raise ValueError(
            f"docs scope config field {field} contains unknown fields: "
            + ", ".join(sorted(str(key) for key in raw))
        )
    return {}


def source_folder_path(front_matter: Mapping[str, Any], *, doc_id: str) -> str:
    if FOLDER_PATH_FIELD not in front_matter:
        return ""
    raw_value = front_matter[FOLDER_PATH_FIELD]
    if not isinstance(raw_value, str):
        raise ValueError(
            f"folder_path must be a scalar string for sub-scope doc {doc_id!r}"
        )
    try:
        return normalize_decoded_relative_target(raw_value)
    except ValueError as error:
        raise ValueError(
            f"Invalid folder_path for sub-scope doc {doc_id!r}: {error}"
        ) from error


def validate_document(
    settings: Mapping[str, Any],
    front_matter: Mapping[str, Any],
    *,
    doc_id: str,
) -> None:
    if settings:
        raise ValueError("dotlineform_projects settings must be empty")
    source_folder_path(front_matter, doc_id=doc_id)


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
        folder_path = source_folder_path(front_matter, doc_id=doc_id)
        if folder_path:
            rows[doc_id] = {FOLDER_PATH_FIELD: folder_path}
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
    return {FOLDER_PATH_FIELD: source_folder_path(front_matter, doc_id=doc_id)}


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
    if not isinstance(raw, dict):
        raise ValueError("customisation must be an object")
    if set(raw) != {FOLDER_PATH_FIELD}:
        raise ValueError("customisation must contain exactly folder_path")
    raw_folder_path = raw[FOLDER_PATH_FIELD]
    if not isinstance(raw_folder_path, str):
        raise ValueError("customisation.folder_path must be a scalar string")

    current_folder_path = source_folder_path(front_matter, doc_id=doc_id)
    folder_path = ""
    if raw_folder_path.strip():
        base_path = configured_base_dir(repo_root)
        try:
            folder_path = normalize_structured_local_target_input(
                raw_folder_path,
                base_path,
            )
        except ValueError as error:
            raise ValueError(f"customisation.folder_path is invalid: {error}") from error

    changed = folder_path != current_folder_path
    return {
        "front_matter_updates": {
            FOLDER_PATH_FIELD: folder_path or None,
        },
        "record": {FOLDER_PATH_FIELD: folder_path},
        "changes": {"folder_path_changed": changed},
    }


__all__ = [
    "CUSTOMISATION_ID",
    "metadata_record",
    "normalize_metadata_update",
    "normalize_settings",
    "project_manifest",
    "source_folder_path",
    "validate_document",
]
