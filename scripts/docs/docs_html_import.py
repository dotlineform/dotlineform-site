#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass, field
from html import escape
from pathlib import Path
from typing import Any, Optional

from bs4 import BeautifulSoup, Comment, NavigableString, Tag


SCOPE_ROOTS = {
    "studio": Path("_docs_src"),
    "library": Path("_docs_library_src"),
}
STAGING_REL_DIR = Path("var/docs/import-staging")
BLOCK_TAGS = {
    "body",
    "section",
    "article",
    "div",
    "p",
    "ul",
    "ol",
    "li",
    "blockquote",
    "pre",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
    "details",
    "summary",
    "footer",
}
DROP_TAGS = {"head", "script", "meta", "title"}
PROMPT_META_CLASS_TOKENS = {"prompt", "meta", "shade"}
SEMANTIC_CALLOUT_CLASS_TOKENS = {"key"}
LIST_WRAPPER_CLASS_TOKENS = {"legend"}
ROWSPAN_COLSPAN_ATTRS = {"rowspan", "colspan"}
PROMPT_META_TEXT_PREFIXES = ("[prompt]", "original prompt", "follow-up")


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def escape_markdown_pipes(text: str) -> str:
    return (text or "").replace("|", r"\|")


def slugify(value: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", (value or "").strip().lower()).strip("-")
    return text or "imported-doc"


def fence_code(text: str) -> str:
    content = text.rstrip("\n")
    return f"```\n{content}\n```"


def relative_path(base: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(base.resolve()).as_posix()
    except Exception:
        return str(path)


def normalize_scope(scope: str) -> str:
    value = str(scope or "").strip().lower()
    if value not in SCOPE_ROOTS:
        raise ValueError(f"scope must be one of: {', '.join(sorted(SCOPE_ROOTS.keys()))}")
    return value


def detect_bundle_bin() -> Optional[str]:
    rbenv_bundle = Path.home() / ".rbenv" / "shims" / "bundle"
    if rbenv_bundle.exists() and os.access(rbenv_bundle, os.X_OK):
        return str(rbenv_bundle)
    return shutil.which("bundle")


@dataclass
class TextNode:
    text: str
    parent: Optional["ElementNode"] = None

    def text_content(self) -> str:
        return self.text


@dataclass
class ElementNode:
    tag: str
    attrs: dict[str, str] = field(default_factory=dict)
    children: list[Any] = field(default_factory=list)
    parent: Optional["ElementNode"] = None

    def add_child(self, child: Any) -> None:
        child.parent = self
        self.children.append(child)

    def attr(self, name: str, default: str = "") -> str:
        return self.attrs.get(name, default)

    def class_tokens(self) -> set[str]:
        raw = self.attr("class")
        return {token.strip().lower() for token in raw.split() if token.strip()}

    def text_content(self) -> str:
        return "".join(child.text_content() for child in self.children)

    def inner_html(self) -> str:
        return "".join(serialize_node(child) for child in self.children)


@dataclass
class ParsedDocument:
    root: ElementNode
    tag_counts: Counter[str]
    comment_count: int


def parse_with_bs4(source_html: str) -> ParsedDocument:
    soup = BeautifulSoup(source_html, "lxml")
    root = ElementNode(tag="#document")
    tag_counts: Counter[str] = Counter()
    comment_count = 0

    def convert(node: Any) -> Optional[Any]:
        nonlocal comment_count
        if isinstance(node, Comment):
            comment_count += 1
            return None
        if isinstance(node, NavigableString):
            text = str(node)
            if not text:
                return None
            return TextNode(text=text)
        if isinstance(node, Tag):
            tag = node.name.lower()
            attrs: dict[str, str] = {}
            for key, value in node.attrs.items():
                if isinstance(value, list):
                    attrs[key.lower()] = " ".join(str(item) for item in value)
                else:
                    attrs[key.lower()] = str(value)
            element = ElementNode(tag=tag, attrs=attrs)
            tag_counts[tag] += 1
            for child in node.children:
                converted = convert(child)
                if converted is not None:
                    element.add_child(converted)
            return element
        return None

    for child in soup.contents:
        converted = convert(child)
        if converted is not None:
            root.add_child(converted)
    return ParsedDocument(root=root, tag_counts=tag_counts, comment_count=comment_count)


def serialize_attrs(attrs: dict[str, str], *, for_svg: bool) -> str:
    kept: list[str] = []
    for key, value in attrs.items():
        if not value and key not in {"viewbox", "xmlns", "role"}:
            continue
        if key.startswith("on"):
            continue
        if key == "style" and not for_svg:
            continue
        if key in {"target", "rel", "class", "id"} and not for_svg:
            continue
        kept.append(f' {key}="{escape(value, quote=True)}"')
    return "".join(kept)


def serialize_node(node: Any, *, in_svg: bool = False) -> str:
    if isinstance(node, TextNode):
        return escape(node.text, quote=False)
    tag = node.tag
    if tag in DROP_TAGS:
        return ""
    current_in_svg = in_svg or tag == "svg"
    attrs = serialize_attrs(node.attrs, for_svg=current_in_svg)
    if tag == "img":
        return f"<img{attrs}>"
    inner = "".join(serialize_node(child, in_svg=current_in_svg) for child in node.children)
    return f"<{tag}{attrs}>{inner}</{tag}>"


def render_prompt_meta_block(text: str) -> str:
    content = escape_markdown_pipes(normalize_space(text))
    if not content:
        return ""
    return f"> {content}"


def walk(node: Any):
    yield node
    if isinstance(node, ElementNode):
        for child in node.children:
            yield from walk(child)


def find_first(node: ElementNode, tag: str) -> Optional[ElementNode]:
    for candidate in walk(node):
        if isinstance(candidate, ElementNode) and candidate.tag == tag:
            return candidate
    return None


def collect_all(node: ElementNode, tag: str) -> list[ElementNode]:
    matches: list[ElementNode] = []
    for candidate in walk(node):
        if isinstance(candidate, ElementNode) and candidate.tag == tag:
            matches.append(candidate)
    return matches


def extract_title(root: ElementNode) -> str:
    title_node = find_first(root, "title")
    if title_node:
        title_text = normalize_space(title_node.text_content())
        if title_text:
            return title_text
    h1_node = find_first(root, "h1")
    if h1_node:
        h1_text = normalize_space(h1_node.text_content())
        if h1_text:
            return h1_text
    return ""


def is_prompt_meta_node(node: ElementNode) -> bool:
    classes = node.class_tokens()
    if classes & PROMPT_META_CLASS_TOKENS:
        return True
    if any("prompt" in token or token == "meta" or token.startswith("meta-") or token.endswith("-meta") for token in classes):
        return True
    text = normalize_space(node.text_content()).lower()
    if node.tag in {"code", "pre", "div", "p", "blockquote"} and any(text.startswith(prefix) for prefix in PROMPT_META_TEXT_PREFIXES):
        return True
    return False


def is_semantic_callout_node(node: ElementNode) -> bool:
    classes = node.class_tokens()
    return bool(classes & SEMANTIC_CALLOUT_CLASS_TOKENS)


def render_inline(node: Any) -> str:
    if isinstance(node, TextNode):
        return escape_markdown_pipes(node.text)
    tag = node.tag
    if tag in {"strong", "b"}:
        return f"**{''.join(render_inline(child) for child in node.children).strip()}**"
    if tag in {"em", "i"}:
        return f"*{''.join(render_inline(child) for child in node.children).strip()}*"
    if tag == "code":
        return f"`{normalize_space(node.text_content())}`"
    if tag in {"sub", "sup"}:
        return serialize_node(node)
    if tag == "a":
        text = normalize_space("".join(render_inline(child) for child in node.children)) or escape_markdown_pipes(node.attr("href"))
        href = node.attr("href")
        if href:
            return f"[{text}]({href})"
        return text
    if tag == "br":
        return "\n"
    if tag == "img":
        src = node.attr("src")
        alt = normalize_space(node.attr("alt"))
        if src.startswith("http://") or src.startswith("https://"):
            return f"![{alt}]({src})" if alt else src
        if src.startswith("data:"):
            return f"![{alt}]({src})" if alt else src
        return src or alt
    if tag == "svg":
        return serialize_node(node)
    return "".join(render_inline(child) for child in node.children)


def has_rowspan_or_colspan(table: ElementNode) -> bool:
    for candidate in walk(table):
        if isinstance(candidate, ElementNode):
            if any(attr in ROWSPAN_COLSPAN_ATTRS for attr in candidate.attrs):
                return True
    return False


def extract_table_rows(table: ElementNode) -> list[list[str]]:
    rows: list[list[str]] = []
    for tr in collect_all(table, "tr"):
        cells: list[str] = []
        for child in tr.children:
            if isinstance(child, ElementNode) and child.tag in {"th", "td"}:
                cells.append(normalize_space("".join(render_inline(grand) for grand in child.children)))
        if cells:
            rows.append(cells)
    return rows


def render_table(table: ElementNode, warnings: list[str]) -> str:
    if has_rowspan_or_colspan(table):
        warnings.append("Complex table kept as plain text because rowspan/colspan is unsupported in v1.")
        return escape_markdown_pipes(normalize_space(table.text_content()))
    rows = extract_table_rows(table)
    if not rows:
        return ""
    column_count = max(len(row) for row in rows)
    normalized_rows = [row + [""] * (column_count - len(row)) for row in rows]
    header = normalized_rows[0]
    body = normalized_rows[1:] if len(normalized_rows) > 1 else []
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in header) + " |",
    ]
    for row in body:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def render_list(node: ElementNode, warnings: list[str], indent: int = 0, ordered: bool = False) -> list[str]:
    lines: list[str] = []
    index = 1
    for child in node.children:
        if not isinstance(child, ElementNode) or child.tag != "li":
            continue
        prefix = f"{index}." if ordered else "-"
        segments: list[str] = []
        nested_blocks: list[str] = []
        for grand in child.children:
            if isinstance(grand, ElementNode) and grand.tag in {"ul", "ol"}:
                nested_blocks.append(
                    "\n".join(
                        render_list(
                            grand,
                            warnings,
                            indent=indent + 2,
                            ordered=(grand.tag == "ol"),
                        )
                    )
                )
            else:
                segments.append(render_inline(grand))
        line = (" " * indent) + f"{prefix} {normalize_space(''.join(segments))}".rstrip()
        lines.append(line)
        if nested_blocks:
            lines.extend(block for block in nested_blocks if block)
        index += 1
    return [line for line in lines if line.strip()]


