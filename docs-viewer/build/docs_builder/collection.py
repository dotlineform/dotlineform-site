from __future__ import annotations

from collections.abc import Sequence
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
from .collection_metadata import CollectionDocumentSummary, merge_collection_manifest, read_collection_manifest
from .links_builder import build_document_links, prepare_document_links
from .media_builds import build_collection_media_snapshot
from .source import DocRecord, DocumentIdentity
from docs_collection_customisations import (
    project_collection_customisation_manifest,
    collection_customisation_authoring_subject_fields,
)
from docs_document_subjects import (
    AUTHORING_SUBJECT_FIELDS,
    FOLDER_PATH_FIELD,
    normalize_authoring_subject,
    project_reader_subject,
    project_subject_associations,
    subject_projection_generation,
)


class CollectionDocsBuilder(DocsDataBuilder):
    def __init__(
        self,
        *,
        repo_root: Path,
        config: DocsStageConfig,
        collection: Any,
        only_doc_ids: list[str] | None = None,
        skip_media_builds: bool = False,
        links_doc_ids: list[str] | None = None,
        links_created_doc_ids: list[str] | None = None,
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
            links_created_doc_ids=links_created_doc_ids,
        )
        self.collection_id = collection.collection
        self.output_url_base = self.output_url_base_for(self.output_url_dir())
        if self.targeted_build and not self.only_doc_ids:
            raise ValueError("Targeted collection build requires at least one document ID")

    def output_url_dir(self) -> Path:
        output = generated_documents_path(self.collection_config)
        return resolve_workspace_path(self.repo_root, output)

    def content_url_for(self, doc_id: str) -> str:
        return f"{self.output_url_base}/by-id/{quote(doc_id)}.json"

    def viewer_url_for(self, doc_id: str, anchor: str = "") -> str:
        parent_doc_id = self.collection_config.report_host_doc_id
        pairs: list[str] = []
        pairs.append(f"stage={quote(self.config.stage)}")
        pairs.append(f"doc={quote(parent_doc_id)}")
        pairs.append(f"subdoc={quote(str(doc_id))}")
        url = f"{self.viewer_base_url}?{'&'.join(pairs)}"
        return f"{url}#{anchor}" if anchor else url

    def by_id_metadata_entry(self, doc: DocRecord, docs: Sequence[DocumentIdentity]) -> dict[str, Any]:
        entry = self.metadata_entry(doc, docs)
        entry.pop("ui_status", None)
        if doc.report is not None:
            entry["report"] = dict(doc.report.as_payload())
        return entry

    def manifest_payload(self, ordered_docs: list[DocRecord]) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "docs": [
                {
                    "doc_id": doc.doc_id,
                    "title": doc.title,
                    "subject": project_reader_subject(doc.front_matter),
                }
                for doc in ordered_docs
            ]
        }
        projected = project_collection_customisation_manifest(
            self.collection_config.collection_customisation,
            ordered_docs,
            published=True,
            repo_root=self.repo_root,
            collection=self.collection_id,
            stage=self.config.stage,
        )
        if projected is not None:
            payload["customisation"] = projected["root"]
            rows_by_id = projected["rows"]
            for row in payload["docs"]:
                row_customisation = rows_by_id.get(row["doc_id"])
                if row_customisation is not None:
                    row["customisation"] = row_customisation
        return payload

    def manage_manifest_payload(
        self,
        ordered_docs: list[DocRecord],
        *,
        subjects_by_doc_id: dict[str, dict[str, Any]] | None = None,
        subject_generation: str = "",
    ) -> dict[str, Any]:
        rows: list[dict[str, Any]] = []
        for doc in ordered_docs:
            row: dict[str, Any] = {
                "doc_id": doc.doc_id,
                "title": doc.title,
                "last_updated": doc.last_updated,
            }
            if self.config.stage == "working":
                row["draft"] = doc.front_matter.get("draft", True)
            rows.append(row)
        payload: dict[str, Any] = {"docs": rows}
        if subjects_by_doc_id is not None:
            payload["subject_generation"] = subject_generation
            for row in payload["docs"]:
                row["authoring_subject"] = subjects_by_doc_id[row["doc_id"]]
        projected = project_collection_customisation_manifest(
            self.collection_config.collection_customisation,
            ordered_docs,
            published=False,
            repo_root=self.repo_root,
            collection=self.collection_id,
            stage=self.config.stage,
        )
        if projected is not None:
            payload["customisation"] = projected["root"]
            rows_by_id = projected["rows"]
            unknown_ids = sorted(set(rows_by_id) - {doc.doc_id for doc in ordered_docs})
            if unknown_ids:
                raise RuntimeError(
                    "Docs collection customisation projected unknown document IDs: "
                    + ", ".join(unknown_ids)
                )
            for row in payload["docs"]:
                row_customisation = rows_by_id.get(row["doc_id"])
                if row_customisation is not None:
                    if "customisation" in row:
                        raise RuntimeError(
                            "Docs collection customisation row namespace collision: "
                            + row["doc_id"]
                        )
                    row["customisation"] = row_customisation
        return payload

    def folder_subject_supported(self) -> bool:
        return self.config.stage == "working" and FOLDER_PATH_FIELD in collection_customisation_authoring_subject_fields(
            self.collection_config.collection_customisation
        )

    def private_authoring_subjects(
        self,
        ordered_docs: list[DocRecord],
    ) -> dict[str, dict[str, Any]] | None:
        folder_supported = self.folder_subject_supported()
        configured_fields = collection_customisation_authoring_subject_fields(
            self.collection_config.collection_customisation
        )
        if not configured_fields and not any(
            any(field_name in doc.front_matter for field_name in AUTHORING_SUBJECT_FIELDS)
            for doc in ordered_docs
        ) and not (self.output_dir / "subject-associations.json").is_file():
            return None
        return {
            doc.doc_id: normalize_authoring_subject(
                doc.front_matter,
                folder_supported=folder_supported,
            )
            for doc in ordered_docs
        }

    def saved_collection_metadata(self) -> tuple[dict[str, Any], dict[str, Any]]:
        """Load the prior list metadata required for a targeted update."""
        manifest = read_collection_manifest(self.output_dir / "manifest.json")
        manage_manifest = read_collection_manifest(self.output_dir / "manage-manifest.json")
        if {row["doc_id"] for row in manifest["docs"]} != {row["doc_id"] for row in manage_manifest["docs"]}:
            raise ValueError("Collection manifests disagree on document membership; run a complete Build first")
        if not (self.semantic_tokens_dir / "index.json").is_file():
            raise RuntimeError(
                "Targeted collection build requires the existing semantic-token index; run a complete Build first"
            )
        return manifest, manage_manifest

    def run(self, *, write: bool, emit_diagnostics: bool = False) -> dict[str, Any]:
        """Build all source documents or merge selected sources into saved metadata."""
        started_at = monotonic_time()
        previous_manifest, previous_manage = self.saved_collection_metadata() if self.targeted_build else (None, None)
        docs = self.load_docs(self.only_doc_ids)
        self.validate_canonical_doc_ids(docs)
        if not self.targeted_build:
            self.validate_docs(docs)
        ordered_docs = sorted(docs, key=self.doc_sort_key)
        manifest_payload = self.manifest_payload(ordered_docs)
        subjects_by_doc_id = self.private_authoring_subjects(ordered_docs)
        manage_manifest_payload = self.manage_manifest_payload(
            ordered_docs,
            subjects_by_doc_id=subjects_by_doc_id,
        )
        if self.targeted_build:
            manifest_payload = merge_collection_manifest(previous_manifest, manifest_payload, self.only_doc_ids)
            manage_manifest_payload = merge_collection_manifest(previous_manage, manage_manifest_payload, self.only_doc_ids)
        summaries = [
            CollectionDocumentSummary(row["doc_id"], row["title"], self.viewer_url_for(row["doc_id"]))
            for row in manifest_payload["docs"]
        ]
        known_ids = {row.doc_id for row in summaries}
        for doc in docs:
            if doc.parent_id and doc.parent_id not in known_ids and not self.allow_unresolved_parent_ids:
                raise RuntimeError(f"Unknown parent_id {doc.parent_id!r} for doc {doc.doc_id!r}")
        media_snapshot = (
            None if self.skip_media_builds or self.targeted_build
            else build_collection_media_snapshot(self.repo_root, self.media_owner, write=write)
        )
        semantic_tokens_by_doc: dict[str, list[dict[str, Any]]] = {}
        item_payloads = {
            doc.doc_id: self.item_entry(doc, summaries, semantic_tokens_by_doc)
            for doc in ordered_docs
        }
        subject_associations_payload: dict[str, Any] | None = None
        if subjects_by_doc_id is not None or "subject_generation" in manage_manifest_payload:
            subjects_by_doc_id = {
                row["doc_id"]: row.setdefault(
                    "authoring_subject", normalize_authoring_subject({}, folder_supported=self.folder_subject_supported())
                )
                for row in manage_manifest_payload["docs"]
            }
            subject_generation = subject_projection_generation(
                stage=self.config.stage,
                collection=self.collection_id,
                subjects_by_doc_id=subjects_by_doc_id,
            )
            subject_associations_payload = project_subject_associations(
                stage=self.config.stage,
                collection=self.collection_id,
                documents=summaries,
                subjects_by_doc_id=subjects_by_doc_id,
                subject_generation=subject_generation,
            )
            manage_manifest_payload["subject_generation"] = subject_generation
        write_plan = self.build_collection_write_plan(
            manifest_payload,
            manage_manifest_payload,
            subject_associations_payload,
            item_payloads,
            target_doc_ids=self.only_doc_ids,
        )
        semantic_token_payloads = self.build_semantic_token_payloads(docs, semantic_tokens_by_doc)
        write_plan.update(self.build_semantic_token_write_plan(semantic_token_payloads))
        links_plan = prepare_document_links(self, docs, item_payloads, write_plan["stale_item_ids"])
        diagnostics = self.collection_diagnostics_payload(
            docs_total=len(summaries),
            docs_emitted=len(item_payloads),
            write_plan=write_plan,
            elapsed_seconds=round(monotonic_time() - started_at, 3),
        )
        if write:
            self.write_collection_outputs(write_plan, docs_total=len(summaries))
        else:
            self.print_collection_summary(write_plan, mode="dry-run", docs_total=len(summaries))
        links_build = build_document_links(self, links_plan, write=write)
        diagnostics["warning_count"] = len(self.warnings)
        if emit_diagnostics:
            self.print_diagnostics(diagnostics)
        return {
            "manifest_payload": manifest_payload,
            "manage_manifest_payload": manage_manifest_payload,
            "subject_associations_payload": subject_associations_payload,
            "item_payloads": item_payloads,
            "semantic_token_payloads": semantic_token_payloads,
            "media_snapshot": media_snapshot,
            "write_plan": write_plan,
            "diagnostics": diagnostics,
            "links_build": links_build,
        }

    def build_collection_write_plan(
        self,
        manifest_payload: dict[str, Any],
        manage_manifest_payload: dict[str, Any],
        subject_associations_payload: dict[str, Any] | None,
        item_payloads: dict[str, dict[str, Any]],
        *,
        target_doc_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Compare selected payloads and confine targeted removals to selected IDs."""
        manifest_text = json_text(manifest_payload)
        manage_manifest_text = json_text(manage_manifest_payload)
        subject_associations_text = (
            json_text(subject_associations_payload)
            if subject_associations_payload is not None
            else ""
        )
        item_text_by_id: dict[str, str] = {}
        changed_item_ids: list[str] = []
        for doc_id, payload in item_payloads.items():
            text = json_text(payload)
            item_text_by_id[doc_id] = text
            if read_text(self.items_dir / f"{doc_id}.json") != text:
                changed_item_ids.append(doc_id)
        existing_item_ids = (
            self.existing_doc_payload_ids(self.items_dir)
            if target_doc_ids is None
            else [doc_id for doc_id in target_doc_ids if (self.items_dir / f"{doc_id}.json").is_file()]
        )
        stale_item_ids = set(existing_item_ids) - set(item_payloads)
        if target_doc_ids is not None:
            stale_item_ids &= set(target_doc_ids)
        return {
            "manifest_write": read_text(self.output_dir / "manifest.json") != manifest_text,
            "manifest_text": manifest_text,
            "manage_manifest_write": (
                read_text(self.output_dir / "manage-manifest.json")
                != manage_manifest_text
            ),
            "manage_manifest_text": manage_manifest_text,
            "subject_associations_write": (
                subject_associations_payload is not None
                and read_text(self.output_dir / "subject-associations.json")
                != subject_associations_text
            ),
            "subject_associations_text": subject_associations_text,
            "changed_item_ids": sorted(changed_item_ids),
            "stale_item_ids": sorted(stale_item_ids),
            "item_text_by_id": item_text_by_id,
        }

    def write_collection_outputs(self, write_plan: dict[str, Any], *, docs_total: int) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.items_dir.mkdir(parents=True, exist_ok=True)
        if write_plan["manifest_write"]:
            write_text(self.output_dir / "manifest.json", write_plan["manifest_text"])
        if write_plan["manage_manifest_write"]:
            write_text(
                self.output_dir / "manage-manifest.json",
                write_plan["manage_manifest_text"],
            )
        if write_plan["subject_associations_write"]:
            write_text(
                self.output_dir / "subject-associations.json",
                write_plan["subject_associations_text"],
            )
        for doc_id in write_plan["changed_item_ids"]:
            write_text(self.items_dir / f"{doc_id}.json", write_plan["item_text_by_id"][doc_id])
        for doc_id in write_plan["stale_item_ids"]:
            (self.items_dir / f"{doc_id}.json").unlink(missing_ok=True)
        self.write_semantic_token_outputs(write_plan)
        self.print_collection_summary(write_plan, mode="write", docs_total=docs_total)

    def print_collection_summary(self, write_plan: dict[str, Any], *, mode: str, docs_total: int) -> None:
        verb = "would write" if mode == "dry-run" else "wrote"
        remove_verb = "would remove" if mode == "dry-run" else "removed"
        print(f"Docs collection build ({mode}) stage={self.config.stage} collection={self.collection_id}")
        print(f"  docs total: {docs_total}")
        print(f"  docs rendered: {len(write_plan['item_text_by_id'])}")
        print(f"  docs {verb}: {len(write_plan['changed_item_ids'])}")
        print(f"  docs {remove_verb}: {len(write_plan['stale_item_ids'])}")
        print(f"  manifest {verb}: {1 if write_plan['manifest_write'] else 0}")
        print(
            "  manage manifest "
            f"{verb}: {1 if write_plan['manage_manifest_write'] else 0}"
        )
        print(
            "  subject associations "
            f"{verb}: {1 if write_plan['subject_associations_write'] else 0}"
        )
        print(f"  semantic tokens {verb}: {1 if write_plan['semantic_token_index_write'] else 0}")
        print(f"  warnings: {len(self.warnings)}")

    def collection_diagnostics_payload(
        self,
        *,
        docs_total: int,
        docs_emitted: int,
        write_plan: dict[str, Any],
        elapsed_seconds: float,
    ) -> dict[str, Any]:
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
            "manifest_changed": 1 if write_plan["manifest_write"] else 0,
            "manage_manifest_changed": (
                1 if write_plan["manage_manifest_write"] else 0
            ),
            "subject_associations_changed": (
                1 if write_plan["subject_associations_write"] else 0
            ),
            "semantic_token_index_changed": 1 if write_plan["semantic_token_index_write"] else 0,
            "warning_count": len(self.warnings),
            "warnings": self.warnings,
            "elapsed_seconds": elapsed_seconds,
        }


def selected_collection(config: DocsStageConfig, collection_id: str) -> Any:
    for collection in config.collections:
        if collection.collection == collection_id:
            return collection
    raise RuntimeError(f"Unknown collection {collection_id!r} in stage {config.stage!r}")
