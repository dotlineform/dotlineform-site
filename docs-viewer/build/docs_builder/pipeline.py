from __future__ import annotations

from pathlib import Path
from typing import Any

from .inline_icons import InlineIconRenderer
from .related_links import prepare_related_links
from .links_builder import build_document_links, prepare_document_links
from .common import (
    DocsStageConfig,
    document_source_path,
    generated_documents_path,
    load_docs_workspace_config,
    load_site_tools_config,
    monotonic_time,
    normalize_doc_ids,
    normalize_viewer_base_url,
    resolve_workspace_path,
)
from .media_builds import build_collection_media_snapshot
from .payloads import PayloadBuilderMixin
from .rendering import ContentRenderingMixin
from .semantic_token_registry import load_semantic_token_registry
from .semantic_tokens import SemanticTokensMixin
from .source import SourceLoadingMixin
from .ordinary_metadata import targeted_document_metadata
from .write_plan import WritePlanMixin
from docs_index_order import read_index_order, tree_parent_ids
from docs_selected_documents import read_selected, refresh_selected_documents, selected_path


class DocsDataBuilder(
    SourceLoadingMixin,
    PayloadBuilderMixin,
    ContentRenderingMixin,
    SemanticTokensMixin,
    WritePlanMixin,
):
    def __init__(
        self,
        *,
        repo_root: Path,
        config: DocsStageConfig,
        source_dir: Path | None = None,
        output_dir: Path | None = None,
        viewer_base_url: str | None = None,
        only_doc_ids: list[str] | None = None,
        links_doc_ids: list[str] | None = None,
        skip_media_builds: bool = False,
        skip_recent: bool = False,
        related_links_dir: Path | None = None,
    ) -> None:
        self.repo_root = repo_root.resolve()
        self.config = config
        self.media_owner = getattr(self, "collection_config", config)
        self.workspace = load_docs_workspace_config(self.repo_root)
        self.report_source_contract = None
        self.source_dir = resolve_workspace_path(self.repo_root, source_dir or document_source_path(config))
        self.output_dir = resolve_workspace_path(self.repo_root, output_dir or generated_documents_path(config))
        self.items_dir = self.output_dir / "by-id"
        self.viewer_base_url = normalize_viewer_base_url(viewer_base_url)
        self.allow_unresolved_parent_ids = config.allow_unresolved_parent_ids is True
        self.only_doc_ids = None if only_doc_ids is None else normalize_doc_ids(only_doc_ids)
        self.links_doc_ids = None if links_doc_ids is None else normalize_doc_ids(links_doc_ids)
        self.skip_media_builds = skip_media_builds is True
        self.skip_recent = skip_recent is True
        self.output_url_base = self.output_url_base_for(self.output_url_dir())
        self.site_config = load_site_tools_config(self.repo_root)
        self.semantic_token_registry = load_semantic_token_registry(self.repo_root)
        self.inline_icons = InlineIconRenderer(self.repo_root)
        self._catalogue_work_cache: dict[str, dict[str, Any]] = {}
        self.related_links_dir = related_links_dir or generated_documents_path(config) / "links-by-id"
        self.source_files_scanned = 0
        self.warnings: list[str] = []

    def run(self, *, write: bool, emit_diagnostics: bool = False) -> dict[str, Any]:
        started_at = monotonic_time()
        self.inline_icons = InlineIconRenderer(self.repo_root)
        self._catalogue_work_cache = {}
        parent_ids = tree_parent_ids(read_index_order(self.source_dir))
        source_ids = None if self.only_doc_ids is None else list(set(self.only_doc_ids) | set(self.links_doc_ids or []))
        capture_media_sources = self.targeted_build and not self.skip_media_builds
        docs = self.load_docs(source_ids, parent_ids=parent_ids, capture_source_text=capture_media_sources)
        self.validate_canonical_doc_ids(docs)
        self.validate_docs(docs, known_doc_ids=parent_ids)
        documents = docs
        previous_tree = None
        previous_tree_text = None
        if self.targeted_build:
            documents, previous_tree, previous_tree_text = targeted_document_metadata(self, docs, parent_ids)
        docs_by_id = {doc.doc_id: doc for doc in documents}
        read_selected(self.config)
        media_snapshot = (
            None
            if self.skip_media_builds
            else build_collection_media_snapshot(
                self.repo_root, self.media_owner, write=write,
                markdown_sources=[doc.source_text for doc in docs if doc.source_text is not None] if capture_media_sources else None,
            )
        )
        media_builds = [] if media_snapshot is None else media_snapshot["producer_builds"]
        target_doc_ids = self.only_doc_ids if self.only_doc_ids is not None else [doc.doc_id for doc in docs]
        target_set = set(target_doc_ids)
        docs_for_item_build = [doc for doc in docs if doc.doc_id in target_set]
        stale_item_ids = self.stale_doc_payload_ids(
            [doc.doc_id for doc in docs_for_item_build],
            target_doc_ids=target_doc_ids if self.targeted_build else None,
        )
        links_plan = prepare_document_links(
            self, docs, target_doc_ids, stale_item_ids, document_identities=docs_by_id,
        )
        related_records = {}
        links_build = build_document_links(self, links_plan, write=write, related_records=related_records)
        prepare_related_links(self, docs_for_item_build, related_records)

        item_payloads = {
            doc.doc_id: self.item_entry(
                doc,
                docs_by_id,
            )
            for doc in docs_for_item_build
        }

        index_tree_payload = self.index_tree_payload(docs_by_id, previous_payload=previous_tree)
        # Preview, targeted builds and authoring follow-through preserve saved Recents.
        recent_payload = None
        if self.config.stage == "working" and not self.targeted_build and not self.skip_recent:
            recent_candidates = self.recent_candidates(docs, index_tree_payload["docs"])
            recent_payload = self.recent_payload(
                recent_candidates,
                output_path=self.output_dir / "recent.json",
            )
        write_plan = self.build_write_plan(
            index_tree_payload,
            recent_payload,
            item_payloads,
            stale_item_ids=stale_item_ids,
            existing_tree_text=previous_tree_text,
        )
        diagnostics = self.diagnostics_payload(
            docs_total=len(documents),
            docs_emitted=len(item_payloads),
            write_plan=write_plan,
            elapsed_seconds=round(monotonic_time() - started_at, 3),
            target_doc_ids=target_doc_ids if self.targeted_build else None,
        )
        if write:
            self.write_outputs(
                write_plan,
                docs_total=len(documents),
                tree_total=len(index_tree_payload["docs"]),
                recent_total=len(recent_payload["docs"]) if recent_payload is not None else None,
            )
        else:
            self.print_human_summary(
                write_plan,
                mode="dry-run",
                docs_total=len(documents),
                tree_total=len(index_tree_payload["docs"]),
                recent_total=len(recent_payload["docs"]) if recent_payload is not None else None,
            )
        if self.config.stage == "working":
            refresh_selected_documents(self.config, self.config, docs_for_item_build, write=write)
        elif write:
            (self.output_dir / "selected.json").write_bytes(selected_path(self.config).read_bytes())
        diagnostics["warning_count"] = len(self.warnings)
        if emit_diagnostics:
            self.print_diagnostics(diagnostics)
        return {
            "index_tree_payload": index_tree_payload,
            "recent_payload": recent_payload,
            "item_payloads": item_payloads,
            "write_plan": write_plan,
            "diagnostics": diagnostics,
            "media_builds": media_builds,
            "media_snapshot": media_snapshot,
            "links_build": links_build,
        }

    @property
    def targeted_build(self) -> bool:
        return self.only_doc_ids is not None
