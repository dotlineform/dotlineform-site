from __future__ import annotations

from pathlib import Path
from typing import Any

from .common import (
    DocsScopeConfig,
    document_source_path,
    is_public_readonly_scope,
    load_site_tools_config,
    monotonic_time,
    normalize_doc_ids,
    normalize_viewer_base_url,
    published_documents_path,
    resolve_scope_path,
    utc_timestamp,
)
from .media_builds import referenced_build_media_identities, run_registered_media_builds
from .payloads import PayloadBuilderMixin
from .recent_policy import recent_basis_for_route
from .rendering import ContentRenderingMixin
from .semantic_token_artifacts import SemanticTokenArtifactsMixin
from .semantic_token_registry import load_semantic_token_registry
from .semantic_tokens import SemanticTokensMixin, load_semantic_token_targets
from .source import SourceLoadingMixin
from .write_plan import WritePlanMixin


class DocsDataBuilder(
    SourceLoadingMixin,
    PayloadBuilderMixin,
    ContentRenderingMixin,
    SemanticTokensMixin,
    SemanticTokenArtifactsMixin,
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
        skip_media_builds: bool = False,
    ) -> None:
        self.repo_root = repo_root.resolve()
        self.config = config
        self.scope_id = config.scope_id
        self.report_source_contract = None
        self.source_dir = resolve_scope_path(self.repo_root, source_dir or document_source_path(config))
        self.output_dir = resolve_scope_path(self.repo_root, output_dir or published_documents_path(config))
        self.items_dir = self.output_dir / "by-id"
        self.viewer_base_url = normalize_viewer_base_url(viewer_base_url or config.viewer_base_url)
        self.include_scope_param = config.include_scope_param
        self.non_loadable_doc_ids = normalize_doc_ids(list(config.non_loadable_doc_ids))
        self.manage_only_tree_root_ids = normalize_doc_ids(list(config.manage_only_tree_root_ids))
        self.allow_unresolved_parent_ids = config.allow_unresolved_parent_ids is True
        self.only_doc_ids = None if only_doc_ids is None else normalize_doc_ids(only_doc_ids)
        self.skip_media_builds = skip_media_builds is True
        self.output_url_base = self.output_url_base_for(self.output_url_dir())
        self.site_config = load_site_tools_config(self.repo_root)
        self.semantic_token_registry = load_semantic_token_registry(self.repo_root)
        self.semantic_token_targets_by_key = load_semantic_token_targets(self.repo_root)
        self.source_files_scanned = 0
        self.warnings: list[str] = []
        self._viewer_scope_for_path: dict[str, str] | None = None

    def run(self, *, write: bool, emit_diagnostics: bool = False) -> dict[str, Any]:
        started_at = monotonic_time()
        media_builds = (
            []
            if self.targeted_build or self.skip_media_builds
            else run_registered_media_builds(self.repo_root, self.config, write=write)
        )
        docs = self.load_docs()
        self.validate_canonical_doc_ids(docs)
        self.validate_docs(docs)
        target_doc_ids = self.only_doc_ids if self.only_doc_ids is not None else [doc.doc_id for doc in docs]
        if self.targeted_build:
            self.validate_targeted_build_prerequisites(docs, target_doc_ids)
            semantic_tokens_by_doc = self.existing_semantic_token_occurrences_by_doc(
                docs,
                target_doc_ids,
            )
        else:
            semantic_tokens_by_doc: dict[str, list[dict[str, Any]]] = {}

        docs_for_item_build = [doc for doc in docs if doc.doc_id in target_doc_ids]
        if self.targeted_build and not self.skip_media_builds:
            requested_media = referenced_build_media_identities(
                self.config,
                (doc.body_markdown for doc in docs_for_item_build),
            )
            media_builds = run_registered_media_builds(
                self.repo_root,
                self.config,
                write=write,
                requested_published_identities=requested_media,
            )
        item_payloads = {
            doc.doc_id: self.item_entry(
                doc,
                docs,
                semantic_tokens_by_doc,
            )
            for doc in docs_for_item_build
        }
        for doc in docs_for_item_build:
            semantic_tokens_by_doc.setdefault(doc.doc_id, [])

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
        recent_basis = recent_basis_for_route(self.repo_root, app_kind="manage")
        recent_payload = self.recent_payload(
            docs,
            basis=recent_basis,
            output_path=self.output_dir / "recent.json",
        )
        public_recent_basis = recent_basis_for_route(
            self.repo_root,
            app_kind="public",
            scope=self.scope_id,
        )
        publication_recent_payload = (
            self.recent_payload(
                self.public_recent_docs(docs),
                basis=public_recent_basis,
                output_path=self.output_dir / ".publish/recent.json",
            )
            if public_recent_basis
            else None
        )
        semantic_token_payloads = self.build_semantic_token_payloads(docs, semantic_tokens_by_doc)
        write_plan = self.build_write_plan(
            index_tree_payload,
            recent_payload,
            publication_recent_payload,
            item_payloads,
            semantic_token_payloads,
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
                recent_total=len(recent_payload["docs"]),
                semantic_token_total=len(semantic_token_payloads["index"]["occurrences"]),
            )
        else:
            self.print_dry_run(
                index_payload,
                index_tree_payload,
                recent_payload,
                semantic_token_payloads,
                write_plan,
            )
        if emit_diagnostics:
            self.print_diagnostics(diagnostics)
        return {
            "index_payload": index_payload,
            "index_tree_payload": index_tree_payload,
            "recent_payload": recent_payload,
            "publication_recent_payload": publication_recent_payload,
            "item_payloads": item_payloads,
            "semantic_token_payloads": semantic_token_payloads,
            "write_plan": write_plan,
            "diagnostics": diagnostics,
            "media_builds": media_builds,
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
    def publishable_supported(self) -> bool:
        document_config = getattr(self, "sub_scope_config", self.config)
        return document_config.public_projection is not None

    @property
    def public_readonly_scope(self) -> bool:
        return is_public_readonly_scope(
            viewer_base_url=self.viewer_base_url,
            include_scope_param=self.include_scope_param,
        )
