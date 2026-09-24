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
    managed_document_target_request,
    resolve_managed_document_target,
)
from docs_workspace_config import path_label, require_document_authoring  # noqa: E402
from local_env import runtime_env  # noqa: E402
from markdown_renderer import normalize_markdown_blank_lines  # noqa: E402
from docs_publication_ignore import publication_ignore_path  # noqa: E402
from docs_document_subjects import project_reader_subject  # noqa: E402

STRICT_FRONT_MATTER_PATTERN = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|$)", re.DOTALL)


def normalize_source_body(value: Any) -> str:
    return str(value if value is not None else "").replace("\r\n", "\n").replace("\r", "\n")


def normalize_source_body_for_write(value: Any) -> str:
    return normalize_markdown_blank_lines(normalize_source_body(value))


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


def read_source_body(repo_root: Path, params: Dict[str, list[str]]) -> Dict[str, Any]:
    """Load the complete source snapshot for one exact editor session."""
    request_target = managed_document_target_request({key: values[0] if values else "" for key, values in params.items()})
    resolved = resolve_managed_document_target(repo_root, request_target)
    target = resolved.document
    source_text = target.source_text
    front_matter_source, front_matter, source_body = split_source_exact(source_text)
    existing_doc_id = str(front_matter.get("doc_id") or "").strip()
    if not existing_doc_id:
        raise ValueError("existing source front matter is missing doc_id")
    if existing_doc_id != target.doc_id:
        raise ValueError(f"existing source doc_id {existing_doc_id!r} does not match requested doc {target.doc_id!r}")
    payload = {
        "ok": True,
        **resolved.request_target(),
        "source_body": normalize_source_body(source_body),
        "subject": project_reader_subject(front_matter),
        "source_front_matter": front_matter_source,
        "metadata": front_matter,
        "path": path_label(repo_root, target.path),
    }
    if resolved.collection:
        payload["collection"] = resolved.collection
    return payload


def rewrite_session_metadata(front_matter_source: str, front_matter: Dict[str, Any], metadata: Dict[str, str]) -> str:
    """Apply only the retained editor fields, preserving all other authored lines."""
    lines = front_matter_source.splitlines(keepends=True)
    newline = "\r\n" if lines[0].endswith("\r\n") else "\n"
    for key, value in metadata.items():
        normalize = normalize_summary if key == "summary" else normalize_metadata_text
        if value == normalize(front_matter.get(key)):
            continue
        pattern = re.compile(rf"^[ \t]*{key}[ \t]*:")
        indices = [index for index, line in enumerate(lines) if pattern.match(line)]
        insertion = indices[0] if indices else len(lines) - 1
        lines = [line for index, line in enumerate(lines) if index not in indices]
        if value:
            lines.insert(insertion, f"{key}: {source_model.format_front_matter_value(value)}{newline}")
    result = "".join(lines)
    return result if result.endswith("\n") else result + newline


def save_source_document(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    """Validate and atomically persist the loaded session, without generation or revision checks.

    The loaded front-matter snapshot preserves non-edited fields. Only Title and
    Summary are editable here; the exact resolved target owns identity and collection.
    The watcher observes the ordinary source write independently.
    """
    required = {"stage", "doc_id", "source_front_matter", "source_body", "metadata"}
    if not required.issubset(body) or set(body) - required - {"collection"}:
        raise ValueError("Source Save requires an exact target, loaded front matter, body and metadata")
    if not isinstance(body["source_body"], str) or not isinstance(body["source_front_matter"], str):
        raise ValueError("source_body and source_front_matter must be strings")
    metadata = body["metadata"]
    if not isinstance(metadata, dict) or set(metadata) != {"title", "summary"}:
        raise ValueError("Source metadata must contain exactly title and summary")
    if any(not isinstance(value, str) for value in metadata.values()):
        raise ValueError("Source metadata values must be strings")
    metadata = {"title": normalize_metadata_text(metadata["title"]), "summary": normalize_summary(metadata["summary"])}
    if not metadata["title"]:
        raise ValueError("title is required")

    resolved = resolve_managed_document_target(repo_root, managed_document_target_request(body))
    require_document_authoring(resolved.parent_config)
    target = resolved.document
    front_matter_source, front_matter, trailing_body = split_source_exact(body["source_front_matter"])
    if trailing_body:
        raise ValueError("source_front_matter must contain only the loaded front matter")
    if front_matter.get("doc_id") != target.doc_id:
        raise ValueError("loaded source doc_id does not match the requested document")
    if "collection" in front_matter and front_matter["collection"] != resolved.collection:
        raise ValueError("loaded source collection does not match the requested collection")
    source_model.validate_document_status_front_matter(
        front_matter,
        collection_config=resolved.document_config,
        source_name=target.path.name,
    )

    next_source_body = normalize_source_body_for_write(body["source_body"])
    next_front_matter_source = rewrite_session_metadata(front_matter_source, front_matter, metadata)
    next_source_text = source_model.rewrite_source_collection(next_front_matter_source + next_source_body, resolved.collection)
    source_changed = next_source_text != target.source_text
    if source_changed and not dry_run:
        next_front_matter_source, next_metadata, _ = split_source_exact(next_source_text)
        next_front_matter_source = source_model.rewrite_front_matter_source_timestamp(next_front_matter_source, next_metadata)
        next_source_text = next_front_matter_source + next_source_body

    source_model.parse_collection_document_report(
        repo_root, resolved.parent_config, resolved.document_config,
        next_source_text, source_name=target.path.as_posix(),
    )
    saved_front_matter, saved_metadata, saved_body = split_source_exact(next_source_text)
    payload = {
        "ok": True,
        **resolved.request_target(),
        "source_front_matter": saved_front_matter,
        "metadata": saved_metadata,
        "source_body": normalize_source_body(saved_body),
        "path": path_label(repo_root, target.path),
        "summary_text": (
            f"{'Would save' if dry_run else 'Saved'} {target.doc_id}."
            if source_changed else f"No source changes for {target.doc_id}."
        ),
        "source_changed": source_changed,
        "dry_run": dry_run,
    }
    if source_changed and not dry_run:
        source_model.write_text_atomic(target.path, next_source_text)
    return payload


def open_publication_ignore(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    """Open only the configured Working ignore file in VS Code, including invalid JSON for repair."""
    if set(body) != {"stage"} or body.get("stage") != "working":
        raise ValueError("Opening the publication ignore file requires only Working stage identity")
    path = publication_ignore_path(repo_root)
    if not path.is_file():
        raise FileNotFoundError("Working unpublishable.json is unavailable")
    open_source_path(repo_root, path, editor="vscode", dry_run=dry_run)
    return {"ok": True, "stage": "working", "editor": "vscode", "dry_run": dry_run}


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
            "stage": resolved.stage,
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
