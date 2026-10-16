"""Saved Docs Media datasets; only an explicit refresh scans sources and writes."""

from __future__ import annotations

from dataclasses import asdict
import datetime as dt
import json
from pathlib import Path
import re
from typing import Any

from docs_document_identity import is_document_id
from docs_media_inventory import list_collection_media, parsed_source_media_references
from docs_source_inspection import inspection_source_paths, read_inspection_source
from docs_workspace_config import (
    COLLECTION_ID_PATTERN, MANAGED_MEDIA_TYPES,
    DocsCollectionConfig, DocsStageConfig, load_docs_workspace_config,
    select_workspace_stage,
)
from docs_builder.semantic_tokens import parse_semantic_tokens

SCHEMA_VERSION = "docs_media_metadata_v1"
REPORT_MEDIA_TYPES = MANAGED_MEDIA_TYPES - {"thumbs"}
REFRESH_TIME = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")


def _keys(value: Any, keys: set[str]) -> None:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError("Docs Media metadata has an invalid record shape")


def _text(value: Any, *, allow_empty: bool = False) -> bool:
    return isinstance(value, str) and value == value.strip() and (bool(value) or allow_empty)


def _validate_media_target(record: dict[str, Any]) -> None:
    role, media_type, identity = (record.get(key) for key in ("role", "media_type", "identity"))
    allowed = REPORT_MEDIA_TYPES if role == "source" else ()
    if not isinstance(media_type, str) or media_type not in allowed or not _text(identity):
        raise ValueError("Docs Media metadata has an invalid media target")
    if "\\" in identity or any(ord(character) < 32 or ord(character) == 127 for character in identity):
        raise ValueError("Docs Media metadata has an invalid media identity")
    if any(part in {"", ".", ".."} for part in identity.split("/")):
        raise ValueError("Docs Media metadata has an invalid media identity")


def validate_media_metadata(metadata: Any) -> dict[str, Any]:
    """Validate saved identity data without consulting mutable documents or media."""
    _keys(metadata, {"schema_version", "refreshed_at", "owners"})
    timestamp = metadata["refreshed_at"]
    if metadata["schema_version"] != SCHEMA_VERSION or not isinstance(timestamp, str) or not REFRESH_TIME.fullmatch(timestamp):
        raise ValueError("Docs Media metadata has an unsupported schema or refresh time")
    dt.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    if not isinstance(metadata["owners"], list):
        raise ValueError("Docs Media metadata requires an owner list")
    for owner in metadata["owners"]:
        _keys(owner, {"collection", "title", "files", "documents"})
        collection = owner["collection"]
        if not _text(collection, allow_empty=True) or (collection and not COLLECTION_ID_PATTERN.fullmatch(collection)):
            raise ValueError("Docs Media metadata has an invalid owner")
        if not isinstance(owner["title"], str):
            raise ValueError("Docs Media metadata has an invalid owner label")
        if not isinstance(owner["files"], list) or not isinstance(owner["documents"], list):
            raise ValueError("Docs Media metadata requires file and document lists")
        for file in owner["files"]:
            _keys(file, {"collection", "role", "media_type", "identity"})
            _validate_media_target(file)
            if file["collection"] != collection:
                raise ValueError("Docs Media metadata has a mismatched file owner")
        for document in owner["documents"]:
            _keys(document, {"target", "title", "references"})
            _keys(document["target"], {"collection", "doc_id"})
            target = document["target"]
            if (target["collection"] != collection or not _text(target["doc_id"])
                    or not is_document_id(target["doc_id"], collection=collection)
                    or not isinstance(document["title"], str)):
                raise ValueError("Docs Media metadata has an invalid document")
            if not isinstance(document["references"], list):
                raise ValueError("Docs Media metadata requires document references")
            for reference in document["references"]:
                _keys(reference, {"role", "media_type", "identity"})
                _validate_media_target(reference)
                if reference["role"] != "source":
                    raise ValueError("Docs Media metadata has an invalid reference role")
    return metadata


def _owner_metadata(repo_root: Path, owner: DocsStageConfig | DocsCollectionConfig) -> dict[str, Any]:
    collection = getattr(owner, "collection", "")
    files = list_collection_media(repo_root, owner, exclude_media_types=frozenset({"thumbs"}))
    documents = []
    root, paths = inspection_source_paths(repo_root, owner)
    for path in paths:
        document = read_inspection_source(root, path, collection=collection)
        references = [
            {"role": "source", "media_type": reference.media_type, "identity": reference.identity}
            for reference in parsed_source_media_references(
                owner, document.source_text, metadata=document.metadata,
                semantic_tokens=parse_semantic_tokens(document.body, registry=None),
                doc_id=document.doc_id, document_collection=collection,
                exclude_media_types=frozenset({"thumbs"}),
            )
        ]
        documents.append({
            "target": {"collection": collection, "doc_id": document.doc_id},
            "title": document.title,
            "references": references,
        })
    return {
        "collection": collection,
        "title": owner.title if isinstance(owner, DocsCollectionConfig) else "Ordinary docs",
        "files": [asdict(file) for file in files],
        "documents": documents,
    }


def build_media_metadata(repo_root: Path, config: DocsStageConfig) -> dict[str, Any]:
    """Scan each configured owner once; return complete datasets without writing."""
    if config.stage != "working":
        raise ValueError("Docs Media generation requires Working")
    owners = []
    for owner in (config, *config.media_collections):
        label = owner.title if isinstance(owner, DocsCollectionConfig) else "Ordinary docs"
        try:
            owners.append(_owner_metadata(repo_root, owner))
        except (OSError, ValueError, RuntimeError) as error:
            raise ValueError(f"Docs Media scan failed for {label}; check its documents and media, then use Run/Refresh.") from error
    return {
        "schema_version": SCHEMA_VERSION,
        "refreshed_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "owners": owners,
    }


def read_media_metadata(repo_root: Path) -> dict[str, Any]:
    """Read the configured saved artifact only; a missing file means an empty report."""
    path = load_docs_workspace_config(repo_root).media_report_metadata.path
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {"ok": True, "metadata": None}
    except (OSError, UnicodeError) as error:
        raise ValueError("Docs Media metadata is unreadable. Use Run/Refresh to regenerate it.") from error
    try:
        metadata = validate_media_metadata(json.loads(text))
    except (ValueError, TypeError) as error:
        raise ValueError("Docs Media metadata is invalid. Use Run/Refresh to regenerate it.") from error
    return {"ok": True, "metadata": metadata}


def refresh_media_metadata(repo_root: Path) -> dict[str, Any]:
    """Await a complete scan before replacing the single report file; never retry."""
    workspace = load_docs_workspace_config(repo_root)
    metadata = build_media_metadata(repo_root, select_workspace_stage(workspace, "working"))
    path = workspace.media_report_metadata.path
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except OSError as error:
        raise ValueError("Docs Media metadata could not be saved. Use Run/Refresh to retry.") from error
    return {"ok": True, "metadata": metadata}
