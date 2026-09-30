#!/usr/bin/env python3
"""Single document Subject identities for authoring metadata and Links."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Mapping

from docs_local_links import normalize_decoded_relative_target


FOLDER_PATH_FIELD = "folder_path"
WORK_ID_FIELD = "work_id"
SERIES_ID_FIELD = "series_id"
AUTHORING_SUBJECT_FIELDS = (
    FOLDER_PATH_FIELD,
    WORK_ID_FIELD,
    SERIES_ID_FIELD,
)
SUBJECT_KIND_BY_FIELD = {
    FOLDER_PATH_FIELD: "folder",
    WORK_ID_FIELD: "work",
    SERIES_ID_FIELD: "series",
}
WORK_ID_PATTERN = re.compile(r"\A\d{5}\Z")
SERIES_ID_PATTERN = re.compile(r"\A[a-z0-9][a-z0-9-]*\Z")


def subject_key_is_canonical(kind: str, key: str) -> bool:
    """Validate exact non-Folder identity without consulting a registry."""
    if kind == "work":
        return WORK_ID_PATTERN.fullmatch(key) is not None
    if kind == "series":
        return SERIES_ID_PATTERN.fullmatch(key) is not None
    return False


def normalize_authoring_subject(
    front_matter: Mapping[str, Any],
    *,
    folder_supported: bool,
) -> dict[str, str]:
    """Project one Subject identity, rejecting invalid source declarations."""

    declared_fields = [
        field_name
        for field_name in AUTHORING_SUBJECT_FIELDS
        if field_name in front_matter
    ]
    if not declared_fields:
        return {"kind": "none", "key": ""}
    if len(declared_fields) > 1:
        raise ValueError("A document must declare at most one Subject")

    field_name = declared_fields[0]
    kind = SUBJECT_KIND_BY_FIELD[field_name]
    value = front_matter[field_name]
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"Document {field_name} must be one exact nonblank string")
    if field_name == FOLDER_PATH_FIELD:
        if not folder_supported:
            raise ValueError("This collection does not support Folder subjects")
        value = normalize_decoded_relative_target(value)
    elif not subject_key_is_canonical(kind, value):
        raise ValueError(f"Document {field_name} must be one canonical {kind} ID")
    return {"kind": kind, "key": value}


def project_reader_subject(front_matter: Mapping[str, Any]) -> dict[str, str] | None:
    """Project Work/Series identity for source authoring and publication inputs."""
    subject = normalize_authoring_subject(front_matter, folder_supported=True)
    if subject["kind"] not in {"work", "series"}:
        return None
    return subject


def subject_projection_generation(
    *,
    collection: str,
    subjects_by_doc_id: Mapping[str, Mapping[str, Any]],
) -> str:
    source = {
        "collection": collection,
        "documents": [
            {
                "doc_id": doc_id,
                "authoring_subject": subjects_by_doc_id[doc_id],
            }
            for doc_id in sorted(subjects_by_doc_id)
        ],
    }
    encoded = json.dumps(
        source,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


__all__ = [
    "AUTHORING_SUBJECT_FIELDS",
    "FOLDER_PATH_FIELD",
    "SERIES_ID_FIELD",
    "WORK_ID_FIELD",
    "subject_key_is_canonical",
    "normalize_authoring_subject",
    "project_reader_subject",
    "subject_projection_generation",
]
