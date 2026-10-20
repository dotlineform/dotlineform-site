"""Docs source management service routes for Local Studio."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
SHARED_PYTHON_DIR = REPO_ROOT / "studio" / "shared" / "python"
if str(SHARED_PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_PYTHON_DIR))

import docs_source_model as source_model  # noqa: E402
from docs_management_context import DEFAULT_MARKDOWN_APP_ENV, log_event  # noqa: E402
from docs_management_mutations import normalize_metadata_text  # noqa: E402
from docs_front_matter import normalize_summary, rewrite_front_matter_fields  # noqa: E402
from docs_management_document_target import (  # noqa: E402
    committed_document_record,
    ManagedDocumentCollection,
    ManagedDocumentTarget,
    managed_document_target_request,
    normalize_managed_document_target,
    resolve_managed_document_target,
)
from docs_workspace_config import load_docs_stage, path_label, require_document_authoring  # noqa: E402
from local_env import runtime_env  # noqa: E402
from markdown_renderer import normalize_markdown_blank_lines  # noqa: E402
from docs_publication_ignore import publication_ignore_path  # noqa: E402
from docs_recent_exclusions import recent_exclusions_path  # noqa: E402
from docs_document_rebuild import rebuild_prepared_document  # noqa: E402
from docs_source_media_service import source_media_options, prepare_source_media, write_prepared_source_media  # noqa: E402
from docs_source_media_upload import SourceMediaUpload  # noqa: E402
from docs_document_media_ownership import compare_document_media  # noqa: E402
from docs_source_media_adoption import prepare_source_media_adoption  # noqa: E402
from docs_report_source import ReportDescriptor  # noqa: E402


def normalize_source_body(value: Any) -> str:
    return str(value if value is not None else "").replace("\r\n", "\n").replace("\r", "\n")


def normalize_source_body_for_write(value: Any) -> str:
    return normalize_markdown_blank_lines(normalize_source_body(value))


def _validate_source_identity(
    target: Dict[str, str], front_matter: Dict[str, Any], resolved: ManagedDocumentCollection | ManagedDocumentTarget,
) -> None:
    if front_matter.get("doc_id") != target["doc_id"]:
        raise ValueError("source doc_id must match the mounted document")
    if "collection" in front_matter and front_matter["collection"] != resolved.collection:
        raise ValueError("source collection must match the mounted document collection")


def read_source_document(repo_root: Path, params: Dict[str, list[str]]) -> Dict[str, Any]:
    """Load the complete source snapshot for one exact editor session."""
    request_target = managed_document_target_request({key: values[0] if values else "" for key, values in params.items()})
    resolved = resolve_managed_document_target(repo_root, request_target)
    target = resolved.document
    source_text = target.source_text
    payload = {
        "ok": True,
        **resolved.request_target(),
        "source_text": source_text,
        "media_options": source_media_options(),
        "path": path_label(repo_root, target.path),
    }
    if resolved.collection:
        payload["collection"] = resolved.collection
    return payload


def source_metadata_updates(front_matter: Dict[str, Any]) -> tuple[Dict[str, str], list[str]]:
    """Keep existing Title/Summary formatting; Title completeness belongs to the UI."""
    updates: Dict[str, str] = {}
    removed: list[str] = []
    for key in ("title", "summary"):
        if key not in front_matter and key == "summary":
            continue
        raw_value = front_matter.get(key)
        if not isinstance(raw_value, str):
            raise ValueError(f"{key} must be a string")
        normalize = normalize_summary if key == "summary" else normalize_metadata_text
        value = normalize(raw_value)
        if value == raw_value and (value or key == "title"):
            continue
        if value or key == "title":
            updates[key] = value
        else:
            removed.append(key)
    return updates, removed


def source_candidate_target(body: Dict[str, Any]) -> Dict[str, str]:
    """Accept one complete buffer with an independently declared fixed target."""
    required = {"doc_id", "source_text"}
    if not required.issubset(body) or set(body) - required - {"collection"}:
        raise ValueError("Source requires an exact target and complete source_text")
    if not isinstance(body["source_text"], str):
        raise ValueError("source_text must be a string")
    return normalize_managed_document_target(managed_document_target_request(body))


def _source_candidate_parts(
    target: Dict[str, str],
    source_text: str,
    resolved: ManagedDocumentCollection | ManagedDocumentTarget,
) -> source_model.SourceParts:
    """Parse once and bind the buffer to its fixed target without Save rules."""
    source_name = f"{target['doc_id']}.md"
    parts = source_model.parse_source_parts(
        source_text, source_name=source_name, strict=True,
    )
    _validate_source_identity(target, parts.metadata, resolved)
    return parts


@dataclass(frozen=True)
class SourceCandidate:
    parts: source_model.SourceParts
    metadata: Dict[str, Any]
    body: str
    updates: Dict[str, str]
    removed: list[str]
    report: ReportDescriptor | None


def prepare_source_candidate(
    repo_root: Path,
    target: Dict[str, str],
    source_text: str,
    resolved: ManagedDocumentTarget,
) -> SourceCandidate:
    """Establish candidate validity once before selected media preparation."""
    require_document_authoring(resolved.parent_config)
    source_name = f"{target['doc_id']}.md"
    parts = _source_candidate_parts(target, source_text, resolved)
    front_matter = parts.metadata
    source_model.validate_document_status_front_matter(
        front_matter,
        collection_config=resolved.document_config,
        source_name=source_name,
    )

    updates, removed = source_metadata_updates(front_matter)
    if resolved.collection:
        if front_matter.get("collection") != resolved.collection:
            updates["collection"] = resolved.collection
        removed.append("ui_status")
    else:
        removed.append("collection")
    next_metadata = {key: value for key, value in front_matter.items() if key not in removed}
    next_metadata.update(updates)
    next_source_body = normalize_source_body_for_write(parts.body)
    report = source_model.parse_collection_document_report(
        repo_root, resolved.parent_config, resolved.document_config,
        parts.prefix + next_source_body, front_matter=next_metadata, body=next_source_body, source_name=source_name,
    )
    return SourceCandidate(parts, next_metadata, next_source_body, updates, removed, report)


def finish_source_candidate(
    resolved: ManagedDocumentTarget, candidate: SourceCandidate, body: str, *, dry_run: bool,
) -> tuple[source_model.SourceDoc, bool]:
    """Assemble validated fields and the adopted body without parsing them again."""
    updates = dict(candidate.updates)
    next_metadata = candidate.metadata
    header_newline = "\r\n" if resolved.document.source_text.splitlines(keepends=True)[0].endswith("\r\n") else "\n"

    def assembled_source() -> str:
        prefix = rewrite_front_matter_fields(
            candidate.parts.prefix, updates, remove_fields=candidate.removed, fields=candidate.parts.fields,
        )
        prefix = normalize_source_body(prefix).replace("\n", header_newline)
        return (prefix if prefix.endswith("\n") else prefix + header_newline) + body

    next_source_text = assembled_source()
    source_changed = next_source_text != resolved.document.source_text
    if source_changed and not dry_run:
        next_metadata = source_model.advance_doc_front_matter(next_metadata)
        updates.update({key: next_metadata[key] for key in ("added_date", "last_updated")})
        next_source_text = assembled_source()
    return replace(
        resolved.document, source_text=next_source_text, front_matter=next_metadata,
        body=body, title=next_metadata["title"],
        ui_status=source_model.normalize_ui_status(next_metadata.get("ui_status")), report=candidate.report, parts=None,
    ), source_changed


def save_source_document(
    repo_root: Path, body: Dict[str, Any], dry_run: bool, *, media_uploads: list[SourceMediaUpload],
) -> Dict[str, Any]:
    """Prepare selected media, persist one candidate and await exact generation."""
    request_target = source_candidate_target({key: value for key, value in body.items() if key != "media"})
    resolved = resolve_managed_document_target(repo_root, request_target)
    try:
        candidate = prepare_source_candidate(repo_root, request_target, body["source_text"], resolved)
    except (ValueError, OSError, RuntimeError) as error:
        raise ValueError(f"Source {resolved.doc_id} candidate preparation failed: {error}") from error
    writes, notes = prepare_source_media(repo_root, resolved, body["media"], media_uploads)
    adopted_body, adopted_writes = prepare_source_media_adoption(repo_root, resolved, candidate.body, writes)
    writes.extend(adopted_writes)
    prepared, source_changed = finish_source_candidate(resolved, candidate, adopted_body, dry_run=dry_run)
    target = resolved.document
    next_source_text = prepared.source_text
    media_change = compare_document_media(
        resolved.document_config, target.doc_id,
        previous_body=target.body,
        body=prepared.body,
    )

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
        "media_notes": notes,
        "media_effects": [],
        "media_complete": False,
        "source_saved": False,
        "generation_complete": False,
    }
    if not dry_run:
        committed = {"target": resolved.request_target(), "record": committed_document_record(prepared.front_matter, target.doc_id, resolved.document_config, collection=resolved.collection, parent_id=target.parent_id)}
        prepared.has_thumbnail = committed["record"].get("has_thumbnail", False)
        phase = "media persistence"
        try:
            write_prepared_source_media(writes, payload["media_effects"])
            payload["media_complete"] = True
            phase = "source persistence"
            if source_changed:
                source_model.write_text_atomic(target.path, next_source_text)
            payload["source_saved"] = True
            payload["committed_document"] = committed
            phase = "document generation"
            media_writes = {kind: set(names) for kind, names in media_change.added.items()}
            ready_media: dict[str, list[str]] = {}
            for effect in payload["media_effects"]:
                if effect["status"] in {"verified", "unchanged"}:
                    ready_media.setdefault(effect["media_type"], []).append(effect["identity"])
                if effect["status"] == "verified" and effect["identity"] in media_change.current.get(effect["media_type"], []):
                    media_writes.setdefault(effect["media_type"], set()).add(effect["identity"])
            media_change = replace(media_change, ready=ready_media)
            payload["rebuild"] = rebuild_prepared_document(
                repo_root, resolved, prepared, media_change=media_change,
                media_writes={kind: sorted(names) for kind, names in media_writes.items()},
            )["rebuild"]
        except Exception as error:
            from docs_publication_preparation import PublicationHandoffError

            if isinstance(error, PublicationHandoffError):
                payload.update(ok=False, phase=error.phase, generation_complete=True, publication_handoff_complete=False,
                               media_removal_effects=error.removal_effects,
                               error=f"{target.doc_id}: source saved and local document generated; {error.phase} incomplete: {error}")
                return payload
            completed = [f"{item['media_type']}/{item['identity']} ({item['status']})" for item in payload["media_effects"] if item["status"] in {"written", "verified"}]
            effects = "; completed media writes: " + ", ".join(completed) if completed else ""
            saved = "Source saved; " if payload["source_saved"] else "Source not saved; "
            payload.update(ok=False, phase=phase, error=f"{target.doc_id}: {saved}{phase} failed: {error}{effects}")
            return payload
        payload["generation_complete"] = True
        payload["publication_handoff_complete"] = True
        payload["summary_text"] = "Source saved and document rebuilt."
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

    preferred_app = detect_preferred_markdown_app() if editor == "default" else None
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
