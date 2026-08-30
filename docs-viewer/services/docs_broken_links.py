#!/usr/bin/env python3
"""Audit Docs Viewer links for missing targets.

Run:
  ./docs-viewer/services/docs_broken_links.py --scope studio
  ./docs-viewer/services/docs_broken_links.py --scope analysis --json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote

from docs_scope_config import (
    DOCS_SCOPE_CONFIGS,
    DocsScopeConfig,
    generated_documents_path,
    load_docs_scope_configs,
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
from docs_builder.semantic_target_lookup import tag_resolution_states  # noqa: E402
from docs_builder.semantic_tokens import (  # noqa: E402
    load_semantic_token_target_records,
    parse_semantic_tokens,
    resolve_catalogue_image_target,
)
from docs_source_model import load_scope_docs_for_config  # noqa: E402


# Retained for callers that present the configured scope list. Audit reads
# always reload the selected repository's current config.
SCOPE_OUTPUT_DIRS = {
    scope: generated_documents_path(config)
    for scope, config in DOCS_SCOPE_CONFIGS.items()
}


@dataclass(frozen=True)
class DocMeta:
    scope: str
    doc_id: str
    title: str
    viewer_url: str


@dataclass(frozen=True)
class DocPayload:
    meta: DocMeta
    content_html: str


def normalize_scope(scope: Any, configs: dict[str, DocsScopeConfig]) -> str:
    value = str(scope or "").strip().lower()
    if value not in configs:
        raise ValueError(f"scope must be one of: {', '.join(sorted(configs))}")
    return value


def viewer_url_for(configs: dict[str, DocsScopeConfig], scope: str, doc_id: str) -> str:
    config = configs[scope]
    pairs: list[str] = []
    if config.include_scope_param:
        pairs.append(f"scope={quote(scope)}")
    pairs.append(f"doc={quote(doc_id)}")
    return f"{config.viewer_base_url}?{'&'.join(pairs)}"


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


def flatten_index_tree(
    scope: str,
    docs: list[Any],
    configs: dict[str, DocsScopeConfig],
) -> list[DocMeta]:
    items: list[DocMeta] = []
    for item in docs:
        if not isinstance(item, dict):
            continue
        doc_id = normalize_text(item.get("doc_id"))
        title = normalize_text(item.get("title"))
        if doc_id and title:
            items.append(
                DocMeta(
                    scope=scope,
                    doc_id=doc_id,
                    title=title,
                    viewer_url=viewer_url_for(configs, scope, doc_id),
                )
            )
        children = item.get("children")
        if isinstance(children, list):
            items.extend(flatten_index_tree(scope, children, configs))
    return items


def load_index_tree(
    repo_root: Path,
    scope: str,
    configs: dict[str, DocsScopeConfig],
) -> list[DocMeta]:
    index_path = repo_root / generated_documents_path(configs[scope]) / "index-tree.json"
    payload = read_json(index_path, f"{scope} docs index tree")
    docs = payload.get("docs")
    if not isinstance(docs, list):
        raise ValueError(f"Expected docs array in {index_path}")
    return flatten_index_tree(scope, docs, configs)


def load_doc_payload(
    repo_root: Path,
    meta: DocMeta,
    configs: dict[str, DocsScopeConfig],
) -> DocPayload:
    payload_path = repo_root / generated_documents_path(configs[meta.scope]) / "by-id" / f"{meta.doc_id}.json"
    payload = read_json(payload_path, f"{meta.scope} doc payload for {meta.doc_id}")
    hydrated_meta = DocMeta(
        scope=meta.scope,
        doc_id=meta.doc_id,
        title=normalize_text(payload.get("title")) or meta.title,
        viewer_url=normalize_text(payload.get("viewer_url")) or meta.viewer_url,
    )
    if not hydrated_meta.title or not hydrated_meta.viewer_url:
        raise ValueError(f"Expected title and viewer_url in {payload_path}")
    return DocPayload(
        meta=hydrated_meta,
        content_html=str(payload.get("content_html") or ""),
    )


def semantic_token_broken_entries(
    repo_root: Path,
    scope: str,
    configs: dict[str, DocsScopeConfig],
) -> list[dict[str, Any]]:
    registry = load_semantic_token_registry(repo_root)
    if registry is None:
        raise ValueError("Semantic-token registry is unavailable.")
    targets_by_key = load_semantic_token_target_records(repo_root)
    entries: list[dict[str, Any]] = []
    tag_states: dict[str, str] | None = None
    for doc in load_scope_docs_for_config(repo_root, configs[scope]):
        for token in parse_semantic_tokens(doc.body, registry=registry):
            target = targets_by_key.get((token.family, token.target_type, token.target_id))
            reason = ""
            if not token.supported:
                reason = "unsupported_kind"
            elif token.family == "tag":
                if tag_states is None:
                    tag_states = tag_resolution_states(repo_root)
                reason = tag_states.get(token.target_id, "unknown_tag")
                if not reason and target is None:
                    reason = "missing_target"
            elif target is None:
                reason = "missing_target"
            elif not str(target.get("href") or "").strip().startswith("/"):
                reason = "missing_destination"
            elif token.presentation == "image":
                resolved_target = resolve_catalogue_image_target(repo_root, token, target)
                if resolved_target is None:
                    reason = "missing_detail_image" if token.detail_id else "missing_image"
            if not reason:
                continue
            link_url = str((target or {}).get("href") or "").strip()
            if token.family == "tag" and reason in {
                "unknown_tag",
                "missing_tag_association",
                "missing_tag_destination",
            }:
                link_url = ""
            entries.append(
                {
                    "issue_type": "semantic_token",
                    "source_scope": scope,
                    "source_doc_id": doc.doc_id,
                    "source_range": token.source_range,
                    "raw": token.raw,
                    "family": token.family,
                    "target_type": token.target_type,
                    "target_id": token.target_id,
                    "reason": reason,
                    "link_text": token.title,
                    "link_url": link_url,
                    "from_page_text": doc.title,
                    "from_page_url": viewer_url_for(configs, scope, doc.doc_id),
                    "from_page_scope": scope,
                    "from_page_doc_id": doc.doc_id,
                }
            )
    return entries


def audit_docs_broken_links(repo_root: Path, scope: str) -> dict[str, Any]:
    configs = load_docs_scope_configs(repo_root)
    normalized_scope = normalize_scope(scope, configs)
    viewer_routes = tuple(
        (scope_id, config.viewer_base_url)
        for scope_id, config in configs.items()
    )
    docs_by_key: dict[tuple[str, str], DocMeta] = {}
    for known_scope in sorted(configs):
        for meta in load_index_tree(repo_root, known_scope, configs):
            docs_by_key[(meta.scope, meta.doc_id)] = meta

    audited_docs = [
        load_doc_payload(repo_root, meta, configs)
        for meta in load_index_tree(repo_root, normalized_scope, configs)
    ]
    entries: list[dict[str, Any]] = semantic_token_broken_entries(
        repo_root,
        normalized_scope,
        configs,
    )

    for doc in audited_docs:
        for anchor in collect_anchors(doc.content_html):
            raw_href = normalize_text(anchor.get("href"))
            if not raw_href:
                continue

            resolved_href = resolve_href(raw_href, doc.meta.viewer_url)
            target = parse_docs_target(
                resolved_href,
                viewer_routes=viewer_routes,
                known_scopes=set(configs),
            )
            if target is None:
                continue
            if is_same_doc_fragment_link(
                current_scope=doc.meta.scope,
                current_doc_id=doc.meta.doc_id,
                target=target,
            ):
                continue

            link_text = normalize_text(anchor.get("text")) or normalize_text(raw_href) or normalize_text(resolved_href)
            from_page_text = doc.meta.title
            from_page_url = doc.meta.viewer_url
            from_page_scope = doc.meta.scope
            from_page_doc_id = doc.meta.doc_id

            if target.get("kind") == "source_markdown":
                entries.append(
                    {
                        "link_text": link_text,
                        "link_url": resolved_href,
                        "from_page_text": from_page_text,
                        "from_page_url": from_page_url,
                        "from_page_scope": from_page_scope,
                        "from_page_doc_id": from_page_doc_id,
                    }
                )
                continue

            target_scope = normalize_text(target.get("scope"))
            target_doc_id = normalize_text(target.get("doc_id"))
            if docs_by_key.get((target_scope, target_doc_id)) is None:
                entries.append(
                    {
                        "link_text": link_text,
                        "link_url": resolved_href,
                        "from_page_text": from_page_text,
                        "from_page_url": from_page_url,
                        "from_page_scope": from_page_scope,
                        "from_page_doc_id": from_page_doc_id,
                    }
                )

    entries.sort(
        key=lambda item: (
            str(item.get("from_page_text") or "").lower(),
            str(item.get("link_text") or item.get("raw") or "").lower(),
            str(item.get("link_url") or item.get("reason") or "").lower(),
        )
    )

    return {
        "ok": True,
        "scope": normalized_scope,
        "summary": {
            "total": len(entries),
        },
        "entries": entries,
    }


def print_human_summary(payload: dict[str, Any]) -> None:
    scope = normalize_text(payload.get("scope"))
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    total = int(summary.get("total") or 0)
    print(f"Docs broken links for {scope}: {total} issue(s)")
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
    parser.add_argument("--scope", required=True, help=f"Docs scope to audit: {', '.join(sorted(SCOPE_OUTPUT_DIRS))}")
    parser.add_argument("--repo-root", help="Override repo root auto-detection")
    parser.add_argument("--json", action="store_true", help="Print JSON payload")
    args = parser.parse_args(argv)

    try:
        repo_root = detect_repo_root(args.repo_root)
        payload = audit_docs_broken_links(repo_root, args.scope)
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
