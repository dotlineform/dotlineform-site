#!/usr/bin/env python3
"""Export generated Docs Viewer payloads as standalone static HTML."""

from __future__ import annotations

import html
import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

from docs_scope_config import (
    LOCAL_EXTERNAL_SCOPE_TYPE,
    DocsScopeConfig,
    published_documents_path,
    is_public_readonly_scope,
    load_docs_scope_configs,
    path_is_relative_to,
    resolve_scope_path,
    scope_uses_external_data,
)
from studio.shared.python.external_workspace_paths import (
    ExternalWorkspaceRoot,
    PROJECTS_BASE_DIR_ENV,
    resolve_external_workspace_root,
    resolve_workspace_path,
)


EXPORT_SCHEMA_VERSION = "docs_static_html_export_v1"
SAFE_DOC_ID_PATTERN = re.compile(r"\A[a-z0-9][a-z0-9_-]*\Z")
HREF_PATTERN = re.compile(r"""(?P<prefix>\bhref\s*=\s*)(?P<quote>["'])(?P<url>.*?)(?P=quote)""", re.IGNORECASE)
EMPTY_CONFLICT_DIR_PATTERN = re.compile(r"\A(?P<base>[A-Za-z0-9_-]+) [2-9][0-9]*\Z")
DOCS_EXPORT_WORKSPACE_SUBDIR = "docs-export"


@dataclass(frozen=True)
class StaticHtmlExportPaths:
    scope: str
    generated_root: Path
    index_tree_path: Path
    payload_root: Path
    destination_root: Path


def normalize_export_scope(repo_root: Path, value: Any) -> tuple[str, DocsScopeConfig]:
    scope = str(value or "").strip().lower()
    if not scope:
        raise ValueError("scope is required")
    config = load_docs_scope_configs(repo_root).get(scope)
    if config is None:
        raise ValueError(f"unsupported docs scope: {scope}")
    if config.scope_type == LOCAL_EXTERNAL_SCOPE_TYPE or scope_uses_external_data(config):
        raise ValueError(f"scope {scope!r} is not a repo-backed local scope")
    if is_public_readonly_scope(
        viewer_base_url=config.viewer_base_url,
        include_scope_param=config.include_scope_param,
    ):
        raise ValueError(f"scope {scope!r} is not a repo-backed local scope")
    if config.scope_type != "local" or not config.include_scope_param:
        raise ValueError(f"scope {scope!r} is not a repo-backed local scope")
    return scope, config


def resolve_docs_export_workspace() -> ExternalWorkspaceRoot:
    try:
        return resolve_external_workspace_root(DOCS_EXPORT_WORKSPACE_SUBDIR, require_exists=False)
    except ValueError as exc:
        if f"{PROJECTS_BASE_DIR_ENV} is required" in str(exc):
            raise ValueError(f"{PROJECTS_BASE_DIR_ENV} is required for static HTML export") from exc
        raise


def resolve_projects_base_dir() -> Path:
    return resolve_docs_export_workspace().projects_base


def resolve_repo_backed_scope_input_paths(repo_root: Path, scope: str, config: DocsScopeConfig) -> StaticHtmlExportPaths:
    generated_root = resolve_scope_path(repo_root, published_documents_path(config)).resolve()
    repo_resolved = repo_root.resolve()
    if not path_is_relative_to(generated_root, repo_resolved):
        raise ValueError(f"scope {scope!r} generated output is not repo-backed")
    index_tree_path = generated_root / "index-tree.json"
    payload_root = generated_root / "by-id"
    if not index_tree_path.is_file():
        raise FileNotFoundError(f"index-tree.json not found for scope {scope}: {index_tree_path}")
    if not payload_root.is_dir():
        raise FileNotFoundError(f"by-id payload root not found for scope {scope}: {payload_root}")

    destination_root = resolve_workspace_path(resolve_docs_export_workspace(), scope)
    validate_destination_path(destination_root)
    return StaticHtmlExportPaths(
        scope=scope,
        generated_root=generated_root,
        index_tree_path=index_tree_path,
        payload_root=payload_root,
        destination_root=destination_root,
    )