def render_block(node: Any, warnings: list[str], include_prompt_meta: bool) -> str:
    if isinstance(node, TextNode):
        return escape_markdown_pipes(normalize_space(node.text))
    tag = node.tag
    if tag in DROP_TAGS:
        return ""
    if tag == "style" and node.parent and node.parent.tag != "svg":
        return ""
    if is_prompt_meta_node(node):
        if not include_prompt_meta:
            return ""
        return render_prompt_meta_block(node.text_content())
    if tag in {"body", "section", "article"}:
        return "\n\n".join(part for part in (render_block(child, warnings, include_prompt_meta) for child in node.children) if part)
    if tag == "div":
        if is_semantic_callout_node(node):
            content = normalize_space("".join(render_inline(child) for child in node.children))
            return f"> {content}" if content else ""
        if node.class_tokens() & LIST_WRAPPER_CLASS_TOKENS:
            items = [normalize_space("".join(render_inline(child) for child in node.children))]
            text = ", ".join(item for item in items if item)
            return text
        return "\n\n".join(part for part in (render_block(child, warnings, include_prompt_meta) for child in node.children) if part)
    if tag == "footer":
        return "\n\n".join(part for part in (render_block(child, warnings, include_prompt_meta) for child in node.children) if part)
    if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
        level = int(tag[1])
        text = normalize_space("".join(render_inline(child) for child in node.children))
        return f"{'#' * level} {text}" if text else ""
    if tag == "p":
        return normalize_space("".join(render_inline(child) for child in node.children))
    if tag == "blockquote":
        inner = normalize_space("".join(render_inline(child) for child in node.children))
        return "\n".join(f"> {line}".rstrip() for line in inner.splitlines() if line.strip())
    if tag == "pre":
        return fence_code(node.text_content())
    if tag == "ul":
        return "\n".join(render_list(node, warnings, ordered=False))
    if tag == "ol":
        return "\n".join(render_list(node, warnings, ordered=True))
    if tag == "details":
        summary = next((child for child in node.children if isinstance(child, ElementNode) and child.tag == "summary"), None)
        parts: list[str] = []
        if summary:
            summary_text = normalize_space("".join(render_inline(child) for child in summary.children))
            if summary_text:
                parts.append(f"### {summary_text}")
        for child in node.children:
            if child is summary:
                continue
            rendered = render_block(child, warnings, include_prompt_meta)
            if rendered:
                parts.append(rendered)
        return "\n\n".join(parts)
    if tag == "summary":
        return ""
    if tag == "table":
        return render_table(node, warnings)
    if tag == "svg":
        return serialize_node(node)
    if tag == "img":
        return render_inline(node)
    return "\n\n".join(part for part in (render_block(child, warnings, include_prompt_meta) for child in node.children) if part)


