#!/usr/bin/env python3
"""
Localhost-only write service for shared Docs Viewer source docs.

Run:
  ./scripts/docs/docs_management_server.py
  ./scripts/docs/docs_management_server.py --port 8789
  ./scripts/docs/docs_management_server.py --repo-root /path/to/dotlineform-site
  ./scripts/docs/docs_management_server.py --dry-run

Endpoints:
  GET /health
  GET /capabilities
  GET /docs/import-html-files
  POST /docs/import-html
  POST /docs/rebuild
  POST /docs/broken-links
  POST /docs/open-source
  POST /docs/update-metadata
  POST /docs/update-viewability
  POST /docs/update-viewability-bulk
  POST /docs/create
  POST /docs/move
  POST /docs/archive
  POST /docs/delete-preview
  POST /docs/delete-apply

Security constraints:
  - Binds to 127.0.0.1 only.
  - CORS allows only http://localhost:* and http://127.0.0.1:*.
  - Writes only allowlisted Markdown docs under _docs_src/ and _docs_library_src/.
  - Creates timestamped backup bundles under var/docs/backups/.
  - Writes minimal local logs under var/docs/logs/.
"""

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
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlparse

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from script_logging import append_script_log  # noqa: E402
from docs_broken_links import audit_docs_broken_links  # noqa: E402
from docs_html_import import generate_import_preview, list_staged_html_files, resolve_staged_html  # noqa: E402
from docs_watch_suppression import (  # noqa: E402
    DEFAULT_COMPLETE_TTL_SECONDS,
    DEFAULT_PENDING_TTL_SECONDS,
    SUPPRESSION_COMPLETE,
    SUPPRESSION_PENDING,
    clear_watch_suppressions,
    set_watch_suppressions,
)


MAX_BODY_BYTES = 64 * 1024
FRONT_MATTER_PATTERN = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
INTEGER_PATTERN = re.compile(r"^-?\d+$")
SLUG_SEP_PATTERN = re.compile(r"[^a-z0-9]+")
SAFE_PLAIN_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 .,&()/_'-]*$")
SAFE_DOC_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
SCOPE_ROOTS = {
    "studio": Path("_docs_src"),
    "library": Path("_docs_library_src"),
}
RESERVED_DOC_IDS = {"_archive"}
BACKUPS_REL_DIR = Path("var/docs/backups")
LOGS_REL_DIR = Path("var/docs/logs")
DEFAULT_MARKDOWN_APP_ENV = "DOCS_MANAGEMENT_DEFAULT_MARKDOWN_APP"


@dataclass
class ScopeDoc:
    scope: str
    path: Path
    source_text: str
    front_matter: Dict[str, Any]
    body: str
    doc_id: str
    title: str
    parent_id: str
    sort_order: Optional[int]
    published: bool
    viewable: bool


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def backup_stamp_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%S-%f")


def current_date() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")


def find_repo_root(start: Path) -> Optional[Path]:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "_config.yml").exists():
            return candidate
    return None


def detect_repo_root(explicit_root: str) -> Path:
    if explicit_root:
        repo_root = Path(explicit_root).expanduser().resolve()
        if not (repo_root / "_config.yml").exists():
            raise SystemExit(f"--repo-root does not look like repo root (missing _config.yml): {repo_root}")
        return repo_root

    for start in [Path.cwd(), Path(__file__).resolve().parent]:
        found = find_repo_root(start)
        if found is not None:
            return found

    raise SystemExit("Could not auto-detect repo root. Pass --repo-root.")


def detect_preferred_markdown_app() -> Optional[str]:
    configured = os.environ.get(DEFAULT_MARKDOWN_APP_ENV, "").strip()
    if configured:
        return configured

    for app_name in ["MarkEdit", "Typora", "Marked 2", "Marked"]:
        if (Path("/Applications") / f"{app_name}.app").exists():
            return app_name
    return None


def detect_bundle_bin() -> Optional[str]:
    rbenv_bundle = Path.home() / ".rbenv" / "shims" / "bundle"
    if rbenv_bundle.exists() and os.access(rbenv_bundle, os.X_OK):
        return str(rbenv_bundle)
    return shutil.which("bundle")


def allowed_origin(origin: str) -> Optional[str]:
    if not origin:
        return None

    try:
        parsed = urlparse(origin)
    except Exception:
        return None

    if parsed.scheme != "http":
        return None
    if parsed.hostname not in {"localhost", "127.0.0.1"}:
        return None
    if parsed.path not in {"", "/"}:
        return None
    if parsed.params or parsed.query or parsed.fragment:
        return None
    if parsed.port is None:
        return f"{parsed.scheme}://{parsed.hostname}"
    return f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"


def humanize(value: str) -> str:
    return " ".join(part.capitalize() for part in re.split(r"[_\-\s]+", value.strip()) if part)


def slugify(value: str) -> str:
    normalized = SLUG_SEP_PATTERN.sub("-", str(value or "").strip().lower()).strip("-")
    return normalized or "new-doc"


def parse_front_matter_value(raw_value: str) -> Any:
    value = raw_value.strip()
    if value == '""':
        return ""
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if INTEGER_PATTERN.match(value):
        try:
            return int(value)
        except ValueError:
            return value
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        quote = value[0]
        inner = value[1:-1]
        if quote == '"':
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return inner
        return inner.replace("\\'", "'")
    return value


def parse_source(path: Path) -> tuple[Dict[str, Any], str]:
    raw = path.read_text(encoding="utf-8")
    match = FRONT_MATTER_PATTERN.match(raw)
    if not match:
        return {}, raw

    front_matter: Dict[str, Any] = {}
    for line in match.group(1).splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, raw_value = stripped.split(":", 1)
        front_matter[key.strip()] = parse_front_matter_value(raw_value)
    body = raw[match.end():]
    return front_matter, body


def format_front_matter_value(value: Any) -> str:
    if value is None:
        return '""'
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int):
        return str(value)
    text = str(value)
    if SAFE_PLAIN_PATTERN.match(text) and text not in {"true", "false"}:
        return text
    return json.dumps(text, ensure_ascii=False)


def format_source(front_matter: Dict[str, Any], body: str) -> str:
    preferred_order = [
        "doc_id",
        "title",
        "added_date",
        "last_updated",
        "parent_id",
        "sort_order",
        "published",
        "viewable",
    ]
    ordered_keys = [key for key in preferred_order if key in front_matter]
    ordered_keys.extend(sorted(key for key in front_matter.keys() if key not in ordered_keys))
    lines = ["---"]
    for key in ordered_keys:
        lines.append(f"{key}: {format_front_matter_value(front_matter[key])}")
    lines.append("---")
    normalized_body = body if body.startswith("\n") else "\n" + body
    return "\n".join(lines) + normalized_body


def write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f"{path.name}.", suffix=".tmp", dir=str(path.parent))
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass


def doc_is_published(front_matter: Dict[str, Any]) -> bool:
    return front_matter_boolean(front_matter, "published", True)


def doc_is_viewable(front_matter: Dict[str, Any]) -> bool:
    return front_matter_boolean(front_matter, "viewable", True)


def front_matter_boolean(front_matter: Dict[str, Any], key: str, default: bool) -> bool:
    if key not in front_matter:
        return default
    value = front_matter[key]
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() not in {"false", "0", "no", "off"}


def default_viewable_for_scope(scope: str) -> bool:
    return scope != "library"


def normalize_scope(scope: Any) -> str:
    value = str(scope or "").strip().lower()
    if value not in SCOPE_ROOTS:
        raise ValueError(f"scope must be one of: {', '.join(sorted(SCOPE_ROOTS.keys()))}")
    return value


