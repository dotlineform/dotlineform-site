#!/usr/bin/env python3
"""Atomic returned document-package validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from docs_management_document_target import (
    resolve_managed_document_collection,
    source_doc_from_path,
)
from docs_document_packages.returned_common import (
    DOCS_REVIEW_CAPABILITY,
    RETURN_IMPORT_CAPABILITY,
    issue,
    normalize_text,
)
import docs_source_model as source_model
from docs_subscope_report_customisations import report_customisation_document_groups


def validate_whole_returned_package(
    raw_rows: list[Any] | tuple[Any, ...],
    trusted_metadata: dict[str, Any],
    *,
    repo_root: Path,
    scope: str,
    sub_scope: str | None = None,
    required_capability: str,
) -> list[dict[str, Any]]:
    """Require trusted routing, optional exact child identity, and full membership."""

    if required_capability not in {
        DOCS_REVIEW_CAPABILITY,
        RETURN_IMPORT_CAPABILITY,
    }:
        raise ValueError(f"unsupported returned-package capability: {required_capability}")
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

    capabilities_valid = True
    for field in (DOCS_REVIEW_CAPABILITY, RETURN_IMPORT_CAPABILITY):
        if not isinstance(trusted_metadata.get(field), bool):
            capabilities_valid = False
            issues.append(
                issue(
                    "error",
                    f"invalid_{field}",
                    f"trusted package metadata {field} must be true or false",
                )
            )
    if (
        capabilities_valid
        and trusted_metadata.get(DOCS_REVIEW_CAPABILITY) is False
        and trusted_metadata.get(RETURN_IMPORT_CAPABILITY) is True
    ):
        capabilities_valid = False
        issues.append(
            issue(
                "error",
                "invalid_package_capabilities",
                "trusted package metadata supports_return_import true "
                "requires supports_docs_review true",
            )
        )

    metadata_sub_scope = normalize_text(trusted_metadata.get("sub_scope")).lower()
    expected_sub_scope = (
        None
        if sub_scope is None
        else normalize_text(sub_scope).lower()
    )
    sub_scope_matches_request = (
        expected_sub_scope is None
        or metadata_sub_scope == expected_sub_scope
    )
    if not sub_scope_matches_request:
        issues.append(
            issue(
                "error",
                "sub_scope_mismatch",
                (
                    "trusted package sub_scope "
                    f"{metadata_sub_scope or '<parent>'!r} does not match "
                    f"requested sub_scope {expected_sub_scope or '<parent>'!r}"
                ),
            )
        )
    if (
        capabilities_valid
        and required_capability == DOCS_REVIEW_CAPABILITY
        and trusted_metadata.get(DOCS_REVIEW_CAPABILITY) is not True
    ):
        issues.append(
            issue(
                "error",
                "docs_review_unsupported_profile",
                f"profile does not support Docs Review: {profile_id or '<missing>'}",
            )
        )
    elif (
        capabilities_valid
        and required_capability == RETURN_IMPORT_CAPABILITY
        and trusted_metadata.get(RETURN_IMPORT_CAPABILITY) is not True
    ):
        issues.append(
            issue(
                "error",
                "export_only_sub_scope" if metadata_sub_scope else "export_only_profile",
                (
                    "trusted sub-scope package does not support Docs Import: "
                    f"{metadata_scope}/{metadata_sub_scope}"
                    if metadata_sub_scope
                    else f"profile does not support returned-package import: {profile_id or '<missing>'}"
                ),
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

    if (
        metadata_sub_scope
        and metadata_scope == expected_scope
        and sub_scope_matches_request
        and expected_seen
    ):
        try:
            collection = resolve_managed_document_collection(
                repo_root,
                scope=expected_scope,
                sub_scope=metadata_sub_scope,
            )
            collection_docs = [
                source_doc_from_path(
                    path=path,
                    scope=collection.scope,
                )
                for path in source_model.scope_markdown_paths(
                    collection.source_root
                )
            ]
            for doc in collection_docs:
                source_model.validate_sub_scope_document_metadata(
                    doc,
                    ui_statuses=collection.document_config.ui_statuses,
                    document_groups=report_customisation_document_groups(
                        collection.document_config.report_customisation
                    ),
                    report_customisation=collection.document_config.report_customisation,
                )
            collection_ids = {
                doc.doc_id
                for doc in collection_docs
            }
            if len(collection_ids) != len(collection_docs):
                raise ValueError("configured child collection contains duplicate doc_id")
        except (FileNotFoundError, OSError, RuntimeError, ValueError) as exc:
            issues.append(
                issue(
                    "error",
                    "invalid_sub_scope",
                    (
                        "trusted package metadata sub_scope must identify one "
                        f"configured child collection: {exc}"
                    ),
                )
            )
        else:
            cross_collection = sorted(expected_seen - collection_ids)
            if cross_collection:
                item = issue(
                    "error",
                    "cross_collection_selected_documents",
                    (
                        "trusted selected_doc_ids contains documents outside "
                        f"{expected_scope}/{metadata_sub_scope}: "
                        + ", ".join(cross_collection)
                    ),
                )
                item["cross_collection_doc_ids"] = cross_collection
                issues.append(item)

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
