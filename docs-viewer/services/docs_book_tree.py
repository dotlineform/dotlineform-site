"""Working-only placement and order for the Book collection."""

from __future__ import annotations

from dataclasses import replace
import json
import re
from pathlib import Path
from typing import Any

from docs_book_toc import edition_rows, project_book_contents
from docs_front_matter import rewrite_front_matter_fields
from docs_generation import generate_documents, prepare_restored, rebuild_book_host
from docs_generated_reads import read_generated_json
from docs_management_document_target import (
    ManagedDocumentCollection, committed_document_record, confined_document_path,
    resolve_managed_document_collection, source_doc_from_path,
)
from docs_publication_paths import confined
from docs_publication_preparation import load_preparation
from docs_source_model import BOOK_EDITIONS, parse_collection_document_report, write_text_atomic
from docs_workspace_config import DocsCollectionConfig, DocsStageConfig, document_source_path, generated_documents_path, is_curated_book, require_document_authoring


def resolve_book_collection(
    repo_root: Path, collection: Any, *, config: DocsStageConfig | None = None,
) -> ManagedDocumentCollection:
    if collection is None:
        raise ValueError("Choose a configured Book collection")
    owner = resolve_managed_document_collection(repo_root, collection=collection, config=config)
    if not is_curated_book(owner.document_config):
        raise ValueError("Choose a configured Book collection")
    return owner


def book_order_path(config: DocsCollectionConfig) -> Path:
    return confined(document_source_path(config).parent, "index-order.json")


def book_manifest_path(config: DocsCollectionConfig) -> Path:
    return confined(generated_documents_path(config), "manage-manifest.json")


def project_chapter_sources(
    manifest: dict[str, Any], doc_id: str, sources: list[dict[str, str]],
) -> dict[str, Any]:
    """Carry completed provenance into the private chapter row."""
    row = next((row for row in manifest["docs"] if row["doc_id"] == doc_id), None)
    if row is None:
        raise ValueError(f"Chapter {doc_id} is missing from the Book management manifest")
    if sources:
        row["library_sources"] = sources
    else:
        row.pop("library_sources", None)
    return row