def resolve_scope_export_destination(scope: str) -> Path:
    destination_root = resolve_workspace_path(resolve_docs_export_workspace(), scope)
    validate_destination_path(destination_root)
    return destination_root


def validate_destination_path(path: Path) -> None:
    resolved = path.resolve()
    base = resolve_docs_export_workspace().root
    if not path_is_relative_to(resolved, base):
        raise ValueError(f"export destination must be under {base}")
    if resolved == resolved.parent:
        raise ValueError("export destination must not be the filesystem root")
    if len(resolved.parts) < len(base.parts) + 1:
        raise ValueError("export destination must include a scope folder")


def load_index_tree(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("index-tree.json must contain a JSON object")
    if not isinstance(payload.get("docs"), list):
        raise ValueError("index-tree.json must contain docs array")
    return payload


def validate_doc_id_for_html_filename(doc_id: str) -> str:
    value = str(doc_id or "").strip()
    if not SAFE_DOC_ID_PATTERN.fullmatch(value):
        raise ValueError(f"doc_id is not a safe HTML filename: {value!r}")
    return value


def collect_doc_ids_from_tree(rows: Any) -> list[str]:
    doc_ids: list[str] = []

    def walk(items: Any) -> None:
        if not isinstance(items, list):
            return
        for item in items:
            if not isinstance(item, dict):
                continue
            doc_id = str(item.get("doc_id") or "").strip()
            if doc_id:
                doc_ids.append(validate_doc_id_for_html_filename(doc_id))
            walk(item.get("children"))

    walk(rows)
    seen: set[str] = set()
    ordered: list[str] = []
    for doc_id in doc_ids:
        if doc_id in seen:
            raise ValueError(f"duplicate doc_id in index tree: {doc_id}")
        seen.add(doc_id)
        ordered.append(doc_id)
    return ordered


def load_doc_payload(payload_root: Path, doc_id: str) -> dict[str, Any]:
    safe_doc_id = validate_doc_id_for_html_filename(doc_id)
    path = payload_root / f"{safe_doc_id}.json"
    if not path.is_file():
        raise FileNotFoundError(f"doc payload not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"doc payload must contain a JSON object: {safe_doc_id}")
    payload_doc_id = str(payload.get("doc_id") or safe_doc_id).strip()
    if payload_doc_id != safe_doc_id:
        raise ValueError(f"doc payload id mismatch for {safe_doc_id}: {payload_doc_id}")
    return payload


def rewrite_internal_docs_viewer_links(html_text: str, *, scope: str, link_prefix: str) -> str:
    def replacement(match: re.Match[str]) -> str:
        raw_url = html.unescape(match.group("url"))
        split = urlsplit(raw_url)
        if split.scheme or split.netloc or split.path != "/docs/":
            return match.group(0)
        params = parse_qs(split.query, keep_blank_values=True)
        if (params.get("scope") or [""])[0] != scope:
            return match.group(0)
        doc_id = (params.get("doc") or [""])[0]
        if not doc_id:
            return match.group(0)
        validate_doc_id_for_html_filename(doc_id)
        rewritten = f"{link_prefix}{doc_id}.html"
        if split.fragment:
            rewritten += f"#{split.fragment}"
        quote = match.group("quote")
        return f"{match.group('prefix')}{quote}{html.escape(rewritten, quote=True)}{quote}"

    return HREF_PATTERN.sub(replacement, html_text)


def render_styles_css() -> str:
    return """\
:root {
  color-scheme: light;
  --page-bg: #f8f8f5;
  --text: #222;
  --muted: #64635e;
  --border: #d9d6cf;
  --link: #1f5f8f;
  --code-bg: #ece9e1;
}

body {
  margin: 0;
  background: var(--page-bg);
  color: var(--text);
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  line-height: 1.55;
}

nav,
main {
  width: min(920px, calc(100% - 32px));
  margin: 0 auto;
}

nav {
  padding: 18px 0 0;
}

main {
  padding: 28px 0 56px;
}

a {
  color: var(--link);
}

h1,
h2,
h3 {
  line-height: 1.2;
}

pre {
  overflow-x: auto;
  padding: 14px;
  border: 1px solid var(--border);
  background: var(--code-bg);
}

code {
  background: var(--code-bg);
  padding: 0.1em 0.25em;
}

pre code {
  padding: 0;
}

.docsExport__tree {
  padding-left: 1.25rem;
}

.docsExport__tree li {
  margin: 0.3rem 0;
}

.docsExport__meta {
  color: var(--muted);
}
"""


def render_tree_rows(rows: Any) -> str:
    if not isinstance(rows, list) or not rows:
        return ""
    parts = ['<ul class="docsExport__tree">']
    for row in rows:
        if not isinstance(row, dict):
            continue
        doc_id = validate_doc_id_for_html_filename(str(row.get("doc_id") or ""))
        title = str(row.get("title") or doc_id).strip() or doc_id
        parts.append(
            f'<li><a href="docs/{html.escape(doc_id, quote=True)}.html">{html.escape(title)}</a>'
        )
        child_html = render_tree_rows(row.get("children"))
        if child_html:
            parts.append(child_html)
        parts.append("</li>")
    parts.append("</ul>")
    return "".join(parts)


def render_index_html(index_tree: dict[str, Any], *, scope: str, default_doc_id: str, document_count: int) -> str:
    title = f"{scope} docs"
    default_html = ""
    if default_doc_id:
        safe_default = validate_doc_id_for_html_filename(default_doc_id)
        default_html = (
            f'<p class="docsExport__meta">Default document: '
            f'<a href="docs/{html.escape(safe_default, quote=True)}.html">{html.escape(safe_default)}</a></p>'
        )
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '  <meta charset="utf-8">',
            '  <meta name="viewport" content="width=device-width, initial-scale=1">',
            f"  <title>{html.escape(title)}</title>",
            '  <link rel="stylesheet" href="styles.css">',
            "</head>",
            "<body>",
            "  <main>",
            f"    <h1>{html.escape(title)}</h1>",
            f'    <p class="docsExport__meta">{document_count} documents exported from generated Docs Viewer payloads.</p>',
            f"    {default_html}",
            f"    {render_tree_rows(index_tree.get('docs'))}",
            "  </main>",
            "</body>",
            "</html>",
            "",
        ]
    )


