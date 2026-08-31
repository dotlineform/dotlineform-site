#!/usr/bin/env python3
"""Export generated Docs Viewer payloads as standalone static HTML."""

from __future__ import annotations

import hashlib
import hmac
import html
from html.parser import HTMLParser
import json
import os
import re
import stat as stat_module
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlsplit

from docs_static_html_export_media import SnapshotMediaPlan, plan_snapshot_media
from docs_scope_config import (
    DocsScopeConfig,
    load_docs_scope_configs,
    resolve_location_path,
)
from studio.shared.python.external_workspace_paths import (
    ExternalWorkspaceRoot,
    PROJECTS_BASE_DIR_ENV,
    resolve_external_workspace_root,
)


SNAPSHOT_SCHEMA_VERSION = "docs_static_html_snapshot_v2"
SNAPSHOT_PREVIEW_SCHEMA_VERSION = "docs_static_html_snapshot_preview_v2"
SNAPSHOT_APPLY_SCHEMA_VERSION = "docs_static_html_snapshot_apply_v2"
SNAPSHOT_PROVENANCE_FILENAME = "snapshot.json"
SAFE_DOC_ID_PATTERN = re.compile(r"\A[a-z0-9][a-z0-9_-]*\Z")
REVISION_PATTERN = re.compile(r"\A[0-9a-f]{64}\Z")
ISO_DATE_PATTERN = re.compile(r"\A[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")
HREF_PATTERN = re.compile(r"""(?P<prefix>\bhref\s*=\s*)(?P<quote>["'])(?P<url>.*?)(?P=quote)""", re.IGNORECASE)
UNSAFE_FOLDER_CHARACTER_PATTERN = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
WINDOWS_RESERVED_FOLDER_NAMES = frozenset(
    {"CON", "PRN", "AUX", "NUL", *(f"COM{index}" for index in range(1, 10)), *(f"LPT{index}" for index in range(1, 10))}
)
MAX_SNAPSHOT_LABEL_BYTES = 180
DOCS_EXPORT_WORKSPACE_SUBDIR = "docs-export"
IGNORED_HOST_METADATA_FILENAMES = frozenset({".DS_Store"})


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
    media_plan: SnapshotMediaPlan
    plan_revision: str
    target_state: str
    target_revision: str
    existing_snapshot: dict[str, Any] | None


class StaticHtmlSnapshotApplyConflict(ValueError):
    """A stale or unsafe snapshot apply that requires a fresh preview."""

    def __init__(self, message: str, *, plan: StaticHtmlSnapshotPlan | None = None) -> None:
        super().__init__(message)
        self.payload = {
            "ok": False,
            "schema_version": SNAPSHOT_APPLY_SCHEMA_VERSION,
            "operation": "apply",
            "conflict": True,
            "requires_preview": True,
            "error": message,
        }
        if plan is not None:
            self.payload.update(
                {
                    "scope": plan.scope,
                    "doc_ids": list(plan.doc_ids),
                    "destination_label": plan.destination_label,
                    "target_state": plan.target_state,
                }
            )


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


def resolve_snapshot_input_paths(
    repo_root: Path,
    scope: str,
    config: DocsScopeConfig,
) -> StaticHtmlSnapshotInputPaths:
    """Resolve readable generated inputs for any configured filesystem scope."""

    generated_root = resolve_location_path(repo_root, config.generated.documents.location)
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
    return {**payload, "doc_id": safe_doc_id}


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