def read_book_order(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def book_order_text(order: dict[str, Any]) -> str:
    return json.dumps(order, ensure_ascii=False, indent=2) + "\n"


def book_headings(tree: list[dict[str, Any]]):
    for node in tree:
        yield node
        yield from node.get("sections", [])


def placement_list(order: dict[str, Any], heading_id: str, *, section_only: bool = False) -> list[str]:
    if heading_id == "":
        return order["root"]
    if not section_only and heading_id in {"@front", "@back"}:
        return order[heading_id[1:]]
    for heading in book_headings(order["tree"]):
        if heading["id"] == heading_id and (not section_only or "sections" not in heading):
            return heading["doc_ids"]
    raise ValueError("Choose Root or a heading in the selected Book")


def validate_book_order(order: Any, book_ids: set[str], host_id: str) -> None:
    headings: set[str] = set()
    placements: set[str] = set()

    def documents(values: Any) -> None:
        if not isinstance(values, list):
            raise ValueError("Book placement document IDs must be a list")
        for doc_id in values:
            if not isinstance(doc_id, str) or doc_id not in book_ids or doc_id in placements:
                raise ValueError("Each placement must identify one distinct Book document")
            placements.add(doc_id)

    def heading(node: Any, fields: set[str], *, top_level_section: bool = False) -> None:
        optional = {"before_opening"} if top_level_section else set()
        if not isinstance(node, dict) or set(node) - optional != fields | {"id", "title", "doc_ids"}:
            raise ValueError("Book headings require an ID, title and document IDs; Parts also require sections")
        if top_level_section and type(node.get("before_opening", False)) is not bool:
            raise ValueError("Before Opening pages must be true or false")
        node_id, title = node["id"], node["title"]
        if not isinstance(node_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", node_id) or node_id in headings:
            raise ValueError("Book heading IDs must be distinct slugs")
        if not isinstance(title, str) or not title.strip():
            raise ValueError("Book headings require a title")
        headings.add(node_id)
        documents(node["doc_ids"])

    if (not isinstance(order, dict) or set(order) - {"link_part_headings"} != {"front", "root", "tree", "back"}
            or not isinstance(order["tree"], list)):
        raise ValueError("Book order requires front matter, Root chapters, headings and back matter")
    if type(order.get("link_part_headings", False)) is not bool:
        raise ValueError("Link Part headings must be true or false")
    front = order["front"]
    if not isinstance(front, list) or front.count(host_id) != 1:
        raise ValueError("Place the Book table of contents among the opening pages")
    documents([doc_id for doc_id in front if doc_id != host_id])
    documents(order["root"])
    for node in order["tree"]:
        if isinstance(node, dict) and "sections" in node:
            heading(node, {"sections"})
            if not isinstance(node["sections"], list):
                raise ValueError("Book Part sections must be a list")
            for section in node["sections"]:
                heading(section, set())
        else:
            heading(node, set(), top_level_section=True)
    documents(order["back"])
    if placements != book_ids:
        raise ValueError("Book order must place every document")


def save_book_tree(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    fields = set(body)
    placement = fields == {"collection", "book_order"}
    settings = fields == {"collection", "link_part_headings"}
    if not placement and not settings and fields != {"collection", "doc_id", "book_edition"}:
        raise ValueError("Book Save requires the complete order, Book settings or one front- or back-matter edition")
    owner = resolve_book_collection(repo_root, body["collection"])
    require_document_authoring(owner.parent_config)
    config = owner.document_config
    manifest_path = book_manifest_path(config)
    manifest = read_generated_json(manifest_path, "Book inventory")
    previous = manifest["book_order"]
    editions = {}
    if settings:
        linked = body["link_part_headings"]
        if type(linked) is not bool:
            raise ValueError("Link Part headings must be true or false")
        if linked == previous.get("link_part_headings", False):
            return {"ok": True, "book_order": previous}
        order = {**previous, "link_part_headings": linked}
    elif placement:
        order = body["book_order"]
        if order == previous:
            return {"ok": True, "book_order": order}
        rows = {row["doc_id"]: row for row in manifest["docs"]}
        validate_book_order(order, set(rows), config.report_host_doc_id)
        previous_matter = set(previous["front"]) | set(previous["back"])
        matter = set(order["front"]) | set(order["back"])
        into_chapters = previous_matter - matter
        editions = {doc_id: "both" for doc_id, row in rows.items()
                    if doc_id in into_chapters and row.get("book_edition", "both") != "both"}
    else:
        order = previous
        rows = {row["doc_id"]: row for row in manifest["docs"]}
        doc_id, edition = body["doc_id"], body["book_edition"]
        if not isinstance(doc_id, str) or doc_id not in rows or doc_id not in (*order["front"], *order["back"]):
            raise ValueError("Choose a front- or back-matter page")
        if edition not in BOOK_EDITIONS:
            raise ValueError("Choose Both, Web only or Export only")
        if edition == rows[doc_id].get("book_edition", "both"):
            return {"ok": True, "book_order": order}
        editions = {doc_id: edition}

    prepared = []
    records = {}
    for doc_id, edition in editions.items():
        path = confined_document_path(owner.source_root, doc_id)
        document = source_doc_from_path(path=path, requested_doc_id=doc_id)
        parts = document.parts
        updates = {"book_edition": edition}
        metadata = {**document.front_matter, **updates}
        source = rewrite_front_matter_fields(parts.prefix, updates, fields=parts.fields) + parts.body
        report = parse_collection_document_report(
            repo_root, owner.parent_config, config, source,
            front_matter=metadata, body=document.body, source_name=path.name,
        )
        thumbnail = rows[doc_id].get("has_thumbnail", False)
        prepared.append(replace(document, front_matter=metadata, source_text=source, parts=None,
                                report=report, has_thumbnail=thumbnail))
        records[doc_id] = committed_document_record(
            metadata, doc_id, config, collection=owner.collection, thumbnail=thumbnail,
        )

    saved_records = []
    result = {"ok": True, "records": saved_records}
    phase = "saving Markdown"
    target = owner.collection
    try:
        for document in prepared:
            target = document.doc_id
            write_text_atomic(document.path, document.source_text)
            saved_records.append(records[target])
        if placement or settings:
            phase = "saving Book order"
            target = "index-order.json"
            write_text_atomic(book_order_path(config), book_order_text(order))

        result["book_order"] = order
        phase = "generating Working output"
        target = owner.collection
        if prepared:
            from docs_write_rebuild import create_collection_builder, prepared_build_record

            doc_ids = [document.doc_id for document in prepared]
            builder = create_collection_builder(repo_root, owner, owner.workspace, doc_ids=doc_ids)
            builder.collection_manifest = manifest
            rebuilt = generate_documents(
                builder, write=True, documents=[prepared_build_record(builder, document) for document in prepared],
                book_order=order, related_records={}, media_writes={doc_id: {} for doc_id in doc_ids}, update_selected=False,
            )
            result["book_toc"] = rebuilt.get("book_toc")
        else:
            completed = {**manifest, "book_order": order}
            host_id = config.report_host_doc_id
            before = edition_rows(manifest, "web")
            after = before if settings else edition_rows(completed, "web")
            contents = project_book_contents(order, after, host_id)
            toc_changed = contents != project_book_contents(previous, before, host_id)
            write_text_atomic(manifest_path, json.dumps(completed, ensure_ascii=False, indent=2) + "\n")
            publication = None
            rendering_inputs = None
            if before.keys() != after.keys():
                phase = "preparing Book publication"
                publication = load_preparation(repo_root, owner.workspace)
                publication.metadata.collection(owner.collection, completed, book_rows=after)
                publication.documents(config, set(), [], changed_ids=set())
                rendering_inputs = prepare_restored(owner.parent_config, {}, publication, finalize_publication=False)
            if toc_changed:
                phase = "rebuilding the Book TOC"
                result["book_toc"] = rebuild_book_host(
                    repo_root, owner.parent_config, owner.workspace, config, contents, publication=publication,
                    rendering_inputs=rendering_inputs,
                )
            if publication is not None:
                phase = "saving the Book publication handoff"
                publication.write_metadata()
                publication.save()
    except (OSError, RuntimeError, ValueError) as error:
        message = f"Book Save failed while {phase} ({target}): {error}"
        if saved_records:
            saved_ids = ", ".join(record["doc_id"] for record in saved_records)
            message += f" Saved edition changes for {saved_ids}."
        if (placement or settings) and "book_order" in result:
            message += " Book order saved."
        return {**result, "ok": False, "error": message}
    return result


def remove_book_placements(owner: ManagedDocumentCollection, removed: set[str]) -> dict[str, Any]:
    path = book_order_path(owner.document_config)
    order = read_book_order(path)
    for key in ("front", "root", "back"):
        order[key] = [doc_id for doc_id in order[key] if doc_id not in removed]
    for heading in book_headings(order["tree"]):
        heading["doc_ids"] = [doc_id for doc_id in heading["doc_ids"] if doc_id not in removed]
    write_text_atomic(path, book_order_text(order))
    return order
