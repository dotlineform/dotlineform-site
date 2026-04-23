#!/usr/bin/env python3
"""Audit Docs Viewer links for missing targets and title mismatches.

Run:
  ./scripts/docs/docs_broken_links.py --scope studio
  ./scripts/docs/docs_broken_links.py --scope library --json
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
from urllib.parse import parse_qs, urljoin, urlparse


SCOPE_OUTPUT_DIRS = {
    "studio": Path("assets/data/docs/scopes/studio"),
    "library": Path("assets/data/docs/scopes/library"),
}
TEMP_BASE_URL = "https://dotlineform.local"
WHITESPACE_PATTERN = re.compile(r"\s+")


@dataclass(frozen=True)
class DocMeta:
    scope: str
    doc_id: str
    title: str
    viewer_url: str
    source_path: str


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

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        href = ""
        for key, value in attrs:
            if key.lower() == "href":
                href = str(value or "").strip()
                break
        self._current_href = href
        self._current_parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a" or self._current_href is None:
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
        raise ValueError("scope must be 'studio' or 'library'")
    return value


def normalize_text(value: Any) -> str:
    return WHITESPACE_PATTERN.sub(" ", str(value or "")).strip()


def humanize_problem(value: str) -> str:
    return value.replace("_", " ")


def detect_repo_root(explicit_root: str | None = None) -> Path:
    if explicit_root:
        repo_root = Path(explicit_root).expanduser().resolve()
        if not (repo_root / "_config.yml").exists():
            raise ValueError(f"--repo-root does not look like repo root: {repo_root}")
        return repo_root

    current = Path.cwd().resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "_config.yml").exists():
            return candidate

    script_dir = Path(__file__).resolve().parent
    for candidate in [script_dir, *script_dir.parents]:
        if (candidate / "_config.yml").exists():
            return candidate

    raise ValueError("Could not detect repo root")


def read_json(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object for {label}: {path}")
    return payload


def load_index(repo_root: Path, scope: str) -> list[DocMeta]:
    index_path = repo_root / SCOPE_OUTPUT_DIRS[scope] / "index.json"
    payload = read_json(index_path, f"{scope} docs index")
    docs = payload.get("docs")
    if not isinstance(docs, list):
        raise ValueError(f"Expected docs array in {index_path}")

    items: list[DocMeta] = []
    for item in docs:
        if not isinstance(item, dict):
            continue
        doc_id = normalize_text(item.get("doc_id"))
        title = normalize_text(item.get("title"))
        viewer_url = normalize_text(item.get("viewer_url"))
        source_path = normalize_text(item.get("source_path"))
        if not doc_id or not title or not viewer_url:
            continue
        items.append(
            DocMeta(
                scope=scope,
                doc_id=doc_id,
                title=title,
                viewer_url=viewer_url,
                source_path=source_path,
            )
        )
    return items


def load_doc_payload(repo_root: Path, meta: DocMeta) -> DocPayload:
    payload_path = repo_root / SCOPE_OUTPUT_DIRS[meta.scope] / "by-id" / f"{meta.doc_id}.json"
    payload = read_json(payload_path, f"{meta.scope} doc payload for {meta.doc_id}")
    return DocPayload(
        meta=meta,
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

    if trimmed_path == "/docs":
        doc_id = normalize_text(query.get("doc", [""])[0])
        if not doc_id:
            return None
        return {"kind": "viewer", "scope": "studio", "doc_id": doc_id}

    if trimmed_path == "/library":
        doc_id = normalize_text(query.get("doc", [""])[0])
        if not doc_id:
            return None
        return {"kind": "viewer", "scope": "library", "doc_id": doc_id}

    if path.endswith(".md"):
        return {"kind": "source_markdown", "path": path}

    return None


def linked_page_text_for_missing(target: dict[str, str], resolved_href: str) -> str:
    if target.get("kind") == "viewer":
        scope = normalize_text(target.get("scope"))
        doc_id = normalize_text(target.get("doc_id"))
        return f"{scope}:{doc_id}" if scope and doc_id else normalize_text(resolved_href)
    return normalize_text(target.get("path")) or normalize_text(resolved_href)


def audit_docs_broken_links(repo_root: Path, scope: str) -> dict[str, Any]:
    normalized_scope = normalize_scope(scope)
    docs_by_key: dict[tuple[str, str], DocMeta] = {}
    for known_scope in sorted(SCOPE_OUTPUT_DIRS.keys()):
        for meta in load_index(repo_root, known_scope):
            docs_by_key[(meta.scope, meta.doc_id)] = meta

    audited_docs = [load_doc_payload(repo_root, meta) for meta in load_index(repo_root, normalized_scope)]
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

            link_text = normalize_text(anchor.get("text")) or normalize_text(raw_href) or normalize_text(resolved_href)
            from_page_text = doc.meta.title
            from_page_url = doc.meta.viewer_url

            if target.get("kind") == "source_markdown":
                entries.append(
                    {
                        "problem": "not found",
                        "linked_page_text": linked_page_text_for_missing(target, resolved_href),
                        "linked_page_url": resolved_href,
                        "link_text": link_text,
                        "link_url": resolved_href,
                        "from_page_text": from_page_text,
                        "from_page_url": from_page_url,
                    }
                )
                continue

            target_scope = normalize_text(target.get("scope"))
            target_doc_id = normalize_text(target.get("doc_id"))
            target_meta = docs_by_key.get((target_scope, target_doc_id))
            if target_meta is None:
                entries.append(
                    {
                        "problem": "not found",
                        "linked_page_text": linked_page_text_for_missing(target, resolved_href),
                        "linked_page_url": resolved_href,
                        "link_text": link_text,
                        "link_url": resolved_href,
                        "from_page_text": from_page_text,
                        "from_page_url": from_page_url,
                    }
                )
                continue

            if link_text and normalize_text(link_text) != normalize_text(target_meta.title):
                entries.append(
                    {
                        "problem": "wrong title",
                        "linked_page_text": target_meta.title,
                        "linked_page_url": target_meta.viewer_url,
                        "link_text": link_text,
                        "link_url": resolved_href,
                        "from_page_text": from_page_text,
                        "from_page_url": from_page_url,
                    }
                )

    entries.sort(
        key=lambda item: (
            item["problem"],
            item["from_page_text"].lower(),
            item["linked_page_text"].lower(),
            item["link_text"].lower(),
        )
    )

    not_found_count = sum(1 for item in entries if item["problem"] == "not found")
    wrong_title_count = sum(1 for item in entries if item["problem"] == "wrong title")

    return {
        "ok": True,
        "scope": normalized_scope,
        "summary": {
            "total": len(entries),
            "not_found": not_found_count,
            "wrong_title": wrong_title_count,
        },
        "entries": entries,
    }


def print_human_summary(payload: dict[str, Any]) -> None:
    scope = normalize_text(payload.get("scope"))
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    total = int(summary.get("total") or 0)
    not_found = int(summary.get("not_found") or 0)
    wrong_title = int(summary.get("wrong_title") or 0)
    print(f"Docs broken links for {scope}: {total} issue(s)")
    print(f"  not found: {not_found}")
    print(f"  wrong title: {wrong_title}")
    for entry in payload.get("entries") or []:
        if not isinstance(entry, dict):
            continue
        print(
            f"- {humanize_problem(str(entry.get('problem') or ''))}: "
            f"{normalize_text(entry.get('link_text'))} -> {normalize_text(entry.get('linked_page_text'))} "
            f"(from {normalize_text(entry.get('from_page_text'))})"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit Docs Viewer links for missing targets and title mismatches.")
    parser.add_argument("--scope", required=True, help="Docs scope to audit: studio or library")
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
