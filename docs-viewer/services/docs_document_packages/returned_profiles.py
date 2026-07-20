#!/usr/bin/env python3
"""Returned document-package profile resolution."""

from __future__ import annotations

from typing import Any

from docs_document_packages.returned_common import PROFILE_ID_TO_IMPORT_TYPE, normalize_text

def detect_import_type(package_metadata: dict[str, Any]) -> str:
    if package_metadata.get("supports_return_import") is False:
        return "export_only"
    profile_id = normalize_text(package_metadata.get("profile_id"))
    if profile_id in PROFILE_ID_TO_IMPORT_TYPE:
        return PROFILE_ID_TO_IMPORT_TYPE[profile_id]
    return "unknown"


def supported_return_import_profile_ids() -> set[str]:
    return set(PROFILE_ID_TO_IMPORT_TYPE)
