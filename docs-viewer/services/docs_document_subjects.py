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
AUTHORING_SUBJECT_FIELDS = (
    FOLDER_PATH_FIELD,
    WORK_ID_FIELD,
)
SUBJECT_KIND_BY_FIELD = {
    FOLDER_PATH_FIELD: "folder",
    WORK_ID_FIELD: "work",
}
WORK_ID_PATTERN = re.compile(r"\A[0-9]{5}\Z")


def subject_key_is_canonical(kind: str, key: str) -> bool:
    """Validate exact non-Folder identity without consulting a registry."""
    if kind == "work":
        return WORK_ID_PATTERN.fullmatch(key) is not None
    return False


def validate_document_subject_fields(front_matter: Mapping[str, Any]) -> None:
    """Reject retired Subject fields even when no current Subject is declared."""
    if "series_id" in front_matter:
        raise ValueError("Document Series subjects are retired; use work_id or folder_path")


def normalize_authoring_subject(
    front_matter: Mapping[str, Any],
    *,
    folder_supported: bool,
) -> dict[str, str]:
    """Project one Subject identity, rejecting invalid source declarations."""

    validate_document_subject_fields(front_matter)
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
        if subject_key_is_canonical("work", value):
            raise ValueError("A bare five-digit Folder subject is reserved for Work identity")
    elif not subject_key_is_canonical(kind, value):
        raise ValueError(f"Document {field_name} must be one canonical {kind} ID")
    return {"kind": kind, "key": value}


def project_document_subject(
    front_matter: Mapping[str, Any], *, folder_supported: bool,
) -> str | None:
    """Project an optional scalar; callers omit the field for an unassigned source."""
    subject = normalize_authoring_subject(front_matter, folder_supported=folder_supported)
    return subject["key"] if subject["kind"] != "none" else None


def subject_from_record(
    record: Mapping[str, Any], *, folder_supported: bool,
) -> dict[str, str]:
    """Classify optional scalar metadata, rejecting present invalid or retired shapes.

    Absence means None only in management inputs. Public Context may omit a Work
    subject because an authored thumbnail takes precedence. No registry is read.
    """
    if "authoring_subject" in record:
        raise ValueError("Generated authoring_subject is retired; run a complete collection Build")
    if "subject" not in record:
        return {"kind": "none", "key": ""}
    value = record["subject"]
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError("Document subject must be one exact nonblank string")
    if subject_key_is_canonical("work", value):
        return {"kind": "work", "key": value}
    if not folder_supported:
        raise ValueError("This collection does not support Folder subjects")
    return {"kind": "folder", "key": normalize_decoded_relative_target(value)}


def project_reader_subject(front_matter: Mapping[str, Any]) -> str | None:
    """Project the optional Work scalar for source context and publication inputs."""
    subject = normalize_authoring_subject(front_matter, folder_supported=True)
    if subject["kind"] != "work":
        return None
    return subject["key"]


def subject_projection_generation(
    *,
    collection: str,
    subjects_by_doc_id: Mapping[str, str | None],
) -> str:
    """Hash collection identity and scalar Subjects, including unassigned document IDs."""
    source = {
        "collection": collection,
        "documents": [
            {
                "doc_id": doc_id,
                **({"subject": subjects_by_doc_id[doc_id]} if subjects_by_doc_id[doc_id] is not None else {}),
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
    "WORK_ID_FIELD",
    "subject_key_is_canonical",
    "validate_document_subject_fields",
    "normalize_authoring_subject",
    "project_document_subject",
    "subject_from_record",
    "project_reader_subject",
    "subject_projection_generation",
]
