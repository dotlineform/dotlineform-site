"""Preview and apply Catalogue Work documents through one awaited batch build."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

from docs_catalogue_media import read_catalogue_work, read_catalogue_work_index
from docs_catalogue_work_record import CatalogueWorkRecord, catalogue_work_record
from docs_management_context import log_event
from docs_management_document_target import confined_source_path, resolve_managed_document_collection, source_doc_from_path
from docs_management_mutations import SourceWrite, plan_create
import docs_source_model as source_model
from docs_workspace_config import require_document_authoring
from docs_write_rebuild import perform_collection_source_write_and_rebuild


TARGET = {"stage": "working", "collection": "catalogue"}
PREVIEW_KEYS = frozenset({"stage", "collection", "only_create_new"})
APPLY_KEYS = PREVIEW_KEYS | {"work_ids", "preview_revision", "confirm"}


class CatalogueRegenerationConflict(ValueError):
    """The preview no longer describes the selected Work data and sources."""


class CatalogueRegenerationApplyError(RuntimeError):
    """Carry exact committed sources and an incomplete write/build outcome."""

    def __init__(self, payload: dict[str, Any]) -> None:
        super().__init__(payload["error"])
        self.payload = payload


@dataclass(frozen=True)
class RegenerationEntry:
    record: CatalogueWorkRecord
    document: source_model.SourceDoc | None

    def preview(self) -> dict[str, str]:
        return {
            "work_id": self.record.work_id,
            "doc_id": self.document.doc_id if self.document else "",
            "title": self.record.title,
            "operation": "regenerate" if self.document else "create",
        }


def _request(body: dict[str, Any], *, apply: bool = False) -> bool:
    if set(body) != (APPLY_KEYS if apply else PREVIEW_KEYS):
        raise ValueError("Catalogue Regenerate request fields are invalid")
    if any(body.get(key) != value for key, value in TARGET.items()):
        raise ValueError("Regenerate requires the Working Catalogue collection")
    if type(body.get("only_create_new")) is not bool:
        raise ValueError("only_create_new must be a boolean")
    if apply and body.get("confirm") is not True:
        raise ValueError("Confirm the Regenerate preview before applying")
    return body["only_create_new"]


def _plan(repo_root: Path, only_create_new: bool) -> tuple[list[RegenerationEntry], dict[str, Any]]:
    collection = resolve_managed_document_collection(repo_root, **TARGET)
    require_document_authoring(collection.parent_config)
    documents: dict[str, source_model.SourceDoc] = {}
    for path in source_model.document_markdown_paths(collection.source_root):
        document = source_doc_from_path(
            path=confined_source_path(collection.source_root, path),
            requested_doc_id=path.stem,
        )
        work_id = document.front_matter.get("work_id")
        if work_id is None:
            continue
        if not isinstance(work_id, str):
            raise ValueError(f"Catalogue document {document.doc_id} requires a string work_id")
        if work_id in documents:
            raise ValueError(f"Work {work_id} has multiple Catalogue documents")
        documents[work_id] = document
    works = read_catalogue_work_index(repo_root)
    candidates = [work_id for work_id in sorted(works) if not only_create_new or work_id not in documents]
    entries = []
    revision_records = []
    for work_id in candidates:
        try:
            record = catalogue_work_record(read_catalogue_work(repo_root, work_id)["work"])
        except (OSError, ValueError) as error:
            raise ValueError(f"Work {work_id}: {error}") from error
        document = documents.get(work_id)
        entry = RegenerationEntry(record, document)
        entries.append(entry)
        revision_records.append({
            **entry.preview(), "body": record.body,
            "source_name": document.path.name if document else "",
            "source_revision": source_model.source_revision(document.source_text.encode("utf-8")) if document else "",
        })
    revision = hashlib.sha256(json.dumps(
        {"only_create_new": only_create_new, "records": revision_records},
        sort_keys=True, ensure_ascii=False,
    ).encode("utf-8")).hexdigest()
    created = sum(entry.document is None for entry in entries)
    return entries, {
        "ok": True, **TARGET, "only_create_new": only_create_new,
        "preview_revision": revision,
        "work_ids": [entry.record.work_id for entry in entries],
        "records": [entry.preview() for entry in entries],
        "counts": {
            "selected": len(entries), "create": created,
            "regenerate": len(entries) - created,
            "skip": len(works) - len(candidates),
        },
    }


def preview_catalogue_regeneration(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    """Read the inventory once and preview only the selected Work records; write nothing."""
    return _plan(repo_root, _request(body))[1]


def apply_catalogue_regeneration(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    """Apply the exact preview; preserve existing Links and report partial commits.

    Recompute the plan once to reject changed selection or inputs. New identities
    are allocated only here. All source writes and the selected build complete
    before success; failures neither retry creation nor roll sources back.
    """
    entries, preview = _plan(repo_root, _request(body, apply=True))
    if body.get("work_ids") != preview["work_ids"] or body.get("preview_revision") != preview["preview_revision"]:
        raise CatalogueRegenerationConflict("Catalogue inputs changed. Preview Regenerate again.")
    if not entries:
        return {**preview, "committed": False, "completed_records": [], "rebuild": None, "summary_text": "No documents to create."}

    writes: list[tuple[RegenerationEntry, str, SourceWrite]] = []
    timestamp = source_model.current_doc_timestamp()
    for entry in entries:
        record, document = entry.record, entry.document
        if document is None:
            create = plan_create(repo_root, {
                **TARGET, "work_id": record.work_id, "title": record.title,
            }, body_markdown=record.body)
            writes.append((entry, create.response["doc_id"], create.source_writes[0]))
        else:
            metadata = {**document.front_matter, "title": record.title}
            content = source_model.format_source(metadata, record.body, collection="catalogue")
            if content != document.source_text:
                content = source_model.format_source(
                    source_model.advance_doc_front_matter(metadata, timestamp=timestamp),
                    record.body, collection="catalogue",
                )
            writes.append((entry, document.doc_id, SourceWrite(
                document.path, content, original_bytes=document.source_text.encode("utf-8"),
            )))

    committed: list[dict[str, str]] = []
    failed_work_id = ""
    phase = "write"

    def write_operation() -> None:
        nonlocal failed_work_id, phase
        for entry, _doc_id, write in writes:
            failed_work_id = entry.record.work_id
            if write.original_bytes is not None and write.path.read_bytes() != write.original_bytes:
                raise CatalogueRegenerationConflict(f"Work {failed_work_id} source changed. Preview Regenerate again.")
        for entry, doc_id, write in writes:
            failed_work_id = entry.record.work_id
            if write.create_only:
                source_model.write_text_atomic_new(write.path, write.text)
            elif write.text.encode("utf-8") != write.original_bytes:
                source_model.write_text_atomic(write.path, write.text)
            else:
                continue
            committed.append({**entry.preview(), "doc_id": doc_id})
        failed_work_id = ""
        phase = "build"

    created_ids = [doc_id for _entry, doc_id, write in writes if write.create_only]
    try:
        rebuild = perform_collection_source_write_and_rebuild(
            repo_root, "catalogue", [write.path for _entry, _doc_id, write in writes],
            write_operation, stage="working", suppression_reason="docs-catalogue-regenerate",
            links_doc_ids=created_ids, links_created_doc_ids=created_ids,
            source_writes_committed=lambda: bool(committed),
        )
    except CatalogueRegenerationConflict:
        raise
    except Exception as error:
        payload = {
            "ok": False, **TARGET, "committed": bool(committed),
            "retry_create": False, "completed_records": committed,
            "failed_work_id": failed_work_id, "failed_phase": phase,
            "rebuild": {"ok": False, "completed": False},
            "error": f"{f'Work {failed_work_id}: ' if failed_work_id else ''}{error}",
        }
        log_event(repo_root, "docs-catalogue-regenerate-failed", {
            "failed_work_id": failed_work_id, "phase": phase, "committed_count": len(committed),
        })
        raise CatalogueRegenerationApplyError(payload) from error
    result = {
        **preview, "committed": bool(committed), "completed_records": committed,
        "records": [{**entry.preview(), "doc_id": doc_id} for entry, doc_id, _write in writes],
        "rebuild": rebuild,
        "summary_text": f"Created {len(created_ids)} and regenerated {len(entries) - len(created_ids)} documents.",
    }
    log_event(repo_root, "docs-catalogue-regenerate", {**TARGET, "counts": preview["counts"]})
    return result
