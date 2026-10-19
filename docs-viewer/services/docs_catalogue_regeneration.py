"""Per-Work Catalogue document generation and explicit design maintenance."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

from docs_catalogue_media import read_catalogue_work, read_catalogue_work_index
from docs_catalogue_source_inventory import catalogue_source_documents
from docs_catalogue_work_record import catalogue_work_record
from docs_management_context import log_event
from docs_management_document_target import resolve_managed_document_collection
from docs_selected_documents import selected_path, selected_text
from docs_publication_preparation import load_preparation
from docs_generation import complete_catalogue_handoff
import docs_source_model as source_model
from docs_workspace_config import load_docs_workspace_config, require_document_authoring, select_workspace_stage
from docs_write_rebuild import create_collection_builder, perform_collection_source_write_and_rebuild, validate_changed_source_paths
from studio.services.catalogue.catalogue_pending_updates import FILENAME as UPDATES_FILENAME
from studio.services.catalogue.catalogue_pending_publication import FILENAME as PUBLICATION_FILENAME, merge_completed_work_selections
from studio.services.catalogue.catalogue_pending_state import load_pending_queue, pending_counts, pending_path, persist_pending_queue
from studio.services.catalogue.catalogue_shared_changes import REFRESH_FIELDS


TARGET = {"collection": "catalogue"}


class CatalogueRegenerationError(RuntimeError):
    """Retain completed source/build effects and identify the unfinished Work/step."""

    def __init__(self, payload: dict[str, Any]) -> None:
        super().__init__(payload["error"])
        self.payload = payload


def _remove_selection(builder: Any, work_id: str) -> bool:
    payload = builder.selected_documents()
    rows = [row for row in payload["docs"] if row.get("collection") != "catalogue" or row["doc_id"] != work_id]
    if rows == payload["docs"]:
        return False
    updated = {**payload, "docs": rows}
    source_model.write_text_atomic(selected_path(builder.config), selected_text(updated))
    builder.selected_payload = updated
    return True


def _regeneration_result(repo_root: Path, pending: dict[str, Any], counts: dict[str, int], *, design_maintenance: bool) -> dict[str, Any]:
    counts["updated"] = counts["retitle"] + counts["regenerate_body"] + counts["build_only"]
    result = {"ok": True, **TARGET, "counts": counts, "pending_updates": pending_counts(pending),
              "summary_text": f"Updated {counts['updated']}, created {counts['create']}, deleted {counts['delete']} Catalogue documents."}
    log_event(repo_root, "docs-catalogue-regenerate", {"counts": counts, "design_maintenance": design_maintenance})
    return result


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
    workspace = load_docs_workspace_config(repo_root)
    updates_path = pending_path(repo_root, UPDATES_FILENAME, workspace=workspace)
    pending = load_pending_queue(updates_path)
    if any(pending[field] for field in REFRESH_FIELDS):
        raise ValueError("Complete queued Catalogue shared Refresh before Regenerate.")
    selections = {family: {wid: dict(entry) for wid, entry in pending[family].items() if entry["refreshed"]}
                  for family in ("current_works", "deleted_works")}
    counts = {"create": 0, "retitle": 0, "regenerate_body": 0, "build_only": 0, "delete": 0, "built": 0, "updated": 0}
    if not design_maintenance and not any(selections.values()):
        return _regeneration_result(repo_root, pending, counts, design_maintenance=False)

    config = select_workspace_stage(workspace, "working")
    collection = resolve_managed_document_collection(repo_root, **TARGET, config=config)
    require_document_authoring(config)
    publication_path = pending_path(repo_root, PUBLICATION_FILENAME, workspace=workspace)
    publication = load_pending_queue(publication_path)
    document_publication = load_preparation(repo_root, workspace)
    if design_maintenance:
        works = read_catalogue_work_index(repo_root, workspace=workspace.catalogue.working)
        documents = catalogue_source_documents(repo_root, collection=collection)
        unfinished = {wid for family in ("current_works", "deleted_works")
                      for wid, entry in pending[family].items() if not entry["refreshed"]}
        for wid in sorted(set(works) - unfinished):
            selections["current_works"].setdefault(wid, {"metadata": True, "image": False, "file_names": [], "refreshed": True})
        for wid in sorted(set(documents) - set(works) - unfinished):
            selections["deleted_works"].setdefault(wid, {"image": False, "file_names": [], "refreshed": True})
    else:
        selected_ids = sorted(set(selections["current_works"]) | set(selections["deleted_works"]))
        documents = {}

    builder = create_collection_builder(
        repo_root, collection, workspace, doc_ids=None if design_maintenance else selected_ids,
    )
    committed: list[dict[str, str]] = []
    selection_updated = False
    maintenance_paths: list[Path] = []
    maintenance_completed = []
    work_records: dict[str, dict[str, Any]] = {}
    timestamp = source_model.current_doc_timestamp()
    work_id, phase = "", "source"

    def build_record(document: source_model.SourceDoc) -> Any:
        report = builder.document_report(
            document.source_text, document.front_matter, document.body, source_name=document.path.name,
        )
        return builder.document_record(
            path=document.path, front_matter=document.front_matter, body_markdown=document.body,
            doc_id=document.doc_id, title=document.title, parent_id=document.parent_id, report=report,
        )

    try:
        for family in ("current_works", "deleted_works"):
            for work_id, selection in sorted(selections[family].items()):
                phase = "source"
                if not design_maintenance:
                    documents.update(catalogue_source_documents(repo_root, [work_id], collection=collection))
                document = documents.get(work_id)
                replacement = None
                download_names: set[str] = set()
                operation = "delete"
                if family == "current_works":
                    if work_id not in work_records:
                        work_records[work_id] = read_catalogue_work(repo_root, work_id, workspace=workspace.catalogue.working)["work"]
                    work = work_records[work_id]
                    record = catalogue_work_record(work)
                    download_names = {item["filename"] for item in work.get("downloads", [])}
                    if document is None:
                        replacement = source_model.new_document_source(
                            collection.source_root / f"{work_id}.md", work_id, record.title, record.body,
                            config=collection.document_config, timestamp=timestamp,
                        )
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
                                replacement = replace(
                                    document, front_matter=metadata, title=record.title, source_text=text,
                                    body="\n" + record.body,
                                )
                                counts["retitle" if title_changed else "regenerate_body"] += 1
                        if replacement is None:
                            counts["build_only"] += 1
                        operation = "update"
                    selection = {**selection, "metadata": selection["metadata"] or design_maintenance}
                else:
                    counts["delete"] += 1

                def write_operation() -> None:
                    nonlocal phase, selection_updated
                    if replacement is not None:
                        writer = source_model.write_text_atomic_new if operation == "create" else source_model.write_text_atomic
                        writer(replacement.path, replacement.source_text)
                        documents[work_id] = replacement
                        committed.append({"work_id": work_id, "doc_id": work_id, "operation": operation})
                    if family == "deleted_works":
                        if document is not None:
                            document.path.unlink(missing_ok=True)
                            documents.pop(work_id)
                            committed.append({"work_id": work_id, "doc_id": work_id, "operation": "delete"})
                        if _remove_selection(builder, work_id):
                            selection_updated = True
                    phase = "build"

                paths = [replacement.path] if replacement is not None else []
                if family == "deleted_works" and document is not None:
                    paths.append(document.path)
                completed = (family, work_id, selection, download_names)
                if design_maintenance:
                    validate_changed_source_paths(collection.source_root, paths)
                    write_operation()
                    maintenance_paths.extend(paths)
                    maintenance_completed.append(completed)
                    continue
                current_document = replacement or document
                build_documents = [] if family == "deleted_works" else [build_record(current_document)]
                perform_collection_source_write_and_rebuild(
                    repo_root, "catalogue", paths, write_operation,
                    links_doc_ids=[work_id], build_doc_ids=[work_id], builder=builder,
                    documents=build_documents,
                    publication=document_publication, catalogue_pending=publication,
                )
                phase = "publication queue"
                merge_completed_work_selections(publication, [completed])
                complete_catalogue_handoff(document_publication, pending=publication)
                phase = "updates queue"
                del pending[family][work_id]
                persist_pending_queue(updates_path, pending, progress="refreshed")
                if family == "current_works":
                    counts["built"] += 1
        if design_maintenance:
            work_id, phase = "Catalogue maintenance", "build"
            perform_collection_source_write_and_rebuild(
                repo_root, "catalogue", maintenance_paths, lambda: None, complete_build=True, builder=builder,
                documents=[build_record(document) for document in documents.values()],
                publication=document_publication, catalogue_pending=publication,
            )
            phase = "publication queue"
            merge_completed_work_selections(publication, maintenance_completed)
            complete_catalogue_handoff(document_publication, pending=publication)
            phase = "updates queue"
            for family, wid, _selection, _names in maintenance_completed:
                pending[family].pop(wid, None)
            persist_pending_queue(updates_path, pending, progress="refreshed")
            counts["built"] = len(selections["current_works"])
    except Exception as error:
        payload = {"ok": False, **TARGET, "failed_phase": phase, "failed_work_id": work_id,
                   "completed_records": committed, "selection_updated": selection_updated,
                   "committed_source_operations": len(committed) + int(selection_updated),
                   "error": f"Work {work_id}, {phase}: {error}"}
        log_event(repo_root, "docs-catalogue-regenerate-failed", {"failed_phase": phase, "failed_work_id": work_id})
        raise CatalogueRegenerationError(payload) from error
    return _regeneration_result(repo_root, pending, counts, design_maintenance=design_maintenance)
