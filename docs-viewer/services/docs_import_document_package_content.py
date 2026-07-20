#!/usr/bin/env python3
"""Normalize trusted returned document-package rows into Docs Import content."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any, Iterable

_BOOTSTRAP_START = Path(__file__).resolve()
for _candidate in (_BOOTSTRAP_START.parent, *_BOOTSTRAP_START.parents):
    if (_candidate / "site-tools" / "config" / "site-tools.json").exists():
        _docs_services_root = _candidate / "docs-viewer" / "services"
        if str(_docs_services_root) not in sys.path:
            sys.path.insert(0, str(_docs_services_root))
        break

from docs_import_content import (  # noqa: E402
    CONTENT_FORMAT_MARKDOWN,
    CONTENT_FORMAT_PLAIN_TEXT,
    CONTENT_INTENT_EMPTY_NEW,
    CONTENT_INTENT_PRESERVE_EXISTING,
    CONTENT_INTENT_REPLACE,
    ImportContent,
)
from docs_management_source_service import (  # noqa: E402
    STRICT_FRONT_MATTER_PATTERN,
    split_source_exact,
)


COMPACT_PROFILE_ID = "document-content"
FULL_SOURCE_PROFILE_ID = "document-full-source"
COMPACT_SCHEMA_VERSION = "data_sharing_returned_package_v1"
FULL_SOURCE_SCHEMA_VERSION = "documents_full_package_v1"

COMPACT_CONTENT_FORMATS = {CONTENT_FORMAT_MARKDOWN, CONTENT_FORMAT_PLAIN_TEXT}
ALLOWED_FRONT_MATTER_FIELDS = ("title", "parent_id", "summary", "viewable")
COMPACT_MAPPED_FIELDS = {
    "doc_id",
    "title",
    "parent_id",
    "parent_title",
    "summary",
    "current_summary",
    "viewable",
    "headings",
    "last_updated",
    "content",
    "content_intent",
    "ancestors",
    "children",
    "assets",
    "links",
    "_record_index",
    "_source_line",
}
FULL_SOURCE_MAPPED_FIELDS = {
    "record_type",
    "doc_id",
    "scope",
    "source_path",
    "source_sha256",
    "source_bytes",
    "source_byte_count",
    "existing",
    "is_existing",
    "canonical_url",
    "document",
    "canonical_markdown",
    "content_intent",
    "assets",
    "links",
    "semantic_references",
    "embedded_content",
    "dependencies",
    "_record_index",
    "_source_line",
}


def clean_text(value: Any) -> str:
    return str(value or "").strip()


def object_tuple(value: Any, *, field: str, record_index: int) -> tuple[dict[str, Any], ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise ValueError(f"record {record_index} {field} must be a list of objects")
    return tuple(copy.deepcopy(value))


def allowed_front_matter(source: dict[str, Any]) -> dict[str, Any]:
    return {
        field: copy.deepcopy(source[field])
        for field in ALLOWED_FRONT_MATTER_FIELDS
        if field in source
    }


def duplicate_front_matter_fields(source_text: str) -> list[str]:
    match = STRICT_FRONT_MATTER_PATTERN.match(source_text)
    if not match:
        return []
    seen: set[str] = set()
    duplicates: list[str] = []
    for line in match.group(1).splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key = stripped.split(":", 1)[0].strip()
        if key in seen and key not in duplicates:
            duplicates.append(key)
        seen.add(key)
    return duplicates


def package_contract(package_metadata: dict[str, Any]) -> tuple[str, str]:
    profile_id = clean_text(package_metadata.get("profile_id") or package_metadata.get("config_id"))
    schema_version = clean_text(package_metadata.get("schema_version"))
    if profile_id == COMPACT_PROFILE_ID and schema_version in {"", COMPACT_SCHEMA_VERSION}:
        return "compact", profile_id
    if profile_id == FULL_SOURCE_PROFILE_ID and schema_version in {"", FULL_SOURCE_SCHEMA_VERSION}:
        return "full_source", profile_id
    raise ValueError(
        "unsupported returned document package contract: "
        f"profile_id={profile_id or '<missing>'}, schema_version={schema_version or '<missing>'}"
    )


def compact_content_format(package_metadata: dict[str, Any]) -> str:
    content_format = clean_text(package_metadata.get("content_format"))
    if content_format not in COMPACT_CONTENT_FORMATS:
        raise ValueError(
            "document-content package content_format must be one of: "
            + ", ".join(sorted(COMPACT_CONTENT_FORMATS))
        )
    return content_format


def row_title(row: dict[str, Any], *, full_source: bool) -> str:
    if full_source:
        document = row.get("document")
        if document is not None and not isinstance(document, dict):
            raise ValueError("full-source record document must be an object")
        return clean_text((document or {}).get("title") or row.get("title"))
    return clean_text(row.get("title"))


def row_parent_id(row: dict[str, Any], *, full_source: bool) -> str:
    if full_source:
        document = row.get("document") if isinstance(row.get("document"), dict) else {}
        return clean_text(document.get("parent_id") or row.get("parent_id"))
    return clean_text(row.get("parent_id"))


def full_source_content(
    row: dict[str, Any],
    *,
    doc_id: str,
    record_index: int,
) -> tuple[str, str, dict[str, Any], str, list[dict[str, Any]]]:
    canonical = row.get("canonical_markdown")
    if not isinstance(canonical, str):
        raise ValueError(f"record {record_index} canonical_markdown must be a string")
    duplicates = duplicate_front_matter_fields(canonical)
    if duplicates:
        raise ValueError(
            f"record {record_index} canonical_markdown contains duplicate front matter fields: "
            + ", ".join(duplicates)
        )
    try:
        _front_matter_source, parsed_front_matter, body = split_source_exact(canonical)
    except ValueError as exc:
        raise ValueError(f"record {record_index} canonical_markdown front matter is invalid: {exc}") from exc
    parsed_doc_id = clean_text(parsed_front_matter.get("doc_id"))
    if parsed_doc_id != doc_id:
        raise ValueError(
            f"record {record_index} doc_id {doc_id!r} does not match canonical_markdown doc_id {parsed_doc_id!r}"
        )
    title = clean_text(parsed_front_matter.get("title"))
    if not title:
        raise ValueError(f"record {record_index} canonical_markdown title is required")
    parent_id = clean_text(parsed_front_matter.get("parent_id"))
    diagnostics: list[dict[str, Any]] = []
    duplicate_document = row.get("document") if isinstance(row.get("document"), dict) else {}
    for field, canonical_value in (("title", title), ("parent_id", parent_id)):
        duplicated_value = clean_text(duplicate_document.get(field))
        if duplicated_value and duplicated_value != canonical_value:
            diagnostics.append(
                {
                    "level": "warning",
                    "code": "duplicated_metadata_ignored",
                    "field": field,
                    "message": f"canonical_markdown {field} overrides duplicated document metadata",
                }
            )
    return body, title, allowed_front_matter(parsed_front_matter), parent_id, diagnostics


@dataclass(frozen=True)
class DocumentsImportContentBatch:
    records: tuple[ImportContent, ...]
    provenance: dict[str, Any]
    diagnostics: tuple[dict[str, Any], ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "records": [record.as_dict() for record in self.records],
            "provenance": copy.deepcopy(self.provenance),
            "diagnostics": copy.deepcopy(list(self.diagnostics)),
        }


def normalize_documents_import_content(
    raw_rows: Iterable[Any],
    *,
    package_metadata: dict[str, Any],
    current_doc_ids: set[str] | None = None,
    staged_filename: str = "",
) -> DocumentsImportContentBatch:
    if not isinstance(package_metadata, dict):
        raise ValueError("document package metadata must be an object")
    package_kind, profile_id = package_contract(package_metadata)
    export_id = clean_text(package_metadata.get("export_id"))
    if not export_id:
        raise ValueError("document package export_id is required")
    schema_version = clean_text(package_metadata.get("schema_version")) or (
        FULL_SOURCE_SCHEMA_VERSION if package_kind == "full_source" else COMPACT_SCHEMA_VERSION
    )
    source_identity = export_id
    existing_ids = set(current_doc_ids or set())
    package_content_format = (
        CONTENT_FORMAT_MARKDOWN
        if package_kind == "full_source"
        else compact_content_format(package_metadata)
    )
    provenance = {
        "adapter": "data_sharing_documents",
        "export_id": export_id,
        "profile_id": profile_id,
        "schema_version": schema_version,
        "scope": clean_text(package_metadata.get("scope")),
        "staged_filename": clean_text(staged_filename),
    }
    records: list[ImportContent] = []
    seen_doc_ids: set[str] = set()
    for record_index, row in enumerate(raw_rows):
        if not isinstance(row, dict):
            raise ValueError(f"record {record_index} must be an object")
        doc_id = clean_text(row.get("doc_id"))
        if not doc_id:
            raise ValueError(f"record {record_index} doc_id is required")
        if doc_id in seen_doc_ids:
            raise ValueError(f"record {record_index} duplicates doc_id {doc_id!r}")
        seen_doc_ids.add(doc_id)
        source_record_index = (
            int(row["_record_index"])
            if isinstance(row.get("_record_index"), int)
            else record_index
        )
        if package_kind == "full_source" and clean_text(row.get("record_type")) not in {"", "document"}:
            raise ValueError(f"record {record_index} record_type must be document")
        if "canonical_markdown" in row and "content" in row:
            raise ValueError(f"record {record_index} must not supply both canonical_markdown and content")

        diagnostics: list[dict[str, Any]] = [
            {
                "level": "info",
                "code": "data_sharing_mapping",
                "profile_id": profile_id,
                "schema_version": schema_version,
            }
        ]
        mapped_fields = FULL_SOURCE_MAPPED_FIELDS if package_kind == "full_source" else COMPACT_MAPPED_FIELDS
        ignored_fields = sorted(key for key in row if key not in mapped_fields)
        if ignored_fields:
            diagnostics.append(
                {
                    "level": "warning",
                    "code": "unmapped_fields_ignored",
                    "fields": ignored_fields,
                }
            )

        content: str | None = None
        front_matter: dict[str, Any]
        if package_kind == "full_source" and "canonical_markdown" in row:
            content, title, front_matter, parent_id, canonical_diagnostics = full_source_content(
                row,
                doc_id=doc_id,
                record_index=record_index,
            )
            diagnostics.extend(canonical_diagnostics)
            content_intent = CONTENT_INTENT_REPLACE
        elif package_kind == "compact" and "content" in row:
            if not isinstance(row.get("content"), str):
                raise ValueError(f"record {record_index} content must be a string")
            content = str(row["content"])
            title = row_title(row, full_source=False)
            parent_id = row_parent_id(row, full_source=False)
            front_matter = allowed_front_matter(row)
            content_intent = CONTENT_INTENT_REPLACE
        else:
            if package_kind == "full_source" and "content" in row:
                raise ValueError(f"record {record_index} full-source rows must use canonical_markdown")
            if package_kind == "compact" and "canonical_markdown" in row:
                raise ValueError(f"record {record_index} compact rows must use content")
            title = row_title(row, full_source=package_kind == "full_source")
            parent_id = row_parent_id(row, full_source=package_kind == "full_source")
            source_front_matter = row.get("document") if package_kind == "full_source" else row
            front_matter = allowed_front_matter(source_front_matter if isinstance(source_front_matter, dict) else {})
            content_intent = (
                CONTENT_INTENT_PRESERVE_EXISTING
                if doc_id in existing_ids or row.get("existing") is True or row.get("is_existing") is True
                else CONTENT_INTENT_EMPTY_NEW
            )
        declared_content_intent = clean_text(row.get("content_intent"))
        if declared_content_intent and declared_content_intent != content_intent:
            raise ValueError(
                f"record {record_index} content_intent {declared_content_intent!r} "
                f"does not match normalized intent {content_intent!r}"
            )
        if not title:
            raise ValueError(f"record {record_index} title is required")
        front_matter["title"] = title
        if "parent_id" in front_matter or parent_id:
            front_matter["parent_id"] = parent_id

        record_provenance = {
            **provenance,
            "record_index": source_record_index,
            "source_line": row.get("_source_line") if isinstance(row.get("_source_line"), int) else None,
        }
        records.append(
            ImportContent(
                source_kind="data_sharing_documents",
                source_identity=source_identity,
                record_identity=f"{source_identity}:{source_record_index}:{doc_id}",
                doc_id=doc_id,
                title=title,
                content_intent=content_intent,
                content_format=package_content_format,
                content=content,
                front_matter=front_matter,
                parent_id=parent_id,
                links=object_tuple(row.get("links"), field="links", record_index=record_index),
                assets=object_tuple(row.get("assets"), field="assets", record_index=record_index),
                diagnostics=tuple(diagnostics),
                provenance=record_provenance,
            )
        )
    return DocumentsImportContentBatch(records=tuple(records), provenance=provenance)


__all__ = [
    "ALLOWED_FRONT_MATTER_FIELDS",
    "COMPACT_PROFILE_ID",
    "DocumentsImportContentBatch",
    "FULL_SOURCE_PROFILE_ID",
    "normalize_documents_import_content",
]
