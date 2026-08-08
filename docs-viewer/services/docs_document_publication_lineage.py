#!/usr/bin/env python3
"""Private working-to-editorial Docs document lineage."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

import docs_source_model as source_model


LINEAGE_SCHEMA_VERSION = "docs_document_publication_lineage_v1"
LINEAGE_PATH = Path("docs-viewer/data/canonical/document-publication-lineage.json")
UTC_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


@dataclass(frozen=True, order=True)
class DocumentLineageIdentity:
    scope: str
    sub_scope: str
    doc_id: str

    def payload(self) -> dict[str, str]:
        return {
            "scope": self.scope,
            "sub_scope": self.sub_scope,
            "doc_id": self.doc_id,
        }


@dataclass(frozen=True)
class DocumentPublicationEvidence:
    public_url: str
    published_at: str
    generation: str

    def payload(self) -> dict[str, str]:
        return {
            "public_url": self.public_url,
            "published_at": self.published_at,
            "generation": self.generation,
        }


@dataclass(frozen=True)
class DocumentPublicationLineageRow:
    source: DocumentLineageIdentity
    editorial: DocumentLineageIdentity
    created_at: str
    last_copied_at: str
    publication: DocumentPublicationEvidence | None

    def payload(self) -> dict[str, Any]:
        return {
            "source": self.source.payload(),
            "editorial": self.editorial.payload(),
            "created_at": self.created_at,
            "last_copied_at": self.last_copied_at,
            "publication": (
                self.publication.payload() if self.publication is not None else None
            ),
        }


def current_timestamp() -> str:
    return datetime.now(timezone.utc).strftime(UTC_TIMESTAMP_FORMAT)


def _required_text(raw: Any, *, field: str) -> str:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(f"{field} is required")
    return raw.strip()


def _identity(raw: Any, *, field: str) -> DocumentLineageIdentity:
    if not isinstance(raw, Mapping):
        raise ValueError(f"{field} must be an object")
    identity = DocumentLineageIdentity(
        scope=_required_text(raw.get("scope"), field=f"{field}.scope"),
        sub_scope=_required_text(raw.get("sub_scope"), field=f"{field}.sub_scope"),
        doc_id=_required_text(raw.get("doc_id"), field=f"{field}.doc_id"),
    )
    if not source_model.is_immutable_doc_id(identity.doc_id):
        raise ValueError(f"{field}.doc_id is invalid")
    return identity


def _publication(raw: Any, *, field: str) -> DocumentPublicationEvidence | None:
    if raw is None:
        return None
    if not isinstance(raw, Mapping):
        raise ValueError(f"{field} must be an object or null")
    return DocumentPublicationEvidence(
        public_url=_required_text(raw.get("public_url"), field=f"{field}.public_url"),
        published_at=_required_text(
            raw.get("published_at"),
            field=f"{field}.published_at",
        ),
        generation=_required_text(raw.get("generation"), field=f"{field}.generation"),
    )


def _row(raw: Any, *, index: int) -> DocumentPublicationLineageRow:
    if not isinstance(raw, Mapping):
        raise ValueError(f"document publication lineage rows[{index}] must be an object")
    return DocumentPublicationLineageRow(
        source=_identity(raw.get("source"), field=f"rows[{index}].source"),
        editorial=_identity(raw.get("editorial"), field=f"rows[{index}].editorial"),
        created_at=_required_text(raw.get("created_at"), field=f"rows[{index}].created_at"),
        last_copied_at=_required_text(
            raw.get("last_copied_at"),
            field=f"rows[{index}].last_copied_at",
        ),
        publication=_publication(raw.get("publication"), field=f"rows[{index}].publication"),
    )


def render_table(rows: Iterable[DocumentPublicationLineageRow]) -> bytes:
    ordered = sorted(rows, key=lambda row: (row.source, row.editorial))
    payload = {
        "schema_version": LINEAGE_SCHEMA_VERSION,
        "rows": [row.payload() for row in ordered],
    }
    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def table_path(repo_root: Path) -> Path:
    return repo_root / LINEAGE_PATH


def load_rows(repo_root: Path) -> tuple[DocumentPublicationLineageRow, ...]:
    path = table_path(repo_root)
    if not path.is_file():
        return ()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("document publication lineage table is invalid JSON") from exc
    if not isinstance(payload, Mapping):
        raise ValueError("document publication lineage table must be an object")
    if payload.get("schema_version") != LINEAGE_SCHEMA_VERSION:
        raise ValueError("document publication lineage schema_version is invalid")
    raw_rows = payload.get("rows")
    if not isinstance(raw_rows, list):
        raise ValueError("document publication lineage rows must be an array")
    return tuple(_row(raw, index=index) for index, raw in enumerate(raw_rows))


def write_rows_atomic(
    repo_root: Path,
    rows: Iterable[DocumentPublicationLineageRow],
) -> tuple[DocumentPublicationLineageRow, ...]:
    ordered = tuple(sorted(rows, key=lambda row: (row.source, row.editorial)))
    source_model.write_bytes_atomic(table_path(repo_root), render_table(ordered))
    return ordered


def rows_for_source(
    rows: Iterable[DocumentPublicationLineageRow],
    source: DocumentLineageIdentity,
    *,
    editorial_scope: str,
    editorial_sub_scope: str,
) -> tuple[DocumentPublicationLineageRow, ...]:
    return tuple(
        row
        for row in rows
        if row.source == source
        and row.editorial.scope == editorial_scope
        and row.editorial.sub_scope == editorial_sub_scope
    )


def apply_copy_results(
    repo_root: Path,
    *,
    source_scope: str,
    source_sub_scope: str,
    editorial_scope: str,
    editorial_sub_scope: str,
    results: Iterable[Mapping[str, str]],
) -> tuple[DocumentPublicationLineageRow, ...]:
    rows_by_pair = {
        (row.source, row.editorial): row
        for row in load_rows(repo_root)
    }
    copied_at = current_timestamp()
    for index, result in enumerate(results):
        source = _identity(
            {
                "scope": source_scope,
                "sub_scope": source_sub_scope,
                "doc_id": result.get("source_doc_id"),
            },
            field=f"copy results[{index}].source",
        )
        editorial = _identity(
            {
                "scope": editorial_scope,
                "sub_scope": editorial_sub_scope,
                "doc_id": result.get("target_doc_id"),
            },
            field=f"copy results[{index}].editorial",
        )
        pair = (source, editorial)
        existing = rows_by_pair.get(pair)
        action = str(result.get("action") or "").strip().lower()
        if action == "new":
            if existing is not None:
                raise ValueError("New copy would duplicate an exact lineage relationship")
            rows_by_pair[pair] = DocumentPublicationLineageRow(
                source=source,
                editorial=editorial,
                created_at=copied_at,
                last_copied_at=copied_at,
                publication=None,
            )
        elif action == "replace":
            if existing is None:
                raise ValueError("Replace target is not an exact current lineage row")
            rows_by_pair[pair] = replace(existing, last_copied_at=copied_at)
        else:
            raise ValueError(f"copy results[{index}].action is invalid")
    return write_rows_atomic(repo_root, rows_by_pair.values())


__all__ = [
    "DocumentLineageIdentity",
    "DocumentPublicationEvidence",
    "DocumentPublicationLineageRow",
    "LINEAGE_PATH",
    "LINEAGE_SCHEMA_VERSION",
    "apply_copy_results",
    "current_timestamp",
    "load_rows",
    "render_table",
    "rows_for_source",
    "table_path",
    "write_rows_atomic",
]
