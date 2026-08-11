#!/usr/bin/env python3
"""Plan the one-time Registry-v5 Tag document-link ownership cutover."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import PurePosixPath
from typing import Any, Mapping, Sequence

import docs_source_model
from docs_document_identity import is_immutable_doc_id
from docs_tag_documents import normalize_tag_declaration
from tags import tag_source_model as tag_source


PLAN_VERSION = "tag_document_link_migration_plan_v1"
SOURCE_REGISTRY_VERSION = "tag_registry_v5"
TARGET_REGISTRY_VERSION = "tag_registry_v6"
LEGACY_ROW_KEYS = frozenset(("tag_id", "group", "doc_url", "updated_at_utc"))


def canonical_json_text(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_text(payload: str) -> str:
    return sha256_bytes(payload.encode("utf-8"))


def canonical_json_sha256(payload: Any) -> str:
    return sha256_text(canonical_json_text(payload))


def validate_legacy_registry(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    if payload.get("tag_registry_version") != SOURCE_REGISTRY_VERSION:
        raise ValueError(
            f"Tag document link migration requires {SOURCE_REGISTRY_VERSION}"
        )
    raw_tags = payload.get("tags")
    if not isinstance(raw_tags, list):
        raise ValueError("tag_registry.tags must be an array")
    allowed_groups = tag_source.extract_allowed_groups(dict(payload))
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw_row in enumerate(raw_tags):
        field = f"tag_registry.tags[{index}]"
        if not isinstance(raw_row, dict) or set(raw_row) != LEGACY_ROW_KEYS:
            raise ValueError(f"{field} must use the exact Registry v5 row schema")
        tag_id = tag_source.sanitize_tag_id(raw_row.get("tag_id"), f"{field}.tag_id")
        if tag_id in seen:
            raise ValueError(f"{field} duplicates tag_id {tag_id!r}")
        seen.add(tag_id)
        group = tag_source.sanitize_group(
            raw_row.get("group"),
            allowed_groups,
            f"{field}.group",
        )
        urls = tag_source.sanitize_tag_document_urls(
            raw_row.get("doc_url"),
            f"{field}.doc_url",
        )
        updated_at_utc = raw_row.get("updated_at_utc")
        if not isinstance(updated_at_utc, str):
            raise ValueError(f"{field}.updated_at_utc must be a string")
        rows.append(
            {
                "tag_id": tag_id,
                "group": group,
                "doc_url": urls,
                "updated_at_utc": updated_at_utc,
            }
        )
    return rows


def normalize_documents(documents: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    for index, raw in enumerate(documents):
        doc_id = str(raw.get("doc_id") or "").strip()
        relative_path = str(raw.get("relative_path") or "").strip()
        source_text = str(raw.get("source_text") or "")
        source_sha256 = str(raw.get("source_sha256") or "").strip()
        path = PurePosixPath(relative_path)
        if not is_immutable_doc_id(doc_id):
            raise ValueError(f"documents[{index}].doc_id is invalid")
        if (
            not relative_path
            or path.is_absolute()
            or ".." in path.parts
            or path.name != f"{doc_id}.md"
        ):
            raise ValueError(f"documents[{index}].relative_path is invalid")
        if doc_id in seen_ids or relative_path in seen_paths:
            raise ValueError(f"documents[{index}] duplicates source identity")
        if source_sha256 != sha256_text(source_text):
            raise ValueError(f"documents[{index}].source_sha256 does not match source")
        front_matter, _body = docs_source_model.parse_source_text(
            source_text,
            source_name=relative_path,
        )
        if str(front_matter.get("doc_id") or "").strip() != doc_id:
            raise ValueError(f"documents[{index}] source doc_id does not match")
        seen_ids.add(doc_id)
        seen_paths.add(relative_path)
        normalized.append(
            {
                "doc_id": doc_id,
                "relative_path": relative_path,
                "source_sha256": source_sha256,
                "source_text": source_text,
                "title": str(raw.get("title") or doc_id).strip() or doc_id,
                "front_matter": front_matter,
            }
        )
    return sorted(normalized, key=lambda row: row["doc_id"])


def insert_tag_id(source_text: str, tag_id: str, *, source_name: str) -> str:
    front_source, front_matter, body = docs_source_model.split_source_text(
        source_text,
        source_name=source_name,
    )
    if "tag_id" in front_matter:
        raise ValueError(f"{source_name} already contains tag_id")
    lines = front_source.splitlines(keepends=True)
    closing_index = max(
        index for index, line in enumerate(lines) if line.strip() == "---"
    )
    insert_index = closing_index
    for index, line in enumerate(lines[:closing_index]):
        if line.split(":", 1)[0].strip() == "group":
            insert_index = index + 1
            break
    newline = "\r\n" if "\r\n" in front_source else "\n"
    lines.insert(insert_index, f"tag_id: {tag_id}{newline}")
    return "".join(lines) + body


def _location_map(
    locations: Sequence[Mapping[str, Any]],
) -> dict[str, dict[str, str]]:
    by_url: dict[str, dict[str, str]] = {}
    for index, raw in enumerate(locations):
        url = str(raw.get("url") or "").strip()
        scope = str(raw.get("scope_id") or "").strip()
        sub_scope = str(raw.get("sub_scope") or "").strip()
        doc_id = str(raw.get("doc_id") or "").strip()
        if scope != "analysis" or sub_scope != "tags" or not is_immutable_doc_id(doc_id):
            continue
        if not url or url in by_url:
            raise ValueError(f"locations[{index}] has duplicate or missing URL")
        by_url[url] = {
            "scope": scope,
            "sub_scope": sub_scope,
            "doc_id": doc_id,
            "title": str(raw.get("document_title") or doc_id).strip() or doc_id,
        }
    return by_url


def _association_rows(declarations: Mapping[str, str]) -> list[dict[str, Any]]:
    documents_by_tag: dict[str, list[dict[str, str]]] = {}
    for doc_id, tag_id in declarations.items():
        documents_by_tag.setdefault(tag_id, []).append(
            {"scope": "analysis", "sub_scope": "tags", "doc_id": doc_id}
        )
    return [
        {
            "tag_id": tag_id,
            "documents": sorted(
                documents,
                key=lambda target: (
                    target["scope"],
                    target["sub_scope"],
                    target["doc_id"],
                ),
            ),
        }
        for tag_id, documents in sorted(documents_by_tag.items())
    ]


def build_migration_plan(
    registry_payload: Mapping[str, Any],
    documents: Sequence[Mapping[str, Any]],
    locations: Sequence[Mapping[str, Any]],
    *,
    created_at_utc: str,
    input_fingerprints: Mapping[str, str],
) -> dict[str, Any]:
    legacy_rows = validate_legacy_registry(registry_payload)
    normalized_documents = normalize_documents(documents)
    documents_by_id = {row["doc_id"]: row for row in normalized_documents}
    locations_by_url = _location_map(locations)
    tag_ids = {row["tag_id"] for row in legacy_rows}

    declarations: dict[str, str] = {}
    declaration_states: dict[str, dict[str, Any]] = {}
    for document in normalized_documents:
        state = normalize_tag_declaration(document["front_matter"])
        declaration_states[document["doc_id"]] = state
        if state["state"] == "valid":
            declarations[document["doc_id"]] = str(state["tag_id"])

    resolved: list[dict[str, Any]] = []
    unresolved: list[dict[str, str]] = []
    requests_by_doc: dict[str, list[tuple[str, str]]] = {}
    first_target_by_tag: dict[str, dict[str, str]] = {}
    for row in legacy_rows:
        for index, url in enumerate(row["doc_url"]):
            target = locations_by_url.get(url)
            if target is None or target["doc_id"] not in documents_by_id:
                unresolved.append({"tag_id": row["tag_id"], "url": url})
                continue
            record = {
                "tag_id": row["tag_id"],
                "url": url,
                "target": {
                    "scope": target["scope"],
                    "sub_scope": target["sub_scope"],
                    "doc_id": target["doc_id"],
                },
                "title": target["title"],
            }
            resolved.append(record)
            requests_by_doc.setdefault(target["doc_id"], []).append(
                (row["tag_id"], url)
            )
            if index == 0:
                first_target_by_tag[row["tag_id"]] = record["target"]

    blocking_conflicts: list[dict[str, Any]] = []
    source_edits: list[dict[str, str]] = []
    for doc_id, requests in sorted(requests_by_doc.items()):
        requested_tags = sorted({tag_id for tag_id, _url in requests})
        state = declaration_states[doc_id]
        if len(requested_tags) != 1:
            blocking_conflicts.append(
                {
                    "doc_id": doc_id,
                    "reason": "several_tags_target_one_document",
                    "tag_ids": requested_tags,
                }
            )
            continue
        requested_tag = requested_tags[0]
        if state["state"] == "valid" and state["tag_id"] == requested_tag:
            declarations[doc_id] = requested_tag
            continue
        if state["state"] != "none":
            blocking_conflicts.append(
                {
                    "doc_id": doc_id,
                    "reason": "existing_declaration_conflicts",
                    "tag_ids": requested_tags,
                    "existing_state": state,
                }
            )
            continue
        document = documents_by_id[doc_id]
        projected_source = insert_tag_id(
            document["source_text"],
            requested_tag,
            source_name=document["relative_path"],
        )
        declarations[doc_id] = requested_tag
        source_edits.append(
            {
                "tag_id": requested_tag,
                "doc_id": doc_id,
                "relative_path": document["relative_path"],
                "input_sha256": document["source_sha256"],
                "output_sha256": sha256_text(projected_source),
                "source_text": projected_source,
            }
        )

    expected_associations = _association_rows(declarations)
    associated_doc_ids = {
        document["doc_id"]
        for association in expected_associations
        for document in association["documents"]
    }

    projected_rows: list[dict[str, Any]] = []
    primary_count = 0
    associations_by_tag = {
        row["tag_id"]: row["documents"] for row in expected_associations
    }
    for row in legacy_rows:
        projected_row: dict[str, Any] = {
            "tag_id": row["tag_id"],
            "group": row["group"],
            "updated_at_utc": row["updated_at_utc"],
        }
        documents_for_tag = associations_by_tag.get(row["tag_id"], [])
        first_target = first_target_by_tag.get(row["tag_id"])
        if len(documents_for_tag) > 1 and first_target in documents_for_tag:
            projected_row["primary_document"] = first_target
            projected_row["updated_at_utc"] = created_at_utc
            primary_count += 1
        projected_rows.append(projected_row)

    projected_registry = copy.deepcopy(dict(registry_payload))
    projected_registry["tag_registry_version"] = TARGET_REGISTRY_VERSION
    projected_registry["updated_at_utc"] = created_at_utc
    projected_registry["tags"] = projected_rows
    registry_stats = tag_source.validate_registry_payload(projected_registry)

    unassociated_documents = [
        {
            "doc_id": row["doc_id"],
            "title": row["title"],
            "current_tag_id": declarations.get(row["doc_id"], ""),
        }
        for row in normalized_documents
        if row["doc_id"] not in associated_doc_ids
    ]
    plan = {
        "plan_version": PLAN_VERSION,
        "created_at_utc": created_at_utc,
        "input": {
            "registry_version": SOURCE_REGISTRY_VERSION,
            "fingerprints": dict(input_fingerprints),
            "tag_count": len(legacy_rows),
            "document_count": len(normalized_documents),
            "legacy_url_count": sum(len(row["doc_url"]) for row in legacy_rows),
        },
        "output": {
            "registry_version": TARGET_REGISTRY_VERSION,
            "registry_sha256": canonical_json_sha256(projected_registry),
            "source_edit_count": len(source_edits),
            "resolved_legacy_url_count": len(resolved),
            "unresolved_legacy_url_count": len(unresolved),
            "blocking_conflict_count": len(blocking_conflicts),
            "association_tag_count": len(expected_associations),
            "associated_document_count": len(associated_doc_ids),
            "primary_document_count": primary_count,
            **registry_stats,
        },
        "resolved_legacy": resolved,
        "unresolved_legacy": unresolved,
        "blocking_conflicts": blocking_conflicts,
        "unassociated_documents": unassociated_documents,
        "source_edits": source_edits,
        "expected_associations": expected_associations,
        "projected_registry": projected_registry,
        "known_registry_tag_ids": sorted(tag_ids),
    }
    return plan


def validate_migration_plan(
    plan: Mapping[str, Any],
    registry_payload: Mapping[str, Any],
    documents: Sequence[Mapping[str, Any]],
    locations: Sequence[Mapping[str, Any]],
    *,
    input_fingerprints: Mapping[str, str],
) -> dict[str, int]:
    if plan.get("plan_version") != PLAN_VERSION:
        raise ValueError(f"migration plan must use {PLAN_VERSION}")
    expected = build_migration_plan(
        registry_payload,
        documents,
        locations,
        created_at_utc=str(plan.get("created_at_utc") or ""),
        input_fingerprints=input_fingerprints,
    )
    if dict(plan) != expected:
        raise ValueError("migration plan does not match current canonical input")
    if expected["blocking_conflicts"]:
        raise ValueError("migration plan contains blocking document conflicts")
    return {
        key: int(expected["output"][key])
        for key in (
            "source_edit_count",
            "resolved_legacy_url_count",
            "unresolved_legacy_url_count",
            "association_tag_count",
            "associated_document_count",
            "primary_document_count",
        )
    }


__all__ = [
    "PLAN_VERSION",
    "SOURCE_REGISTRY_VERSION",
    "TARGET_REGISTRY_VERSION",
    "build_migration_plan",
    "canonical_json_sha256",
    "canonical_json_text",
    "normalize_documents",
    "sha256_bytes",
    "sha256_text",
    "validate_legacy_registry",
    "validate_migration_plan",
]
