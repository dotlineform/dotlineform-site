"""Docs source management service routes for Local Studio."""

from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

import docs_source_model as source_model
import docs_write_rebuild as write_rebuild
from docs_management_context import DEFAULT_MARKDOWN_APP_ENV, log_event, relative_path
from local_env import runtime_env

STRICT_FRONT_MATTER_PATTERN = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|$)", re.DOTALL)


def normalize_source_body(value: Any) -> str:
    return str(value if value is not None else "").replace("\r\n", "\n").replace("\r", "\n")


def source_revision_for_text(source_text: str) -> str:
    digest = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def parse_front_matter_block(front_matter_text: str) -> Dict[str, Any]:
    front_matter: Dict[str, Any] = {}
    for line_number, line in enumerate(front_matter_text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            raise ValueError(f"front matter line {line_number} is not a key/value pair")
        key, raw_value = stripped.split(":", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"front matter line {line_number} has a blank key")
        front_matter[key] = source_model.parse_front_matter_value(raw_value)
    return front_matter


def split_source_exact(source_text: str) -> tuple[str, Dict[str, Any], str]:
    match = STRICT_FRONT_MATTER_PATTERN.match(source_text)
    if not match:
        raise ValueError("existing source front matter could not be parsed")
    front_matter = parse_front_matter_block(match.group(1))
    return source_text[: match.end()], front_matter, source_text[match.end() :]


def resolve_scope_doc(repo_root: Path, scope: str, doc_id: str) -> source_model.ScopeDoc:
    docs = source_model.load_scope_docs(repo_root, scope)
    target = next((doc for doc in docs if doc.doc_id == doc_id), None)
    if target is None:
        raise FileNotFoundError(f"doc {doc_id!r} not found in scope {scope}")
    root = source_model.scope_root(repo_root, scope).resolve()
    target_path = target.path.resolve()
    try:
        target_path.relative_to(root)
    except ValueError as error:
        raise ValueError("source path escapes configured scope root") from error
    return target


def read_source_body(repo_root: Path, params: Dict[str, list[str]]) -> Dict[str, Any]:
    scope = source_model.normalize_scope((params.get("scope") or [""])[0])
    doc_id = str((params.get("doc_id") or params.get("doc") or [""])[0] or "").strip()
    if not doc_id:
        raise ValueError("doc_id is required")
    target = resolve_scope_doc(repo_root, scope, doc_id)
    source_text = target.path.read_text(encoding="utf-8")
    _front_matter_source, front_matter, source_body = split_source_exact(source_text)
    existing_doc_id = str(front_matter.get("doc_id") or "").strip()
    if not existing_doc_id:
        raise ValueError("existing source front matter is missing doc_id")
    if existing_doc_id != target.doc_id:
        raise ValueError(f"existing source doc_id {existing_doc_id!r} does not match requested doc {target.doc_id!r}")
    return {
        "ok": True,
        "scope": scope,
        "doc_id": target.doc_id,
        "source_body": normalize_source_body(source_body),
        "source_revision": source_revision_for_text(source_text),
        "path": relative_path(repo_root, target.path),
    }


def rebuild_source_body(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    scope = source_model.normalize_scope(body.get("scope"))
    doc_id = str(body.get("doc_id") or "").strip()
    source_revision = str(body.get("source_revision") or "").strip()
    if not doc_id:
        raise ValueError("doc_id is required")
    if not source_revision:
        raise ValueError("source_revision is required")
    if "source_body" not in body:
        raise ValueError("source_body is required")

    target = resolve_scope_doc(repo_root, scope, doc_id)
    current_source_text = target.path.read_text(encoding="utf-8")
    current_revision = source_revision_for_text(current_source_text)
    if source_revision != current_revision:
        raise ValueError("source revision is stale; reload source before rebuilding")

    front_matter_source, front_matter, _current_source_body = split_source_exact(current_source_text)
    existing_doc_id = str(front_matter.get("doc_id") or "").strip()
    if not existing_doc_id:
        raise ValueError("existing source front matter is missing doc_id")
    if existing_doc_id != target.doc_id:
        raise ValueError(f"existing source doc_id {existing_doc_id!r} does not match requested doc {target.doc_id!r}")

    next_source_body = normalize_source_body(body.get("source_body"))
    next_source_text = front_matter_source + next_source_body
    next_revision = source_revision_for_text(next_source_text)
    rebuild = None

    if not dry_run:
        def write_operation() -> None:
            source_model.write_text_atomic(target.path, next_source_text)

        rebuild = write_rebuild.perform_source_write_and_rebuild(
            repo_root,
            scope,
            [target.path],
            write_operation,
            suppression_reason="docs-source-editor",
            docs_doc_ids=[target.doc_id],
            search_doc_ids=[target.doc_id],
        )
        log_event(
            repo_root,
            "docs-source-editor-rebuild",
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
        "source_revision": next_revision,
        "path": relative_path(repo_root, target.path),
        "rebuild": rebuild,
        "summary_text": f"Rebuilt {target.doc_id}.",
        "dry_run": dry_run,
    }


def detect_preferred_markdown_app() -> Optional[str]:
    configured = runtime_env().get(DEFAULT_MARKDOWN_APP_ENV, "").strip()
    if configured:
        return configured

    for app_name in ["MarkEdit", "Typora", "Marked 2", "Marked"]:
        if (Path("/Applications") / f"{app_name}.app").exists():
            return app_name
    return None


def open_source_doc(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    scope = source_model.normalize_scope(body.get("scope"))
    doc_id = str(body.get("doc_id") or "").strip()
    editor = str(body.get("editor") or "default").strip().lower()
    if not doc_id:
        raise ValueError("doc_id is required")
    if editor not in {"default", "vscode"}:
        raise ValueError("editor must be `default` or `vscode`")

    docs = source_model.load_scope_docs(repo_root, scope)
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
