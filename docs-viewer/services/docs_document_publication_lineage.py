#!/usr/bin/env python3
"""Private Working-owned Editorial document lineage."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

import docs_source_model as source_model


LINEAGE_SCHEMA_VERSION = "docs_document_publication_lineage_v3"
LINEAGE_PATH = Path("docs-viewer/data/canonical/document-publication-lineage.json")
UTC_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


@dataclass(frozen=True, order=True)
class DocumentLineageCollection:
    scope: str
    sub_scope: str

    def payload(self) -> dict[str, str]:
        return {"scope": self.scope, "sub_scope": self.sub_scope}


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


def current_timestamp() -> str:
    return datetime.now(timezone.utc).strftime(UTC_TIMESTAMP_FORMAT)


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
    payload = _strict_object(raw, field=field, keys={"scope", "sub_scope"})
    return DocumentLineageCollection(
        scope=_required_text(payload["scope"], field=f"{field}.scope"),
        sub_scope=_required_text(
            payload["sub_scope"],
            field=f"{field}.sub_scope",
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
    working_scope: str,
    working_sub_scope: str,
    editorial_scope: str,
    editorial_sub_scope: str,
) -> DocumentLineageTable:
    return _validated_table(
        DocumentLineageTable(
            working_collection=DocumentLineageCollection(
                scope=working_scope,
                sub_scope=working_sub_scope,
            ),
            editorial_collection=DocumentLineageCollection(
                scope=editorial_scope,
                sub_scope=editorial_sub_scope,
            ),
            records=(),
        )
    )


def render_table(table: DocumentLineageTable) -> bytes:
    validated = _validated_table(table)
    return (
        json.dumps(validated.payload(), ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")


def table_path(repo_root: Path) -> Path:
    return repo_root / LINEAGE_PATH


def load_table(repo_root: Path) -> DocumentLineageTable | None:
    path = table_path(repo_root)
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
    return _validated_table(
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


def write_table_atomic(
    repo_root: Path,
    table: DocumentLineageTable,
) -> DocumentLineageTable:
    validated = _validated_table(table)
    source_model.write_bytes_atomic(table_path(repo_root), render_table(validated))
    return validated


def editorials_for_working(
    table: DocumentLineageTable | None,
    *,
    working_scope: str,
    working_sub_scope: str,
    editorial_scope: str,
    editorial_sub_scope: str,
    working_doc_id: str,
) -> tuple[DocumentEditorialChild, ...]:
    if table is None:
        return ()
    expected_working = DocumentLineageCollection(working_scope, working_sub_scope)
    expected_editorial = DocumentLineageCollection(editorial_scope, editorial_sub_scope)
    if (
        table.working_collection != expected_working
        or table.editorial_collection != expected_editorial
    ):
        raise ValueError("document publication lineage collections do not match Copy")
    for record in table.records:
        if record.working_doc_id == working_doc_id:
            return record.editorials
    return ()


def apply_copy_results(
    repo_root: Path,
    *,
    source_scope: str,
    source_sub_scope: str,
    editorial_scope: str,
    editorial_sub_scope: str,
    results: Iterable[Mapping[str, str]],
) -> DocumentLineageTable:
    table = load_table(repo_root) or empty_table(
        working_scope=source_scope,
        working_sub_scope=source_sub_scope,
        editorial_scope=editorial_scope,
        editorial_sub_scope=editorial_sub_scope,
    )
    expected_working = DocumentLineageCollection(source_scope, source_sub_scope)
    expected_editorial = DocumentLineageCollection(editorial_scope, editorial_sub_scope)
    if (
        table.working_collection != expected_working
        or table.editorial_collection != expected_editorial
    ):
        raise ValueError("document publication lineage collections do not match Copy")

    copied_at = current_timestamp()
    records = {record.working_doc_id: record for record in table.records}
    editorial_owners = {
        editorial.doc_id: record.working_doc_id
        for record in table.records
        for editorial in record.editorials
    }
    for index, result in enumerate(results):
        working_doc_id = _doc_id(
            result.get("source_doc_id"),
            field=f"copy results[{index}].source_doc_id",
        )
        editorial_doc_id = _doc_id(
            result.get("target_doc_id"),
            field=f"copy results[{index}].target_doc_id",
        )
        record = records.get(working_doc_id)
        editorials = list(record.editorials if record is not None else ())
        existing_index = next(
            (
                child_index
                for child_index, editorial in enumerate(editorials)
                if editorial.doc_id == editorial_doc_id
            ),
            None,
        )
        action = str(result.get("action") or "").strip().lower()
        if action == "new":
            if editorial_doc_id in editorial_owners:
                raise ValueError("New copy would duplicate an exact Editorial child")
            editorials.append(
                DocumentEditorialChild(
                    doc_id=editorial_doc_id,
                    created_at=copied_at,
                    last_copied_at=copied_at,
                    published_url=None,
                )
            )
            editorial_owners[editorial_doc_id] = working_doc_id
        elif action == "replace":
            if existing_index is None:
                raise ValueError("Replace target is not an exact current Editorial child")
            editorials[existing_index] = replace(
                editorials[existing_index],
                last_copied_at=copied_at,
            )
        else:
            raise ValueError(f"copy results[{index}].action is invalid")
        records[working_doc_id] = DocumentLineageRecord(
            working_doc_id=working_doc_id,
            editorials=tuple(editorials),
        )

    return write_table_atomic(repo_root, replace(table, records=tuple(records.values())))


def reconcile_publications(
    repo_root: Path,
    *,
    editorial_scope: str,
    editorial_sub_scope: str,
    publication_urls: Mapping[str, str],
) -> DocumentLineageTable | None:
    table = load_table(repo_root)
    if table is None or table.editorial_collection != DocumentLineageCollection(
        editorial_scope,
        editorial_sub_scope,
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
    return (
        write_table_atomic(repo_root, replace(table, records=tuple(records)))
        if changed
        else table
    )


__all__ = [
    "DocumentEditorialChild",
    "DocumentLineageCollection",
    "DocumentLineageRecord",
    "DocumentLineageTable",
    "LINEAGE_PATH",
    "LINEAGE_SCHEMA_VERSION",
    "apply_copy_results",
    "current_timestamp",
    "editorials_for_working",
    "empty_table",
    "load_table",
    "reconcile_publications",
    "render_table",
    "table_path",
    "write_table_atomic",
]
