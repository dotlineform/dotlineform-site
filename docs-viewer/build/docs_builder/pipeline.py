from __future__ import annotations

from pathlib import Path
from typing import Any

from .common import (
    DocsScopeConfig,
    is_public_readonly_scope,
    load_site_tools_config,
    monotonic_time,
    normalize_doc_ids,
    normalize_viewer_base_url,
    resolve_scope_path,
    utc_timestamp,
)
from .payloads import PayloadBuilderMixin
from .reference_artifacts import ReferenceArtifactsMixin
from .rendering import ContentRenderingMixin
from .semantic_registry import load_semantic_reference_registry
from .semantic_references import SemanticReferencesMixin
from .source import SourceLoadingMixin
from .write_plan import WritePlanMixin


class DocsDataBuilder(
    SourceLoadingMixin,
    PayloadBuilderMixin,
    ContentRenderingMixin,
    SemanticReferencesMixin,
    ReferenceArtifactsMixin,
    WritePlanMixin,
):
    def __init__(
        self,
        *,
        repo_root: Path,
        config: DocsScopeConfig,
        source_dir: Path | None = None,
        output_dir: Path | None = None,
        viewer_base_url: str | None = None,
        only_doc_ids: list[str] | None = None,
    ) -> None:
        self.repo_root = repo_root.resolve()
        self.config = config
        self.scope_id = config.scope_id
        self.source_dir = resolve_scope_path(self.repo_root, source_dir or config.source)
        self.output_dir = resolve_scope_path(self.repo_root, output_dir or config.output)
        self.items_dir = self.output_dir / "by-id"
        self.viewer_base_url = normalize_viewer_base_url(viewer_base_url or config.viewer_base_url)
        self.include_scope_param = config.include_scope_param
        self.non_loadable_doc_ids = normalize_doc_ids(list(config.non_loadable_doc_ids))
        self.manage_only_tree_root_ids = normalize_doc_ids(list(config.manage_only_tree_root_ids))
        self.allow_unresolved_parent_ids = config.allow_unresolved_parent_ids is True
        self.only_doc_ids = None if only_doc_ids is None else normalize_doc_ids(only_doc_ids)
        self.output_url_base = self.output_url_base_for(self.output_url_dir())
        self.site_config = load_site_tools_config(self.repo_root)
        self.semantic_reference_registry = load_semantic_reference_registry(self.repo_root)
        self.source_files_scanned = 0
        self.warnings: list[str] = []
        self._viewer_scope_for_path: dict[str, str] | None = None

    def run(self, *, write: bool, emit_diagnostics: bool = False) -> dict[str, Any]:
        started_at = monotonic_time()
        docs = self.load_docs()
        self.validate_canonical_doc_ids(docs)
        self.validate_docs(docs)
        target_doc_ids = self.only_doc_ids if self.only_doc_ids is not None else [doc.doc_id for doc in docs]
        if self.targeted_build:
            self.validate_targeted_build_prerequisites(docs, target_doc_ids)
            semantic_references_by_doc = self.existing_reference_records_by_doc(docs, target_doc_ids)
        else:
            semantic_references_by_doc: dict[str, list[dict[str, Any]]] = {}

        docs_for_item_build = [doc for doc in docs if doc.doc_id in target_doc_ids]
        item_payloads = {
            doc.doc_id: self.item_entry(doc, docs, semantic_references_by_doc) for doc in docs_for_item_build
        }
        for doc in docs_for_item_build:
            semantic_references_by_doc.setdefault(doc.doc_id, [])

        flat_doc_rows = [
            self.index_entry(doc, docs, item_payloads.get(doc.doc_id)) for doc in self.ordered_docs_for_index(docs)
        ]
        viewer_options = self.viewer_options_payload()
        index_payload = {
            "generated_at": utc_timestamp(),
            "viewer_options": viewer_options,
            "docs": flat_doc_rows,
        }
        index_tree_payload = self.index_tree_payload(docs, viewer_options)
        recently_added_payload = self.recently_added_payload(docs)
        reference_payloads = self.build_reference_payloads(docs, semantic_references_by_doc)
        write_plan = self.build_write_plan(
            index_tree_payload,
            recently_added_payload,
            item_payloads,
            reference_payloads,
            target_doc_ids=target_doc_ids if self.targeted_build else None,
        )
        diagnostics = self.diagnostics_payload(
            docs=docs,
            write_plan=write_plan,
            elapsed_seconds=round(monotonic_time() - started_at, 3),
            target_doc_ids=target_doc_ids if self.targeted_build else None,
        )
        if write:
            self.write_outputs(
                write_plan,
                docs_total=len(index_payload["docs"]),
                tree_total=len(index_tree_payload["docs"]),
                recently_added_total=len(recently_added_payload["docs"]),
                reference_total=reference_payloads["index"]["header"]["count"],
            )
        else:
            self.print_dry_run(index_payload, index_tree_payload, recently_added_payload, reference_payloads, write_plan)
        if emit_diagnostics:
            self.print_diagnostics(diagnostics)
        return {
            "index_payload": index_payload,
            "index_tree_payload": index_tree_payload,
            "recently_added_payload": recently_added_payload,
            "item_payloads": item_payloads,
            "reference_payloads": reference_payloads,
            "write_plan": write_plan,
            "diagnostics": diagnostics,
        }

    @property
    def targeted_build(self) -> bool:
        return self.only_doc_ids is not None

    def viewer_options_payload(self) -> dict[str, Any]:
        return {
            "non_loadable_doc_ids": self.non_loadable_doc_ids,
            "manage_only_tree_root_ids": self.manage_only_tree_root_ids,
        }

    @property
    def public_readonly_scope(self) -> bool:
        return is_public_readonly_scope(
            viewer_base_url=self.viewer_base_url,
            include_scope_param=self.include_scope_param,
        )
