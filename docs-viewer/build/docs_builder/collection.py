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
    write_text,
)
from .pipeline import DocsDataBuilder
from .collection_metadata import read_collection_manifest
from docs_selected_documents import read_selected
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
        self.collection_manifest: dict[str, Any] | None = None
        self.selected_payload: dict[str, Any] | None = None
        if self.targeted_build and not self.only_doc_ids:
            raise ValueError("Targeted collection build requires at least one document ID")

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
        self, *, write: bool, documents: list[DocRecord],
        document_identities: dict[str, Any], manifest_payload: dict[str, Any],
        stale_item_ids: list[str],
        related_documents: dict[Any, Any],
        catalogue_works: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        """Render and write the supplied collection artifacts; return completed facts."""
        started_at = monotonic_time()
        self.related_documents = related_documents
        self._catalogue_work_cache = catalogue_works
        item_payloads = {doc.doc_id: self.item_entry(doc, document_identities) for doc in documents}
        write_plan = self.build_collection_write_plan(manifest_payload, item_payloads, stale_item_ids=stale_item_ids)
        diagnostics = self.collection_diagnostics_payload(
            docs_total=len(document_identities), docs_emitted=len(item_payloads), write_plan=write_plan,
            elapsed_seconds=round(monotonic_time() - started_at, 3),
        )
        if write:
            self.write_collection_outputs(write_plan, docs_total=len(document_identities))
            self.collection_manifest = manifest_payload
        else:
            self.print_collection_summary(write_plan, mode="dry-run", docs_total=len(document_identities))
        diagnostics["warning_count"] = len(self.warnings)
        return {
            "manifest_payload": manifest_payload, "item_payloads": item_payloads,
            "write_plan": write_plan, "diagnostics": diagnostics,
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
