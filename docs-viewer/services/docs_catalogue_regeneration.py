"""Per-Work Catalogue document generation and explicit design maintenance."""

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
from studio.services.catalogue.catalogue_pending_updates import read_pending_updates, remove_pending_update, write_pending_updates
from studio.services.catalogue.catalogue_pending_publication import merge_completed_works, read_pending_publication
from studio.services.catalogue.catalogue_pending_state import pending_counts


TARGET = {"collection": "catalogue"}


class CatalogueRegenerationError(RuntimeError):
    """Retain completed source/build effects and identify the unfinished Work/step."""

    def __init__(self, payload: dict[str, Any]) -> None:
        super().__init__(payload["error"])
        self.payload = payload


def _selection_write(config: Any, work_id: str) -> SourceWrite | None:
    path = selected_path(config)
    original = path.read_bytes()
    payload = json.loads(original)
    validate_selected_payload(payload)
    rows = [row for row in payload["docs"] if row.get("collection") != "catalogue" or row["doc_id"] != work_id]
    if rows == payload["docs"]:
        return None
    return SourceWrite(path, selected_text({**payload, "docs": rows}), original_bytes=original)


def regenerate_catalogue(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    """Regenerate only refreshed entries; caller-selected modes are retired."""
    if not isinstance(body, dict) or body != TARGET:
        raise ValueError("Regenerate requires only the Working Catalogue collection")
    return _regenerate(repo_root, design_maintenance=False)


def reconcile_catalogue_design(repo_root: Path) -> dict[str, Any]:
    """Explicitly rebuild supplied Catalogue sources/documents after design changes.

    False-readiness Works are excluded. Unqueued repairs become document-only
    publication changes; queued ready entries retain their exact media selections.
    Orphan source cleanup has no authority to reconstruct media deletions.
    """
    return _regenerate(repo_root, design_maintenance=True)


def _regenerate(repo_root: Path, *, design_maintenance: bool) -> dict[str, Any]:
    pending = read_pending_updates(repo_root)
    read_pending_publication(repo_root)
    collection = resolve_managed_document_collection(repo_root, **TARGET)
    require_document_authoring(collection.parent_config)
    selections = {family: {wid: dict(entry) for wid, entry in pending[family].items() if entry["refreshed"]}
                  for family in ("current_works", "deleted_works")}
    if design_maintenance:
        works = read_catalogue_work_index(repo_root)
        documents = catalogue_source_documents(repo_root)
        unfinished = {wid for family in ("current_works", "deleted_works")
                      for wid, entry in pending[family].items() if not entry["refreshed"]}
        for wid in sorted(set(works) - unfinished):
            selections["current_works"].setdefault(wid, {"metadata": True, "image": False, "file_names": [], "refreshed": True})
        for wid in sorted(set(documents) - set(works) - unfinished):
            selections["deleted_works"].setdefault(wid, {"image": False, "file_names": [], "refreshed": True})
    else:
        documents = catalogue_source_documents(repo_root, sorted(set(selections["current_works"]) | set(selections["deleted_works"])))
    counts = {"create": 0, "retitle": 0, "regenerate_body": 0, "build_only": 0, "delete": 0, "built": 0, "updated": 0}
    committed: list[dict[str, str]] = []
    selection_updated = False
    maintenance_paths: list[Path] = []
    maintenance_completed = []
    timestamp = source_model.current_doc_timestamp()
    work_id, phase = "", "source"
    try:
        for family in ("current_works", "deleted_works"):
            for work_id, selection in sorted(selections[family].items()):
                phase = "source"
                document = documents.get(work_id)
                writes: list[SourceWrite] = []
                download_names: set[str] = set()
                operation = "delete"
                if family == "current_works":
                    work = read_catalogue_work(repo_root, work_id)["work"]
                    record = catalogue_work_record(work)
                    download_names = {item["filename"] for item in work.get("downloads", [])}
                    if document is None:
                        create = plan_create(repo_root, {**TARGET, "work_id": work_id, "title": record.title}, body_markdown=record.body)
                        writes.extend(create.source_writes)
                        counts["create"] += 1
                        operation = "create"
                    else:
                        title_changed = document.title != record.title
                        if title_changed or design_maintenance:
                            metadata = {**document.front_matter, "title": record.title}
                            if title_changed:
                                metadata = source_model.advance_doc_front_matter(
                                    metadata, timestamp=source_model.strictly_later_doc_timestamp(document.front_matter["last_updated"], timestamp),
                                )
                            text = source_model.format_source(metadata, record.body, collection="catalogue")
                            if text != document.source_text:
                                writes.append(SourceWrite(document.path, text))
                                counts["retitle" if title_changed else "regenerate_body"] += 1
                        if not writes:
                            counts["build_only"] += 1
                        operation = "update"
                    selection = {**selection, "metadata": selection["metadata"] or design_maintenance}
                    selection_write = None
                else:
                    selection_write = _selection_write(collection.parent_config, work_id)
                    counts["delete"] += 1

                def write_operation() -> None:
                    nonlocal phase, selection_updated
                    for write in writes:
                        writer = source_model.write_text_atomic_new if write.create_only else source_model.write_text_atomic
                        writer(write.path, write.text)
                        committed.append({"work_id": work_id, "doc_id": work_id, "operation": operation})
                    if family == "deleted_works" and document is not None:
                        document.path.unlink(missing_ok=True)
                        committed.append({"work_id": work_id, "doc_id": work_id, "operation": "delete"})
                    if selection_write is not None:
                        source_model.write_text_atomic(selection_write.path, selection_write.text)
                        selection_updated = True
                    phase = "build"

                paths = [write.path for write in writes]
                if family == "deleted_works" and document is not None:
                    paths.append(document.path)
                completed = (family, work_id, selection, download_names)
                if design_maintenance:
                    write_operation()
                    maintenance_paths.extend(paths)
                    maintenance_completed.append(completed)
                    continue
                perform_collection_source_write_and_rebuild(repo_root, "catalogue", paths, write_operation,
                                                            links_doc_ids=[work_id], build_doc_ids=[work_id])
                phase = "publication queue"
                merge_completed_works(repo_root, [completed])
                phase = "updates queue"
                if work_id in pending[family]:
                    remove_pending_update(repo_root, pending, family, work_id)
                if family == "current_works":
                    counts["built"] += 1
        if design_maintenance:
            work_id, phase = "Catalogue maintenance", "build"
            perform_collection_source_write_and_rebuild(repo_root, "catalogue", maintenance_paths, lambda: None, complete_build=True)
            phase = "publication queue"
            merge_completed_works(repo_root, maintenance_completed)
            phase = "updates queue"
            for family, wid, _selection, _names in maintenance_completed:
                pending[family].pop(wid, None)
            write_pending_updates(repo_root, pending)
            counts["built"] = len(selections["current_works"])
    except Exception as error:
        payload = {"ok": False, **TARGET, "failed_phase": phase, "failed_work_id": work_id,
                   "completed_records": committed, "selection_updated": selection_updated,
                   "committed_source_operations": len(committed) + int(selection_updated),
                   "error": f"Work {work_id}, {phase}: {error}"}
        log_event(repo_root, "docs-catalogue-regenerate-failed", {"failed_phase": phase, "failed_work_id": work_id})
        raise CatalogueRegenerationError(payload) from error
    counts["updated"] = counts["retitle"] + counts["regenerate_body"] + counts["build_only"]
    result = {"ok": True, **TARGET, "counts": counts, "pending_updates": pending_counts(pending),
              "summary_text": f"Updated {counts['updated']}, created {counts['create']}, deleted {counts['delete']} Catalogue documents."}
    log_event(repo_root, "docs-catalogue-regenerate", {"counts": counts, "design_maintenance": design_maintenance})
    return result
