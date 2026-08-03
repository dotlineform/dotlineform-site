#!/usr/bin/env python3
"""Body-free staged document candidate projections for app-level Docs Import."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import docs_source_model as source_model
from docs_document_packages import metadata as package_metadata
from docs_document_packages.returned_common import (
    DOCS_REVIEW_CAPABILITY,
    RETURN_IMPORT_CAPABILITY,
)
from docs_document_packages.returned_parser import parse_staged_import
from docs_import_document_package import (
    COLLECTION_SOURCE_FORMAT,
    EXPORT_ONLY_COLLECTION_SOURCE_FORMAT,
    document_package_source_format,
)
from docs_import_preview import list_staged_import_source_files
from docs_import_review_source_folder import (
    EDITED_REVIEW_SOURCE_FORMAT,
    is_edited_review_source_candidate,
    is_review_source_markdown,
    recognize_edited_review_source_folder,
)
from docs_management_document_target import (
    ManagedDocumentCollection,
    resolve_managed_document_collection,
)
from studio.shared.python.projects_directories import projects_path_marker


ORDINARY_CANDIDATE_KIND = "ordinary_document"
RETURNED_PACKAGE_CANDIDATE_KIND = "returned_package"
EDITED_REVIEW_SOURCE_CANDIDATE_KIND = "edited_review_source"
ORDINARY_CONTEXT_TARGET_MODE = "ordinary_context"
MANIFEST_COLLECTION_TARGET_MODE = "manifest_collection"
NO_TARGET_MODE = "none"
TRUSTED_SOURCE_STAGING_CODE = "trusted_source_requires_import_staging"
TRUSTED_SOURCE_STAGING_MESSAGE = (
    "Trusted document packages and edited review sources must be selected from "
    "data-sharing/import-staging."
)


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _diagnostic(code: str, message: str) -> dict[str, str]:
    return {
        "code": _clean_text(code) or "invalid_candidate",
        "message": _clean_text(message) or "Staged source validation failed.",
    }


def _project_issues(payload: dict[str, Any]) -> list[dict[str, str]]:
    return [
        _diagnostic(
            str(item.get("code") or ""),
            str(item.get("message") or ""),
        )
        for item in payload.get("issues", [])
        if isinstance(item, dict) and item.get("level") == "error"
    ]


def _ordinary_candidate(record: dict[str, Any]) -> dict[str, Any]:
    return {
        **record,
        "candidate_kind": ORDINARY_CANDIDATE_KIND,
        "validation_state": "ready",
        "target_mode": ORDINARY_CONTEXT_TARGET_MODE,
        "target": None,
        "target_label": "Current Docs display",
        "supports_docs_review": False,
        "supports_return_import": False,
        "docs_review_enabled": False,
        "docs_review_disabled_reason": "ordinary_source",
        "import_enabled": True,
        "import_disabled_reason": "",
        "disabled_reason": "",
        "diagnostics": [],
    }


def _blocked_candidate(
    record: dict[str, Any],
    *,
    candidate_kind: str,
    source_format: str,
    code: str,
    message: str,
    target_mode: str = NO_TARGET_MODE,
) -> dict[str, Any]:
    return {
        **record,
        "source_format": source_format,
        "candidate_kind": candidate_kind,
        "validation_state": "blocked",
        "target_mode": target_mode,
        "target": None,
        "target_label": "",
        "supports_docs_review": False,
        "supports_return_import": False,
        "docs_review_enabled": False,
        "docs_review_disabled_reason": code,
        "import_enabled": False,
        "import_disabled_reason": code,
        "disabled_reason": code,
        "diagnostics": [_diagnostic(code, message)],
    }


def _project_ordinary_candidate(record: dict[str, Any]) -> dict[str, Any]:
    if (
        record.get("source_format") == "markdown_package"
        and record.get("package_markdown_count") != 1
    ):
        return _blocked_candidate(
            record,
            candidate_kind=ORDINARY_CANDIDATE_KIND,
            source_format="markdown_package",
            code="invalid_ordinary_markdown_folder",
            message=(
                "An ordinary Markdown folder must contain exactly one Markdown "
                "document."
            ),
            target_mode=ORDINARY_CONTEXT_TARGET_MODE,
        )
    return _ordinary_candidate(record)


def _trusted_source_staging_block(
    record: dict[str, Any],
    *,
    candidate_kind: str,
    source_format: str,
) -> dict[str, Any]:
    return _blocked_candidate(
        record,
        candidate_kind=candidate_kind,
        source_format=source_format,
        code=TRUSTED_SOURCE_STAGING_CODE,
        message=TRUSTED_SOURCE_STAGING_MESSAGE,
        target_mode=MANIFEST_COLLECTION_TARGET_MODE,
    )


def _source_record(
    path: Path,
    projects_base: Path,
    ordinary_record: dict[str, Any] | None,
) -> dict[str, Any]:
    if ordinary_record is not None:
        return ordinary_record
    return {
        "filename": path.name,
        "path": projects_path_marker(path, projects_base),
    }


def _collection_label(collection: ManagedDocumentCollection) -> str:
    scope_label = source_model.humanize(collection.scope)
    if not collection.sub_scope:
        return scope_label
    sub_scope_label = (
        _clean_text(getattr(collection.document_config, "title", ""))
        or source_model.humanize(collection.sub_scope)
    )
    return f"{scope_label} / {sub_scope_label}"


def _edited_review_candidate(
    record: dict[str, Any],
    *,
    edited: Any,
    collection: ManagedDocumentCollection,
) -> dict[str, Any]:
    return {
        **record,
        **edited.listing_projection(),
        "candidate_kind": EDITED_REVIEW_SOURCE_CANDIDATE_KIND,
        "validation_state": "ready",
        "target_mode": MANIFEST_COLLECTION_TARGET_MODE,
        "target": collection.request_target(),
        "target_label": _collection_label(collection),
        "supports_docs_review": False,
        "supports_return_import": True,
        "docs_review_enabled": False,
        "docs_review_disabled_reason": "edited_review_source",
        "import_enabled": True,
        "import_disabled_reason": "",
        "disabled_reason": "",
        "diagnostics": [],
    }


def _returned_package_candidate(
    repo_root: Path,
    path: Path,
    *,
    metadata_root: Path,
    workspace_root: Path,
) -> dict[str, Any] | None:
    try:
        record = package_metadata.staged_file_record(
            path,
            metadata_root=metadata_root,
            workspace_root=workspace_root,
        )
    except OSError:
        return _blocked_candidate(
            {"filename": path.name},
            candidate_kind=RETURNED_PACKAGE_CANDIDATE_KIND,
            source_format=COLLECTION_SOURCE_FORMAT,
            code="unreadable_claimed_package",
            message="The claimed staged package could not be read safely.",
            target_mode=MANIFEST_COLLECTION_TARGET_MODE,
        )
    if record.get("metadata_ok") is not True:
        try:
            export_id = package_metadata.export_id_from_staged_file(path)
        except (OSError, ValueError):
            return None
        record["export_id"] = export_id
        return _blocked_candidate(
            record,
            candidate_kind=RETURNED_PACKAGE_CANDIDATE_KIND,
            source_format=COLLECTION_SOURCE_FORMAT,
            code="untrusted_package_metadata",
            message="Trusted export metadata is unavailable for this claimed package.",
            target_mode=MANIFEST_COLLECTION_TARGET_MODE,
        )

    if (
        _clean_text(record.get("data_domain")) != "documents"
        and _clean_text(record.get("adapter_id")) != "documents"
    ):
        return None

    scope = _clean_text(record.get("scope")).lower()
    sub_scope = _clean_text(record.get("sub_scope")).lower()
    declared_target = {
        "scope": scope,
        **({"sub_scope": sub_scope} if sub_scope else {}),
    }
    try:
        collection = resolve_managed_document_collection(
            repo_root,
            scope=scope,
            sub_scope=sub_scope or None,
        )
    except (FileNotFoundError, OSError, ValueError):
        blocked = _blocked_candidate(
            record,
            candidate_kind=RETURNED_PACKAGE_CANDIDATE_KIND,
            source_format=COLLECTION_SOURCE_FORMAT,
            code="invalid_manifest_target",
            message=(
                "Trusted package metadata does not identify one configured "
                "managed document collection."
            ),
            target_mode=MANIFEST_COLLECTION_TARGET_MODE,
        )
        blocked["declared_target"] = declared_target
        return blocked

    capabilities_valid = record.get("capabilities_ok") is True
    supports_review = capabilities_valid and record.get("supports_docs_review") is True
    supports_import = capabilities_valid and record.get("supports_return_import") is True
    if sub_scope and not getattr(
        collection.document_config,
        "supports_return_import",
        False,
    ):
        supports_import = False

    review_payload = (
        parse_staged_import(
            repo_root=repo_root,
            scope=collection.scope,
            sub_scope=collection.sub_scope or None,
            staged_file=path.name,
            staging_root=path.parent,
            metadata_root=metadata_root,
            required_capability=DOCS_REVIEW_CAPABILITY,
        )
        if supports_review
        else {}
    )
    import_payload = (
        parse_staged_import(
            repo_root=repo_root,
            scope=collection.scope,
            sub_scope=collection.sub_scope or None,
            staged_file=path.name,
            staging_root=path.parent,
            metadata_root=metadata_root,
            required_capability=RETURN_IMPORT_CAPABILITY,
        )
        if supports_import
        else {}
    )
    docs_review_enabled = supports_review and review_payload.get("ok") is True
    import_enabled = supports_import and import_payload.get("ok") is True
    review_diagnostics = _project_issues(review_payload)
    import_diagnostics = _project_issues(import_payload)
    diagnostics = [*review_diagnostics, *import_diagnostics]
    if not capabilities_valid:
        diagnostics.append(
            _diagnostic(
                "invalid_capability_metadata",
                _clean_text(record.get("capability_error"))
                or "Trusted package capabilities are invalid.",
            )
        )
    elif not supports_review and not supports_import:
        diagnostics.append(
            _diagnostic(
                "capability_blocked",
                "Trusted package capabilities do not enable Docs Review or Import.",
            )
        )
    elif not import_enabled and sub_scope and record.get("supports_return_import") is True:
        diagnostics.append(
            _diagnostic(
                "collection_import_disabled",
                "Returned-package Import is not enabled for the exact child collection.",
            )
        )

    validation_state = (
        "ready"
        if docs_review_enabled or import_enabled
        else "blocked"
    )
    counts = (
        import_payload.get("counts")
        if import_payload.get("ok") is True
        else review_payload.get("counts")
    )
    document_count = (
        counts.get("records")
        if isinstance(counts, dict)
        and isinstance(counts.get("records"), int)
        else 0
    )
    if docs_review_enabled:
        docs_review_disabled_reason = ""
    elif not capabilities_valid:
        docs_review_disabled_reason = "invalid_capability_metadata"
    elif review_diagnostics:
        docs_review_disabled_reason = review_diagnostics[0]["code"]
    else:
        docs_review_disabled_reason = "docs_review_unsupported"

    if import_enabled:
        import_disabled_reason = ""
    elif not capabilities_valid:
        import_disabled_reason = "invalid_capability_metadata"
    elif import_diagnostics:
        import_disabled_reason = import_diagnostics[0]["code"]
    elif (
        sub_scope
        and record.get("supports_return_import") is True
        and not getattr(
            collection.document_config,
            "supports_return_import",
            False,
        )
    ):
        import_disabled_reason = "collection_import_disabled"
    else:
        import_disabled_reason = "return_import_unsupported"

    return {
        **record,
        "source_format": COLLECTION_SOURCE_FORMAT,
        "candidate_kind": RETURNED_PACKAGE_CANDIDATE_KIND,
        "validation_state": validation_state,
        "target_mode": MANIFEST_COLLECTION_TARGET_MODE,
        "target": collection.request_target(),
        "target_label": _collection_label(collection),
        "supports_docs_review": record.get("supports_docs_review") is True,
        "supports_return_import": record.get("supports_return_import") is True,
        "docs_review_enabled": docs_review_enabled,
        "docs_review_disabled_reason": docs_review_disabled_reason,
        "import_enabled": import_enabled,
        "import_disabled_reason": import_disabled_reason,
        "disabled_reason": (
            ""
            if validation_state == "ready"
            else diagnostics[0]["code"]
            if diagnostics
            else "capability_blocked"
        ),
        "diagnostics": diagnostics,
        "document_count": document_count,
    }


def list_import_candidates(
    repo_root: Path,
    *,
    staging_root: Path,
    workspace_root: Path,
    metadata_root: Path,
    projects_base: Path | None = None,
    trusted_sources_allowed: bool = True,
) -> list[dict[str, Any]]:
    """List all claimed document candidates without projecting source bodies."""

    source_projects_base = (projects_base or workspace_root).resolve()
    ordinary_records = {
        str(record.get("filename") or ""): record
        for record in list_staged_import_source_files(
            staging_root,
            source_projects_base,
        )
    }
    candidates: list[dict[str, Any]] = []
    for path in sorted(
        staging_root.iterdir(),
        key=lambda candidate: candidate.name.lower(),
    ):
        if path.is_symlink():
            continue
        ordinary_record = ordinary_records.get(path.name)
        if path.is_dir():
            try:
                claimed_review_folder = is_edited_review_source_candidate(path)
            except (OSError, ValueError):
                if ordinary_record is not None:
                    candidates.append(
                        _blocked_candidate(
                            ordinary_record,
                            candidate_kind=EDITED_REVIEW_SOURCE_CANDIDATE_KIND,
                            source_format=EDITED_REVIEW_SOURCE_FORMAT,
                            code="unreadable_edited_review_source",
                            message=(
                                "A staged folder could not be inspected safely "
                                "for review provenance."
                            ),
                            target_mode=MANIFEST_COLLECTION_TARGET_MODE,
                        )
                    )
                continue
            if claimed_review_folder:
                if not trusted_sources_allowed:
                    candidates.append(
                        _trusted_source_staging_block(
                            _source_record(path, source_projects_base, ordinary_record),
                            candidate_kind=EDITED_REVIEW_SOURCE_CANDIDATE_KIND,
                            source_format=EDITED_REVIEW_SOURCE_FORMAT,
                        )
                    )
                    continue
                try:
                    edited = recognize_edited_review_source_folder(
                        repo_root,
                        candidate=path,
                        staging_root=staging_root,
                        metadata_root=metadata_root,
                    )
                    if edited is None:
                        raise ValueError(
                            "review provenance did not resolve a complete edited folder",
                        )
                    collection = resolve_managed_document_collection(
                        repo_root,
                        scope=edited.source_scope,
                        sub_scope=edited.source_sub_scope or None,
                    )
                except (FileNotFoundError, OSError, RuntimeError, ValueError) as exc:
                    if ordinary_record is not None:
                        safe_message = (
                            str(exc)
                            .replace(
                                str(repo_root.resolve()),
                                "<repository>",
                            )
                            .replace(
                                str(source_projects_base),
                                "$DOTLINEFORM_PROJECTS_BASE_DIR",
                            )
                        )
                        candidates.append(
                            _blocked_candidate(
                                ordinary_record,
                                candidate_kind=EDITED_REVIEW_SOURCE_CANDIDATE_KIND,
                                source_format=EDITED_REVIEW_SOURCE_FORMAT,
                                code="invalid_edited_review_source",
                                message=safe_message,
                                target_mode=MANIFEST_COLLECTION_TARGET_MODE,
                            )
                        )
                    continue
                if ordinary_record is not None:
                    candidates.append(
                        _edited_review_candidate(
                            ordinary_record,
                            edited=edited,
                            collection=collection,
                        )
                    )
                continue
            if ordinary_record is not None:
                candidates.append(_project_ordinary_candidate(ordinary_record))
            continue

        if is_review_source_markdown(path):
            if ordinary_record is not None:
                candidates.append(
                    _trusted_source_staging_block(
                        ordinary_record,
                        candidate_kind=EDITED_REVIEW_SOURCE_CANDIDATE_KIND,
                        source_format=EDITED_REVIEW_SOURCE_FORMAT,
                    )
                    if not trusted_sources_allowed
                    else _blocked_candidate(
                        ordinary_record,
                        candidate_kind=EDITED_REVIEW_SOURCE_CANDIDATE_KIND,
                        source_format=EDITED_REVIEW_SOURCE_FORMAT,
                        code="incomplete_edited_review_source",
                        message=(
                            "A review source must be staged as its complete edited "
                            "review-source folder."
                        ),
                        target_mode=MANIFEST_COLLECTION_TARGET_MODE,
                    )
                )
            continue
        if path.suffix.lower() in package_metadata.SUPPORTED_EXTENSIONS:
            if not trusted_sources_allowed:
                source_format = document_package_source_format(
                    repo_root,
                    path,
                    metadata_root=metadata_root,
                )
                if source_format in {
                    COLLECTION_SOURCE_FORMAT,
                    EXPORT_ONLY_COLLECTION_SOURCE_FORMAT,
                }:
                    candidates.append(
                        _trusted_source_staging_block(
                            _source_record(path, source_projects_base, ordinary_record),
                            candidate_kind=RETURNED_PACKAGE_CANDIDATE_KIND,
                            source_format=source_format,
                        )
                    )
                continue
            returned = _returned_package_candidate(
                repo_root,
                path,
                metadata_root=metadata_root,
                workspace_root=workspace_root,
            )
            if returned is not None:
                candidates.append(returned)
            continue
        if ordinary_record is not None:
            candidates.append(_project_ordinary_candidate(ordinary_record))
    return candidates


__all__ = [
    "EDITED_REVIEW_SOURCE_CANDIDATE_KIND",
    "MANIFEST_COLLECTION_TARGET_MODE",
    "NO_TARGET_MODE",
    "ORDINARY_CANDIDATE_KIND",
    "ORDINARY_CONTEXT_TARGET_MODE",
    "RETURNED_PACKAGE_CANDIDATE_KIND",
    "TRUSTED_SOURCE_STAGING_CODE",
    "TRUSTED_SOURCE_STAGING_MESSAGE",
    "list_import_candidates",
]
