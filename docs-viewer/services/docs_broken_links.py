#!/usr/bin/env python3
"""Audit Docs Viewer links for missing targets.

Run:
  python3 docs-viewer/services/docs_broken_links.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parents[2]
for import_directory in (
    REPO_ROOT, REPO_ROOT / "studio/shared/python", REPO_ROOT / "studio/services", REPO_ROOT / "docs-viewer/build",
):
    if str(import_directory) not in sys.path:
        sys.path.insert(0, str(import_directory))

from docs_artifact_locations import ArtifactLocation, FilesystemArtifactLocationAdapter, filesystem_location_root  # noqa: E402
from docs_document_identity import is_document_id  # noqa: E402
from docs_document_location import canonical_document_viewer_url  # noqa: E402
from docs_source_inspection import inspection_source_paths, read_inspection_source  # noqa: E402

from docs_workspace_config import (  # noqa: E402
    DocsWorkspaceConfig,
    generated_documents_path,
    public_document_reader_paths,
    load_docs_workspace_config,
    resolve_workspace_path,
    select_workspace_stage,
)
from docs_rendered_links import (  # noqa: E402
    collect_anchors,
    is_same_doc_fragment_link,
    normalize_text,
    parse_docs_target,
    resolve_href,
)

from docs_builder.semantic_token_registry import load_semantic_token_registry  # noqa: E402
from docs_builder.semantic_tokens import (  # noqa: E402
    parse_semantic_tokens,
)
from docs_media_inventory import parsed_source_media_references  # noqa: E402
from docs_catalogue_media import catalogue_media_record, read_catalogue_media_config, read_catalogue_gallery, read_catalogue_work  # noqa: E402
from studio.services.catalogue.catalogue_gallery_records import validate_gallery_record  # noqa: E402


@dataclass(frozen=True)
class DocMeta:
    doc_id: str
    title: str
    viewer_url: str
    collection: str

    def source_fields(self) -> dict[str, str]:
        """Expose the exact correction location without filesystem paths."""
        return {
            "from_page_text": self.title,
            "from_page_url": self.viewer_url,
            "from_page_collection": self.collection,
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
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object for {label}: {path}")
    return payload


def document_payload_path(root: Path, doc_id: str) -> Path:
    """Resolve one by-ID read without traversing symlinks outside its owner."""
    path = root / "by-id" / f"{doc_id}.json"
    if path.resolve() != path:
        raise ValueError(f"Generated document path must not traverse symlinks: {doc_id}")
    return path


def target_payload_exists(target: dict[str, str], roots: dict[str, Path]) -> bool:
    """Check the exact configured by-ID destination without reading its browse host."""
    doc_id = target["doc_id"]
    collection = target.get("collection", "")
    if collection not in roots or not is_document_id(doc_id, collection=collection):
        return False
    return document_payload_path(roots[collection], doc_id).is_file()


def catalogue_target_reason(
    repo_root: Path,
    target_type: str,
    target_id: str,
    *,
    workspace: ArtifactLocation,
) -> str:
    """Diagnose one selected generated record within the supplied Catalogue owner."""
    try:
        if target_type == "gallery":
            validate_gallery_record(read_catalogue_gallery(repo_root, target_id, workspace=workspace), gallery_id=target_id)
        else:
            catalogue_media_record(read_catalogue_work(repo_root, target_id, workspace=workspace), target_id)
    except ValueError:
        return "missing_gallery" if target_type == "gallery" else "missing_media"
    return ""


def audit_docs_broken_links(repo_root: Path, workspace: DocsWorkspaceConfig) -> dict[str, Any]:
    """Audit authored sources without relationship/publication eligibility filters.

    Every configured collection in the configured workspace is audited. Rendered links
    use generated by-ID HTML; token diagnosis uses source Markdown. Missing
    source payloads are returned separately so partial coverage is visible.
    Destination lookup remains independent of the selected source boundary.
    """
    config = select_workspace_stage(workspace, "working")
    viewer_routes = ("/docs/", workspace.public_viewer_base_url)
    collections = [("", config), *((item.collection, item) for item in config.collections)]
    local_roots = {child: resolve_workspace_path(repo_root, generated_documents_path(owner)) for child, owner in collections}
    public_roots = {child: resolve_workspace_path(repo_root, path) for child, path in public_document_reader_paths(workspace).items()}
    registry = load_semantic_token_registry(repo_root)
    if registry is None:
        raise ValueError("Semantic-token registry is unavailable.")
    entries: list[dict[str, Any]] = []
    unavailable_sources: list[dict[str, str]] = []
    destination_exists: dict[tuple[bool, str, str], bool] = {}
    catalogue_reasons: dict[tuple[str, str], str] = {}
    media_policy_available: bool | None = None
    for collection, owner in collections:
        root, paths = inspection_source_paths(repo_root, owner)
        media_assets = {
            media_type: FilesystemArtifactLocationAdapter(
                media.asset_location, root=filesystem_location_root(repo_root, media.asset_location),
            ) for media_type, media in (owner.media.types.items() if owner.media is not None else ())
        }
        media_exists: dict[tuple[str, str], bool] = {}
        for path in paths:
            source = read_inspection_source(root, path, collection=collection)
            meta = DocMeta(
                source.doc_id, source.title, canonical_document_viewer_url(source.doc_id, collection=collection), collection,
            )
            tokens = parse_semantic_tokens(source.body, registry=registry)
            for reference in parsed_source_media_references(
                owner, source.source_text, semantic_tokens=tokens,
                doc_id=meta.doc_id,
            ):
                key = (reference.media_type, reference.identity)
                if key not in media_exists:
                    media_exists[key] = media_assets[reference.media_type].resolve(reference.identity).is_file()
                if not media_exists[key]:
                    entries.append({
                        "issue_type": "document_media",
                        "reason": "missing_media",
                        "media_type": reference.media_type,
                        "media_identity": reference.identity,
                        "link_text": reference.logical_path,
                        "link_url": "",
                        **meta.source_fields(),
                    })
            for token in tokens:
                if token.family != "catalogue":
                    continue
                reason = "unsupported_kind"
                if token.supported:
                    if media_policy_available is None:
                        try:
                            read_catalogue_media_config(repo_root, workspace=workspace.catalogue.working)
                            media_policy_available = True
                        except ValueError:
                            media_policy_available = False
                    key = (token.target_type, token.target_id)
                    if key not in catalogue_reasons:
                        catalogue_reasons[key] = catalogue_target_reason(
                            repo_root, *key, workspace=workspace.catalogue.working,
                        ) if media_policy_available else (
                            "missing_gallery" if token.target_type == "gallery" else "missing_media"
                        )
                    reason = catalogue_reasons[key]
                if reason:
                    entries.append({
                        "issue_type": "semantic_token",
                        "source_collection": meta.collection,
                        "source_doc_id": meta.doc_id,
                        "source_range": token.source_range,
                        "raw": token.raw,
                        "family": token.family,
                        "target_type": token.target_type,
                        "target_id": token.target_id,
                        "reason": reason,
                        "link_text": token.title,
                        "link_url": "",
                        **meta.source_fields(),
                    })
            payload_path = document_payload_path(local_roots[collection], meta.doc_id)
            try:
                payload = read_json(payload_path, "source document payload")
            except FileNotFoundError:
                destination_exists[(False, collection, meta.doc_id)] = False
                unavailable_sources.append(meta.source_fields())
                continue
            destination_exists[(False, collection, meta.doc_id)] = True
            entries.extend(rendered_link_broken_entries(
                meta, payload["content_html"],
                workspace, local_roots, public_roots, viewer_routes, destination_exists,
            ))

    return {
        "ok": True,
        "summary": {"total": len(entries)},
        "entries": entries,
        "unavailable_sources": unavailable_sources,
    }


def rendered_link_broken_entries(
    meta: DocMeta, content_html: str,
    workspace: DocsWorkspaceConfig, local_roots: dict[str, Path], public_roots: dict[str, Path],
    viewer_routes: tuple[str, ...],
    destination_exists: dict[tuple[bool, str, str], bool],
) -> list[dict[str, Any]]:
    """Diagnose rendered document links while retaining the owning source identity."""
    entries: list[dict[str, Any]] = []
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
        is_public = urlparse(resolved_href).path.rstrip("/") == workspace.public_viewer_base_url.rstrip("/")
        if not is_public and is_same_doc_fragment_link(
            current_doc_id=meta.doc_id,
            current_collection=meta.collection,
            target=target,
        ):
            continue

        link_text = normalize_text(anchor.get("text")) or normalize_text(raw_href) or normalize_text(resolved_href)
        available = False
        if target["kind"] == "viewer":
            key = (is_public, target.get("collection", ""), target["doc_id"])
            if key not in destination_exists:
                destination_exists[key] = target_payload_exists(target, public_roots if is_public else local_roots)
            available = destination_exists[key]
        if not available:
            entries.append(
                {
                    "link_text": link_text,
                    "link_url": resolved_href,
                    **meta.source_fields(),
                }
            )

    return entries


def print_human_summary(payload: dict[str, Any]) -> None:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    total = int(summary.get("total") or 0)
    print(f"Docs broken links: {total} issue(s)")
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
    parser.add_argument("--repo-root", help="Override repo root auto-detection")
    parser.add_argument("--json", action="store_true", help="Print JSON payload")
    args = parser.parse_args(argv)

    try:
        repo_root = detect_repo_root(args.repo_root)
        payload = audit_docs_broken_links(repo_root, load_docs_workspace_config(repo_root))
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