def render_doc_html(payload: dict[str, Any], *, scope: str) -> str:
    doc_id = validate_doc_id_for_html_filename(str(payload.get("doc_id") or ""))
    title = str(payload.get("title") or doc_id).strip() or doc_id
    content_html = str(payload.get("content_html") or "")
    content_html = rewrite_internal_docs_viewer_links(content_html, scope=scope, link_prefix="")
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '  <meta charset="utf-8">',
            '  <meta name="viewport" content="width=device-width, initial-scale=1">',
            f"  <title>{html.escape(title)}</title>",
            '  <link rel="stylesheet" href="../styles.css">',
            "</head>",
            "<body>",
            '  <nav><a href="../index.html">Index</a></nav>',
            "  <main>",
            f"    {content_html}",
            "  </main>",
            "</body>",
            "</html>",
            "",
        ]
    )


def compute_replace_plan(
    *,
    paths: StaticHtmlExportPaths,
    index_tree: dict[str, Any],
    doc_payloads: dict[str, dict[str, Any]],
    default_doc_id: str,
) -> dict[Path, bytes]:
    doc_ids = list(doc_payloads)
    files: dict[Path, bytes] = {
        Path("index.html"): render_index_html(
            index_tree,
            scope=paths.scope,
            default_doc_id=default_doc_id,
            document_count=len(doc_ids),
        ).encode("utf-8"),
        Path("styles.css"): render_styles_css().encode("utf-8"),
    }
    for doc_id, payload in doc_payloads.items():
        files[Path("docs") / f"{doc_id}.html"] = render_doc_html(payload, scope=paths.scope).encode("utf-8")
    return files


