"""The source provenance shared by document exports and trusted returns."""

from typing import Any

EXPORT_META_SCHEMA_VERSION = "data_sharing_export_meta_v4"
PACKAGE_SCHEMA_VERSION = "docs_review_validated_package_v4"
INVALID_PROVENANCE_MESSAGE = "Package provenance is invalid."


def package_provenance_error(metadata: dict[str, Any]) -> str:
    if metadata.get("schema_version") != EXPORT_META_SCHEMA_VERSION:
        return f"Package metadata must use {EXPORT_META_SCHEMA_VERSION}."
    if any(field in metadata for field in ("stage", "source_stage", "scope", "source_scope", "sub_scope", "source_sub_scope")):
        return "Package metadata contains retired context."
    return ""
