#!/usr/bin/env python3
"""Export generated Docs Viewer payloads as standalone static HTML."""

from __future__ import annotations

import hashlib
import html
import json
import os
import re
import shutil
import stat as stat_module
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime
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
    resolve_location_path,
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
SNAPSHOT_SCHEMA_VERSION = "docs_static_html_snapshot_v1"
SNAPSHOT_PREVIEW_SCHEMA_VERSION = "docs_static_html_snapshot_preview_v1"
SNAPSHOT_PROVENANCE_FILENAME = "snapshot.json"
SAFE_DOC_ID_PATTERN = re.compile(r"\A[a-z0-9][a-z0-9_-]*\Z")
HREF_PATTERN = re.compile(r"""(?P<prefix>\bhref\s*=\s*)(?P<quote>["'])(?P<url>.*?)(?P=quote)""", re.IGNORECASE)
EMPTY_CONFLICT_DIR_PATTERN = re.compile(r"\A(?P<base>[A-Za-z0-9_-]+) [2-9][0-9]*\Z")
UNSAFE_FOLDER_CHARACTER_PATTERN = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
WINDOWS_RESERVED_FOLDER_NAMES = frozenset(
    {"CON", "PRN", "AUX", "NUL", *(f"COM{index}" for index in range(1, 10)), *(f"LPT{index}" for index in range(1, 10))}
)
MAX_SNAPSHOT_LABEL_BYTES = 180
DOCS_EXPORT_WORKSPACE_SUBDIR = "docs-export"


@dataclass(frozen=True)
class StaticHtmlExportPaths:
    scope: str
    generated_root: Path
    index_tree_path: Path
    payload_root: Path
    destination_root: Path


@dataclass(frozen=True)
class StaticHtmlSnapshotInputPaths:
    scope: str
    generated_root: Path
    index_tree_path: Path
    payload_root: Path


@dataclass(frozen=True)
class StaticHtmlSnapshotPlan:
    scope: str
    doc_ids: tuple[str, ...]
    selection_kind: str
    default_doc_id: str
    export_date: str
    folder_name: str
    destination_root: Path
    destination_label: str
    index_tree: dict[str, Any]
    doc_payloads: dict[str, dict[str, Any]]
    plan_revision: str
    target_state: str
    target_revision: str
    existing_snapshot: dict[str, Any] | None


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


def normalize_snapshot_scope(repo_root: Path, value: Any) -> tuple[str, DocsScopeConfig]:
    """Resolve one configured snapshot scope without imposing source ownership policy."""

    scope = str(value or "").strip().lower()
    if not scope:
        raise ValueError("scope is required")
    config = load_docs_scope_configs(repo_root, scope_ids=(scope,)).get(scope)
    if config is None:
        raise ValueError(f"unsupported docs scope: {scope}")
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
        raise FileNotFoundError(f"index-tree.json not found for scope {scope}")
    if not payload_root.is_dir():
        raise FileNotFoundError(f"by-id payload root not found for scope {scope}")

    destination_root = resolve_workspace_path(resolve_docs_export_workspace(), scope)
    validate_destination_path(destination_root)
    return StaticHtmlExportPaths(
        scope=scope,
        generated_root=generated_root,
        index_tree_path=index_tree_path,
        payload_root=payload_root,
        destination_root=destination_root,
    )


def resolve_snapshot_input_paths(
    repo_root: Path,
    scope: str,
    config: DocsScopeConfig,
) -> StaticHtmlSnapshotInputPaths:
    """Resolve readable generated inputs for any configured filesystem scope."""

    generated_root = resolve_location_path(repo_root, config.published.documents.location)
    index_tree_path = generated_root / "index-tree.json"
    payload_root = generated_root / "by-id"
    if not index_tree_path.is_file():
        raise FileNotFoundError(f"index-tree.json not found for scope {scope}: {index_tree_path}")
    if not payload_root.is_dir():
        raise FileNotFoundError(f"by-id payload root not found for scope {scope}: {payload_root}")
    return StaticHtmlSnapshotInputPaths(
        scope=scope,
        generated_root=generated_root,
        index_tree_path=index_tree_path,
        payload_root=payload_root,
    )


def resolve_scope_export_destination(scope: str) -> Path:
    destination_root = resolve_workspace_path(resolve_docs_export_workspace(), scope)
    validate_destination_path(destination_root)
    return destination_root


