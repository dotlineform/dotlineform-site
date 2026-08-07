from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import quote

from .common import (
    DocsScopeConfig,
    document_source_path,
    json_text,
    monotonic_time,
    read_text,
    publication_documents_path,
    published_documents_path,
    resolve_scope_path,
    write_text,
)
from .pipeline import DocsDataBuilder
from .source import DocRecord
from docs_subscope_customisations import (
    project_sub_scope_customisation_manifest,
    sub_scope_customisation_authoring_subject_fields,
    sub_scope_customisation_document_groups,
    validate_sub_scope_customisation_document,
)
from docs_document_subjects import (
    AUTHORING_SUBJECT_FIELDS,
    FOLDER_PATH_FIELD,
    normalize_authoring_subject,
    project_subject_associations,
    subject_projection_generation,
)


class SubScopeDocsBuilder(DocsDataBuilder):
    def __init__(
        self,
        *,
        repo_root: Path,
        config: DocsScopeConfig,
        sub_scope: Any,
    ) -> None:
        self.sub_scope_config = sub_scope
        super().__init__(
            repo_root=repo_root,
            config=config,
            source_dir=document_source_path(sub_scope),
            output_dir=published_documents_path(sub_scope),
        )
        self.sub_scope_id = sub_scope.sub_scope
        self.output_url_base = self.output_url_base_for(self.output_url_dir())
        self._parent_report_doc_id: str | None = None

    def output_url_dir(self) -> Path:
        output = (
            publication_documents_path(self.sub_scope_config)
            if self.public_readonly_scope
            else published_documents_path(self.sub_scope_config)
        )
        return resolve_scope_path(self.repo_root, output)

    def parent_report_doc_id(self) -> str:
        if self._parent_report_doc_id is not None:
            return self._parent_report_doc_id
        parent_builder = DocsDataBuilder(repo_root=self.repo_root, config=self.config)
        parent_docs = parent_builder.load_docs()
        parent_builder.validate_canonical_doc_ids(parent_docs)
        matching = [
            doc.doc_id for doc in parent_docs
            if (
                doc.viewer_report == "docs_subscope"
                and doc.viewer_report_subscope == self.sub_scope_id
            )
        ]
        if len(matching) == 1:
            self._parent_report_doc_id = matching[0]
        else:
            if len(matching) > 1:
                self.warnings.append(
                    "Sub-scope detail links are ambiguous for "
                    f"{self.scope_id}/{self.sub_scope_id}; matching parent reports: {', '.join(sorted(matching))}"
                )
            self._parent_report_doc_id = ""
        return self._parent_report_doc_id

    def viewer_url_for(self, doc_id: str, anchor: str = "") -> str:
        parent_doc_id = self.parent_report_doc_id()
        if not parent_doc_id:
            return super().viewer_url_for(doc_id, anchor)
        pairs: list[str] = []
        if self.include_scope_param and self.scope_id:
            pairs.append(f"scope={quote(self.scope_id)}")
        pairs.append(f"doc={quote(parent_doc_id)}")
        pairs.append(f"subdoc={quote(str(doc_id))}")
        url = f"{self.viewer_base_url}?{'&'.join(pairs)}"
        return f"{url}#{anchor}" if anchor else url

    def by_id_metadata_entry(self, doc: DocRecord, docs: list[DocRecord]) -> dict[str, Any]:
        return self.metadata_entry(doc, docs)

    def manifest_payload(self, ordered_docs: list[DocRecord]) -> dict[str, Any]:
        visible_docs = [doc for doc in ordered_docs if doc.viewable]
        payload: dict[str, Any] = {
            "docs": [
                {
                    "doc_id": doc.doc_id,
                    "title": doc.title,
                }
                for doc in visible_docs
            ]
        }
        projected = project_sub_scope_customisation_manifest(
            self.sub_scope_config.sub_scope_customisation,
            visible_docs,
            published=True,
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
        payload: dict[str, Any] = {
            "docs": [
                {
                    "doc_id": doc.doc_id,
                    "title": doc.title,
                    "ui_status": doc.ui_status,
                    "viewable": doc.viewable,
                    "last_updated": doc.last_updated,
                }
                for doc in ordered_docs
            ]
        }
        if subjects_by_doc_id is not None:
            payload["subject_generation"] = subject_generation
            for row in payload["docs"]:
                row["authoring_subject"] = subjects_by_doc_id[row["doc_id"]]
        projected = project_sub_scope_customisation_manifest(
            self.sub_scope_config.sub_scope_customisation,
            ordered_docs,
            published=False,
        )
        if projected is not None:
            payload["customisation"] = projected["root"]
            rows_by_id = projected["rows"]
            unknown_ids = sorted(set(rows_by_id) - {doc.doc_id for doc in ordered_docs})
            if unknown_ids:
                raise RuntimeError(
                    "Docs sub-scope customisation projected unknown document IDs: "
                    + ", ".join(unknown_ids)
                )
            for row in payload["docs"]:
                row_customisation = rows_by_id.get(row["doc_id"])
                if row_customisation is not None:
                    if "customisation" in row:
                        raise RuntimeError(
                            "Docs sub-scope customisation row namespace collision: "
                            + row["doc_id"]
                        )
                    row["customisation"] = row_customisation
        return payload

    def folder_subject_supported(self) -> bool:
        return FOLDER_PATH_FIELD in sub_scope_customisation_authoring_subject_fields(
            self.sub_scope_config.sub_scope_customisation
        )

    def private_authoring_subjects(
        self,
        ordered_docs: list[DocRecord],
    ) -> dict[str, dict[str, Any]] | None:
        if self.public_readonly_scope:
            return None
        folder_supported = self.folder_subject_supported()
        if not folder_supported and not any(
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

    def validate_docs(self, docs: list[DocRecord]) -> None:
        super().validate_docs(docs)
        allowed_statuses = set(self.sub_scope_config.ui_statuses)
        allowed_groups = set(
            sub_scope_customisation_document_groups(
                self.sub_scope_config.sub_scope_customisation
            )
        )
        for doc in docs:
            if doc.ui_status and doc.ui_status not in allowed_statuses:
                raise RuntimeError(
                    f"Unknown ui_status {doc.ui_status!r} for "
                    f"{self.scope_id}/{self.sub_scope_id} doc {doc.doc_id!r}"
                )
            if doc.group and not allowed_groups:
                raise RuntimeError(
                    f"group is not configured for "
                    f"{self.scope_id}/{self.sub_scope_id} doc {doc.doc_id!r}"
                )
            if doc.group and doc.group not in allowed_groups:
                raise RuntimeError(
                    f"Unknown group {doc.group!r} for "
                    f"{self.scope_id}/{self.sub_scope_id} doc {doc.doc_id!r}"
                )
            validate_sub_scope_customisation_document(
                self.sub_scope_config.sub_scope_customisation,
                doc.front_matter,
                doc_id=doc.doc_id,
            )

    def run(self, *, write: bool, emit_diagnostics: bool = False) -> dict[str, Any]:
        started_at = monotonic_time()
        docs = self.load_docs()
        self.validate_canonical_doc_ids(docs)
        self.validate_docs(docs)
        ordered_docs = sorted(docs, key=self.doc_sort_key)
        semantic_tokens_by_doc: dict[str, list[dict[str, Any]]] = {}
        item_payloads = {
            doc.doc_id: self.item_entry(
                doc,
                docs,
                semantic_tokens_by_doc,
            )
            for doc in ordered_docs
        }
        manifest_payload = self.manifest_payload(ordered_docs)
        subjects_by_doc_id = self.private_authoring_subjects(ordered_docs)
        subject_generation = ""
        subject_associations_payload: dict[str, Any] | None = None
        if subjects_by_doc_id is not None:
            subject_generation = subject_projection_generation(
                scope=self.scope_id,
                sub_scope=self.sub_scope_id,
                subjects_by_doc_id=subjects_by_doc_id,
            )
            subject_associations_payload = project_subject_associations(
                scope=self.scope_id,
                sub_scope=self.sub_scope_id,
                documents=ordered_docs,
                subjects_by_doc_id=subjects_by_doc_id,
                subject_generation=subject_generation,
            )
        manage_manifest_payload = self.manage_manifest_payload(
            ordered_docs,
            subjects_by_doc_id=subjects_by_doc_id,
            subject_generation=subject_generation,
        )
        write_plan = self.build_sub_scope_write_plan(
            manifest_payload,
            manage_manifest_payload,
            subject_associations_payload,
            item_payloads,
        )
        diagnostics = self.sub_scope_diagnostics_payload(
            docs=docs,
            write_plan=write_plan,
            elapsed_seconds=round(monotonic_time() - started_at, 3),
        )
        if write:
            self.write_sub_scope_outputs(write_plan, docs_total=len(docs))
        else:
            self.print_sub_scope_summary(write_plan, mode="dry-run", docs_total=len(docs))
        if emit_diagnostics:
            self.print_diagnostics(diagnostics)
        return {
            "manifest_payload": manifest_payload,
            "manage_manifest_payload": manage_manifest_payload,
            "subject_associations_payload": subject_associations_payload,
            "item_payloads": item_payloads,
            "write_plan": write_plan,
            "diagnostics": diagnostics,
        }

    def build_sub_scope_write_plan(
        self,
        manifest_payload: dict[str, Any],
        manage_manifest_payload: dict[str, Any],
        subject_associations_payload: dict[str, Any] | None,
        item_payloads: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
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
        existing_item_ids = self.existing_doc_payload_ids(self.items_dir)
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
            "stale_item_ids": sorted(set(existing_item_ids) - set(item_payloads)),
            "item_text_by_id": item_text_by_id,
        }

    def write_sub_scope_outputs(self, write_plan: dict[str, Any], *, docs_total: int) -> None:
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
        self.print_sub_scope_summary(write_plan, mode="write", docs_total=docs_total)

    def print_sub_scope_summary(self, write_plan: dict[str, Any], *, mode: str, docs_total: int) -> None:
        verb = "would write" if mode == "dry-run" else "wrote"
        remove_verb = "would remove" if mode == "dry-run" else "removed"
        print(f"Docs sub-scope build ({mode}) scope={self.scope_id} sub_scope={self.sub_scope_id}")
        print(f"  docs total: {docs_total}")
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
        print(f"  warnings: {len(self.warnings)}")

    def sub_scope_diagnostics_payload(
        self,
        *,
        docs: list[DocRecord],
        write_plan: dict[str, Any],
        elapsed_seconds: float,
    ) -> dict[str, Any]:
        return {
            "scope": self.scope_id,
            "sub_scope": self.sub_scope_id,
            "build_mode": "sub_scope",
            "source_files_scanned": self.source_files_scanned,
            "docs_emitted": len(docs),
            "doc_payloads_changed": len(write_plan["changed_item_ids"]),
            "doc_payloads_removed": len(write_plan["stale_item_ids"]),
            "manifest_changed": 1 if write_plan["manifest_write"] else 0,
            "manage_manifest_changed": (
                1 if write_plan["manage_manifest_write"] else 0
            ),
            "subject_associations_changed": (
                1 if write_plan["subject_associations_write"] else 0
            ),
            "warning_count": len(self.warnings),
            "warnings": self.warnings,
            "elapsed_seconds": elapsed_seconds,
        }


def selected_sub_scope(config: DocsScopeConfig, sub_scope_id: str) -> Any:
    for sub_scope in config.sub_scopes:
        if sub_scope.sub_scope == sub_scope_id:
            return sub_scope
    raise RuntimeError(f"Unknown sub-scope {sub_scope_id!r} for scope {config.scope_id!r}")