def is_ignored_host_metadata(path: Path) -> bool:
    return (
        path.name in IGNORED_HOST_METADATA_FILENAMES
        and not path.is_symlink()
        and path.is_file()
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
            if is_ignored_host_metadata(child):
                continue
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
    normalized_entries = [
        {
            key: value
            for key, value in entry.items()
            if key not in {"size", "mtime_ns", "ctime_ns"} or entry.get("kind") != "directory"
        }
        for entry in entries
    ]
    return _revision({"state": state, "entries": normalized_entries})


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
        media = payload.get("media")
        external_dependencies = payload.get("external_dependencies")
        if not isinstance(media, list) or not isinstance(external_dependencies, list):
            return None
        media_count = payload.get("media_count")
        media_bytes = payload.get("media_bytes")
        external_dependency_count = payload.get("external_dependency_count")
        if (
            isinstance(media_count, bool)
            or not isinstance(media_count, int)
            or media_count != len(media)
            or isinstance(media_bytes, bool)
            or not isinstance(media_bytes, int)
            or media_bytes < 0
            or isinstance(external_dependency_count, bool)
            or not isinstance(external_dependency_count, int)
            or external_dependency_count != len(external_dependencies)
        ):
            return None
        media_sizes: list[int] = []
        selected_doc_ids = list(doc_ids)
        for item in media:
            if not isinstance(item, dict):
                return None
            media_type = str(item.get("media_type") or "")
            identity = str(item.get("identity") or "")
            packaged_path = Path(str(item.get("packaged_path") or ""))
            item_size = item.get("size")
            if (
                not SAFE_DOC_ID_PATTERN.fullmatch(media_type)
                or not identity
                or Path(identity).is_absolute()
                or ".." in Path(identity).parts
                or packaged_path != Path("media") / media_type / identity
                or not str(item.get("provider") or "").strip()
                or isinstance(item_size, bool)
                or not isinstance(item_size, int)
                or item_size < 0
                or not REVISION_PATTERN.fullmatch(str(item.get("sha256") or ""))
            ):
                return None
            normalize_snapshot_doc_ids(item.get("doc_ids"), selected_doc_ids)
            media_sizes.append(item_size)
        if media_bytes != sum(media_sizes):
            return None
        for item in external_dependencies:
            if (
                not isinstance(item, dict)
                or not str(item.get("reference") or "").strip()
                or not str(item.get("element") or "").strip()
                or not str(item.get("attribute") or "").strip()
            ):
                return None
            normalize_snapshot_doc_ids(item.get("doc_ids"), selected_doc_ids)
    except (OSError, ValueError, json.JSONDecodeError, TypeError):
        return None
    return {
        "scope": scope,
        "selection_kind": selection_kind,
        "document_count": len(doc_ids),
        "media_count": media_count,
        "media_bytes": media_bytes,
        "external_dependency_count": external_dependency_count,
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
    media_plan: SnapshotMediaPlan,
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
            "content_sha256": {
                doc_id: hashlib.sha256(str(doc_payloads[doc_id].get("content_html") or "").encode("utf-8")).hexdigest()
                for doc_id in doc_ids
            },
            "media": media_plan.manifest_records(),
            "external_dependencies": media_plan.external_dependency_records(),
        }
    )


def plan_static_html_snapshot(
    repo_root: Path,
    body: dict[str, Any],
    *,
    export_date: date | None = None,
) -> StaticHtmlSnapshotPlan:
    """Build a write-free exact-selection snapshot plan from generated payloads."""

    for unsupported_field in ("action", "mode", "include_descendants", "root_doc_id"):
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
    media_plan = plan_snapshot_media(repo_root, config, doc_payloads)
    selected_tree = {**index_tree, "docs": filter_index_tree_rows(index_tree.get("docs"), included_doc_ids)}
    selection_kind = snapshot_selection_kind(doc_ids, available_doc_ids)
    selected_date = export_date or datetime.now().astimezone().date()
    if type(selected_date) is not date:
        raise ValueError("export_date must be a date")
    if selection_kind == "complete":
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
        media_plan=media_plan,
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
        media_plan=media_plan,
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
        "media_count": len(plan.media_plan.items),
        "media_bytes": plan.media_plan.media_bytes,
        "external_dependency_count": len(plan.media_plan.external_dependencies),
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
    link_suffix: str = ".html",
    included_doc_ids: set[str] | None = None,
    preserve_fragment: bool = True,
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
        rewritten = f"{link_prefix}{doc_id}{link_suffix}"
        if split.fragment and preserve_fragment:
            rewritten += f"#{split.fragment}"
        quote = match.group("quote")
        return f"{match.group('prefix')}{quote}{html.escape(rewritten, quote=True)}{quote}"

    return HREF_PATTERN.sub(replacement, html_text)