def validate_destination_path(path: Path) -> None:
    base = resolve_docs_export_workspace().root.resolve()
    resolved_parent = path.parent.resolve()
    if resolved_parent != base:
        raise ValueError(f"export destination must be under {base}")
    if path.name in {"", ".", ".."}:
        raise ValueError("export destination must include a snapshot folder")


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


def normalize_snapshot_doc_ids(value: Any, available_doc_ids: list[str]) -> tuple[str, ...]:
    """Validate exact checked IDs and return them in generated tree order."""

    if not isinstance(value, list) or not value:
        raise ValueError("doc_ids must be a non-empty array")
    requested: list[str] = []
    seen: set[str] = set()
    for item in value:
        doc_id = validate_doc_id_for_html_filename(str(item or "").strip())
        if doc_id in seen:
            raise ValueError(f"duplicate doc_id in snapshot selection: {doc_id}")
        seen.add(doc_id)
        requested.append(doc_id)
    available = set(available_doc_ids)
    unknown = sorted(set(requested) - available)
    if unknown:
        raise ValueError(f"doc_ids are not in the active generated scope: {', '.join(unknown)}")
    requested_set = set(requested)
    return tuple(doc_id for doc_id in available_doc_ids if doc_id in requested_set)


def filter_index_tree_rows(rows: Any, included_doc_ids: set[str]) -> list[dict[str, Any]]:
    """Keep exact selected rows, promoting selected children of omitted parents."""

    result: list[dict[str, Any]] = []
    if not isinstance(rows, list):
        return result
    for row in rows:
        if not isinstance(row, dict):
            continue
        selected_children = filter_index_tree_rows(row.get("children"), included_doc_ids)
        doc_id = str(row.get("doc_id") or "").strip()
        if doc_id in included_doc_ids:
            selected_row = {key: item for key, item in row.items() if key != "children"}
            if selected_children:
                selected_row["children"] = selected_children
            result.append(selected_row)
        else:
            result.extend(selected_children)
    return result


def _truncate_utf8(value: str, byte_limit: int) -> str:
    encoded = value.encode("utf-8")
    if len(encoded) <= byte_limit:
        return value
    return encoded[:byte_limit].decode("utf-8", errors="ignore").rstrip(" .")


def normalize_snapshot_folder_label(value: Any) -> str:
    """Return a portable, deterministic snapshot folder base label."""

    label = unicodedata.normalize("NFC", str(value or ""))
    label = UNSAFE_FOLDER_CHARACTER_PATTERN.sub("-", label)
    label = re.sub(r"\s+", " ", label).strip(" .")
    if not label or label in {".", ".."}:
        label = "snapshot"
    if label.split(".", 1)[0].upper() in WINDOWS_RESERVED_FOLDER_NAMES:
        label = f"{label} snapshot"
    return _truncate_utf8(label, MAX_SNAPSHOT_LABEL_BYTES) or "snapshot"


def snapshot_folder_name(base_label: Any, export_date: date) -> str:
    return f"{normalize_snapshot_folder_label(base_label)} - {export_date.isoformat()}"


def snapshot_selection_kind(doc_ids: tuple[str, ...], available_doc_ids: list[str]) -> str:
    if len(doc_ids) == len(available_doc_ids):
        return "complete"
    if len(doc_ids) == 1:
        return "single"
    return "partial"


