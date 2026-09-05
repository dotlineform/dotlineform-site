#!/usr/bin/env python3
"""Normalized document authoring subjects and private association projections."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Mapping, Sequence

from docs_local_links import normalize_decoded_relative_target


FOLDER_PATH_FIELD = "folder_path"
WORK_ID_FIELD = "work_id"
SERIES_ID_FIELD = "series_id"
DETAIL_UID_FIELD = "detail_uid"
AUTHORING_SUBJECT_FIELDS = (
    FOLDER_PATH_FIELD,
    WORK_ID_FIELD,
    SERIES_ID_FIELD,
    DETAIL_UID_FIELD,
)
SUBJECT_KIND_BY_FIELD = {
    FOLDER_PATH_FIELD: "folder",
    WORK_ID_FIELD: "work",
    SERIES_ID_FIELD: "series",
    DETAIL_UID_FIELD: "detail",
}
SUBJECT_ASSOCIATIONS_SCHEMA_VERSION = "docs_subject_associations_v1"
WORK_ID_PATTERN = re.compile(r"\A\d{5}\Z")
SERIES_ID_PATTERN = re.compile(r"\A[a-z0-9][a-z0-9-]*\Z")
DETAIL_UID_PATTERN = re.compile(r"\A([0-9]{5})-([0-9]{3})\Z")


def parse_detail_uid(value: str) -> tuple[str, str]:
    """Decode Studio's exact composite identity without a Catalogue lookup."""

    match = DETAIL_UID_PATTERN.fullmatch(value)
    if match is None:
        raise ValueError("Detail UID must be an exact five-digit Work ID and three-digit Detail ID")
    return match.group(1), match.group(2)


def catalogue_subject_key_is_canonical(kind: str, key: str) -> bool:
    if kind == "work":
        return WORK_ID_PATTERN.fullmatch(key) is not None
    if kind == "series":
        return SERIES_ID_PATTERN.fullmatch(key) is not None
    if kind == "detail":
        return DETAIL_UID_PATTERN.fullmatch(key) is not None
    return False


def normalize_authoring_subject(
    front_matter: Mapping[str, Any],
    *,
    folder_supported: bool,
) -> dict[str, Any]:
    """Project one non-blocking subject state from raw canonical front matter."""

    declared_fields = [
        field_name
        for field_name in AUTHORING_SUBJECT_FIELDS
        if field_name in front_matter
    ]
    if not declared_fields:
        return {
            "state": "none",
            "kind": "none",
            "key": "",
            "fields": [],
        }
    if len(declared_fields) > 1:
        return {
            "state": "conflicting",
            "kind": "conflict",
            "key": "",
            "fields": declared_fields,
            "evidence": {
                field_name: front_matter[field_name]
                for field_name in declared_fields
            },
        }

    field_name = declared_fields[0]
    kind = SUBJECT_KIND_BY_FIELD[field_name]
    raw_value = front_matter[field_name]
    value = raw_value if isinstance(raw_value, str) else ""
    valid = bool(value) and value == value.strip()
    if field_name == FOLDER_PATH_FIELD:
        valid = valid and folder_supported
        if valid:
            try:
                value = normalize_decoded_relative_target(value)
            except ValueError:
                valid = False
    elif valid:
        valid = catalogue_subject_key_is_canonical(kind, value)
    if not valid:
        return {
            "state": "malformed",
            "kind": kind,
            "key": "",
            "fields": [field_name],
            "evidence": {field_name: raw_value},
        }
    return {
        "state": "valid",
        "kind": kind,
        "key": value,
        "fields": [field_name],
    }


def subject_projection_generation(
    *,
    scope: str,
    sub_scope: str,
    subjects_by_doc_id: Mapping[str, Mapping[str, Any]],
) -> str:
    source = {
        "scope": scope,
        "sub_scope": sub_scope,
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


def project_subject_associations(
    *,
    scope: str,
    sub_scope: str,
    documents: Sequence[Any],
    subjects_by_doc_id: Mapping[str, Mapping[str, Any]],
    subject_generation: str,
) -> dict[str, Any]:
    """Group valid exact declarations into a deterministic private product."""

    documents_by_subject: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for document in documents:
        doc_id = str(getattr(document, "doc_id", "") or "")
        subject = subjects_by_doc_id.get(doc_id, {})
        if subject.get("state") != "valid":
            continue
        kind = str(subject.get("kind") or "")
        key = str(subject.get("key") or "")
        viewer_url = str(getattr(document, "viewer_url", "") or "")
        if kind not in {"folder", "work", "series", "detail"} or not key or not viewer_url:
            raise ValueError(
                f"valid authoring subject has no exact private location for {doc_id!r}"
            )
        documents_by_subject.setdefault((kind, key), []).append(
            {
                "target": {
                    "scope": scope,
                    "sub_scope": sub_scope,
                    "doc_id": doc_id,
                },
                "locations": [
                    {
                        "access": "manage",
                        "url": viewer_url,
                    }
                ],
            }
        )

    associations: list[dict[str, Any]] = []
    for kind, key in sorted(documents_by_subject):
        association_documents = sorted(
            documents_by_subject[(kind, key)],
            key=lambda record: (
                record["target"]["scope"],
                record["target"]["sub_scope"],
                record["target"]["doc_id"],
            ),
        )
        associations.append(
            {
                "subject": {"kind": kind, "key": key},
                "documents": association_documents,
            }
        )

    return {
        "schema_version": SUBJECT_ASSOCIATIONS_SCHEMA_VERSION,
        "scope": scope,
        "sub_scope": sub_scope,
        "subject_generation": subject_generation,
        "associations": associations,
    }


__all__ = [
    "AUTHORING_SUBJECT_FIELDS",
    "DETAIL_UID_FIELD",
    "FOLDER_PATH_FIELD",
    "SERIES_ID_FIELD",
    "SUBJECT_ASSOCIATIONS_SCHEMA_VERSION",
    "WORK_ID_FIELD",
    "catalogue_subject_key_is_canonical",
    "normalize_authoring_subject",
    "parse_detail_uid",
    "project_subject_associations",
    "subject_projection_generation",
]
