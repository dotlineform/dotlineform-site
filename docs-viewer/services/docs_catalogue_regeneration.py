"""Reconcile exact Catalogue Work documents in one awaited operation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from docs_catalogue_media import read_catalogue_work, read_catalogue_work_index
from docs_catalogue_source_inventory import catalogue_source_documents
from docs_catalogue_work_record import catalogue_work_record
from docs_management_context import log_event
from docs_management_document_target import resolve_managed_document_collection
from docs_management_mutations import SourceWrite, plan_create
from docs_selected_documents import selected_path, selected_text, validate_selected_payload
import docs_source_model as source_model
from docs_workspace_config import require_document_authoring
from docs_write_rebuild import perform_collection_source_write_and_rebuild
from studio.services.catalogue.catalogue_pending_updates import clear_pending_updates, read_pending_updates


TARGET = {"collection": "catalogue"}
MODES = frozenset({"pending", "full"})


class CatalogueRegenerationError(RuntimeError):
    """Report an incomplete write, Build or pending-list update without rollback."""

    def __init__(self, payload: dict[str, Any]) -> None:
        super().__init__(payload["error"])
        self.payload = payload


def _request_mode(body: dict[str, Any]) -> str:
    if (not isinstance(body, dict) or set(body) != {"collection", "mode"}
            or body.get("collection") != "catalogue"
            or not isinstance(body.get("mode"), str) or body["mode"] not in MODES):
        raise ValueError("Regenerate requires the Working Catalogue collection and pending or full mode")
    return body["mode"]


def _selection_write(config: Any, *, removed_doc_ids: set[str], full_keep_ids: set[str] | None) -> SourceWrite | None:
    path = selected_path(config)
    original = path.read_bytes()
    payload = json.loads(original)
    validate_selected_payload(payload)
    rows = [
        row for row in payload["docs"]
        if row.get("collection") != "catalogue"
        or (row["doc_id"] not in removed_doc_ids
            and (full_keep_ids is None or row["doc_id"] in full_keep_ids))
    ]
    if rows == payload["docs"]:
        return None
    return SourceWrite(path, selected_text({**payload, "docs": rows}), original_bytes=original)


def regenerate_catalogue(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    """Reconcile one requested mode and clear pending IDs only after its Build succeeds."""
    mode = _request_mode(body)
    pending = read_pending_updates(repo_root)
    collection = resolve_managed_document_collection(repo_root, **TARGET)
    require_document_authoring(collection.parent_config)
    if mode == "pending" and not pending["current_work_ids"] and not pending["deleted_work_ids"]:
        counts = {"create": 0, "retitle": 0, "regenerate_body": 0, "build_only": 0, "delete": 0, "built": 0, "updated": 0}
        return {"ok": True, **TARGET, "mode": mode, "counts": counts,
                "pending_updates": {"current": 0, "deleted": 0}, "summary_text": "No pending Catalogue updates."}
    documents = catalogue_source_documents(repo_root)
    works = read_catalogue_work_index(repo_root)
    current_ids = sorted(works if mode == "full" else pending["current_work_ids"])
    deleted_ids = sorted(
        set(documents) - set(works) if mode == "full" else pending["deleted_work_ids"]
    )
    for work_id in current_ids:
        if work_id not in works:
            raise ValueError(f"Pending Work {work_id} is absent from the generated index; run Refresh Catalogue")
    for work_id in deleted_ids:
        if work_id in works:
            raise ValueError(f"Deleted Work {work_id} remains in the generated index; run Refresh Catalogue")

    timestamp = source_model.current_doc_timestamp()
    writes: list[tuple[str, str, SourceWrite]] = []
    deletes: list[tuple[str, str, Path]] = []
    build_doc_ids: set[str] = set()
    current_doc_ids: set[str] = set()
    deleted_doc_ids: set[str] = set()
    link_doc_ids: set[str] = set()
    counts = {"create": 0, "retitle": 0, "regenerate_body": 0, "build_only": 0, "delete": 0}

    for work_id in current_ids:
        try:
            record = catalogue_work_record(read_catalogue_work(repo_root, work_id)["work"])
        except (OSError, ValueError) as error:
            raise ValueError(f"Work {work_id}: {error}") from error
        document = documents.get(work_id)
        if document is None:
            create = plan_create(repo_root, {**TARGET, "work_id": work_id, "title": record.title},
                                 body_markdown=record.body)
            doc_id = create.response["doc_id"]
            writes.append((work_id, doc_id, create.source_writes[0]))
            link_doc_ids.add(doc_id)
            counts["create"] += 1
        else:
            doc_id = document.doc_id
            title_changed = document.front_matter["title"] != record.title
            if mode == "full" or title_changed:
                metadata = {**document.front_matter, "title": record.title}
                content = source_model.format_source(metadata, record.body, collection="catalogue")
                if content != document.source_text:
                    content = source_model.format_source(
                        source_model.advance_doc_front_matter(
                            metadata,
                            timestamp=source_model.strictly_later_doc_timestamp(
                                document.front_matter["last_updated"], timestamp,
                            ),
                        ),
                        record.body, collection="catalogue",
                    )
                    writes.append((work_id, doc_id, SourceWrite(document.path, content)))
                    link_doc_ids.add(doc_id)
                    counts["retitle" if title_changed else "regenerate_body"] += 1
                else:
                    counts["build_only"] += 1
            else:
                counts["build_only"] += 1
        build_doc_ids.add(doc_id)
        current_doc_ids.add(doc_id)

    for work_id in deleted_ids:
        document = documents.get(work_id)
        doc_id = work_id
        deleted_doc_ids.add(doc_id)
        if document is not None:
            deletes.append((work_id, doc_id, document.path))
        build_doc_ids.add(doc_id)
        link_doc_ids.add(doc_id)
        counts["delete"] += 1

    full_keep_ids = current_doc_ids if mode == "full" else None
    selection_write = _selection_write(collection.parent_config, removed_doc_ids=deleted_doc_ids,
                                       full_keep_ids=full_keep_ids)

    if mode == "pending" and not build_doc_ids:
        remaining = clear_pending_updates(repo_root, pending, current=set(current_ids), deleted=set(deleted_ids))
        return {"ok": True, **TARGET, "mode": mode, "counts": {**counts, "built": 0, "updated": 0},
                "pending_updates": remaining, "summary_text": "No Catalogue documents required a Build."}

    committed_records: list[dict[str, str]] = []
    selection_updated = False
    failed_work_id = ""
    phase = "source"

    def write_operation() -> None:
        nonlocal selection_updated, failed_work_id, phase
        for work_id, doc_id, write in writes:
            failed_work_id = work_id
            if write.create_only:
                source_model.write_text_atomic_new(write.path, write.text)
            else:
                source_model.write_text_atomic(write.path, write.text)
            committed_records.append({"work_id": work_id, "doc_id": doc_id, "operation": "create" if write.create_only else "update"})
        if selection_write is not None:
            failed_work_id = ""
            source_model.write_text_atomic(selection_write.path, selection_write.text)
            selection_updated = True
        for work_id, doc_id, path in deletes:
            failed_work_id = work_id
            path.unlink()
            committed_records.append({"work_id": work_id, "doc_id": doc_id, "operation": "delete"})
        failed_work_id = ""
        phase = "build"

    changed_paths = [write.path for _work_id, _doc_id, write in writes]
    changed_paths.extend(path for _work_id, _doc_id, path in deletes)
    try:
        rebuild = perform_collection_source_write_and_rebuild(
            repo_root, "catalogue", changed_paths, write_operation,
            suppression_reason="docs-catalogue-regenerate",
            links_doc_ids=None if mode == "full" else sorted(link_doc_ids),
            source_writes_committed=lambda: bool(committed_records or selection_updated),
            build_doc_ids=sorted(build_doc_ids),
            complete_build=mode == "full",
        )
        phase = "pending-list"
        remaining = clear_pending_updates(
            repo_root, pending,
            current=set(pending["current_work_ids"]) if mode == "full" else set(current_ids),
            deleted=set(pending["deleted_work_ids"]) if mode == "full" else set(deleted_ids),
        )
    except Exception as error:
        message = f"{f'Work {failed_work_id}: ' if failed_work_id else ''}{error}"
        if phase == "build" and deletes:
            message += "; inspect the partial deletion and run Full reconciliation if needed"
        payload = {"ok": False, **TARGET, "mode": mode, "failed_phase": phase,
                   "failed_work_id": failed_work_id, "completed_records": committed_records,
                   "selection_updated": selection_updated, "build_completed": phase == "pending-list",
                   "committed_source_operations": len(committed_records) + int(selection_updated),
                   "error": message}
        log_event(repo_root, "docs-catalogue-regenerate-failed", {
            "mode": mode, "failed_phase": phase, "failed_work_id": failed_work_id,
            "committed_source_operations": payload["committed_source_operations"],
        })
        raise CatalogueRegenerationError(payload) from error
    counts["built"] = len(current_ids)
    counts["updated"] = counts["retitle"] + counts["regenerate_body"] + counts["build_only"]
    result = {"ok": True, **TARGET, "mode": mode, "counts": counts, "pending_updates": remaining,
              "rebuild": rebuild,
              "summary_text": (
                  f"Updated {counts['updated']}, created {counts['create']}, deleted {counts['delete']} Catalogue documents."
              )}
    log_event(repo_root, "docs-catalogue-regenerate", {**TARGET, "mode": mode, "counts": counts})
    return result
