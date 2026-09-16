#!/usr/bin/env python3
"""Private Working-owned Editorial document lineage."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping

import docs_source_model as source_model
from docs_workspace_config import (
    document_source_path,
    load_docs_stage,
    resolve_workspace_path,
)
from docs_collection_customisations import (
    LINEAGE_EDITORIAL_ROLE,
    LINEAGE_SOURCE_ROLE,
    collection_customisation_document_lineage_contracts,
)


LINEAGE_SCHEMA_VERSION = "docs_document_publication_lineage_v4"
LINEAGE_FILENAME = "document-publication-lineage.json"
LINEAGE_RELATIVE_PATH = Path("data") / LINEAGE_FILENAME
UTC_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


@dataclass(frozen=True, order=True)
class DocumentLineageCollection:
    stage: str
    collection: str

    def payload(self) -> dict[str, str]:
        return {"stage": self.stage, "collection": self.collection}


@dataclass(frozen=True, order=True)
class DocumentLineageWorkflow:
    contract_id: str
    working_collection: DocumentLineageCollection
    editorial_collection: DocumentLineageCollection
    path: Path


@dataclass(frozen=True, order=True)
class DocumentEditorialChild:
    doc_id: str
    created_at: str
    last_copied_at: str
    published_url: str | None

    def payload(self) -> dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "created_at": self.created_at,
            "last_copied_at": self.last_copied_at,
            "published_url": self.published_url,
        }


@dataclass(frozen=True, order=True)
class DocumentLineageRecord:
    working_doc_id: str
    editorials: tuple[DocumentEditorialChild, ...]

    def payload(self) -> dict[str, Any]:
        return {
            "working_doc_id": self.working_doc_id,
            "editorials": [editorial.payload() for editorial in self.editorials],
        }


@dataclass(frozen=True)
class DocumentLineageTable:
    working_collection: DocumentLineageCollection
    editorial_collection: DocumentLineageCollection
    records: tuple[DocumentLineageRecord, ...]

    def payload(self) -> dict[str, Any]:
        return {
            "schema_version": LINEAGE_SCHEMA_VERSION,
            "working_collection": self.working_collection.payload(),
            "editorial_collection": self.editorial_collection.payload(),
            "records": [record.payload() for record in self.records],
        }


@dataclass(frozen=True)
class DocumentLineageDeleteChange:
    contract_id: str
    table: DocumentLineageTable
    affected_working_doc_ids: tuple[str, ...]


@dataclass(frozen=True)
class DocumentLineageDeleteResult:
    role: str
    workflows: tuple[DocumentLineageDeleteChange, ...]

    @property
    def changed(self) -> bool:
        return any(change.affected_working_doc_ids for change in self.workflows)


def _strict_object(raw: Any, *, field: str, keys: set[str]) -> Mapping[str, Any]:
    if not isinstance(raw, Mapping):
        raise ValueError(f"{field} must be an object")
    unknown = sorted(set(raw) - keys)
    if unknown:
        raise ValueError(f"{field} contains unknown fields: {', '.join(unknown)}")
    missing = sorted(keys - set(raw))
    if missing:
        raise ValueError(f"{field} is missing required fields: {', '.join(missing)}")
    return raw


def _required_text(raw: Any, *, field: str) -> str:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(f"{field} is required")
    value = raw.strip()
    if value != raw:
        raise ValueError(f"{field} must be exact nonblank text")
    return value


def _doc_id(raw: Any, *, field: str) -> str:
    doc_id = _required_text(raw, field=field)
    if not source_model.is_immutable_doc_id(doc_id):
        raise ValueError(f"{field} is invalid")
    return doc_id


def _timestamp(raw: Any, *, field: str) -> str:
    timestamp = _required_text(raw, field=field)
    try:
        parsed = datetime.strptime(timestamp, UTC_TIMESTAMP_FORMAT)
    except ValueError as exc:
        raise ValueError(f"{field} is invalid") from exc
    if parsed.strftime(UTC_TIMESTAMP_FORMAT) != timestamp:
        raise ValueError(f"{field} is invalid")
    return timestamp


def _published_url(raw: Any, *, field: str) -> str | None:
    if raw is None:
        return None
    return _required_text(raw, field=field)


def _collection(raw: Any, *, field: str) -> DocumentLineageCollection:
    payload = _strict_object(raw, field=field, keys={"stage", "collection"})
    if payload["stage"] != "working":
        raise ValueError(f"{field}.stage must identify Working")
    return DocumentLineageCollection(
        stage=payload["stage"],
        collection=_required_text(
            payload["collection"],
            field=f"{field}.collection",
        ),
    )


def _editorial(raw: Any, *, field: str) -> DocumentEditorialChild:
    payload = _strict_object(
        raw,
        field=field,
        keys={"doc_id", "created_at", "last_copied_at", "published_url"},
    )
    return DocumentEditorialChild(
        doc_id=_doc_id(payload["doc_id"], field=f"{field}.doc_id"),
        created_at=_timestamp(payload["created_at"], field=f"{field}.created_at"),
        last_copied_at=_timestamp(
            payload["last_copied_at"],
            field=f"{field}.last_copied_at",
        ),
        published_url=_published_url(
            payload["published_url"],
            field=f"{field}.published_url",
        ),
    )


def _ordered_editorials(
    editorials: Iterable[DocumentEditorialChild],
    *,
    field: str,
) -> tuple[DocumentEditorialChild, ...]:
    ordered = tuple(sorted(editorials, key=lambda editorial: editorial.doc_id))
    if not ordered:
        raise ValueError(f"{field} must contain at least one Editorial child")
    seen: set[str] = set()
    for index, editorial in enumerate(ordered):
        _doc_id(editorial.doc_id, field=f"{field}[{index}].doc_id")
        _timestamp(editorial.created_at, field=f"{field}[{index}].created_at")
        _timestamp(
            editorial.last_copied_at,
            field=f"{field}[{index}].last_copied_at",
        )
        _published_url(
            editorial.published_url,
            field=f"{field}[{index}].published_url",
        )
        if editorial.doc_id in seen:
            raise ValueError("document publication lineage Editorial doc_id is duplicated")
        seen.add(editorial.doc_id)
    return ordered


def _record(raw: Any, *, index: int) -> DocumentLineageRecord:
    field = f"records[{index}]"
    payload = _strict_object(
        raw,
        field=field,
        keys={"working_doc_id", "editorials"},
    )
    raw_editorials = payload["editorials"]
    if not isinstance(raw_editorials, list):
        raise ValueError(f"{field}.editorials must be an array")
    return DocumentLineageRecord(
        working_doc_id=_doc_id(
            payload["working_doc_id"],
            field=f"{field}.working_doc_id",
        ),
        editorials=_ordered_editorials(
            (
                _editorial(raw_editorial, field=f"{field}.editorials[{child_index}]")
                for child_index, raw_editorial in enumerate(raw_editorials)
            ),
            field=f"{field}.editorials",
        ),
    )


def _ordered_records(
    records: Iterable[DocumentLineageRecord],
) -> tuple[DocumentLineageRecord, ...]:
    ordered = tuple(
        sorted(
            (
                replace(
                    record,
                    editorials=_ordered_editorials(
                        record.editorials,
                        field=f"records[{index}].editorials",
                    ),
                )
                for index, record in enumerate(records)
            ),
            key=lambda record: record.working_doc_id,
        )
    )
    working_ids: set[str] = set()
    editorial_ids: set[str] = set()
    for index, record in enumerate(ordered):
        _doc_id(record.working_doc_id, field=f"records[{index}].working_doc_id")
        if record.working_doc_id in working_ids:
            raise ValueError("document publication lineage Working doc_id is duplicated")
        working_ids.add(record.working_doc_id)
        for editorial in record.editorials:
            if editorial.doc_id in editorial_ids:
                raise ValueError(
                    "document publication lineage Editorial doc_id is duplicated"
                )
            editorial_ids.add(editorial.doc_id)
    return ordered


def _validated_table(table: DocumentLineageTable) -> DocumentLineageTable:
    working_collection = _collection(
        table.working_collection.payload(),
        field="working_collection",
    )
    editorial_collection = _collection(
        table.editorial_collection.payload(),
        field="editorial_collection",
    )
    if working_collection == editorial_collection:
        raise ValueError("document publication lineage collections must be distinct")
    return replace(
        table,
        working_collection=working_collection,
        editorial_collection=editorial_collection,
        records=_ordered_records(table.records),
    )


def empty_table(
    *,
    working_stage: str,
    working_collection: str,
    editorial_stage: str,
    editorial_collection: str,
) -> DocumentLineageTable:
    return _validated_table(
        DocumentLineageTable(
            working_collection=DocumentLineageCollection(
                stage=working_stage,
                collection=working_collection,
            ),
            editorial_collection=DocumentLineageCollection(
                stage=editorial_stage,
                collection=editorial_collection,
            ),
            records=(),
        )
    )


def render_table(table: DocumentLineageTable) -> bytes:
    validated = _validated_table(table)
    return (
        json.dumps(validated.payload(), ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")


def configured_workflows(repo_root: Path) -> tuple[DocumentLineageWorkflow, ...]:
    """Discover every complete exact source-to-Editorial lineage contract."""

    roles_by_contract: dict[
        str,
        dict[str, list[tuple[DocumentLineageCollection, Path]]],
    ] = {}
    config = load_docs_stage(repo_root, "working")
    for collection in config.collections:
        resolved_collection = DocumentLineageCollection(
            stage=config.stage,
            collection=collection.collection,
        )
        documents_root = resolve_workspace_path(
            repo_root,
            document_source_path(collection),
        )
        for aspect in collection_customisation_document_lineage_contracts(
            collection.collection_customisation
        ):
            roles = roles_by_contract.setdefault(
                aspect.contract_id,
                {LINEAGE_SOURCE_ROLE: [], LINEAGE_EDITORIAL_ROLE: []},
            )
            roles[aspect.role].append(
                (resolved_collection, documents_root.parent / LINEAGE_RELATIVE_PATH)
            )

    workflows: list[DocumentLineageWorkflow] = []
    for contract_id, roles in sorted(roles_by_contract.items()):
        sources = roles[LINEAGE_SOURCE_ROLE]
        editorials = roles[LINEAGE_EDITORIAL_ROLE]
        if len(sources) != 1 or len(editorials) != 1:
            raise ValueError(
                "document publication lineage contract must configure exactly one "
                f"Working source and one Editorial target: {contract_id}"
            )
        working_collection, path = sources[0]
        editorial_collection, _editorial_path = editorials[0]
        if working_collection == editorial_collection:
            raise ValueError(
                "document publication lineage collections must be distinct"
            )
        workflows.append(
            DocumentLineageWorkflow(
                contract_id=contract_id,
                working_collection=working_collection,
                editorial_collection=editorial_collection,
                path=path,
            )
        )
    working_collections = [workflow.working_collection for workflow in workflows]
    table_paths = [workflow.path for workflow in workflows]
    if len(set(working_collections)) != len(working_collections):
        raise ValueError(
            "document publication lineage Working collection is configured for "
            "multiple workflows"
        )
    if len(set(table_paths)) != len(table_paths):
        raise ValueError(
            "document publication lineage table path is configured for multiple workflows"
        )
    return tuple(workflows)


def workflow_for_contract(repo_root: Path, contract_id: str) -> DocumentLineageWorkflow:
    exact_contract_id = _required_text(contract_id, field="lineage contract_id")
    matching = [
        workflow
        for workflow in configured_workflows(repo_root)
        if workflow.contract_id == exact_contract_id
    ]
    if len(matching) != 1:
        raise ValueError(
            f"document publication lineage contract is not configured exactly once: "
            f"{exact_contract_id}"
        )
    return matching[0]


def workflows_for_collection(
    repo_root: Path,
    collection: DocumentLineageCollection,
) -> tuple[DocumentLineageWorkflow, ...]:
    return tuple(
        workflow
        for workflow in configured_workflows(repo_root)
        if collection in {
            workflow.working_collection,
            workflow.editorial_collection,
        }
    )


def table_path(repo_root: Path, *, contract_id: str) -> Path:
    return workflow_for_contract(repo_root, contract_id).path


def _load_table_path(
    path: Path,
    workflow: DocumentLineageWorkflow,
) -> DocumentLineageTable | None:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("document publication lineage table is invalid JSON") from exc
    payload = _strict_object(
        payload,
        field="document publication lineage table",
        keys={
            "schema_version",
            "working_collection",
            "editorial_collection",
            "records",
        },
    )
    if payload["schema_version"] != LINEAGE_SCHEMA_VERSION:
        raise ValueError("document publication lineage schema_version is invalid")
    raw_records = payload["records"]
    if not isinstance(raw_records, list):
        raise ValueError("document publication lineage records must be an array")
    table = _validated_table(
        DocumentLineageTable(
            working_collection=_collection(
                payload["working_collection"],
                field="working_collection",
            ),
            editorial_collection=_collection(
                payload["editorial_collection"],
                field="editorial_collection",
            ),
            records=_ordered_records(
                _record(raw_record, index=index)
                for index, raw_record in enumerate(raw_records)
            ),
        )
    )
    if (
        table.working_collection != workflow.working_collection
        or table.editorial_collection != workflow.editorial_collection
    ):
        raise ValueError(
            "document publication lineage collections do not match configured workflow"
        )
    return table


def load_tables(
    repo_root: Path,
) -> dict[str, DocumentLineageTable | None]:
    workflows = configured_workflows(repo_root)
    tables = {
        workflow.contract_id: _load_table_path(workflow.path, workflow)
        for workflow in workflows
    }
    editorial_owners: dict[tuple[DocumentLineageCollection, str], str] = {}
    for workflow in workflows:
        table = tables[workflow.contract_id]
        if table is None:
            continue
        for record in table.records:
            for editorial in record.editorials:
                key = (workflow.editorial_collection, editorial.doc_id)
                owner = editorial_owners.get(key)
                if owner is not None and owner != workflow.contract_id:
                    raise ValueError(
                        "document publication lineage Editorial doc_id has "
                        "cross-table ownership"
                    )
                editorial_owners[key] = workflow.contract_id
    return tables


def load_table(
    repo_root: Path,
    *,
    contract_id: str,
) -> DocumentLineageTable | None:
    workflow = workflow_for_contract(repo_root, contract_id)
    return load_tables(repo_root)[workflow.contract_id]


def write_table_atomic(
    repo_root: Path,
    table: DocumentLineageTable,
    *,
    contract_id: str,
) -> DocumentLineageTable:
    workflow = workflow_for_contract(repo_root, contract_id)
    validated = _validated_table(table)
    if (
        validated.working_collection != workflow.working_collection
        or validated.editorial_collection != workflow.editorial_collection
    ):
        raise ValueError(
            "document publication lineage collections do not match configured workflow"
        )
    workflows = configured_workflows(repo_root)
    existing = {
        configured.contract_id: _load_table_path(configured.path, configured)
        for configured in workflows
    }
    existing[workflow.contract_id] = validated
    editorial_owners: dict[tuple[DocumentLineageCollection, str], str] = {}
    for configured in workflows:
        candidate = existing[configured.contract_id]
        if candidate is None:
            continue
        for record in candidate.records:
            for editorial in record.editorials:
                key = (configured.editorial_collection, editorial.doc_id)
                owner = editorial_owners.get(key)
                if owner is not None and owner != configured.contract_id:
                    raise ValueError(
                        "document publication lineage Editorial doc_id has "
                        "cross-table ownership"
                    )
                editorial_owners[key] = configured.contract_id
    source_model.write_bytes_atomic(workflow.path, render_table(validated))
    return validated


def apply_document_deletes(
    repo_root: Path,
    *,
    stage: str,
    collection: str,
    doc_ids: Iterable[str],
) -> DocumentLineageDeleteResult:
    """Remove exact Working records or Editorial children after confirmed Delete."""

    target_collection = DocumentLineageCollection(
        stage=_required_text(stage, field="delete collection.stage"),
        collection=_required_text(
            collection,
            field="delete collection.collection",
        ),
    )
    deleted_doc_ids = {
        _doc_id(doc_id, field=f"deleted doc_ids[{index}]")
        for index, doc_id in enumerate(doc_ids)
    }
    workflows = workflows_for_collection(repo_root, target_collection)
    if not workflows:
        return DocumentLineageDeleteResult(role="", workflows=())
    tables = load_tables(repo_root)
    roles = {
        "working"
        if workflow.working_collection == target_collection
        else "editorial"
        for workflow in workflows
    }
    if len(roles) != 1:
        raise ValueError(
            "document publication lineage collection has ambiguous source/Editorial roles"
        )
    role = next(iter(roles))
    changes: list[DocumentLineageDeleteChange] = []
    for workflow in workflows:
        table = tables[workflow.contract_id]
        if table is None:
            continue
        if role == "working":
            affected = tuple(
                record.working_doc_id
                for record in table.records
                if record.working_doc_id in deleted_doc_ids
            )
            records = tuple(
                record
                for record in table.records
                if record.working_doc_id not in deleted_doc_ids
            )
        else:
            affected_working_ids: list[str] = []
            retained_records: list[DocumentLineageRecord] = []
            for record in table.records:
                editorials = tuple(
                    editorial
                    for editorial in record.editorials
                    if editorial.doc_id not in deleted_doc_ids
                )
                if editorials != record.editorials:
                    affected_working_ids.append(record.working_doc_id)
                if editorials:
                    retained_records.append(replace(record, editorials=editorials))
            affected = tuple(affected_working_ids)
            records = tuple(retained_records)
        updated = (
            write_table_atomic(
                repo_root,
                replace(table, records=records),
                contract_id=workflow.contract_id,
            )
            if affected
            else table
        )
        changes.append(
            DocumentLineageDeleteChange(
                contract_id=workflow.contract_id,
                table=updated,
                affected_working_doc_ids=affected,
            )
        )
    return DocumentLineageDeleteResult(role=role, workflows=tuple(changes))


def project_publications(
    table: DocumentLineageTable | None,
    *,
    editorial_stage: str,
    editorial_collection: str,
    publication_urls: Mapping[str, str],
) -> DocumentLineageTable | None:
    if table is None or table.editorial_collection != DocumentLineageCollection(
        editorial_stage,
        editorial_collection,
    ):
        return table
    records: list[DocumentLineageRecord] = []
    changed = False
    for record in table.records:
        editorials = tuple(
            replace(
                editorial,
                published_url=publication_urls.get(editorial.doc_id),
            )
            for editorial in record.editorials
        )
        changed = changed or editorials != record.editorials
        records.append(replace(record, editorials=editorials))
    return replace(table, records=tuple(records)) if changed else table


__all__ = [
    "DocumentEditorialChild",
    "DocumentLineageCollection",
    "DocumentLineageDeleteChange",
    "DocumentLineageDeleteResult",
    "DocumentLineageRecord",
    "DocumentLineageTable",
    "DocumentLineageWorkflow",
    "LINEAGE_FILENAME",
    "LINEAGE_RELATIVE_PATH",
    "LINEAGE_SCHEMA_VERSION",
    "apply_document_deletes",
    "configured_workflows",
    "empty_table",
    "load_table",
    "load_tables",
    "project_publications",
    "render_table",
    "table_path",
    "workflow_for_contract",
    "workflows_for_collection",
    "write_table_atomic",
]
