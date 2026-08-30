#!/usr/bin/env python3
"""Private scope-owned provenance for media added from configured source folders."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

from docs_artifact_locations import artifact_location_adapter
from docs_media_storage import validate_media_filename
from docs_scope_config import DocsScopeConfig, load_docs_scope_configs
from studio.shared.python.projects_directories import (
    PROJECTS_ROOT_MARKER,
    normalize_projects_directory_marker,
)


SCHEMA_VERSION = "docs_media_source_evidence_v1"
TABLE_IDENTITY = "media-source-evidence.json"


@dataclass(frozen=True)
class DocsMediaSourceEvidence:
    media_type: str
    identity: str
    source_root: str
    source_path: str


def _canonical_source_path(value: Any, *, source_root: str) -> str:
    raw_path = str(value or "")
    if raw_path != raw_path.strip():
        raise ValueError("source_path must not contain surrounding whitespace")
    if not raw_path or raw_path.startswith("/") or raw_path.endswith("/") or "\\" in raw_path:
        raise ValueError("source_path must be a canonical Projects-relative POSIX file path")
    parts = raw_path.split("/")
    if any(not part or part in {".", ".."} for part in parts):
        raise ValueError("source_path must be a canonical Projects-relative POSIX file path")
    if any(any(ord(character) < 32 or ord(character) == 127 for character in part) for part in parts):
        raise ValueError("source_path must not contain control characters")
    normalized = "/".join(parts)
    if not normalized.startswith(f"{source_root}/"):
        raise ValueError("source_path must be below source_root")
    return normalized


def _normalize_record(raw: Any, *, config: DocsScopeConfig, field: str) -> DocsMediaSourceEvidence:
    if not isinstance(raw, dict) or set(raw) != {
        "media_type",
        "identity",
        "source_root",
        "source_path",
    }:
        raise ValueError(f"{field} must contain only media_type, identity, source_root, and source_path")
    media_type = str(raw.get("media_type") or "")
    if media_type not in config.media.types:
        raise ValueError(f"{field}.media_type must be configured for scope {config.scope_id!r}")
    identity = validate_media_filename(str(raw.get("identity") or ""))
    source_root = normalize_projects_directory_marker(raw.get("source_root"))
    if source_root == PROJECTS_ROOT_MARKER:
        raise ValueError(f"{field}.source_root must identify a directory below Projects")
    source_path = _canonical_source_path(raw.get("source_path"), source_root=source_root)
    return DocsMediaSourceEvidence(
        media_type=media_type,
        identity=identity,
        source_root=source_root,
        source_path=source_path,
    )


def _adapter(repo_root: Path, config: DocsScopeConfig):
    return artifact_location_adapter(repo_root, config.media.source_location)


def load_media_source_evidence(
    repo_root: Path,
    scope: str,
) -> tuple[DocsMediaSourceEvidence, ...]:
    normalized_scope = str(scope or "").strip().lower()
    configs = load_docs_scope_configs(repo_root, scope_ids=(normalized_scope,))
    if normalized_scope not in configs:
        raise ValueError(f"unknown Docs scope: {normalized_scope}")
    config = configs[normalized_scope]
    adapter = _adapter(repo_root, config)
    if adapter.stat(TABLE_IDENTITY) is None:
        return ()
    try:
        payload = json.loads(adapter.read(TABLE_IDENTITY).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Docs media source evidence is invalid JSON") from exc
    if not isinstance(payload, dict) or set(payload) != {"schema_version", "scope", "records"}:
        raise ValueError("Docs media source evidence must contain only schema_version, scope, and records")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"Docs media source evidence schema_version must be {SCHEMA_VERSION}")
    if payload.get("scope") != normalized_scope:
        raise ValueError("Docs media source evidence scope does not match its owner")
    raw_records = payload.get("records")
    if not isinstance(raw_records, list):
        raise ValueError("Docs media source evidence records must be an array")
    records = tuple(
        _normalize_record(record, config=config, field=f"records[{index}]")
        for index, record in enumerate(raw_records)
    )
    keys = [(record.media_type, record.identity) for record in records]
    if len(keys) != len(set(keys)):
        raise ValueError("Docs media source evidence contains duplicate media identities")
    if keys != sorted(keys):
        raise ValueError("Docs media source evidence records must use canonical sort order")
    return records


def record_media_source_evidence(
    repo_root: Path,
    scope: str,
    *,
    media_type: str,
    identity: str,
    source_root: str,
    source_path: str,
) -> DocsMediaSourceEvidence:
    normalized_scope = str(scope or "").strip().lower()
    configs = load_docs_scope_configs(repo_root, scope_ids=(normalized_scope,))
    if normalized_scope not in configs:
        raise ValueError(f"unknown Docs scope: {normalized_scope}")
    config = configs[normalized_scope]
    record = _normalize_record(
        {
            "media_type": media_type,
            "identity": identity,
            "source_root": source_root,
            "source_path": source_path,
        },
        config=config,
        field="record",
    )
    records = {
        (existing.media_type, existing.identity): existing
        for existing in load_media_source_evidence(repo_root, normalized_scope)
    }
    records[(record.media_type, record.identity)] = record
    ordered = tuple(records[key] for key in sorted(records))
    payload = {
        "schema_version": SCHEMA_VERSION,
        "scope": normalized_scope,
        "records": [asdict(item) for item in ordered],
    }
    encoded = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    adapter = _adapter(repo_root, config)
    adapter.replace(TABLE_IDENTITY, encoded, content_type="application/json")
    if not adapter.verify_bytes(TABLE_IDENTITY, encoded):
        raise RuntimeError("Docs media source evidence verification failed")
    return record


def media_source_evidence_for(
    repo_root: Path,
    scope: str,
    media_type: str,
    identity: str,
) -> DocsMediaSourceEvidence | None:
    normalized_identity = validate_media_filename(identity)
    return next(
        (
            record
            for record in load_media_source_evidence(repo_root, scope)
            if record.media_type == media_type and record.identity == normalized_identity
        ),
        None,
    )


__all__ = [
    "DocsMediaSourceEvidence",
    "SCHEMA_VERSION",
    "TABLE_IDENTITY",
    "load_media_source_evidence",
    "media_source_evidence_for",
    "record_media_source_evidence",
]
