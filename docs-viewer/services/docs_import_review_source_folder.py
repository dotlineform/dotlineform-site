#!/usr/bin/env python3
"""Strict recognition of complete edited Docs Review source folders."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from docs_import_document_package_content import duplicate_front_matter_fields
from docs_management_document_target import resolve_managed_document_collection
from docs_management_source_service import split_source_exact
import docs_review_packages
from docs_document_packages.returned_common import RETURN_IMPORT_CAPABILITY
from docs_document_packages.returned_files import metadata_from_internal_export_meta
from docs_document_packages.returned_profiles import supported_return_import_profile_ids
from docs_document_packages.returned_validation import validate_whole_returned_package
from docs_document_packages.review_sources import derive_folder_id


EDITED_REVIEW_SOURCE_FORMAT = "edited_review_sources"
REVIEW_SOURCE_MARKER_PATTERN = re.compile(
    r"(?m)^[ \t]*review_(?:folder_id|source_export_id|source_scope|"
    r"source_sub_scope|profile_id)[ \t]*:",
)
DATE_PATTERN = re.compile(r"\A\d{4}-\d{2}-\d{2}\Z")
REQUIRED_TEXT_FIELDS = (
    "doc_id",
    "title",
    "added_date",
    "last_updated",
    "review_folder_id",
    "review_source_export_id",
    "review_source_scope",
    "review_profile_id",
)
OPTIONAL_REVIEW_FIELD = "review_source_sub_scope"
ALLOWED_FRONT_MATTER_FIELDS = {
    *REQUIRED_TEXT_FIELDS,
    OPTIONAL_REVIEW_FIELD,
    "summary",
    "parent_id",
    "publishable",
}
PROVENANCE_FIELDS = (
    "review_folder_id",
    "review_source_export_id",
    "review_source_scope",
    OPTIONAL_REVIEW_FIELD,
    "review_profile_id",
)
RETAINED_IDENTITY_FIELDS = (
    "doc_id",
    "added_date",
    "last_updated",
    *PROVENANCE_FIELDS,
)


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _direct_child(candidate: Path, staging_root: Path) -> Path:
    root = staging_root.resolve()
    if candidate.is_symlink():
        raise ValueError("edited review source folders must not be symlinks")
    resolved = candidate.resolve()
    if resolved.parent != root:
        raise ValueError(
            "edited review source folders must be direct children of the "
            "configured import staging root",
        )
    return resolved


def _front_matter_candidate_text(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    if not text.startswith("---"):
        return ""
    closing = re.search(r"(?m)^---[ \t]*$", text[3:])
    if closing is None:
        return text[:16384]
    return text[: closing.end() + 3]


def is_review_source_markdown(path: Path) -> bool:
    """Claim only Markdown whose leading front-matter region has review provenance."""

    return (
        path.is_file()
        and not path.is_symlink()
        and path.suffix.lower() == ".md"
        and REVIEW_SOURCE_MARKER_PATTERN.search(_front_matter_candidate_text(path))
        is not None
    )


def _folder_has_review_source_marker(path: Path) -> bool:
    try:
        markdown_paths = [
            candidate
            for candidate in path.rglob("*")
            if candidate.suffix.lower() == ".md"
        ]
    except OSError as exc:
        raise ValueError(f"edited review source folder is unreadable: {exc}") from exc
    return any(is_review_source_markdown(candidate) for candidate in markdown_paths)


def is_edited_review_source_candidate(path: Path) -> bool:
    """Claim a folder before ordinary Markdown package normalization."""

    return (
        path.is_dir()
        and not path.is_symlink()
        and _folder_has_review_source_marker(path)
    )


def _source_paths(path: Path) -> list[Path]:
    if not path.is_dir():
        raise ValueError("edited review source candidate must be a folder")
    descendants = list(path.iterdir())
    if any(candidate.is_symlink() for candidate in path.rglob("*")):
        raise ValueError("edited review source folders must not contain symlinks")
    nested = [candidate for candidate in descendants if candidate.is_dir()]
    if nested:
        raise ValueError(
            "edited review source folders must contain only direct Markdown files",
        )
    unsupported = [
        candidate.name
        for candidate in descendants
        if not candidate.is_file() or candidate.suffix.lower() != ".md"
    ]
    if unsupported:
        raise ValueError(
            "edited review source folders contain unsupported entries: "
            + ", ".join(sorted(unsupported)),
        )
    paths = sorted(descendants, key=lambda candidate: candidate.name.lower())
    if not paths:
        raise ValueError(
            "edited review source folders must contain at least one Markdown file",
        )
    return paths


def _required_text(front_matter: dict[str, Any], field: str, filename: str) -> str:
    value = front_matter.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"edited review source {filename} {field} must be a non-blank string",
        )
    return value.strip()


def _source_record(path: Path) -> dict[str, Any]:
    try:
        source_text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ValueError(f"edited review source is unreadable: {path.name}") from exc
    duplicates = duplicate_front_matter_fields(source_text)
    if duplicates:
        raise ValueError(
            f"edited review source {path.name} contains duplicate front matter "
            "fields: "
            + ", ".join(duplicates),
        )
    try:
        _front_matter_source, front_matter, source_body = split_source_exact(
            source_text,
        )
    except ValueError as exc:
        raise ValueError(
            f"edited review source {path.name} front matter is invalid: {exc}",
        ) from exc
    unknown_fields = sorted(set(front_matter) - ALLOWED_FRONT_MATTER_FIELDS)
    if unknown_fields:
        raise ValueError(
            f"edited review source {path.name} contains unsupported front matter "
            "fields: "
            + ", ".join(unknown_fields),
        )
    values = {
        field: _required_text(front_matter, field, path.name)
        for field in REQUIRED_TEXT_FIELDS
    }
    doc_id = docs_review_packages.validate_doc_id(values["doc_id"])
    if path.stem != doc_id:
        raise ValueError(
            f"edited review source filename must match doc_id: {path.name}",
        )
    for field in ("added_date", "last_updated"):
        if DATE_PATTERN.fullmatch(values[field]) is None:
            raise ValueError(
                f"edited review source {path.name} {field} must be YYYY-MM-DD",
            )
    if values["added_date"] != values["last_updated"]:
        raise ValueError(
            f"edited review source {path.name} transport dates must match",
        )
    if OPTIONAL_REVIEW_FIELD in front_matter:
        values[OPTIONAL_REVIEW_FIELD] = _required_text(
            front_matter,
            OPTIONAL_REVIEW_FIELD,
            path.name,
        )
    else:
        values[OPTIONAL_REVIEW_FIELD] = ""
    for field in ("summary", "parent_id"):
        if field in front_matter and not isinstance(front_matter[field], str):
            raise ValueError(
                f"edited review source {path.name} {field} must be a string",
            )
    if "publishable" in front_matter and not isinstance(
        front_matter["publishable"],
        bool,
    ):
        raise ValueError(
            f"edited review source {path.name} publishable must be true or false",
        )
    return {
        "doc_id": doc_id,
        "filename": path.name,
        "path": path,
        "source_text": source_text,
        "front_matter": front_matter,
        "source_body": source_body,
        **values,
    }


def _consistent_value(
    records: list[dict[str, Any]],
    field: str,
) -> str:
    values = {_clean_text(record.get(field)) for record in records}
    if len(values) != 1:
        raise ValueError(
            f"edited review sources must have one consistent {field}",
        )
    return values.pop()


def _manifest_source_membership(
    manifest: dict[str, Any],
    records: list[dict[str, Any]],
) -> None:
    raw_source_files = manifest.get("source_files")
    if not isinstance(raw_source_files, list):
        raise ValueError(
            "review package manifest source_files must be an array",
        )
    expected = {
        (record["doc_id"], f"source/{record['filename']}")
        for record in records
    }
    actual: set[tuple[str, str]] = set()
    for item in raw_source_files:
        if not isinstance(item, dict):
            raise ValueError(
                "review package manifest source_files entries must be objects",
            )
        doc_id = _clean_text(item.get("doc_id"))
        path = _clean_text(item.get("path"))
        if not doc_id or not path:
            raise ValueError(
                "review package manifest source_files entries require doc_id and path",
            )
        identity = (doc_id, path)
        if identity in actual:
            raise ValueError(
                "review package manifest source_files contains duplicate entries",
            )
        actual.add(identity)
    if actual != expected:
        raise ValueError(
            "review package manifest source_files does not match the staged "
            "edited source set",
        )


def _validate_retained_source_identity(
    repo_root: Path,
    *,
    folder_id: str,
    records: list[dict[str, Any]],
) -> None:
    retained_root = docs_review_packages.resolve_package_path(
        repo_root,
        folder_id,
    ) / "source"
    for record in records:
        retained_path = retained_root / record["filename"]
        if not retained_path.is_file() or retained_path.is_symlink():
            raise ValueError(
                "retained review package source is missing: "
                + record["filename"],
            )
        retained_record = _source_record(retained_path)
        for field in RETAINED_IDENTITY_FIELDS:
            if _clean_text(retained_record.get(field)) != _clean_text(
                record.get(field),
            ):
                raise ValueError(
                    f"edited review source {record['filename']} {field} does not "
                    "match the retained review package",
                )


def _validate_source_versions(
    trusted_metadata: dict[str, Any],
    doc_ids: set[str],
) -> tuple[tuple[str, str], ...]:
    raw_versions = trusted_metadata.get("source_last_updated")
    if not isinstance(raw_versions, dict):
        raise ValueError(
            "trusted package metadata must contain source_last_updated for every "
            "prepared document",
        )
    if any(not isinstance(doc_id, str) for doc_id in raw_versions):
        raise ValueError(
            "trusted source_last_updated document ids must be strings",
        )
    noncanonical_ids = sorted(
        doc_id
        for doc_id in raw_versions
        if doc_id != doc_id.strip()
    )
    if noncanonical_ids:
        raise ValueError(
            "trusted source_last_updated document ids must not contain leading "
            "or trailing whitespace",
        )
    version_ids = {_clean_text(doc_id) for doc_id in raw_versions}
    if version_ids != doc_ids:
        raise ValueError(
            "trusted source_last_updated membership does not match the edited "
            "review source set",
        )
    invalid = sorted(
        _clean_text(doc_id)
        for doc_id, value in raw_versions.items()
        if not isinstance(value, str) or not value.strip()
    )
    if invalid:
        raise ValueError(
            "trusted source_last_updated values must be non-blank strings for: "
            + ", ".join(invalid),
        )
    return tuple(
        sorted(
            (
                _clean_text(doc_id),
                _clean_text(value),
            )
            for doc_id, value in raw_versions.items()
        )
    )


def _edited_sources_sha256(records: list[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for record in records:
        filename = str(record["filename"]).encode("utf-8")
        source_bytes = str(record["source_text"]).encode("utf-8")
        digest.update(len(filename).to_bytes(8, "big"))
        digest.update(filename)
        digest.update(len(source_bytes).to_bytes(8, "big"))
        digest.update(source_bytes)
    return digest.hexdigest()


def _trusted_metadata_sha256(trusted_metadata: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            trusted_metadata,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class EditedReviewSourceRecord:
    filename: str
    doc_id: str
    title: str
    body: str
    summary_present: bool
    summary: str
    parent_id_present: bool
    parent_id: str
    publishable_present: bool
    publishable: bool


@dataclass(frozen=True)
class EditedReviewSourceFolder:
    path: Path
    staged_filename: str
    review_folder_id: str
    source_export_id: str
    source_scope: str
    source_sub_scope: str
    profile_id: str
    document_count: int
    doc_ids: tuple[str, ...]
    source_sha256: str
    trusted_metadata_sha256: str
    source_last_updated: tuple[tuple[str, str], ...]
    records: tuple[EditedReviewSourceRecord, ...]

    def listing_projection(self) -> dict[str, Any]:
        return {
            "display_name": f"{self.review_folder_id} (reviewed)",
            "source_format": EDITED_REVIEW_SOURCE_FORMAT,
            "scope": self.source_scope,
            "sub_scope": self.source_sub_scope,
            "supports_return_import": True,
            "review_folder_id": self.review_folder_id,
            "source_export_id": self.source_export_id,
            "source_scope": self.source_scope,
            "source_sub_scope": self.source_sub_scope,
            "profile_id": self.profile_id,
            "document_count": self.document_count,
        }


def recognize_edited_review_source_folder(
    repo_root: Path,
    *,
    candidate: Path,
    staging_root: Path,
    metadata_root: Path,
) -> EditedReviewSourceFolder | None:
    """Return a trusted folder projection, or None when Markdown remains ordinary."""

    if not candidate.is_dir() or candidate.is_symlink():
        return None
    if not _folder_has_review_source_marker(candidate):
        return None
    path = _direct_child(candidate, staging_root)
    records = [_source_record(source_path) for source_path in _source_paths(path)]
    doc_ids = [record["doc_id"] for record in records]
    if len(set(doc_ids)) != len(doc_ids):
        raise ValueError("edited review source doc_id values must be unique")

    folder_id = docs_review_packages.validate_package_id(
        _consistent_value(records, "review_folder_id"),
    )
    export_id = _consistent_value(records, "review_source_export_id")
    source_scope = _consistent_value(records, "review_source_scope").lower()
    source_sub_scope = _consistent_value(
        records,
        OPTIONAL_REVIEW_FIELD,
    ).lower()
    profile_id = _consistent_value(records, "review_profile_id")
    _consistent_value(records, "added_date")
    _consistent_value(records, "last_updated")
    if profile_id not in supported_return_import_profile_ids():
        raise ValueError(
            f"edited review source profile is not importable: {profile_id}",
        )

    manifest_payload = docs_review_packages.read_manifest(repo_root, folder_id)
    manifest = manifest_payload["manifest"]
    expected_manifest = {
        "source_export_id": export_id,
        "source_scope": source_scope,
        "source_sub_scope": source_sub_scope,
        "profile_id": profile_id,
    }
    for field, expected in expected_manifest.items():
        if _clean_text(manifest.get(field)).lower() != expected.lower():
            raise ValueError(
                f"review package manifest {field} does not match the edited "
                "review sources",
            )
    if manifest.get("supports_return_import") is not True:
        raise ValueError(
            "review package manifest supports_return_import must be true",
        )
    if set(manifest.get("selected_doc_ids") or []) != set(doc_ids):
        raise ValueError(
            "review package manifest selected_doc_ids does not match the staged "
            "edited source set",
        )
    _manifest_source_membership(manifest, records)
    _validate_retained_source_identity(
        repo_root,
        folder_id=folder_id,
        records=records,
    )

    trusted_metadata, _unknown, metadata_issues, _metadata_path = (
        metadata_from_internal_export_meta(
            repo_root,
            export_id,
            metadata_root,
        )
    )
    if metadata_issues:
        raise ValueError(
            "trusted export metadata is unavailable: "
            + "; ".join(
                _clean_text(item.get("message"))
                for item in metadata_issues
                if _clean_text(item.get("message"))
            ),
        )
    issues = validate_whole_returned_package(
        [{"doc_id": doc_id} for doc_id in doc_ids],
        trusted_metadata,
        repo_root=repo_root,
        scope=source_scope,
        sub_scope=source_sub_scope or None,
        required_capability=RETURN_IMPORT_CAPABILITY,
    )
    if issues:
        raise ValueError(
            "edited review source provenance is invalid: "
            + "; ".join(
                _clean_text(item.get("message"))
                for item in issues
                if _clean_text(item.get("message"))
            ),
        )
    if _clean_text(trusted_metadata.get("export_id")) != export_id:
        raise ValueError(
            "trusted export metadata export_id does not match the edited review "
            "sources",
        )
    if _clean_text(
        trusted_metadata.get("profile_id")
        or trusted_metadata.get("config_id"),
    ) != profile_id:
        raise ValueError(
            "trusted export metadata profile_id does not match the edited review "
            "sources",
        )
    expected_folder_id = derive_folder_id(trusted_metadata)
    if folder_id != expected_folder_id:
        raise ValueError(
            "edited review sources use a retired review_folder_id; regenerate "
            f"the package as {expected_folder_id}",
        )
    source_last_updated = _validate_source_versions(
        trusted_metadata,
        set(doc_ids),
    )
    resolve_managed_document_collection(
        repo_root,
        scope=source_scope,
        sub_scope=source_sub_scope or None,
    )

    return EditedReviewSourceFolder(
        path=path,
        staged_filename=path.name,
        review_folder_id=folder_id,
        source_export_id=export_id,
        source_scope=source_scope,
        source_sub_scope=source_sub_scope,
        profile_id=profile_id,
        document_count=len(records),
        doc_ids=tuple(doc_ids),
        source_sha256=_edited_sources_sha256(records),
        trusted_metadata_sha256=_trusted_metadata_sha256(trusted_metadata),
        source_last_updated=source_last_updated,
        records=tuple(
            EditedReviewSourceRecord(
                filename=str(record["filename"]),
                doc_id=str(record["doc_id"]),
                title=str(record["title"]),
                body=str(record["source_body"]),
                summary_present="summary" in record["front_matter"],
                summary=str(record["front_matter"].get("summary") or ""),
                parent_id_present="parent_id" in record["front_matter"],
                parent_id=str(record["front_matter"].get("parent_id") or ""),
                publishable_present="publishable" in record["front_matter"],
                publishable=bool(record["front_matter"].get("publishable", True)),
            )
            for record in records
        ),
    )


__all__ = [
    "EDITED_REVIEW_SOURCE_FORMAT",
    "EditedReviewSourceFolder",
    "EditedReviewSourceRecord",
    "is_edited_review_source_candidate",
    "is_review_source_markdown",
    "recognize_edited_review_source_folder",
]
