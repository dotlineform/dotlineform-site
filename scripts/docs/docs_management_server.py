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
  POST /docs/create
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
from urllib.parse import urlparse

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from script_logging import append_script_log  # noqa: E402


MAX_BODY_BYTES = 64 * 1024
FRONT_MATTER_PATTERN = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
INTEGER_PATTERN = re.compile(r"^-?\d+$")
SLUG_SEP_PATTERN = re.compile(r"[^a-z0-9]+")
SAFE_PLAIN_PATTERN = re.compile(r"^[A-Za-z0-9._/-]+$")
SCOPE_ROOTS = {
    "studio": Path("_docs_src"),
    "library": Path("_docs_library_src"),
}
RESERVED_DOC_IDS = {"_archive"}
BACKUPS_REL_DIR = Path("var/docs/backups")
LOGS_REL_DIR = Path("var/docs/logs")


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
    preferred_order = ["doc_id", "title", "last_updated", "parent_id", "sort_order", "published"]
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
    if "published" not in front_matter:
        return True
    value = front_matter["published"]
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() not in {"false", "0", "no", "off"}


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


def make_backup_bundle(repo_root: Path, scope: str, operation: str, docs: list[ScopeDoc]) -> Path:
    bundle_dir = repo_root / BACKUPS_REL_DIR / f"{backup_stamp_now()}-{scope}-{operation}"
    bundle_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "time_utc": utc_now(),
        "scope": scope,
        "operation": operation,
        "count": len(docs),
        "files": [doc.path.name for doc in docs],
    }
    write_text_atomic(bundle_dir / "manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    for doc in docs:
        shutil.copy2(doc.path, bundle_dir / doc.path.name)
    return bundle_dir


def rebuild_scope_outputs(repo_root: Path, scope: str) -> Dict[str, Any]:
    bundle_bin = detect_bundle_bin()
    if not bundle_bin:
        raise RuntimeError("bundle executable not found")

    commands = [
        [bundle_bin, "exec", "ruby", "scripts/build_docs.rb", "--scope", scope, "--write"],
        [bundle_bin, "exec", "ruby", "scripts/build_search.rb", "--scope", scope, "--write"],
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
            raise RuntimeError(f"rebuild failed for {scope}: {detail}")
    return {
        "ok": True,
        "steps": steps,
    }


def relative_path(repo_root: Path, path: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


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


def handle_create(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    scope = normalize_scope(body.get("scope"))
    docs = load_scope_docs(repo_root, scope)
    title = str(body.get("title") or "New Doc").strip() or "New Doc"
    parent_id = str(body.get("parent_id") or "").strip()
    docs_by_id = {doc.doc_id: doc for doc in docs}
    if parent_id and parent_id not in docs_by_id:
        raise ValueError(f"Unknown parent_id {parent_id!r} for scope {scope}")

    raw_sort_order = body.get("sort_order")
    if raw_sort_order in {None, ""}:
        sort_order = next_sort_order(docs, parent_id)
    else:
        try:
            sort_order = int(raw_sort_order)
        except (TypeError, ValueError) as exc:
            raise ValueError("sort_order must be an integer") from exc

    doc_id = ensure_unique_stem(docs, title)
    target_root = scope_root(repo_root, scope)
    target_path = target_root / f"{doc_id}.md"
    front_matter = {
        "doc_id": doc_id,
        "title": title,
        "last_updated": current_date(),
        "parent_id": parent_id,
        "sort_order": sort_order,
    }
    source_text = format_source(front_matter, f"# {title}\n")

    backup_dir = None
    rebuild = None
    if not dry_run:
        backup_dir = make_backup_bundle(repo_root, scope, "create", docs)
        write_text_atomic(target_path, source_text)
        rebuild = rebuild_scope_outputs(repo_root, scope)
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
        },
        "summary_text": f"Created {doc_id}.",
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
    updated_front_matter["last_updated"] = current_date()
    updated_front_matter["parent_id"] = "_archive"
    updated_front_matter["sort_order"] = next_order

    backup_dir = None
    rebuild = None
    if not dry_run:
        backup_dir = make_backup_bundle(repo_root, scope, "archive", docs)
        write_text_atomic(target.path, format_source(updated_front_matter, target.body))
        rebuild = rebuild_scope_outputs(repo_root, scope)
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
        backup_dir = make_backup_bundle(repo_root, scope, "delete", docs)
        target.path.unlink()
        rebuild = rebuild_scope_outputs(repo_root, scope)
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
        error_response(self, HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:  # noqa: N802
        origin = self.headers.get("Origin", "")
        if origin and not allowed_origin(origin):
            error_response(self, HTTPStatus.FORBIDDEN, "Origin not allowed")
            return

        try:
            body = parse_json_body(self)
            repo_root = self.app["repo_root"]
            dry_run = self.app["dry_run"]
            if self.path == "/docs/create":
                payload = handle_create(repo_root, body, dry_run)
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