def scope_root(repo_root: Path, scope: str) -> Path:
    return repo_root / SCOPE_ROOTS[scope]


def load_scope_docs(repo_root: Path, scope: str) -> list[ScopeDoc]:
    root = scope_root(repo_root, scope)
    if not root.exists():
        raise ValueError(f"missing source root for scope {scope}: {root}")

    docs: list[ScopeDoc] = []
    for path in sorted(root.glob("*.md")):
        front_matter, body = parse_source(path)
        doc_id = str(front_matter.get("doc_id") or path.stem).strip()
        title = str(front_matter.get("title") or humanize(doc_id or path.stem)).strip() or doc_id
        parent_id = str(front_matter.get("parent_id") or "").strip()
        sort_order = front_matter.get("sort_order")
        if sort_order is not None:
            try:
                sort_order = int(sort_order)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Invalid sort_order for {path.name}: {sort_order!r}") from exc
        docs.append(
            ScopeDoc(
                scope=scope,
                path=path,
                source_text=path.read_text(encoding="utf-8"),
                front_matter=dict(front_matter),
                body=body,
                doc_id=doc_id,
                title=title,
                parent_id=parent_id,
                sort_order=sort_order,
                published=doc_is_published(front_matter),
                viewable=doc_is_viewable(front_matter),
            )
        )
    validate_scope_docs(docs)
    return docs


def validate_scope_docs(docs: list[ScopeDoc]) -> None:
    stem_seen: dict[str, ScopeDoc] = {}
    id_seen: dict[str, ScopeDoc] = {}
    for doc in docs:
        stem = doc.path.stem
        if stem in stem_seen:
            raise ValueError(f"Duplicate filename stem {stem!r} in scope docs")
        stem_seen[stem] = doc
        if doc.doc_id in id_seen:
            raise ValueError(f"Duplicate doc_id {doc.doc_id!r} in scope docs")
        id_seen[doc.doc_id] = doc

    for doc in docs:
        if doc.parent_id and doc.parent_id not in id_seen:
            raise ValueError(f"Unknown parent_id {doc.parent_id!r} for doc {doc.doc_id!r}")


def next_sort_order(docs: list[ScopeDoc], parent_id: str) -> int:
    sibling_orders = [doc.sort_order for doc in docs if doc.parent_id == parent_id and isinstance(doc.sort_order, int)]
    if not sibling_orders:
        return 10
    return max(sibling_orders) + 10


def scope_doc_sort_key(doc: ScopeDoc) -> tuple[Any, ...]:
    return (
        doc.sort_order is None,
        0 if doc.sort_order is None else doc.sort_order,
        doc.title.lower(),
        doc.doc_id,
    )


def sorted_siblings(docs: list[ScopeDoc], parent_id: str) -> list[ScopeDoc]:
    return sorted((doc for doc in docs if doc.parent_id == parent_id), key=scope_doc_sort_key)


def create_sort_order_after(docs: list[ScopeDoc], after_doc: ScopeDoc) -> int:
    current_order = after_doc.sort_order if isinstance(after_doc.sort_order, int) else None
    if current_order is None:
        return next_sort_order(docs, after_doc.parent_id)
    return current_order + 1


def descendant_doc_ids(docs: list[ScopeDoc], doc_id: str) -> set[str]:
    children_by_parent: dict[str, list[ScopeDoc]] = {}
    for doc in docs:
        children_by_parent.setdefault(doc.parent_id, []).append(doc)

    seen: set[str] = set()
    stack = [doc_id]
    while stack:
        current = stack.pop()
        for child in children_by_parent.get(current, []):
            if child.doc_id in seen:
                continue
            seen.add(child.doc_id)
            stack.append(child.doc_id)
    return seen


def rewrite_doc_source(doc: ScopeDoc, front_matter_updates: Dict[str, Any]) -> str:
    updated_front_matter = dict(doc.front_matter)
    updated_front_matter["added_date"] = str(
        updated_front_matter.get("added_date") or updated_front_matter.get("last_updated") or current_date()
    ).strip()
    updated_front_matter.update(front_matter_updates)
    return format_source(updated_front_matter, doc.body)


def ensure_unique_stem(docs: list[ScopeDoc], title: str) -> str:
    base = slugify(title)
    existing_stems = {doc.path.stem for doc in docs}
    existing_ids = {doc.doc_id for doc in docs}
    candidate = base
    suffix = 2
    while candidate in existing_stems or candidate in existing_ids:
        candidate = f"{base}-{suffix}"
        suffix += 1
    return candidate