def _revision(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _file_sha256(path: Path, initial_stat: os.stat_result) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    final_stat = path.lstat()
    if _stat_identity(final_stat) != _stat_identity(initial_stat):
        raise ValueError("export destination changed during preview; preview again")
    return digest.hexdigest()


def _stat_identity(path_stat: os.stat_result) -> tuple[int, int, int, int, int, int]:
    return (
        path_stat.st_mode,
        path_stat.st_size,
        path_stat.st_mtime_ns,
        path_stat.st_ctime_ns,
        path_stat.st_dev,
        path_stat.st_ino,
    )


def _target_entry_state(path: Path, relative_path: Path) -> list[dict[str, Any]]:
    path_stat = path.lstat()
    common = {
        "path": relative_path.as_posix() if relative_path.parts else ".",
        "mode": path_stat.st_mode,
        "size": path_stat.st_size,
        "mtime_ns": path_stat.st_mtime_ns,
        "ctime_ns": path_stat.st_ctime_ns,
        "device": path_stat.st_dev,
        "inode": path_stat.st_ino,
    }
    if path.is_symlink():
        target = os.readlink(path)
        if _stat_identity(path.lstat()) != _stat_identity(path_stat):
            raise ValueError("export destination changed during preview; preview again")
        return [{**common, "kind": "symlink", "target": target}]
    if stat_module.S_ISDIR(path_stat.st_mode):
        entries = [{**common, "kind": "directory"}]
        for child in sorted(path.iterdir(), key=lambda item: item.name):
            entries.extend(_target_entry_state(child, relative_path / child.name))
        if _stat_identity(path.lstat()) != _stat_identity(path_stat):
            raise ValueError("export destination changed during preview; preview again")
        return entries
    if stat_module.S_ISREG(path_stat.st_mode):
        return [{**common, "kind": "file", "sha256": _file_sha256(path, path_stat)}]
    return [{**common, "kind": "special"}]


def snapshot_target_revision(path: Path, state: str) -> str:
    if state == "absent":
        return _revision({"state": state})
    try:
        entries = _target_entry_state(path, Path())
    except OSError as exc:
        raise ValueError("could not inspect export destination; resolve filesystem permissions and preview again") from exc
    return _revision({"state": state, "entries": entries})


def load_existing_snapshot_summary(destination_root: Path) -> dict[str, Any] | None:
    provenance_path = destination_root / SNAPSHOT_PROVENANCE_FILENAME
    if provenance_path.is_symlink() or not provenance_path.is_file():
        return None
    try:
        payload = json.loads(provenance_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or payload.get("schema_version") != SNAPSHOT_SCHEMA_VERSION:
            return None
        scope = validate_doc_id_for_html_filename(str(payload.get("scope") or "").strip())
        doc_ids = normalize_snapshot_doc_ids(payload.get("doc_ids"), list(payload.get("doc_ids") or []))
        selection_kind = str(payload.get("selection_kind") or "").strip()
        if selection_kind not in {"single", "partial", "complete"}:
            return None
        if selection_kind == "single" and len(doc_ids) != 1:
            return None
        if selection_kind == "partial" and len(doc_ids) < 2:
            return None
        document_count = payload.get("document_count")
        if isinstance(document_count, bool) or not isinstance(document_count, int) or document_count != len(doc_ids):
            return None
        generated_at = str(payload.get("generated_at") or "").strip()
        if not generated_at:
            return None
        generated_time = datetime.fromisoformat(generated_at)
        if generated_time.tzinfo is None or generated_time.utcoffset() is None:
            return None
    except (OSError, ValueError, json.JSONDecodeError, TypeError):
        return None
    return {
        "scope": scope,
        "selection_kind": selection_kind,
        "document_count": len(doc_ids),
        "generated_at": generated_at,
        "selection_revision": _revision({"scope": scope, "doc_ids": doc_ids}),
    }


def inspect_snapshot_destination(destination_root: Path) -> tuple[str, str, dict[str, Any] | None]:
    if not os.path.lexists(destination_root):
        state = "absent"
        return state, snapshot_target_revision(destination_root, state), None
    if destination_root.is_symlink() or not destination_root.is_dir():
        state = "non_directory"
        return state, snapshot_target_revision(destination_root, state), None
    existing_snapshot = load_existing_snapshot_summary(destination_root)
    state = "recognized" if existing_snapshot is not None else "unrecognized"
    return state, snapshot_target_revision(destination_root, state), existing_snapshot


def _snapshot_plan_revision(
    *,
    scope: str,
    doc_ids: tuple[str, ...],
    export_date: str,
    folder_name: str,
    default_doc_id: str,
    index_tree: dict[str, Any],
    doc_payloads: dict[str, dict[str, Any]],
) -> str:
    return _revision(
        {
            "scope": scope,
            "doc_ids": doc_ids,
            "export_date": export_date,
            "folder_name": folder_name,
            "default_doc_id": default_doc_id,
            "tree": index_tree.get("docs", []),
            "titles": {doc_id: str(doc_payloads[doc_id].get("title") or doc_id) for doc_id in doc_ids},
        }
    )


def plan_static_html_snapshot(
    repo_root: Path,
    body: dict[str, Any],
    *,
    export_date: date | None = None,
) -> StaticHtmlSnapshotPlan:
    """Build a write-free exact-selection snapshot plan from generated payloads."""

    for unsupported_field in ("mode", "include_descendants", "root_doc_id"):
        if unsupported_field in body:
            raise ValueError(f"{unsupported_field} is not supported for static HTML snapshots")
    if str(body.get("sub_scope") or "").strip():
        raise ValueError("sub_scope is not supported for static HTML snapshots")
    scope, config = normalize_snapshot_scope(repo_root, body.get("scope"))
    paths = resolve_snapshot_input_paths(repo_root, scope, config)
    index_tree = load_index_tree(paths.index_tree_path)
    available_doc_ids = collect_doc_ids_from_tree(index_tree.get("docs"))
    doc_ids = normalize_snapshot_doc_ids(body.get("doc_ids"), available_doc_ids)
    try:
        doc_payloads = {doc_id: load_doc_payload(paths.payload_root, doc_id) for doc_id in doc_ids}
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"selected document payload not found for scope {scope}") from exc
    included_doc_ids = set(doc_ids)
    selected_tree = {**index_tree, "docs": filter_index_tree_rows(index_tree.get("docs"), included_doc_ids)}
    selection_kind = snapshot_selection_kind(doc_ids, available_doc_ids)
    selected_date = export_date or datetime.now().astimezone().date()
    if type(selected_date) is not date:
        raise ValueError("export_date must be a date")
    if selection_kind == "single":
        base_label = str(doc_payloads[doc_ids[0]].get("title") or doc_ids[0]).strip() or doc_ids[0]
    elif selection_kind == "complete":
        base_label = scope
    else:
        base_label = f"{scope} selection"
    folder_name = snapshot_folder_name(base_label, selected_date)
    destination_root = resolve_docs_export_workspace().root / folder_name
    validate_destination_path(destination_root)
    default_doc_id = config.default_doc_id if config.default_doc_id in included_doc_ids else doc_ids[0]
    destination_label_value = f"/docs-export/{folder_name}/"
    target_state, target_revision, existing_snapshot = inspect_snapshot_destination(destination_root)
    plan_revision = _snapshot_plan_revision(
        scope=scope,
        doc_ids=doc_ids,
        export_date=selected_date.isoformat(),
        folder_name=folder_name,
        default_doc_id=default_doc_id,
        index_tree=selected_tree,
        doc_payloads=doc_payloads,
    )
    return StaticHtmlSnapshotPlan(
        scope=scope,
        doc_ids=doc_ids,
        selection_kind=selection_kind,
        default_doc_id=default_doc_id,
        export_date=selected_date.isoformat(),
        folder_name=folder_name,
        destination_root=destination_root,
        destination_label=destination_label_value,
        index_tree=selected_tree,
        doc_payloads=doc_payloads,
        plan_revision=plan_revision,
        target_state=target_state,
        target_revision=target_revision,
        existing_snapshot=existing_snapshot,
    )


def preview_static_html_export(
    repo_root: Path,
    body: dict[str, Any],
    *,
    export_date: date | None = None,
) -> dict[str, Any]:
    plan = plan_static_html_snapshot(repo_root, body, export_date=export_date)
    return {
        "ok": True,
        "schema_version": SNAPSHOT_PREVIEW_SCHEMA_VERSION,
        "operation": "preview",
        "dry_run": True,
        "scope": plan.scope,
        "doc_ids": list(plan.doc_ids),
        "document_count": len(plan.doc_ids),
        "selection_kind": plan.selection_kind,
        "default_doc_id": plan.default_doc_id,
        "export_date": plan.export_date,
        "destination_label": plan.destination_label,
        "target_state": plan.target_state,
        "replacement_required": plan.target_state in {"recognized", "unrecognized"},
        "replace_allowed": plan.target_state != "non_directory",
        "existing_snapshot": plan.existing_snapshot,
        "plan_revision": plan.plan_revision,
        "target_revision": plan.target_revision,
        "summary_text": f"Prepared a {len(plan.doc_ids)}-document snapshot preview for {plan.destination_label}.",
    }


def rewrite_internal_docs_viewer_links(
    html_text: str,
    *,
    scope: str,
    link_prefix: str,
    included_doc_ids: set[str] | None = None,
) -> str:
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
        if included_doc_ids is not None and doc_id not in included_doc_ids:
            return match.group(0)
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


def render_doc_html(
    payload: dict[str, Any],
    *,
    scope: str,
    included_doc_ids: set[str] | None = None,
) -> str:
    doc_id = validate_doc_id_for_html_filename(str(payload.get("doc_id") or ""))
    title = str(payload.get("title") or doc_id).strip() or doc_id
    content_html = str(payload.get("content_html") or "")
    content_html = rewrite_internal_docs_viewer_links(
        content_html,
        scope=scope,
        link_prefix="",
        included_doc_ids=included_doc_ids,
    )
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
