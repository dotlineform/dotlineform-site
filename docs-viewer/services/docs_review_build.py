#!/usr/bin/env python3
"""Synthetic DocsDataBuilder configuration for one validated review package."""

from __future__ import annotations

import html
import sys
from pathlib import Path
from typing import Any
from urllib.parse import quote

BUILD_DIR = Path(__file__).resolve().parents[1] / "build"
if str(BUILD_DIR) not in sys.path:
    sys.path.insert(0, str(BUILD_DIR))

from docs_builder.pipeline import DocsDataBuilder  # noqa: E402
from docs_builder.source import DocRecord  # noqa: E402
from docs_scope_config import (  # noqa: E402
    LOCAL_EXTERNAL_SCOPE_TYPE,
    DocsImportMediaConfig,
    DocsScopeConfig,
)


class DocsReviewDataBuilder(DocsDataBuilder):
    """Keep generated review URLs package-rooted instead of scope-rooted."""

    def __init__(self, *, package_id: str, asset_records: list[dict[str, Any]], **kwargs: Any) -> None:
        self.package_id = package_id
        self.asset_records = asset_records
        super().__init__(**kwargs)

    @property
    def public_readonly_scope(self) -> bool:
        return False

    def validate_canonical_doc_ids(self, docs: list[DocRecord]) -> None:
        # Review documents retain package record identity until Docs Import maps
        # a create to a new local identity or an overwrite to an existing one.
        return None

    def viewer_url_for(self, doc_id: str, anchor: str = "") -> str:
        url = f"/docs-review/?package={quote(self.package_id)}&doc={quote(str(doc_id))}"
        return f"{url}#{anchor}" if anchor else url

    def content_url_for(self, doc_id: str) -> str:
        return (
            f"/docs-review/packages/payload?package_id={quote(self.package_id)}"
            f"&doc_id={quote(str(doc_id))}"
        )

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

    def interactive_html_iframe(self, raw_body: str) -> str:
        token = self.parse_interactive_html_token(raw_body)
        filename = token["filename"]
        record = self._asset_record(filename, kind="interactive")
        if record is None:
            raise RuntimeError(f"Review package interactive asset is not inventoried: {filename}")
        title = f"Interactive HTML: {filename}"
        style_attr = f' style="--docs-viewer-interactive-height: {token["height"]}px"' if token.get("height") else ""
        return (
            f'<iframe class="docsViewer__interactiveFrame" '
            f'src="{html.escape(self._asset_url(str(record.get("package_path") or "")), quote=True)}" '
            f'sandbox="allow-scripts" loading="lazy" title="{html.escape(title, quote=True)}"{style_attr}></iframe>'
        )


def synthetic_review_config(
    *,
    package_id: str,
    source_dir: Path,
    generated_dir: Path,
    default_doc_id: str,
) -> DocsScopeConfig:
    return DocsScopeConfig(
        scope_id=package_id,
        scope_type=LOCAL_EXTERNAL_SCOPE_TYPE,
        source=source_dir,
        media_path_prefix=Path("assets/media"),
        output=generated_dir,
        search_output=generated_dir / "search" / "index.json",
        publish_output=generated_dir,
        publish_search_output=generated_dir / "search" / "index.json",
        viewer_base_url="/docs-review/",
        include_scope_param=False,
        default_doc_id=default_doc_id,
        non_loadable_doc_ids=(),
        manage_only_tree_root_ids=(),
        allow_unresolved_parent_ids=False,
        import_media_storage=DocsImportMediaConfig(
            storage_mode="staging_manual",
            media_path_prefix=Path("assets/media"),
            repo_assets_path_prefix=Path("assets/media"),
            repo_assets_public_path_prefix="/docs-review/assets/media",
        ),
        sub_scopes=(),
    )


def build_review_package(
    repo_root: Path,
    *,
    package_id: str,
    source_dir: Path,
    generated_dir: Path,
    default_doc_id: str,
    asset_records: list[dict[str, Any]],
) -> dict[str, Any]:
    config = synthetic_review_config(
        package_id=package_id,
        source_dir=source_dir,
        generated_dir=generated_dir,
        default_doc_id=default_doc_id,
    )
    result = DocsReviewDataBuilder(
        repo_root=repo_root,
        config=config,
        package_id=package_id,
        asset_records=asset_records,
    ).run(write=True)
    diagnostics = result.get("diagnostics") if isinstance(result.get("diagnostics"), dict) else {}
    return {
        "document_count": len(result.get("item_payloads") or {}),
        "asset_count": len(asset_records),
        "warnings": list(diagnostics.get("warnings") or []),
        "diagnostics": diagnostics,
    }