def make_backup_bundle(
    repo_root: Path,
    scope: str,
    operation: str,
    docs: list[ScopeDoc],
    metadata: Optional[Dict[str, Any]] = None,
) -> Path:
    bundle_dir = repo_root / BACKUPS_REL_DIR / f"{backup_stamp_now()}-{scope}-{operation}"
    bundle_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "time_utc": utc_now(),
        "scope": scope,
        "operation": operation,
        "count": len(docs),
        "files": [
            {
                "doc_id": doc.doc_id,
                "title": doc.title,
                "path": relative_path(repo_root, doc.path),
                "filename": doc.path.name,
            }
            for doc in docs
        ],
    }
    if metadata:
        manifest["metadata"] = metadata
    write_text_atomic(bundle_dir / "manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    for doc in docs:
        shutil.copy2(doc.path, bundle_dir / doc.path.name)
    return bundle_dir


def make_import_overwrite_backup(
    repo_root: Path,
    scope: str,
    target: ScopeDoc,
    metadata: Optional[Dict[str, Any]] = None,
) -> Path:
    bundle_name = f"{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%d')}-{scope}-import-overwrite-{slugify(target.doc_id)}"
    bundle_dir = repo_root / BACKUPS_REL_DIR / bundle_name
    if bundle_dir.exists():
        shutil.rmtree(bundle_dir)
    bundle_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "time_utc": utc_now(),
        "scope": scope,
        "operation": "import-overwrite",
        "count": 1,
        "files": [
            {
                "doc_id": target.doc_id,
                "title": target.title,
                "path": relative_path(repo_root, target.path),
                "filename": target.path.name,
            }
        ],
    }
    if metadata:
        manifest["metadata"] = metadata
    write_text_atomic(bundle_dir / "manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    shutil.copy2(target.path, bundle_dir / target.path.name)
    return bundle_dir


def rebuild_scope_outputs(repo_root: Path, scope: str, include_search: bool = True) -> Dict[str, Any]:
    bundle_bin = detect_bundle_bin()
    if not bundle_bin:
        raise RuntimeError("bundle executable not found")

    commands = [[bundle_bin, "exec", "ruby", "scripts/build_docs.rb", "--scope", scope, "--write"]]
    if include_search:
        commands.append([bundle_bin, "exec", "ruby", "scripts/build_search.rb", "--scope", scope, "--write"])
    steps = []
    for command in commands:
        completed = subprocess.run(
            command,
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
        steps.append(
            {
                "command": " ".join(command),
                "returncode": completed.returncode,
                "stdout": completed.stdout.strip(),
                "stderr": completed.stderr.strip(),
            }
        )
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip() or f"exit {completed.returncode}"
            raise RuntimeError(f"rebuild failed for {scope}: {detail}")
    return {
        "ok": True,
        "steps": steps,
    }


def perform_source_write_and_rebuild(
    repo_root: Path,
    scope: str,
    changed_paths: list[Path],
    write_operation,
    *,
    suppression_reason: str,
    include_search: bool = True,
) -> Dict[str, Any]:
    filenames = sorted({path.name for path in changed_paths if isinstance(path, Path)})
    if filenames:
        set_watch_suppressions(
            repo_root,
            scope,
            filenames,
            status=SUPPRESSION_PENDING,
            reason=suppression_reason,
            ttl_seconds=DEFAULT_PENDING_TTL_SECONDS,
        )
    try:
        write_operation()
        rebuild = rebuild_scope_outputs(repo_root, scope, include_search=include_search)
    except Exception:
        if filenames:
            clear_watch_suppressions(repo_root, scope, filenames)
        raise
    if filenames:
        set_watch_suppressions(
            repo_root,
            scope,
            filenames,
            status=SUPPRESSION_COMPLETE,
            reason=suppression_reason,
            ttl_seconds=DEFAULT_COMPLETE_TTL_SECONDS,
        )
    return rebuild


def rebuild_all_docs_outputs(repo_root: Path) -> Dict[str, Any]:
    bundle_bin = detect_bundle_bin()
    if not bundle_bin:
        raise RuntimeError("bundle executable not found")

    commands = [
        [bundle_bin, "exec", "ruby", "scripts/build_docs.rb", "--write"],
        [bundle_bin, "exec", "ruby", "scripts/build_search.rb", "--scope", "studio", "--write"],
        [bundle_bin, "exec", "ruby", "scripts/build_search.rb", "--scope", "library", "--write"],
    ]
    steps = []
    for command in commands:
        completed = subprocess.run(
            command,
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
        steps.append(
            {
                "command": " ".join(command),
                "returncode": completed.returncode,
                "stdout": completed.stdout.strip(),
                "stderr": completed.stderr.strip(),
            }
        )
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip() or f"exit {completed.returncode}"
            raise RuntimeError(f"docs rebuild failed: {detail}")
    return {
        "ok": True,
        "steps": steps,
        "summary_text": "Docs and docs search rebuilt for studio and library.",
    }


def relative_path(repo_root: Path, path: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def viewer_url_for(scope: str, doc_id: str) -> str:
    if scope == "studio":
        return f"/docs/?scope=studio&doc={doc_id}"
    return f"/library/?doc={doc_id}&mode=manage"


def generated_docs_index_path(repo_root: Path, scope: str) -> Path:
    return repo_root / "assets" / "data" / "docs" / "scopes" / scope / "index.json"


def generated_doc_payload_path(repo_root: Path, scope: str, doc_id: str) -> Path:
    if not SAFE_DOC_ID_PATTERN.match(doc_id):
        raise ValueError("doc_id contains unsupported characters")
    return repo_root / "assets" / "data" / "docs" / "scopes" / scope / "by-id" / f"{doc_id}.json"


def generated_search_index_path(repo_root: Path, scope: str) -> Path:
    return repo_root / "assets" / "data" / "search" / scope / "index.json"


def read_generated_json(path: Path, label: str) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"{label} not found: {path.name}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{label} is not valid JSON: {path.name}") from exc


def query_param(handler: BaseHTTPRequestHandler, name: str) -> str:
    parsed = urlparse(handler.path)
    values = parse_qs(parsed.query).get(name, [])
    return str(values[0] if values else "").strip()


def open_source_doc(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    scope = normalize_scope(body.get("scope"))
    doc_id = str(body.get("doc_id") or "").strip()
    editor = str(body.get("editor") or "default").strip().lower()
    if not doc_id:
        raise ValueError("doc_id is required")
    if editor not in {"default", "vscode"}:
        raise ValueError("editor must be `default` or `vscode`")

    docs = load_scope_docs(repo_root, scope)
    target = next((doc for doc in docs if doc.doc_id == doc_id), None)
    if target is None:
        raise FileNotFoundError(f"doc {doc_id!r} not found in scope {scope}")

    preferred_app = detect_preferred_markdown_app()

    if editor == "vscode":
        command = ["open", "-a", "Visual Studio Code", str(target.path)]
    else:
        if preferred_app:
            command = ["open", "-a", preferred_app, str(target.path)]
        else:
            command = ["open", str(target.path)]

    if not dry_run:
        completed = subprocess.run(
            command,
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip() or f"exit {completed.returncode}"
            raise RuntimeError(f"open source failed: {detail}")
        log_event(
            repo_root,
            "docs-open-source",
            {
                "scope": scope,
                "doc_id": target.doc_id,
                "editor": editor,
                "preferred_app": preferred_app if editor == "default" else "",
                "path": relative_path(repo_root, target.path),
            },
        )

    return {
        "ok": True,
        "scope": scope,
        "doc_id": target.doc_id,
        "editor": editor,
        "preferred_app": preferred_app if editor == "default" else "",
        "path": relative_path(repo_root, target.path),
        "summary_text": f"Opened {target.doc_id} source.",
        "dry_run": dry_run,
    }


def preview_delete(repo_root: Path, scope: str, doc_id: str) -> Dict[str, Any]:
    docs = load_scope_docs(repo_root, scope)
    docs_by_id = {doc.doc_id: doc for doc in docs}
    target = docs_by_id.get(doc_id)
    if target is None:
        raise FileNotFoundError(f"doc {doc_id!r} not found in scope {scope}")

    children = [
        {
            "doc_id": doc.doc_id,
            "title": doc.title,
            "path": relative_path(repo_root, doc.path),
        }
        for doc in docs
        if doc.parent_id == target.doc_id
    ]
    inbound_refs = find_inbound_refs(repo_root, target, docs)
    blockers = []
    warnings = []
    if target.doc_id in RESERVED_DOC_IDS:
        blockers.append(f"{target.doc_id} is a reserved system doc")
    if children:
        blockers.append(f"{len(children)} child docs still depend on this parent")
    if inbound_refs:
        warnings.append(f"{len(inbound_refs)} inbound markdown references will become broken")

    return {
        "ok": True,
        "scope": scope,
        "doc_id": target.doc_id,
        "title": target.title,
        "path": relative_path(repo_root, target.path),
        "allowed": not blockers,
        "blockers": blockers,
        "warnings": warnings,
        "children": children,
        "inbound_refs": inbound_refs,
    }


def find_inbound_refs(repo_root: Path, target: ScopeDoc, docs: list[ScopeDoc]) -> list[Dict[str, str]]:
    target_filename = target.path.name
    doc_link_fragment = f"doc={target.doc_id}"
    refs: list[Dict[str, str]] = []
    for doc in docs:
        if doc.doc_id == target.doc_id:
            continue
        source = doc.source_text
        if doc_link_fragment not in source and target_filename not in source:
            continue
        refs.append(
            {
                "doc_id": doc.doc_id,
                "title": doc.title,
                "path": relative_path(repo_root, doc.path),
            }
        )
    refs.sort(key=lambda item: (item["title"].lower(), item["doc_id"]))
    return refs


def capabilities_payload(repo_root: Path) -> Dict[str, Any]:
    scopes: Dict[str, Any] = {}
    for scope in sorted(SCOPE_ROOTS.keys()):
        root = scope_root(repo_root, scope)
        scope_docs = load_scope_docs(repo_root, scope)
        scopes[scope] = {
            "available": root.exists(),
            "root": relative_path(repo_root, root),
            "archive_available": any(doc.doc_id == "_archive" for doc in scope_docs),
            "count": len(scope_docs),
        }
    return {
        "ok": True,
        "capabilities": {
            "docs_management": True,
            "html_import": True,
            "scopes": scopes,
        },
    }


def parse_json_body(handler: BaseHTTPRequestHandler) -> Dict[str, Any]:
    content_length = handler.headers.get("Content-Length", "").strip()
    try:
        length = int(content_length)
    except ValueError as exc:
        raise ValueError("Invalid Content-Length") from exc
    if length < 0 or length > MAX_BODY_BYTES:
        raise ValueError("Request body too large")
    raw = handler.rfile.read(length)
    try:
        payload = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("Request body must be valid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("Request body must be a JSON object")
    return payload


def write_response(handler: BaseHTTPRequestHandler, status: HTTPStatus, payload: Dict[str, Any]) -> None:
    encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    origin = allowed_origin(handler.headers.get("Origin", ""))
    if origin:
        handler.send_header("Access-Control-Allow-Origin", origin)
        handler.send_header("Vary", "Origin")
        handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(encoded)))
    handler.end_headers()
    handler.wfile.write(encoded)


def error_response(handler: BaseHTTPRequestHandler, status: HTTPStatus, message: str) -> None:
    write_response(handler, status, {"ok": False, "error": message})


def log_event(repo_root: Path, event: str, details: Dict[str, Any]) -> None:
    append_script_log(__file__, event, details=details, repo_root=repo_root, log_dir_rel=LOGS_REL_DIR)


def handle_broken_links(repo_root: Path, body: Dict[str, Any]) -> Dict[str, Any]:
    scope = normalize_scope(body.get("scope"))
    payload = audit_docs_broken_links(repo_root, scope)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    log_event(
        repo_root,
        "docs_broken_links",
        {
            "scope": scope,
            "total": int(summary.get("total") or 0),
            "not_found": int(summary.get("not_found") or 0),
            "wrong_title": int(summary.get("wrong_title") or 0),
        },
    )
    return payload


def imported_body_markdown(preview: Dict[str, Any]) -> str:
    title = str(preview.get("title") or "Imported Doc").strip() or "Imported Doc"
    markdown = str(preview.get("markdown_preview") or "").strip()
    if markdown:
        return markdown + "\n"
    return f"# {title}\n"


def imported_source_text_for_create(preview: Dict[str, Any], docs: list[ScopeDoc], scope: str) -> str:
    title = str(preview.get("title") or "Imported Doc").strip() or "Imported Doc"
    today = current_date()
    front_matter = {
        "doc_id": preview["proposed_doc_id"],
        "title": title,
        "added_date": today,
        "last_updated": today,
        "parent_id": "",
        "sort_order": next_sort_order(docs, ""),
        "published": True,
        "viewable": default_viewable_for_scope(scope),
    }
    return format_source(front_matter, imported_body_markdown(preview))


def imported_source_text_for_overwrite(preview: Dict[str, Any], target: ScopeDoc) -> str:
    title = str(preview.get("title") or target.title).strip() or target.title
    today = current_date()
    front_matter = dict(target.front_matter)
    front_matter["doc_id"] = target.doc_id
    front_matter["title"] = title
    front_matter["added_date"] = str(front_matter.get("added_date") or front_matter.get("last_updated") or today).strip()
    front_matter["last_updated"] = today
    front_matter["parent_id"] = target.parent_id
    front_matter.setdefault("published", True)
    front_matter.setdefault("viewable", target.viewable)
    if target.sort_order is None:
        front_matter.pop("sort_order", None)
    else:
        front_matter["sort_order"] = target.sort_order
    return format_source(front_matter, imported_body_markdown(preview))


def handle_import_html(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    scope = normalize_scope(body.get("scope"))
    staged_filename = str(body.get("staged_filename") or "").strip()
    include_prompt_meta = bool(body.get("include_prompt_meta"))
    overwrite_doc_id = str(body.get("overwrite_doc_id") or "").strip()
    confirm_overwrite = bool(body.get("confirm_overwrite"))
    preview_only = bool(body.get("preview_only"))
    source_path = resolve_staged_html(repo_root, staged_filename)
    preview = generate_import_preview(
        repo_root,
        source_path=source_path,
        scope=scope,
        include_prompt_meta=include_prompt_meta,
    )

    docs = load_scope_docs(repo_root, scope)
    collision_doc = next((doc for doc in docs if doc.doc_id == preview["proposed_doc_id"]), None)
    collision = {
        "exists": collision_doc is not None,
        "doc_id": collision_doc.doc_id if collision_doc else "",
        "title": collision_doc.title if collision_doc else "",
        "path": relative_path(repo_root, collision_doc.path) if collision_doc else "",
    }

    if overwrite_doc_id and collision_doc is None:
        raise ValueError("overwrite_doc_id is only allowed when the generated import target collides with an existing doc")
    if overwrite_doc_id and collision_doc and overwrite_doc_id != collision_doc.doc_id:
        raise ValueError(f"overwrite_doc_id must match the colliding doc_id {collision_doc.doc_id!r}")

    requires_overwrite_confirmation = collision_doc is not None and not (overwrite_doc_id and confirm_overwrite)
    if requires_overwrite_confirmation:
        preview.setdefault("warnings", []).append(
            f"Proposed doc_id {collision_doc.doc_id!r} already exists in {scope}; explicit overwrite flow will be required."
        )

    if dry_run or preview_only or requires_overwrite_confirmation:
        log_event(
            repo_root,
            "docs-import-html-preview",
            {
                "scope": scope,
                "staged_filename": staged_filename,
                "include_prompt_meta": include_prompt_meta,
                "proposed_doc_id": preview["proposed_doc_id"],
                "collision": collision["exists"],
                "requires_overwrite_confirmation": requires_overwrite_confirmation,
            },
        )
        return {
            "ok": True,
            "scope": scope,
            "staged_filename": staged_filename,
            "include_prompt_meta": include_prompt_meta,
            "preview_only": True,
            "requires_overwrite_confirmation": requires_overwrite_confirmation,
            "collision": collision,
            "import_preview": preview,
            "summary_text": (
                f"Overwrite confirmation required for {collision['doc_id']}."
                if requires_overwrite_confirmation
                else f"Prepared HTML import preview for {staged_filename}."
            ),
            "dry_run": dry_run,
        }

    backup_dir = None
    rebuild = None
    if collision_doc is not None:
        source_text = imported_source_text_for_overwrite(preview, collision_doc)
        if not dry_run:
            backup_dir = make_import_overwrite_backup(
                repo_root,
                scope,
                collision_doc,
                {
                    "staged_filename": staged_filename,
                    "include_prompt_meta": include_prompt_meta,
                    "source_html": preview.get("source_html"),
                    "title": preview.get("title"),
                },
            )
            rebuild = perform_source_write_and_rebuild(
                repo_root,
                scope,
                [collision_doc.path],
                lambda: write_text_atomic(collision_doc.path, source_text),
                suppression_reason="docs-import-html-overwrite",
            )
        log_event(
            repo_root,
            "docs-import-html-overwrite",
            {
                "scope": scope,
                "staged_filename": staged_filename,
                "doc_id": collision_doc.doc_id,
                "path": relative_path(repo_root, collision_doc.path),
                "include_prompt_meta": include_prompt_meta,
            },
        )
        return {
            "ok": True,
            "scope": scope,
            "staged_filename": staged_filename,
            "include_prompt_meta": include_prompt_meta,
            "preview_only": False,
            "requires_overwrite_confirmation": False,
            "operation": "overwrite",
            "doc_id": collision_doc.doc_id,
            "path": relative_path(repo_root, collision_doc.path),
            "viewer_url": viewer_url_for(scope, collision_doc.doc_id),
            "title": preview["title"],
            "record": {
                "doc_id": collision_doc.doc_id,
                "title": preview["title"],
                "parent_id": collision_doc.parent_id,
                "sort_order": collision_doc.sort_order,
                "published": True,
                "viewable": collision_doc.viewable,
            },
            "collision": collision,
            "import_preview": preview,
            "backup_dir": relative_path(repo_root, backup_dir) if backup_dir else "",
            "rebuild": rebuild,
            "summary_text": f"Overwrote {collision_doc.doc_id} from {staged_filename}.",
            "dry_run": dry_run,
        }

    doc_id = preview["proposed_doc_id"]
    target_path = scope_root(repo_root, scope) / f"{doc_id}.md"
    source_text = imported_source_text_for_create(preview, docs, scope)
    if not dry_run:
        backup_dir = make_backup_bundle(
            repo_root,
            scope,
            "import-create",
            [],
            {
                "staged_filename": staged_filename,
                "include_prompt_meta": include_prompt_meta,
                "doc_id": doc_id,
                "title": preview["title"],
                "path": relative_path(repo_root, target_path),
                "source_html": preview.get("source_html"),
            },
        )
        rebuild = perform_source_write_and_rebuild(
            repo_root,
            scope,
            [target_path],
            lambda: write_text_atomic(target_path, source_text),
            suppression_reason="docs-import-html-create",
        )
    log_event(
        repo_root,
        "docs-import-html-create",
        {
            "scope": scope,
            "staged_filename": staged_filename,
            "doc_id": doc_id,
            "path": relative_path(repo_root, target_path),
            "include_prompt_meta": include_prompt_meta,
        },
    )
    return {
        "ok": True,
        "scope": scope,
        "staged_filename": staged_filename,
        "include_prompt_meta": include_prompt_meta,
        "preview_only": False,
        "requires_overwrite_confirmation": False,
        "operation": "create",
        "doc_id": doc_id,
        "path": relative_path(repo_root, target_path),
        "viewer_url": viewer_url_for(scope, doc_id),
        "title": preview["title"],
        "record": {
            "doc_id": doc_id,
            "title": preview["title"],
            "parent_id": "",
            "sort_order": next_sort_order(docs, ""),
            "published": True,
            "viewable": default_viewable_for_scope(scope),
        },
        "collision": collision,
        "import_preview": preview,
        "backup_dir": relative_path(repo_root, backup_dir) if backup_dir else "",
        "rebuild": rebuild,
        "summary_text": f"Created {doc_id} from {staged_filename}.",
        "dry_run": dry_run,
    }


def handle_create(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    scope = normalize_scope(body.get("scope"))
    docs = load_scope_docs(repo_root, scope)
    title = str(body.get("title") or "New Doc").strip() or "New Doc"
    docs_by_id = {doc.doc_id: doc for doc in docs}
    raw_sort_order = body.get("sort_order")
    after_doc_id = str(body.get("after_doc_id") or "").strip()
    parent_id = str(body.get("parent_id") or "").strip()

    if after_doc_id:
        after_doc = docs_by_id.get(after_doc_id)
        if after_doc is None:
            raise ValueError(f"Unknown after_doc_id {after_doc_id!r} for scope {scope}")
        parent_id = after_doc.parent_id
        sort_order = create_sort_order_after(docs, after_doc)
    elif parent_id and parent_id not in docs_by_id:
        raise ValueError(f"Unknown parent_id {parent_id!r} for scope {scope}")
    elif raw_sort_order in {None, ""}:
        sort_order = next_sort_order(docs, parent_id)
    else:
        try:
            sort_order = int(raw_sort_order)
        except (TypeError, ValueError) as exc:
            raise ValueError("sort_order must be an integer") from exc

    doc_id = ensure_unique_stem(docs, title)
    target_root = scope_root(repo_root, scope)
    target_path = target_root / f"{doc_id}.md"
    today = current_date()
    front_matter = {
        "doc_id": doc_id,
        "title": title,
        "added_date": today,
        "last_updated": today,
        "parent_id": parent_id,
        "sort_order": sort_order,
        "published": True,
        "viewable": default_viewable_for_scope(scope),
    }
    source_text = format_source(front_matter, f"# {title}\n")

    backup_dir = None
    rebuild = None
    if not dry_run:
        backup_dir = make_backup_bundle(
            repo_root,
            scope,
            "create",
            [],
            {
                "doc_id": doc_id,
                "title": title,
                "path": relative_path(repo_root, target_path),
                "parent_id": parent_id,
                "sort_order": sort_order,
                "after_doc_id": after_doc_id,
            },
        )
        rebuild = perform_source_write_and_rebuild(
            repo_root,
            scope,
            [target_path],
            lambda: write_text_atomic(target_path, source_text),
            suppression_reason="docs-create",
        )
        log_event(
            repo_root,
            "docs-create",
            {
                "scope": scope,
                "doc_id": doc_id,
                "path": relative_path(repo_root, target_path),
            },
        )

    return {
        "ok": True,
        "scope": scope,
        "doc_id": doc_id,
        "path": relative_path(repo_root, target_path),
        "record": {
            "doc_id": doc_id,
            "title": title,
            "parent_id": parent_id,
            "sort_order": sort_order,
            "published": True,
            "viewable": default_viewable_for_scope(scope),
        },
        "summary_text": f"Created {doc_id}.",
        "backup_dir": relative_path(repo_root, backup_dir) if backup_dir else "",
        "rebuild": rebuild,
        "dry_run": dry_run,
    }


def handle_update_metadata(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    scope = normalize_scope(body.get("scope"))
    doc_id = str(body.get("doc_id") or "").strip()
    if not doc_id:
        raise ValueError("doc_id is required")

    docs = load_scope_docs(repo_root, scope)
    docs_by_id = {doc.doc_id: doc for doc in docs}
    target = docs_by_id.get(doc_id)
    if target is None:
        raise FileNotFoundError(f"doc {doc_id!r} not found in scope {scope}")
    if target.doc_id in RESERVED_DOC_IDS:
        raise ValueError(f"{target.doc_id} is a reserved system doc and cannot be edited")

    title = str(body.get("title") or "").strip()
    if not title:
        raise ValueError("title is required")

    parent_id = str(body.get("parent_id") or "").strip()
    if parent_id == target.doc_id:
        raise ValueError("parent_id cannot be the current doc")
    if parent_id and parent_id not in docs_by_id:
        raise ValueError(f"Unknown parent_id {parent_id!r} for scope {scope}")
    if parent_id and parent_id in descendant_doc_ids(docs, target.doc_id):
        raise ValueError("parent_id cannot be a child or descendant of the current doc")

    raw_sort_order = body.get("sort_order")
    raw_sort_order_text = "" if raw_sort_order is None else str(raw_sort_order).strip()
    if raw_sort_order_text.lower() == "append":
        remaining_docs = [doc for doc in docs if doc.doc_id != target.doc_id]
        sort_order = next_sort_order(remaining_docs, parent_id)
    elif raw_sort_order_text == "":
        sort_order = None
    else:
        try:
            sort_order = int(raw_sort_order_text)
        except (TypeError, ValueError) as exc:
            raise ValueError("sort_order must be an integer, blank, or append") from exc
        if sort_order < 0:
            raise ValueError("sort_order must be zero or greater")

    title_changed = title != target.title
    parent_changed = parent_id != target.parent_id
    sort_changed = sort_order != target.sort_order
    if not (title_changed or parent_changed or sort_changed):
        return {
            "ok": True,
            "scope": scope,
            "doc_id": target.doc_id,
            "path": relative_path(repo_root, target.path),
            "record": {
                "doc_id": target.doc_id,
                "title": target.title,
                "parent_id": target.parent_id,
                "sort_order": target.sort_order,
            },
            "summary_text": f"No metadata changes for {target.doc_id}.",
            "dry_run": dry_run,
        }

    updated_front_matter = dict(target.front_matter)
    updated_front_matter["added_date"] = str(
        updated_front_matter.get("added_date") or updated_front_matter.get("last_updated") or current_date()
    ).strip()
    updated_front_matter["title"] = title
    updated_front_matter["last_updated"] = current_date()
    updated_front_matter["parent_id"] = parent_id
    if sort_order is None:
        updated_front_matter.pop("sort_order", None)
    else:
        updated_front_matter["sort_order"] = sort_order

    rewritten_source = format_source(updated_front_matter, target.body)
    backup_dir = None
    rebuild = None
    if not dry_run:
        backup_dir = make_backup_bundle(
            repo_root,
            scope,
            "update-metadata",
            [target],
            {
                "doc_id": target.doc_id,
                "from_title": target.title,
                "to_title": title,
                "from_parent_id": target.parent_id,
                "to_parent_id": parent_id,
                "from_sort_order": target.sort_order,
                "to_sort_order": sort_order,
            },
        )
        rebuild = perform_source_write_and_rebuild(
            repo_root,
            scope,
            [target.path],
            lambda: write_text_atomic(target.path, rewritten_source),
            suppression_reason="docs-update-metadata",
        )
        log_event(
            repo_root,
            "docs-update-metadata",
            {
                "scope": scope,
                "doc_id": target.doc_id,
                "title_changed": title_changed,
                "parent_changed": parent_changed,
                "sort_changed": sort_changed,
            },
        )

    return {
        "ok": True,
        "scope": scope,
        "doc_id": target.doc_id,
        "path": relative_path(repo_root, target.path),
        "record": {
            "doc_id": target.doc_id,
            "title": title,
            "parent_id": parent_id,
            "sort_order": sort_order,
        },
        "summary_text": f"Updated metadata for {target.doc_id}.",
        "backup_dir": relative_path(repo_root, backup_dir) if backup_dir else "",
        "rebuild": rebuild,
        "dry_run": dry_run,
    }


def ordered_unique_doc_ids(raw_doc_ids: Any) -> list[str]:
    if not isinstance(raw_doc_ids, list):
        raise ValueError("doc_ids must be a list")
    seen: set[str] = set()
    doc_ids: list[str] = []
    for raw_doc_id in raw_doc_ids:
        doc_id = str(raw_doc_id or "").strip()
        if not doc_id or doc_id in seen:
            continue
        seen.add(doc_id)
        doc_ids.append(doc_id)
    if not doc_ids:
        raise ValueError("doc_ids is required")
    return doc_ids


def expand_viewability_targets(docs: list[ScopeDoc], doc_ids: list[str], include_descendants: bool) -> list[ScopeDoc]:
    docs_by_id = {doc.doc_id: doc for doc in docs}
    target_ids: list[str] = []
    seen: set[str] = set()

    def add_doc_id(doc_id: str) -> None:
        if doc_id not in docs_by_id:
            raise FileNotFoundError(f"doc {doc_id!r} not found")
        if doc_id in seen:
            return
        seen.add(doc_id)
        target_ids.append(doc_id)

    for doc_id in doc_ids:
        add_doc_id(doc_id)
        if include_descendants:
            for descendant_id in sorted(descendant_doc_ids(docs, doc_id)):
                add_doc_id(descendant_id)

    targets = [docs_by_id[doc_id] for doc_id in target_ids]
    reserved = [doc.doc_id for doc in targets if doc.doc_id in RESERVED_DOC_IDS]
    if reserved:
        raise ValueError(f"{', '.join(reserved)} cannot be edited")
    return targets


def apply_viewability_update(
    repo_root: Path,
    scope: str,
    targets: list[ScopeDoc],
    next_viewable: bool,
    dry_run: bool,
    *,
    operation: str,
    suppression_reason: str,
    requested_doc_ids: list[str],
    include_descendants: bool,
) -> Dict[str, Any]:
    changed_targets = [target for target in targets if target.viewable != next_viewable]
    skipped_targets = [target for target in targets if target.viewable == next_viewable]
    changed_doc_ids = {target.doc_id for target in changed_targets}

    if not changed_targets:
        return {
            "ok": True,
            "scope": scope,
            "doc_ids": [target.doc_id for target in targets],
            "changed_doc_ids": [],
            "skipped_doc_ids": [target.doc_id for target in skipped_targets],
            "records": [
                {
                    "doc_id": target.doc_id,
                    "viewable": target.viewable,
                    "path": relative_path(repo_root, target.path),
                }
                for target in targets
            ],
            "summary_text": f"No viewability changes for {len(targets)} doc{'s' if len(targets) != 1 else ''}.",
            "dry_run": dry_run,
        }

    rewritten_sources = {
        target.doc_id: rewrite_doc_source(target, {"published": True, "viewable": next_viewable})
        for target in changed_targets
    }
    backup_dir = None
    rebuild = None
    if not dry_run:
        backup_dir = make_backup_bundle(
            repo_root,
            scope,
            operation,
            changed_targets,
            {
                "requested_doc_ids": requested_doc_ids,
                "include_descendants": include_descendants,
                "target_doc_ids": [target.doc_id for target in targets],
                "changed_doc_ids": [target.doc_id for target in changed_targets],
                "skipped_doc_ids": [target.doc_id for target in skipped_targets],
                "to_viewable": next_viewable,
            },
        )
        rebuild = perform_source_write_and_rebuild(
            repo_root,
            scope,
            [target.path for target in changed_targets],
            lambda: [
                write_text_atomic(target.path, rewritten_sources[target.doc_id])
                for target in changed_targets
            ],
            suppression_reason=suppression_reason,
        )
        log_event(
            repo_root,
            operation,
            {
                "scope": scope,
                "requested_count": len(requested_doc_ids),
                "target_count": len(targets),
                "changed_count": len(changed_targets),
                "to_viewable": next_viewable,
            },
        )

    return {
        "ok": True,
        "scope": scope,
        "doc_ids": [target.doc_id for target in targets],
        "changed_doc_ids": [target.doc_id for target in changed_targets],
        "skipped_doc_ids": [target.doc_id for target in skipped_targets],
        "records": [
            {
                "doc_id": target.doc_id,
                "viewable": next_viewable if target.doc_id in changed_doc_ids else target.viewable,
                "path": relative_path(repo_root, target.path),
            }
            for target in targets
        ],
        "summary_text": f"Updated viewability for {len(changed_targets)} doc{'s' if len(changed_targets) != 1 else ''}.",
        "backup_dir": relative_path(repo_root, backup_dir) if backup_dir else "",
        "rebuild": rebuild,
        "dry_run": dry_run,
    }


def handle_update_viewability_bulk(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    scope = normalize_scope(body.get("scope"))
    doc_ids = ordered_unique_doc_ids(body.get("doc_ids"))
    if "viewable" not in body:
        raise ValueError("viewable is required")
    next_viewable = front_matter_boolean(body, "viewable", True)
    include_descendants = bool(body.get("include_descendants"))
    docs = load_scope_docs(repo_root, scope)
    targets = expand_viewability_targets(docs, doc_ids, include_descendants)
    return apply_viewability_update(
        repo_root,
        scope,
        targets,
        next_viewable,
        dry_run,
        operation="update-viewability-bulk",
        suppression_reason="docs-update-viewability-bulk",
        requested_doc_ids=doc_ids,
        include_descendants=include_descendants,
    )


def handle_update_viewability(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    scope = normalize_scope(body.get("scope"))
    doc_id = str(body.get("doc_id") or "").strip()
    if not doc_id:
        raise ValueError("doc_id is required")
    if "viewable" not in body:
        raise ValueError("viewable is required")

    next_viewable = front_matter_boolean(body, "viewable", True)
    docs = load_scope_docs(repo_root, scope)
    targets = expand_viewability_targets(docs, [doc_id], False)
    payload = apply_viewability_update(
        repo_root,
        scope,
        targets,
        next_viewable,
        dry_run,
        operation="update-viewability",
        suppression_reason="docs-update-viewability",
        requested_doc_ids=[doc_id],
        include_descendants=False,
    )
    target = targets[0]
    payload["doc_id"] = target.doc_id
    payload["path"] = relative_path(repo_root, target.path)
    payload["record"] = {
        "doc_id": target.doc_id,
        "viewable": next_viewable if target.viewable != next_viewable else target.viewable,
    }
    if target.viewable == next_viewable:
        payload["summary_text"] = f"No viewability changes for {target.doc_id}."
    else:
        payload["summary_text"] = f"Updated viewability for {target.doc_id}."
    return payload


def handle_move(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    scope = normalize_scope(body.get("scope"))
    doc_id = str(body.get("doc_id") or "").strip()
    target_doc_id = str(body.get("target_doc_id") or "").strip()
    position = str(body.get("position") or "after").strip().lower()
    if not doc_id:
        raise ValueError("doc_id is required")
    if not target_doc_id:
        raise ValueError("target_doc_id is required")
    if position not in {"after", "inside"}:
        raise ValueError("position must be `after` or `inside`")

    docs = load_scope_docs(repo_root, scope)
    docs_by_id = {doc.doc_id: doc for doc in docs}
    moving_doc = docs_by_id.get(doc_id)
    target_doc = docs_by_id.get(target_doc_id)
    if moving_doc is None:
        raise FileNotFoundError(f"doc {doc_id!r} not found in scope {scope}")
    if target_doc is None:
        raise FileNotFoundError(f"target_doc_id {target_doc_id!r} not found in scope {scope}")
    if moving_doc.doc_id in RESERVED_DOC_IDS:
        raise ValueError(f"{moving_doc.doc_id} is a reserved system doc and cannot be moved")
    if moving_doc.doc_id == target_doc.doc_id:
        raise ValueError("doc cannot be moved onto itself")
    if any(doc.parent_id == moving_doc.doc_id for doc in docs):
        raise ValueError(f"{moving_doc.doc_id} has child docs and cannot be moved")

    remaining_docs = [doc for doc in docs if doc.doc_id != moving_doc.doc_id]
    if position == "inside":
        next_parent_id = target_doc.doc_id
        next_sort_order_value = next_sort_order(remaining_docs, next_parent_id)
    else:
        next_parent_id = target_doc.parent_id
        next_sort_order_value = create_sort_order_after(remaining_docs, target_doc)

    if moving_doc.parent_id == next_parent_id and moving_doc.sort_order == next_sort_order_value:
        rewrites: list[tuple[ScopeDoc, str]] = []
        touched_docs: list[ScopeDoc] = []
    else:
        rewrites = [
            (
                moving_doc,
                rewrite_doc_source(
                    moving_doc,
                    {
                        "parent_id": next_parent_id,
                        "sort_order": next_sort_order_value,
                    },
                ),
            )
        ]
        touched_docs = [moving_doc]

    backup_dir = None
    rebuild = None
    if not dry_run:
        backup_dir = make_backup_bundle(
            repo_root,
            scope,
            "move",
            touched_docs,
            {
                "doc_id": moving_doc.doc_id,
                "target_doc_id": target_doc.doc_id,
                "position": position,
                "parent_id": next_parent_id,
                "sort_order": next_sort_order_value,
            },
        )
        rebuild = perform_source_write_and_rebuild(
            repo_root,
            scope,
            [doc.path for doc, _rewritten_source in rewrites],
            lambda: [write_text_atomic(doc.path, rewritten_source) for doc, rewritten_source in rewrites],
            suppression_reason="docs-move",
        )
        log_event(
            repo_root,
            "docs-move",
            {
                "scope": scope,
                "doc_id": moving_doc.doc_id,
                "target_doc_id": target_doc.doc_id,
                "position": position,
                "parent_id": next_parent_id,
                "sort_order": next_sort_order_value,
            },
        )

    moved_record = {
        "doc_id": moving_doc.doc_id,
        "parent_id": next_parent_id,
        "sort_order": next_sort_order_value,
    }

    return {
        "ok": True,
        "scope": scope,
        "doc_id": moving_doc.doc_id,
        "record": moved_record,
        "summary_text": f"Moved {moving_doc.doc_id}.",
        "backup_dir": relative_path(repo_root, backup_dir) if backup_dir else "",
        "rebuild": rebuild,
        "dry_run": dry_run,
    }


def handle_archive(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    scope = normalize_scope(body.get("scope"))
    doc_id = str(body.get("doc_id") or "").strip()
    if not doc_id:
        raise ValueError("doc_id is required")

    docs = load_scope_docs(repo_root, scope)
    docs_by_id = {doc.doc_id: doc for doc in docs}
    target = docs_by_id.get(doc_id)
    if target is None:
        raise FileNotFoundError(f"doc {doc_id!r} not found in scope {scope}")
    if target.doc_id in RESERVED_DOC_IDS:
        raise ValueError(f"{target.doc_id} is a reserved system doc and cannot be archived")
    if "_archive" not in docs_by_id:
        raise ValueError(f"scope {scope} does not define reserved _archive doc")
    if target.parent_id == "_archive":
        return {
            "ok": True,
            "scope": scope,
            "doc_id": target.doc_id,
            "path": relative_path(repo_root, target.path),
            "summary_text": f"{target.doc_id} is already archived.",
            "dry_run": dry_run,
        }

    next_order = next_sort_order(docs, "_archive")
    updated_front_matter = dict(target.front_matter)
    updated_front_matter["added_date"] = str(
        updated_front_matter.get("added_date") or updated_front_matter.get("last_updated") or current_date()
    ).strip()
    updated_front_matter["last_updated"] = current_date()
    updated_front_matter["parent_id"] = "_archive"
    updated_front_matter["sort_order"] = next_order

    backup_dir = None
    rebuild = None
    if not dry_run:
        backup_dir = make_backup_bundle(
            repo_root,
            scope,
            "archive",
            [target],
            {
                "doc_id": target.doc_id,
                "from_parent_id": target.parent_id,
                "to_parent_id": "_archive",
                "from_sort_order": target.sort_order,
                "to_sort_order": next_order,
            },
        )
        rebuild = perform_source_write_and_rebuild(
            repo_root,
            scope,
            [target.path],
            lambda: write_text_atomic(target.path, format_source(updated_front_matter, target.body)),
            suppression_reason="docs-archive",
        )
        log_event(
            repo_root,
            "docs-archive",
            {
                "scope": scope,
                "doc_id": target.doc_id,
                "path": relative_path(repo_root, target.path),
            },
        )

    return {
        "ok": True,
        "scope": scope,
        "doc_id": target.doc_id,
        "path": relative_path(repo_root, target.path),
        "record": {
            "parent_id": "_archive",
            "sort_order": next_order,
        },
        "summary_text": f"Archived {target.doc_id}.",
        "backup_dir": relative_path(repo_root, backup_dir) if backup_dir else "",
        "rebuild": rebuild,
        "dry_run": dry_run,
    }


def handle_delete_apply(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    scope = normalize_scope(body.get("scope"))
    doc_id = str(body.get("doc_id") or "").strip()
    if not doc_id:
        raise ValueError("doc_id is required")
    if not body.get("confirm"):
        raise ValueError("delete apply requires confirm=true")

    preview = preview_delete(repo_root, scope, doc_id)
    if not preview["allowed"]:
        raise ValueError("; ".join(preview["blockers"]))

    docs = load_scope_docs(repo_root, scope)
    target = next(doc for doc in docs if doc.doc_id == doc_id)
    backup_dir = None
    rebuild = None
    if not dry_run:
        backup_dir = make_backup_bundle(
            repo_root,
            scope,
            "delete",
            [target],
            {
                "doc_id": target.doc_id,
                "warnings": preview["warnings"],
                "inbound_ref_count": len(preview["inbound_refs"]),
            },
        )
        rebuild = perform_source_write_and_rebuild(
            repo_root,
            scope,
            [target.path],
            lambda: target.path.unlink(),
            suppression_reason="docs-delete",
        )
        log_event(
            repo_root,
            "docs-delete",
            {
                "scope": scope,
                "doc_id": target.doc_id,
                "path": relative_path(repo_root, target.path),
            },
        )

    return {
        "ok": True,
        "scope": scope,
        "doc_id": target.doc_id,
        "path": relative_path(repo_root, target.path),
        "warnings": preview["warnings"],
        "inbound_refs": preview["inbound_refs"],
        "summary_text": f"Deleted {target.doc_id}.",
        "backup_dir": relative_path(repo_root, backup_dir) if backup_dir else "",
        "rebuild": rebuild,
        "dry_run": dry_run,
    }


class DocsManagementHandler(BaseHTTPRequestHandler):
    server_version = "DocsManagementServer/0.1"

    @property
    def app(self) -> Dict[str, Any]:
        return getattr(self.server, "app_state")  # type: ignore[attr-defined]

    def do_OPTIONS(self) -> None:  # noqa: N802
        origin = allowed_origin(self.headers.get("Origin", ""))
        if not origin:
            self.send_response(HTTPStatus.FORBIDDEN)
            self.end_headers()
            return
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        try:
            if self.path == "/health":
                write_response(
                    self,
                    HTTPStatus.OK,
                    {
                        "ok": True,
                        "service": "docs_management",
                        "dry_run": self.app["dry_run"],
                    },
                )
                return
            if self.path == "/capabilities":
                write_response(self, HTTPStatus.OK, capabilities_payload(self.app["repo_root"]))
                return
            parsed = urlparse(self.path)
            if parsed.path == "/docs/index":
                scope = normalize_scope(query_param(self, "scope"))
                payload = read_generated_json(
                    generated_docs_index_path(self.app["repo_root"], scope),
                    f"generated docs index for {scope}",
                )
                write_response(self, HTTPStatus.OK, payload)
                return
            if parsed.path == "/docs/doc":
                scope = normalize_scope(query_param(self, "scope"))
                doc_id = query_param(self, "doc_id")
                if not doc_id:
                    raise ValueError("doc_id is required")
                payload = read_generated_json(
                    generated_doc_payload_path(self.app["repo_root"], scope, doc_id),
                    f"generated doc payload for {doc_id}",
                )
                write_response(self, HTTPStatus.OK, payload)
                return
            if parsed.path == "/docs/search":
                scope = normalize_scope(query_param(self, "scope"))
                payload = read_generated_json(
                    generated_search_index_path(self.app["repo_root"], scope),
                    f"generated search index for {scope}",
                )
                write_response(self, HTTPStatus.OK, payload)
                return
            if parsed.path == "/docs/import-html-files":
                write_response(
                    self,
                    HTTPStatus.OK,
                    {
                        "ok": True,
                        "files": list_staged_html_files(self.app["repo_root"]),
                    },
                )
                return
            error_response(self, HTTPStatus.NOT_FOUND, "Not found")
        except FileNotFoundError as error:
            error_response(self, HTTPStatus.NOT_FOUND, str(error))
        except ValueError as error:
            error_response(self, HTTPStatus.BAD_REQUEST, str(error))
        except RuntimeError as error:
            error_response(self, HTTPStatus.INTERNAL_SERVER_ERROR, str(error))

    def do_POST(self) -> None:  # noqa: N802
        origin = self.headers.get("Origin", "")
        if origin and not allowed_origin(origin):
            error_response(self, HTTPStatus.FORBIDDEN, "Origin not allowed")
            return

        try:
            body = parse_json_body(self)
            repo_root = self.app["repo_root"]
            dry_run = self.app["dry_run"]
            if self.path == "/docs/open-source":
                payload = open_source_doc(repo_root, body, dry_run)
                write_response(self, HTTPStatus.OK, payload)
                return
            if self.path == "/docs/broken-links":
                payload = handle_broken_links(repo_root, body)
                write_response(self, HTTPStatus.OK, payload)
                return
            if self.path == "/docs/import-html":
                payload = handle_import_html(repo_root, body, dry_run)
                write_response(self, HTTPStatus.OK, payload)
                return
            if self.path == "/docs/update-metadata":
                payload = handle_update_metadata(repo_root, body, dry_run)
                write_response(self, HTTPStatus.OK, payload)
                return
            if self.path == "/docs/update-viewability":
                payload = handle_update_viewability(repo_root, body, dry_run)
                write_response(self, HTTPStatus.OK, payload)
                return
            if self.path == "/docs/update-viewability-bulk":
                payload = handle_update_viewability_bulk(repo_root, body, dry_run)
                write_response(self, HTTPStatus.OK, payload)
                return
            if self.path == "/docs/create":
                payload = handle_create(repo_root, body, dry_run)
                write_response(self, HTTPStatus.OK, payload)
                return
            if self.path == "/docs/rebuild":
                scope = normalize_scope(body.get("scope"))
                payload = rebuild_scope_outputs(repo_root, scope)
                payload["summary_text"] = f"Docs and docs search rebuilt for {scope}."
                write_response(self, HTTPStatus.OK, payload)
                return
            if self.path == "/docs/move":
                payload = handle_move(repo_root, body, dry_run)
                write_response(self, HTTPStatus.OK, payload)
                return
            if self.path == "/docs/archive":
                payload = handle_archive(repo_root, body, dry_run)
                write_response(self, HTTPStatus.OK, payload)
                return
            if self.path == "/docs/delete-preview":
                scope = normalize_scope(body.get("scope"))
                doc_id = str(body.get("doc_id") or "").strip()
                if not doc_id:
                    raise ValueError("doc_id is required")
                payload = preview_delete(repo_root, scope, doc_id)
                write_response(self, HTTPStatus.OK, payload)
                return
            if self.path == "/docs/delete-apply":
                payload = handle_delete_apply(repo_root, body, dry_run)
                write_response(self, HTTPStatus.OK, payload)
                return
            error_response(self, HTTPStatus.NOT_FOUND, "Not found")
        except FileNotFoundError as error:
            error_response(self, HTTPStatus.NOT_FOUND, str(error))
        except ValueError as error:
            error_response(self, HTTPStatus.BAD_REQUEST, str(error))
        except RuntimeError as error:
            error_response(self, HTTPStatus.INTERNAL_SERVER_ERROR, str(error))

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the localhost docs-management server.")
    parser.add_argument("--port", type=int, default=8789, help="Port to bind. Default: 8789")
    parser.add_argument("--repo-root", default="", help="Explicit repo root")
    parser.add_argument("--dry-run", action="store_true", help="Validate but do not write files")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    repo_root = detect_repo_root(args.repo_root)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), DocsManagementHandler)
    server.app_state = {  # type: ignore[attr-defined]
        "repo_root": repo_root,
        "dry_run": bool(args.dry_run),
    }
    print(f"Docs Management Server listening on http://127.0.0.1:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Docs Management Server")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
