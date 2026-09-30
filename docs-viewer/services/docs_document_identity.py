#!/usr/bin/env python3
"""Dependency-free document identity and timestamp primitives."""

from __future__ import annotations

import datetime as dt
import re
import secrets
from typing import Any, Callable, Iterable


DOC_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
IMMUTABLE_DOC_ID_PATTERN = re.compile(r"^d-\d{8}-\d{6}-[0-9a-f]{6}$")
CATALOGUE_WORK_DOC_ID_PATTERN = re.compile(r"^[0-9]{5}$")


def current_doc_timestamp() -> str:
    return dt.datetime.now().astimezone().strftime(DOC_TIMESTAMP_FORMAT)


def is_doc_timestamp(value: Any) -> bool:
    try:
        dt.datetime.strptime(str(value or "").strip(), DOC_TIMESTAMP_FORMAT)
    except ValueError:
        return False
    return True


def doc_updated_date(value: Any) -> str:
    """Project source update metadata without inventing dates for undated documents."""
    source_value = str(value or "").strip()
    if not source_value or is_doc_date(source_value):
        return source_value
    try:
        return dt.datetime.strptime(source_value, DOC_TIMESTAMP_FORMAT).date().isoformat()
    except ValueError as error:
        raise ValueError("Document list dates require a source date or complete timestamp") from error


def is_doc_date(value: Any) -> bool:
    """Require one canonical YYYY-MM-DD calendar date in projected metadata."""
    if not isinstance(value, str):
        return False
    try:
        return dt.date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def is_immutable_doc_id(value: Any) -> bool:
    return bool(IMMUTABLE_DOC_ID_PATTERN.fullmatch(str(value or "").strip()))


def is_document_id(value: Any, *, collection: str = "") -> bool:
    """Accept Work IDs only for documents owned by the Catalogue collection."""
    candidate = str(value or "")
    return bool(
        CATALOGUE_WORK_DOC_ID_PATTERN.fullmatch(candidate)
        if collection == "catalogue"
        else IMMUTABLE_DOC_ID_PATTERN.fullmatch(candidate)
    )


def doc_id_matches_added_date(doc_id: str, added_date: str) -> bool:
    try:
        timestamp = dt.datetime.strptime(str(added_date or "").strip(), DOC_TIMESTAMP_FORMAT)
    except ValueError:
        return False
    return str(doc_id or "").startswith(timestamp.strftime("d-%Y%m%d-%H%M%S-"))


def allocate_doc_id(
    added_date: str,
    existing_identities: Iterable[str] = (),
    *,
    token_factory: Callable[[int], str] = secrets.token_hex,
) -> str:
    """Allocate one immutable document ID without writing source."""

    timestamp = dt.datetime.strptime(str(added_date or "").strip(), DOC_TIMESTAMP_FORMAT)
    prefix = timestamp.strftime("d-%Y%m%d-%H%M%S-")
    unavailable = {str(value or "").strip() for value in existing_identities}
    for _attempt in range(100):
        suffix = str(token_factory(3) or "").strip()
        candidate = prefix + suffix
        if not is_immutable_doc_id(candidate):
            raise ValueError("document identity token factory must return six lowercase hexadecimal characters")
        if candidate not in unavailable:
            return candidate
    raise RuntimeError("could not allocate a unique document identity after 100 attempts")


__all__ = [
    "DOC_TIMESTAMP_FORMAT",
    "IMMUTABLE_DOC_ID_PATTERN",
    "allocate_doc_id",
    "current_doc_timestamp",
    "doc_id_matches_added_date",
    "doc_updated_date",
    "is_doc_date",
    "is_doc_timestamp",
    "is_immutable_doc_id",
    "is_document_id",
]
