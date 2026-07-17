#!/usr/bin/env python3
"""Audit Docs Viewer links for missing targets.

Run:
  ./docs-viewer/services/docs_broken_links.py --scope studio
  ./docs-viewer/services/docs_broken_links.py --scope library --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, quote, urljoin, urlparse

from docs_scope_config import DOCS_SCOPE_CONFIGS, published_documents_path


SCOPE_OUTPUT_DIRS = {scope: published_documents_path(config) for scope, config in DOCS_SCOPE_CONFIGS.items()}
TEMP_BASE_URL = "https://dotlineform.local"
WHITESPACE_PATTERN = re.compile(r"\s+")


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


class AnchorCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.anchors: list[dict[str, str]] = []
        self._current_href: str | None = None
        self._current_parts: list[str] = []
        self._code_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized_tag = tag.lower()
        if normalized_tag in {"code", "pre"}:
            self._code_depth += 1
        if normalized_tag != "a" or self._code_depth > 0:
            return
        href = ""
        for key, value in attrs:
            if key.lower() == "href":
                href = str(value or "").strip()
                break
        self._current_href = href
        self._current_parts = []

    def handle_endtag(self, tag: str) -> None:
        normalized_tag = tag.lower()
        if normalized_tag in {"code", "pre"}:
            self._code_depth = max(0, self._code_depth - 1)
        if normalized_tag != "a" or self._current_href is None:
            return
        self.anchors.append(
            {
                "href": self._current_href,
                "text": normalize_text("".join(self._current_parts)),
            }
        )
        self._current_href = None
        self._current_parts = []

    def handle_data(self, data: str) -> None:
        if self._current_href is None:
            return
        self._current_parts.append(data)


def normalize_scope(scope: Any) -> str:
    value = str(scope or "").strip().lower()
    if value not in SCOPE_OUTPUT_DIRS:
        raise ValueError(f"scope must be one of: {', '.join(sorted(SCOPE_OUTPUT_DIRS))}")
    return value


def normalize_text(value: Any) -> str:
    return WHITESPACE_PATTERN.sub(" ", str(value or "")).strip()


def viewer_url_for(scope: str, doc_id: str) -> str:
    config = DOCS_SCOPE_CONFIGS[scope]
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


def flatten_index_tree(scope: str, docs: list[Any]) -> list[DocMeta]:
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
                    viewer_url=viewer_url_for(scope, doc_id),
                )
            )
        children = item.get("children")
        if isinstance(children, list):
            items.extend(flatten_index_tree(scope, children))
    return items


def load_index_tree(repo_root: Path, scope: str) -> list[DocMeta]:
    index_path = repo_root / SCOPE_OUTPUT_DIRS[scope] / "index-tree.json"
    payload = read_json(index_path, f"{scope} docs index tree")
    docs = payload.get("docs")
    if not isinstance(docs, list):
        raise ValueError(f"Expected docs array in {index_path}")
    return flatten_index_tree(scope, docs)


def load_doc_payload(repo_root: Path, meta: DocMeta) -> DocPayload:
    payload_path = repo_root / SCOPE_OUTPUT_DIRS[meta.scope] / "by-id" / f"{meta.doc_id}.json"
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


def collect_anchors(html_text: str) -> list[dict[str, str]]:
    parser = AnchorCollector()
    parser.feed(html_text)
    parser.close()
    return parser.anchors


def resolve_href(href: str, from_page_url: str) -> str:
    raw = normalize_text(href)
    if not raw:
        return ""
    absolute = urljoin(f"{TEMP_BASE_URL}{from_page_url}", raw)
    parsed = urlparse(absolute)
    if parsed.netloc != urlparse(TEMP_BASE_URL).netloc:
        return absolute
    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"
    if parsed.fragment:
        path = f"{path}#{parsed.fragment}"
    return path


def parse_docs_target(resolved_href: str) -> dict[str, str] | None:
    raw = normalize_text(resolved_href)
    if not raw or raw.startswith("#"):
        return None

    parsed = urlparse(raw)
    if parsed.scheme and parsed.scheme not in {"http", "https"}:
        return None
    if parsed.scheme in {"http", "https"} and parsed.netloc != urlparse(TEMP_BASE_URL).netloc:
        return None

    path = parsed.path or ""
    query = parse_qs(parsed.query)
    trimmed_path = path.rstrip("/")
    fragment = normalize_text(parsed.fragment)

    for scope, config in DOCS_SCOPE_CONFIGS.items():
        viewer_path = config.viewer_base_url.rstrip("/")
        if trimmed_path != viewer_path.rstrip("/"):
            continue
        doc_id = normalize_text(query.get("doc", [""])[0])
        if not doc_id:
            return None
        explicit_scope = normalize_text(query.get("scope", [""])[0])
        target_scope = explicit_scope if explicit_scope in DOCS_SCOPE_CONFIGS else scope
        return {"kind": "viewer", "scope": target_scope, "doc_id": doc_id, "fragment": fragment}

    if path.endswith(".md"):
        return {"kind": "source_markdown", "path": path, "fragment": fragment}

    return None


def is_same_doc_fragment_link(current_doc: DocMeta, target: dict[str, str]) -> bool:
    fragment = normalize_text(target.get("fragment"))
    if not fragment:
        return False

    if target.get("kind") == "viewer":
        return (
            normalize_text(target.get("scope")) == current_doc.scope
            and normalize_text(target.get("doc_id")) == current_doc.doc_id
        )

    return False


def audit_docs_broken_links(repo_root: Path, scope: str) -> dict[str, Any]:
    normalized_scope = normalize_scope(scope)
    docs_by_key: dict[tuple[str, str], DocMeta] = {}
    for known_scope in sorted(SCOPE_OUTPUT_DIRS.keys()):
        for meta in load_index_tree(repo_root, known_scope):
            docs_by_key[(meta.scope, meta.doc_id)] = meta

    audited_docs = [load_doc_payload(repo_root, meta) for meta in load_index_tree(repo_root, normalized_scope)]
    entries: list[dict[str, str]] = []

    for doc in audited_docs:
        for anchor in collect_anchors(doc.content_html):
            raw_href = normalize_text(anchor.get("href"))
            if not raw_href:
                continue

            resolved_href = resolve_href(raw_href, doc.meta.viewer_url)
            target = parse_docs_target(resolved_href)
            if target is None:
                continue
            if is_same_doc_fragment_link(doc.meta, target):
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
            item["from_page_text"].lower(),
            item["link_text"].lower(),
            item["link_url"].lower(),
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
