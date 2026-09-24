#!/usr/bin/env python3
"""Read helpers for generated Docs Viewer JSON artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict
from urllib.parse import parse_qs, urlparse

from docs_document_identity import is_immutable_doc_id
from docs_document_location import management_collection_viewer_url, management_document_viewer_url
from docs_workspace_config import (
    DocsStageConfig,
    generated_documents_path,
    generated_search_path,
    load_docs_stage,
    resolve_workspace_path,
)


EXTERNAL_COLLECTION_GENERATED_PREFIX = "/docs/generated/external/"


def generated_stage_config(repo_root: Path, stage: str | None = None) -> DocsStageConfig:
    if stage != "working":
        raise ValueError("Generated reads require Working; use the Preview snapshot reader for Preview")
    return load_docs_stage(repo_root, stage)


def generated_docs_output_root(repo_root: Path, stage: str | None = None) -> Path:
    config = generated_stage_config(repo_root, stage)
    return resolve_workspace_path(repo_root, generated_documents_path(config))


def external_collection_payload_path(repo_root: Path, request_path: str, stage: str | None = None) -> Path:
    if not request_path.startswith(EXTERNAL_COLLECTION_GENERATED_PREFIX):
        raise ValueError("Invalid external Docs collection payload route")
    parts = request_path.removeprefix(EXTERNAL_COLLECTION_GENERATED_PREFIX).split("/")
    if len(parts) < 3:
        raise ValueError("Generated collection route requires stage, collection and artifact")
    route_stage, collection, *artifact = parts
    if stage is not None and stage != route_stage:
        raise ValueError("Conflicting generated stage target")
    config = generated_stage_config(repo_root, route_stage)
    selected = next((child for child in config.collections if child.collection == collection), None)
    if selected is None:
        raise FileNotFoundError(f"Docs collection not found: {collection}")
    if len(artifact) == 1 and artifact[0] in {"manifest.json", "manage-manifest.json", "subject-associations.json"}:
        relative_path = Path(artifact[0])
    elif len(artifact) == 2 and artifact[0] == "by-id" and artifact[1].endswith(".json") and is_immutable_doc_id(artifact[1][:-5]):
        relative_path = Path(*artifact)
    else:
        raise ValueError("Invalid external Docs collection payload route")
    output_root = resolve_workspace_path(repo_root, generated_documents_path(selected))
    path = (output_root / relative_path).resolve()
    if not path.is_relative_to(output_root):
        raise ValueError("Generated collection payload escapes its configured output")
    if not path.is_file():
        raise FileNotFoundError(f"Generated collection payload not found: {route_stage}/{collection}/{relative_path}")
    return path


def generated_docs_index_tree_path(repo_root: Path, stage: str | None = None) -> Path:
    return generated_docs_output_root(repo_root, stage) / "index-tree.json"


def generated_recent_path(repo_root: Path, stage: str | None = None) -> Path:
    return generated_docs_output_root(repo_root, stage) / "recent.json"


def generated_backlinks_path(repo_root: Path, stage: str | None = None) -> Path:
    return generated_docs_output_root(repo_root, stage) / "backlinks.json"


def generated_semantic_tokens_index_path(repo_root: Path, stage: str | None = None) -> Path:
    return generated_docs_output_root(repo_root, stage) / "semantic-tokens" / "index.json"


def generated_doc_payload_path(repo_root: Path, doc_id: str, stage: str | None = None) -> Path:
    if not is_immutable_doc_id(doc_id):
        raise ValueError("doc_id must use the immutable document ID format")
    return generated_docs_output_root(repo_root, stage) / "by-id" / f"{doc_id}.json"


def generated_search_index_path(repo_root: Path, stage: str | None = None) -> Path:
    config = generated_stage_config(repo_root, stage)
    return resolve_workspace_path(repo_root, generated_search_path(config))


def read_generated_doc_links(
    repo_root: Path, doc_id: str, collection: str = "", stage: str | None = None,
) -> Dict[str, Any]:
    """Read one configured relationship file and require its exact requested identity.

    This read does not build, repair, or search another collection or stage.
    """
    if not is_immutable_doc_id(doc_id):
        raise ValueError("doc_id must use the immutable document ID format")
    config = generated_stage_config(repo_root, stage)
    if collection and collection not in {child.collection for child in config.collections}:
        raise ValueError("Links collection must be an exact configured collection")
    output = resolve_workspace_path(repo_root, generated_documents_path(config)).resolve()
    directory = output / "links-by-id"
    path = directory / f"{doc_id}.json"
    if directory.is_symlink() or path.is_symlink() or path.resolve().parent != directory.resolve():
        raise ValueError("Links data must remain in its configured directory")
    payload = read_generated_json(path, "generated document Links")
    expected = {"stage": config.stage, "collection": collection, "doc_id": doc_id}
    summary = payload.get("self") if isinstance(payload, dict) else None
    if not isinstance(summary, dict) or summary.get("target") != expected:
        raise ValueError("Links data does not match the requested document")
    return payload


def read_generated_workspace_links(repo_root: Path, stage: str | None) -> Dict[str, Any]:
    """Read the last completed Working aggregate without building or scanning records."""
    if stage != "working":
        raise ValueError("Workspace Links is available only in Working")
    output = generated_docs_output_root(repo_root, stage).resolve()
    path = output / "links.json"
    if path.is_symlink():
        raise ValueError("Workspace Links data must remain in its configured directory")
    payload = read_generated_json(path, "generated workspace Links")
    if (
        not isinstance(payload, dict) or payload.get("schema_version") != 2
        or "scope" in payload or payload.get("stage") != stage
        or not isinstance(payload.get("documents"), list)
    ):
        raise ValueError("Workspace Links data does not match Working")
    return payload


def read_generated_json(path: Path, label: str) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"{label} not found: {path.name}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{label} is not valid JSON: {path.name}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"{label} must contain a JSON object: {path.name}")
    return payload


def generated_stage_data_available(repo_root: Path, stage: str | None = None) -> bool:
    return generated_docs_index_tree_path(repo_root, stage).exists()


def generated_search_data_available(repo_root: Path, stage: str | None = None) -> bool:
    return generated_search_index_path(repo_root, stage).exists()


def read_generated_docs_index_tree(repo_root: Path, stage: str | None = None) -> Dict[str, Any]:
    return read_generated_json(
        generated_docs_index_tree_path(repo_root, stage),
        f"generated docs index tree for {stage}",
    )


def read_generated_recent(repo_root: Path, stage: str | None = None) -> Dict[str, Any]:
    return read_generated_json(
        generated_recent_path(repo_root, stage),
        f"generated Recent docs for {stage}",
    )


def read_generated_backlinks(repo_root: Path, stage: str | None = None) -> Dict[str, Any]:
    return read_generated_json(
        generated_backlinks_path(repo_root, stage),
        f"generated backlinks for {stage}",
    )


def read_generated_semantic_tokens_index(repo_root: Path, stage: str | None = None) -> Dict[str, Any]:
    """Read usage plus exact generated source titles and stage-owned report locations.

    Source summaries are response-only. Never infer a collection from a document
    ID or use publication eligibility to omit an indexed occurrence.
    """
    config = generated_stage_config(repo_root, stage)
    payload = read_generated_json(
        generated_semantic_tokens_index_path(repo_root, stage),
        f"generated semantic-token usage index for {stage}",
    )
    if payload.get("schema_version") != "docs_semantic_token_usage_index_v2" or "scope" in payload or payload.get("stage") != config.stage or not isinstance(payload.get("occurrences"), list):
        raise ValueError("Semantic-token index does not match its requested stage")
    owners = {"": config, **{child.collection: child for child in config.collections}}
    documents: dict[tuple[str, str], dict[str, Any]] = {}
    collection_urls: dict[str, str] = {}
    for occurrence in payload["occurrences"]:
        if not isinstance(occurrence, dict) or "source_scope" in occurrence or occurrence.get("source_stage") != config.stage:
            raise ValueError("Semantic-token occurrence has invalid source stage")
        collection = occurrence.get("source_collection")
        doc_id = occurrence.get("source_doc_id")
        if collection not in owners or not is_immutable_doc_id(doc_id):
            raise ValueError("Semantic-token source must identify an exact configured document")
        key = (collection, doc_id)
        if key in documents:
            continue
        output = resolve_workspace_path(repo_root, generated_documents_path(owners[collection]))
        document = read_generated_json(output / "by-id" / f"{doc_id}.json", "semantic-token source document")
        if document.get("doc_id") != doc_id or not isinstance(document.get("title"), str):
            raise ValueError("Semantic-token source payload does not match its document")
        if collection not in collection_urls:
            collection_urls[collection] = management_collection_viewer_url(repo_root, collection, stage=config.stage)
        documents[key] = {
            "target": {"stage": config.stage, "collection": collection, "doc_id": doc_id},
            "title": document["title"],
            "href": management_document_viewer_url(collection_urls[collection], doc_id, collection=bool(collection)),
        }
    return {**payload, "stage": config.stage, "source_documents": list(documents.values())}


def read_generated_search_index(repo_root: Path, stage: str | None = None) -> Dict[str, Any]:
    return read_generated_json(
        generated_search_index_path(repo_root, stage),
        f"generated search index for {stage}",
    )


def read_generated_doc_payload(repo_root: Path, doc_id: str, stage: str | None = None) -> Dict[str, Any]:
    if not is_immutable_doc_id(doc_id):
        raise ValueError("doc_id must use the immutable document ID format")

    index_payload = read_generated_docs_index_tree(repo_root, stage)
    docs = index_payload.get("docs")
    if not isinstance(docs, list):
        raise RuntimeError(f"generated docs index tree for {stage} is missing docs")

    record = find_generated_doc_record(docs, doc_id)
    if record is None:
        raise FileNotFoundError(f"generated doc payload for {doc_id} not found")

    config = generated_stage_config(repo_root, stage)
    content_url = str(record.get("content_url") or "").strip()
    parsed = urlparse(content_url)
    if parsed.scheme or parsed.netloc or parsed.path != "/docs/doc" or parse_qs(parsed.query) != {"stage": [config.stage], "doc_id": [doc_id]}:
        raise RuntimeError(f"generated docs index tree has an unexpected payload target for {doc_id}")

    return read_generated_json(
        generated_doc_payload_path(repo_root, doc_id, stage),
        f"generated doc payload for {doc_id}",
    )


def find_generated_doc_record(docs: list[Any], doc_id: str) -> Dict[str, Any] | None:
    stack = [doc for doc in docs if isinstance(doc, dict)]
    while stack:
        record = stack.pop(0)
        if record.get("doc_id") == doc_id:
            return record
        children = record.get("children")
        if isinstance(children, list):
            stack.extend(child for child in children if isinstance(child, dict))
    return None