def wipe_and_write_destination(destination_root: Path, files: dict[Path, bytes]) -> None:
    if destination_root.exists():
        if not destination_root.is_dir():
            raise ValueError(f"export destination exists and is not a directory: {destination_root}")
        shutil.rmtree(destination_root)
    destination_root.mkdir(parents=True, exist_ok=True)
    for relative_path, content in files.items():
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise ValueError(f"unsafe export output path: {relative_path}")
        target_path = destination_root / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(content)


def remove_empty_conflict_dirs(destination_root: Path, canonical_dir_names: set[str]) -> list[str]:
    if not destination_root.is_dir():
        return []
    removed: list[str] = []
    for child in sorted(destination_root.iterdir(), key=lambda item: item.name):
        if not child.is_dir():
            continue
        match = EMPTY_CONFLICT_DIR_PATTERN.fullmatch(child.name)
        if not match or match.group("base") not in canonical_dir_names:
            continue
        try:
            child.rmdir()
        except OSError:
            continue
        removed.append(child.name)
    return removed


def destination_label(scope: str) -> str:
    return f"/docs-export/{scope}/"


def build_static_html_export(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    if str(body.get("action") or "").strip() != "export":
        raise ValueError("action must be export")
    scope, config = normalize_export_scope(repo_root, body.get("scope"))
    paths = resolve_repo_backed_scope_input_paths(repo_root, scope, config)
    index_tree = load_index_tree(paths.index_tree_path)
    doc_ids = collect_doc_ids_from_tree(index_tree.get("docs"))
    doc_payloads = {doc_id: load_doc_payload(paths.payload_root, doc_id) for doc_id in doc_ids}
    files = compute_replace_plan(
        paths=paths,
        index_tree=index_tree,
        doc_payloads=doc_payloads,
        default_doc_id=config.default_doc_id,
    )
    wipe_and_write_destination(paths.destination_root, files)
    cleaned_empty_conflict_dirs = remove_empty_conflict_dirs(paths.destination_root, {"docs"})
    return {
        "ok": True,
        "schema_version": EXPORT_SCHEMA_VERSION,
        "action": "export",
        "operation": "apply",
        "scope": scope,
        "document_count": len(doc_ids),
        "file_count": len(files),
        "cleaned_empty_conflict_dirs": cleaned_empty_conflict_dirs,
        "default_doc_id": config.default_doc_id,
        "destination": str(paths.destination_root),
        "destination_label": destination_label(scope),
        "summary_text": f"Exported {len(doc_ids)} docs to {destination_label(scope)}.",
    }


def delete_static_html_export(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    scope, _config = normalize_export_scope(repo_root, body.get("scope"))
    destination_root = resolve_scope_export_destination(scope)
    deleted = destination_root.exists()
    if deleted:
        if not destination_root.is_dir():
            raise ValueError(f"export destination exists and is not a directory: {destination_root}")
        shutil.rmtree(destination_root)
    return {
        "ok": True,
        "schema_version": EXPORT_SCHEMA_VERSION,
        "action": "delete_export",
        "operation": "delete",
        "scope": scope,
        "deleted": deleted,
        "destination": str(destination_root),
        "destination_label": destination_label(scope),
        "summary_text": f"Deleted static HTML export for {scope}." if deleted else f"No static HTML export found for {scope}.",
    }


def scope_static_html_export_capability(repo_root: Path, scope: str, config: DocsScopeConfig) -> dict[str, Any]:
    try:
        normalize_export_scope(repo_root, scope)
        paths = resolve_repo_backed_scope_input_paths(repo_root, scope, config)
        index_tree = load_index_tree(paths.index_tree_path)
        doc_count = len(collect_doc_ids_from_tree(index_tree.get("docs")))
        available = True
        error = ""
    except (FileNotFoundError, ValueError) as exc:
        doc_count = 0
        available = False
        error = str(exc)
    return {
        "apply": available,
        "delete": available,
        "destination": destination_label(scope),
        "document_count": doc_count,
        "default_doc_id": config.default_doc_id,
        "error": error,
    }
