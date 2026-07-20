#!/usr/bin/env python3
"""Trusted returned document-package intake for Docs Import."""

from __future__ import annotations

import copy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

from docs_import_document_package_content import COMPACT_PROFILE_ID, FULL_SOURCE_PROFILE_ID
from docs_import_document_package_content import normalize_documents_import_content
from docs_import_collection_plan import CollectionRecordState, collection_issue
from docs_import_preview import resolve_staged_import_source
from docs_document_packages.returned_files import (
    export_id_from_json_payload,
    export_id_from_jsonl_header,
    metadata_from_internal_export_meta,
    parse_json_file,
    parse_jsonl_file,
    rows_from_payload,
)
from docs_document_packages.returned_validation import validate_whole_returned_package
from docs_source_model import slugify


COLLECTION_SUFFIXES = {".json", ".jsonl"}
COLLECTION_SOURCE_FORMAT = "data_sharing_documents"
SUPPORTED_COLLECTION_PROFILE_IDS = {COMPACT_PROFILE_ID, FULL_SOURCE_PROFILE_ID}
BLOCKING_PACKAGE_ERRORS = (
    "must not supply both canonical_markdown and content",
    "record_type must be document",
    "does not match canonical_markdown doc_id",
)


@dataclass(frozen=True)
class LoadedDocumentPackage:
    path: Path
    export_id: str
    raw_rows: tuple[Any, ...]
    package_metadata: dict[str, Any]
    source_sha256: str


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _row_title(row: dict[str, Any]) -> str:
    document = row.get("document") if isinstance(row.get("document"), dict) else {}
    return _clean_text(row.get("title") or document.get("title"))


def _row_parent_id(row: dict[str, Any]) -> str:
    document = row.get("document") if isinstance(row.get("document"), dict) else {}
    return _clean_text(document.get("parent_id") or row.get("parent_id"))


def _jsonl_header(path: Path) -> dict[str, Any]:
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if isinstance(payload, dict) and payload.get("record_type") == "data_sharing_header":
            return {key: copy.deepcopy(value) for key, value in payload.items() if key != "record_type"}
        return {}
    return {}


def _content_format(
    trusted_metadata: dict[str, Any],
    package_metadata: dict[str, Any],
    raw_rows: tuple[Any, ...],
) -> str:
    for source in (trusted_metadata, package_metadata):
        value = _clean_text(source.get("content_format"))
        if value:
            return value
    for row in raw_rows:
        if isinstance(row, dict):
            value = _clean_text(row.get("content_format"))
            if value:
                return value
    return ""


def document_package_source_format(
    repo_root: Path,
    path: Path,
    *,
    metadata_root: Path,
) -> str:
    """Classify a trusted supported documents package before generic JSON import."""

    if not path.is_file() or path.is_symlink() or path.suffix.lower() not in COLLECTION_SUFFIXES:
        return ""
    if path.suffix.lower() == ".jsonl":
        export_id, export_issues = export_id_from_jsonl_header(path)
    else:
        payload, parse_issues = parse_json_file(path)
        if parse_issues:
            return ""
        export_id, export_issues = export_id_from_json_payload(payload)
    if export_issues or not export_id:
        return ""
    trusted_metadata, _unknown, metadata_issues, _metadata_path = metadata_from_internal_export_meta(
        repo_root,
        export_id,
        metadata_root,
    )
    if metadata_issues:
        return ""
    profile_id = _clean_text(
        trusted_metadata.get("profile_id") or trusted_metadata.get("config_id")
    )
    if (
        _clean_text(trusted_metadata.get("adapter_id")) != "documents"
        or trusted_metadata.get("supports_return_import") is False
        or profile_id not in SUPPORTED_COLLECTION_PROFILE_IDS
    ):
        return ""
    return COLLECTION_SOURCE_FORMAT


