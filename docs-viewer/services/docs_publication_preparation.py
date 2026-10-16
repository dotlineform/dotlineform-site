"""Upstream public artifacts and exact generation-to-publication handoffs.

Saved private metadata selects eligibility effects without reopening the corpus.
Rendering stays with the document builders; Publish consumes finished files only.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from docs_deploy_repo import project_document_payload
from docs_document_images import generated_thumbnail_filename
from docs_publication_ignore import read_publication_ignore_ids
from docs_publication_payloads import project_public_view
from docs_publication_queue import read_queue, save_queue, select_document, select_shared
from docs_publication_media import HTML_START_TAG_PATTERN, MEDIA_URL_ATTRIBUTE_PATTERN, _media_identity_from_url
from docs_source_model import write_text_atomic
from docs_workspace_config import generated_documents_path, select_workspace_stage, safe_relative_path


class PublicationHandoffError(RuntimeError):
    """Local generation completed, but its public handoff is incomplete."""


def preparation_root(workspace: Any) -> Path:
    return generated_documents_path(select_workspace_stage(workspace, "working")).parent / "publication"


def confined(root: Path, relative: str | Path) -> Path:
    relative = safe_relative_path(str(relative), field="publication artifact")
    path = root / relative
    if path.resolve() != path or not path.is_relative_to(root):
        raise ValueError("Publication artifact must stay inside its configured owner")
    return path


def public_document_path(workspace: Any, collection: str, doc_id: str) -> Path:
    prefix = Path("collections") / collection if collection else Path("documents")
    return confined(preparation_root(workspace), prefix / "by-id" / f"{doc_id}.json")


def public_shared_path(workspace: Any, owner: str, output: str) -> Path:
    if owner == "workspace":
        names = {"ordinary_index": "index-tree.json", "recent": "recent.json", "selected": "selected.json"}
        return confined(preparation_root(workspace), Path("documents") / names[output])
    if output != "collection_manifest":
        raise ValueError(f"Unknown collection publication output: {output}")
    return confined(preparation_root(workspace), Path("collections") / owner / "manifest.json")


def write_public(path: Path, value: Any) -> None:
    write_text_atomic(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def document_media(owner: Any, payload: dict[str, Any]) -> dict[str, list[str]]:
    """Extract exact references from the completed render, without media reads."""
    if owner.media is None:
        return {}
    collection = getattr(owner, "collection", "")
    prefix = f"collections/{collection}" if collection else "workspace"
    references: dict[str, set[str]] = {}
    thumbnail = generated_thumbnail_filename(payload, doc_id=payload["doc_id"], collection=collection)
    if thumbnail:
        references["thumbs"] = {thumbnail}
    for tag in HTML_START_TAG_PATTERN.finditer(payload["content_html"]):
        for attribute in MEDIA_URL_ATTRIBUTE_PATTERN.finditer(tag["body"]):
            value = attribute["quoted_value"] if attribute["quote"] else attribute["unquoted_value"]
            for kind in owner.media.types:
                identity = _media_identity_from_url(value, f"docs-media:{prefix}/{kind}")
                if identity:
                    references.setdefault(kind, set()).add(identity)
                    break
    return {kind: sorted(names) for kind, names in references.items()}


def eligible_documents(workspace: Any, records: dict[str, Any], ignored: frozenset[str]) -> set[str]:
    working = select_workspace_stage(workspace, "working")
    hosts = {owner.collection: owner.report_host_doc_id for owner in working.collections}
    resolved: dict[str, bool] = {}

    def eligible(doc_id: str) -> bool:
        if doc_id in resolved:
            return resolved[doc_id]
        record = records[doc_id]
        collection = record["collection"]
        if record["draft"] or (not collection and doc_id in ignored):
            resolved[doc_id] = False
            return False
        parent = hosts[collection] if collection else record["parent_id"]
        resolved[doc_id] = not parent or (parent in records and eligible(parent))
        return resolved[doc_id]

    return {doc_id for doc_id in records if eligible(doc_id)}


class PublicationPreparation:
    """Explicit operation inputs; constructors perform no I/O or generation."""

    def __init__(self, repo_root: Path, workspace: Any, state: dict[str, Any], pending: dict[str, Any], ignored: frozenset[str]) -> None:
        self.repo_root = repo_root
        self.workspace = workspace
        self.state = state
        self.pending = pending
        self.ignored = ignored
        self.catalogue_documents: set[str] = set()
        self.mermaid_runtime: Any = None

    def documents(self, builder: Any, docs: list[Any], payloads: dict[str, Any], navigation: dict[str, Any], deleted: list[str], *, selected: dict[str, Any] | None, baseline: bool = False, catalogue_work_selection: bool = True) -> None:
        collection = getattr(builder, "collection_id", "")
        previous = set(self.state["eligible"])
        records = self.state["documents"]
        known = set(records)
        removed = {doc_id: records.pop(doc_id) for doc_id in deleted if doc_id in records}
        previous_records = {doc.doc_id: records.get(doc.doc_id) for doc in docs}
        for doc in docs:
            row = builder.public_manifest_payload([doc])["docs"][0] if collection else None
            records[doc.doc_id] = {
                "collection": collection, "parent_id": doc.parent_id if not collection else "",
                "draft": False if collection == "catalogue" else doc.front_matter["draft"],
                "media": {}, "row": row,
                "mermaid": [] if previous_records[doc.doc_id] is None else previous_records[doc.doc_id]["mermaid"],
                "public_ready": False,
            }
        if not collection:
            self.state["navigation"] = navigation
        current = eligible_documents(self.workspace, records, self.ignored)
        self.state["eligible"] = sorted(current)
        baseline_source = None
        if baseline and builder.media_owner.media is not None:
            preview = select_workspace_stage(self.workspace, "preview")
            owner = next(child for child in preview.collections if child.collection == collection) if collection else preview
            baseline_source = owner.media.types["svg"].asset_location
        for doc in docs:
            payload = copy.deepcopy(payloads[doc.doc_id])
            record = records[doc.doc_id]
            if doc.doc_id in current:
                from docs_mermaid_preparation import prepare_document_mermaid

                payload, record["mermaid"], self.mermaid_runtime = prepare_document_mermaid(
                    self.repo_root, builder.media_owner, doc, payload, previous_records[doc.doc_id],
                    force=not builder.targeted_build, baseline_source=baseline_source, runtime=self.mermaid_runtime,
                )
                payload.pop("draft", None)
                data = project_document_payload(project_public_view(self.workspace, payload))
                write_text_atomic(public_document_path(self.workspace, collection, doc.doc_id), data.decode("utf-8"))
                record["public_ready"] = True
            record["media"] = document_media(builder.media_owner, payload)
        if collection == "catalogue" and catalogue_work_selection:
            self.catalogue_documents.update(set(payloads) & current)
        changed = set(payloads) | (current ^ previous) | set(removed)
        for doc_id in changed:
            record = records.get(doc_id) or removed[doc_id]
            # Catalogue Work generation retains its own item queue. Host changes
            # are design-time collection changes, not canonical Work deletion.
            if record["collection"] == "catalogue" and catalogue_work_selection:
                host_change = doc_id in known and doc_id not in removed and doc_id in (current ^ previous)
                withdrawal = doc_id not in current and (host_change or doc_id in payloads)
                restoration = doc_id in current and host_change and doc_id not in payloads
                if not withdrawal and not restoration:
                    continue
            select_document(self.pending, doc_id, record["collection"], media=record["media"], delete=doc_id not in current)
        for doc_id, record in removed.items():
            public_document_path(self.workspace, record["collection"], doc_id).unlink(missing_ok=True)
        owners = {records[doc_id]["collection"] for doc_id in current ^ previous if doc_id in records}
        if collection != "catalogue" or catalogue_work_selection or any(
            previous_records[doc.doc_id] is None or records[doc.doc_id]["row"] != previous_records[doc.doc_id]["row"] for doc in docs
        ):
            owners.add(collection)
        self.aggregates(current, selected=selected, owners=owners)

    def aggregates(self, eligible: set[str], *, selected: dict[str, Any] | None, owners: set[str]) -> None:
        def nodes(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
            result = []
            for row in rows:
                if row["doc_id"] not in eligible:
                    continue
                projected = {key: value for key, value in row.items() if key not in {"draft", "children"}}
                if row.get("children"):
                    children = nodes(row["children"])
                    if children:
                        projected["children"] = children
                result.append(projected)
            return result

        if "" in owners:
            tree = {**self.state["navigation"], "docs": nodes(self.state["navigation"]["docs"])}
            self.shared("workspace", "ordinary_index", project_public_view(self.workspace, tree))
        for collection in owners - {""}:
            owner = next(child for child in select_workspace_stage(self.workspace, "working").collections if child.collection == collection)
            if owner.report_host_doc_id not in eligible:
                select_shared(self.pending, collection, "collection_manifest", delete=True)
                continue
            rows = [record["row"] for doc_id, record in self.state["documents"].items() if record["collection"] == collection and doc_id in eligible]
            self.shared(collection, "collection_manifest", {"docs": sorted(rows, key=lambda row: (row["title"].lower(), row["doc_id"]))})
        if selected is not None:
            self.selected(selected)

    def selected(self, payload: dict[str, Any]) -> None:
        eligible = set(self.state["eligible"])
        self.shared("workspace", "selected", {**payload, "docs": [row for row in payload["docs"] if row["doc_id"] in eligible]})

    def shared(self, owner: str, output: str, payload: dict[str, Any]) -> None:
        write_public(public_shared_path(self.workspace, owner, output), payload)
        select_shared(self.pending, owner, output)

    def save(self, *, catalogue_pending: dict[str, Any] | None = None) -> None:
        self.state["ignored"] = sorted(self.ignored)
        write_public(confined(preparation_root(self.workspace), "state.json"), self.state)
        save_queue(self.workspace, self.pending)
        if self.catalogue_documents or catalogue_pending is not None:
            from studio.services.catalogue.catalogue_pending_publication import FILENAME, merge_document_selections
            from studio.services.catalogue.catalogue_pending_state import load_pending_queue, pending_path, persist_pending_queue

            path = pending_path(self.repo_root, FILENAME, workspace=self.workspace)
            pending = load_pending_queue(path) if catalogue_pending is None else catalogue_pending
            merge_document_selections(pending, self.catalogue_documents)
            persist_pending_queue(path, pending, progress="published")
            self.catalogue_documents.clear()


def load_preparation(repo_root: Path, workspace: Any, *, ignored_ids: frozenset[str] | None = None) -> PublicationPreparation:
    state = json.loads(confined(preparation_root(workspace), "state.json").read_bytes())
    return PublicationPreparation(repo_root, workspace, state, read_queue(workspace), frozenset(state["ignored"]) if ignored_ids is None else ignored_ids)


def complete_generation(builder: Any, docs: list[Any], payloads: dict[str, Any], navigation: dict[str, Any], deleted: list[str], *, selected: dict[str, Any] | None, related_records: dict[Any, Any], dependency_ids: set[str], preparation: PublicationPreparation | None = None, expand_dependencies: bool = True, recent: dict[str, Any] | None = None, catalogue_work_selection: bool = True) -> None:
    """Carry loaded/rendered inputs to public preparation and persist its handoff."""
    try:
        if preparation is None:
            ignored = None if builder.targeted_build or getattr(builder, "collection_id", "") else read_publication_ignore_ids(builder.repo_root, config=builder.config)
            operation = load_preparation(builder.repo_root, builder.workspace, ignored_ids=ignored)
        else:
            operation = preparation
        operation.documents(builder, docs, payloads, navigation, deleted, selected=selected, catalogue_work_selection=catalogue_work_selection)
        if recent is not None:
            operation.shared("workspace", "recent", recent)
        if expand_dependencies:
            prepare_dependencies(builder, {target: record for target, record in related_records.items() if target.doc_id in dependency_ids}, set(payloads) | set(deleted), operation)
            prepare_restored(builder, related_records, operation)
        if preparation is None:
            operation.save()
    except Exception as error:
        raise PublicationHandoffError(f"Selected local documents were generated, but their publication handoff is incomplete: {error}") from error


def prepare_dependencies(builder: Any, related_records: dict[Any, Any], supplied: set[str], operation: PublicationPreparation) -> None:
    """Render exact affected saved neighbours with the existing rendering owner."""
    targets = [target for target, record in related_records.items() if target.doc_id not in supplied and record is not None]
    render_targets(builder, targets, related_records, operation)


def prepare_restored(builder: Any, related_records: dict[Any, Any], operation: PublicationPreparation) -> None:
    """Prepare newly eligible drafts only when no completed public form exists."""
    from docs_builder.links_model import DocumentTarget

    eligible = set(operation.state["eligible"])
    targets = [DocumentTarget(record["collection"], doc_id) for doc_id, record in operation.state["documents"].items()
               if not record["public_ready"] and doc_id in eligible]
    render_targets(builder, targets, related_records, operation)


def render_targets(builder: Any, targets: list[Any], related_records: dict[Any, Any], operation: PublicationPreparation) -> None:
    """Read/render exact restored or directly dependent saved sources upstream."""
    if not targets:
        return
    from docs_builder.collection import CollectionDocsBuilder
    from docs_builder.pipeline import DocsDataBuilder

    owners = {owner.collection: owner for owner in builder.config.collections}
    parents: dict[str, str] = {}

    def collect(rows: list[dict[str, Any]], parent: str = "") -> None:
        for row in rows:
            parents[row["doc_id"]] = parent
            collect(row.get("children", []), row["doc_id"])

    collect(operation.state["navigation"]["docs"])
    for target in targets:
        arguments = {"repo_root": builder.repo_root, "config": builder.config, "workspace": builder.workspace,
                     "rendering_inputs": builder.rendering_inputs, "only_doc_ids": [target.doc_id], "links_doc_ids": [], "skip_media_builds": True}
        neighbour = CollectionDocsBuilder(**arguments, collection=owners[target.collection]) if target.collection else DocsDataBuilder(**arguments, skip_recent=True)
        hierarchy = {"parent_ids": parents} if not target.collection else {}
        docs = neighbour.load_docs([target.doc_id], **hierarchy)
        if not docs:
            continue
        # A changed Related Links section selects a document, not Work JSON/media.
        selection = {"catalogue_work_selection": False} if target.collection == "catalogue" else {}
        neighbour.run(write=True, documents=docs, related_records=related_records, publication=operation, expand_dependencies=False,
                      update_selected=False, catalogue_works=builder._catalogue_work_cache, **hierarchy, **selection)


def queue_shared_file(config: Any, output: str) -> None:
    """Queue completed Search bytes without reading or rewriting the index."""
    pending = read_queue(config)
    select_shared(pending, "workspace", output)
    save_queue(config, pending)


def requeue_media(repo_root: Path, workspace: Any, collection: str, kind: str, filename: str) -> None:
    """Known media writes reuse eligible saved references and prepared documents."""
    operation = load_preparation(repo_root, workspace)
    eligible = set(operation.state["eligible"])
    changed = False
    for doc_id, record in operation.state["documents"].items():
        if record["collection"] == collection and doc_id in eligible and filename in record["media"].get(kind, []):
            select_document(operation.pending, doc_id, collection, media=record["media"])
            changed = True
    if changed:
        save_queue(workspace, operation.pending)