class _PortableHtmlImageRewriter(HTMLParser):
    """Replace images while preserving every other rendered HTML event."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.parts: list[str] = []

    def image_placeholder(self, attrs: list[tuple[str, str | None]]) -> str:
        attrs_by_name = {name.lower(): str(value or "") for name, value in attrs}
        alt = " ".join(html.unescape(attrs_by_name.get("alt", "")).split())
        label = f"[image: {alt}]" if alt else "[image]"
        return f'<span class="docsExport__mediaPlaceholder">{html.escape(label)}</span>'

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "img":
            self.parts.append(self.image_placeholder(attrs))
            return
        self.parts.append(self.get_starttag_text())

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "img":
            self.parts.append(self.image_placeholder(attrs))
            return
        self.parts.append(self.get_starttag_text())

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "img":
            self.parts.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def handle_entityref(self, name: str) -> None:
        self.parts.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self.parts.append(f"&#{name};")

    def handle_comment(self, data: str) -> None:
        self.parts.append(f"<!--{data}-->")

    def handle_decl(self, decl: str) -> None:
        self.parts.append(f"<!{decl}>")

    def handle_pi(self, data: str) -> None:
        self.parts.append(f"<?{data}>")

    def unknown_decl(self, data: str) -> None:
        self.parts.append(f"<![{data}]>")


def replace_images_with_placeholders(html_text: str) -> str:
    parser = _PortableHtmlImageRewriter()
    parser.feed(html_text)
    parser.close()
    return "".join(parser.parts)


def markdown_document_link(payload: dict[str, Any], *, scope: str) -> str:
    doc_id = validate_doc_id_for_html_filename(str(payload.get("doc_id") or ""))
    title = str(payload.get("title") or doc_id).strip() or doc_id
    escaped_title = title.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")
    query = urlencode((("scope", scope), ("doc", doc_id)))
    return f"[{escaped_title}](/docs/?{query})"


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


def render_portable_styles_css() -> str:
    return render_styles_css() + """\

.docsExport__portableIndex {
  padding-bottom: 1.5rem;
  border-bottom: 1px solid var(--border);
}

.docsExport__portableDocument {
  padding-top: 1.5rem;
  scroll-margin-top: 1rem;
}

.docsExport__portableDocument + .docsExport__portableDocument {
  margin-top: 2rem;
  border-top: 1px solid var(--border);
}

.docsExport__mediaPlaceholder {
  color: var(--muted);
  font-style: italic;
}

