"""Project the single workspace into local stage and public reader settings."""
from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import quote

from .common import DOCS_VIEWER_BROWSER_CONFIG_SCHEMA_VERSION, browser_path_for_repo_relative, json_text
from .links_builder import links_enabled
from docs_workspace_config import DocsStageConfig, DocsCollectionConfig, DocsWorkspaceConfig, public_documents_path, public_search_path, select_workspace_stage
from docs_collection_customisations import browser_collection_customisation_payload


def public_document_base(config: DocsStageConfig | DocsCollectionConfig) -> str:
    output = public_documents_path(config)
    if output is None:
        raise ValueError("public document projection requires a configured destination")
    return browser_path_for_repo_relative(output)


def browser_docs_index_tree_url(config: DocsStageConfig, *, published: bool = False) -> str:
    return f"{public_document_base(config)}/index-tree.json" if published else f"/docs/index-tree?stage={quote(config.stage)}"


def browser_docs_recent_url(config: DocsStageConfig, *, published: bool = False) -> str:
    return f"{public_document_base(config)}/recent.json" if published else f"/docs/recent?stage={quote(config.stage)}"


def browser_docs_backlinks_url(config: DocsStageConfig, *, published: bool = False) -> str:
    return "" if published else f"/docs/backlinks?stage={quote(config.stage)}"


def browser_search_index_url(config: DocsStageConfig, *, published: bool = False) -> str:
    if not published:
        return f"/docs/search?stage={quote(config.stage)}"
    output = public_search_path(config)
    if output is None:
        raise ValueError("public Search projection requires a configured destination")
    return browser_path_for_repo_relative(output)


def browser_search_policy_payload(config: DocsStageConfig, *, published: bool = False) -> dict[str, Any]:
    return {"domain": "docs_viewer", "schema": "docs_viewer_search_index_v3",
            "index_url": browser_search_index_url(config, published=published), "rebuild_policy": "whole_index"}


def browser_collection_output_url_base(config: DocsStageConfig, collection: DocsCollectionConfig, *, published: bool = False) -> str:
    if published:
        return public_document_base(collection)
    return f"/docs/generated/external/{quote(config.stage)}/{quote(collection.collection)}"


def browser_collection_records(repo_root: Path, config: DocsStageConfig, *, published: bool = False) -> list[dict[str, Any]]:
    records = []
    for child in config.collections:
        base = browser_collection_output_url_base(config, child, published=published)
        record = {
            "collection": child.collection,
            "title": child.public_title if published else child.title,
            "manifest_url": f"{base}/manifest.json" if published else f"{base}/manage-manifest.json",
            "by_id_url_base": f"{base}/by-id",
        }
        customisation = browser_collection_customisation_payload(child.collection_customisation, published=published)
        if customisation is not None:
            record["collection_customisation"] = customisation
        records.append(record)
    return records


def browser_stage_record(repo_root: Path, config: DocsStageConfig, *, public_viewer_base_url: str = "", published: bool = False) -> dict[str, Any]:
    if published and config.public_projection is None:
        raise ValueError("public reader settings require Pre-publish configuration")
    media = config.public_projection.media if published else config.media.types
    record = {
        "viewer_base_url": public_viewer_base_url if published else "/docs/",
        "default_doc_id": config.default_doc_id,
        "media": {kind: {"reference_prefix": item.reference_prefix.as_posix(), "served_path_prefix": item.served_path_prefix}
                  for kind, item in sorted(media.items())},
        "index_tree_url": browser_docs_index_tree_url(config, published=published),
        "recent_url": browser_docs_recent_url(config, published=published),
        "search_index_url": browser_search_index_url(config, published=published),
        "search": browser_search_policy_payload(config, published=published),
        "collections": browser_collection_records(repo_root, config, published=published),
    }
    if not published:
        record.update(stage=config.stage, links_enabled=links_enabled(repo_root, config), backlinks_url=browser_docs_backlinks_url(config))
    return record


def browser_published_record(repo_root: Path, workspace: DocsWorkspaceConfig) -> dict[str, Any]:
    """Expose the accepted local snapshot without source/generated write authority."""
    prepared = select_workspace_stage(workspace, "pre-publish")
    record = browser_stage_record(repo_root, prepared)
    record.update(stage="published", default_doc_id="", links_enabled=False)
    for key, route in (("index_tree_url", "index-tree"), ("recent_url", "recent"), ("backlinks_url", "backlinks"), ("search_index_url", "search")):
        record[key] = f"/docs/published/{route}"
    record["search"] = {**record["search"], "index_url": record["search_index_url"]}
    for kind, media in record["media"].items():
        media["served_path_prefix"] = f"/docs/published/media/{kind}"
    record["collections"] = browser_collection_records(repo_root, prepared, published=True)
    for child in record["collections"]:
        base = f"/docs/published/external/{quote(child['collection'])}"
        child.update(manifest_url=f"{base}/manifest.json", by_id_url_base=f"{base}/by-id")
    return record


def browser_workspace_config_payload(repo_root: Path, workspace: DocsWorkspaceConfig, *, published: bool = False) -> dict[str, Any]:
    payload = {"schema_version": DOCS_VIEWER_BROWSER_CONFIG_SCHEMA_VERSION, "docs_viewer": {"recent_limit": workspace.recent_limit}}
    if published:
        payload["workspace"] = browser_stage_record(repo_root, select_workspace_stage(workspace, "pre-publish"),
                                                    published=True, public_viewer_base_url=workspace.public_viewer_base_url)
    else:
        payload["public_viewer_base_url"] = workspace.public_viewer_base_url
        payload["stages"] = [browser_stage_record(repo_root, stage) for stage in workspace.stages] + [browser_published_record(repo_root, workspace)]
    return payload


def write_browser_config(repo_root: Path, workspace: DocsWorkspaceConfig, *, path: Path, label: str, published: bool = False) -> None:
    target = repo_root / path
    text = json_text(browser_workspace_config_payload(repo_root, workspace, published=published))
    if target.is_file() and target.read_text(encoding="utf-8") == text:
        print(f"{label}: unchanged")
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    print(f"{label}: wrote")
