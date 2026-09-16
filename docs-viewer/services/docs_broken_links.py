#!/usr/bin/env python3
"""Audit Docs Viewer links for missing targets.

Run:
  python3 docs-viewer/services/docs_broken_links.py --stage working --json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import docs_document_location as document_location
from docs_document_identity import is_immutable_doc_id

from docs_workspace_config import (
    DocsStageConfig,
    DocsSubScopeConfig,
    DocsWorkspaceConfig,
    generated_documents_path,
    published_documents_path,
    load_docs_workspace_config,
    select_workspace_stage,
    resolve_workspace_path,
)
from docs_rendered_links import (
    collect_anchors,
    is_same_doc_fragment_link,
    normalize_text,
    parse_docs_target,
    resolve_href,
)


BUILD_DIR = Path(__file__).resolve().parents[1] / "build"
if str(BUILD_DIR) not in sys.path:
    sys.path.insert(0, str(BUILD_DIR))

from docs_builder.semantic_token_registry import load_semantic_token_registry  # noqa: E402
from docs_builder.semantic_tokens import (  # noqa: E402
    parse_semantic_tokens,
)
from docs_source_model import load_document_collection_docs_for_config  # noqa: E402
# The workspace and builder imports initialize repository and shared Python paths.
from docs_catalogue_media import catalogue_media_record, read_catalogue_series, read_catalogue_work  # noqa: E402


@dataclass(frozen=True)
class DocMeta:
    doc_id: str
    title: str
    viewer_url: str
    stage: str
    sub_scope: str

    def source_fields(self) -> dict[str, str]:
        """Expose the exact correction location without filesystem paths."""
        return {
            "from_page_text": self.title,
            "from_page_url": self.viewer_url,
            "from_page_stage": self.stage,
            "from_page_sub_scope": self.sub_scope,
            "from_page_doc_id": self.doc_id,
        }


def detect_repo_root(explicit_root: str | None = None) -> Path:
    if explicit_root:
        repo_root = Path(explicit_root).expanduser().resolve()
        if not (repo_root / "site-tools" / "config" / "site-tools.json").exists():
            raise ValueError(f"--repo-root does not look like repo root: {repo_root}")
        return repo_root

    current = Path.cwd().resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "site-tools" / "config" / "site-tools.json").exists():
            return candidate

    script_dir = Path(__file__).resolve().parent
    for candidate in [script_dir, *script_dir.parents]:
        if (candidate / "site-tools" / "config" / "site-tools.json").exists():
            return candidate

    raise ValueError("Could not detect repo root")


def read_json(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object for {label}: {path}")
    return payload


def target_stage_config(
    target: dict[str, str], workspace: DocsWorkspaceConfig,
) -> DocsStageConfig | None:
    """Resolve the destination collection configuration without selecting source data."""
    if target.get("kind") != "viewer":
        return None
    stage = target.get("stage")
    try:
        return select_workspace_stage(workspace, "pre-publish" if stage == "published" else stage)
    except ValueError:
        return None


def target_payload_exists(
    repo_root: Path, target: dict[str, str], config: DocsStageConfig,
) -> bool:
    """Check the selected generated or accepted destination through its exact host."""
    doc_id = target["doc_id"]
    if not is_immutable_doc_id(doc_id):
        return False
    documents_path = published_documents_path if target["stage"] == "published" else generated_documents_path
    path = resolve_workspace_path(repo_root, documents_path(config)) / "by-id" / f"{doc_id}.json"
    if not path.is_file():
        return False
    child_id = target.get("subdoc")
    if not child_id:
        return True
    if not is_immutable_doc_id(child_id):
        return False
    host = read_json(path, "destination report host")
    report = host.get("report")
    if not isinstance(report, dict) or report.get("id") != "docs_subscope":
        return False
    collection = next(
        (item for item in config.sub_scopes if item.sub_scope == report.get("sub_scope")),
        None,
    )
    return bool(collection and (
        resolve_workspace_path(repo_root, documents_path(collection)) / "by-id" / f"{child_id}.json"
    ).is_file())


def semantic_token_broken_entries(
    repo_root: Path,
    sources: list[tuple[DocMeta, str]],
) -> list[dict[str, Any]]:
    registry = load_semantic_token_registry(repo_root)
    if registry is None:
        raise ValueError("Semantic-token registry is unavailable.")
    entries: list[dict[str, Any]] = []
    for meta, body in sources:
        for token in parse_semantic_tokens(body, registry=registry):
            reason = ""
            if not token.supported:
                reason = "unsupported_kind"
            else:
                try:
                    if token.target_type == "series":
                        read_catalogue_series(repo_root, token.target_id)
                    else:
                        catalogue_media_record(read_catalogue_work(repo_root, token.target_id), token.target_id, token.detail_id)
                except ValueError:
                    reason = "missing_series" if token.target_type == "series" else "missing_detail_image" if token.detail_id else "missing_media"
            if not reason:
                continue
            entries.append(
                {
                    "issue_type": "semantic_token",
                    "source_stage": meta.stage,
                    "source_sub_scope": meta.sub_scope,
                    "source_doc_id": meta.doc_id,
                    "source_range": token.source_range,
                    "raw": token.raw,
                    "family": token.family,
                    "target_type": token.target_type,
                    "target_id": token.target_id,
                    "detail_id": token.detail_id,
                    "reason": reason,
                    "link_text": token.title,
                    "link_url": "",
                    **meta.source_fields(),
                }
            )
    return entries


def audit_docs_broken_links(repo_root: Path, *, stage: str) -> dict[str, Any]:
    """Audit authored sources without relationship/publication eligibility filters.

    Every configured collection in the explicit selected stage is audited. Rendered links
    use generated by-ID HTML; token diagnosis uses source Markdown. Missing
    source payloads are returned separately so partial coverage is visible.
    Destination lookup remains independent of the selected source boundary.
    """
    workspace = load_docs_workspace_config(repo_root)
    config = select_workspace_stage(workspace, stage)
    viewer_routes = ("/docs/", workspace.public_viewer_base_url)
    collections: list[tuple[str, DocsStageConfig | DocsSubScopeConfig]] = [("", config)]
    collections.extend((item.sub_scope, item) for item in config.sub_scopes)
    sources: list[tuple[DocMeta, str]] = []
    entries: list[dict[str, Any]] = []
    unavailable_sources: list[dict[str, str]] = []
    destination_exists: dict[str, bool] = {}
    for sub_scope, collection in collections:
        collection_url = document_location.management_collection_viewer_url(
            repo_root, sub_scope, stage=config.stage,
        )
        for doc in load_document_collection_docs_for_config(repo_root, config, collection):
            meta = DocMeta(
                stage=config.stage, sub_scope=sub_scope,
                doc_id=doc.doc_id, title=doc.title,
                viewer_url=document_location.management_document_viewer_url(
                    collection_url, doc.doc_id, sub_scope=bool(sub_scope),
                ),
            )
            sources.append((meta, doc.body))
            payload_path = resolve_workspace_path(repo_root, generated_documents_path(collection)) / "by-id" / f"{doc.doc_id}.json"
            if not payload_path.is_file():
                unavailable_sources.append(meta.source_fields())
                continue
            payload = read_json(payload_path, "source document payload")
            entries.extend(rendered_link_broken_entries(
                repo_root, meta, str(payload.get("content_html") or ""),
                workspace, viewer_routes, destination_exists,
            ))

    entries.extend(semantic_token_broken_entries(repo_root, sources))
    entries.sort(key=lambda item: (
        str(item.get("from_page_text") or "").lower(),
        str(item.get("link_text") or item.get("raw") or "").lower(),
        str(item.get("link_url") or item.get("reason") or "").lower(),
    ))
    return {
        "ok": True,
        "stage": config.stage,
        "summary": {"total": len(entries)},
        "entries": entries,
        "unavailable_sources": unavailable_sources,
    }


def rendered_link_broken_entries(
    repo_root: Path, meta: DocMeta, content_html: str,
    workspace: DocsWorkspaceConfig, viewer_routes: tuple[str, ...],
    destination_exists: dict[str, bool],
) -> list[dict[str, Any]]:
    """Diagnose rendered document links while retaining the owning source identity."""
    entries: list[dict[str, Any]] = []
    parent_id = parse_qs(urlparse(meta.viewer_url).query).get("doc", [""])[0] if meta.sub_scope else ""
    for anchor in collect_anchors(content_html):
        raw_href = normalize_text(anchor.get("href"))
        if not raw_href:
            continue

        if raw_href.startswith("#") or (
            "#" in raw_href and raw_href.split("#", 1)[0] in {f"{meta.doc_id}.md", f"./{meta.doc_id}.md"}
        ):
            continue
        resolved_href = resolve_href(raw_href, meta.viewer_url)
        target = parse_docs_target(
            resolved_href,
            viewer_routes=viewer_routes,
        )
        if target is None:
            continue
        if target.get("kind") == "viewer":
            parsed = urlparse(resolved_href)
            is_public = parsed.path.rstrip("/") == workspace.public_viewer_base_url.rstrip("/")
            if is_public and "stage" in parse_qs(parsed.query, keep_blank_values=True):
                target["kind"] = "invalid_viewer"
            elif "stage" not in parse_qs(parsed.query, keep_blank_values=True):
                target["stage"] = "published" if is_public else "working"
        target_config = target_stage_config(target, workspace)
        if is_same_doc_fragment_link(
            current_doc_id=meta.doc_id,
            current_stage=meta.stage,
            current_parent_doc_id=parent_id,
            target=target,
        ):
            continue

        link_text = normalize_text(anchor.get("text")) or normalize_text(raw_href) or normalize_text(resolved_href)
        if resolved_href not in destination_exists:
            destination_exists[resolved_href] = bool(
                target.get("kind") == "viewer" and target_config is not None
                and target_payload_exists(repo_root, target, target_config)
            )
        if not destination_exists[resolved_href]:
            entries.append(
                {
                    "link_text": link_text,
                    "link_url": resolved_href,
                    **meta.source_fields(),
                }
            )

    return entries


def print_human_summary(payload: dict[str, Any]) -> None:
    stage = normalize_text(payload.get("stage"))
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    total = int(summary.get("total") or 0)
    print(f"Docs broken links for {stage}: {total} issue(s)")
    for source in payload.get("unavailable_sources") or []:
        print(f"- Links not scanned (generated payload missing): {source['from_page_url']}")
    for entry in payload.get("entries") or []:
        if not isinstance(entry, dict):
            continue
        if entry.get("issue_type") == "semantic_token":
            print(
                f"- {normalize_text(entry.get('raw'))} "
                f"({normalize_text(entry.get('reason'))}, from "
                f"{normalize_text(entry.get('from_page_text'))})"
            )
            continue
        print(
            f"- {normalize_text(entry.get('link_text'))} -> {normalize_text(entry.get('link_url'))} "
            f"(from {normalize_text(entry.get('from_page_text'))})"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit Docs Viewer links for missing targets.")
    parser.add_argument("--stage", required=True, choices=("working", "pre-publish"), help="Exact authoring stage to audit")
    parser.add_argument("--repo-root", help="Override repo root auto-detection")
    parser.add_argument("--json", action="store_true", help="Print JSON payload")
    args = parser.parse_args(argv)

    try:
        repo_root = detect_repo_root(args.repo_root)
        payload = audit_docs_broken_links(repo_root, stage=args.stage)
    except (FileNotFoundError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print_human_summary(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
