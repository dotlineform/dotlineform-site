#!/usr/bin/env python3
"""Dependency-free document identity and timestamp primitives."""

from __future__ import annotations

import datetime as dt
import re
import secrets
from typing import Any, Callable, Iterable


DOC_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
IMMUTABLE_DOC_ID_PATTERN = re.compile(r"^d-\d{8}-\d{6}-[0-9a-f]{6}$")


def current_doc_timestamp() -> str:
    return dt.datetime.now().astimezone().strftime(DOC_TIMESTAMP_FORMAT)


def is_immutable_doc_id(value: Any) -> bool:
    return bool(IMMUTABLE_DOC_ID_PATTERN.fullmatch(str(value or "").strip()))


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
    "is_immutable_doc_id",
]
