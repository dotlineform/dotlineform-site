#!/usr/bin/env python3
"""Management-only Docs Viewer review-session temp-folder helpers."""

from __future__ import annotations

import json
from pathlib import Path
import re
import shutil
from typing import Any

from services.paths import configured_workspace_paths, marker_path

SAFE_SESSION_ID_PATTERN = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9._-]*\Z")
SAFE_DOC_ID_PATTERN = re.compile(r"\A[A-Za-z0-9_-]+\Z")


def repo_relative(repo_root: Path, path: Path) -> str:
    del repo_root
    try:
        return marker_path(path)
    except ValueError:
        return str(path)


def import_preview_root(repo_root: Path) -> Path:
    return configured_workspace_paths(repo_root).import_preview.resolve()


def validate_session_id(session_id: Any) -> str:
    value = str(session_id or "").strip()
    if not value:
        raise ValueError("session_id is required")
    if not SAFE_SESSION_ID_PATTERN.match(value):
        raise ValueError("session_id contains unsupported characters")
    return value


def validate_doc_id(doc_id: Any) -> str:
    value = str(doc_id or "").strip()
    if not value:
        raise ValueError("doc_id is required")
    if not SAFE_DOC_ID_PATTERN.match(value):
        raise ValueError("doc_id contains unsupported characters")
    return value


def resolve_session_path(repo_root: Path, session_id: Any) -> Path:
    normalized_session_id = validate_session_id(session_id)
    root = import_preview_root(repo_root)
    path = root / normalized_session_id
    if path.is_symlink():
        raise ValueError("review session folders must not be symlinks")
    resolved = path.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError("session_id resolves outside the review-session root") from exc
    return resolved


def read_json_object(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"{label} not found: {path.name}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{label} is not valid JSON: {path.name}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"{label} must be a JSON object: {path.name}")
    return payload


def read_manifest(path: Path) -> tuple[dict[str, Any], list[str]]:
    manifest_path = path / "manifest.json"
    if not manifest_path.exists():
        return {}, []
    try:
        return read_json_object(manifest_path, "review session manifest"), []
    except (FileNotFoundError, RuntimeError) as exc:
        return {}, [str(exc)]


def generated_payload_count(path: Path) -> int:
    by_id_root = path / "generated" / "by-id"
    if not by_id_root.is_dir():
        return 0
    return sum(1 for candidate in by_id_root.glob("*.json") if candidate.is_file())


def session_record(repo_root: Path, path: Path) -> dict[str, Any]:
    manifest, warnings = read_manifest(path)
    source_path = path / "source"
    generated_root = path / "generated"
    index_tree_path = generated_root / "index-tree.json"
    payload_count = generated_payload_count(path)
    return {
        "session_id": path.name,
        "path": repo_relative(repo_root, path),
        "manifest_path": repo_relative(repo_root, path / "manifest.json") if (path / "manifest.json").exists() else "",
        "manifest": manifest,
        "warnings": warnings,
        "source_exists": source_path.is_dir(),
        "generated_root_exists": generated_root.is_dir(),
        "index_tree_exists": index_tree_path.is_file(),
        "generated_payload_count": payload_count,
        "built": index_tree_path.is_file() and payload_count > 0,
    }


def list_review_sessions(repo_root: Path) -> dict[str, Any]:
    root = import_preview_root(repo_root)
    sessions: list[dict[str, Any]] = []
    if root.exists():
        if not root.is_dir():
            raise RuntimeError(f"review-session root is not a directory: {repo_relative(repo_root, root)}")
        for candidate in sorted(root.iterdir(), key=lambda item: item.name.lower()):
            if candidate.is_symlink() or not candidate.is_dir():
                continue
            if not SAFE_SESSION_ID_PATTERN.match(candidate.name):
                sessions.append(
                    {
                        "session_id": candidate.name,
                        "path": repo_relative(repo_root, candidate),
                        "built": False,
                        "warnings": ["session folder name contains unsupported characters"],
                    }
                )
                continue
            sessions.append(session_record(repo_root, candidate.resolve()))
    return {
        "ok": True,
        "schema_version": "docs_review_sessions_v1",
        "root": marker_path(root),
        "sessions": sessions,
    }


def read_review_session_index_tree(repo_root: Path, session_id: Any) -> dict[str, Any]:
    session_path = resolve_session_path(repo_root, session_id)
    if not session_path.exists():
        raise FileNotFoundError(f"review session not found: {validate_session_id(session_id)}")
    payload = read_json_object(session_path / "generated" / "index-tree.json", "review session index tree")
    return {
        "ok": True,
        "session_id": session_path.name,
        "index_tree": payload,
    }


def read_review_session_payload(repo_root: Path, session_id: Any, doc_id: Any) -> dict[str, Any]:
    session_path = resolve_session_path(repo_root, session_id)
    normalized_doc_id = validate_doc_id(doc_id)
    if not session_path.exists():
        raise FileNotFoundError(f"review session not found: {validate_session_id(session_id)}")
    payload = read_json_object(session_path / "generated" / "by-id" / f"{normalized_doc_id}.json", "review session document payload")
    return {
        "ok": True,
        "session_id": session_path.name,
        "doc_id": normalized_doc_id,
        "payload": payload,
    }


def build_review_session(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    session_path = resolve_session_path(repo_root, body.get("session_id"))
    if not session_path.exists():
        raise FileNotFoundError(f"review session not found: {session_path.name}")
    if not session_path.is_dir():
        raise ValueError(f"review session is not a directory: {session_path.name}")
    record = session_record(repo_root, session_path)
    return {
        "ok": True,
        "session_id": session_path.name,
        "build_status": "not_implemented",
        "built": record["built"],
        "session": record,
        "summary_text": "Review session build endpoint is reserved; build implementation is not wired yet.",
    }


def delete_review_session(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    session_path = resolve_session_path(repo_root, body.get("session_id"))
    session_id = session_path.name
    if not session_path.exists():
        return {
            "ok": True,
            "session_id": session_id,
            "deleted": False,
            "summary_text": f"Review session {session_id} was already absent.",
        }
    if not session_path.is_dir():
        raise ValueError(f"review session is not a directory: {session_id}")
    shutil.rmtree(session_path)
    return {
        "ok": True,
        "session_id": session_id,
        "deleted": True,
        "summary_text": f"Review session {session_id} deleted.",
    }