def build_summary(root: ElementNode, *, source_html: str, title: str, include_prompt_meta: bool) -> dict[str, Any]:
    warnings: list[str] = []
    body = find_first(root, "body") or root
    markdown = render_block(body, warnings, include_prompt_meta=include_prompt_meta).strip()
    links = []
    images = []
    svg_count = 0
    prompt_meta_blocks = 0
    semantic_callouts = 0
    details_count = 0
    for node in walk(root):
        if not isinstance(node, ElementNode):
            continue
        if node.tag == "a" and node.attr("href"):
            links.append(node.attr("href"))
        if node.tag == "img" and node.attr("src"):
            images.append(node.attr("src"))
        if node.tag == "svg":
            svg_count += 1
        if node.tag == "details":
            details_count += 1
        if is_prompt_meta_node(node):
            prompt_meta_blocks += 1
        if is_semantic_callout_node(node):
            semantic_callouts += 1
    title_source = "title" if find_first(root, "title") and normalize_space(find_first(root, "title").text_content()) else ("h1" if find_first(root, "h1") else "fallback")
    return {
        "title": title or "Imported Doc",
        "title_source": title_source,
        "proposed_doc_id": slugify(title or "Imported Doc"),
        "source_stats": {
            "chars": len(source_html),
            "links": len(links),
            "images": len(images),
            "svg": svg_count,
            "details": details_count,
            "prompt_meta_blocks": prompt_meta_blocks,
            "semantic_callouts": semantic_callouts,
        },
        "image_summary": {
            "external": sum(1 for src in images if src.startswith("http://") or src.startswith("https://")),
            "data_urls": sum(1 for src in images if src.startswith("data:")),
            "repo_local_or_other": sum(1 for src in images if not (src.startswith("http://") or src.startswith("https://") or src.startswith("data:"))),
        },
        "warnings": warnings,
        "markdown_preview": markdown,
    }


