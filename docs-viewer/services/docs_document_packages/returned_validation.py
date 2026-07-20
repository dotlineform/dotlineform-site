#!/usr/bin/env python3
"""Atomic returned document-package validation."""

from __future__ import annotations

from typing import Any

from docs_document_packages.returned_common import issue, normalize_text


def validate_whole_returned_package(
    raw_rows: list[Any] | tuple[Any, ...],
    trusted_metadata: dict[str, Any],
    *,
    scope: str,
) -> list[dict[str, Any]]:
    """Require trusted document routing and the complete prepared document set."""

    issues: list[dict[str, Any]] = []
    expected_identity = {
        "schema_version": "data_sharing_export_meta_v1",
        "app": "docs-viewer",
        "adapter_id": "documents",
        "data_domain": "documents",
        "record_shape": "document_rows",
    }
    for field, expected in expected_identity.items():
        actual = normalize_text(trusted_metadata.get(field))
        if actual != expected:
            issues.append(
                issue(
                    "error",
                    f"invalid_{field}",
                    f"trusted package metadata {field} must be {expected!r}, got {actual or '<missing>'!r}",
                )
            )

    profile_id = normalize_text(trusted_metadata.get("profile_id"))
    config_id = normalize_text(trusted_metadata.get("config_id"))
    if not profile_id:
        issues.append(
            issue(
                "error",
                "missing_import_metadata",
                "trusted package metadata profile_id is required",
            )
        )
    if config_id and profile_id and config_id != profile_id:
        issues.append(
            issue(
                "error",
                "profile_id_mismatch",
                f"trusted package metadata config_id {config_id!r} does not match profile_id {profile_id!r}",
            )
        )

    metadata_scope = normalize_text(trusted_metadata.get("scope")).lower()
    expected_scope = normalize_text(scope).lower()
    if not metadata_scope:
        issues.append(issue("error", "missing_scope", "trusted package metadata scope is required"))
    elif metadata_scope != expected_scope:
        issues.append(
            issue(
                "error",
                "scope_mismatch",
                f"trusted package scope {metadata_scope!r} does not match requested scope {expected_scope!r}",
            )
        )

    target_format = normalize_text(trusted_metadata.get("target_format"))
    if target_format not in {"json", "jsonl"}:
        issues.append(
            issue(
                "error",
                "invalid_target_format",
                "trusted package metadata target_format must be 'json' or 'jsonl'",
            )
        )
    if trusted_metadata.get("supports_return_import") is not True:
        issues.append(
            issue(
                "error",
                "export_only_profile",
                f"profile does not support returned-package import: {profile_id or '<missing>'}",
            )
        )

    raw_expected = trusted_metadata.get("selected_doc_ids")
    if not isinstance(raw_expected, list):
        issues.append(
            issue(
                "error",
                "missing_selected_doc_ids",
                "trusted package metadata must contain selected_doc_ids",
            )
        )
        return issues
    if not raw_expected:
        issues.append(
            issue(
                "error",
                "empty_selected_doc_ids",
                "trusted package metadata selected_doc_ids must not be empty",
            )
        )

    expected: list[str] = []
    expected_seen: set[str] = set()
    for metadata_index, raw_doc_id in enumerate(raw_expected):
        if not isinstance(raw_doc_id, str):
            issues.append(
                issue(
                    "error",
                    "invalid_selected_doc_id",
                    f"trusted selected_doc_ids entry {metadata_index} must be a string",
                )
            )
            continue
        doc_id = normalize_text(raw_doc_id)
        if not doc_id:
            issues.append(
                issue(
                    "error",
                    "invalid_selected_doc_id",
                    f"trusted selected_doc_ids entry {metadata_index} is empty",
                )
            )
            continue
        if doc_id in expected_seen:
            issues.append(
                issue(
                    "error",
                    "duplicate_selected_doc_id",
                    f"trusted selected_doc_ids contains duplicate doc_id: {doc_id}",
                    doc_id=doc_id,
                )
            )
            continue
        expected_seen.add(doc_id)
        expected.append(doc_id)

    returned: list[str] = []
    returned_seen: set[str] = set()
    for record_index, row in enumerate(raw_rows):
        if not isinstance(row, dict):
            continue
        doc_id = normalize_text(row.get("doc_id"))
        if not doc_id:
            continue
        if doc_id not in returned_seen:
            returned_seen.add(doc_id)
            returned.append(doc_id)

    missing = sorted(expected_seen - returned_seen)
    unexpected = sorted(returned_seen - expected_seen)
    if missing:
        item = issue(
            "error",
            "missing_prepared_documents",
            "returned package is missing prepared documents: " + ", ".join(missing),
        )
        item["missing_doc_ids"] = missing
        issues.append(item)
    if unexpected:
        item = issue(
            "error",
            "unexpected_returned_documents",
            "returned package contains documents outside the prepared set: " + ", ".join(unexpected),
        )
        item["unexpected_doc_ids"] = unexpected
        issues.append(item)
    return issues


__all__ = ["validate_whole_returned_package"]
