#!/usr/bin/env python3
"""Sandboxed HTML media handling for staged Docs source imports."""

from __future__ import annotations


import re
import tempfile
from pathlib import Path
from typing import Any, Dict

from docs_artifact_locations import (
    ArtifactLocationAdapter,
    artifact_location_adapter,
    authenticated_remote_client_for_locations,
    normalize_artifact_identity,
)
from docs_import_common import HTML_STAGED_SUFFIXES, is_interactive_html_import_asset
from docs_media_storage import docs_media_file, docs_publish_succeeded, publish_docs_media_files
from docs_workspace_config import DocsStageConfig, DocsCollectionConfig, DocsManagedMediaConfig, managed_media_config
from docs_source_model import slugify
from studio.shared.python.projects_directories import projects_path_marker

INTERACTIVE_HTML_FILENAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*\.html$")


def _html_media_adapter(repo_root: Path, config: DocsStageConfig | DocsCollectionConfig):
    media = managed_media_config(config, "html")
    remote_client = authenticated_remote_client_for_locations(repo_root, [media.asset_location])
    return media, artifact_location_adapter(
        repo_root,
        media.asset_location,
        served_path_prefix=media.served_path_prefix,
        remote_client=remote_client,
    )

def interactive_html_staged_paths(staging_root: Path) -> list[Path]:
    staging_root = staging_root.resolve()
    if not staging_root.exists():
        return []
    return [
        path
        for path in sorted(staging_root.iterdir(), key=lambda candidate: candidate.name.lower())
        if path.is_file()
        and not path.is_symlink()
        and path.suffix.lower() in HTML_STAGED_SUFFIXES
        and is_interactive_html_import_asset(path)
    ]


def interactive_html_asset_plan_for_path(
    workspace_root: Path,
    source_path: Path,
    *,
    collection: str = "",
    doc_id: str,
    media: DocsManagedMediaConfig,
    adapter: ArtifactLocationAdapter,
) -> Dict[str, Any]:
    filename = f"{slugify(source_path.stem)}.html"
    if not INTERACTIVE_HTML_FILENAME_PATTERN.fullmatch(filename):
        raise ValueError(f"Interactive HTML asset filename must be a simple slug ending in .html: {filename}")
    identity = f"{doc_id}/{filename}"

    media_path = f"{media.reference_prefix.as_posix()}/{identity}"

    return {
        "collection": collection,
        "source_path": projects_path_marker(source_path, workspace_root),
        "target_path": media_path,
        "public_path": adapter.served_reference(identity),
        "token": f"[[html-media:{media_path}]]",
        "filename": identity,
        "staged_filename": source_path.name,
        "display_name": Path(filename).stem,
        "result_type": "script file",
        "target_exists": adapter.stat(identity) is not None,
    }


def interactive_html_asset_plans(
    repo_root: Path,
    staging_root: Path,
    workspace_root: Path,
    *,
    config: DocsStageConfig | DocsCollectionConfig,
    doc_id: str,
) -> list[Dict[str, Any]]:
    paths = interactive_html_staged_paths(staging_root)
    if not paths:
        return []
    media, adapter = _html_media_adapter(repo_root, config)
    plans = [
        interactive_html_asset_plan_for_path(
            workspace_root, path, collection=getattr(config, "collection", ""),
            doc_id=doc_id, media=media, adapter=adapter,
        )
        for path in paths
    ]
    target_paths: set[str] = set()
    for plan in plans:
        target_path = str(plan.get("target_path") or "")
        if target_path in target_paths:
            raise ValueError(f"Multiple interactive HTML staged files resolve to {target_path}.")
        target_paths.add(target_path)
    return plans


def ensure_interactive_html_targets_available(plans: list[Dict[str, Any]], *, allow_overwrite: bool = False) -> None:
    for plan in plans:
        if plan.get("target_exists") and not allow_overwrite:
            raise FileExistsError(
                f"Interactive HTML asset already exists: {plan.get('target_path')}. "
                "Edit that asset directly or confirm overwrite to replace it during import."
            )


def materialize_interactive_html_asset(
    repo_root: Path,
    staging_root: Path,
    plan: Dict[str, Any],
    *,
    config: DocsStageConfig | DocsCollectionConfig,
    allow_overwrite: bool = False,
) -> Dict[str, Any]:
    staged_filename = str(plan.get("staged_filename") or "").strip()
    if not staged_filename or Path(staged_filename).name != staged_filename:
        raise ValueError("Interactive HTML asset plan has an invalid staged filename.")
    staged_path = staging_root / staged_filename
    if staged_path.is_symlink():
        raise ValueError("Interactive HTML asset source must not be a symlink.")
    source_path = staged_path.resolve()
    staging_root = staging_root.resolve()
    if not source_path.is_relative_to(staging_root):
        raise ValueError("Interactive HTML asset source escapes import staging root.")
    if "scope" in plan:
        raise ValueError("scope-bearing import plans are retired; recreate the preview")
    target_filename = normalize_artifact_identity(plan["filename"])
    with tempfile.TemporaryDirectory(prefix="docs-html-media-") as temp_dir:
        publication_root = Path(temp_dir)
        publication_path = publication_root / target_filename
        publication_path.parent.mkdir(parents=True, exist_ok=True)
        publication_path.write_bytes(source_path.read_bytes())
        item = docs_media_file(
            config,
            media_class="html",
            local_path=publication_path,
            source_root=publication_root,
            filename=target_filename,
        )
        results = publish_docs_media_files(
            repo_root,
            [item],
            config=config,
            write=True,
            force=allow_overwrite,
        )
    if not docs_publish_succeeded(results):
        status = results[0].status if results else "not_attempted"
        raise RuntimeError(f"HTML media publication did not complete: {status}")
    return {
        "source_path": str(plan.get("source_path") or ""),
        "target_path": str(plan.get("target_path") or ""),
        "public_path": str(plan.get("public_path") or ""),
        "token": str(plan.get("token") or ""),
        "filename": item.filename,
        "display_name": str(plan.get("display_name") or Path(item.filename).stem),
        "result_type": "script file",
        "size_bytes": item.size,
        "overwrote": results[0].status == "overwritten",
    }


def materialize_interactive_html_assets(
    repo_root: Path,
    staging_root: Path,
    plans: list[Dict[str, Any]],
    *,
    config: DocsStageConfig | DocsCollectionConfig,
    allow_overwrite: bool = False,
) -> list[Dict[str, Any]]:
    if not plans:
        return []
    return [
        materialize_interactive_html_asset(repo_root, staging_root, plan, config=config, allow_overwrite=allow_overwrite)
        for plan in plans
    ]
