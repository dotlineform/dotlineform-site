#!/usr/bin/env python3
"""Synthetic DocsDataBuilder configuration for one validated review package."""

from __future__ import annotations

from collections.abc import Iterable
import html
import sys
from pathlib import Path
from typing import Any
from urllib.parse import quote

BUILD_DIR = Path(__file__).resolve().parents[1] / "build"
if str(BUILD_DIR) not in sys.path:
    sys.path.insert(0, str(BUILD_DIR))

from docs_builder.pipeline import DocsDataBuilder  # noqa: E402
from docs_artifact_locations import ArtifactLocation, EXTERNAL_LOCAL_PROVIDER  # noqa: E402
from docs_publication_paths import confined  # noqa: E402
from docs_workspace_config import (  # noqa: E402
    DocsGeneratedConfig,
    DocsMediaConfig,
    DocsArtifactConfig,
    DocsPreviewConfig,
    DocsStageConfig,
    DocsSourceConfig,
)


class DocsReviewDataBuilder(DocsDataBuilder):
    """Keep generated review URLs package-rooted instead of workspace-rooted."""

    def __init__(self, *, package_id: str, asset_records: list[dict[str, Any]], **kwargs: Any) -> None:
        self.package_id = package_id
        self.asset_records = asset_records
        super().__init__(**kwargs)

    def viewer_url_for(self, doc_id: str, anchor: str = "") -> str:
        url = f"/docs-review/?package={quote(self.package_id)}&doc={quote(str(doc_id))}"
        return f"{url}#{anchor}" if anchor else url

    def rendered_viewer_target_for(self, doc_id: str, anchor: str = "") -> str:
        return self.viewer_url_for(doc_id, anchor)

    def _asset_record(self, raw_path: str, *, kind: str) -> dict[str, Any] | None:
        target = str(raw_path or "").strip().lstrip("/")
        for record in self.asset_records:
            record_kind = str(record.get("kind") or "").strip().lower()
            if record_kind and record_kind != kind:
                continue
            candidates = {
                str(record.get(key) or "").strip().lstrip("/")
                for key in ("token_path", "source_path", "original_path")
            }
            if target in candidates:
                return record
        return None

    def _asset_url(self, package_path: str) -> str:
        encoded_path = "/".join(quote(part) for part in Path(package_path).parts)
        return f"/docs-review/packages/assets-content/{quote(self.package_id)}/{encoded_path}"

    def resolve_media_url(self, raw_path: str) -> str:
        relative_path = str(raw_path or "").strip()
        if not relative_path or "://" in relative_path:
            return super().resolve_media_url(relative_path)
        record = self._asset_record(relative_path, kind="media")
        if record is None:
            raise RuntimeError(f"Review package media asset is not inventoried: {relative_path}")
        return self._asset_url(str(record.get("package_path") or ""))

    def image_token_media_url(self, media_path: str) -> str | None:
        """Only a bundled Docs image has a URL in the Review reader."""
        record = self._asset_record(media_path, kind="media")
        return self._asset_url(record["package_path"]) if record is not None else None

    def html_media_iframe(self, raw_body: str) -> str:
        token = self.parse_html_media_token(raw_body)
        media_path = token["media_path"]
        filename = Path(token["identity"]).name
        record = self._asset_record(media_path, kind="interactive")
        if record is None:
            raise RuntimeError(f"Review package HTML media is not inventoried: {media_path}")
        title = f"Interactive HTML: {filename}"
        style_attr = f' style="--docs-viewer-interactive-height: {token["height"]}px"' if token.get("height") else ""
        return (
            f'<iframe class="docsViewer__interactiveFrame" '
            f'src="{html.escape(self._asset_url(str(record.get("package_path") or "")), quote=True)}" '
            f'sandbox="allow-scripts" loading="lazy" title="{html.escape(title, quote=True)}"{style_attr}></iframe>'
        )


def synthetic_review_config(
    *,
    source_dir: Path,
    generated_dir: Path,
    default_doc_id: str,
) -> DocsStageConfig:
    return DocsStageConfig(
        stage="review",
        workspace_root=ArtifactLocation(provider=EXTERNAL_LOCAL_PROVIDER, path=source_dir.parent),
        source=DocsSourceConfig(
            location=ArtifactLocation(provider=EXTERNAL_LOCAL_PROVIDER, path=source_dir),
            documents_path=Path("."),
            collections_path=Path("."),
        ),
        media=DocsMediaConfig(
            asset_location=ArtifactLocation(
                provider=EXTERNAL_LOCAL_PROVIDER,
                path=source_dir / "media",
            ),
            asset_root=ArtifactLocation(
                provider=EXTERNAL_LOCAL_PROVIDER,
                path=source_dir,
            ),
            types={},
        ),
        generated=DocsGeneratedConfig(
            documents=DocsArtifactConfig(
                location=ArtifactLocation(provider=EXTERNAL_LOCAL_PROVIDER, path=generated_dir)
            ),
            search=DocsArtifactConfig(
                location=ArtifactLocation(
                    provider=EXTERNAL_LOCAL_PROVIDER,
                    path=generated_dir / "search" / "index.json",
                )
            ),
        ),
        preview=DocsPreviewConfig(
            documents=DocsArtifactConfig(
                location=ArtifactLocation(provider=EXTERNAL_LOCAL_PROVIDER, path=generated_dir.parent / "preview")
            ),
            search=DocsArtifactConfig(
                location=ArtifactLocation(
                    provider=EXTERNAL_LOCAL_PROVIDER,
                    path=generated_dir.parent / "preview" / "search" / "index.json",
                )
            ),
        ),
        public_projection=None,
        default_doc_id=default_doc_id,
        allow_unresolved_parent_ids=False,
        collections=(),
        search_fields=(),
    )


def build_review_package(
    repo_root: Path,
    *,
    package_id: str,
    source_dir: Path,
    generated_dir: Path,
    default_doc_id: str,
    source_records: Iterable[dict[str, Any]],
    asset_records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Render the supplied package members and their tree from package-local source."""
    confined(generated_dir, "index-tree.json")
    config = synthetic_review_config(
        source_dir=source_dir,
        generated_dir=generated_dir,
        default_doc_id=default_doc_id,
    )
    builder = DocsReviewDataBuilder(
        repo_root=repo_root,
        config=config,
        source_dir=source_dir,
        output_dir=generated_dir,
        related_links_dir=generated_dir / "links-by-id",
        package_id=package_id,
        asset_records=asset_records,
        viewer_base_url="/docs-review/",
        skip_media_builds=True,
    )
    documents = []
    for record in source_records:
        doc_id = record["doc_id"]
        fields = record["front_matter"]
        documents.append(builder.document_record(
            path=source_dir / f"{doc_id}.md", front_matter=fields, body_markdown=record["source_body"],
            doc_id=doc_id, title=fields["title"], parent_id=fields.get("parent_id", ""), thumbnail=False,
        ))
    identities = {doc.doc_id: doc for doc in documents}
    result = builder.run(
        write=True, documents=documents, document_identities=identities,
        index_tree_payload=builder.index_tree_payload(identities, previous_payload=None),
        previous_tree_text=None, recent_payload=None, stale_item_ids=[], related_documents={},
    )
    diagnostics = result["diagnostics"]
    return {
        "document_count": len(documents),
        "asset_count": len(asset_records),
        "warnings": diagnostics["warnings"],
        "diagnostics": diagnostics,
    }
