from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any
from urllib.parse import quote

from .common import (
    DocsStageConfig,
    document_source_path,
    generated_documents_path,
    json_text,
    monotonic_time,
    read_text,
    resolve_workspace_path,
    write_text,
)
from .pipeline import DocsDataBuilder
from .related_links import prepare_related_links
from .collection_metadata import CollectionDocumentSummary, merge_collection_manifest, read_collection_manifest
from .links_builder import build_document_links, prepare_document_links
from .media_builds import build_collection_media_snapshot
from .links_model import DocumentLinks, DocumentTarget
from .rendering_inputs import RenderingInputs
from .source import DocRecord, DocumentIdentity
from docs_collection_customisations import (
    collection_customisation_authoring_subject_fields,
)
from docs_document_subjects import (
    AUTHORING_SUBJECT_FIELDS,
    FOLDER_PATH_FIELD,
    project_document_subject,
    project_reader_subject,
)
from docs_document_identity import doc_updated_date
from docs_selected_documents import read_selected, refresh_selected_documents
from docs_document_images import has_document_thumbnail
from docs_workspace_config import DocsWorkspaceConfig


class CollectionDocsBuilder(DocsDataBuilder):
    """Render collection sources and maintain one manifest for the build role."""

    def __init__(
        self,
        *,
        repo_root: Path,
        config: DocsStageConfig,
        collection: Any,
        only_doc_ids: list[str] | None = None,
        skip_media_builds: bool = False,
        links_doc_ids: list[str] | None = None,
        related_links_dir: Path | None = None,
        workspace: DocsWorkspaceConfig | None = None,
        rendering_inputs: RenderingInputs | None = None,
    ) -> None:
        self.collection_config = collection
        super().__init__(
            repo_root=repo_root,
            config=config,
            source_dir=document_source_path(collection),
            output_dir=generated_documents_path(collection),
            only_doc_ids=only_doc_ids,
            skip_media_builds=skip_media_builds,
            links_doc_ids=links_doc_ids,
            related_links_dir=related_links_dir,
            workspace=workspace,
            rendering_inputs=rendering_inputs,
        )
        self.collection_id = collection.collection
        self.manifest_filename = "manage-manifest.json" if config.stage == "working" else "manifest.json"
        self.output_url_base = self.output_url_base_for(self.output_url_dir())
        self.collection_manifest: dict[str, Any] | None = None
        self.selected_payload: dict[str, Any] | None = None
        if self.targeted_build and not self.only_doc_ids:
            raise ValueError("Targeted collection build requires at least one document ID")

    def output_url_dir(self) -> Path:
        output = generated_documents_path(self.collection_config)
        return resolve_workspace_path(self.repo_root, output)

    def content_url_for(self, doc_id: str) -> str:
        return f"{self.output_url_base}/by-id/{quote(doc_id)}.json"

    def viewer_url_for(self, doc_id: str, anchor: str = "") -> str:
        pairs = [f"collection={quote(self.collection_id)}", f"doc={quote(str(doc_id))}"]
        url = f"{self.viewer_base_url}?{'&'.join(pairs)}"
        return f"{url}#{anchor}" if anchor else url

    def by_id_metadata_entry(self, doc: DocRecord, docs_by_id: Mapping[str, DocumentIdentity]) -> dict[str, Any]:
        entry = super().by_id_metadata_entry(doc, docs_by_id)
        entry.pop("ui_status", None)
        return entry

    def manifest_row(self, doc: DocRecord) -> dict[str, Any]:
        """Project supplied identity, title and update metadata for both readers."""
        row = {"doc_id": doc.doc_id, "title": doc.title, "last_updated": doc_updated_date(doc.last_updated)}
        if has_document_thumbnail(doc.front_matter, collection=self.collection_id):
            row["has_thumbnail"] = True
        return row

    def public_manifest_payload(self, ordered_docs: list[DocRecord]) -> dict[str, Any]:
        """Select authored-first Context thumbnail fields without private Subject data."""
        payload: dict[str, Any] = {
            "docs": [self.manifest_row(doc) for doc in ordered_docs]
        }
        if self.collection_id == "works":
            for doc, row in zip(ordered_docs, payload["docs"], strict=True):
                subject = project_reader_subject(doc.front_matter)
                if row.get("has_thumbnail") is not True and subject is not None:
                    row["subject"] = subject
        return payload

    def manage_manifest_payload(
        self,
        ordered_docs: list[DocRecord],
        *,
        subjects_by_doc_id: dict[str, str | None] | None = None,
    ) -> dict[str, Any]:
        """Project private list metadata without filtering requested documents."""
        rows: list[dict[str, Any]] = []
        for doc in ordered_docs:
            row = self.manifest_row(doc)
            if self.config.stage == "working" and self.collection_id != "catalogue":
                row["draft"] = doc.front_matter["draft"]
            rows.append(row)
        payload: dict[str, Any] = {"docs": rows}
        if subjects_by_doc_id is not None:
            for row in payload["docs"]:
                subject = subjects_by_doc_id[row["doc_id"]]
                if subject is not None:
                    row["subject"] = subject
        return payload

    def folder_subject_supported(self) -> bool:
        return self.config.stage == "working" and FOLDER_PATH_FIELD in collection_customisation_authoring_subject_fields(
            self.collection_config.collection_customisation
        )

    def private_authoring_subjects(
        self,
        ordered_docs: list[DocRecord],
    ) -> dict[str, str | None] | None:
        """Preserve existing projection opt-in and exact Folder capability for scalar rows."""
        if self.collection_id == "catalogue":
            return None
        folder_supported = self.folder_subject_supported()
        configured_fields = collection_customisation_authoring_subject_fields(
            self.collection_config.collection_customisation
        )
        if self.collection_id != "works" and not configured_fields and not any(
            any(field_name in doc.front_matter for field_name in AUTHORING_SUBJECT_FIELDS)
            for doc in ordered_docs
        ):
            return None
        return {
            doc.doc_id: project_document_subject(
                doc.front_matter,
                folder_supported=folder_supported,
            )
            for doc in ordered_docs
        }

    def saved_collection_metadata(self) -> dict[str, Any]:
        """Carry saved metadata between completed builds without row audits."""
        if self.collection_manifest is None:
            self.collection_manifest = read_collection_manifest(self.output_dir / self.manifest_filename)
        return self.collection_manifest

    def selected_documents(self) -> dict[str, Any]:
        """Read Selected once for this operation and retain completed updates."""
        if self.selected_payload is None:
            self.selected_payload = read_selected(self.config)
        return self.selected_payload

    def run(
        self, *, write: bool, emit_diagnostics: bool = False,
        documents: list[DocRecord] | None = None,
        catalogue_works: dict[str, dict[str, Any]] | None = None,
        related_records: dict[DocumentTarget, DocumentLinks | None] | None = None,
        stale_item_ids: list[str] | None = None,
        update_selected: bool = True,
        publication: Any = None,
        expand_dependencies: bool = True,
        catalogue_work_selection: bool = True,
    ) -> dict[str, Any]:
        """Render sources and update this operation's collection manifest.

        Complete Working generation supplies final relationship records and
        stale IDs, and owns the single cross-collection Selected refresh.
        Catalogue dependency renders select a document without a Work unit.
        """
        started_at = monotonic_time()
        self.warnings = []
        self._catalogue_work_cache = {} if catalogue_works is None else catalogue_works
        previous_manifest = self.saved_collection_metadata() if self.targeted_build else None
        docs = self.load_docs(self.only_doc_ids, capture_source_text=not self.skip_media_builds) if documents is None else documents
        if documents is not None:
            self.source_files_scanned = 0
        if not self.targeted_build and documents is None:
            self.validate_canonical_doc_ids(docs)
            self.validate_docs(docs)
        ordered_docs = sorted(docs, key=self.doc_sort_key)
        subjects_by_doc_id = None
        if self.config.stage == "working":
            subjects_by_doc_id = self.private_authoring_subjects(ordered_docs)
            manifest_payload = self.manage_manifest_payload(
                ordered_docs,
                subjects_by_doc_id=subjects_by_doc_id,
            )
        else:
            manifest_payload = self.public_manifest_payload(ordered_docs)
        if self.targeted_build:
            manifest_payload = merge_collection_manifest(previous_manifest, manifest_payload, self.only_doc_ids)
        summaries = [
            CollectionDocumentSummary(row["doc_id"], row["title"])
            for row in manifest_payload["docs"]
        ]
        docs_by_id = {doc.doc_id: doc for doc in summaries}
        media_snapshot = (
            None if self.skip_media_builds or self.targeted_build or self.media_owner.media is None
            else build_collection_media_snapshot(
                self.repo_root, self.media_owner, write=write,
                markdown_sources=[doc.source_text for doc in docs if doc.source_text is not None],
            )
        )
        built_doc_ids = [doc.doc_id for doc in ordered_docs]
        if stale_item_ids is None:
            stale_item_ids = self.stale_doc_payload_ids(built_doc_ids, target_doc_ids=self.only_doc_ids)
        links_build = None
        if related_records is None:
            links_plan = prepare_document_links(
                self, docs, built_doc_ids, stale_item_ids, document_identities=docs_by_id,
            )
            related_records = {}
            links_build = build_document_links(self, links_plan, write=write, related_records=related_records)
        prepare_related_links(self, docs, related_records)
        item_payloads = {
            doc.doc_id: self.item_entry(doc, docs_by_id)
            for doc in ordered_docs
        }
        write_plan = self.build_collection_write_plan(
            manifest_payload,
            item_payloads,
            stale_item_ids=stale_item_ids,
        )
        diagnostics = self.collection_diagnostics_payload(
            docs_total=len(summaries),
            docs_emitted=len(item_payloads),
            write_plan=write_plan,
            elapsed_seconds=round(monotonic_time() - started_at, 3),
        )
        if write:
            self.write_collection_outputs(write_plan, docs_total=len(summaries))
            self.collection_manifest = manifest_payload
        else:
            self.print_collection_summary(write_plan, mode="dry-run", docs_total=len(summaries))
        if self.config.stage == "working" and update_selected:
            selected = refresh_selected_documents(
                self.config, self.collection_config, docs, write=write,
                payload=self.selected_documents(),
            )
            if write:
                self.selected_payload = selected
        if write and self.config.stage == "working":
            from docs_publication_preparation import complete_generation

            complete_generation(self, docs, item_payloads, {}, stale_item_ids,
                                selected=self.selected_payload, related_records=related_records,
                                dependency_ids={Path(name).stem for name in links_build["written"]} if links_build is not None else set(),
                                preparation=publication, expand_dependencies=expand_dependencies,
                                catalogue_work_selection=catalogue_work_selection)
        diagnostics["warning_count"] = len(self.warnings)
        if emit_diagnostics:
            self.print_diagnostics(diagnostics)
        return {
            "manifest_payload": manifest_payload,
            "item_payloads": item_payloads,
            "media_snapshot": media_snapshot,
            "write_plan": write_plan,
            "diagnostics": diagnostics,
            "links_build": links_build,
        }

    def build_collection_write_plan(
        self,
        manifest_payload: dict[str, Any],
        item_payloads: dict[str, dict[str, Any]],
        *,
        stale_item_ids: list[str],
    ) -> dict[str, Any]:
        """Compare the selected manifest and payloads; confine targeted removals."""
        manifest_text = json_text(manifest_payload)
        item_text_by_id: dict[str, str] = {}
        changed_item_ids: list[str] = []
        for doc_id, payload in item_payloads.items():
            text = json_text(payload)
            item_text_by_id[doc_id] = text
            if read_text(self.items_dir / f"{doc_id}.json") != text:
                changed_item_ids.append(doc_id)
        return {
            "manifest_write": (
                read_text(self.output_dir / self.manifest_filename) != manifest_text
                if self.collection_manifest is None else self.collection_manifest != manifest_payload
            ),
            "manifest_text": manifest_text,
            "changed_item_ids": sorted(changed_item_ids),
            "stale_item_ids": sorted(stale_item_ids),
            "item_text_by_id": item_text_by_id,
        }

    def write_collection_outputs(self, write_plan: dict[str, Any], *, docs_total: int) -> None:
        """Write this build role's manifest and requested document output changes."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.items_dir.mkdir(parents=True, exist_ok=True)
        if write_plan["manifest_write"]:
            write_text(self.output_dir / self.manifest_filename, write_plan["manifest_text"])
        for doc_id in write_plan["changed_item_ids"]:
            write_text(self.items_dir / f"{doc_id}.json", write_plan["item_text_by_id"][doc_id])
        for doc_id in write_plan["stale_item_ids"]:
            (self.items_dir / f"{doc_id}.json").unlink(missing_ok=True)
        self.print_collection_summary(write_plan, mode="write", docs_total=docs_total)

    def print_collection_summary(self, write_plan: dict[str, Any], *, mode: str, docs_total: int) -> None:
        verb = "would write" if mode == "dry-run" else "wrote"
        remove_verb = "would remove" if mode == "dry-run" else "removed"
        print(f"Docs collection build ({mode}) stage={self.config.stage} collection={self.collection_id}")
        print(f"  docs total: {docs_total}")
        print(f"  docs rendered: {len(write_plan['item_text_by_id'])}")
        print(f"  docs {verb}: {len(write_plan['changed_item_ids'])}")
        print(f"  docs {remove_verb}: {len(write_plan['stale_item_ids'])}")
        print(f"  {self.manifest_filename} {verb}: {1 if write_plan['manifest_write'] else 0}")
        print(f"  warnings: {len(self.warnings)}")

    def collection_diagnostics_payload(
        self,
        *,
        docs_total: int,
        docs_emitted: int,
        write_plan: dict[str, Any],
        elapsed_seconds: float,
    ) -> dict[str, Any]:
        """Describe the selected manifest and requested writes for build consumers."""
        return {
            "stage": self.config.stage,
            "collection": self.collection_id,
            "build_mode": "targeted_collection" if self.targeted_build else "collection",
            "source_files_scanned": self.source_files_scanned,
            "docs_total": docs_total,
            "docs_emitted": docs_emitted,
            "target_doc_ids": self.only_doc_ids,
            "doc_payloads_changed": len(write_plan["changed_item_ids"]),
            "doc_payloads_removed": len(write_plan["stale_item_ids"]),
            "manifest_filename": self.manifest_filename,
            "manifest_changed": 1 if write_plan["manifest_write"] else 0,
            "warning_count": len(self.warnings),
            "warnings": self.warnings,
            "elapsed_seconds": elapsed_seconds,
        }


def selected_collection(config: DocsStageConfig, collection_id: str) -> Any:
    for collection in config.collections:
        if collection.collection == collection_id:
            return collection
    raise RuntimeError(f"Unknown collection {collection_id!r} in stage {config.stage!r}")