.docsExport__referenceToken {
  margin-top: 0.35rem;
  color: var(--muted);
  font-size: 0.8rem;
  overflow-wrap: anywhere;
}
"""


def render_tree_rows(
    rows: Any,
    *,
    link_prefix: str = "docs/",
    link_suffix: str = ".html",
) -> str:
    if not isinstance(rows, list) or not rows:
        return ""
    parts = ['<ul class="docsExport__tree">']
    for row in rows:
        if not isinstance(row, dict):
            continue
        doc_id = validate_doc_id_for_html_filename(str(row.get("doc_id") or ""))
        title = str(row.get("title") or doc_id).strip() or doc_id
        target = f"{link_prefix}{doc_id}{link_suffix}"
        parts.append(
            f'<li><a href="{html.escape(target, quote=True)}">{html.escape(title)}</a>'
        )
        child_html = render_tree_rows(
            row.get("children"),
            link_prefix=link_prefix,
            link_suffix=link_suffix,
        )
        if child_html:
            parts.append(child_html)
        parts.append("</li>")
    parts.append("</ul>")
    return "".join(parts)


def render_index_html(index_tree: dict[str, Any], *, scope: str, default_doc_id: str, document_count: int) -> str:
    title = f"{scope} docs"
    document_label = "document" if document_count == 1 else "documents"
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
            f'    <p class="docsExport__meta">{document_count} {document_label} exported from generated Docs Viewer payloads.</p>',
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
    content_html_override: str | None = None,
) -> str:
    doc_id = validate_doc_id_for_html_filename(str(payload.get("doc_id") or ""))
    title = str(payload.get("title") or doc_id).strip() or doc_id
    content_html = (
        str(payload.get("content_html") or "")
        if content_html_override is None
        else content_html_override
    )
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


def render_portable_html(plan: StaticHtmlSnapshotPlan) -> str:
    included_doc_ids = set(plan.doc_ids)
    tree_html = render_tree_rows(
        plan.index_tree.get("docs"),
        link_prefix="#doc-",
        link_suffix="",
    )
    document_html: list[str] = []
    for doc_id in plan.doc_ids:
        payload = plan.doc_payloads[doc_id]
        content_html = rewrite_internal_docs_viewer_links(
            str(payload.get("content_html") or ""),
            scope=plan.scope,
            link_prefix="#doc-",
            link_suffix="",
            included_doc_ids=included_doc_ids,
            preserve_fragment=False,
        )
        document_html.extend(
            [
                f'    <article class="docsExport__portableDocument" id="doc-{html.escape(doc_id, quote=True)}">',
                f"      {replace_images_with_placeholders(content_html)}",
                '      <p class="docsExport__meta"><a href="#index">Back to index</a></p>',
                f'      <p class="docsExport__referenceToken"><code>{html.escape(markdown_document_link(payload, scope=plan.scope))}</code></p>',
                "    </article>",
            ]
        )
    document_label = "document" if len(plan.doc_ids) == 1 else "documents"
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '  <meta charset="utf-8">',
            '  <meta name="viewport" content="width=device-width, initial-scale=1">',
            f"  <title>{html.escape(plan.scope)} docs</title>",
            "  <style>",
            render_portable_styles_css(),
            "  </style>",
            "</head>",
            "<body>",
            '  <main id="index">',
            '    <section class="docsExport__portableIndex">',
            f"      <h1>{html.escape(plan.scope)} docs</h1>",
            f'      <p class="docsExport__meta">{len(plan.doc_ids)} {document_label} exported from generated Docs Viewer payloads.</p>',
            f"      {tree_html}",
            "    </section>",
            *document_html,
            "  </main>",
            "</body>",
            "</html>",
            "",
        ]
    )


def snapshot_provenance(plan: StaticHtmlSnapshotPlan, *, generated_at: str) -> dict[str, Any]:
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "scope": plan.scope,
        "doc_ids": list(plan.doc_ids),
        "selection_kind": plan.selection_kind,
        "document_count": len(plan.doc_ids),
        "media_count": len(plan.media_plan.items),
        "media_bytes": plan.media_plan.media_bytes,
        "media": plan.media_plan.manifest_records(),
        "external_dependency_count": len(plan.media_plan.external_dependencies),
        "external_dependencies": plan.media_plan.external_dependency_records(),
        "default_doc_id": plan.default_doc_id,
        "export_date": plan.export_date,
        "generated_at": generated_at,
        "plan_revision": plan.plan_revision,
    }


def compute_snapshot_files(plan: StaticHtmlSnapshotPlan, *, generated_at: str) -> dict[Path, bytes]:
    included_doc_ids = set(plan.doc_ids)
    files: dict[Path, bytes] = {
        Path("index.html"): render_index_html(
            plan.index_tree,
            scope=plan.scope,
            default_doc_id=plan.default_doc_id,
            document_count=len(plan.doc_ids),
        ).encode("utf-8"),
        Path("styles.css"): render_styles_css().encode("utf-8"),
        Path("portable.html"): render_portable_html(plan).encode("utf-8"),
        Path(SNAPSHOT_PROVENANCE_FILENAME): (
            json.dumps(snapshot_provenance(plan, generated_at=generated_at), ensure_ascii=False, indent=2) + "\n"
        ).encode("utf-8"),
    }
    for doc_id in plan.doc_ids:
        files[Path("docs") / f"{doc_id}.html"] = render_doc_html(
            plan.doc_payloads[doc_id],
            scope=plan.scope,
            included_doc_ids=included_doc_ids,
            content_html_override=plan.media_plan.rewritten_html_by_doc[doc_id],
        ).encode("utf-8")
    for item in plan.media_plan.items:
        files[item.packaged_path] = item.data
    return files


def snapshot_output_directories(files: dict[Path, bytes]) -> set[Path]:
    return {
        parent
        for relative_path in files
        for parent in relative_path.parents
        if parent.parts
    }


def clear_snapshot_output_files(
    destination_root: Path,
    retained_directories: set[Path],
) -> None:
    paths = sorted(
        destination_root.rglob("*"),
        key=lambda path: (len(path.relative_to(destination_root).parts), path.as_posix()),
        reverse=True,
    )
    for path in paths:
        relative_path = path.relative_to(destination_root)
        if is_ignored_host_metadata(path):
            continue
        if path.is_symlink() or not path.is_dir():
            path.unlink(missing_ok=True)
        elif relative_path not in retained_directories:
            path.rmdir()


def write_snapshot_files(destination_root: Path, files: dict[Path, bytes]) -> None:
    completion_path = Path(SNAPSHOT_PROVENANCE_FILENAME)
    if completion_path not in files:
        raise ValueError("snapshot output is missing its completion manifest")
    ordered_paths = sorted(
        (relative_path for relative_path in files if relative_path != completion_path),
        key=lambda path: path.as_posix(),
    )
    ordered_paths.append(completion_path)
    for relative_path in ordered_paths:
        content = files[relative_path]
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise ValueError(f"unsafe snapshot output path: {relative_path}")
        target_path = destination_root / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(content)


def validate_snapshot_files(
    plan: StaticHtmlSnapshotPlan,
    destination_root: Path,
    expected_files: dict[Path, bytes],
) -> None:
    expected_paths = set(expected_files)
    expected_dirs = {parent for path in expected_paths for parent in path.parents if parent.parts}
    actual_files: set[Path] = set()
    actual_dirs: set[Path] = set()
    for path in destination_root.rglob("*"):
        relative_path = path.relative_to(destination_root)
        if is_ignored_host_metadata(path):
            continue
        if path.is_symlink():
            raise ValueError(f"snapshot contains a symlink: {relative_path.as_posix()}")
        if path.is_dir():
            actual_dirs.add(relative_path)
        elif path.is_file():
            actual_files.add(relative_path)
        else:
            raise ValueError(f"snapshot contains a special entry: {relative_path.as_posix()}")
    if actual_files != expected_paths or actual_dirs != expected_dirs:
        differences: list[str] = []
        for label, paths in (
            ("missing files", expected_paths - actual_files),
            ("unexpected files", actual_files - expected_paths),
            ("missing directories", expected_dirs - actual_dirs),
            ("unexpected directories", actual_dirs - expected_dirs),
        ):
            ordered = sorted(path.as_posix() for path in paths)
            if ordered:
                shown = ", ".join(ordered[:5])
                suffix = f" (+{len(ordered) - 5} more)" if len(ordered) > 5 else ""
                differences.append(f"{label}: {shown}{suffix}")
        raise ValueError(
            "snapshot file set does not match the planned artifact: "
            + "; ".join(differences)
        )
    for relative_path, expected_content in expected_files.items():
        if (destination_root / relative_path).read_bytes() != expected_content:
            raise ValueError(f"snapshot content validation failed: {relative_path.as_posix()}")
    summary = load_existing_snapshot_summary(destination_root)
    if summary is None:
        raise ValueError("snapshot provenance validation failed")
    expected_selection_revision = _revision({"scope": plan.scope, "doc_ids": plan.doc_ids})
    if (
        summary["scope"] != plan.scope
        or summary["selection_kind"] != plan.selection_kind
        or summary["document_count"] != len(plan.doc_ids)
        or summary["selection_revision"] != expected_selection_revision
    ):
        raise ValueError("snapshot provenance does not match the planned selection")


def normalize_snapshot_apply_revision(value: Any, *, field: str) -> str:
    revision = str(value or "").strip().lower()
    if not REVISION_PATTERN.fullmatch(revision):
        raise ValueError(f"{field} must be a snapshot preview revision")
    return revision


def normalize_snapshot_export_date(value: Any) -> date:
    date_text = str(value or "").strip()
    if not ISO_DATE_PATTERN.fullmatch(date_text):
        raise ValueError("export_date must be an ISO local date from snapshot preview")
    try:
        parsed = date.fromisoformat(date_text)
    except ValueError as exc:
        raise ValueError("export_date must be an ISO local date from snapshot preview") from exc
    if parsed.isoformat() != date_text:
        raise ValueError("export_date must be an ISO local date from snapshot preview")
    return parsed


def ensure_snapshot_target_unchanged(plan: StaticHtmlSnapshotPlan) -> None:
    state, revision, _summary = inspect_snapshot_destination(plan.destination_root)
    if state != plan.target_state or not hmac.compare_digest(revision, plan.target_revision):
        raise StaticHtmlSnapshotApplyConflict(
            "Snapshot destination changed after preview; preview and confirm again.",
            plan=plan,
        )


def install_snapshot_in_place(plan: StaticHtmlSnapshotPlan, files: dict[Path, bytes]) -> bool:
    ensure_snapshot_target_unchanged(plan)
    replaced = plan.target_state != "absent"
    if plan.target_state == "absent":
        try:
            plan.destination_root.mkdir()
        except OSError as exc:
            raise StaticHtmlSnapshotApplyConflict(
                "Snapshot destination changed during apply; preview and confirm again.",
                plan=plan,
            ) from exc

    expected_directories = snapshot_output_directories(files)
    completion_path = plan.destination_root / SNAPSHOT_PROVENANCE_FILENAME
    try:
        if plan.destination_root.is_symlink() or not plan.destination_root.is_dir():
            raise StaticHtmlSnapshotApplyConflict(
                "Snapshot destination changed during apply; preview and confirm again.",
                plan=plan,
            )
        if completion_path.is_symlink() or completion_path.is_file():
            completion_path.unlink(missing_ok=True)
        clear_snapshot_output_files(plan.destination_root, expected_directories)
        for relative_path in sorted(
            expected_directories,
            key=lambda path: (len(path.parts), path.as_posix()),
        ):
            (plan.destination_root / relative_path).mkdir(parents=True, exist_ok=True)
        write_snapshot_files(plan.destination_root, files)
        validate_snapshot_files(plan, plan.destination_root, files)
    except Exception:
        if completion_path.is_symlink() or completion_path.is_file():
            completion_path.unlink(missing_ok=True)
        raise
    return replaced


def apply_static_html_snapshot(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    if body.get("confirm") is not True:
        raise ValueError("confirm must be true to apply a static HTML snapshot")
    export_date = normalize_snapshot_export_date(body.get("export_date"))
    requested_plan_revision = normalize_snapshot_apply_revision(body.get("plan_revision"), field="plan_revision")
    requested_target_revision = normalize_snapshot_apply_revision(body.get("target_revision"), field="target_revision")
    plan = plan_static_html_snapshot(repo_root, body, export_date=export_date)
    if not hmac.compare_digest(plan.plan_revision, requested_plan_revision):
        raise StaticHtmlSnapshotApplyConflict(
            "Snapshot plan changed after preview; preview and confirm again.",
            plan=plan,
        )
    if not hmac.compare_digest(plan.target_revision, requested_target_revision):
        raise StaticHtmlSnapshotApplyConflict(
            "Snapshot destination changed after preview; preview and confirm again.",
            plan=plan,
        )
    if plan.target_state == "non_directory":
        raise StaticHtmlSnapshotApplyConflict(
            "Snapshot destination is not a replaceable directory.",
            plan=plan,
        )
    replace_existing = body.get("replace_existing") is True
    if plan.target_state in {"recognized", "unrecognized"} and not replace_existing:
        raise ValueError("replace_existing must be true to replace the confirmed snapshot destination")
    if plan.target_state == "absent" and replace_existing:
        raise ValueError("replace_existing must be false when the confirmed snapshot destination is absent")

    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    files = compute_snapshot_files(plan, generated_at=generated_at)
    workspace = resolve_docs_export_workspace()
    workspace.root.mkdir(exist_ok=True)
    replaced = install_snapshot_in_place(plan, files)

    target_state, target_revision, existing_snapshot = inspect_snapshot_destination(plan.destination_root)
    if target_state != "recognized" or existing_snapshot is None:
        raise RuntimeError("installed snapshot failed post-apply provenance validation")
    document_label = "document" if len(plan.doc_ids) == 1 else "documents"
    return {
        "ok": True,
        "schema_version": SNAPSHOT_APPLY_SCHEMA_VERSION,
        "operation": "apply",
        "scope": plan.scope,
        "doc_ids": list(plan.doc_ids),
        "document_count": len(plan.doc_ids),
        "media_count": len(plan.media_plan.items),
        "media_bytes": plan.media_plan.media_bytes,
        "external_dependency_count": len(plan.media_plan.external_dependencies),
        "file_count": len(files),
        "selection_kind": plan.selection_kind,
        "default_doc_id": plan.default_doc_id,
        "export_date": plan.export_date,
        "generated_at": generated_at,
        "destination_label": plan.destination_label,
        "replaced": replaced,
        "plan_revision": plan.plan_revision,
        "target_revision": target_revision,
        "summary_text": f"Exported {len(plan.doc_ids)} {document_label} to {plan.destination_label}.",
    }


def static_html_export_capability() -> dict[str, Any]:
    try:
        resolve_docs_export_workspace()
    except ValueError:
        return {
            "preview": False,
            "apply": False,
            "error": f"Snapshot workspace is unavailable. Configure {PROJECTS_BASE_DIR_ENV}.",
        }
    return {
        "preview": True,
        "apply": True,
        "error": "",
    }


def scope_static_html_export_capability(
    repo_root: Path,
    scope: str,
    config: DocsScopeConfig,
    *,
    workspace_available: bool,
) -> dict[str, Any]:
    available = False
    document_count = 0
    if not workspace_available:
        error = "Snapshot workspace is unavailable."
    else:
        try:
            paths = resolve_snapshot_input_paths(repo_root, scope, config)
            index_tree = load_index_tree(paths.index_tree_path)
            doc_ids = collect_doc_ids_from_tree(index_tree.get("docs"))
            for doc_id in doc_ids:
                load_doc_payload(paths.payload_root, doc_id)
            document_count = len(doc_ids)
            available = document_count > 0
            error = "" if available else "No generated documents are available for this scope."
        except (FileNotFoundError, OSError, ValueError, json.JSONDecodeError):
            error = "Generated documents are unavailable for this scope."
    return {
        "preview": available,
        "apply": available,
        "document_count": document_count,
        "default_doc_id": config.default_doc_id,
        "error": error,
    }
