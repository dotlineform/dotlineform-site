#!/usr/bin/env python3
"""Manage-only registration for the Processing Working collection."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

import docs_dotlineform_projects_customisation as working_subjects
from docs_document_subjects import normalize_authoring_subject


# A Working collection reports document-owned subjects; it does not own a folder
# namespace. Keep Processing on the established Projects subject rules.
CUSTOMISATION_ID = "dotlineform_processing"
LINEAGE_CONTRACT_ID = "dotlineform_processing_to_analysis_works"
FOLDER_PATH_FIELD = working_subjects.FOLDER_PATH_FIELD
SERIES_ID_FIELD = working_subjects.SERIES_ID_FIELD
WORK_ID_FIELD = working_subjects.WORK_ID_FIELD


def _require_empty_settings(settings: Mapping[str, Any]) -> None:
    if settings:
        raise ValueError("dotlineform_processing settings must be empty")


def normalize_settings(raw: Any, field: str) -> Mapping[str, Any]:
    return working_subjects.normalize_settings(raw, field)


def project_manifest(
    settings: Mapping[str, Any],
    documents: Sequence[Any],
    repo_root: Path,
    scope: str,
    sub_scope: str,
) -> dict[str, Any]:
    """Project document-owned subjects without adding a folder inventory."""

    _require_empty_settings(settings)
    rows: dict[str, dict[str, Any]] = {}
    for document in documents:
        doc_id = str(getattr(document, "doc_id", "") or "").strip()
        front_matter = getattr(document, "front_matter", None)
        if not isinstance(front_matter, Mapping):
            raise ValueError(
                f"dotlineform_processing source metadata is unavailable for {doc_id!r}"
            )
        subject = normalize_authoring_subject(front_matter, folder_supported=True)
        if subject["state"] == "valid" and subject["kind"] == "folder":
            rows[doc_id] = {FOLDER_PATH_FIELD: subject["key"]}
    publication_targets = working_subjects.publication_targets_for_documents(
        repo_root,
        contract_id=LINEAGE_CONTRACT_ID,
        source_scope=scope,
        source_sub_scope=sub_scope,
        doc_ids={
            str(getattr(document, "doc_id", "") or "").strip()
            for document in documents
        },
    )
    for doc_id, targets in publication_targets.items():
        rows.setdefault(doc_id, {})["publication_targets"] = targets
    return {
        "root": {"id": CUSTOMISATION_ID, "data": {}},
        "rows": rows,
    }


def metadata_record(
    settings: Mapping[str, Any],
    front_matter: Mapping[str, Any],
    *,
    doc_id: str,
) -> dict[str, str]:
    _require_empty_settings(settings)
    return working_subjects.metadata_record({}, front_matter, doc_id=doc_id)


def normalize_metadata_update(
    settings: Mapping[str, Any],
    raw: Any,
    *,
    repo_root: Path,
    front_matter: Mapping[str, Any],
    doc_id: str,
) -> dict[str, Any]:
    _require_empty_settings(settings)
    return working_subjects.normalize_metadata_update(
        {},
        raw,
        repo_root=repo_root,
        front_matter=front_matter,
        doc_id=doc_id,
    )


def normalize_import_front_matter(
    settings: Mapping[str, Any],
    raw: Any,
    *,
    doc_id: str,
) -> dict[str, str]:
    _require_empty_settings(settings)
    return working_subjects.normalize_import_front_matter({}, raw, doc_id=doc_id)


__all__ = [
    "CUSTOMISATION_ID",
    "FOLDER_PATH_FIELD",
    "LINEAGE_CONTRACT_ID",
    "SERIES_ID_FIELD",
    "WORK_ID_FIELD",
    "metadata_record",
    "normalize_metadata_update",
    "normalize_import_front_matter",
    "normalize_settings",
    "project_manifest",
]