def validate_markdown_with_jekyll(repo_root: Path, markdown: str) -> dict[str, Any]:
    renderer_script = repo_root / "scripts" / "render_markdown_with_jekyll.rb"
    if not renderer_script.exists():
        raise RuntimeError(f"Markdown renderer helper not found: {relative_path(repo_root, renderer_script)}")

    bundle_bin = detect_bundle_bin()
    if not bundle_bin:
        raise RuntimeError("Bundler not found; ensure the local Jekyll toolchain is available before validating imported Markdown.")

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md", delete=False) as handle:
        handle.write(markdown)
        handle.write("\n")
        temp_path = Path(handle.name)

    try:
        completed = subprocess.run(
            [bundle_bin, "exec", "ruby", str(renderer_script), str(temp_path)],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        try:
            temp_path.unlink()
        except OSError:
            pass

    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip() or f"exit {completed.returncode}"
        raise RuntimeError(f"Jekyll Markdown validation failed: {detail}")

    return {
        "ok": True,
        "html_chars": len(completed.stdout),
        "renderer": "scripts/render_markdown_with_jekyll.rb",
    }


def resolve_staged_html(repo_root: Path, staged_filename: str) -> Path:
    filename = str(staged_filename or "").strip()
    if not filename:
        raise ValueError("staged_filename is required")
    path = (repo_root / STAGING_REL_DIR / filename).resolve()
    staging_root = (repo_root / STAGING_REL_DIR).resolve()
    if staging_root not in [path, *path.parents]:
        raise ValueError(f"staged file must resolve inside {STAGING_REL_DIR.as_posix()}")
    if not path.exists():
        raise FileNotFoundError(f"staged HTML does not exist: {filename}")
    return path


def list_staged_html_files(repo_root: Path) -> list[dict[str, Any]]:
    staging_root = (repo_root / STAGING_REL_DIR).resolve()
    if not staging_root.exists():
        return []
    files: list[dict[str, Any]] = []
    for path in sorted(staging_root.glob("*.html")):
        stat = path.stat()
        files.append(
            {
                "filename": path.name,
                "path": relative_path(repo_root, path),
                "size_bytes": stat.st_size,
                "modified_utc": dt.datetime.fromtimestamp(stat.st_mtime, tz=dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
        )
    return files


def generate_import_preview(
    repo_root: Path,
    *,
    source_path: Path,
    scope: str,
    include_prompt_meta: bool,
) -> dict[str, Any]:
    normalized_scope = normalize_scope(scope)
    source_html = source_path.read_text(encoding="utf-8", errors="replace")
    parsed = parse_with_bs4(source_html)
    title = extract_title(parsed.root)
    summary = build_summary(
        parsed.root,
        source_html=source_html,
        title=title,
        include_prompt_meta=include_prompt_meta,
    )
    summary["scope"] = normalized_scope
    summary["source_html"] = relative_path(repo_root, source_path)
    summary["staging_root"] = STAGING_REL_DIR.as_posix()
    summary["tag_counts"] = dict(parsed.tag_counts.most_common())
    summary["comment_count"] = parsed.comment_count
    summary["jekyll_validation"] = validate_markdown_with_jekyll(repo_root, summary["markdown_preview"])
    return summary


def detect_repo_root(explicit_root: str) -> Path:
    if explicit_root:
        root = Path(explicit_root).expanduser().resolve()
        if not (root / "_config.yml").exists():
            raise SystemExit(f"--repo-root does not look like repo root (missing _config.yml): {root}")
        return root
    for candidate in [Path.cwd(), Path(__file__).resolve().parent]:
        current = candidate.resolve()
        for parent in [current, *current.parents]:
            if (parent / "_config.yml").exists():
                return parent
    raise SystemExit("Could not auto-detect repo root. Pass --repo-root.")


def resolve_source_html(repo_root: Path, args: argparse.Namespace) -> Path:
    if args.source_html:
        path = Path(args.source_html).expanduser().resolve()
        if not path.exists():
            raise SystemExit(f"Source HTML does not exist: {path}")
        return path
    if args.staged_filename:
        try:
            return resolve_staged_html(repo_root, args.staged_filename)
        except (FileNotFoundError, ValueError) as exc:
            raise SystemExit(str(exc)) from exc
    raise SystemExit("Pass either --source-html or --staged-filename.")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dry-run HTML import conversion for Docs Viewer source docs.")
    parser.add_argument("--repo-root", default="", help="Override repo root auto-detection.")
    parser.add_argument("--source-html", default="", help="Import directly from an HTML file path.")
    parser.add_argument("--staged-filename", default="", help="Import from var/docs/import-staging/<filename>.")
    parser.add_argument("--scope", default="studio", choices=sorted(SCOPE_ROOTS.keys()), help="Target docs scope.")
    parser.add_argument("--include-prompt-meta", action="store_true", help="Include clearly identifiable prompt/meta blocks.")
    parser.add_argument("--markdown-preview-out", default="", help="Optional path to write the Markdown preview.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = detect_repo_root(args.repo_root)
    source_path = resolve_source_html(repo_root, args)
    summary = generate_import_preview(
        repo_root,
        source_path=source_path,
        scope=args.scope,
        include_prompt_meta=bool(args.include_prompt_meta),
    )

    if args.markdown_preview_out:
        output_path = Path(args.markdown_preview_out).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(summary["markdown_preview"] + "\n", encoding="utf-8")
        summary["markdown_preview_out"] = str(output_path)

    json.dump(summary, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
