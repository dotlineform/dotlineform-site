"""The source provenance shared by document exports and trusted returns."""

from typing import Any

EXPORT_META_SCHEMA_VERSION = "data_sharing_export_meta_v2"
REEXPORT_MESSAGE = "This package uses retired scope provenance. Re-export the documents and prepare a new Review package."


def require_package_stage(value: Any) -> str:
    if value != "working":
        raise ValueError("Document packages require explicit stage 'working'")
    return "working"


def package_provenance_error(metadata: dict[str, Any]) -> str:
    if "scope" in metadata or "source_scope" in metadata or metadata.get("schema_version") == "data_sharing_export_meta_v1":
        return REEXPORT_MESSAGE
    if metadata.get("schema_version") != EXPORT_META_SCHEMA_VERSION:
        return f"Package metadata must use {EXPORT_META_SCHEMA_VERSION}; re-export the documents."
    if metadata.get("stage") != "working":
        return "Trusted package metadata must identify stage 'working'; re-export the documents."
    return ""