def load_document_package(
    repo_root: Path,
    *,
    scope: str,
    staged_filename: str,
    staging_root: Path,
    metadata_root: Path,
) -> tuple[LoadedDocumentPackage | None, list[dict[str, Any]]]:
    """Resolve one safe package and its trusted export metadata."""

    blockers: list[dict[str, Any]] = []
    try:
        path = resolve_staged_import_source(
            staging_root,
            staged_filename,
            allowed_suffixes=COLLECTION_SUFFIXES,
        )
    except (FileNotFoundError, ValueError) as exc:
        return None, [collection_issue("error", "unsafe_or_missing_staged_package", str(exc))]

    package_metadata: dict[str, Any] = {}
    raw_rows: list[Any] = []
    export_id = ""
    if path.suffix.lower() == ".jsonl":
        try:
            package_metadata = _jsonl_header(path)
        except (OSError, json.JSONDecodeError) as exc:
            blockers.append(
                collection_issue("error", "invalid_jsonl_header", f"invalid JSONL header: {exc}")
            )
        export_id, export_issues = export_id_from_jsonl_header(path)
        raw_rows, parse_issues = parse_jsonl_file(path)
        blockers.extend(copy.deepcopy(export_issues))
        blockers.extend(copy.deepcopy(parse_issues))
    else:
        payload, parse_issues = parse_json_file(path)
        blockers.extend(copy.deepcopy(parse_issues))
        if not blockers:
            export_id, export_issues = export_id_from_json_payload(payload)
            raw_rows, package_metadata, unknown, shape_issues = rows_from_payload(payload)
            blockers.extend(copy.deepcopy(export_issues))
            blockers.extend(copy.deepcopy(shape_issues))
            if unknown:
                package_metadata["unknown_file_metadata"] = copy.deepcopy(unknown)

    if blockers:
        return None, blockers
    if not raw_rows:
        return None, [
            collection_issue("error", "empty_documents_package", "documents package contains no records")
        ]

    trusted_metadata, _unknown, metadata_issues, _metadata_path = metadata_from_internal_export_meta(
        repo_root,
        export_id,
        metadata_root,
    )
    blockers.extend(copy.deepcopy(metadata_issues))
    if not blockers:
        blockers.extend(
            copy.deepcopy(
                validate_whole_returned_package(raw_rows, trusted_metadata, scope=scope)
            )
        )
    if blockers:
        return None, blockers
    if _clean_text(trusted_metadata.get("adapter_id")) != "documents":
        blockers.append(
            collection_issue(
                "error",
                "invalid_documents_adapter",
                "trusted export metadata adapter_id must be documents",
            )
        )
    if trusted_metadata.get("supports_return_import") is False:
        blockers.append(
            collection_issue(
                "error",
                "export_only_profile",
                "trusted export profile does not support returned-package import",
            )
        )
    trusted_profile_id = _clean_text(
        trusted_metadata.get("profile_id") or trusted_metadata.get("config_id")
    )
    declared_profile_id = _clean_text(
        package_metadata.get("profile_id") or package_metadata.get("config_id")
    )
    if declared_profile_id and declared_profile_id != trusted_profile_id:
        blockers.append(
            collection_issue(
                "error",
                "profile_id_mismatch",
                (
                    f"package profile_id {declared_profile_id!r} does not match trusted "
                    f"profile_id {trusted_profile_id!r}"
                ),
            )
        )
    if blockers:
        return None, blockers

    normalized_package_metadata = {
        **copy.deepcopy(package_metadata),
        **copy.deepcopy(trusted_metadata),
    }
    wrapper_schema = _clean_text(package_metadata.get("schema_version"))
    if wrapper_schema:
        normalized_package_metadata["schema_version"] = wrapper_schema
    else:
        normalized_package_metadata.pop("schema_version", None)
    normalized_package_metadata["export_id"] = export_id
    content_format = _content_format(
        trusted_metadata,
        normalized_package_metadata,
        tuple(raw_rows),
    )
    if content_format:
        normalized_package_metadata["content_format"] = content_format

    return (
        LoadedDocumentPackage(
            path=path,
            export_id=export_id,
            raw_rows=tuple(raw_rows),
            package_metadata=normalized_package_metadata,
            source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        ),
        [],
    )


