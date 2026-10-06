"""Docs source management service routes for Local Studio."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
SHARED_PYTHON_DIR = REPO_ROOT / "studio" / "shared" / "python"
if str(SHARED_PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_PYTHON_DIR))

import docs_source_model as source_model  # noqa: E402
from docs_management_context import DEFAULT_MARKDOWN_APP_ENV, log_event  # noqa: E402
from docs_management_mutations import normalize_metadata_text, normalize_summary  # noqa: E402
from docs_management_document_target import (  # noqa: E402
    committed_document_record,
    ManagedDocumentCollection,
    ManagedDocumentTarget,
    managed_document_target_request,
    normalize_managed_document_target,
    resolve_managed_document_collection,
    resolve_managed_document_target,
)
from docs_workspace_config import load_docs_stage, path_label, require_document_authoring  # noqa: E402
from local_env import runtime_env  # noqa: E402
from markdown_renderer import normalize_markdown_blank_lines  # noqa: E402
from docs_publication_ignore import publication_ignore_path  # noqa: E402
from docs_recent_exclusions import recent_exclusions_path  # noqa: E402
from docs_document_subjects import project_reader_subject  # noqa: E402
from docs_collection_customisations import collection_customisation_metadata_record  # noqa: E402


def normalize_source_body(value: Any) -> str:
    return str(value if value is not None else "").replace("\r\n", "\n").replace("\r", "\n")


def normalize_source_body_for_write(value: Any) -> str:
    return normalize_markdown_blank_lines(normalize_source_body(value))


def read_source_document(repo_root: Path, params: Dict[str, list[str]]) -> Dict[str, Any]:
    """Load the complete source snapshot for one exact editor session."""
    request_target = managed_document_target_request({key: values[0] if values else "" for key, values in params.items()})
    resolved = resolve_managed_document_target(repo_root, request_target)
    target = resolved.document
    source_text = target.source_text
    _, front_matter, _ = source_model.split_source_text(source_text, source_name=target.path.name, strict=True)
    existing_doc_id = str(front_matter.get("doc_id") or "").strip()
    if not existing_doc_id:
        raise ValueError("existing source front matter is missing doc_id")
    if existing_doc_id != target.doc_id:
        raise ValueError(f"existing source doc_id {existing_doc_id!r} does not match requested doc {target.doc_id!r}")
    payload = {
        "ok": True,
        **resolved.request_target(),
        "source_text": source_text,
        "path": path_label(repo_root, target.path),
    }
    if resolved.collection:
        payload["collection"] = resolved.collection
    return payload


def normalize_source_metadata(front_matter_source: str, front_matter: Dict[str, Any]) -> str:
    """Normalize Title/Summary without rewriting unrelated authored lines."""
    lines = front_matter_source.splitlines(keepends=True)
    newline = "\r\n" if lines[0].endswith("\r\n") else "\n"
    for key in ("title", "summary"):
        if key not in front_matter and key == "summary":
            continue
        raw_value = front_matter.get(key)
        if not isinstance(raw_value, str):
            raise ValueError(f"{key} must be a string")
        normalize = normalize_summary if key == "summary" else normalize_metadata_text
        value = normalize(raw_value)
        if key == "title" and not value:
            raise ValueError("title is required")
        if value and value == raw_value:
            continue
        pattern = re.compile(rf"^[ \t]*{key}[ \t]*:")
        indices = [index for index, line in enumerate(lines) if pattern.match(line)]
        insertion = indices[0] if indices else len(lines) - 1
        lines = [line for index, line in enumerate(lines) if index not in indices]
        if value:
            lines.insert(insertion, f"{key}: {source_model.format_front_matter_value(value)}{newline}")
    result = "".join(lines)
    return result if result.endswith("\n") else result + newline


def source_candidate_target(body: Dict[str, Any]) -> Dict[str, str]:
    """Accept one complete buffer with an independently declared fixed target."""
    required = {"doc_id", "source_text"}
    if not required.issubset(body) or set(body) - required - {"collection"}:
        raise ValueError("Source requires an exact target and complete source_text")
    if not isinstance(body["source_text"], str):
        raise ValueError("source_text must be a string")
    return normalize_managed_document_target(managed_document_target_request(body))


def validate_source_candidate(
    repo_root: Path,
    target: Dict[str, str],
    source_text: str,
    resolved: ManagedDocumentCollection | ManagedDocumentTarget,
) -> tuple[str, Dict[str, Any]]:
    """Validate the buffer using already resolved identity and schema owners."""
    require_document_authoring(resolved.parent_config)
    source_name = f"{target['doc_id']}.md"
    front_matter_source, front_matter, source_body = source_model.split_source_text(
        source_text, source_name=source_name, strict=True,
    )
    if front_matter.get("doc_id") != target["doc_id"]:
        raise ValueError("source doc_id must match the mounted document")
    if "collection" in front_matter and front_matter["collection"] != resolved.collection:
        raise ValueError("source collection must match the mounted document collection")
    source_model.validate_document_status_front_matter(
        front_matter,
        collection_config=resolved.document_config,
        source_name=source_name,
    )

    next_source_body = normalize_source_body_for_write(source_body)
    next_front_matter_source = normalize_source_metadata(front_matter_source, front_matter)
    next_source_text = source_model.rewrite_source_collection(next_front_matter_source + next_source_body, resolved.collection)
    _, next_metadata, _ = source_model.split_source_text(next_source_text, source_name=source_name, strict=True)
    # Collection customisations own Subject validity; common projection also rejects multiple declarations.
    if resolved.collection:
        collection_customisation_metadata_record(
            resolved.document_config.collection_customisation, next_metadata, doc_id=target["doc_id"],
        )
    project_reader_subject(next_metadata)
    source_model.parse_collection_document_report(
        repo_root, resolved.parent_config, resolved.document_config,
        next_source_text, source_name=source_name,
    )
    return next_source_text, next_metadata


def read_source_context(repo_root: Path, body: Dict[str, Any]) -> Dict[str, Any]:
    """Project validated unsaved authoring context without a write or browser parser."""
    target = source_candidate_target(body)
    resolved = resolve_managed_document_collection(repo_root, collection=target.get("collection"))
    _, metadata = validate_source_candidate(repo_root, target, body["source_text"], resolved)
    payload: Dict[str, Any] = {"ok": True, **target}
    subject = project_reader_subject(metadata)
    if subject is not None:
        payload["subject"] = subject
    return payload


def save_source_document(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    """Persist one validated complete buffer; the watcher independently observes the write."""
    request_target = source_candidate_target(body)
    resolved = resolve_managed_document_target(repo_root, request_target)
    next_source_text, _ = validate_source_candidate(repo_root, request_target, body["source_text"], resolved)
    target = resolved.document
    # Textareas normalize line endings; retain the loaded header's newline convention.
    front_matter_source, _, source_body = source_model.split_source_text(next_source_text, strict=True)
    original_first_line = target.source_text.splitlines(keepends=True)[0]
    header_newline = "\r\n" if original_first_line.endswith("\r\n") else "\n"
    next_source_text = normalize_source_body(front_matter_source).replace("\n", header_newline) + source_body
    source_changed = next_source_text != target.source_text
    if source_changed and not dry_run:
        next_front_matter_source, next_metadata, next_source_body = source_model.split_source_text(next_source_text, strict=True)
        next_front_matter_source = source_model.rewrite_front_matter_source_timestamp(next_front_matter_source, next_metadata)
        next_source_text = next_front_matter_source + next_source_body

    payload = {
        "ok": True,
        **resolved.request_target(),
        "source_text": next_source_text,
        "path": path_label(repo_root, target.path),
        "summary_text": (
            f"{'Would save' if dry_run else 'Saved'} {target.doc_id}."
            if source_changed else f"No source changes for {target.doc_id}."
        ),
        "source_changed": source_changed,
        "dry_run": dry_run,
    }
    if not dry_run:
        metadata, _ = source_model.parse_source_text(next_source_text, strict=True)
        payload["committed_document"] = {"target": resolved.request_target(), "record": committed_document_record(metadata, target.doc_id, resolved.document_config, collection=resolved.collection, parent_id=target.parent_id)}
    if source_changed and not dry_run:
        source_model.write_text_atomic(target.path, next_source_text)
    return payload


def open_publication_ignore(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    """Open only the configured Working ignore file in VS Code, including invalid JSON for repair."""
    if body:
        raise ValueError("Opening the publication ignore file requires an empty request")
    path = publication_ignore_path(repo_root)
    if not path.is_file():
        raise FileNotFoundError("Working unpublishable.json is unavailable")
    open_source_path(repo_root, path, editor="vscode", dry_run=dry_run)
    return {"ok": True, "editor": "vscode", "dry_run": dry_run}


def open_recent_exclusions(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    """Open the exact Recent policy file in VS Code, including invalid JSON for repair."""
    if body:
        raise ValueError("Opening Recent exclusions requires an empty request")
    path = recent_exclusions_path(load_docs_stage(repo_root, "working"))
    if not path.is_file():
        raise FileNotFoundError("Working recent-exclusions.json is unavailable")
    open_source_path(repo_root, path, editor="vscode", dry_run=dry_run)
    return {"ok": True, "editor": "vscode", "dry_run": dry_run}


def detect_preferred_markdown_app() -> Optional[str]:
    configured = runtime_env().get(DEFAULT_MARKDOWN_APP_ENV, "").strip()
    if configured:
        return configured

    for app_name in ["MarkEdit", "Typora", "Marked 2", "Marked"]:
        if (Path("/Applications") / f"{app_name}.app").exists():
            return app_name
    return None


def open_source_path(
    repo_root: Path,
    source_path: Path,
    *,
    editor: str,
    dry_run: bool,
) -> Optional[str]:
    if editor not in {"default", "vscode"}:
        raise ValueError("editor must be `default` or `vscode`")

    preferred_app = detect_preferred_markdown_app()
    if editor == "vscode":
        command = ["open", "-a", "Visual Studio Code", str(source_path)]
    elif preferred_app:
        command = ["open", "-a", preferred_app, str(source_path)]
    else:
        command = ["open", str(source_path)]

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
    return preferred_app if editor == "default" else None


def open_source_doc(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    editor = str(body.get("editor") or "default").strip().lower()

    resolved = resolve_managed_document_target(
        repo_root,
        managed_document_target_request(body),
    )
    target = resolved.document
    preferred_app = open_source_path(
        repo_root,
        target.path,
        editor=editor,
        dry_run=dry_run,
    )

    if not dry_run:
        event_details = {
            "doc_id": target.doc_id,
            "editor": editor,
            "preferred_app": preferred_app if editor == "default" else "",
            "path": path_label(repo_root, target.path),
        }
        if resolved.collection:
            event_details["collection"] = resolved.collection
        log_event(repo_root, "docs-open-source", event_details)

    payload = {
        "ok": True,
        **resolved.request_target(),
        "editor": editor,
        "preferred_app": preferred_app if editor == "default" else "",
        "path": path_label(repo_root, target.path),
        "summary_text": f"Opened {target.doc_id} source.",
        "dry_run": dry_run,
    }
    if resolved.collection:
        payload["collection"] = resolved.collection
    return payload
