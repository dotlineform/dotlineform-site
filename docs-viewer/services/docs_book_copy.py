"""Copy selected Library fragments into Working Book documents."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from docs_book_tree import book_headings, book_tree_paths, write_book_tree
from docs_document_identity import allocate_doc_id, current_doc_timestamp, is_immutable_doc_id
from docs_front_matter import book_source_records, rewrite_front_matter_fields
from docs_generation import generate_documents
from docs_management_document_target import (
    ManagedDocumentCollection,
    committed_document_record,
    confined_document_path,
    resolve_managed_document_collection,
    source_doc_from_path,
)
from docs_publication_paths import confined
from docs_publication_preparation import write_json
from docs_source_media_adoption import prepare_source_media_adoption
from docs_source_media_service import write_prepared_source_media
from docs_source_model import SourceDoc, format_source, new_document_source, write_text_atomic, write_text_atomic_new
from docs_workspace_config import require_document_authoring
from docs_write_rebuild import create_collection_builder, prepared_build_record


def copied_flags_path(library: ManagedDocumentCollection) -> Path:
    return confined(library.source_root.parent, "copied-to-book.json")


def read_copied_flags(repo_root: Path) -> dict[str, Any]:
    library = resolve_managed_document_collection(repo_root, collection="library")
    return {"doc_ids": json.loads(copied_flags_path(library).read_text(encoding="utf-8"))}


def library_selection_ids(value: Any) -> list[str]:
    if (
        not isinstance(value, list) or not value
        or any(not isinstance(doc_id, str) or not is_immutable_doc_id(doc_id) for doc_id in value)
        or len(set(value)) != len(value)
    ):
        raise ValueError("Select distinct Library document IDs")
    return value


def clear_copied_flags(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    if set(body) != {"doc_ids"}:
        raise ValueError("Clear Copied to Book requires selected Library document IDs")
    selected = set(library_selection_ids(body["doc_ids"]))
    library = resolve_managed_document_collection(repo_root, collection="library")
    require_document_authoring(library.parent_config)
    path = copied_flags_path(library)
    saved = json.loads(path.read_text(encoding="utf-8"))
    cleared = [doc_id for doc_id in saved if doc_id in selected]
    if cleared:
        write_json(path, [doc_id for doc_id in saved if doc_id not in selected])
    return {"ok": True, "cleared_doc_ids": cleared}


def read_chapter(book: ManagedDocumentCollection, doc_id: Any) -> SourceDoc:
    if not isinstance(doc_id, str) or not is_immutable_doc_id(doc_id):
        raise ValueError("Select one Book chapter")
    path = confined_document_path(book.source_root, doc_id)
    document = source_doc_from_path(path=path, requested_doc_id=doc_id)
    if "copied_from_library" in document.front_matter:
        raise ValueError("Select a chapter rather than a working copy")
    return document


def with_chapter_sources(chapter: SourceDoc, records: list[dict[str, str]]) -> SourceDoc:
    if records == chapter.front_matter.get("library_sources", []):
        return chapter
    parts = chapter.parts
    if parts is None:
        metadata = {**chapter.front_matter, "library_sources": records}
        return replace(chapter, front_matter=metadata, source_text=format_source(metadata, chapter.body))
    metadata = dict(chapter.front_matter)
    if records:
        metadata["library_sources"] = records
    else:
        metadata.pop("library_sources", None)
    prefix = rewrite_front_matter_fields(
        parts.prefix, {"library_sources": records} if records else {},
        remove_fields=() if records else ("library_sources",), fields=parts.fields,
    )
    return replace(chapter, front_matter=metadata, source_text=prefix + parts.body, parts=None)


def complete_book_documents(repo_root: Path, book: ManagedDocumentCollection, documents: list[SourceDoc]) -> None:
    builder = create_collection_builder(repo_root, book, book.workspace, doc_ids=[doc.doc_id for doc in documents])
    records = [prepared_build_record(builder, doc) for doc in documents]
    generate_documents(builder, write=True, documents=records)


def save_chapter_sources(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    if set(body) != {"doc_id", "library_sources"}:
        raise ValueError("Library sources Save requires a chapter ID and source list")
    records = book_source_records(body["library_sources"])
    book = resolve_managed_document_collection(repo_root, collection="book")
    require_document_authoring(book.parent_config)
    current = read_chapter(book, body["doc_id"])
    updated = with_chapter_sources(current, records)
    if updated is not current:
        write_text_atomic(updated.path, updated.source_text)
        complete_book_documents(repo_root, book, [updated])
    return {"ok": True, "doc_id": current.doc_id, "library_sources": records}


def copy_to_book(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    required = {"doc_ids", "section_id"}
    if not required <= body.keys() <= required | {"new_chapter_title", "existing_chapter_id"}:
        raise ValueError("Copy to Book requires selected documents and a Book section")
    doc_ids = library_selection_ids(body["doc_ids"])
    new_chapter_title = ""
    if "new_chapter_title" in body:
        title = body["new_chapter_title"]
        if not isinstance(title, str) or not title.strip():
            raise ValueError("Enter a chapter title")
        new_chapter_title = title.strip()

    library = resolve_managed_document_collection(repo_root, collection="library")
    require_document_authoring(library.parent_config)
    book = replace(
        resolve_managed_document_collection(repo_root, collection="book", config=library.parent_config),
        workspace=library.workspace,
    )
    tree_paths = book_tree_paths(book.document_config)
    tree = json.loads(tree_paths[0].read_text(encoding="utf-8"))
    section_id = body["section_id"]
    section = next((node for node in book_headings(tree) if node["id"] == section_id and "sections" not in node), None)
    if section is None:
        raise ValueError("Choose a Book section")
    existing_chapter = None
    if "existing_chapter_id" in body:
        existing_id = body["existing_chapter_id"]
        if existing_id not in section["doc_ids"]:
            raise ValueError("Choose a chapter in the selected Book section")
        existing_chapter = read_chapter(book, existing_id)
    flags_path = copied_flags_path(library)
    flags = set(json.loads(flags_path.read_text(encoding="utf-8")))
    timestamp = current_doc_timestamp()
    unavailable = set(doc_ids)

    def new_book_document(title: str, markdown: str) -> SourceDoc:
        new_id = allocate_doc_id(timestamp, unavailable)
        unavailable.add(new_id)
        path = confined(book.source_root, f"{new_id}.md")
        if path.exists():
            raise FileExistsError(f"Book source already exists: {new_id}")
        return new_document_source(
            path, new_id, title, markdown, config=book.document_config, timestamp=timestamp,
        )

    new_documents = []
    writes = []
    origins = []
    for source_id in doc_ids:
        source_path = confined_document_path(library.source_root, source_id)
        source = source_doc_from_path(path=source_path, requested_doc_id=source_id)
        origin = {"doc_id": source_id, "title": source.front_matter["title"]}
        new = new_book_document(origin["title"], source.body)
        adopted, media = prepare_source_media_adoption(repo_root, book, new.body, [], doc_id=new.doc_id)
        metadata = {**new.front_matter, "copied_from_library": origin}
        for field in ("summary", "date", "date_display"):
            if field in source.front_matter:
                metadata[field] = source.front_matter[field]
        new_documents.append(replace(new, body=adopted, front_matter=metadata, source_text=format_source(metadata, adopted)))
        writes.extend(media)
        origins.append(origin)

    if new_chapter_title:
        chapter = new_book_document(new_chapter_title, "")
        new_documents.append(with_chapter_sources(chapter, origins))

    changed = new_documents.copy()
    updated_chapter = None
    if existing_chapter is not None:
        existing = existing_chapter.front_matter.get("library_sources", [])
        present = {record["doc_id"] for record in existing}
        updated = with_chapter_sources(
            existing_chapter, existing + [origin for origin in origins if origin["doc_id"] not in present],
        )
        if updated is not existing_chapter:
            updated_chapter = updated
            changed.append(updated)

    saved = []
    effects = []
    phase = "body media"
    try:
        write_prepared_source_media(writes, effects)
        phase = "source persistence"
        for document in new_documents:
            write_text_atomic_new(document.path, document.source_text)
            saved.append(document.doc_id)
        if updated_chapter is not None:
            write_text_atomic(updated_chapter.path, updated_chapter.source_text)
            saved.append(updated_chapter.doc_id)
        phase = "Working generation"
        complete_book_documents(repo_root, book, changed)
        phase = "Book section placement"
        placed_doc_ids = [document.doc_id for document in new_documents]
        section["doc_ids"].extend(placed_doc_ids)
        write_book_tree(tree_paths, tree)
        phase = "Library copy flags"
        if not set(doc_ids) <= flags:
            write_json(flags_path, sorted(flags.union(doc_ids)))
    except (OSError, RuntimeError, ValueError) as error:
        return {
            "ok": False, "error": f"Copy to Book failed during {phase}: {error}",
            "saved_doc_ids": saved, "media_effects": effects,
        }
    return {
        "ok": True,
        "section_id": section_id,
        "placed_doc_ids": placed_doc_ids,
        "copied_doc_ids": doc_ids,
        "records": [
            committed_document_record(
                document.front_matter, document.doc_id, book.document_config,
                collection="book", thumbnail=document.has_thumbnail,
            )
            for document in changed
        ],
    }
