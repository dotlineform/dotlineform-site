#!/usr/bin/env python3
"""Pure write-decision helpers for generated catalogue artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Optional


ROUTE_EXISTS = "route_exists"
VERSION_MATCH = "version_match"


@dataclass(frozen=True)
class GeneratedWriteDecision:
    """A pure write/skip decision for a generated artifact."""

    should_write: bool
    overwrite: bool
    skip_reason: Optional[str] = None
    existing_version: Optional[str] = None
    payload_version: Optional[str] = None


def build_route_stub_content() -> str:
    """Build a metadata-free Jekyll collection route anchor."""
    return "---\n---\n"


def decide_route_stub_write(*, path_exists: bool, force: bool) -> GeneratedWriteDecision:
    if path_exists and not force:
        return GeneratedWriteDecision(should_write=False, overwrite=True, skip_reason=ROUTE_EXISTS)
    return GeneratedWriteDecision(should_write=True, overwrite=path_exists)


def extract_header_scalar_from_json_text(text: str, key: str) -> Optional[str]:
    try:
        obj = json.loads(text)
    except Exception:
        return None
    if not isinstance(obj, dict):
        return None
    header = obj.get("header")
    if not isinstance(header, dict):
        return None
    value: Any = header.get(key)
    if value is None:
        return None
    scalar = str(value).strip()
    return scalar or None


def decide_json_payload_write(
    *,
    path_exists: bool,
    existing_version: Optional[str],
    payload_version: str,
    force: bool,
) -> GeneratedWriteDecision:
    if existing_version is not None and existing_version == payload_version and not force:
        return GeneratedWriteDecision(
            should_write=False,
            overwrite=path_exists,
            skip_reason=VERSION_MATCH,
            existing_version=existing_version,
            payload_version=payload_version,
        )
    return GeneratedWriteDecision(
        should_write=True,
        overwrite=path_exists,
        existing_version=existing_version,
        payload_version=payload_version,
    )
