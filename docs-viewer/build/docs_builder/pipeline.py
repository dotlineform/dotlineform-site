from __future__ import annotations

from pathlib import Path
from typing import Any

from .rendering_inputs import RenderingInputs
from .common import (
    DocsStageConfig,
    document_source_path,
    generated_documents_path,
    load_docs_workspace_config,
    monotonic_time,
    normalize_doc_ids,
    normalize_viewer_base_url,
    resolve_workspace_path,
)
from .payloads import PayloadBuilderMixin
from .rendering import ContentRenderingMixin
from .semantic_tokens import SemanticTokensMixin
from .source import DocRecord, SourceLoadingMixin
from .write_plan import WritePlanMixin
from docs_workspace_config import DocsWorkspaceConfig


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
        workspace: DocsWorkspaceConfig | None = None,
        rendering_inputs: RenderingInputs | None = None,
    ) -> None:
        self.repo_root = repo_root.resolve()
        self.config = config
        self.media_owner = getattr(self, "collection_config", config)
        self.workspace = load_docs_workspace_config(self.repo_root) if workspace is None else workspace
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
        rendering_inputs = RenderingInputs.load(self.repo_root) if rendering_inputs is None else rendering_inputs
        self.site_config = rendering_inputs.site_config
        self.semantic_token_registry = rendering_inputs.semantic_token_registry
        self.inline_icons = rendering_inputs.inline_icons
        self.rendering_inputs = rendering_inputs
        self._catalogue_work_cache: dict[str, dict[str, Any]] = {}
        self.related_links_dir = related_links_dir or generated_documents_path(config) / "links-by-id"
        self.source_files_scanned = 0
        self.warnings: list[str] = []

    def run(
        self, *, write: bool, documents: list[DocRecord],
        document_identities: dict[str, Any], index_tree_payload: dict[str, Any],
        recent_payload: dict[str, Any] | None, stale_item_ids: list[str],
        previous_tree_text: str | None,
        related_documents: dict[Any, Any],
        catalogue_works: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        """Render and write the supplied ordinary artifacts; return completed facts."""
        started_at = monotonic_time()
        self.related_documents = related_documents
        self._catalogue_work_cache = catalogue_works
        item_payloads = {doc.doc_id: self.item_entry(doc, document_identities) for doc in documents}
        write_plan = self.build_write_plan(
            index_tree_payload, recent_payload, item_payloads,
            stale_item_ids=stale_item_ids, existing_tree_text=previous_tree_text,
        )
        diagnostics = self.diagnostics_payload(
            docs_total=len(document_identities), docs_emitted=len(item_payloads), write_plan=write_plan,
            elapsed_seconds=round(monotonic_time() - started_at, 3),
            target_doc_ids=self.only_doc_ids if self.targeted_build else None,
        )
        summary = {
            "docs_total": len(document_identities), "tree_total": len(index_tree_payload["docs"]),
            "recent_total": len(recent_payload["docs"]) if recent_payload is not None else None,
        }
        if write:
            self.write_outputs(write_plan, **summary)
        else:
            self.print_human_summary(write_plan, mode="dry-run", **summary)
        diagnostics["warning_count"] = len(self.warnings)
        return {
            "index_tree_payload": index_tree_payload, "recent_payload": recent_payload,
            "item_payloads": item_payloads, "write_plan": write_plan, "diagnostics": diagnostics,
        }

    @property
    def targeted_build(self) -> bool:
        return self.only_doc_ids is not None
