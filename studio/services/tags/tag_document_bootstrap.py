#!/usr/bin/env python3
"""Plan and validate the one-time canonical tag-document bootstrap."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import PurePosixPath
from typing import Any, Callable, Dict, Iterable

from tags import tag_flat_identity_migration
from tags import tag_source_model as tag_source


PLAN_VERSION = "tag_document_bootstrap_plan_v1"
SOURCE_REGISTRY_VERSION = "tag_registry_v3"
TARGET_REGISTRY_VERSION = "tag_registry_v4"
DEFAULT_DOCUMENTS_ROOT = (
    "docs-viewer/scopes/analysis/source/sub-scopes/tags/documents"
)

AllocateDocumentId = Callable[[str, Iterable[str]], str]
DocumentIdPredicate = Callable[[Any], bool]
DocumentDatePredicate = Callable[[str, str], bool]


def canonical_json_text(payload: Any) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
        sort_keys=False,
    ) + "\n"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_text(payload: str) -> str:
    return sha256_bytes(payload.encode("utf-8"))


def canonical_json_sha256(payload: Any) -> str:
    return sha256_text(canonical_json_text(payload))


def _normalized_relative_path(raw_path: Any, field_name: str) -> str:
    value = str(raw_path or "").strip()
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{field_name} must be a confined repository-relative path")
    return path.as_posix()


def normalize_document_inventory(records: Any) -> list[Dict[str, str]]:
    if not isinstance(records, list):
        raise ValueError("document inventory must be an array")
    normalized: list[Dict[str, str]] = []
    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    for idx, raw_record in enumerate(records):
        if not isinstance(raw_record, dict):
            raise ValueError(f"document inventory[{idx}] must be an object")
        doc_id = str(raw_record.get("doc_id") or "").strip()
        path = _normalized_relative_path(
            raw_record.get("relative_path"),
            f"document inventory[{idx}].relative_path",
        )
        source_sha256 = str(raw_record.get("source_sha256") or "").strip()
        if len(source_sha256) != 64:
            raise ValueError(
                f"document inventory[{idx}].source_sha256 must be a SHA-256 digest"
            )
        if doc_id in seen_ids:
            raise ValueError(f"document inventory duplicates doc_id '{doc_id}'")
        if path in seen_paths:
            raise ValueError(f"document inventory duplicates path '{path}'")
        seen_ids.add(doc_id)
        seen_paths.add(path)
        normalized.append(
            {
                "doc_id": doc_id,
                "relative_path": path,
                "source_sha256": source_sha256,
            }
        )
    return sorted(normalized, key=lambda record: record["relative_path"])


def document_inventory_sha256(records: Any) -> str:
    return canonical_json_sha256(normalize_document_inventory(records))


def render_tag_document_source(
    *,
    tag_id: str,
    group: str,
    description: str,
    doc_id: str,
    added_date: str,
) -> str:
    last_updated = added_date.split(" ", 1)[0]
    body = f"# {tag_id}\n\n**{group}**"
    if description:
        body += f"\n\n{description}"
    return (
        "---\n"
        f"doc_id: {doc_id}\n"
        f"title: {json.dumps(tag_id, ensure_ascii=False)}\n"
        f"added_date: {json.dumps(added_date, ensure_ascii=False)}\n"
        f"last_updated: {json.dumps(last_updated, ensure_ascii=False)}\n"
        'parent_id: ""\n'
        "---\n"
        f"{body}\n"
    )


def _validate_existing_documents(
    records: list[Dict[str, str]],
    *,
    is_immutable_doc_id: DocumentIdPredicate,
) -> None:
    for idx, record in enumerate(records):
        if not is_immutable_doc_id(record["doc_id"]):
            raise ValueError(
                f"document inventory[{idx}].doc_id must use immutable document identity"
            )
        if PurePosixPath(record["relative_path"]).name != f"{record['doc_id']}.md":
            raise ValueError(
                f"document inventory[{idx}] filename must match its doc_id"
            )


def _validated_source_rows(
    registry_payload: Dict[str, Any],
) -> tuple[list[Dict[str, Any]], list[str]]:
    if registry_payload.get("tag_registry_version") != SOURCE_REGISTRY_VERSION:
        raise ValueError(
            f"tag document bootstrap requires {SOURCE_REGISTRY_VERSION}"
        )
    raw_tags = registry_payload.get("tags")
    if not isinstance(raw_tags, list) or not raw_tags:
        raise ValueError("tag_registry.tags must be a non-empty array")
    allowed_groups = tag_source.extract_allowed_groups(registry_payload)
    rows: list[Dict[str, Any]] = []
    tag_ids: list[str] = []
    seen_tag_ids: set[str] = set()
    for idx, raw_tag in enumerate(raw_tags):
        if not isinstance(raw_tag, dict):
            raise ValueError(f"tag_registry.tags[{idx}] must be an object")
        tag_id = tag_source.sanitize_tag_id(
            raw_tag.get("tag_id"),
            f"tag_registry.tags[{idx}].tag_id",
        )
        if tag_id in seen_tag_ids:
            raise ValueError(f"tag_registry.tags[{idx}] duplicates tag_id '{tag_id}'")
        seen_tag_ids.add(tag_id)
        group = tag_source.sanitize_group(
            raw_tag.get("group"),
            allowed_groups,
            f"tag_registry.tags[{idx}].group",
        )
        if "groups" in raw_tag or isinstance(raw_tag.get("group"), list):
            raise ValueError(f"tag_registry.tags[{idx}] must have one scalar group")
        if "label" in raw_tag:
            raise ValueError(f"tag_registry.tags[{idx}] must not include label")
        if "doc_id" in raw_tag:
            raise ValueError(
                f"tag_registry.tags[{idx}] already contains doc_id"
            )
        description = raw_tag.get("description")
        if not isinstance(description, str):
            raise ValueError(
                f"tag_registry.tags[{idx}].description must be a string"
            )
        normalized = copy.deepcopy(raw_tag)
        normalized["tag_id"] = tag_id
        normalized["group"] = group
        rows.append(normalized)
        tag_ids.append(tag_id)
    return rows, tag_ids


def _validate_input_fingerprints(raw_fingerprints: Any) -> Dict[str, str]:
    expected_keys = {
        "registry_sha256",
        "aliases_sha256",
        "assignments_sha256",
        "documents_sha256",
    }
    if not isinstance(raw_fingerprints, dict):
        raise ValueError("input fingerprints must be an object")
    if set(raw_fingerprints) != expected_keys:
        raise ValueError(
            "input fingerprints must contain registry, aliases, assignments, "
            "and documents SHA-256 values"
        )
    fingerprints: Dict[str, str] = {}
    for key in sorted(expected_keys):
        value = str(raw_fingerprints.get(key) or "").strip()
        if len(value) != 64:
            raise ValueError(f"input fingerprints.{key} must be a SHA-256 digest")
        fingerprints[key] = value
    return fingerprints


def build_tag_document_bootstrap_plan(
    registry_payload: Dict[str, Any],
    aliases_payload: Dict[str, Any],
    assignments_payload: Dict[str, Any],
    existing_documents: Any,
    *,
    added_date: str,
    created_at_utc: str,
    input_fingerprints: Dict[str, str],
    allocate_document_id: AllocateDocumentId,
    is_immutable_doc_id: DocumentIdPredicate,
    doc_id_matches_added_date: DocumentDatePredicate,
    documents_root: str = DEFAULT_DOCUMENTS_ROOT,
) -> Dict[str, Any]:
    fingerprints = _validate_input_fingerprints(input_fingerprints)
    inventory = normalize_document_inventory(existing_documents)
    if fingerprints["documents_sha256"] != document_inventory_sha256(inventory):
        raise ValueError("document inventory fingerprint does not match inventory")
    _validate_existing_documents(
        inventory,
        is_immutable_doc_id=is_immutable_doc_id,
    )
    source_rows, tag_ids = _validated_source_rows(registry_payload)
    tag_flat_identity_migration.validate_flat_identity_sources(
        registry_payload,
        aliases_payload,
        assignments_payload,
        expected_registry_version=SOURCE_REGISTRY_VERSION,
    )

    normalized_root = _normalized_relative_path(
        documents_root,
        "documents_root",
    ).rstrip("/")
    unavailable_ids = {record["doc_id"] for record in inventory}
    planned_documents: list[Dict[str, str]] = []
    projected_rows: list[Dict[str, Any]] = []
    for idx, raw_tag in enumerate(source_rows):
        tag_id = raw_tag["tag_id"]
        group = raw_tag["group"]
        description = raw_tag["description"]
        doc_id = allocate_document_id(added_date, unavailable_ids)
        if not is_immutable_doc_id(doc_id):
            raise ValueError(
                f"allocated doc_id for tag_registry.tags[{idx}] is not immutable"
            )
        if not doc_id_matches_added_date(doc_id, added_date):
            raise ValueError(
                f"allocated doc_id for tag_registry.tags[{idx}] does not match added_date"
            )
        if doc_id in unavailable_ids:
            raise ValueError(f"allocated duplicate doc_id '{doc_id}'")
        unavailable_ids.add(doc_id)
        relative_path = f"{normalized_root}/{doc_id}.md"
        source_text = render_tag_document_source(
            tag_id=tag_id,
            group=group,
            description=description,
            doc_id=doc_id,
            added_date=added_date,
        )
        planned_documents.append(
            {
                "tag_id": tag_id,
                "group": group,
                "doc_id": doc_id,
                "relative_path": relative_path,
                "source_sha256": sha256_text(source_text),
                "source_text": source_text,
            }
        )
        projected_row = copy.deepcopy(raw_tag)
        projected_row["doc_id"] = doc_id
        projected_rows.append(projected_row)

    projected_registry = copy.deepcopy(registry_payload)
    projected_registry["tag_registry_version"] = TARGET_REGISTRY_VERSION
    projected_registry["updated_at_utc"] = created_at_utc
    projected_registry["tags"] = projected_rows
    reconciliation = tag_flat_identity_migration.validate_flat_identity_sources(
        projected_registry,
        aliases_payload,
        assignments_payload,
        expected_registry_version=TARGET_REGISTRY_VERSION,
    )
    plan: Dict[str, Any] = {
        "plan_version": PLAN_VERSION,
        "created_at_utc": created_at_utc,
        "added_date": added_date,
        "documents_root": normalized_root,
        "input": {
            "fingerprints": fingerprints,
            "registry_version": SOURCE_REGISTRY_VERSION,
            "tag_ids": tag_ids,
            "existing_documents": inventory,
        },
        "output": {
            "registry_version": TARGET_REGISTRY_VERSION,
            "projected_registry_sha256": canonical_json_sha256(
                projected_registry
            ),
            "mapping_sha256": canonical_json_sha256(planned_documents),
            "new_document_count": len(planned_documents),
            "final_document_count": len(inventory) + len(planned_documents),
            **reconciliation,
        },
        "documents": planned_documents,
        "projected_registry": projected_registry,
    }
    validate_tag_document_bootstrap_plan(
        plan,
        registry_payload,
        aliases_payload,
        assignments_payload,
        inventory,
        input_fingerprints=fingerprints,
        is_immutable_doc_id=is_immutable_doc_id,
        doc_id_matches_added_date=doc_id_matches_added_date,
    )
    return plan


def validate_tag_document_bootstrap_plan(
    plan: Any,
    registry_payload: Dict[str, Any],
    aliases_payload: Dict[str, Any],
    assignments_payload: Dict[str, Any],
    existing_documents: Any,
    *,
    input_fingerprints: Dict[str, str],
    is_immutable_doc_id: DocumentIdPredicate,
    doc_id_matches_added_date: DocumentDatePredicate,
) -> Dict[str, int]:
    if not isinstance(plan, dict) or plan.get("plan_version") != PLAN_VERSION:
        raise ValueError(f"bootstrap plan must use {PLAN_VERSION}")
    fingerprints = _validate_input_fingerprints(input_fingerprints)
    plan_input = plan.get("input")
    if not isinstance(plan_input, dict):
        raise ValueError("bootstrap plan input must be an object")
    if plan_input.get("fingerprints") != fingerprints:
        raise ValueError("bootstrap plan input fingerprints do not match live source")
    inventory = normalize_document_inventory(existing_documents)
    if plan_input.get("existing_documents") != inventory:
        raise ValueError("bootstrap plan document inventory does not match live source")
    if fingerprints["documents_sha256"] != document_inventory_sha256(inventory):
        raise ValueError("live document inventory fingerprint does not match inventory")
    _validate_existing_documents(
        inventory,
        is_immutable_doc_id=is_immutable_doc_id,
    )
    source_rows, tag_ids = _validated_source_rows(registry_payload)
    if plan_input.get("tag_ids") != tag_ids:
        raise ValueError("bootstrap plan tag order does not match live registry")
    tag_flat_identity_migration.validate_flat_identity_sources(
        registry_payload,
        aliases_payload,
        assignments_payload,
        expected_registry_version=SOURCE_REGISTRY_VERSION,
    )

    documents_root = _normalized_relative_path(
        plan.get("documents_root"),
        "bootstrap plan documents_root",
    ).rstrip("/")
    added_date = str(plan.get("added_date") or "").strip()
    created_at_utc = str(plan.get("created_at_utc") or "").strip()
    raw_documents = plan.get("documents")
    if not isinstance(raw_documents, list) or len(raw_documents) != len(source_rows):
        raise ValueError("bootstrap plan must contain one document per registry tag")
    existing_ids = {record["doc_id"] for record in inventory}
    planned_ids: set[str] = set()
    projected_rows: list[Dict[str, Any]] = []
    for idx, (raw_tag, raw_document) in enumerate(
        zip(source_rows, raw_documents, strict=True)
    ):
        if not isinstance(raw_document, dict):
            raise ValueError(f"bootstrap plan documents[{idx}] must be an object")
        tag_id = str(raw_document.get("tag_id") or "").strip()
        group = str(raw_document.get("group") or "").strip()
        doc_id = str(raw_document.get("doc_id") or "").strip()
        relative_path = _normalized_relative_path(
            raw_document.get("relative_path"),
            f"bootstrap plan documents[{idx}].relative_path",
        )
        source_text = str(raw_document.get("source_text") or "")
        if tag_id != raw_tag["tag_id"] or group != raw_tag["group"]:
            raise ValueError(
                f"bootstrap plan documents[{idx}] does not match registry row"
            )
        if not is_immutable_doc_id(doc_id):
            raise ValueError(
                f"bootstrap plan documents[{idx}].doc_id is not immutable"
            )
        if not doc_id_matches_added_date(doc_id, added_date):
            raise ValueError(
                f"bootstrap plan documents[{idx}].doc_id does not match added_date"
            )
        if doc_id in existing_ids or doc_id in planned_ids:
            raise ValueError(f"bootstrap plan duplicates doc_id '{doc_id}'")
        planned_ids.add(doc_id)
        if relative_path != f"{documents_root}/{doc_id}.md":
            raise ValueError(
                f"bootstrap plan documents[{idx}] target path does not match doc_id"
            )
        expected_source = render_tag_document_source(
            tag_id=tag_id,
            group=group,
            description=raw_tag["description"],
            doc_id=doc_id,
            added_date=added_date,
        )
        if source_text != expected_source:
            raise ValueError(
                f"bootstrap plan documents[{idx}] source does not match template"
            )
        if raw_document.get("source_sha256") != sha256_text(source_text):
            raise ValueError(
                f"bootstrap plan documents[{idx}] source fingerprint is invalid"
            )
        projected_row = copy.deepcopy(raw_tag)
        projected_row["doc_id"] = doc_id
        projected_rows.append(projected_row)

    expected_registry = copy.deepcopy(registry_payload)
    expected_registry["tag_registry_version"] = TARGET_REGISTRY_VERSION
    expected_registry["updated_at_utc"] = created_at_utc
    expected_registry["tags"] = projected_rows
    if plan.get("projected_registry") != expected_registry:
        raise ValueError("bootstrap plan projected registry does not match source")
    reconciliation = tag_flat_identity_migration.validate_flat_identity_sources(
        expected_registry,
        aliases_payload,
        assignments_payload,
        expected_registry_version=TARGET_REGISTRY_VERSION,
    )
    output = plan.get("output")
    if not isinstance(output, dict):
        raise ValueError("bootstrap plan output must be an object")
    expected_output = {
        "registry_version": TARGET_REGISTRY_VERSION,
        "projected_registry_sha256": canonical_json_sha256(expected_registry),
        "mapping_sha256": canonical_json_sha256(raw_documents),
        "new_document_count": len(raw_documents),
        "final_document_count": len(inventory) + len(raw_documents),
        **reconciliation,
    }
    if output != expected_output:
        raise ValueError("bootstrap plan output reconciliation is invalid")
    return {
        "tag_count": len(source_rows),
        "existing_document_count": len(inventory),
        "new_document_count": len(raw_documents),
        "final_document_count": len(inventory) + len(raw_documents),
    }


def validate_applied_tag_document_bootstrap(
    plan: Any,
    registry_payload: Dict[str, Any],
    aliases_payload: Dict[str, Any],
    assignments_payload: Dict[str, Any],
    documents: Any,
    *,
    registry_sha256: str,
    aliases_sha256: str,
    assignments_sha256: str,
    is_immutable_doc_id: DocumentIdPredicate,
) -> Dict[str, int]:
    if not isinstance(plan, dict) or plan.get("plan_version") != PLAN_VERSION:
        raise ValueError(f"bootstrap plan must use {PLAN_VERSION}")
    plan_input = plan.get("input")
    plan_output = plan.get("output")
    if not isinstance(plan_input, dict) or not isinstance(plan_output, dict):
        raise ValueError("bootstrap plan input and output must be objects")
    fingerprints = _validate_input_fingerprints(plan_input.get("fingerprints"))
    if aliases_sha256 != fingerprints["aliases_sha256"]:
        raise ValueError("aliases changed since bootstrap preview")
    if assignments_sha256 != fingerprints["assignments_sha256"]:
        raise ValueError("assignments changed since bootstrap preview")
    if registry_payload != plan.get("projected_registry"):
        raise ValueError("applied registry does not match reviewed projection")
    if registry_sha256 != plan_output.get("projected_registry_sha256"):
        raise ValueError("applied registry fingerprint does not match projection")
    reconciliation = tag_flat_identity_migration.validate_flat_identity_sources(
        registry_payload,
        aliases_payload,
        assignments_payload,
        expected_registry_version=TARGET_REGISTRY_VERSION,
    )

    inventory = normalize_document_inventory(documents)
    _validate_existing_documents(
        inventory,
        is_immutable_doc_id=is_immutable_doc_id,
    )
    actual_by_path = {record["relative_path"]: record for record in inventory}
    expected_by_path = {
        record["relative_path"]: record
        for record in normalize_document_inventory(
            plan_input.get("existing_documents")
        )
    }
    raw_documents = plan.get("documents")
    if not isinstance(raw_documents, list):
        raise ValueError("bootstrap plan documents must be an array")
    for idx, raw_document in enumerate(raw_documents):
        if not isinstance(raw_document, dict):
            raise ValueError(f"bootstrap plan documents[{idx}] must be an object")
        expected_by_path[str(raw_document["relative_path"])] = {
            "doc_id": str(raw_document["doc_id"]),
            "relative_path": str(raw_document["relative_path"]),
            "source_sha256": str(raw_document["source_sha256"]),
        }
    if actual_by_path != expected_by_path:
        raise ValueError("applied document inventory does not match reviewed plan")
    return {
        "tag_count": reconciliation["tag_count"],
        "linked_document_count": len(raw_documents),
        "existing_document_count": len(plan_input["existing_documents"]),
        "final_document_count": len(inventory),
        "alias_count": reconciliation["alias_count"],
        "alias_target_count": reconciliation["alias_target_count"],
        "assignment_reference_count": reconciliation[
            "assignment_reference_count"
        ],
    }