def document_package_record_states(
    raw_rows: tuple[Any, ...],
) -> tuple[list[CollectionRecordState], list[dict[str, Any]]]:
    """Represent every raw package row and classify blocking identity errors."""

    states: list[CollectionRecordState] = []
    blockers: list[dict[str, Any]] = []
    seen_doc_ids: dict[str, int] = {}
    for index, raw_row in enumerate(raw_rows):
        state = CollectionRecordState(record_index=index, raw=raw_row)
        states.append(state)
        if not isinstance(raw_row, dict):
            state.blocked = True
            blockers.append(
                collection_issue(
                    "error",
                    "non_object_record",
                    "package record must be an object",
                    record_index=index,
                )
            )
            continue
        state.doc_id = _clean_text(raw_row.get("doc_id"))
        state.title = _row_title(raw_row)
        state.parent_id = _row_parent_id(raw_row)
        if not state.doc_id:
            state.blocked = True
            blockers.append(
                collection_issue(
                    "error",
                    "missing_doc_id",
                    "package record doc_id is required",
                    record_index=index,
                )
            )
        elif slugify(state.doc_id) != state.doc_id:
            state.blocked = True
            blockers.append(
                collection_issue(
                    "error",
                    "unsafe_doc_id",
                    f"package record doc_id must be a safe normalized docs id: {state.doc_id}",
                    record_index=index,
                    doc_id=state.doc_id,
                )
            )
        elif state.doc_id in seen_doc_ids:
            state.blocked = True
            blockers.append(
                collection_issue(
                    "error",
                    "duplicate_doc_id",
                    f"package record duplicates doc_id {state.doc_id!r}",
                    record_index=index,
                    doc_id=state.doc_id,
                )
            )
        else:
            seen_doc_ids[state.doc_id] = index
        canonical_title_source = isinstance(raw_row.get("canonical_markdown"), str)
        if not state.title and not canonical_title_source:
            state.blocked = True
            blockers.append(
                collection_issue(
                    "error",
                    "missing_title",
                    "package record title is required",
                    record_index=index,
                    doc_id=state.doc_id,
                )
            )
    return states, blockers


def _blocking_package_error(message: str) -> bool:
    return any(fragment in message for fragment in BLOCKING_PACKAGE_ERRORS)


def normalize_document_package_record_states(
    package: LoadedDocumentPackage,
    states: list[CollectionRecordState],
    *,
    current_doc_ids: set[str],
    staged_filename: str,
) -> list[dict[str, Any]]:
    """Normalize each wrapper row while retaining explicit per-record errors."""

    blockers: list[dict[str, Any]] = []
    unsupported_format_message = ""
    try:
        normalize_documents_import_content(
            [],
            package_metadata=package.package_metadata,
            current_doc_ids=current_doc_ids,
            staged_filename=staged_filename,
        )
    except ValueError as exc:
        message = str(exc)
        if "content_format must be one of" in message:
            unsupported_format_message = message
        else:
            blockers.append(
                collection_issue("error", "invalid_documents_package_contract", message)
            )
    if blockers:
        return blockers

    for state in states:
        if not isinstance(state.raw, dict) or not state.doc_id:
            continue
        if unsupported_format_message:
            state.errors.append(
                collection_issue(
                    "error",
                    "unsupported_content_format",
                    unsupported_format_message,
                    record_index=state.record_index,
                    doc_id=state.doc_id,
                )
            )
            continue
        prepared_row = dict(state.raw)
        prepared_row["_record_index"] = state.record_index
        try:
            batch = normalize_documents_import_content(
                [prepared_row],
                package_metadata=package.package_metadata,
                current_doc_ids=current_doc_ids,
                staged_filename=staged_filename,
            )
        except ValueError as exc:
            message = str(exc)
            problem = collection_issue(
                "error",
                "invalid_record_contract",
                message,
                record_index=state.record_index,
                doc_id=state.doc_id,
            )
            if _blocking_package_error(message):
                state.blocked = True
                blockers.append(problem)
            else:
                state.errors.append(problem)
            continue
        state.normalized = batch.records[0]
        state.title = state.normalized.title
        state.parent_id = state.normalized.parent_id
        for diagnostic in state.normalized.diagnostics:
            if diagnostic.get("level") != "warning":
                continue
            warning = collection_issue(
                "warning",
                _clean_text(diagnostic.get("code")) or "import_content_warning",
                _clean_text(diagnostic.get("message")) or "Document package content warning.",
                record_index=state.record_index,
                doc_id=state.normalized.doc_id,
            )
            for key, value in diagnostic.items():
                if key not in {"level", "code", "message"}:
                    warning[key] = copy.deepcopy(value)
            state.warnings.append(warning)
    return blockers


__all__ = [
    "COLLECTION_SOURCE_FORMAT",
    "document_package_source_format",
    "LoadedDocumentPackage",
    "document_package_record_states",
    "load_document_package",
    "normalize_document_package_record_states",
]
